import sys
import socket
import struct
import re
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QColor

# 本地主机地址和端口
local_ip = '192.168.188.101'  # 替换为实际的本地 IP
local_port = 5003  # 替换为实际的本地端口

# 目标 IP 和端口
target_ip = '192.168.188.100'
target_port = 5001



# 启动 UDP 监听器，接收并解析轴相关数据，更新 UI
def start_udp_listener(update_ui_callback):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((local_ip, local_port))
    print(f"Listening for UDP messages on {local_ip}:{local_port}...")

    while True:
        data, addr = udp_socket.recvfrom(4096)
        data_array = struct.unpack('20d', data)  # 假设数据是 20 个 double 型（LREAL），通过 unpack 解析成数组

        # 解析并构建数据字典
        axis_data = {
            'A1轴通信状态': data_array[0],
            'A1轴运行状态': data_array[1],
            'A1轴故障代码': data_array[2],
            'A1轴伺服反馈位置': data_array[3],
            'A1轴伺服反馈速度': data_array[4],
            'A1轴伺服反馈转矩': data_array[5],
            'A2轴通信状态': data_array[6],
            'A2轴运行状态': data_array[7],
            'A2轴故障代码': data_array[8],
            'A2轴伺服反馈位置': data_array[9],
            'A2轴伺服反馈速度': data_array[10],
            'A2轴伺服反馈转矩': data_array[11],
        }

        # 更新 UI
        update_ui_callback(axis_data)


