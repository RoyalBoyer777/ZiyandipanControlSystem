from modules.can_protocol import FB_CAN_VCU_SES_Req as VCU_SES_Req
import can
import time

#can总线有必要每次初始化一个类的时候都有初始化吗？不太必要，可以在主程序中初始化一次CAN总线对象，然后传递给需要使用的类，这样可以避免重复初始化和资源浪费。或者也可以设计一个单例模式的CAN总线管理类，确保全局只有一个CAN总线实例被创建和使用。
class SteeringController:
    def __init__(self, bus):
        # 初始化CAN总线
        self.bus = bus

        # 前后转向打包器（各自独立rolling counter）
        self.front_packer = VCU_SES_Req()
        self.rear_packer = VCU_SES_Req()

        # CAN ID
        self.FRONT_ID = 0x169   # 169
        self.REAR_ID = 0x179    # 179

    # ==========================
    # 发送单帧
    # ==========================
    def _send(self, can_id, data):
        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=False
        )
        self.bus.send(msg)

    # ==========================
    # 核心控制接口
    # ==========================
    def set_steering(self, angle, angle_spd, veh_spd, enable):
        """
        angle: 前轮目标角度（°）
        angle_spd: 转角速度
        veh_spd: 车速（Byte6）
        enable: 使能
        """

        # ==========================
        # 前轮
        # ==========================
        front_data = self.front_packer.pack(
            Tgt_StrAngle=angle,
            Tgt_StrAngleSpd=angle_spd,
            Veh_Spd=veh_spd,
            Enable=enable
        )

        self._send(self.FRONT_ID, front_data)

        # ==========================
        # 后轮（角度取反）
        # ==========================
        rear_data = self.rear_packer.pack(
            Tgt_StrAngle=-angle,   # ⭐关键：反向
            Tgt_StrAngleSpd=angle_spd,
            Veh_Spd=veh_spd,
            Enable=enable
        )

        self._send(self.REAR_ID, rear_data)

    # ==========================
    # 停止（安全）
    # ==========================
    def stop(self):
        self.set_steering(
            angle=0,
            angle_spd=0,
            veh_spd=0,
            enable=False
        )