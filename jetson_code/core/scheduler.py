from devices.motor import MotorNode
from devices.remote import RemoteNode
from devices.bms import BMSController
from devices.brake import BrakeController
from devices.steer import SteeringController
from config.vehicle_params import VehicleParams
from modules.kinematics import AckermannKinematics, AckermannInverseKinematics
from modules.remote_control import RemoteControlSystem
from modules.auto_drive import AutoDriveSystem
from drivers.udp_comm import UDPNode

import can
import canopen

class Scheduler:
    def __init__(self):
        # 初始化CAN总线和CANOpen网络
        self.can_bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=500000)
        self.canopen_network = canopen.Network()
        self.canopen_network.connect(channel='can0', bustype='socketcan', bitrate=500000)

        #创建CANopen各类节点对象
        self.remote_node = RemoteNode(self.canopen_network, node_id=3, eds_file='config/C6049.eds')
        self.motorL_node = MotorNode(self.canopen_network, node_id=1, eds_file='config/motor.eds')
        self.motorR_node = MotorNode(self.canopen_network, node_id=2, eds_file='config/motor.eds')
        
        #创建CAN总线各类节点对象
        self.bms = BMSController(self.can_bus)
        self.brake = BrakeController(self.can_bus)  
        self.steerFront = SteeringController(self.can_bus, CAN_ID=0x169)
        self.steerRear = SteeringController(self.can_bus, CAN_ID=0x179)

        #udp通信对象（与智能驾驶层通信）
        self.udp_node = UDPNode(local_ip='192.168.100.110', local_port=4002, remote_ip='192.168.100.10', remote_port=8002)
        
        # 正逆运动学模型
        self.ackermann_kinematics = AckermannKinematics()
        self.ackermann_inverse_kinematics = AckermannInverseKinematics()

        #车辆参数节点
        self.vehicle_params = VehicleParams()

        self.remote_control_system = RemoteControlSystem(
            remote_node=self.remote_node, 
            motorL_node=self.motorL_node, 
            motorR_node=self.motorR_node,
            bms=self.bms,
            brake=self.brake,
            steerFront=self.steerFront,
            steerRear=self.steerRear,
            ackermann_kinematics=self.ackermann_kinematics,
            ackermann_inverse_kinematics=self.ackermann_inverse_kinematics,
            vehicle_params=self.vehicle_params
        )
        self.auto_drive_system = AutoDriveSystem(
            udp_node=self.udp_node,
            remote_node=self.remote_node,
            motorL_node=self.motorL_node,
            motorR_node=self.motorR_node,
            bms=self.bms,
            brake=self.brake,
            steerFront=self.steerFront,
            steerRear=self.steerRear,
            ackermann_kinematics=self.ackermann_kinematics,
            ackermann_inverse_kinematics=self.ackermann_inverse_kinematics,
            vehicle_params=self.vehicle_params
        )

    def start(self):
        # 启动调度器，管理遥控和自动驾驶系统
        remote_state = self.remote_node.get_state()
        if remote_state.get('remote_mode', False):
            self.remote_control_system.start()
        else:
            # 进入自动驾驶模式
            self.auto_drive_system.start()

    def stop(self):
        # 停止调度器，关闭遥控和自动驾驶系统
        pass