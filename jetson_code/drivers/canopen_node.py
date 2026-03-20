# import canopen
# import time


# class CANopenNode:
#     def __init__(self, can_channel='can0', bitrate=500000):
#         # 创建网络
#         self.network = canopen.Network()

#         # 绑定到底层 socketcan
#         self.network.connect(
#             channel=can_channel,
#             bustype='socketcan',
#             bitrate=bitrate
#         )

#         self.nodes = {}

#     # ==========================
#     # 添加节点（电机 / 遥控器）
#     # ==========================
#     def add_node(self, node_id, eds_file):
#         node = canopen.RemoteNode(node_id, eds_file)
#         self.network.add_node(node)

#         self.nodes[node_id] = node

#         print(f"[CANopen] Node {node_id} added")
#         return node

#     # ==========================
#     # 启动网络
#     # ==========================
#     def start(self):
#         self.network.nmt.state = 'PRE-OPERATIONAL'
#         time.sleep(0.5)
#         self.network.nmt.state = 'OPERATIONAL'
#         print("[CANopen] Network started")

#     # ==========================
#     # 发送PDO
#     # ==========================
#     def send_rpdo1(self, node_id, data_dict):
#         node = self.nodes.get(node_id)
#         if not node:
#             return
#         for key, value in data_dict.items():
#             node.rpdo[1][key].raw = value
#         node.rpdo[1].transmit()

#     def send_rpdo2(self, node_id, data_dict):
#         node = self.nodes.get(node_id)
#         if not node:
#             return
#         for key, value in data_dict.items():
#             node.rpdo[2][key].raw = value
#         node.rpdo[2].transmit()

#     def send_rpdo3(self, node_id, data_dict):
#         node = self.nodes.get(node_id)
#         if not node:
#             return
#         for key, value in data_dict.items():
#             node.rpdo[3][key].raw = value
#         node.rpdo[3].transmit()

#     def send_rpdo4(self, node_id, data_dict):
#         node = self.nodes.get(node_id)
#         if not node:
#             return

#         for key, value in data_dict.items():
#             node.rpdo[4][key].raw = value

#         node.rpdo[4].transmit()

#     # ==========================
#     # 读取TPDO（反馈）
#     # ==========================
#     def read_tpdo1(self, node_id):
#         node = self.nodes.get(node_id)
#         if not node:
#             return None
#         return node.tpdo[1]
    
#     def read_tpdo2(self, node_id):
#         node = self.nodes.get(node_id)
#         if not node:
#             return None
#         return node.tpdo[2]
    
#     def read_tpdo3(self, node_id):
#         node = self.nodes.get(node_id)
#         if not node:
#             return None
#         return node.tpdo[3]
    
#     def read_tpdo4(self, node_id):
#         node = self.nodes.get(node_id)
#         if not node:
#             return None
#         return node.tpdo[4]

#     # ==========================
#     # SDO读写（调试/配置）
#     # ==========================
#     def sdo_read(self, node_id, index, subindex):
#         node = self.nodes[node_id]
#         return node.sdo[index][subindex].raw

#     def sdo_write(self, node_id, index, subindex, value):
#         node = self.nodes[node_id]
#         node.sdo[index][subindex].raw = value