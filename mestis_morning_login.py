"""MESTIS Plus morning automation (Windows).

Flow:
1) Launch "MESTIS Plus" shortcut from Desktop.
2) Input password 1532 and click 접속.
3) Click top "재고" button.
4) Clear values in "재고구분" and "하치장" fields.

Requirements:
    pip install pywinauto pygetwindow

Run:
    python mestis_morning_login.py
"""

from __future__ import annotations

import time
from pathlib import Path

from pywinauto import Desktop
from pywinauto.application import Application
from pywinauto.keyboard import send_keys

PASSWORD = "1532"
APP_TITLE_KEYWORD = "MESTIS"
SHORTCUT_NAME_CANDIDATES = [
    "MESTIS Plus.lnk",
    "Mestis Plus.lnk",
    "MESTIS Plus.exe",
    "Mestis Plus.exe",
]


def find_desktop_shortcut() -> Path:
    desktop = Path.home() / "Desktop"
    for name in SHORTCUT_NAME_CANDIDATES:
        p = desktop / name
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Desktop에서 MESTIS Plus 실행 파일/바로가기를 찾지 못했습니다: {SHORTCUT_NAME_CANDIDATES}"
    )


def wait_main_window(timeout: float = 30.0):
    end = time.time() + timeout
    while time.time() < end:
        windows = Desktop(backend="uia").windows()
        for w in windows:
            title = (w.window_text() or "").upper()
            if APP_TITLE_KEYWORD in title:
                return w
        time.sleep(0.5)
    raise TimeoutError("MESTIS 메인 창을 찾지 못했습니다.")


def try_click(window, title: str):
    try:
        ctrl = window.child_window(title=title, control_type="Button")
        ctrl.wait("visible ready", timeout=5)
        ctrl.click_input()
        return True
    except Exception:
        return False


def clear_edit_near_label(window, label_title: str):
    # 라벨 기준으로 인접 Edit 찾아 초기화 시도.
    label = window.child_window(title=label_title)
    label.wait("visible", timeout=8)
    label_rect = label.rectangle()

    edits = window.descendants(control_type="Edit")
    # 라벨 우측의 가장 가까운 Edit를 찾는다.
    candidates = []
    for edit in edits:
        rect = edit.rectangle()
        if rect.left >= label_rect.right - 10:
            dist = abs(rect.left - label_rect.right) + abs(rect.top - label_rect.top)
            candidates.append((dist, edit))

    if not candidates:
        raise RuntimeError(f"'{label_title}' 라벨 옆 입력칸(Edit)을 찾지 못했습니다.")

    _, target = sorted(candidates, key=lambda x: x[0])[0]
    target.click_input()
    send_keys("^a{BACKSPACE}")


def main():
    shortcut = find_desktop_shortcut()

    app = Application(backend="uia").start(str(shortcut))
    time.sleep(2)

    win = wait_main_window()
    win.set_focus()

    # 비밀번호 입력
    send_keys(PASSWORD)

    # 접속 클릭 (버튼이 안 잡히면 Enter로 대체)
    if not try_click(win, "접속"):
        send_keys("{ENTER}")

    # 메인 로딩 대기
    time.sleep(3)
    win = wait_main_window()
    win.set_focus()

    # 상단 재고 버튼 클릭
    if not try_click(win, "재고"):
        raise RuntimeError("'재고' 버튼을 찾지 못했습니다. 버튼 텍스트/컨트롤 타입 확인이 필요합니다.")

    time.sleep(1.5)

    # 재고구분, 하치장 값 지우기
    clear_edit_near_label(win, "재고구분")
    clear_edit_near_label(win, "하치장")

    print("완료: 재고 메뉴 진입 후 '재고구분', '하치장' 값 초기화")


if __name__ == "__main__":
    main()
