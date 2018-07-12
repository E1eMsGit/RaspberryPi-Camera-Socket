import io
import socket
import struct
import time

import picamera

while True:
    print("waiting connection...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 9090))
    server_socket.listen(1)
    connection, address = server_socket.accept()
    connection = connection.makefile("wb")
    print("connected:", address)

    with picamera.PiCamera() as camera:
        camera.resolution = (720, 576)
        camera.start_preview()
        time.sleep(2)

        stream = io.BytesIO()
        try:
            for foo in camera.capture_continuous(stream, "jpeg",
                                                 use_video_port=True):
                connection.write(struct.pack("<L", stream.tell()))
                connection.flush()
                stream.seek(0)
                connection.write(stream.read())
                stream.seek(0)
                stream.truncate()

        except socket.error as e:
            if e.errno == 32 or e.errno == 104 or e.errno == 10054:
                server_socket.close()
                print("Client disconnected")
