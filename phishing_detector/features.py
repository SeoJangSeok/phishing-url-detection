"""URL의 15가지 특징을 추출하는 모듈.

특징값: -1(피싱 징후), 0(의심/정보 부족),
1(정상 징후)로 표현하며, 최종 사이트 판정은 예측 모듈에서 수행합니다.
일부 특징은 HTTP, WHOIS, DNS 조회 및 포트 연결을 수행합니다.
"""

import ipaddress
import socket
from datetime import datetime, timedelta
from urllib.parse import urlparse

import pandas as pd
import requests
import tld
import whois
from bs4 import BeautifulSoup
from tld import get_tld

# python-whois 버전에 따른 예외 이름 차이 처리
try:
    from whois.exceptions import WhoisError as WhoisLookupError
except ImportError:
    from whois.parser import PywhoisError as WhoisLookupError


SHORTENERS = {
    "bit.ly",
    "kl.am",
    "cli.gs",
    "bc.vc",
    "po.st",
    "v.gd",
    "bkite.com",
    "shorl.com",
    "scrnch.me",
    "to.ly",
    "adf.ly",
    "x.co",
    "1url.com",
    "ad.vu",
    "migre.me",
    "su.pr",
    "smallurl.co",
    "cutt.us",
    "filoops.info",
    "shor7.com",
    "yfrog.com",
    "tinyurl.com",
    "u.to",
    "ow.ly",
    "ff.im",
    "rubyurl.com",
    "r2me.com",
    "post.ly",
    "twitthis.com",
    "buzurl.com",
    "cur.lv",
    "tr.im",
    "bl.lnk",
    "tiny.cc",
    "lnkd.in",
    "q.gs",
    "is.gd",
    "hurl.ws",
    "om.ly",
    "prettylinkpro.com",
    "qr.net",
    "qr.ae",
    "snipurl.com",
    "ity.im",
    "t.co",
    "db.tt",
    "link.zip.net",
    "doiop.com",
    "url4.eu",
    "poprl.com",
    "tweez.me",
    "short.ie",
    "me2.do",
    "bit.do",
    "shorte.st",
    "go2l.ink",
    "yourls.org",
    "wp.me",
    "goo.gl",
    "j.mp",
    "twurl.nl",
    "snipr.com",
    "shortto.com",
    "vzturl.com",
    "u.bb",
    "shorturl.at",
    "han.gl",
    "wo.gl",
    "wa.gl",
}

PORTS_TO_CHECK = (80, 21, 22, 23, 445, 1433, 1521, 3306, 3389)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
    )
}


# 1. IP 주소 사용 여부
def having_ip_address(url):
    hostname = urlparse(url).hostname

    try:
        ipaddress.ip_address(hostname)
        return -1
    except ValueError:
        return 1


# 2. URL 길이
def url_length(url):
    length = len(url)

    if length < 54:
        return 1
    if length <= 75:
        return 0
    return -1


# 3. 단축 URL 서비스 사용 여부
def shortening_service(url):
    hostname = urlparse(url).hostname
    return -1 if hostname in SHORTENERS else 1


# 4. @ 문자 포함 여부
def having_at_symbol(url):
    return -1 if "@" in url or "%40" in url else 1


# 5. 이중 슬래시 포함 여부
# 기존 코드의 검사 범위를 유지합니다.
def double_slash_redirecting(url):
    return -1 if "//" in url[7:] else 1


# 6. 도메인명 또는 서브도메인의 하이픈 포함 여부
def prefix_suffix(url):
    if having_ip_address(url) == -1:
        return 0

    try:
        domain = get_tld(url, as_object=True)
        has_hyphen = "-" in domain.domain or "-" in domain.subdomain
        return -1 if has_hyphen else 1
    except tld.exceptions.TldDomainNotFound:
        return -1


# 7. 서브도메인 개수
# 기존 www 제거 및 판별 규칙을 유지합니다.
def having_sub_domain(url):
    if having_ip_address(url) == -1:
        return 0

    if "www." in url[:12]:
        url = url.replace("www.", "")

    try:
        subdomain = get_tld(url, as_object=True).subdomain

        if subdomain == "":
            return 1
        if "." not in subdomain:
            return 0
        return -1
    except tld.exceptions.TldDomainNotFound:
        return -1


# WHOIS 날짜가 목록이면 첫 번째 항목을 사용합니다.
def _first_date(value):
    return value[0] if isinstance(value, list) else value


