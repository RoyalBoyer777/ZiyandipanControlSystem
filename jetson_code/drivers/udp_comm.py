import socket
import threading
import time


class UDPNode:
    def __init__(self, local_ip, local_port, remote_ip, remote_port):
        # ---------- 网络参数 ----------
        self.local_ip = local_ip
        self.local_port = local_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port

        # ---------- Socket ----------
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_ip, self.local_port))
        self.sock.setblocking(False)

        # ---------- 线程控制 ----------
        self.running = False

        # ---------- 数据区（线程安全） ----------
        self.tx_lock = threading.Lock()
        self.rx_lock = threading.Lock()

        self.tx_data = b''
        self.rx_data = b''

        # ---------- 回调函数 ----------
        self.callback = None

    # ================= 对外接口 =================

    def start(self):
        """启动UDP线程"""
        self.running = True
        threading.Thread(target=self._send_loop, daemon=True).start()
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def stop(self):
        """停止"""
        self.running = False
        self.sock.close()

    def send(self, data: bytes):
        """发送数据（线程安全）"""
        with self.tx_lock:
            self.tx_data = data

    def get_data(self):
        """获取最新接收数据"""
        with self.rx_lock:
            return self.rx_data

    def register_callback(self, func):
        """注册接收回调函数"""
        self.callback = func

    # ================= 内部线程 =================

    def _send_loop(self):
        while self.running:
            try:
                with self.tx_lock:
                    if self.tx_data:
                        self.sock.sendto(self.tx_data, (self.remote_ip, self.remote_port))
            except Exception as e:
                print("Send error:", e)

            time.sleep(0.01)  # 10ms周期

    def _recv_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)

                with self.rx_lock:
                    self.rx_data = data

                # 回调（推荐方式）
                if self.callback:
                    self.callback(data, addr)

            except BlockingIOError:
                pass
            except Exception as e:
                print("Recv error:", e)

            time.sleep(0.001)