#encoding:utf-8
import os
import sys
import time
import socket
import threading
import traceback
import json
import numpy as np
import struct
from datetime import datetime
from icecream import ic

import debug
import planwork
import setting
import utils
import charge
import dealfire
import errorflag
import robotclient
import fenbushi
import yuanhongwai

def time_str():
	return f'{datetime.now()}|> '
ic.configureOutput(prefix=time_str,includeContext=True)


def receive2dic(tcp_sock):
    """ 以字节方式（bytes）接收数据，
      返回“字典”（python 的key-value 数据类型）"""
    # 接收4字节的固定头部
    head_bytes = tcp_sock.recv(4)
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

class RecvTread(threading.Thread):
    # 接收小车信息线程
    def __init__(self, tcp_socket):
        threading.Thread.__init__(self)
        self.s = tcp_socket

    def run(self):
        while True:
            msg = receive2dic(self.s)
            utils.print2txt(msg)
            utils.get_map_file_code(msg)
            utils.get_real_time_position(msg)
            utils.get_now_running_status(msg)
            charge.get_dump_energy(msg)
            planwork.getplanwork()

class SerrightRecvTread(threading.Thread):
    # 右传感器线程
    def __init__(self, ser_r):
        threading.Thread.__init__(self)
        self.ser_r = ser_r

    def run(self):
        while not setting.find_fire_flag:
            time.sleep(0.3)
        dealfire.get_right_angle_info(self.ser_r)

class SerfenbushiRecvTread(threading.Thread):
    # 获取分布式传感器线程
    def __init__(self, ser_f):
        threading.Thread.__init__(self)
        self.ser_f = ser_f

    def run(self):
        fenbushi.get_ser_str_fen_none(self.ser_f)

class JudgeRobotStatusTread(threading.Thread):
    # 机器人状态线程
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass

class GetYuanhongwaiangleTread(threading.Thread):
    # 远红外摄像头线程
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        yuanhongwai.main()

class SerHeadRecvTread(threading.Thread):
    # 头部旋转线程
    def __init__(self, ser_h):
        threading.Thread.__init__(self)
        self.ser_h = ser_h

    def run(self):
        dealfire.set_head_angle(self.ser_h)

class SerSPwidthRecvTread(threading.Thread):
    # 水炮高度线程
    def __init__(self, ser_p):
        threading.Thread.__init__(self)
        self.ser_p = ser_p

    def run(self):
        dealfire.set_sp_angle(self.ser_p)


class SerleftRecvTread(threading.Thread):
    # 小车红外线接收线程
    def __init__(self, ser_l):
        threading.Thread.__init__(self)
        self.ser_l = ser_l

    def run(self):
        fenbushi.get_ser_str_fen_none1(self.ser_l)


