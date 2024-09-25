import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageGrab, ImageTk
import os
from datetime import datetime
import winreg  # 레지스트리 모듈
import sys

# 선택한 영역의 좌표를 저장할 변수
start_x = None
start_y = None
end_x = None
end_y = None
save_directory = None  # 저장 경로를 저장할 변수
screenshot = None  # 전체 스크린샷을 저장할 변수
registry_key = r"Software\ScreenshotProgram"  # 레지스트리 키

# 리소스 경로를 찾아주는 함수
def resource_path(relative_path):
    """PyInstaller로 패키징된 실행 파일 내의 리소스를 찾기 위한 경로 설정"""
    try:
        # PyInstaller로 패키징된 실행 파일의 임시 경로
        base_path = sys._MEIPASS
    except AttributeError:
        # 개발 중일 때의 경로 (스크립트 실행 시)
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 로그 메시지를 텍스트 창에 출력하는 함수
def log_message(message):
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, message + "\n")
    log_text.config(state=tk.DISABLED)
    log_text.yview(tk.END)  # 항상 마지막 로그가 보이도록 스크롤

# 레지스트리에 경로 저장 함수
def save_directory_to_registry(directory):
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_key)
        winreg.SetValueEx(key, "SavePath", 0, winreg.REG_SZ, directory)
        winreg.CloseKey(key)
        log_message(f"경로가 레지스트리에 저장되었습니다: {directory}")
    except Exception as e:
        log_message(f"레지스트리 저장 중 오류 발생: {e}")

# 레지스트리에서 경로 불러오기 함수
def load_directory_from_registry():
    global save_directory
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key, 0, winreg.KEY_READ)
        save_directory, _ = winreg.QueryValueEx(key, "SavePath")
        winreg.CloseKey(key)
        log_message(f"저장 경로 불러옴: {save_directory}")
    except FileNotFoundError:
        log_message("레지스트리에 저장된 경로가 없습니다.")
    except Exception as e:
        log_message(f"레지스트리에서 경로 불러오기 중 오류 발생: {e}")

# 저장 경로 설정 함수
def set_save_directory():
    global save_directory
    save_directory = filedialog.askdirectory()  # 저장할 디렉토리 선택
    if save_directory:
        save_directory_to_registry(save_directory)  # 레지스트리에 경로 저장
    else:
        messagebox.showwarning("경고", "저장 경로를 선택하지 않았습니다.")
        save_directory = None

# 고유한 파일 이름 생성 함수
def generate_unique_filename(base_name, ext):
    # 현재 시간을 기반으로 파일명 생성
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{ext}"

# 전체 화면 스크린샷 함수
def capture_fullscreen():
    if save_directory:  # 저장 경로가 설정되어 있을 때만 실행
        screenshot = pyautogui.screenshot()
        filename = generate_unique_filename("fullscreen_screenshot", "png")  # 고유한 파일 이름 생성
        save_path = os.path.join(save_directory, filename)
        
        try:
            screenshot.save(save_path)
            log_message(f"전체화면 스크린샷이 {save_path}에 저장되었습니다.")
        except Exception as e:
            log_message(f"스크린샷 저장 중 오류 발생: {e}")
    else:
        messagebox.showwarning("경고", "저장 경로를 먼저 설정하세요.")

# 부분 화면 스크린샷을 찍기 위한 마우스 드래그 함수
def on_button_press(event):
    global start_x, start_y
    start_x = event.x
    start_y = event.y

def on_button_release(event):
    global end_x, end_y
    end_x = event.x
    end_y = event.y
    capture_window.quit()  # 영역 선택 후 창 종료

def on_mouse_move(event):
    canvas.delete("selection")
    # 빨간색 테두리로 영역을 그리기
    canvas.create_rectangle(start_x, start_y, event.x, event.y, outline="red", width=1, tag="selection")

def capture_area():
    if save_directory:  # 저장 경로가 설정되어 있을 때만 실행
        global capture_window, canvas, screenshot
        # 전체 화면 스크린샷 찍기
        screenshot = ImageGrab.grab()

        # Tkinter 캡처 창 설정
        capture_window = tk.Toplevel(root)
        capture_window.attributes("-fullscreen", True)  # 전체 화면
        capture_window.attributes("-topmost", True)  # 항상 위에 표시

        # 스크린샷을 Tkinter 창에 표시
        tk_screenshot = ImageTk.PhotoImage(screenshot)
        canvas = tk.Canvas(capture_window, cursor="cross")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=tk_screenshot)

        canvas.bind("<ButtonPress-1>", on_button_press)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_button_release)

        capture_window.mainloop()

        # 스크린샷 찍기
        if start_x and start_y and end_x and end_y:
            x1 = min(start_x, end_x)
            y1 = min(start_y, end_y)
            x2 = max(start_x, end_x)
            y2 = max(start_y, end_y)
            
            cropped_screenshot = screenshot.crop((x1, y1, x2, y2))  # 선택 영역만큼 자르기
            filename = generate_unique_filename("selected_screenshot", "png")  # 고유한 파일 이름 생성
            save_path = os.path.join(save_directory, filename)
            
            try:
                cropped_screenshot.save(save_path)
                log_message(f"부분 스크린샷이 {save_path}에 저장되었습니다.")
            except Exception as e:
                log_message(f"스크린샷 저장 중 오류 발생: {e}")

        # 캡처 후 창 닫기
        capture_window.destroy()
    else:
        messagebox.showwarning("경고", "저장 경로를 먼저 설정하세요.")

# 메인 Tkinter 윈도우 생성
def main_window():
    global root, log_text
    root = tk.Tk()
    root.title("MacJu 스크린샷 프로그램")
    root.geometry("400x300")

    # 아이콘 설정 (MacJu.ico 파일 경로로 설정)
    icon_path = resource_path("MacJu.ico")
    root.iconbitmap(icon_path)
    
    # 저장 경로 설정 버튼
    set_directory_button = tk.Button(root, text="저장 경로 설정", command=set_save_directory, height=2, width=20)
    set_directory_button.pack(pady=10)

    # 전체화면 스크린샷 버튼
    fullscreen_button = tk.Button(root, text="전체화면", command=capture_fullscreen, height=2, width=20)
    fullscreen_button.pack(pady=10)

    # 부분화면 스크린샷 버튼
    area_button = tk.Button(root, text="부분화면", command=capture_area, height=2, width=20)
    area_button.pack(pady=10)

    # 로그 창 생성
    log_text = tk.Text(root, height=8, state=tk.DISABLED)
    log_text.pack(pady=10, fill=tk.BOTH)

    # 저장 경로 불러오기
    load_directory_from_registry()

    root.mainloop()

if __name__ == "__main__":
    main_window()
