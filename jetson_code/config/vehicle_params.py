#车体的相关参数
class VehicleParams:
    def __init__(self):
        #车体
        self.wheelbase = 1.4  # 轴距，单位：米
        self.track_width = 1.150  # 轮距，单位：米
        self.max_steering_angle = 20.0  # 最大转向角，单位：度
        self.max_speed = 2.7778  # 最大速度，单位：米/秒  10km/h = 2.7778 m/s
        self.wheel_radius = 0.245  # 轮半径，单位：米

        #转向
        self.Ls_mm = 100  # 转向节转臂长度，单位：毫米
        self.Pitch_mm = 50  # 转向器线角比，单位：mm/rev （转向器每转一圈，齿轮的位移）