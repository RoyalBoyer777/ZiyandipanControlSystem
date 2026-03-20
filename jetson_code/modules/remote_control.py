from devices.motor import MotorNode
from devices.remote import RemoteNode
from devices.bms import BMSController
from devices.brake import BrakeController
from devices.steer import SteeringController
from config.vehicle_params import VehicleParams

import can
import canopen

class RemoteControlSystem:
    def __init__(self):

        #初始化CAN总线对象，并传递给需要使用的类
        self.bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=500000)
        self.bms = BMSController(self.bus)  
        self.brake = BrakeController(self.bus)
        self.steerFront = SteeringController(self.bus)
        self.steerRear = SteeringController(self.bus)

        #初始化CANOpen网络对象，并传递给需要使用的类
        self.network = canopen.Network()
        self.network.connect(channel='can0', bustype='socketcan', bitrate=500000)

        self.remote = RemoteNode(self.network, node_id=3, eds_file='config/C6049.eds')
        self.motorL = MotorNode(self.network, node_id=1, eds_file='config/motor.eds')
        self.motorR = MotorNode(self.network, node_id=2, eds_file='config/motor.eds')

        # 车辆参数
        self.vehicle_params = VehicleParams()

    def update(self):
        # 读取遥控器状态