# import can
# import threading
# from collections import deque


# class CANBus:
#     def __init__(self, channel='can0', bitrate=500000):
#         self.bus = can.interface.Bus(
#             channel=channel,
#             bustype='socketcan',
#             bitrate=bitrate
#         )

#         self.running = False

#         # 接收缓存
#         self.rx_queue = deque(maxlen=1000)

#         # 回调（所有协议共用）
#         self.callbacks = []

#         self.lock = threading.Lock()

#     # ==========================
#     # 发送
#     # ==========================
#     def send(self, can_id, data, extended=False):
#         msg = can.Message(
#             arbitration_id=can_id,
#             data=data,
#             is_extended_id=extended
#         )
#         try:
#             self.bus.send(msg)
#             print(f"[CAN TX] {hex(can_id)} {data.hex()}")
#         except can.CanError as e:
#             print(f"[CAN ERROR] {e}")

#     # ==========================
#     # 接收线程
#     # ==========================
#     def _rx_loop(self):
#         while self.running:
#             msg = self.bus.recv(timeout=0.1)
#             if msg:
#                 with self.lock:
#                     self.rx_queue.append(msg)

#                 print(f"[CAN RX] {hex(msg.arbitration_id)} {msg.data.hex()}")

#                 for cb in self.callbacks:
#                     cb(msg)

#     # ==========================
#     def start(self):
#         self.running = True
#         self.thread = threading.Thread(target=self._rx_loop)
#         self.thread.daemon = True
#         self.thread.start()

#     def stop(self):
#         self.running = False
#         self.thread.join()

#     # ==========================
#     # 注册回调
#     # ==========================
#     def add_callback(self, func):
#         self.callbacks.append(func)

#     # ==========================
#     # 按ID获取最新数据
#     # ==========================
#     def get_latest(self, can_id):
#         with self.lock:
#             for msg in reversed(self.rx_queue):
#                 if msg.arbitration_id == can_id:
#                     return msg
#         return None