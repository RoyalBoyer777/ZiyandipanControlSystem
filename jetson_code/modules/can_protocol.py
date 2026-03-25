

#向智能驾驶层发送的底盘状态报文,打包
class FB_CAN_CCU:

    def __init__(self):
        pass

    def pack(self,
             CCU_ShiftLevel_Sts,  # 底盘档位状态（0~3）
             CCU_P_Sts,  # 底盘刹车状态
             CCU_Ignition_Sts,  # VCU点火状态
             CCU_Drive_Mode_Shift,  # 驾驶模式切换按钮信号
             Steering_Wheel_Direction,  # 转向方向（左1右.0）
             CCU_Steering_Wheel_Angle,  # 前轮转角，120对应实际角度27°或24°
             CCU_Vehicle_Speed,  # 车辆速度，单位km/h，乘以10后放大成整数
             CCU_Drive_Mode,   # 驾驶模式（0~3）
             Remote_Brake,  # 遥控器刹车信号
             Emergency_Brake,   # 紧急刹车信号
             SCU_Brake_Singal,  # 自动驾驶模式刹车信号
             Left_Turn_Light_Sts,   # 左转向灯状态
             Right_Turn_Light_Sts,  # 右转向灯状态
             Position_Light_Sts,    # 刹车灯状态
             LowBeam_Sts             # 近光灯状态
             ):  

        # ==========================================
        # 1. 打包64bit
        # ==========================================
        Raw64 = 0

        # bit 0~1
        Raw64 |= (CCU_ShiftLevel_Sts & 0x03) << 0

        # bit 2
        if CCU_P_Sts:
            Raw64 |= (1 << 2)

        # bit 3~4
        Raw64 |= (CCU_Ignition_Sts & 0x03) << 3

        # bit 5
        if CCU_Drive_Mode_Shift:
            Raw64 |= (1 << 5)

        # bit 7
        if Steering_Wheel_Direction:
            Raw64 |= (1 << 7)

        # bit 8~19 (12bit)
        angle_raw = int(CCU_Steering_Wheel_Angle * 10.0)
        Raw64 |= (angle_raw & 0x0FFF) << 8

        # bit 20~28 (9bit)
        speed_raw = int(CCU_Vehicle_Speed * 10.0)
        Raw64 |= (speed_raw & 0x1FF) << 20

        # bit 29~31
        Raw64 |= (CCU_Drive_Mode & 0x07) << 29

        # bit 32
        if Remote_Brake:
            Raw64 |= (1 << 32)

        # bit 33
        if Emergency_Brake:
            Raw64 |= (1 << 33)

        # bit 34
        if SCU_Brake_Singal:
            Raw64 |= (1 << 34)

        # bit 56
        if Left_Turn_Light_Sts:
            Raw64 |= (1 << 56)

        # bit 57
        if Right_Turn_Light_Sts:
            Raw64 |= (1 << 57)

        # bit 59
        if Position_Light_Sts:
            Raw64 |= (1 << 59)

        # bit 60
        if LowBeam_Sts:
            Raw64 |= (1 << 60)

        # ==========================================
        # 2. 拆成8字节（Little Endian）
        # ==========================================
        data = [(Raw64 >> (8 * i)) & 0xFF for i in range(8)]

        # ==========================================
        # 3. 组完整帧（13字节）由于python发送can时只需要8字节数据区，所以这里直接返回data即可
        # ==========================================
        
        TxFrame = [0] * 13

        # DLC
        TxFrame[0] = 0x08

        # CAN ID = 0x51（低字节）
        TxFrame[1] = 0x00
        TxFrame[2] = 0x00
        TxFrame[3] = 0x00
        TxFrame[4] = 0x51

        # Data区
        for i in range(8):
            TxFrame[5 + i] = data[i]

        return TxFrame, data

