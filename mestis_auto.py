import json
import os
import subprocess
import time
from datetime import datetime

import pyautogui
import pyperclip
from openpyxl import Workbook

LOGIN_PW = "1532"
F12_PW = "2600"
SAVE_DIR = r"C:\사용자\우성철강\바탕 화면"
MESTIS_EXE_PATH = r"C:\MESTIS Plus\Mestis.exe"
APP_OPEN_WAIT = 5
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POINTS_FILE = os.path.join(SCRIPT_DIR, "mestis_points.json")


def log(msg: str):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def press_tab(n):
    for _ in range(n):
        pyautogui.press("tab")
        time.sleep(0.05)


def open_mestis_from_desktop():
    if os.path.exists(MESTIS_EXE_PATH):
        log(f"실행 파일 발견: {MESTIS_EXE_PATH}")
        os.startfile(MESTIS_EXE_PATH)
        return True
    log(f"실행 파일이 없습니다: {MESTIS_EXE_PATH}")
    return False


def load_points():
    if not os.path.exists(POINTS_FILE):
        log(f"좌표 파일이 없어 학습 모드로 진행합니다: {POINTS_FILE}")
        return None

    with open(POINTS_FILE, "r", encoding="utf-8") as f:
        points = json.load(f)

    required_keys = {"pw_field", "login_button", "stock_menu", "stock_loading_click", "incoming_checkbox", "search_button", "notepad_taskbar"}
    if not required_keys.issubset(points.keys()):
        log("좌표 파일 형식이 올바르지 않아 재학습합니다.")
        return None

    log(f"좌표 파일 로드 완료: {POINTS_FILE}")
    return points


def save_points(points):
    with open(POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False, indent=2)
    log(f"좌표 파일 저장 완료: {POINTS_FILE}")


def ask_point(name, guide, wait_sec=5):
    log(f"[{name}] {guide}")
    log(f"[{name}] 마우스를 위치시키세요. {wait_sec}초 뒤 현재 위치를 자동 저장합니다.")
    for sec in range(wait_sec, 0, -1):
        print(f"[{name}] {sec}...", end="\r", flush=True)
        time.sleep(1)
    print(" " * 80, end="\r", flush=True)
    pos = pyautogui.position()
    log(f"{name} 좌표 저장: {pos}")
    return {"x": pos.x, "y": pos.y}


def calibrate_points():
    log("=== 좌표 학습(1회만) 시작 ===")
    log("안내: 각 항목에서 마우스를 위치시키면 카운트다운 후 자동 저장됩니다.")

    points = {
        "pw_field": ask_point("로그인 패스워드 칸", "MESTIS 로그인창의 '패스워드 입력칸' 위에 마우스를 올리세요."),
        "login_button": ask_point("로그인 접속 버튼", "MESTIS 로그인창의 '접속' 버튼 위에 마우스를 올리세요."),
        "stock_menu": ask_point("상단 재고 메뉴", "로그인 후 메인화면의 '재고' 메뉴 위에 마우스를 올리세요."),
        "stock_loading_click": ask_point("재고 로딩용 클릭 위치", "재고 메뉴 클릭 후 로딩을 위해 한 번 클릭할 위치에 마우스를 올리세요."),
        "incoming_checkbox": ask_point("입고 체크박스", "재고 조회 화면의 '입고' 체크박스 위에 마우스를 올리세요."),
        "search_button": ask_point("검색 버튼", "재고 조회 화면의 '검색' 버튼 위에 마우스를 올리세요."),
        "notepad_taskbar": ask_point("작업표시줄 메모장", "메모장이 열린 뒤 아래 작업표시줄의 메모장 아이콘 위에 마우스를 올리세요."),
    }

    save_points(points)
    log(f"좌표 저장 완료: {POINTS_FILE}")
    return points


def click_point(pt):
    pyautogui.click(pt["x"], pt["y"])
    time.sleep(0.25)


def move_and_click(pt, label):
    log(f"동작: {label} 위치로 마우스 이동 ({pt['x']}, {pt['y']})")
    pyautogui.moveTo(pt["x"], pt["y"], duration=0.35)
    pyautogui.click()
    time.sleep(0.25)


