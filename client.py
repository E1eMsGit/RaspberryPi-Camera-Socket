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
import tkinter as tk
from threading import Thread
from tkinter import messagebox

import cv2 as cv
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
        # Status index - 1 = Attempting to connect to the server...
        self.status_index = 1

        # Flag for start put image to self.video_image_q queue.
        self.start_write_video_file = False
        # Flag for create and start new thread for writing video file.
        self.create_new_thread = True
        # List of write video file threads.
        self.write_file_threads = []

        # Queue for status of write or stop writing video file.
        self.file_writing_status_q = queue.Queue()
        # Queue for video images for writing video file.
        self.video_image_q = queue.Queue()

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

        self.video_lbl = tk.Label(self.video_frame, bd=2, relief="groove",
                                  width=720, height=576, font=self.font)

        self.record_btn = tk.Button(self.control_frame,
                                    command=self.start_stop_recording,
                                    font=self.font, text="Start recording",
                                    height=50, width=27)
        self.snapshot_btn = tk.Button(self.control_frame, font=self.font,
                                      command=self.make_snapshot,
                                      text="Snapshot", height=50)

        for frame in [self.video_frame, self.control_frame]:
            frame.pack(padx=10, pady=10)
            frame.pack_propagate(0)

        self.video_lbl.pack(padx=10, pady=10)
        self.record_btn.pack(side='left', padx=5, pady=5)
        self.snapshot_btn.pack(fill='x', padx=5, pady=5)

        self.checking_connection_status()

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

        cv.imwrite(path, cv.cvtColor(self.camera_data, cv.COLOR_BGR2RGB))

    def start_stop_recording(self):
        """
        Create catalog for video files if its not exists,
        start write video stream thread if self.write_video_stream_flag is True.
        :return:
        """
        if not os.path.exists("Video"):
            os.mkdir(os.path.join(self.bundle_dir, "Video"))

        if self.create_new_thread is True:
            self.record_btn.configure(text="Stop recording")
            thread = Thread(target=self.recording)
            self.write_file_threads.append(thread)
            self.write_file_threads[-1].start()
        else:
            self.record_btn.configure(text="Start recording")
            self.file_writing_status_q.put(False)
            self.write_file_threads[-1].join()

        self.start_write_video_file = not self.start_write_video_file
        self.create_new_thread = not self.create_new_thread

    def recording(self):
        """
        Function for write video stream in file thread.
        Get date and time, write video file in Video catalog.
        :return:
        """
        write_status = True
        ts = datetime.datetime.now()
        filename = "{}.avi".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        path = os.path.sep.join(("Video", filename))

        fps = 25.0
        resolution = (720, 576)
        four_cc = cv.VideoWriter_fourcc(*'MJPG')
        video = cv.VideoWriter(path, four_cc, fps, resolution)

        while write_status is True:
            if not self.video_image_q.empty():
                video_image = self.video_image_q.get()
                self.video_image_q.task_done()
                video.write(cv.cvtColor(video_image, cv.COLOR_BGR2RGB))
            if not self.file_writing_status_q.empty():
                write_status = self.file_writing_status_q.get()
                self.file_writing_status_q.task_done()

    def checking_connection_status(self):
        """
        Check socket connection status.
        :return:
        """
        connection_status = {0: "Connection complete",
                             1: "Attempting to connect to the server...",
                             2: "Server is not running. Connection fail"}

        if not connection_status_q.empty():
            self.status_index = connection_status_q.get()
            connection_status_q.task_done()
        else:
            if self.status_index in [1, 2]:
                self.video_lbl.configure(
                    text=connection_status.get(self.status_index))
                self.record_btn.configure(state="disabled")
                self.snapshot_btn.configure(state="disabled")
            elif self.status_index == 0:
                self.record_btn.configure(state="normal")
                self.snapshot_btn.configure(state="normal")

                self.camera_data = video_image_q.get()
                video_image_q.task_done()

                if self.start_write_video_file is True:
                    self.video_image_q.put(self.camera_data)

                # Update image in self.video_label.
                a = Image.fromarray(self.camera_data)
                b = ImageTk.PhotoImage(image=a)
                self.video_lbl.configure(image=b)

        self.master.update()
        self.master.after(0, func=lambda: self.checking_connection_status())

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
        connection_status = 0
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
    # Flag for stop receiving video stream.
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
            bgr_video_image = cv.imdecode(data, 1)
            rgb_video_image = cv.cvtColor(bgr_video_image, cv.COLOR_BGR2RGB)

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

    open_connection_t = Thread(target=open_connection)
    get_video_stream_t = Thread(target=get_video_image_loop)

    root = tk.Tk()
    app = VideoStreamClient(root)
    open_connection_t.start()
    root.mainloop()
