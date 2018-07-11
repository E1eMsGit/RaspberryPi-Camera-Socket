import io
import os
import queue
import socket
import struct
import sys
import threading
import tkinter as tk
from tkinter import messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(5)

server_ip = "192.168.1.4"
server_port = 9090
app_name = "RaspberryPi Video Streaming"


def init_ui():
    bg_color = "#FFFFFF"

    root.title(app_name)
    root.resizable(width=False, height=False)
    root.configure(bg='#B0BEC5')
    root.protocol("WM_DELETE_WINDOW", lambda: close_connection())

    video_frame = tk.Frame(root, bg=bg_color, bd=1, relief="raised", width=740,
                           height=596)
    video_label = tk.Label(video_frame, bd=2, relief="groove", height=576,
                           width=720)

    video_frame.pack(padx=10, pady=10)
    video_frame.pack_propagate(0)
    video_label.pack(padx=10, pady=10)

    update_image(video_label)


def update_image(video_label: tk.Label):
    """
    Обновление изображения видеофрейма.
    :param video_label: Видеофрейм.
    :return:
    """
    video_frame = video_stream_q.get()

    a = Image.fromarray(video_frame)
    b = ImageTk.PhotoImage(image=a)
    video_label.configure(image=b)

    root.update()
    root.after(0, func=lambda: update_image(video_label))


def close_connection():
    """
    Уничтожает процессы.
    Уничтожает пользовательский интерфейс.
    Закрывает соединение.
    :return:
    """
    global stop_thread
    result = messagebox.askquestion(app_name, "Close the connection?",
                                    icon='question')

    if result == 'yes':
        stop_thread = True
        video_stream_p.join()
        root.destroy()
        client_socket.close()
    else:
        pass


def video_loop():
    global stop_thread

    while stop_thread is False:
        img_len = struct.unpack("<L", connection.read(
            struct.calcsize("<L")))[0]
        if not img_len:
            break

        image_stream = io.BytesIO()
        image_stream.write(connection.read(img_len))

        data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)
        rgba_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)

        video_stream_q.put(rgba_image)


if __name__ == "__main__":
    stop_thread = False
    video_stream_q = queue.Queue()
    video_stream_p = threading.Thread(target=video_loop)

    try:
        print("Attempting to connect to the server...")
        client_socket.connect((server_ip, server_port))
        print("Connection complete")
    except socket.timeout:
        print("Server is not running. Connection fail")
        sys.exit()

    connection = client_socket.makefile("rb")

    video_stream_p.start()

    root = tk.Tk()
    init_ui()
    root.mainloop()
