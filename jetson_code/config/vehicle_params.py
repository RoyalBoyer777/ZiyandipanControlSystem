#车体的相关参数
class VehicleParams:
    def __init__(self):
        self.wheelbase = 1.4  # 轴距，单位：米
        self.track_width = 1.150  # 轮距，单位：米
        self.max_steering_angle = 20.0  # 最大转向角，单位：度
        self.max_speed = 2.7778  # 最大速度，单位：米/秒  10km/h = 2.7778 m/s
        self.wheel_radius = 0.245  # 轮半径，单位：米
        