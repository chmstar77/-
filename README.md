# MESTIS Plus 아침업무 자동화 (1단계)

현재 스크립트는 아래 작업만 자동화합니다.

1. 바탕화면 `MESTIS Plus` 실행
2. 비밀번호 `1532` 입력 후 `접속`
3. 상단 `재고` 버튼 클릭
4. `재고구분`, `하치장` 입력값 삭제

## 실행 환경

- Windows
- Python 3.10+
- 패키지: `pywinauto`

## 설치

```bash
pip install pywinauto pygetwindow
```

## 실행

```bash
python mestis_morning_login.py
```

## 주의

- 실제 ERP UI 텍스트/컨트롤 타입이 다르면 버튼 탐지/입력칸 탐지가 실패할 수 있습니다.
- 실패 시 `inspect.exe`(Windows SDK)로 컨트롤 이름 확인 후 코드의 `title` 값을 맞춰야 합니다.