def get_pixel_color(pt):
    image = pyautogui.screenshot(region=(pt["x"], pt["y"], 1, 1))
    return image.getpixel((0, 0))


def wait_for_screen_change(pt, label, baseline_color, timeout=30, interval=0.5):
    log(f"{label} 대기 시작: 화면 변화 감지 방식, 최대 {timeout}초")
    deadline = time.time() + timeout
    while time.time() < deadline:
        current_color = get_pixel_color(pt)
        if current_color != baseline_color:
            log(f"{label} 감지 완료: {baseline_color} -> {current_color}")
            time.sleep(0.5)
            return True
        time.sleep(interval)

    raise RuntimeError(f"{label}을 {timeout}초 안에 감지하지 못했습니다.")


def click_window_center(title_candidates, label):
    for title in title_candidates:
        windows = pyautogui.getWindowsWithTitle(title)
        if not windows:
            continue

        window = windows[0]
        log(f"{label} 창 활성화: {window.title}")
        window.activate()
        time.sleep(0.5)
        x = window.left + window.width // 2
        y = window.top + window.height // 2
        pyautogui.moveTo(x, y, duration=0.25)
        pyautogui.click()
        time.sleep(0.2)
        return True

    log(f"{label} 창을 찾지 못했습니다. 현재 활성 창에서 계속 진행합니다.")
    pyautogui.click()
    time.sleep(0.2)
    return False



def open_excel_blank_workbook():
    log("엑셀 새 화면 열기")
    # 한/영 입력 상태와 무관하게 Excel을 실행하기 위해 키보드 타이핑 대신 Windows start 명령 사용
    subprocess.Popen(["cmd", "/c", "start", "", "excel"])
    time.sleep(4.0)

    # Excel 시작 화면이 보이는 환경에서는 Enter로 빈 통합 문서를 선택합니다.
    pyautogui.press("enter")
    time.sleep(2.0)


def select_excel_cell_a1():
    log("엑셀 A1 셀 선택")
    pyautogui.press("f5")
    time.sleep(0.3)
    pyautogui.write("A1", interval=0.03)
    pyautogui.press("enter")
    time.sleep(0.3)


def select_excel_reference(reference: str):
    pyautogui.press("f5")
    time.sleep(0.2)
    pyautogui.write(reference, interval=0.02)
    pyautogui.press("enter")
    time.sleep(0.2)


def move_excel_column(source_column: str, insert_before_column: str, description: str):
    log(f"엑셀 열 이동: {description}")
    select_excel_reference(f"{source_column}:{source_column}")
    pyautogui.hotkey("ctrl", "x")
    time.sleep(0.2)
    select_excel_reference(f"{insert_before_column}:{insert_before_column}")
    pyautogui.hotkey("ctrl", "shift", "=")
    time.sleep(0.5)


def delete_excel_columns(reference: str, description: str):
    log(f"엑셀 열 삭제: {description}")
    select_excel_reference(reference)
    pyautogui.hotkey("ctrl", "-")
    time.sleep(0.4)


def rearrange_excel_columns_after_paste():
    log("엑셀 붙여넣기 후 열 정리 시작")
    move_excel_column("C", "B", "C열을 B열 앞으로")
    move_excel_column("G", "D", "G열을 C열 뒤로")
    move_excel_column("L", "E", "L열을 D열 뒤로")
    move_excel_column("O", "F", "O열을 E열 뒤로")
    move_excel_column("P", "G", "P열을 F열 뒤로")
    delete_excel_columns("H:XFD", "G열 뒤 나머지 열")
    delete_excel_columns("A:A", "B~G열 앞의 A열")




def mouse_self_test():
    """자동화 시작 전 마우스 제어 가능 여부를 눈으로 확인."""
    pos = pyautogui.position()
    log(f"마우스 제어 점검 시작: 현재 위치 ({pos.x}, {pos.y})")
    pyautogui.moveRel(25, 0, duration=0.2)
    pyautogui.moveRel(-25, 0, duration=0.2)
    log("마우스 제어 점검 완료")

def validate_points(points):
    required_keys = ["pw_field", "login_button", "stock_menu", "stock_loading_click", "incoming_checkbox", "search_button", "notepad_taskbar"]
    for key in required_keys:
        if key not in points:
            return False
        x = points[key].get("x")
        y = points[key].get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            return False
    return True

