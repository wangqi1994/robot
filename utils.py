#encoding:utf-8
import os
import time
import json
import struct
import datetime
import configparser
import subprocess
import base64
import math
import serial
import numpy as np
import cv2

import debug
import setting


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


def get_real_time_position(msg):
    if msg['message_type'] == 'report_pos_vel_status':
        setting.robotname = msg['name']
        # 修改后
        real_time_pose = msg['pose']
        setting.robotPosx1 = real_time_pose['x']
        setting.robotPosy1 = real_time_pose['y']
        setting.robotPosyaw1 = real_time_pose['yaw'] / math.pi * 180

def get_map_file_code(msg):   
    # if not os.path.exists(setting.mapfile):
    if msg["message_type"] == "update_file":
        map_code = msg['content']
        code = base64.b64decode(map_code)
        with open(setting.mapfile, "wb+") as fp:
            fp.write(code)

def get_now_angle_code(msg):
    # if not os.path.exists(setting.mapfile):
    if msg["message_type"] == "report_pos_vel_status":
        now_angle = msg['pose']['yaw']
        setting.now_angle = now_angle/math.pi*180

def judge_no_money_shutdown(msg):
    if msg["message_type"] == "no_money_shut_down":
        setting.shutdown_flag = True

def judge_clear_warning(msg):
    if msg["message_type"] == "clear_warning":
        setting.clearwarning_flag = True  #错误引用

def judge_status_camera(msg):
    if msg["message_type"] == "camera_status":
        pass

def judge_robot_shutdown(msg):
    if msg["message_type"] == "robot_shut_down":
        pass

def get_now_running_status(msg):
    # if not os.path.exists(setting.mapfile):
    if msg["message_type"] == "report_stat":
        setting.distance = msg['stat']['dist']

def receive2dic(tcp_sock):
    """ 以字节方式（bytes）接收数据，
      返回“字典”（python 的key-value 数据类型）"""
    # 接收4字节的固定头部
    head_bytes = tcp_sock.recv(4)
    # print(['utils-receive2dic', head_bytes, head_bytes.__len__()])
    while 4 - head_bytes.__len__():
        # if head_bytes.__len__() == 0:
        #     break
        head_bytes += tcp_sock.recv(4 - head_bytes.__len__())
    head_int = struct.unpack('=L', head_bytes)[0]

    buffer = []
    message_len = 0

    while head_int - message_len:
        data_byte = tcp_sock.recv(head_int - message_len)
        buffer.append(data_byte)
        message_len += data_byte.__len__()
    # if len(buffer) > 0:
    # print(['utils-receive2dic111', buffer])

    # 拼接字符串与编码转换
    str_json = (b''.join(buffer)).decode()
    return json.loads(str_json)

def pack2bytes(dic_ready):
    """ 将 JSON 消息打包成（含固定头部的）字节（bytes）数据 """
    json_str = json.dumps(dic_ready)  # Python 数据格式（dict） -> JSON 字符串   (将 Python 对象编码成 JSON 字符串)
    json_bytes = json_str.encode()    # 字符串 转换编码为 bytes 格式
    # Head
    json_bytes_len = len(json_bytes)  # 计算消息的字节（bytes）长度
    message_packed = struct.pack('=L', json_bytes_len) + json_bytes

    return message_packed

def print2txt(msg):  #输出到指定文件
    '''
    把筛选后的信息输出到文件
    :param: msg (str)
    :return: None
    '''
    nowtime = time.strftime("%Y-%m-%d %X")
    f = open(setting.outputfile,'a+')
    f.write("%s \n    %s \n" %(nowtime, msg))

