from devices.motor import MotorNode
from devices.remote import RemoteNode
from devices.bms import BMSController
from devices.brake import BrakeController
from devices.steer import SteeringController
from config.vehicle_params import VehicleParams
from modules.kinematics import AckermannKinematics, AckermannInverseKinematics




class RemoteControlSystem:
    def __init__(self, 
                 remote_node, 
                 motorL_node, 
                 motorR_node, 
                 bms, 
                 brake, 
                 steerFront, 
                 steerRear, 
                 ackermann_kinematics, 
                 ackermann_inverse_kinematics,
                 vehicle_params
                 ):

        #初始化CAN总线对象，并传递给需要使用的类
        self.bms = bms
        self.brake = brake
        self.steerFront = steerFront
        self.steerRear = steerRear
        self.ackermann_kinematics = ackermann_kinematics
        self.ackermann_inverse_kinematics = ackermann_inverse_kinematics

        self.remote = remote_node
        self.motorL = motorL_node
        self.motorR = motorR_node

        # 车辆参数
        self.vehicle_params = vehicle_params
        self.max_steering_angle = self.vehicle_params.max_steering_angle  # 最大转向角度（度）

    def start(self):
        # 读取遥控器状态
        Remote_state = self.remote.get_state()
        if Remote_state.get('estop', False):
            # 急停状态，执行急停逻辑
            self.motorL.set_velocity(0)
            self.motorR.set_velocity(0)
            self.steerFront.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            self.steerRear.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            return
        if Remote_state.get('parking', False):
            # 停车状态，执行停车逻辑
            self.motorL.set_velocity(0)
            self.motorR.set_velocity(0)
            self.steerFront.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            self.steerRear.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            
            if self.motorL.get_actual_velocity() == 0 and self.motorR.get_actual_velocity() == 0:
                self.brake.apply(parking_button=True)  # 施加驻车制动

            return

        # 解析遥控器速度和转向命令
        #self._velocity_cmd_kmh = self.remote.get_velocity_cmd()  #车体速度值km/h
        Vehicle_speed_kmh_cmd = self.remote.get_velocity_cmd()
        #self._steering_cmd = self.remote.get_steer_cmd()     #转向命令值（-20°到+20°）
        Steering_angle_cmd = self.remote.get_steer_cmd()

        # 转向执行
        self.steerFront.set_steering(
            angle=Steering_angle_cmd,
            angle_spd=100,
            veh_spd=abs(Vehicle_speed_kmh_cmd),
            enable=True
        )
        self.steerRear.set_steering(
            angle=-Steering_angle_cmd,
            angle_spd=100,
            veh_spd=abs(Vehicle_speed_kmh_cmd),
            enable=True
        )

        #逆运动学计算（从车体速度和转向角计算左右轮速度）
        Left_wheel_speed_rpm, Right_wheel_speed_rpm = self.ackermann_inverse_kinematics.compute(
            v_kmh=Vehicle_speed_kmh_cmd,
            delta_rad=Steering_angle_cmd * 3.1415926 / 180.0,
            Dir_LR=self.remote.get_left_right()
        )

        #驱动电机执行
        self.motorL.set_velocity(Left_wheel_speed_rpm)
        self.motorR.set_velocity(Right_wheel_speed_rpm)

        # 正运动学计算
        Vehicle_actual_speed_kmh, Vehicle_actual_steering_angle = self.ackermann_kinematics.compute(
            ActVel_RL=self.motorL.get_actual_velocity(),
            ActVel_RR=self.motorR.get_actual_velocity(),
            SteerAngle=Steering_angle_cmd
        )
        self.remote.send_feedback(
            vehicle_speed=Vehicle_actual_speed_kmh,
            battery=self.bms.get_soc()
        )