def paste_text(text: str):
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.1)


def _move_current_column(order, source_position, target_position, insert_after=False):
    source_index = source_position - 1
    target_index = target_position - 1
    moved = order.pop(source_index)

    if source_index < target_index:
        target_index -= 1
    if insert_after:
        target_index += 1

    order.insert(target_index, moved)


def build_inventory_output_rows(data: str):
    source_rows = [line.split("	") for line in data.splitlines() if line.strip()]
    if not source_rows:
        return []

    max_columns = max(len(row) for row in source_rows)
    column_order = list(range(max_columns))

    # 사용자가 엑셀에서 하는 작업을 같은 순서로 재현합니다.
    # C열을 B열 앞으로, G열을 C열 뒤로, L열을 D열 뒤로,
    # O열을 E열 뒤로, P열을 F열 뒤로 옮긴 뒤 B~G열만 남깁니다.
    for source_position, target_position, insert_after in [
        (3, 2, False),
        (7, 3, True),
        (12, 4, True),
        (15, 5, True),
        (16, 6, True),
    ]:
        if len(column_order) >= max(source_position, target_position):
            _move_current_column(column_order, source_position, target_position, insert_after)

    keep_order = column_order[1:7]
    output_rows = []
    for row in source_rows:
        output_row = []
        for source_index in keep_order:
            output_row.append(row[source_index] if source_index < len(row) else "")
        output_rows.append(output_row)

    return output_rows


def rows_to_tsv(rows):
    return "\n".join("\t".join(row) for row in rows)


def fixed_width_keep_first(value):
    text = str(value or "")
    stripped = text.strip()
    if not stripped:
        return ""

    # Excel의 "텍스트 나누기 > 너비가 일정함"에서 뒤쪽으로 분리되는 값을 버리는 용도입니다.
    # 실제 자료는 고정폭 공백으로 붙는 경우가 많으므로, 2칸 이상 공백을 우선 분리 기준으로 둡니다.
    normalized = " ".join(stripped.split())
    for separator in ["  ", "	"]:
        if separator in text:
            return text.split(separator, 1)[0].strip()
    return normalized.split(" ", 1)[0]


def apply_final_excel_adjustments(rows):
    adjusted_rows = []
    for row in rows:
        padded = list(row) + [""] * max(0, 6 - len(row))
        # 수작업 기준:
        # 1) F열 앞에 빈 열 추가
        # 2) E열 텍스트 나누기 후 F열 삭제 -> E열의 앞쪽 값만 유지
        # 3) G열(기존 F열) 텍스트 나누기 후 H열 삭제 -> 기존 F열의 앞쪽 값만 유지
        adjusted_rows.append([
            padded[0],
            padded[1],
            padded[2],
            padded[3],
            fixed_width_keep_first(padded[4]),
            fixed_width_keep_first(padded[5]),
        ])
    return adjusted_rows


def copy_notepad_contents(points):
    for attempt in range(1, 4):
        log(f"메모장 복사 시도 {attempt}/3")
        move_and_click(points["notepad_taskbar"], "작업표시줄 메모장")
        time.sleep(0.8)
        click_window_center(["메모장", "Notepad"], "메모장")

        pyperclip.copy("")
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.7)

        data = pyperclip.paste()
        if data.strip():
            log(f"메모장 복사 성공: {len(data)}글자")
            return data

        log("메모장 복사 실패: 클립보드가 비어 있어 재시도합니다.")

    raise RuntimeError("메모장 내용을 3번 시도했지만 복사하지 못했습니다.")


def _type_password_digits(password: str):
    # 숫자만 안정적으로 입력되도록 key press 방식 사용
    for ch in password:
        pyautogui.press(ch)
        time.sleep(0.05)


def login_mestis(points):
    log("로그인: 패스워드 칸 클릭")
    move_and_click(points["pw_field"], "패스워드 칸")
    pyautogui.doubleClick(points["pw_field"]["x"], points["pw_field"]["y"])
    time.sleep(0.2)

    # 기존 입력 제거
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    pyautogui.press("delete")
    time.sleep(0.1)

    log("로그인: 비밀번호 1532 입력")
    _type_password_digits(LOGIN_PW)
    time.sleep(0.1)

    log("로그인: 접속 버튼 클릭")
    move_and_click(points["login_button"], "접속 버튼")
    time.sleep(1.8)


