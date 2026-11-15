"""프로젝트 루트에서 python3 main.py로 피싱체크를 실행합니다."""

from phishing_detector.model_loader import load_models
from phishing_detector.prediction import predict_phishing
from phishing_detector.ui.app import App


def main():
    models = load_models()

    app = App(models, predict_phishing)
    app.mainloop()


if __name__ == "__main__":
    main()