def main():
    setting.run_time = datetime.now()

    # utils.get_ping_result()
    # 工控机跟机器人连接判断能否通信，能通信返回0，跳出循环，执行下一步操作；
    # 不能通信，返回1，等待2秒后，再次测试能否通信
    while utils.get_ping_result():
        time.sleep(2)

    # 每次启动的时候，都要把之前存在的地图删除掉，以防止地图没更新，之后跟机器人通信后，再生成最新的地图
    if os.path.exists(setting.mapfile):
        os.remove(setting.mapfile)

    # 打开右传感器
    ser_r = utils.serial_open(setting.right_eye_port,bps=9600)
    if ser_r == "error":
        sys.exit(errorflag.flag["001"])
    else:
        print("右传感器串口打开成功！")
        setting.ser_r = True

    # 打开头部水平旋转传感器
    ser_h = utils.serial_open(setting.deluge_gun_port,bps=9600)
    if ser_h == "error":
        sys.exit(errorflag.flag["002"])
    else:
        print("头部水平传感器串口打开成功！")
        setting.ser_h = True

    '''
    # 打开水炮垂直高度传感器
    ser_p = utils.serial_open(setting.shuipao_width_port)
    if ser_p == "error":
        sys.exit(errorflag.flag["003"])
    else:
        print("水炮垂直高度传感器串口打开成功！")
        setting.ser_p = True
    '''
    # 打开分布式传感器
    ser_f = utils.serial_open(setting.fenbushi_port,bps=9600)
    if ser_f == "error":
        sys.exit(errorflag.flag["004"])
    else:
        print("分布式传感器串口打开成功！")
        setting.ser_f = True


    # 打开红外传感器
    ser_l = utils.serial_open(setting.left_eye_port,bps=9600)
    if ser_l == "error":
        sys.exit(errorflag.flag["005"])
    else:
        print("红外传感器串口打开成功！")
        setting.ser_l = True


    # 工控机建立客户端，对应机器人的服务端，能够从机器人服务端接收命令、从工控机客户端发送命令到机器人服务端
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((setting.server_ip, 6789))
    try:
        # 发送注册命令到机器人服务端，让机器人知道有客户端连接
        json_packed = utils.pack2bytes(setting.reg_client_message)
        s.send(json_packed)

        # 发送获取机器人所有信息的命令到机器人服务端
        json_packed = utils.pack2bytes(setting.get_all_robot_info_message)
        s.send(json_packed)

        # 发送获取地图的命令到机器人服务端
        json_packed = utils.pack2bytes(setting.get_map_file)
        s.send(json_packed)

        # 发送设置信息过滤的命令到机器人服务端，机器人服务端一直在定时的发送很多命令，一些不需要的命令，可以过滤掉
        # json_packed = utils.pack2bytes(setting.set_filter) # 设置信息过滤
        # s.send(json_packed)

        # 发送重定位的命令到机器人服务端，机器人在重启的时候可能定位不准确 间隔5秒
        json_packed = utils.pack2bytes(setting.reset_message)
        s.send(json_packed)
        time.sleep(5)

        # 启动接收从机器人服务端发送过来的线程,这个线程一直在运行,只要有消息发送过来,就会执行
        RecvTread(s).start()

        # 启动检测火源的线程,从左右传感器接收消息及发送消息到右传感器
        # 发送火源后,不能在主线程再使用左右传感器的端口发送消息或者接受消息,否则报错"句柄无效"
        # 分布式传感器接收火源信息
        # 头部水平旋转线程
        # 水炮垂直摆动线程
        SerleftRecvTread(ser_l).start()
        SerrightRecvTread(ser_r).start()
        SerfenbushiRecvTread(ser_f).start()
        SerHeadRecvTread(ser_h).start()
        # SerSPwidthRecvTread(ser_p).start()

        # 判断小车运行状态，是否出错
        # JudgeRobotStatusTread().start()

        # 启动APP通信模块
        # robotclient.robotclient()

        # 开启主线程循环,执行灭火,充电,计划任务等操作
        # 每0.3秒,执行一次查询火源信息,发现火源后,先执行灭火动作,充电和计划任务操作不执行
        # 每1秒,判断是否有充电标志,如果有并且没有发现火源,就去充电,不执行计划任务
        # 每1秒,判断是否有计划任务,如果有计划任务并且没有发现火源,电量充足,就去执行计划任务
        i = 0
        fenbushi_num1 = ''

        # json_packed = utils.pack2bytes(setting.cancel_charge)
        # s.send(json_packed)
        # print("取消充电！！！")
        # time.sleep(5)
        while True:
            # print([time.strftime("%Y-%m-%d %X"), "开始循环111"])
            if setting.shutdown_flag:
                break
            i = i + 1
            time.sleep(0.3)
            if setting.robotPosx1 == 0.00:
                continue
            # 小车上的传感器是否发现火源
            if not setting.find_fire_flag:
                # print([time.strftime("%Y-%m-%d %X"), "小车没发现火源"])
                if setting.fen_find_fire_flag:
                    # 判断当前的分布式传感器的序号是否跟上一次一样，如果一样就不用变换路径
                    # 发现火源后，取消导航
                    json_packed = utils.pack2bytes(setting.cancel_goal)
                    s.send(json_packed)
                    time.sleep(1)
                    fenbushi_num1 = setting.fenbushi_num
                    for poi0 in setting.fenbushi_poilist:
                        index = setting.fenbushi_poilist.index(poi0) + 1
                        command_goal1 = setting.command_goal
                        command_goal1["x"] = poi0[0]
                        command_goal1["y"] = poi0[1]
                        command_goal1["yaw"] = poi0[2]
                        json_packed = utils.pack2bytes(command_goal1)
                        s.send(json_packed)
                        print(["前往分布式传感器，第----  %s  ----个坐标点。。。。" % index, poi0])
                        while True:
                            arrive_flag = utils.judge_arrive_flag(poi0[0], poi0[1], setting.robotPosx1,
                                                                  setting.robotPosy1, 0.1)
                            if arrive_flag:
                                print(["----到达分布式传感器，第----  %s  ----个坐标点。。。。" % index, poi0])
                                break
                        if setting.find_fire_flag:
                            break
                        if index == len(setting.fenbushi_poilist) + 1:
                            break
                    # 判断小车到达分布式传感器附近后，小车上的传感器未发现火源，是否要做圆周运动
                    continue
            else:
                print([time.strftime("%Y-%m-%d %X"), "小车发现火源"])
                if not setting.finish_fire:
                    find_fire_pos_flag = False
                    # 发现火源后，取消导航
                    time.sleep(1)
                    json_packed = utils.pack2bytes(setting.cancel_goal)
                    s.send(json_packed)
                    # time.sleep(4)
                    # 启动远红外摄像头线程
                    GetYuanhongwaiangleTread().start()
                    # 1、右传感器是否发现火源，如果传回角度，小车停下，准备调整水炮角度喷水
                    setting.right_eye_angle = 0.00
                    # if setting.right_eye_angle:
                    #     print([time.strftime("%Y-%m-%d %X"), "右传感器发现火源"])
                    #     pass
                    # else:
                    #     time.sleep(3)
                    #     # 2、如果右传感器没有发现火源，让远红外摄像头旋转探测，先按照默认水平角度旋转，再将摄像头高度提高逆转回来，旋转过程中，
                    #     # 发现火源，就让小车，顺着火源的方向前进，直到右传感器发现火源，小车停下
                    #     print([time.strftime("%Y-%m-%d %X"), "右传感器没有发现发现火源，旋转头部远红外摄像头寻找火源"])
                    #     setting.yuanhongwai_need_find_angle = True
                    #     setting.xuanzhuan_flag = setting.xuanzhuan_flag + 1
                    #     # if xuanzhuan_flag == 1:
                    #     # setting.nishizhenshizhen_xuanzhuan_flag = True
                    #     setting.head_flag = 0
                    #     # setting.head_flag_angle_1 = True
                    #     yuanhongwai_start_time = datetime.now()
                    #     now_flag = 0
                    #     while True:
                    #         yuanhongwai_now_time = datetime.now()
                    #         if setting.yuanhongwai_levelAngle1:
                    #             if setting.yuanhongwai_levelAngle1 and (yuanhongwai_now_time - setting.yuanhongwai_now_time1).seconds < 1:
                    #                 time.sleep(1)
                    #                 now_flag = 1
                    #                 break
                    #             else:
                    #                 time.sleep(0.2)
                    #         else:
                    #             if (yuanhongwai_now_time - yuanhongwai_start_time).seconds > 100:
                    #                 break
                    #             else:
                    #                 time.sleep(0.2)
                    #
                    #
                    #
                    #
                    #     # 假的
                    #     if now_flag:
                    #         while True:
                    #             if setting.right_eye_angle:
                    #                 break
                    #             time.sleep(0.5)
                    #         setting.dan_miaozhun_flag = True
                    #         pass
                    #
                    #
                    #
                    #
                    #         '''
                    #         print([time.strftime("%Y-%m-%d %X"), setting.robotPosyaw1, setting.yuanhongwai_levelAngle1, "远红外摄像头发现火源"])
                    #         fire_danjiaodu_angle = setting.robotPosyaw1 + setting.yuanhongwai_levelAngle1
                    #         setting.yuanhongwai_need_find_angle = False
                    #         time.sleep(0.5)
                    #         setting.yuanhongwai_levelAngle = None
                    #         setting.yuanhongwai_levelAngle1 = None
                    #         # setting.head_0_flag = True
                    #         if fire_danjiaodu_angle > 360:
                    #             fire_danjiaodu_angle = fire_danjiaodu_angle - 360
                    #         elif fire_danjiaodu_angle < 0:
                    #             fire_danjiaodu_angle = fire_danjiaodu_angle + 360
                    #         else:
                    #             pass
                    #         print([time.strftime("%Y-%m-%d %X"), fire_danjiaodu_angle, "计算火源相对小车在地图上的角度"])
                    #         one_angle_list = utils.one_angle([setting.robotPosx1, setting.robotPosy1], [fire_danjiaodu_angle])
                    #         for poi1 in one_angle_list:
                    #             if find_fire_pos_flag:
                    #                 json_packed = utils.pack2bytes(setting.cancel_goal)
                    #                 s.send(json_packed)
                    #                 break
                    #             index = one_angle_list.index(poi1) + 1
                    #             command_goal = setting.command_goal
                    #             command_goal["x"] = poi1[0]
                    #             command_goal["y"] = poi1[1]
                    #             command_goal["yaw"] = fire_danjiaodu_angle
                    #             json_packed = utils.pack2bytes(command_goal)
                    #             s.send(json_packed)
                    #             print(["这是单眼角度计算的第%s个点，" % index, poi1, "，我已经去了，主人。"])
                    #             while True:
                    #                 # 当右侧传感器发现了角度时，取消导航
                    #                 if setting.right_eye_angle:
                    #                     print([time.strftime("%Y-%m-%d %X"), index, "单眼角度,右眼找到了角度",
                    #                            setting.right_eye_angle])
                    #                     time.sleep(2)
                    #                     print([time.strftime("%Y-%m-%d %X"), "我已经到达, 到达时的小车角度：", setting.robotPosyaw1,
                    #                            setting.right_eye_angle])
                    #                     json_packed = utils.pack2bytes(setting.cancel_goal)
                    #                     s.send(json_packed)
                    #                     find_fire_pos_flag = True
                    #                     setting.dan_miaozhun_flag = True
                    #                     break
                    #                 arrive_flag = utils.judge_arrive_flag(poi1[0], poi1[1], setting.robotPosx1, setting.robotPosy1, 0.1)
                    #                 if arrive_flag:
                    #                     print([time.strftime("%Y-%m-%d %X"), "这是单眼角度计算的第%s个点，" % index, poi1, "，我已经到达。"])
                    #                     break
                    #                 time.sleep(0.05)
                    #         '''
                    #     else:
                    #         # 3、如果右传感器来回旋转也没有发现火源，就让小车，走圆周运动，直到右传感器发现火源位置，小车停下
                    #         print([time.strftime("%Y-%m-%d %X"), "都没有发现火源，做圆周运动寻找火源"])
                    #         if 90 < setting.robotPosyaw1 < 270:
                    #             move_xflag = 1
                    #         elif 0 < setting.robotPosyaw1 < 90 or 270 < setting.robotPosyaw1 < 360:
                    #             move_xflag = -1
                    #         else:
                    #             move_xflag = 0
                    #             # 计算出圆周上的几个合适坐标点，然后依次出发到五个点
                    #         list_poi = utils.circle_move([setting.robotPosx1, setting.robotPosy1], move_xflag)
                    #         find_fire_pos_flag = False
                    #         for poi in list_poi:
                    #             if find_fire_pos_flag:
                    #                 break
                    #             index = list_poi.index(poi) + 1
                    #             command_goal1 = setting.command_goal
                    #             command_goal1["x"] = poi[0]
                    #             command_goal1["y"] = poi[1]
                    #             json_packed = utils.pack2bytes(command_goal1)
                    #             s.send(json_packed)
                    #             print(["这是圆周运动计算的第%s个点，" % index, poi, "，我已经去了，主人。"])
                    #             while True:
                    #                 time.sleep(0.1)
                    #                 # 在运动过程中若右传感器发现火源，停止导航，当前位置是可以灭火的，
                    #                 # 然后将远红外传感器对准右传感器发现火源的位置
                    #                 if setting.right_eye_angle:
                    #                     if find_fire_pos_flag:
                    #                         json_packed = utils.pack2bytes(setting.cancel_goal)
                    #                         s.send(json_packed)
                    #                         break
                    #                 else:
                    #                     arrive_flag = utils.judge_arrive_flag(poi[0], poi[1], setting.robotPosx1, setting.robotPosy1, 0.1)
                    #                     if arrive_flag:
                    #                         print([time.strftime("%Y-%m-%d %X"), "这是圆周运动计算的第%s个点，" % index, poi, "，我已经到达。"])
                    #                         break

                    # 最后一步，到达灭火目标点，小车停下，根据右传感器传回的角度转动车身，调整远红外摄像头到0度，对准火源，然后根据远红外摄
                    # 像头返回的火源角度循环调整远红外摄像头，使其能够处在误差范围内的角度。
                    if 2 > 1:
                        setting.yuanhongwai_need_find_angle = False
                        time.sleep(0.2)
                        setting.head_flag = 3
                        # setting.head_flag = 2
                        setting.yuanhongwai_levelAngle = None
                        setting.yuanhongwai_levelAngle1 = None
                        print([time.strftime("%Y-%m-%d %X"), "到达灭火位置"])
                        print([time.strftime("%Y-%m-%d %X"),
                               [setting.robotPosx1, setting.robotPosy1, setting.robotPosyaw1],
                               setting.yuanhongwai_levelAngle1, "在灭火地点11111----远红外摄像头发现火源"])
                        setting.yuanhongwai_now_time1 = None
                        setting.yuanhongwai_need_find_angle = True
                        time.sleep(0.5)
                        setting.angle_status = True
                        if setting.dan_miaozhun_flag:
                            setting.miaozhun_flag = True
                        while True:
                            if setting.judge_angle:
                                print("--------------------------水平瞄准火源-----------------------")
                                break
                            time.sleep(0.02)
                        if setting.judge_angle:
                            time.sleep(0.5)
                            setting.angle_status_h = True
                            while True:
                                if setting.judge_angle_h:
                                    print("--------------------------竖直瞄准火源-----------------------")
                                    break
                                time.sleep(0.02)
                        time.sleep(1)
                        if setting.judge_angle_h:
                            setting.shuipao_penshui_flag = True
                            now_time = datetime.now()
                            penshui_status = 0
                            time.sleep(0.2)
                            print([time.strftime("%Y-%m-%d %X"), "灭火时，确定灭火标志00000---", setting.shuipao_penshui_flag])

                            while True:
                                penshui_time = datetime.now()
                                if (penshui_time - now_time).seconds > 120:
                                    break
                                if setting.yuanhongwai_pitchAngle:
                                    penshui_status = 0
                                else:
                                    penshui_status = penshui_status + 1
                                    print([time.strftime("%Y-%m-%d %X"), "灭火时，未检测到火源---", penshui_status])
                                if penshui_status > 15:
                                    time.sleep(0.2)
                                    setting.shuiyao_stop_penshui_flag = True
                                    break
                                setting.yuanhongwai_pitchAngle = None
                                time.sleep(1)
                    print("--------------------------喷水结束了-----------------------")
                    setting.yuanhongwai_levelAngle = None
                    setting.yuanhongwai_levelAngle1 = None
                    setting.finish_fire = True
                    setting.penshui_end_flag = True
                    time.sleep(2)
                    # break

                    command_goal = setting.command_goal
                    command_goal["x"] = -8.455
                    command_goal["y"] = -0.5
                    command_goal["yaw"] = 270
                    json_packed = utils.pack2bytes(command_goal)
                    s.send(json_packed)

                    while True:
                        arrive_flag = utils.judge_arrive_flag(-8.455, -0.5, setting.robotPosx1, setting.robotPosy1, 0.1)
                        time.sleep(0.1)
                        if arrive_flag:
                            ic(arrive_flag)
                            break
                    json_packed = utils.pack2bytes(setting.auto_charge_message)
                    s.send(json_packed)
                    time.sleep(120)



            # continue
            if i == 3:
                i = 0
                # 充电模块执行，充电时其他命令不执行
                utils.print2txt(['当前的电量:', setting.robotcharge])
                print([time.strftime("%Y-%m-%d %X"), '当前的电量:', setting.robotcharge])
                if setting.charge_status:
                    # 正处在充电状态中
                    utils.print2txt("正在充电状态中！！！")
                    print("正在充电状态中！！！")
                    if setting.charge_flag:
                        # 充电命令执行一次
                        json_packed = utils.pack2bytes(setting.cancel_goal)
                        s.send(json_packed)
                        time.sleep(0.5)
                        command_goal = setting.command_goal
                        command_goal["x"] = setting.robotPosx11
                        command_goal["y"] = setting.robotPosy11
                        command_goal["yaw"] = setting.robotPosyaw11
                        json_packed = utils.pack2bytes(command_goal)
                        s.send(json_packed)
                        while True:
                            time.sleep(0.1)
                            if utils.judge_arrive_flag(setting.robotPosx11, setting.robotPosy11, setting.robotPosx1,
                                                       setting.robotPosy1, 0.05):
                                json_packed = utils.pack2bytes(setting.cancel_goal)
                                s.send(json_packed)
                                utils.print2txt("到达目标附件！")
                                # time.sleep(1)
                                json_packed = utils.pack2bytes(setting.auto_charge_message)
                                s.send(json_packed)
                                break
                        setting.charge_flag = False
                    if setting.stopcharger_flag:
                        # 停止充电执行一次
                        json_packed = utils.pack2bytes(setting.cancel_charge)
                        s.send(json_packed)
                        setting.charge_status = False
                        setting.stopcharger_flag = False
                    continue

                # 计划任务模块执行
                move_flag, command_goal = planwork.get_planwork_command()
                if move_flag:
                    if command_goal["x"] == -8.460:
                        ic("执行充电命令。")
                        json_packed = utils.pack2bytes(setting.auto_charge_message)
                        s.send(json_packed)

                    else:
                        print(["执行导航，   ", command_goal])
                        json_packed = utils.pack2bytes(setting.cancel_charge)
                        s.send(json_packed)
                        json_packed = utils.pack2bytes(command_goal)
                        s.send(json_packed)
        s.close()
    except:
        print("错误的结束")
        debug.write_debug(debug.LINE(), "main---", traceback.print_exc())
    finally:
        s.close()

if __name__ == '__main__':
    main()