def run_automation():
    start_ts = time.time()
    start_dt = datetime.now()

    log("자동화 시작")
    mouse_self_test()
    ok = open_mestis_from_desktop()
    if not ok:
        raise RuntimeError("MESTIS 실행 실패")

    time.sleep(APP_OPEN_WAIT)

    points = load_points()
    if points is None:
        log("좌표 파일이 없어 학습 모드로 진행합니다.")
        points = calibrate_points()
    else:
        log("좌표 파일이 있어 자동 모드로 진행합니다.")

    if not validate_points(points):
        log("좌표 파일 값이 비정상이라 재학습합니다.")
        points = calibrate_points()

    log("1초 후 자동 동작을 시작합니다.")
    time.sleep(1)

    log("로그인 처리 시작")
    stock_menu_baseline = get_pixel_color(points["stock_menu"])
    login_mestis(points)
    wait_for_screen_change(points["stock_menu"], "메스티스 메인 화면", stock_menu_baseline, timeout=30)

    log("재고 메뉴 클릭")
    move_and_click(points["stock_menu"], "상단 재고 메뉴")
    time.sleep(0.5)

    log("재고 로딩용 위치 클릭")
    move_and_click(points["stock_loading_click"], "재고 로딩용 클릭 위치")
    time.sleep(1.0)

    log("필드 입력 시작")
    pyautogui.press("delete")
    time.sleep(0.1)

    press_tab(3)
    log("형태구분 입력: 6 COIL협폭")
    paste_text("6 COIL협폭")
    time.sleep(0.2)

    log("하치장 내용 삭제")
    pyautogui.press("tab")
    time.sleep(0.05)
    pyautogui.press("delete")
    time.sleep(0.1)

    press_tab(9)
    pyautogui.write("55", interval=0.04)
    time.sleep(0.1)

    press_tab(1)
    pyautogui.write("2000", interval=0.04)
    time.sleep(0.2)

    log("입고 체크 해제")
    move_and_click(points["incoming_checkbox"], "입고 체크박스")

    log("검색 버튼 클릭")
    move_and_click(points["search_button"], "검색 버튼")
    time.sleep(1.5)

    log("F12 보안 단계")
    pyautogui.press("f12")
    time.sleep(0.5)
    pyautogui.write(F12_PW, interval=0.05)
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(0.5)
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(1.5)

    data = copy_notepad_contents(points)

    output_rows = build_inventory_output_rows(data)
    if not output_rows:
        raise RuntimeError("엑셀로 옮길 데이터가 없습니다.")

    log("최종 엑셀 정리: F열 앞 열 추가, E/G 텍스트 나누기, F/H 삭제 반영")
    output_rows = apply_final_excel_adjustments(output_rows)

    log("엑셀 파일 생성 및 저장")
    os.makedirs(SAVE_DIR, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    file_name = f"_{date_str}스켈프재고조회.xlsx"
    save_path = os.path.join(SAVE_DIR, file_name)

    wb = Workbook()
    ws = wb.active
    ws.title = "재고조회"
    for row_index, row in enumerate(output_rows, start=1):
        for column_index, value in enumerate(row, start=1):
            ws.cell(row=row_index, column=column_index, value=value)
    wb.save(save_path)

    log("저장된 엑셀 파일 열기")
    os.startfile(save_path)

    elapsed = round(time.time() - start_ts, 2)
    log("자동화 완료")
    log(f"저장 파일: {save_path}")
    log(f"실행 시작: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"실행 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"소요 시간: {elapsed}초")


if __name__ == "__main__":
    try:
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        run_automation()
    except Exception as e:
        log(f"[실패] {e}")
        log("힌트: MESTIS를 관리자 권한으로 실행 중이면 스크립트도 관리자 권한 PowerShell에서 실행해야 마우스/키보드 제어가 됩니다.")
        log("힌트: 무선 마우스 여부는 원인이 아닙니다. 좌상단(0,0)에 마우스가 가면 FAILSAFE로 중단될 수 있습니다.")
