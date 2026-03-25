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

        #车辆控制指令
        self._velocity_cmd_kmh = 0  #车辆速度命令（受拨杆控制）
        self._steering_cmd = 0  #转向角度命令（受拨杆控制）
        self._vehicle_actual_speed_kmh = 0  # 车辆速度（由正运动学计算得到）
        self._vehicle_actual_steering_angle = 0  # 车辆实际转向角度（由正运动学计算得到）
        self._wheel_state = {   #轮子状态 
            "deltaL": 0,
            "deltaR": 0,
            "wRL_rpm": 0,
            "wRR_rpm": 0,
            "radius": 0
        }
        self._remote_state = {}  #遥控器状态（急停、停车、遥控模式等）
        self._left_wheel_speed_rpm, self._right_wheel_speed_rpm = 0, 0  #左右轮速度rpm（由逆运动学计算得到）

    def compute_steering_angle(self, steering_cmd):  #从转向角度转换为转向器的转向角度
        
        SteeringRad = steering_cmd * 3.1415926 / 180.0 # 转向角度 (弧度)
        # 轮子角度 -> 拉杆位移
        RackTravel_mm = self.vehicle_params.Ls_mm * SteeringRad           # 拉杆位移 (mm)
        # 拉杆位移 -> 转向器角度
        SteerAngle_deg = (RackTravel_mm / self.vehicle_params.Pitch_mm) * 360.0  # 转向器角度 (度)
        return SteerAngle_deg



    def start(self):
        # 读取遥控器状态
        self._remote_state = self.remote.get_state()
        if self._remote_state.get('estop', False):
            # 急停状态，执行急停逻辑
            self.motorL.set_velocity(0)
            self.motorR.set_velocity(0)
            self.steerFront.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            self.steerRear.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            return
        if self._remote_state.get('parking', False):
            # 停车状态，执行停车逻辑
            self.motorL.set_velocity(0)
            self.motorR.set_velocity(0)
            self.steerFront.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            self.steerRear.set_steering(angle=0, angle_spd=100, veh_spd=0, enable=False)
            
            if self.motorL.get_actual_velocity() == 0 and self.motorR.get_actual_velocity() == 0:
                self.brake.apply(parking_button=True)  # 施加驻车制动

            return

        # 解析遥控器速度和转向命令
        self._velocity_cmd_kmh = self.remote.get_velocity_cmd()  #车体速度值km/h
        self._steering_cmd = self.remote.get_steer_cmd()     #转向命令值（-20°到+20°）

        # 转向执行
        self.steerFront.set_steering(
            angle=self.compute_steering_angle(self._steering_cmd),
            angle_spd=100,
            veh_spd=abs(self._velocity_cmd_kmh),
            enable=True
        )
        self.steerRear.set_steering(
            angle=-self.compute_steering_angle(self._steering_cmd),  # 后轮反向
            angle_spd=100,
            veh_spd=abs(self._velocity_cmd_kmh),
            enable=True
        )

        #逆运动学计算（从车体速度和转向角计算左右轮速度）
        self._left_wheel_speed_rpm, self._right_wheel_speed_rpm = self.ackermann_inverse_kinematics.compute(
            v_kmh=self._velocity_cmd_kmh,
            delta_rad=self._steering_cmd * 3.1415926 / 180.0,
            Dir_LR=self.remote.get_left_right()
        )

        #驱动电机执行
        self.motorL.set_velocity(self._left_wheel_speed_rpm)
        self.motorR.set_velocity(self._right_wheel_speed_rpm)

        # 正运动学计算
        self._vehicle_actual_speed_kmh, self._vehicle_actual_steering_angle = self.ackermann_kinematics.compute(
            ActVel_RL=self.motorL.get_actual_velocity(),
            ActVel_RR=self.motorR.get_actual_velocity(),
            SteerAngle=self._steering_cmd
        )
        self.remote.send_feedback(
            vehicle_speed=self._vehicle_actual_speed_kmh,
            battery=self.bms.get_soc()
        )
