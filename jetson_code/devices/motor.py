import can
import canopen
import time

class MotorNode:
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

    #这个函数应该在主程序中，在创建MotorNode实例后调用一次，进入OPERATIONAL状态，不要调用，直接使用node.nmt.state = 'OPERATIONAL'
    #后期在主程序中调用这个函数，或者直接在主程序中设置node.nmt.state = 'OPERATIONAL'，就不需要这个函数了
    def start_node(self):
        print("NMT: Start node")
        self.node.nmt.state = 'OPERATIONAL'
        time.sleep(0.5)

    def enable_motor(self):
        print("Motor enable sequence...")

        # 进入速度模式
        self.node.sdo['Modes of operation'].raw = 3

        # 状态机
        self.node.sdo['Controlword'].raw = 0x06
        time.sleep(0.1)

        self.node.sdo['Controlword'].raw = 0x07
        time.sleep(0.1)

        self.node.sdo['Controlword'].raw = 0x0F
        time.sleep(0.1)

        print("Motor enabled")

    def set_velocity(self, velocity):
        """
        velocity: 单位根据电机定义（一般 rpm 或者 0.1rpm）
        """

        # RPDO1发送
        rpdo = self.node.rpdo[1]

        rpdo['Target Velocity'].raw = velocity
        rpdo['Controlword'].raw = 0x0F
        rpdo['Modes of operation'].raw = 3

        rpdo.transmit()

    def stop_motor(self):
        print("Stopping motor...")
        self.set_velocity(0)

    def read_feedback(self):
        tpdo = self.node.tpdo[1]

        status = tpdo['Statusword'].raw
        mode_display = tpdo['Modes Of Operation Display'].raw

        print(f"Statusword: {hex(status)}, Mode: {mode_display}")

        tpdo2 = self.node.tpdo[2]
        pos = tpdo2['Position Actual Value'].raw
        vel = tpdo2['Velocity actual value'].raw

        print(f"Position: {pos}, Velocity: {vel}")

    def shutdown(self):
        self.network.disconnect()