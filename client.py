# -*- coding: utf-8 -*-
"""
====================================================================
Application for receiving video stream data from RaspberryPi camera.
====================================================================
"""
import datetime
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


class VideoStreamClient(object):
    """
    Socket client class for display RaspberryPi camera video stream data taken
    from the server on RaspberryPi.
    """

    def __init__(self, master):
        self.master = master
        self.camera_data = None
        self.status_index = 0
        self.font = ("Source Code Pro", 16, "bold")
        self.bg = "#FFFFFF"

        if getattr(sys, "frozen", False):
            self.bundle_dir = os.path.dirname(sys.executable)
        else:
            self.bundle_dir = os.path.dirname(os.path.abspath(__file__))

        self.master.title(app_name)
        self.master.resizable(width=False, height=False)
        self.master.configure(bg='#B0BEC5')
        self.master.protocol("WM_DELETE_WINDOW", lambda: self.close_event())

        self.video_frame = tk.Frame(self.master, bg=self.bg, bd=1,
                                    relief="raised", width=740, height=596)
        self.control_frame = tk.Frame(self.master, bg=self.bg, bd=1,
                                      relief="raised", width=740, height=50)

        self.video_label = tk.Label(self.video_frame, bd=2, relief="groove",
                                    width=720, height=576, font=self.font)
        self.snapshot_button = tk.Button(self.control_frame,
                                         command=self.make_snapshot,
                                         font=self.font, text="Snapshot",
                                         height=50, width=150)

        for frame in [self.video_frame, self.control_frame]:
            frame.pack(padx=10, pady=10)
            frame.pack_propagate(0)

        self.video_label.pack(padx=10, pady=10)
        self.snapshot_button.pack(padx=5, pady=5)

        self.update_image()

    def make_snapshot(self):
        """
        Create catalog for snapshots if its not exists,
        get date and time, make and save snapshot in Snapshots catalog.
        :return:
        """
        if not os.path.exists("Snapshots"):
            os.mkdir(os.path.join(self.bundle_dir, "Snapshots"))

        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        path = os.path.sep.join(("Snapshots", filename))

        cv2.imwrite(path, cv2.cvtColor(self.camera_data, cv2.COLOR_BGR2RGB))

    def update_image(self):
        """
        Update image in self.video_label.
        :return:
        """
        connection_status = {0: "Attempting to connect to the server...",
                             1: "Connection complete",
                             2: "Server is not running. Connection fail"}

        if not connection_status_q.empty():
            self.status_index = connection_status_q.get()
            self.video_label.configure(
                text=connection_status.get(self.status_index))
            connection_status_q.task_done()
        else:
            if self.status_index in [0, 2]:
                self.video_label.configure(
                    text=connection_status.get(self.status_index))
            elif self.status_index == 1:
                self.camera_data = video_image_q.get()
                video_image_q.task_done()

                a = Image.fromarray(self.camera_data)
                b = ImageTk.PhotoImage(image=a)
                self.video_label.configure(image=b)

        self.master.update()
        self.master.after(0, func=lambda: self.update_image())

    def close_event(self):
        """
        Destroys the processes.
        Destroys the user interface.
        Closes the connection.
        :return:
        """
        result = messagebox.askquestion(app_name,
                                        "Are you sure you want to exit?",
                                        icon='question')

        if result == 'yes':
            if open_connection_t.is_alive():
                open_connection_t.join()
            if get_video_stream_t.is_alive():
                stop_video_stream_q.put(True)
                get_video_stream_t.join()
            self.master.destroy()
            client_socket.close()
        else:
            pass


def open_connection():
    """
    Function for open_connection_t thread.
    Establishes a connection to the server.
    :return:
    """
    client_socket.settimeout(5)

    try:
        client_socket.connect((server_ip, server_port))
        connection_status = 1
        connection = client_socket.makefile("rb")
        connection_q.put(connection)
        get_video_stream_t.start()
    except socket.timeout:
        connection_status = 2
    finally:
        connection_status_q.put(connection_status)


def get_video_image_loop():
    """
    Function for get_video_stream_t thread.
    Get data from connection makefile, convert bgr to rgb image, put data to
    video_image_q.
    :return:
    """
    stop_video_stream = False

    if not connection_q.empty():
        connection = connection_q.get()
        connection_q.task_done()

        while stop_video_stream is False:
            img_len = struct.unpack("<L", connection.read(
                struct.calcsize("<L")))[0]
            if not img_len:
                break

            image_stream = io.BytesIO()
            image_stream.write(connection.read(img_len))
            image_stream.seek(0)

            data = np.fromstring(image_stream.getvalue(), dtype=np.uint8)
            bgr_video_image = cv2.imdecode(data, 1)
            rgb_video_image = cv2.cvtColor(bgr_video_image, cv2.COLOR_BGR2RGB)

            video_image_q.put(rgb_video_image)

            if not stop_video_stream_q.empty():
                stop_video_stream = stop_video_stream_q.get()
                stop_video_stream_q.task_done()


if __name__ == "__main__":
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "192.168.1.4"
    server_port = 9090
    app_name = "RaspberryPi Video Streaming"

    # Queue for client_socket makefile.
    connection_q = queue.Queue()
    # Queue for connection status.
    connection_status_q = queue.Queue()
    # Queue for camera data from connection makefile after convert to rgb.
    video_image_q = queue.Queue()
    # Queue for flag to stop video_stream_t thread.
    stop_video_stream_q = queue.Queue()

    open_connection_t = threading.Thread(target=open_connection)
    get_video_stream_t = threading.Thread(target=get_video_image_loop)

    root = tk.Tk()
    app = VideoStreamClient(root)
    open_connection_t.start()
    root.mainloop()
