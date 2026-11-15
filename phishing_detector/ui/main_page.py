import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue, Empty
from threading import Thread

from .widgets import FONT_FAMILY


MODEL_NAMES = {
    "rf": "RandomForest",
    "meanshift": "MeanShift",
    "kmeans": "K-means",
    "gmm": "GMM",
    "birch": "BIRCH",
}

FEATURE_NAMES = {
    "having_ip_addr": "IP 주소 사용",
    "url_length": "URL 길이",
    "shortening_service": "단축 URL",
    "having_at_symbol": "@ 문자 포함",
    "double_slash_redirecting": "이중 슬래시",
    "prefix_suffix": "도메인 하이픈",
    "having_sub_domain": "서브도메인",
    "domain_registration_length": "도메인 등록 기간",
    "Favicon": "Favicon",
    "Port": "포트",
    "HTTPS_token": "HTTPS 토큰",
    "age_of_domain": "도메인 나이",
    "dns_record": "DNS Record",
    "count_Redirection": "리다이렉션",
    "Disabling_Right_Click": "우클릭 제한",
}


class MainPage(tk.Frame):
    def __init__(self, parent, models, predictor):
        super().__init__(
            parent,
            bg="#F5F6FA",
            padx=20,
            pady=18,
        )

        self.models = models
        self.predictor = predictor

        self._results = Queue()
        self._busy = False
        self._poll_after_id = None

        self.prediction_labels = {}

        self.create_widgets()
        self.bind(
            "<Destroy>",
            self._on_destroy,
            add="+",
        )

    def create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # 상단 제목
        header = tk.Frame(self, bg="#F5F6FA")
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 18),
        )

        tk.Label(
            header,
            text="피싱 URL 탐지",
            bg="#F5F6FA",
            font=(FONT_FAMILY, 25, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="URL을 입력해 모델별 판정을 확인하세요.",
            bg="#F5F6FA",
            fg="#626B7B",
            font=(FONT_FAMILY, 12),
        ).pack(anchor="w", pady=(6, 0))

        # URL 입력 영역
        form = tk.LabelFrame(
            self,
            text="검사할 URL",
            bg="white",
            font=(FONT_FAMILY, 13, "bold"),
            padx=15,
            pady=12,
        )
        form.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16),
        )
        form.columnconfigure(0, weight=1)

        self.url_entry = tk.Entry(
            form,
            font=(FONT_FAMILY, 14),
        )
        self.url_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            ipady=8,
            padx=(0, 12),
        )
        self.url_entry.bind(
            "<Return>",
            lambda event: self.check_url(),
        )

        self.check_button = ttk.Button(
            form,
            text="검사하기",
            command=self.check_url,
        )
        self.check_button.grid(
            row=0,
            column=1,
            ipady=6,
        )

        self.status_label = tk.Label(
            form,
            text="검사할 URL을 입력하세요.",
            bg="white",
            fg="#626B7B",
            anchor="w",
            font=(FONT_FAMILY, 11),
            wraplength=850,
        )
        self.status_label.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0),
        )

        # 좌우 결과 영역
        content = tk.Frame(self, bg="#F5F6FA")
        content.grid(
            row=2,
            column=0,
            sticky="nsew",
        )
        content.columnconfigure(0, weight=4, uniform="panel")
        content.columnconfigure(1, weight=5, uniform="panel")
        content.rowconfigure(0, weight=1)

        # 왼쪽: 모델별 판정
        model_panel = tk.LabelFrame(
            content,
            text="모델별 판정",
            bg="white",
            font=(FONT_FAMILY, 17, "bold"),
            padx=14,
            pady=12,
        )
        model_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8),
        )
        model_panel.columnconfigure(0, weight=1)

        for row, (key, name) in enumerate(MODEL_NAMES.items()):
            model_panel.rowconfigure(row, weight=1)

            card = tk.Frame(
                model_panel,
                bg="#F7F8FC",
                padx=12,
                pady=12,
            )
            card.grid(
                row=row,
                column=0,
                sticky="nsew",
                pady=5,
            )
            card.columnconfigure(0, weight=1)

            tk.Label(
                card,
                text=name,
                bg="#F7F8FC",
                anchor="w",
                font=(FONT_FAMILY, 15, "bold"),
            ).grid(row=0, column=0, sticky="w")

            method = "지도학습" if key == "rf" else "군집화 기반"

            tk.Label(
                card,
                text=method,
                bg="#F7F8FC",
                fg="#626B7B",
                font=(FONT_FAMILY, 11),
            ).grid(
                row=1,
                column=0,
                sticky="w",
                pady=(4, 0),
            )

            label = tk.Label(
                card,
                text="—",
                bg="#E9EDF3",
                fg="#626B7B",
                font=(FONT_FAMILY, 14, "bold"),
                width=6,
                pady=7,
            )
            label.grid(
                row=0,
                column=1,
                rowspan=2,
                padx=(8, 0),
            )

            self.prediction_labels[key] = label

        # 오른쪽: 특징값
        feature_panel = tk.LabelFrame(
            content,
            text="특징별 추출 결과",
            bg="white",
            font=(FONT_FAMILY, 17, "bold"),
            padx=14,
            pady=12,
        )
        feature_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0),
        )
        feature_panel.columnconfigure(0, weight=1)
        feature_panel.rowconfigure(1, weight=1)

        tk.Label(
            feature_panel,
            text="추출된 특징값을 표시합니다.",
            bg="white",
            fg="#626B7B",
            font=(FONT_FAMILY, 11),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 10),
        )

        style = ttk.Style(self)
        style.configure(
            "Features.Treeview",
            font=(FONT_FAMILY, 12),
            rowheight=29,
        )
        style.configure(
            "Features.Treeview.Heading",
            font=(FONT_FAMILY, 12, "bold"),
        )

        self.feature_table = ttk.Treeview(
            feature_panel,
            columns=("feature", "value"),
            show="headings",
            style="Features.Treeview",
            height=15,
        )
        self.feature_table.heading("feature", text="특징")
        self.feature_table.heading("value", text="특징별 징후")

        self.feature_table.column(
            "feature",
            width=260,
            minwidth=160,
        )
        self.feature_table.column(
            "value",
            width=70,
            minwidth=50,
            anchor="center",
            stretch=False,
        )
        self.feature_table.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        scroll = ttk.Scrollbar(
            feature_panel,
            orient="vertical",
            command=self.feature_table.yview,
        )
        scroll.grid(row=1, column=1, sticky="ns")

        self.feature_table.configure(yscrollcommand=scroll.set)

        self.clear_features()

    def clear_features(self):
        for item in self.feature_table.get_children():
            self.feature_table.delete(item)

        for key, name in FEATURE_NAMES.items():
            self.feature_table.insert(
                "",
                "end",
                iid=key,
                values=(name, "—"),
            )

    def check_url(self):
        if self._busy:
            return

        url = self.url_entry.get().strip()

        if not url:
            messagebox.showerror(
                "입력 오류",
                "URL을 입력하세요.",
                parent=self,
            )
            return

        self._busy = True
        self.url_entry.config(state=tk.DISABLED)
        self.check_button.state(["disabled"])

        self.status_label.config(
            text="분석 중입니다. 특징 조회에 시간이 걸릴 수 있습니다."
        )

        for label in self.prediction_labels.values():
            label.config(
                text="분석 중",
                bg="#E9EDF3",
                fg="#626B7B",
            )

        self.clear_features()

        Thread(
            target=self.background_check,
            args=(url,),
            daemon=True,
        ).start()

        self._poll_after_id = self.after(
            100,
            self.poll_result,
        )

    def background_check(self, url):
        # 작업 스레드는 Tk 위젯을 직접 변경하지 않습니다.
        try:
            result = self.predictor(url, self.models)
        except Exception as error:
            self._results.put(("error", error))
        else:
            self._results.put(("success", result))

    def poll_result(self):
        self._poll_after_id = None

        try:
            status, payload = self._results.get_nowait()
        except Empty:
            self._poll_after_id = self.after(
                100,
                self.poll_result,
            )
            return

        try:
            if status == "error":
                raise payload

            self.update_result(payload)

        except Exception as error:
            self.status_label.config(text="검사에 실패했습니다.")

            for label in self.prediction_labels.values():
                label.config(
                    text="실패",
                    bg="#E9EDF3",
                    fg="#626B7B",
                )

            self.clear_features()

            messagebox.showerror(
                "검사 오류",
                str(error),
                parent=self,
            )

        finally:
            self._busy = False
            self.url_entry.config(state=tk.NORMAL)
            self.check_button.state(["!disabled"])

    def update_result(self, result):
        self.status_label.config(text=f"검사 완료: {result['url']}")

        for key, label in self.prediction_labels.items():
            phishing = result["predictions"][key] == 1

            label.config(
                text="피싱" if phishing else "정상",
                bg="#FDE7E5" if phishing else "#E4EEFF",
                fg="#C43C32" if phishing else "#215AC5",
            )

        values = result["features"].iloc[0]

        # 숫자 특징값을 화면 표시용 문구로 변환
        value_labels = {1: "정상", 0: "의심", -1: "피싱"}

        for key, name in FEATURE_NAMES.items():
            display_value = value_labels.get(
                values[key],
                "확인불가",
            )

            self.feature_table.item(
                key,
                values=(name, display_value),
            )

    def _on_destroy(self, event):
        if event.widget is self and self._poll_after_id is not None:
            self.after_cancel(self._poll_after_id)
            self._poll_after_id = None
