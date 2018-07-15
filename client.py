import datetime
import io
import os
import queue
import socket
import struct
import threading
import tkinter as tk
from tkinter import messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk


def init_ui():
    bg_color = "#FFFFFF"

    root.title(app_name)
    root.resizable(width=False, height=False)
    root.configure(bg='#B0BEC5')
    root.protocol("WM_DELETE_WINDOW", lambda: close_event())

    video_frame = tk.Frame(root, bg=bg_color, bd=1, relief="raised", width=740,
                           height=596)
    control_frame = tk.Frame(root, bg=bg_color, bd=1, relief="raised",
                             width=740, height=50)

    video_label = tk.Label(video_frame, bd=2, relief="groove", height=576,
                           width=720, font=("Source Code Pro", 16, "bold"))
    snapshot_button = tk.Button(control_frame, command=take_snapshot,
                                font=("Source Code Pro", 16, "bold"),
                                text="Snapshot", height=50, width=150)

    for frame in [video_frame, control_frame]:
        frame.pack(padx=10, pady=10)
        frame.pack_propagate(0)

    video_label.pack(padx=10, pady=10)
    snapshot_button.pack(padx=5, pady=5)

    update_image(video_label)


def update_image(video_label: tk.Label):
    """
    Обновление изображения видеофрейма.
    :param video_label: Видеофрейм.
    :return:
    """
    global status_index
    global queue_data
    connection_status = {0: "Attempting to connect to the server...",
                         1: "Connection complete",
                         2: "Server is not running. Connection fail"}

    if not connection_status_q.empty():
        status_index = connection_status_q.get()
        video_label.configure(text=connection_status.get(status_index))
        connection_status_q.task_done()
    else:
        if status_index in [0, 2]:
            video_label.configure(text=connection_status.get(status_index))
        elif status_index == 1:
            queue_data = video_stream_q.get()

            a = Image.fromarray(queue_data)
            b = ImageTk.PhotoImage(image=a)
            video_label.configure(image=b)
            video_stream_q.task_done()

    root.update()
    root.after(0, func=lambda: update_image(video_label))


def take_snapshot():
    global queue_data

    ts = datetime.datetime.now()
    filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
    path = os.path.sep.join(("photo", filename))

    cv2.imwrite(path, cv2.cvtColor(queue_data, cv2.COLOR_BGR2RGB))


def close_event():
    """
    Уничтожает процессы.
    Уничтожает пользовательский интерфейс.
    Закрывает соединение.
    :return:
    """
    global stop_thread
    result = messagebox.askquestion(app_name, "Are you sure you want to exit?",
                                    icon='question')

    if result == 'yes':
        if connection_t.is_alive():
            connection_t.join()
        if video_stream_t.is_alive():
            stop_thread = True
            video_stream_t.join()
        root.destroy()
        client_socket.close()
    else:
        pass


def open_connection():
    """
    Устанавливает соединение с сервером.
    :return:
    """
    global connection

    try:
        client_socket.connect((server_ip, server_port))
        connection_status = 1
        connection = client_socket.makefile("rb")
        video_stream_t.start()
    except socket.timeout:
        connection_status = 2
    finally:
        connection_status_q.put(connection_status)


def get_stream_loop():
    global stop_thread
    global connection

    while stop_thread is False:
        img_len = struct.unpack("<L", connection.read(
            struct.calcsize("<L")))[0]
        if not img_len:
            break

        image_stream = io.BytesIO()
        image_stream.write(connection.read(img_len))
        image_stream.seek(0)

        data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        video_stream_q.put(rgb_image)


if __name__ == "__main__":
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(5)

    server_ip = "192.168.1.4"
    server_port = 9090
    app_name = "RaspberryPi Video Streaming"

    connection = None
    status_index = 0
    stop_thread = False
    queue_data = None

    video_stream_q = queue.Queue()
    connection_status_q = queue.Queue()

    video_stream_t = threading.Thread(target=get_stream_loop)
    connection_t = threading.Thread(target=open_connection)

    connection_t.start()

    root = tk.Tk()
    init_ui()
    root.mainloop()