# 기존 계산식: 만료일 - 수정일
def get_total_date(url):
    domain = whois.whois(url)

    expiration = _first_date(domain.expiration_date)
    updated = _first_date(domain.updated_date)

    if expiration is None or updated is None:
        return None

    return (expiration - updated).days


# 8. 도메인 등록 기간
# 기존 날짜 계산 기준을 유지합니다.
def domain_registration_length(url):
    try:
        days = get_total_date(url)

        if days is None:
            return 0

        return -1 if days <= 365 else 1
    except WhoisLookupError:
        return -1
    except Exception:
        return 0


# 9. Favicon 주소
# 기존 상대주소/절대주소 판정과 조회 실패 반환값을 유지합니다.
def favicon(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        tags = soup.find_all(
            "link",
            rel=lambda value: value and "icon" in value.lower(),
        )

        for tag in tags:
            href = tag.get("href")

            if href:
                return 1 if urlparse(href).netloc == "" else -1

        return 1
    except Exception:
        return -1


# Port 특징과의 호환을 위해 기존 스킴 제거 방식을 유지합니다.
def remove_schemes(url):
    if "http://" in url:
        return url.replace("http://", "")
    if "https://" in url:
        return url.replace("https://", "")
    return url


# 10. 포트 조회
# 조회 대상과 포트 순서, 반환 기준을 유지합니다.
def port(url):
    target = remove_schemes(url)

    try:
        ip = socket.gethostbyname(target)
    except Exception:
        return -1

    # 기존 전역 타임아웃 동작을 유지합니다.
    socket.setdefaulttimeout(2)

    for port_number in PORTS_TO_CHECK:
        # 연결 실패 시에도 소켓을 닫습니다.
        with socket.socket() as connection:
            try:
                connection.connect((ip, port_number))
            except Exception:
                if port_number == 80:
                    return -1
            else:
                if port_number != 80:
                    return -1

    return 1


# 11. 호스트에 https 문자열이 포함되어 있는지 확인
# HTTPS 연결이나 인증서 유효성을 검사하는 특징은 아닙니다.
def https_token(url):
    hostname = urlparse(url).hostname or ""
    return -1 if "https" in hostname else 1


# 12. 도메인 만료일까지 남은 기간
# 기존 함수 이름은 유지하지만, 실제 도메인 나이를 계산하지는 않습니다.
def age_of_domain(url):
    try:
        domain = whois.whois(url)
        expiration = _first_date(domain.expiration_date)
        remaining = expiration - datetime.now()

        return 1 if remaining >= timedelta(days=182) else -1
    except Exception:
        return 0


# 13. WHOIS 조회 성공 여부
# 기존 함수 이름은 유지하지만, 실제 DNS 레코드 조회는 아닙니다.
def dns_record(url):
    try:
        whois.whois(url)
        return 1
    except Exception:
        return -1


# 14. 리다이렉션 횟수
# 기존 코드와 동일하게 301/302 응답만 집계합니다.
def count_redirection(url):
    try:
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=5,
        )

        count = sum(item.status_code in (301, 302) for item in response.history)

        if count <= 1:
            return 1
        if count < 4:
            return 0
        return -1
    except Exception:
        return 0


# 15. 우클릭 제한 문자열 포함 여부
def disabling_right_click(url):
    try:
        response = requests.get(
            url,
            timeout=5,
            headers=REQUEST_HEADERS,
        )

        return -1 if "event.button==2" in response.text else 1
    except Exception:
        return 0


def feature_extract(url):
    """기존 이름·순서의 DataFrame과 1차원 배열을 반환합니다."""

    features = {
        "having_ip_address": having_ip_address(url),
        "url_length": url_length(url),
        "shortening_service": shortening_service(url),
        "having_at_symbol": having_at_symbol(url),
        "double_slash_redirecting": double_slash_redirecting(url),
        "prefix_suffix": prefix_suffix(url),
        "having_sub_domain": having_sub_domain(url),
        "domain_registration_length": domain_registration_length(url),
        "favicon": favicon(url),
        "port": port(url),
        "https_token": https_token(url),
        "age_of_domain": age_of_domain(url),
        "dns_record": dns_record(url),
        "count_redirection": count_redirection(url),
        "disabling_right_click": disabling_right_click(url),
    }

    features_df = pd.DataFrame([features])
    return features_df, features_df.to_numpy().flatten()