def get_ping_result():
    ret = 1
    ip = setting.server_ip
    p = subprocess.Popen(["ping.exe", ip], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    out = p.stdout.read().decode('gbk')
    find_str = "(0% 丢失)"
    print2txt(["底盘IP通信情况：  ", out])
    print(["底盘IP通信情况：  ", out])
    if find_str in out:
        ret = 0
    return ret

def judge_arrive_flag(cx, cy, nx, ny, juli): #是否到达指定地点
    arrive_flag = False
    if math.pow(cx - nx, 2) + math.pow(cy - ny, 2) <= juli:
        arrive_flag = True
    return arrive_flag

# =============串口方法=============
def serial_open(port_name,bps=115200):
    # todo:改成全局变量，不然可能返回无法预期的结果
    ret = False
    try:
        # 传入串口参数
        portx = port_name
        bps = bps
        timex = 5
        # 打开串口，并得到串口对象
        ser = serial.Serial(portx, bps, timeout=timex)
        # 判断是否打开成功
        if ser.is_open:
            ret = True
            print("串口[", portx, "]打开成功", "ret=", ret, ".")
    # except:
    except Exception as e:
        print("---异常---:", e)
    return ser
# =============串口方法=============

# ================str2float================
def str2float(a_list):
    angle_list = []
    for i in range(len(a_list)):
        angle_list.append(float(a_list[i]))
    return angle_list

# =============NEW:剔出异常数据,以得到准确的angle_α、angle_β值==============
def detect_outliter(angle_list):
    # 1st quartile (25%)
    Q1 = np.percentile(angle_list, 25)
    print(Q1)
    # 3st quartile (75%)
    Q3 = np.percentile(angle_list, 75)
    # Inter quartile range (IQR)
    IQR = Q3 - Q1
    # outlier step
    outlier_step = 1.5 * IQR
    lower_limit = Q1 - outlier_step
    upper_limit = Q3 + outlier_step
    dataFrame = filter(lambda angle: lower_limit <= angle <= upper_limit, angle_list)
    angle_list_new = list(dataFrame)
    angle = round(sum(angle_list_new) / len(angle_list_new), 4)
    return angle

def one_angle(poi,angle_list):
    img = cv2.imread(setting.mapfile, cv2.IMREAD_UNCHANGED)
    maps_size = np.array(img)  # 获取图像行和列大小
    height = maps_size.shape[0]  # 行数->y
    width = maps_size.shape[1]  # 列数->x
    list_poi1 = []
    list_poi2 = []
    for i in angle_list:
        for r in [2,4,6,8,10,12,14]:
            x1 = int(poi[0] + r * math.cos(i * math.pi / 180))
            y1 = int(poi[1] + r * math.sin(i * math.pi / 180))
            poi_pix = me2pix(img.shape,[x1, y1])
            if poi_pix[0] < 0 or poi_pix[0] >= width:
                print(["角度：", i, "距离半径r :", r, poi_pix[0], "width  在区域外"])
                continue
            if poi_pix[1] < 0 or poi_pix[1] >= height:
                print(["角度：", i, "距离半径r :", r, poi_pix[1], "height  在区域外"])
                continue
            if img[poi_pix[1], poi_pix[0]] < 220:
                print(["角度：", i, "距离半径r :", r, [x1, y1], img[y1, x1], "有障碍物"])
                continue
            list_poi1.append([x1,y1])
    for i in list_poi1:
        if i in list_poi2:
            continue
        else:
            list_poi2.append(i)
    # print(list_poi2)
    return list_poi2

def circle_move(poi,move_flag):
    if move_flag == 1:
        angle_list = [180, 135, 90, 270, 225]
    elif move_flag == -1:
        angle_list = [0, 45, 90, 270, 315]
    else:
        angle_list = [0]
    img = cv2.imread(setting.mapfile, cv2.IMREAD_UNCHANGED)
    maps_size = np.array(img)  # 获取图像行和列大小
    height = maps_size.shape[0]  # 行数->y
    width = maps_size.shape[1]  # 列数->x
    list_poi1 = []
    list_poi2 = []
    for i in angle_list:
        for r in [6,5,4]:
            x1 = int(poi[0] + r * math.cos(i * math.pi / 180))
            y1 = int(poi[1] + r * math.sin(i * math.pi / 180))
            poi_pix = me2pix(img.shape, [x1, y1])
            if poi_pix[0] < 0 or poi_pix[0] >= width:
                print(["角度：", i, "距离半径r :", r, poi_pix[0], "width  在区域外"])
                continue
            if poi_pix[1] < 0 or poi_pix[1] >= height:
                print(["角度：", i, "距离半径r :", r, poi_pix[1], "height  在区域外"])
                continue
            if img[poi_pix[1], poi_pix[0]] < 220:
                print(["角度：", i, "距离半径r :", r, [x1, y1], img[y1, x1], "有障碍物"])
                continue
            list_poi1.append([x1, y1])
            break
    print(list_poi1)
    return list_poi1

def me2pix(size, me):
    col = size[0] / 2
    row = size[1] / 2
    _x = me[0] / 0.05000000074505806 + row
    _y = col - me[1] / 0.05000000074505806
    return int(_x), int(_y)

