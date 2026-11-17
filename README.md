# Phishing URL Detection

URL에서 15개 특징을 추출하고, 지도학습 모델과 군집화 모델의 피싱 탐지 결과를 비교하는 데스크톱 GUI 프로젝트입니다.

2024년 졸업작품을 바탕으로 기존 학습·평가 방식을 재검토했습니다. 도메인 기준 데이터 분할과 교차검증을 적용하여 모델을 다시 학습하고, 저장된 모델을 사용할 수 있도록 GUI를 수정했습니다.

## 주요 기능

- URL 입력 및 특징 추출
- Random Forest, MeanShift, K-Means, GMM, BIRCH의 개별 판정 결과 표시
- 입력 URL의 특징별 상태 표시

모델별 판정은 정상 또는 피싱으로 표시합니다. 특징별 정상·의심·피싱 표시는 개별 추출 규칙에 따른 상태이며, 피싱 확률이나 확정 판정을 의미하지 않습니다.

## 실행 과정

```text
URL 입력
   ↓
15개 특징 추출
   ↓
저장된 5개 모델로 예측
   ↓
모델별 판정 및 특징별 상태 표시
```

군집화 모델은 학습 데이터의 레이블을 이용해 각 군집을 정상·피싱으로 대응시킨 정보를 함께 사용합니다. 군집을 형성하는 과정에는 레이블을 사용하지 않았습니다.

## 모델 학습 및 평가

- 기존 URL 데이터 22,000개 사용
- 동일한 도메인이 학습·테스트에 중복되지 않도록 분할
- 학습 데이터 16,828개, 테스트 데이터 5,172개
- 학습 데이터에서 도메인 기준 5-fold 교차검증 수행
- 교차검증의 평균 피싱 F1 점수로 설정 선택
- 선택한 설정으로 전체 학습 데이터를 다시 학습한 뒤 고정된 테스트 데이터로 평가

분할 시 도메인 그룹의 약 20%를 테스트로 배정했으므로, URL 행 수가 정확히 80:20인 것은 아닙니다.

군집화 모델은 군집 수를 2개로 제한한 설정과 여러 군집을 허용한 설정을 비교했습니다. GUI에는 각 모델의 교차검증 결과로 선택한 모델을 적용했습니다.

## GUI에 적용한 모델의 성능

피싱을 양성 클래스인 `1`로 평가한 테스트 결과입니다.

| 모델 | Precision | Recall | F1 |
|---|---:|---:|---:|
| Random Forest | 0.9781 | 0.8958 | 0.9352 |
| MeanShift | 0.9796 | 0.8954 | 0.9356 |
| K-Means | 0.9787 | 0.8585 | 0.9147 |
| GMM | 0.9666 | 0.7716 | 0.8582 |
| BIRCH | 0.9673 | 0.7735 | 0.8596 |

## 파일 구성

```text
.
├── main.py
├── requirements.txt
├── README.md
├── phishing_detector/
│   ├── __init__.py
│   ├── features.py
│   ├── model_loader.py
│   ├── prediction.py
│   └── ui/
│       ├── __init__.py
│       ├── app.py
│       ├── main_page.py
│       └── widgets.py
├── models/
│   └── domain_80_20/
│       ├── random_forest.joblib
│       └── unsupervised/
│           ├── MeanShift_selected.joblib
│           ├── KMeans_selected.joblib
│           ├── GMM_selected.joblib
│           └── BIRCH_selected.joblib
└── assets/
    └── icons/
        └── chk.ico
```


## 실행 방법

확인한 환경은 Python 3.14.4입니다.

### 1. 프로젝트 다운로드

```bash
git clone https://github.com/SeoJangSeok/phishing-url-detection.git
cd phishing-url-detection
```

### 2. 가상환경 생성

```bash
python -m venv .venv
```

macOS에서는 환경에 따라 `python` 대신 `python3`를 사용합니다.

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 라이브러리 설치

```bash
python -m pip install -r requirements.txt
```

### 4. Tkinter 확인

```bash
python -m tkinter
```

작은 창이 열리면 사용할 수 있습니다. `tkinter`가 없는 환경에서는 Python 배포판 또는 운영체제의 설치 방법에 따라 추가해야 합니다.

### 5. GUI 실행

```bash
python main.py
```

프로그램에서 URL을 입력하고 분석을 실행합니다. 웹페이지, WHOIS, 포트 조회를 사용하므로 인터넷 연결이 필요하며 조회 상태에 따라 시간이 걸릴 수 있습니다.
