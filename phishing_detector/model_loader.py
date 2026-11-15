from pathlib import Path

import joblib

# 기존 프로젝트의 training.py에서 사용하는 구형 모델 경로와 목록
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

MODEL_FILES = {
    "kmeans": "kmeans.pkl",
    "gmm": "gmm.pkl",
    "meanshift": "meanshift.pkl",
    "agglomerative": "agglomerative.pkl",
    "log_reg": "lr.pkl",
    "rf": "rf.pkl",
    "cluster_labels": "cluster_labels.pkl",
}

# 현재 GUI에서 사용할 모델
GUI_MODEL_DIR = DEFAULT_MODEL_DIR / "domain_80_20"

GUI_MODEL_FILES = {
    "rf": "random_forest.joblib",
    "meanshift": "unsupervised/MeanShift_selected.joblib",
    "kmeans": "unsupervised/KMeans_selected.joblib",
    "gmm": "unsupervised/GMM_selected.joblib",
    "birch": "unsupervised/BIRCH_selected.joblib",
}


def load_models(model_dir=None):
    model_dir = GUI_MODEL_DIR if model_dir is None else Path(model_dir)

    models = {}

    for name, filename in GUI_MODEL_FILES.items():
        path = model_dir / filename

        if not path.is_file():
            raise FileNotFoundError(f"모델 파일이 없습니다: {path}")

        bundle = joblib.load(path)

        # 모든 모델에 필요한 정보
        required = {"model", "features"}

        # 군집화 모델에 추가로 필요한 정보
        if name != "rf":
            required |= {"mapping", "fallback_label"}

        if not isinstance(bundle, dict) or not required.issubset(bundle):
            raise ValueError(f"모델 저장 형식을 확인하세요: {path}")

        models[name] = bundle

    return models
