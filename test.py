#encoding:utf-8
import time
import math
import json
import struct
import base64
import socket
import threading
import datetime
import configparser
import subprocess
import traceback

import debug
import setting


server_ip = "192.168.8.2"
host_mac = "b0:41:6f:03:d0:4d"
robot_mac = "C4:00:AD:24:58:03"

robotcharge = "0.00"
planworkfile = "./config/planworkfile.conf"
workingstatus = ""
poilist = []
goal_position = []

#[机器人当前位置]
robotPosx1 = 0.00
robotPosy1 = 0.00
robotPosyaw1 = 0.00


# 注册命令
reg_client_message = {
    "message_type": "register_client",
    "client_type": 3,
    "mac_address": host_mac}

# 获取所有机器人信息
get_all_robot_info_message = {
    "message_type": "get_all_robot_info"}

# 移动与停止（持续发送）
move_message = {
    "message_type": "move",
    "robot_mac_address": robot_mac,
    "vx": 0,
    "vy": 0,
    'vtheta': 0.0}

# 消息过滤
set_filter = {
    "message_type": "set_filter",
    "filter": ["laser",
        "all_file_info",
        "auto_guided_task_status",
        # "report_pos_vel_status",
        # "report_sensor_data_info",     # 机器人位置与速度状态更新
        "device_status",
        "sensor_power_status",
        "report_basic_status"]}

# -----------------获取地图文件-----------------
get_map_file = {
    "message_type": "get_file",
    "file_name": "map.1"
}
# -----------------获取地图文件-----------------

# 移动到指定位置与原地旋转（自动导航避障），导航至（detector_x，detector_y，detector_yaw）位置
command_goal = {
    "message_type": "command_goal",
    "robot_mac_address": robot_mac,
    "x": -20.0893,
    "y": 0.39282,
    "yaw": 3.95799,
    # "only_rot": "true",
    # "relative_rot": "true"
}

# 有序漫游
order_roaming = {
    "message_type": "poi_action",
    "robot_mac_address": robot_mac,
    "mode": "order_roaming",
    "params": {
        "loop": "true"
    }
}

#  导航到充电点并自动充电
auto_charge_message = {
    "message_type": "charge",
    "robot_mac_address": robot_mac,
    # charge_point_name与position只取其一，如果同时指定将忽略position参数
    # "charge_point_name": "charge1",
    "position": {"x": -8.445, "y": -5.863, "yaw": 265.17}
}


# 取消充电
cancel_charge = {
    "message_type": "cancel_charge",
    "robot_mac_address": robot_mac,
}

# 判断当前时间是否在某个区间时间内
class JudjeTime(object):
    def __init__(self, start, end):
        self.start = str(start)
        self.end = str(end)

    def judje(self):
        n_time = datetime.datetime.now() # 获取当前时间
        start = datetime.datetime.strptime(str(datetime.datetime.now().date()) + self.start, '%Y-%m-%d%H:%M')
        end = datetime.datetime.strptime(str(datetime.datetime.now().date()) + self.end, '%Y-%m-%d%H:%M')
        if n_time > start and n_time < end:
            return True
        else:
            return False

def getplanwork():
    conf = configparser.ConfigParser()
    conf.read(planworkfile)
    sections = conf.sections()
    for i in sections:
        starttime = conf[i]["starttime"]
        endtime = conf[i]["endtime"]
        if JudjeTime(starttime,endtime).judje():
            global workingstatus
            if workingstatus == i:
                break
            else:
                workingstatus = i
                list1 = []
                global poilist
                if len(conf[i]["poilist"]) > 1:
                    pois = conf[i]["poilist"].split(";")
                    for poi in pois:
                        zs = poi.split(",")
                        for ix in range(len(zs)):
                            zs[ix] = float(zs[ix])
                        list1.append(zs)
                poilist = list1
                break

