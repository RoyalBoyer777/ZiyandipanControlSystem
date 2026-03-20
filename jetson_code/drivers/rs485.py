import serial
import threading
import time

class RS485:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1
        )

        # RS485模式（自动控制收发）
        try:
            self.ser.rs485_mode = serial.rs485.RS485Settings(
                rts_level_for_tx=True,
                rts_level_for_rx=False,
                delay_before_tx=0,
                delay_before_rx=0
            )
            print("RS485 mode enabled")
        except:
            print("RS485 mode not supported, using normal UART")

        self.running = False

    # ======================
    # 发送函数
    # ======================
    def send(self, data: bytes):
        if self.ser.is_open:
            self.ser.write(data)
            print(f"[TX] {data.hex()}")

    # ======================
    # 接收线程
    # ======================
    def receive_loop(self):
        while self.running:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting)
                print(f"[RX] {data.hex()}")
            time.sleep(0.01)

    # ======================
    # 启动接收
    # ======================
    def start(self):
        self.running = True
        self.rx_thread = threading.Thread(target=self.receive_loop)
        self.rx_thread.daemon = True
        self.rx_thread.start()

    # ======================
    # 停止
    # ======================
    def stop(self):
        self.running = False
        self.rx_thread.join()
        self.ser.close()


# ======================
# 主程序
# ======================
if __name__ == "__main__":
    rs485 = RS485(port="COM3", baudrate=115200)

    rs485.start()

    try:
        while True:
            # 示例发送数据（你可以替换为自己的协议）
            tx_data = bytes.fromhex("01 03 00 00 00 02 C4 0B")  # 类似Modbus
            rs485.send(tx_data)

            time.sleep(1)  # 周期发送（1秒）

    except KeyboardInterrupt:
        print("Stopping...")
        rs485.stop()