from modules.can_protocol import FB_CAN_CCU, FB_CAN_SCU_1
import struct

class AutoDriveSystem:
    def __init__(self, 
                 udp_node,
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
        self.remote = remote_node
        self.motorL = motorL_node
        self.motorR = motorR_node
        self.bms = bms
        self.brake = brake
        self.steerFront = steerFront
        self.steerRear = steerRear
        self.ackermann_kinematics = ackermann_kinematics
        self.ackermann_inverse_kinematics = ackermann_inverse_kinematics
        self.vehicle_params = vehicle_params

        # CAN数据打包和拆包对象
        self.can_packer_ccu = FB_CAN_CCU()
        self.can_depacker_scu_1 = FB_CAN_SCU_1()

        #udp通信对象（与智能驾驶层通信）
        self.udp_node = udp_node
        self.udp_node.start()
    
    def compute_steering_angle(self, steering_cmd):  #从前轮转角计算转向器的转向角度
        SteeringRad = steering_cmd * 3.1415926 / 180.0 # 转向角度 (弧度)
        # 轮子角度 -> 拉杆位移
        RackTravel_mm = self.vehicle_params.Ls_mm * SteeringRad           # 拉杆位移 (mm)
        # 拉杆位移 -> 转向器角度
        SteerAngle_deg = (RackTravel_mm / self.vehicle_params.Pitch_mm) * 360.0  # 转向器角度 (度)
        return SteerAngle_deg


    def compute_steering_angle_from_scu(self, steering_raw):  #将SCU前轮转角数据值（0-255）转为为转向器的转向角度
        Steer_angle = -20 + steering_raw / 255.0 * 40  #将转向角度限制在-20°到+20°之间
        return Steer_angle
    
    def start(self):
        SCU_CAN_frame = self.udp_node.get_data()  # 从智能驾驶层接收CAN帧
        CAN_ID = struct.unpack('>I', SCU_CAN_frame[1:5])[0]  # 提取CAN ID（大端）
        if CAN_ID == 0x51:  # 来自智能驾驶层的底盘控制报文
            control_signals = self.can_depacker_scu_1.parse(SCU_CAN_frame)
        
        # 解析control_signals
        Drive_Mode_Req = control_signals.get("SCU_Drive_Mode_Req", 0)
        if Drive_Mode_Req == 0x02:  # 遥控模式
            # 计算遥控模式下的控制指令
            return
        Vehicle_speed_kmh_cmd = control_signals.get("SCU_Target_Speed", 0)
        Steering_wheel_raw = control_signals.get("SCU_Steering_Wheel_Angle_F", 0)  # 前轮转向角度(0-255)
        Steering_wheel_angle_cmd = self.compute_steering_angle_from_scu(Steering_wheel_raw)  # 将前轮转角数据值转为前轮转向角度
        Brake_enable = control_signals.get("SCU_Brk_En", 0)                     # 是否使能刹车
        Left_turn_light = control_signals.get("GW_Left_Turn_Light_Req", 0)      #左转向灯
        Right_turn_light = control_signals.get("GW_Right_Turn_Light_Req", 0)    #右转向灯
        Position_light = control_signals.get("GW_Position_Light_Req", 0)        #刹车灯
        LowBeam = control_signals.get("GW_LowBeam_Req", 0)                      #近光灯

        #逆运动学计算，从车体速度及前轮转角计算左右轮速度及转向器转角
        Wheel_RR_RPM, Wheel_RL_RPM = self.ackermann_inverse_kinematics.compute(
            v_kmh=Vehicle_speed_kmh_cmd,
            delta_rad=Steering_wheel_angle_cmd * 3.1415926 / 180.0,
            Dir_LR=Steering_wheel_raw
        )
        if Brake_enable:
            Wheel_RR_RPM = 0
            Wheel_RL_RPM = 0
            if self.motorL.get_actual_velocity() == 0 and self.motorR.get_actual_velocity() == 0:
                self.brake.apply(parking_button=True)  # 施加驻车制动
        
        if Left_turn_light:
            pass
        if Right_turn_light:
            pass
        if Position_light:
            pass
        if LowBeam:
            pass


        #驱动电机及转向执行
        self.motorL.set_velocity(Wheel_RL_RPM)
        self.motorR.set_velocity(Wheel_RR_RPM)
        self.steerFront.set_steering(
            angle=self.compute_steering_angle(Steering_wheel_angle_cmd), 
            angle_spd=100, 
            veh_spd=abs(Vehicle_speed_kmh_cmd), 
            enable=True)
        self.steerRear.set_steering(
            angle=-self.compute_steering_angle(Steering_wheel_angle_cmd), 
            angle_spd=100, 
            veh_spd=abs(Vehicle_speed_kmh_cmd), 
            enable=True)
        
        # 正运动学计算，从左右轮速度及转向器转角计算车体实际速度及转向角
        Vehicle_speed_kmh_actual, Steering_wheel_angle_actual = self.ackermann_kinematics.compute(
            ActVel_RL=self.motorL.get_actual_velocity(),
            ActVel_RR=self.motorR.get_actual_velocity(),
            SteerAngle=Steering_wheel_angle_cmd
        )

        #执行完毕后对智能驾驶层进行反馈
        #将数据进行CAN帧打包
        CAN_CCU_Frame, CAN_CCU_Frame_data = self.can_packer_ccu.pack(
            CCU_ShiftLevel_Sts=1,   # 底盘档位
            CCU_P_Sts=1,    # 底盘刹车
            CCU_Ignition_Sts=1, # VCU点火状态
            CCU_Drive_Mode_Shift=0, # 驾驶模式切换按钮信号
            Steering_Wheel_Direction=0 if Steering_wheel_angle_actual > 0 else 1, # 左1右0
            CCU_Steering_Wheel_Angle=Steering_wheel_angle_actual, # 前轮转角，120对应实际角度27°或24°
            CCU_Vehicle_Speed=Vehicle_speed_kmh_actual,    # 车辆速度，单位km/h，乘以10后放大成整数
            CCU_Drive_Mode=0,   # 驾驶模式（0~3，各自代表什么意义）
            Remote_Brake=Brake_enable,  # 遥控器刹车信号
            Emergency_Brake=0,  # 紧急刹车信号
            SCU_Brake_Singal=Brake_enable,  # 自动驾驶模式刹车信号
            Left_Turn_Light_Sts=Left_turn_light,    # 左转向灯状态
            Right_Turn_Light_Sts=Right_turn_light,      # 右转向灯状态
            Position_Light_Sts=Position_light,        # 刹车灯状态
            LowBeam_Sts=LowBeam                       # 近光灯状态
        )

        # 将打包好的CAN帧发送回智能驾驶层
        self.udp_node.send(CAN_CCU_Frame_data)  



    def stop(self):
        # 停止自动驾驶逻辑
        pass