def get_real_time_position(msg):
    if msg['message_type'] == 'report_pos_vel_status':
        # 修改后
        real_time_pose = msg['pose']
        global robotPosx1, robotPosy1, robotPosyaw1
        robotPosx1 = real_time_pose['x']
        robotPosy1 = real_time_pose['y']
        robotPosyaw1 = real_time_pose['yaw']

def get_map_file_code(msg):
    if msg["message_type"] == "update_file":
        map_code = msg['content']
        code = base64.b64decode(map_code)
        with open('./' + "map.png", "wb") as fp:
            fp.write(code)

def get_dump_energy(msg):
    dump_energy = ""
    if msg['message_type'] == 'report_obd_status':
        # 修改后
        obd_list = msg['obd'].split(" ")
        voltage = obd_list[0]
        ampere = obd_list[1]
        dump_energy = obd_list[5]
        global robotcharge
        robotcharge = dump_energy
    return dump_energy

def receive2dic(tcp_sock):
    """ 以字节方式（bytes）接收数据，
      返回“字典”（python 的key-value 数据类型）"""
    # 接收4字节的固定头部
    head_bytes = tcp_sock.recv(4)
    # if head_bytes == None:
    #     return ""
    while 4 - head_bytes.__len__():
        head_bytes += tcp_sock.recv(4 - head_bytes.__len__())
    head_int = struct.unpack('=L', head_bytes)[0]

    buffer = []
    message_len = 0

    while head_int - message_len:
        data_byte = tcp_sock.recv(head_int - message_len)
        buffer.append(data_byte)
        message_len += data_byte.__len__()
        # 拼接字符串与编码转换
    str_json = (b''.join(buffer)).decode()
    return json.loads(str_json)

def pack2bytes(dic_ready):
    """ 将 JSON 消息打包成（含固定头部的）字节（bytes）数据 """
    # if dic_ready["message_type"] == "command_goal":
    #     print2txt(["12345678", json.dumps(dic_ready), json.dumps(dic_ready).encode()])
    json_str = json.dumps(dic_ready)  # Python 数据格式（dict） -> JSON 字符串   (将 Python 对象编码成 JSON 字符串)
    json_bytes = json_str.encode()    # 字符串 转换编码为 bytes 格式
    # Head
    json_bytes_len = len(json_bytes)  # 计算消息的字节（bytes）长度
    message_packed = struct.pack('=L', json_bytes_len) + json_bytes

    return message_packed

def print2txt(msg):
    '''
    把筛选后的信息输出到文件
    :param: msg (str)
    :return: None
    '''
    nowtime = time.strftime("%Y-%m-%d %X")
    f = open("123.txt",'a+')
    f.write("%s \n    %s \n" %(nowtime, msg))

class RecvTread(threading.Thread):
    def __init__(self, tcp_socket):
        threading.Thread.__init__(self)
        self.s = tcp_socket

    def run(self):
        while True:
            msg = receive2dic(self.s)
            get_map_file_code(msg)
            getplanwork()
            get_real_time_position(msg)
            print2txt(msg)
            get_dump_energy(msg)

