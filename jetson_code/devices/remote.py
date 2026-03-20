import canopen
import time

class RemoteNode:
    def __init__(self, network, node_id, eds_file):
        self.network = network
        self.node = self.network.add_node(node_id, eds_file)

        # 映射PDO（使用EDS自动解析）
        self.node.tpdo.read()
        self.node.rpdo.read()

        # 启用PDO
        for pdo in self.node.tpdo.values():
            pdo.enabled = True
        for pdo in self.node.rpdo.values():
            pdo.enabled = True


    # ==========================
    # TXPDO1：开关量解析
    # ==========================
    def is_estop(self):
        tpdo = self._read_tpdo1()
        if not tpdo:
            return True
        byte0 = tpdo.data[0]
        return bool(byte0 & (1 << 0))

    def is_remote_mode(self):
        tpdo = self._read_tpdo1()
        if not tpdo:
            return False
        byte1 = tpdo.data[1]
        return bool(byte1 & (1 << 2))

    def is_auto_mode(self):
        tpdo = self._read_tpdo1()
        if not tpdo:
            return False
        byte1 = tpdo.data[1]
        return bool(byte1 & (1 << 3))

    def is_parking(self):
        tpdo = self._read_tpdo1()
        if not tpdo:
            return False
        byte1 = tpdo.data[1]
        return bool(byte1 & (1 << 7))

    # ==========================
    # TXPDO2：模拟量解析
    # ==========================
    def get_speed_set(self):
        tpdo = self._read_tpdo2()
        if not tpdo:
            return 0
        return tpdo.data[0]

    def get_forward_back(self):
        tpdo = self._read_tpdo2()
        if not tpdo:
            return 127
        return tpdo.data[1]

    def get_left_right(self):
        tpdo = self.node.tpdo[2]
        return tpdo.data[2]

    # ==========================
    # 高级接口
    # ==========================
    def get_velocity_cmd(self):
        speed = self.get_speed_set()
        fb = self.get_forward_back()

        direction = (fb - 127) / 127.0
        return speed * direction

    def get_steer_cmd(self):
        lr = self.get_left_right()
        return (lr - 127) / 127.0

    # ==========================
    # 状态汇总
    # ==========================
    def get_state(self):
        return {
            "estop": self.is_estop(),
            "remote_mode": self.is_remote_mode(),
            "auto_mode": self.is_auto_mode(),
            "parking": self.is_parking(),
            "speed_cmd": self.get_velocity_cmd(),
            "steer_cmd": self.get_steer_cmd()
        }

    # ==========================
    # RXPDO：回传数据
    # ==========================
    def send_feedback(self, battery, speed_kmh):
        rpdo = self.node.rpdo[1]

        battery = max(0, min(100, int(battery)))
        speed_disp = max(0, min(150, int(speed_kmh * 10)))

        rpdo.data = bytearray([
            battery,
            speed_disp,
            0, 0, 0, 0, 0, 0
        ])

        rpdo.transmit()