def send_data_using_bytes(data_array):
    """
    通过字节发送数据
    :param data_array: 包含 10 个 LREAL 的数组
    """
    # 使用 struct 打包数据，'10d' 表示 10 个 double 数据
    message = struct.pack('20d', *data_array)

    # 创建 UDP 套接字并发送数据
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.sendto(message, (target_ip, target_port))
    print(f"Sent byte message to {target_ip}:{target_port}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("电机状态监控与控制")
        self.setGeometry(100, 100, 900, 500)

        # 设置全局字体
        self.setFont(QFont("Arial", 10))

        # 创建主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 创建左边的状态显示区域
        self.frame_left = QWidget()
        self.frame_left_layout = QGridLayout()
        self.frame_left.setLayout(self.frame_left_layout)
        main_layout.addWidget(self.frame_left)

        # 创建右边的控制功能区域
        self.frame_right = QWidget()
        self.frame_right_layout = QGridLayout()
        self.frame_right.setLayout(self.frame_right_layout)
        main_layout.addWidget(self.frame_right)

        # 设置标题字体
        title_font = QFont("Arial", 14, QFont.Bold)
        label_font = QFont("Arial", 10, QFont.Bold)
        data_font = QFont("Arial", 10)

        # 轴1 状态显示
        axis1_title = QLabel("轴1 数据")
        axis1_title.setFont(title_font)
        self.frame_left_layout.addWidget(axis1_title, 0, 0, 1, 2)

        self.axis1_labels = {}
        keys = ["轴通信状态", "轴运行状态", "轴故障代码", "轴伺服反馈位置", "轴伺服反馈速度", "轴伺服反馈转矩"]
        for i, key in enumerate(keys):
            label = QLabel(f"A1{key}")
            label.setFont(label_font)
            self.frame_left_layout.addWidget(label, i + 1, 0)
            self.axis1_labels[key] = QLabel("未知")
            self.axis1_labels[key].setFont(data_font)
            self.frame_left_layout.addWidget(self.axis1_labels[key], i + 1, 1)

        # 轴2 状态显示
        axis2_title = QLabel("轴2 数据")
        axis2_title.setFont(title_font)
        self.frame_left_layout.addWidget(axis2_title, 7, 0, 1, 2)

        self.axis2_labels = {}
        for i, key in enumerate(keys):
            label = QLabel(f"A2{key}")
            label.setFont(label_font)
            self.frame_left_layout.addWidget(label, i + 8, 0)
            self.axis2_labels[key] = QLabel("未知")
            self.axis2_labels[key].setFont(data_font)
            self.frame_left_layout.addWidget(self.axis2_labels[key], i + 8, 1)

        # 创建右边控制区域
        control_title = QLabel("控制电机1")
        control_title.setFont(title_font)
        self.frame_right_layout.addWidget(control_title, 0, 0, 1, 2)

        # 输入框和按钮：轴1
        self.position_entries = {}
        self.velocity_entries = {}
        self.acceleration_entries = {}
        self.deceleration_entries = {}

        self.frame_right_layout.addWidget(QLabel("输入位置"), 1, 0)
        self.position_entries[1] = QLineEdit()
        self.frame_right_layout.addWidget(self.position_entries[1], 1, 1)

        self.frame_right_layout.addWidget(QLabel("输入速度"), 2, 0)
        self.velocity_entries[1] = QLineEdit()
        self.frame_right_layout.addWidget(self.velocity_entries[1], 2, 1)

        self.frame_right_layout.addWidget(QLabel("输入加速度"), 3, 0)
        self.acceleration_entries[1] = QLineEdit()
        self.frame_right_layout.addWidget(self.acceleration_entries[1], 3, 1)

        self.frame_right_layout.addWidget(QLabel("输入减速度"), 4, 0)
        self.deceleration_entries[1] = QLineEdit()
        self.frame_right_layout.addWidget(self.deceleration_entries[1], 4, 1)

        # 控制按钮：轴1
        enable_button = QPushButton("使能")
        enable_button.setFont(label_font)
        enable_button.setStyleSheet("background-color: #4CAF50; color: white;")
        enable_button.clicked.connect(self.A1_enable)
        self.frame_right_layout.addWidget(enable_button, 5, 0)

        # 控制按钮：轴1
        disable_button = QPushButton("取消使能")
        disable_button.setFont(label_font)
        disable_button.setStyleSheet("background-color: #B22222; color: white;")
        disable_button.clicked.connect(self.A1_disable)
        self.frame_right_layout.addWidget(disable_button, 5, 1)

        start_button = QPushButton("开始运动")
        start_button.setFont(label_font)
        start_button.setStyleSheet("background-color: #008CBA; color: white;")
        start_button.clicked.connect(lambda: self.A1_start_motion(1))
        self.frame_right_layout.addWidget(start_button, 5, 2)

        # 控制轴2
        control_title2 = QLabel("控制电机2")
        control_title2.setFont(title_font)
        self.frame_right_layout.addWidget(control_title2, 7, 0, 1, 2)

        # 输入框和按钮：轴2
        self.frame_right_layout.addWidget(QLabel("输入位置"), 8, 0)
        self.position_entries[2] = QLineEdit()
        self.frame_right_layout.addWidget(self.position_entries[2], 8, 1)

        self.frame_right_layout.addWidget(QLabel("输入速度"), 9, 0)
        self.velocity_entries[2] = QLineEdit()
        self.frame_right_layout.addWidget(self.velocity_entries[2], 9, 1)

        self.frame_right_layout.addWidget(QLabel("输入加速度"), 10, 0)
        self.acceleration_entries[2] = QLineEdit()
        self.frame_right_layout.addWidget(self.acceleration_entries[2], 10, 1)

        self.frame_right_layout.addWidget(QLabel("输入减速度"), 11, 0)
        self.deceleration_entries[2] = QLineEdit()
        self.frame_right_layout.addWidget(self.deceleration_entries[2], 11, 1)

        # 控制按钮：轴2
        enable_button2 = QPushButton("使能")
        enable_button2.setFont(label_font)
        enable_button2.setStyleSheet("background-color: #4CAF50; color: white;")
        enable_button2.clicked.connect(self.A2_enable)
        self.frame_right_layout.addWidget(enable_button2, 12, 0)

        # 控制按钮：轴2
        disable_button = QPushButton("取消使能")
        disable_button.setFont(label_font)
        disable_button.setStyleSheet("background-color: #B22222; color: white;")
        disable_button.clicked.connect(self.A2_disable)
        self.frame_right_layout.addWidget(disable_button, 12, 1)


        start_button2 = QPushButton("开始运动")
        start_button2.setFont(label_font)
        start_button2.setStyleSheet("background-color: #008CBA; color: white;")
        start_button2.clicked.connect(lambda: self.A2_start_motion(2))
        self.frame_right_layout.addWidget(start_button2, 12,2)

        # 启动 UDP 监听线程
        self.udp_thread = threading.Thread(target=start_udp_listener, args=(self.update_ui,), daemon=True)
        self.udp_thread.start()

    def update_ui(self, data):
        """更新 UI 中的数值"""
        for key in self.axis1_labels:
            self.axis1_labels[key].setText(str(data.get(f'A1{key}', '未知')))
        for key in self.axis2_labels:
            self.axis2_labels[key].setText(str(data.get(f'A2{key}', '未知')))

    def A1_enable(self):
        """使能轴1"""
        # 创建一个包含 10 个 LREAL 的数组，初始化为 0
        data_array = [0.0] * 20
        # 第 0 个位置为 1.0，表示使能
        data_array[8] = 1.0
        # 发送数据
        send_data_using_bytes(data_array)

    def A2_enable(self):
        """使能轴2"""
        # 创建一个包含 10 个 LREAL 的数组，初始化为 0
        data_array = [0.0] * 20
        # 第 0 个位置为 1.0，表示使能
        data_array[9] = 1.0
        # 发送数据
        send_data_using_bytes(data_array)

    def A1_disable(self):
        """使能轴1"""
        # 创建一个包含 10 个 LREAL 的数组，初始化为 0
        data_array = [0.0] * 20
        # 第 0 个位置为 1.0，表示使能
        data_array[10] = 1.0
        # 发送数据
        send_data_using_bytes(data_array)

    def A2_disable(self):
        """使能轴2"""
        # 创建一个包含 10 个 LREAL 的数组，初始化为 0
        data_array = [0.0] * 20
        # 第 0 个位置为 1.0，表示使能
        data_array[11] = 1.0
        # 发送数据
        send_data_using_bytes(data_array)

    def A1_start_motion(self, axis):
        """开始运动"""
        # 获取用户输入的值
        position = self.position_entries[axis].text()
        velocity = self.velocity_entries[axis].text()
        acceleration = self.acceleration_entries[axis].text()
        deceleration = self.deceleration_entries[axis].text()

        # 将输入转换为浮动类型
        position = float(position)
        velocity = float(velocity)
        acceleration = float(acceleration)
        deceleration = float(deceleration)

        # 创建一个包含 10 个 LREAL 的数组，初始化为 0
        data_array = [0.0] * 20

        # 将用户输入的值放入数组的前 4 个位置
        data_array[0] = position
        data_array[1] = velocity
        data_array[2] = acceleration
        data_array[3] = deceleration
        data_array[8] = 1.0

        # 发送数据
        send_data_using_bytes(data_array)

    def A2_start_motion(self, axis):
        """开始运动"""
        # 获取用户输入的值
        position = self.position_entries[axis].text()
        velocity = self.velocity_entries[axis].text()
        acceleration = self.acceleration_entries[axis].text()
        deceleration = self.deceleration_entries[axis].text()

        # 将输入转换为浮动类型
        position = float(position)
        velocity = float(velocity)
        acceleration = float(acceleration)
        deceleration = float(deceleration)

        # 创建一个包含 10 个 LREAL 的数组，初始化为 0
        data_array = [0.0] * 20

        # 将用户输入的值放入数组的前 4 个位置
        data_array[4] = position
        data_array[5] = velocity
        data_array[6] = acceleration
        data_array[7] = deceleration
        data_array[9] = 1.0

        # 发送数据
        send_data_using_bytes(data_array)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())