#来自智能驾驶层发送的底盘控制报文解析
class FB_CAN_SCU_1:

    def __init__(self):
        pass

    def parse(self, raw_frame):
        """
        raw_frame: 长度13的list（对应你的RawFrame）
        return: dict（所有解析信号）
        """

        # ==========================================
        # 1. 提取8字节数据区
        # ==========================================
        data = raw_frame[5:13]  # Data[0..7]

        # ==========================================
        # 2. Little-Endian → 拼64bit
        # ==========================================
        Raw64 = 0
        for i in range(8):
            Raw64 |= data[i] << (8 * i)

        # ==========================================
        # 3. 按bit解析
        # ==========================================
        result = {}

        # Startbit 0, Len 2
        result["SCU_ShiftLevel_Req"] = (Raw64 >> 0) & 0x03

        # Startbit 6, Len 2
        result["SCU_Drive_Mode_Req"] = (Raw64 >> 6) & 0x03

        # Startbit 8, Len 8
        result["SCU_Steering_Wheel_Angle_F"] = (Raw64 >> 8) & 0xFF

        # Startbit 16, Len 8
        result["SCU_Steering_Wheel_Angle_R"] = (Raw64 >> 16) & 0xFF

        # Startbit 24, Len 9
        speed_raw = (Raw64 >> 24) & 0x1FF
        result["SCU_Target_Speed"] = speed_raw * 0.1

        # Startbit 33, Len 1
        result["SCU_Brk_En"] = ((Raw64 >> 33) & 0x01) == 1

        # Startbit 40, Len 2
        result["GW_Left_Turn_Light_Req"] = (Raw64 >> 40) & 0x03

        # Startbit 42, Len 2
        result["GW_Right_Turn_Light_Req"] = (Raw64 >> 42) & 0x03

        # Startbit 46, Len 2
        result["GW_Position_Light_Req"] = (Raw64 >> 46) & 0x03

        # Startbit 48, Len 2
        result["GW_LowBeam_Req"] = (Raw64 >> 48) & 0x03

        # bit 60（两个信号复用）
        # bit60 = (Raw64 >> 60) & 0x01

        # result["angular_speed_flag"] = int(bit60)   # 0/1
        # result["SCU_Brake_Force_Flag"] = (bit60 == 1)

        return result
    

#转向控制帧（VCU_SES_Req），打包
class FB_CAN_VCU_SES_Req:

    def __init__(self):
        self.roll_cnt = 0  # 对应PLC里的RollCnt（必须保存状态）

    def pack(self,
             Tgt_StrAngle,
             Tgt_StrAngleSpd,
             Veh_Spd,
             Enable):

        # ==========================================
        # 1. 物理量 → 原始值
        # ==========================================

        # 角度：Phys = Raw*0.1 - 3000
        raw_angle = int((Tgt_StrAngle + 3000.0) / 0.1) & 0xFFFF

        # 角速度
        raw_spd = int(Tgt_StrAngleSpd) & 0xFFFF

        # ==========================================
        # 2. 清空数据
        # ==========================================
        data = [0] * 8

        # ==========================================
        # 3. Byte0：控制位
        # ==========================================
        if Enable:
            data[0] = 0x02
        else:
            data[0] = 0x00

        # ==========================================
        # 4. 转向角（Motorola 大端）
        # ==========================================
        data[1] = (raw_angle >> 8) & 0xFF
        data[2] = raw_angle & 0xFF

        # ==========================================
        # 5. 转向角速度（Motorola 大端）
        # ==========================================
        data[3] = (raw_spd >> 8) & 0xFF
        data[4] = raw_spd & 0xFF

        # ==========================================
        # 6. Byte5：Rolling Counter + Enable
        # ==========================================
        data[5] = 0x03 | ((self.roll_cnt & 0x0F) << 4)

        # ==========================================
        # 7. Byte6：车速
        # ==========================================
        data[6] = Veh_Spd & 0xFF

        # ==========================================
        # 8. Checksum
        # ==========================================
        checksum = sum(data[0:7]) & 0xFF
        data[7] = checksum ^ 0xFF

        # ==========================================
        # 9. Rolling Counter 自增
        # ==========================================
        self.roll_cnt = (self.roll_cnt + 1) & 0x0F

        return data

