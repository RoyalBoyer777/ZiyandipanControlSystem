import socket
import threading
import time


class UDPNode:
    def __init__(self, local_ip, local_port, remote_ip, remote_port, send_period=0.02):
        """
        send_period: 发送周期（秒），默认20ms
        """
        self.local_addr = (local_ip, local_port)
        self.remote_addr = (remote_ip, remote_port)

        self.send_period = send_period

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.local_addr)

        self.running = False

        # 发送缓存（线程安全）
        self.send_data = b''
        self.lock = threading.Lock()

    # ===============================
    # 对外接口：更新发送数据
    # ===============================
    def update_send_data(self, data: bytes):
        with self.lock:
            self.send_data = data

    # ===============================
    # 发送线程
    # ===============================
    def send_loop(self):
        print("UDP send thread started")
        while self.running:
            with self.lock:
                data = self.send_data

            if data:
                try:
                    self.sock.sendto(data, self.remote_addr)
                except Exception as e:
                    print(f"[UDP SEND ERROR] {e}")

            time.sleep(self.send_period)

    # ===============================
    # 接收线程
    # ===============================
    def recv_loop(self):
        print("UDP recv thread started")
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                self.handle_recv(data, addr)
            except Exception as e:
                print(f"[UDP RECV ERROR] {e}")

    # ===============================
    # 接收处理（可重写）
    # ===============================
    def handle_recv(self, data, addr):
        print(f"[UDP RX] from {addr}: {data.hex()}")

    # ===============================
    # 启动
    # ===============================
    def start(self):
        self.running = True

        self.t_send = threading.Thread(target=self.send_loop, daemon=True)
        self.t_recv = threading.Thread(target=self.recv_loop, daemon=True)

        self.t_send.start()
        self.t_recv.start()

    # ===============================
    # 停止
    # ===============================
    def stop(self):
        self.running = False
        self.sock.close()