import math

class AckermannKinematics:

    def __init__(self):
        # 参数（可以后面改成config）
        self.L = 1.4            # 轴距
        self.wheel_radius = 0.245
        self.track_width = 1.150
        self.eps = 1e-6

    def compute(self,
                ActVel_RL,     # rpm
                ActVel_RR,     # rpm
                SteerAngle_FL, # rad（当前版本未使用）
                SteerAngle_FR, # rad（当前版本未使用）
                radius):       # 转弯半径

        # ==========================================
        # 1. 速度取绝对值（对标ST）
        # ==========================================
        ActVel_RL = abs(ActVel_RL)
        ActVel_RR = abs(ActVel_RR)

        # ==========================================
        # 2. rpm → m/s
        # ==========================================
        v_RL = ActVel_RL / 60.0 * 2.0 * math.pi * self.wheel_radius
        v_RR = ActVel_RR / 60.0 * 2.0 * math.pi * self.wheel_radius

        # ==========================================
        # 3. 计算前轮转角（Ackermann几何）
        # ==========================================
        # 防止radius=0
        if abs(radius) < self.eps:
            radius = self.eps

        delta_L = math.atan((self.L / 2.0) / (radius - self.track_width / 2.0))
        delta_R = math.atan((self.L / 2.0) / (radius + self.track_width / 2.0))

        # ==========================================
        # 4. cos补偿
        # ==========================================
        cosL = math.cos(delta_L)
        cosR = math.cos(delta_R)

        # 防止数值爆炸
        if cosL < 0.05:
            cosL = 0.05
        if cosR < 0.05:
            cosR = 0.05

        # ==========================================
        # 5. 车速（km/h）
        # ==========================================
        vehicle_speed = (v_RL * cosL + v_RR * cosR) / 2.0 * 3.6

        # ==========================================
        # 6. 中心转向角
        # ==========================================
        delta = math.atan((self.L / 2.0) / radius)

        return vehicle_speed, delta
    

class AckermannInverseKinematics:

    def __init__(self):
        self.L = 1.4          # 轴距
        self.W = 1.150        # 轮距
        self.rRL = 0.245      # 左后轮半径
        self.rRR = 0.245      # 右后轮半径
        self.eps = 1e-6

    def compute(self, v_kmh, delta, Dir_LR):
        """
        v_kmh : 车体速度 km/h
        delta : 等效前轮转角 rad
        Dir_LR: 转向方向（2=右转，其它默认左转）
        """

        # ==========================================
        # 1. km/h → m/s
        # ==========================================
        v_ms = v_kmh / 3.6

        # 初始化
        deltaL = 0.0
        deltaR = 0.0
        radius = 0.0

        # ==========================================
        # 2. 直行情况
        # ==========================================
        if abs(delta) < self.eps:
            radius = 1.0e12
            psiDot = 0.0

            deltaL = 0.0
            deltaR = 0.0

            vRL = v_ms
            vRR = v_ms

        # ==========================================
        # 3. 转弯情况
        # ==========================================
        else:
            radius = abs(self.L / math.tan(delta))   # 自行车模型
            psiDot = v_ms / radius                   # 偏航角速度

            # Ackermann几何
            deltaL = math.atan((self.L / 2.0) / (radius - self.W / 2.0))
            deltaR = math.atan((self.L / 2.0) / (radius + self.W / 2.0))

            # 后轮真实路径速度（关键点！你这里是对的）
            vRL = psiDot * math.sqrt((radius - self.W / 2.0)**2 + (self.L / 2.0)**2)
            vRR = psiDot * math.sqrt((radius + self.W / 2.0)**2 + (self.L / 2.0)**2)

        # ==========================================
        # 4. 左右方向切换（右转）
        # ==========================================
        if Dir_LR == 2:
            vRL, vRR = vRR, vRL

        # ==========================================
        # 5. m/s → rpm
        # ==========================================
        wRL_rpm = vRL / self.rRL * 60.0 / (2.0 * math.pi)
        wRR_rpm = vRR / self.rRR * 60.0 / (2.0 * math.pi)

        return {
            "deltaL": deltaL,
            "deltaR": deltaR,
            "wRL_rpm": wRL_rpm,
            "wRR_rpm": wRR_rpm,
            "radius": radius
        }