def get_ping_result():
    ret = 1
    ip = server_ip
    p = subprocess.Popen(["ping.exe", ip], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    out = p.stdout.read().decode('gbk')
    find_str = "(0% 丢失)"
    print(["底盘IP通信情况：  ", out])
    if find_str in out:
        ret = 0
    return ret

def judge_arrive_flag(cx, cy, nx, ny):
    arrive_flag = False
    if math.pow(cx - nx, 2) + math.pow(cy - ny, 2) <= 0.1:
        arrive_flag = True
    return arrive_flag

def send_planwork_command():
    try:
        move_flag = False
        if len(poilist) > 0:
            if goal_position == []:
                goal_position = poilist.pop(0)
                move_flag = True
            else:
                now_position = [robotPosx1, robotPosy1, robotPosyaw1]
                print(["当前的目标位置是否在附近:   ", judge_arrive_flag(goal_position[0], goal_position[1], robotPosx1, robotPosy1)])
                if judge_arrive_flag(goal_position[0], goal_position[1], robotPosx1, robotPosy1):
                    print("到达目标附件！")
                    goal_position = poilist.pop(0)
                    move_flag = True
                else:
                    print("未到达目标附近！")
        if move_flag:
            command_goal = command_goal
            command_goal["x"] = goal_position[0]
            command_goal["y"] = goal_position[1]
            command_goal["yaw"] = goal_position[2]
    except:
        debug.write_debug(debug.LINE(), "main---", traceback.print_exc())

if __name__ == '__main__':
    try:
        while get_ping_result():
            time.sleep(5)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_ip, 6789))

        json_packed = pack2bytes(reg_client_message)
        s.send(json_packed)

        json_packed = pack2bytes(get_all_robot_info_message)
        s.send(json_packed)

        json_packed = pack2bytes(get_map_file)
        s.send(json_packed)

        time.sleep(3)
        print(["发送命令，取消充电。。。。"])
        json_packed = pack2bytes(cancel_charge)
        s.send(json_packed)

        RecvTread(s).start()
        i = 0
        chongdianflag = True
        while True:
            if robotPosx1 == 0.00:
                continue
            # i = i + 1
            # if i == 1:
            #     move_message1 = move_message
            #     move_message1["vx"] = 0.2
            #     s.send(pack2bytes(move_message1))
            #     print(["移动位置1:", pack2bytes(move_message1)])
            # elif i ==2:
            #     move_message1 = move_message
            #     move_message1["vx"] = -0.2
            #     s.send(pack2bytes(move_message1))
            #     print(["移动位置2:", pack2bytes(move_message1)])
            # print([i, '当前的目标位置:', [robotPosx1, robotPosy1, robotPosyaw1]])
            # if i == 2:
            #     i = 0
            # time.sleep(3)
            
            # move_flag = False
            '''
            if len(poilist) > 0:
                if goal_position == []:
                    goal_position = poilist.pop(0)
                    move_flag = True
                else:
                    now_position = [robotPosx1, robotPosy1, robotPosyaw1]
                    print(["当前的目标位置是否在附近:   ", judge_arrive_flag(goal_position[0], goal_position[1], robotPosx1, robotPosy1)])
                    if judge_arrive_flag(goal_position[0], goal_position[1], robotPosx1, robotPosy1):
                        print("到达目标附件！")
                        goal_position = poilist.pop(0)
                        move_flag = True
                    else:
                        print("未到达目标附近！")
            '''
            # if move_flag:
            # if setting.goal_position != [] and iflag == 0:
                # json_packed = pack2bytes(auto_charge_message)
                # print(["导航充电:", json_packed])
                # s.send(json_packed)
                # goal_position = [9.21, 8.29, 3.14]
                # command_goal = command_goal
                # command_goal["x"] = goal_position[0]
                # command_goal["y"] = goal_position[1]
                # command_goal["yaw"] = goal_position[2]
                
                # command_goal = auto_charge_message
                # command_goal["position"]["x"] = goal_position[0]
                # command_goal["position"]["y"] = goal_position[1]
                # command_goal["position"]["yaw"] = goal_position[2]
                # json_packed = pack2bytes(command_goal)
                # s.send(json_packed)
            print("\n")
            # print(['移动的目标位置:', command_goal])
            # print(['当前的电量:', robotcharge])
            # print(['当前的目标位置:', [robotPosx1, robotPosy1, robotPosyaw1]])
            if chongdianflag:
                json_packed = pack2bytes(auto_charge_message)
                print(["导航充电:", json_packed])
                # s.send(json_packed)
                chongdianflag = False
            time.sleep(3)

        s.close()
    except:
        s.close()
        print("错误的结束")
        debug.write_debug(debug.LINE(), "main---", traceback.print_exc())
















