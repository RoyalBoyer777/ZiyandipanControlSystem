import can

class BMSController:
    def __init__(self, bus):
        # 初始化CAN接口
        self.bus = bus
    

        # 状态缓存
        self.state = {
            "voltage": 0.0,  # V
            "current": 0.0,  # A
            "soc": 0         # %
        }

    def recv(self, timeout=0.01):
        """
        接收一帧CAN消息并解析
        """
        msg = self.bus.recv(timeout)
        if msg is None:
            return

        # 只解析ID 0x444
        if msg.arbitration_id == 0x444:
            self._parse_0x444(msg.data)

    def _parse_0x444(self, data):
        """
        Byte解析规则：
        - Byte0 + Byte1：总电压 0~4000 → 0~400V
        - Byte2 + Byte3：总电流 0~1000 → -500~500A
        - Byte6：SOC 0~100 → 0~100%
        """
        # 总电压
        raw_voltage = data[0] | (data[1] << 8)
        voltage = raw_voltage * 0.1  # 0~4000 -> 0~400V
        self.state["voltage"] = voltage

        # 总电流
        raw_current = data[2] | (data[3] << 8)
        current = (raw_current / 1000.0) * 1000 - 500  # 映射 -500~500A
        self.state["current"] = current

        # SOC
        soc = data[6]
        self.state["soc"] = soc

    # 对外接口
    def get_voltage(self):
        return self.state["voltage"]

    def get_current(self):
        return self.state["current"]

    def get_soc(self):
        return self.state["soc"]


# ===========================
# 示例：循环读取
# ===========================
if __name__ == "__main__":
    bms = BMSController()

    while True:
        bms.recv()
        print(f"Voltage: {bms.get_voltage():.1f} V, "
              f"Current: {bms.get_current():.1f} A, "
              f"SOC: {bms.get_soc()}%")