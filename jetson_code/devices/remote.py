import canopen
import time

class Remote:
    def __init__(self, channel='can0', bitrate=500000, node_id=1, eds_file='motor.eds'):
        self.network = canopen.Network()
        self.network.connect(channel=channel, bustype='socketcan', bitrate=bitrate)

        self.node = self.network.add_node(node_id, eds_file)

        # 映射PDO（使用EDS自动解析）
        self.node.tpdo.read()
        self.node.rpdo.read()

        # 启用PDO
        for pdo in self.node.tpdo.values():
            pdo.enabled = True
        for pdo in self.node.rpdo.values():
            pdo.enabled = True

    def start_node(self):
        print("NMT: Start node")
        self.node.nmt.state = 'OPERATIONAL'
        time.sleep(0.5)


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
