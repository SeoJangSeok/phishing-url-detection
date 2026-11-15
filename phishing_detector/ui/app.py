import tkinter as tk

from .main_page import MainPage
from .widgets import ICON_DIR, load_image


class App(tk.Tk):
    def __init__(self, models, predictor):
        super().__init__()

        self.title("피싱 URL 탐지")
        self.geometry("1100x900")
        self.minsize(960, 760)
        self.configure(bg="#F5F6FA")

        icon_path = ICON_DIR / "chk.ico"

        if icon_path.is_file():
            self.icon_image = load_image(
                icon_path,
                (32, 32),
                self,
            )
            self.iconphoto(True, self.icon_image)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.home = MainPage(
            self,
            models,
            predictor,
        )
        self.home.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
