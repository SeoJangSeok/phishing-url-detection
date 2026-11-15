from urllib.parse import urlsplit

import numpy as np

from .features import feature_extract


# 특징 추출 코드의 이름을 학습 데이터의 열 이름과 연결
FEATURE_ALIASES = {
    "having_ip_address": "having_ip_addr",
    "favicon": "Favicon",
    "port": "Port",
    "https_token": "HTTPS_token",
    "count_redirection": "count_Redirection",
    "disabling_right_click": "Disabling_Right_Click",
}


def predict_from_features(features_df, models):
    """추출된 특징으로 모델별 예측을 수행합니다."""

    features_df = features_df.rename(columns=FEATURE_ALIASES)

    predictions = {}

    for name, bundle in models.items():
        missing = set(bundle["features"]) - set(features_df.columns)

        if missing:
            raise ValueError(f"입력 특징이 없습니다: {sorted(missing)}")

        # 모델 학습 때 사용한 특징 순서를 적용
        X = features_df[bundle["features"]].to_numpy(dtype=float)

        if not np.isfinite(X).all():
            raise ValueError("특징값에 결측값 또는 무한대가 있습니다.")

        raw_prediction = bundle["model"].predict(X)

        if name == "rf":
            # RandomForest는 정상·피싱을 직접 예측
            predictions[name] = raw_prediction.astype(int)

        else:
            # 군집 번호를 저장된 대응표로 정상·피싱으로 변환
            predictions[name] = np.array(
                [
                    bundle["mapping"].get(
                        int(cluster),
                        bundle["fallback_label"],
                    )
                    for cluster in raw_prediction
                ],
                dtype=int,
            )

    return features_df, predictions


def predict_phishing(url, models):
    """URL에서 특징을 추출하고 모델별 판정을 반환합니다."""

    url = url.strip()

    # 프로토콜 없이 입력하면 https를 사용
    if "://" not in url:
        url = "https://" + url

    parsed = urlsplit(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("올바른 http 또는 https URL을 입력하세요.")

    features_df, _ = feature_extract(url)

    features_df, predictions = predict_from_features(
        features_df,
        models,
    )

    return {
        "url": url,
        "features": features_df,
        "predictions": {name: int(values[0]) for name, values in predictions.items()},
    }
