import can


class BrakeController:
    def __init__(self, bus):
        self.bus = bus

        self.CAN_ID = 0x7B9

        # 状态
        self.parking_state = False
        self.last_button = False   # 用于上升沿检测

    # ==========================
    # 上升沿检测
    # ==========================
    def _rising_edge(self, current):
        rising = current and not self.last_button
        self.last_button = current
        return rising

    # ==========================
    # 核心更新（每周期调用）
    # ==========================
    def update(self, parking_button):
        """
        parking_button: 来自遥控器（True/False）
        """

        # ===== 上升沿触发 =====
        if self._rising_edge(parking_button):
            self.parking_state = not self.parking_state
            print(f"[Brake] ParkingState -> {self.parking_state}")

        # ===== 根据状态决定压力 =====
        if self.parking_state:
            pressure = 0x20
        else:
            pressure = 0x00

        # ===== 组CAN数据 =====
        data = [0] * 8
        data[0] = 0x06
        data[3] = pressure

        # ===== 发送 =====
        msg = can.Message(
            arbitration_id=self.CAN_ID,
            data=data,
            is_extended_id=False
        )

        self.bus.send(msg)

        return self.parking_state