"""이미지 로드, 로딩 애니메이션, 점수 막대 등 공통 UI 요소"""

import math
import sys
import tkinter as tk
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parents[2] / "assets"
IMAGE_DIR = ASSET_DIR / "images"
ICON_DIR = ASSET_DIR / "icons"
FONT_FAMILY = "Apple SD Gothic Neo" if sys.platform == "darwin" else "Malgun Gothic"


def load_image(image_path, size=(100, 100), master=None):
    """이미지를 로드합니다. 반환값은 사용하는 위젯에서 참조를 유지합니다."""
    from PIL import Image, ImageTk

    with Image.open(image_path) as source:
        image = source.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image, master=master)


class PulsatingLoading(tk.Canvas):
    """원본 노트북의 회전하는 원호 로딩 표시."""

    def __init__(self, parent, size=80, arc_width=6, base_speed=8, color="green"):
        super().__init__(parent, width=size, height=size, highlightthickness=0)
        self.size = size
        self.arc_width = arc_width
        self.base_speed = base_speed
        self.color = color
        self.angle = 0
        self._animation_id = None
        self.animate()

    def animate(self):
        self.angle = (
            self.angle + self.base_speed + math.sin(math.radians(self.angle)) * 1.5
        ) % 360
        extent = 90 + math.sin(math.radians(self.angle)) * 30
        self.delete("all")
        self.create_arc(
            self.arc_width,
            self.arc_width,
            self.size - self.arc_width,
            self.size - self.arc_width,
            start=self.angle,
            extent=extent,
            outline=self.color,
            width=self.arc_width,
            style=tk.ARC,
        )
        self._animation_id = self.after(20, self.animate)

    def destroy(self):
        if self._animation_id is not None:
            self.after_cancel(self._animation_id)
            self._animation_id = None
        super().destroy()


def show_loading_dialog(parent):
    """처리 중 창을 만들고 반환합니다. 작업 완료 시 호출자가 닫습니다."""
    root = parent.winfo_toplevel()
    dialog = tk.Toplevel(root)
    dialog.title("처리중")
    dialog.transient(root)
    dialog.resizable(False, False)
    dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - 350) // 2
    y = root.winfo_rooty() + (root.winfo_height() - 200) // 2
    dialog.geometry(f"350x200{x:+d}{y:+d}")
    tk.Label(
        dialog,
        text="잠시만 기다려 주세요...",
        font=(FONT_FAMILY, 12),
    ).pack(pady=10)
    PulsatingLoading(dialog).pack(pady=10)
    return dialog
