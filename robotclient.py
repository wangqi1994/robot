#encoding:utf-8
import time
import math
import json
import struct
import base64
import socket
import threading
import configparser
import subprocess
import traceback
from datetime import datetime

import debug
import setting
import utils

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
            # pass
            pasmsg = utils.receive2dic(self.s)
            print(["RecvTread-pasmsg", pasmsg, type(pasmsg)])
            # # 判断是否要欠费停机
            # utils.judge_no_money_shutdown(pasmsg)
            # # 判断是否要清除故障报警
            utils.judge_clear_warning(pasmsg)
            # # 判断开启关闭摄像头
            # utils.judge_status_camera(pasmsg)
            # # 判断开启关闭摄像头
            # utils.judge_robot_shutdown(pasmsg)

class Server_Socket(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.tcp_server.bind(("127.0.0.1", 8282))
        self.tcp_server.listen(100)

    def run(self):
        tcp_client = None
        try:
            while 1:
                tcp_client, tcp_client_address = self.tcp_server.accept()
                # recv_data = tcp_client.recv(1024)
                recv_data = utils.receive2dic(tcp_client)
                print("接收客户端的数据为:", recv_data)
                rtn1 = {"message_type": "getmessage_success"}
                json_packed = utils.pack2bytes(rtn1)
                tcp_client.send(json_packed)
                tcp_client.close()
        except:
            if tcp_client:
                tcp_client.close()

    def stop(self):
        # 关闭服务端的套接字, 终止和客户端提供建立连接请求的服务 但是正常来说服务器的套接字是不需要关闭的，因为服务器需要一直运行。
        self.tcp_server.close()

def get_ping_result():
    ret = 1
    ip = setting.appserverip
    p = subprocess.Popen(["ping.exe", ip], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    out = p.stdout.read().decode('gbk')
    find_str = "(0% 丢失)"
    print(["APP的IP通信情况：  ", out])
    if find_str in out:
        ret = 0
    return ret

def selfcheck():
    try:
        # 1.传感器信息
        ser_r = setting.ser_r
        ser_h = setting.ser_h
        ser_p = setting.ser_p
        ser_f = setting.ser_f
        cgq_ser_err = []
        if not ser_r:
            cgq_ser_err.append("001")
        if not ser_h:
            cgq_ser_err.append("002")
        if not ser_p:
            cgq_ser_err.append("003")
        if not ser_f:
            cgq_ser_err.append("004")
        # 2.摄像头开启状态
        camera_status = setting.camera_status
        # 3.电池电量、电压、温度
        robot_charge = setting.robotcharge
        # 4.运行时间
        starttime = setting.run_time
        starttime = datetime.now()  #赋值不就覆盖了？
        time.sleep(0.1)
        nowtime = datetime.now()
        time_seconds = (nowtime - starttime).seconds
        # 5.里程
        distance = setting.distance
        # 6.分布式传感器
        ds_sor_errs = []
        rtn = {"message_type": "self_check", "status": {"robotname":setting.robotname,"cgq_ser_err": cgq_ser_err,"camera_status": camera_status, "robot_charge": robot_charge,
               "runtime": time_seconds, "distance": distance, "ds_sors": ds_sor_errs}}
        return rtn
    except:
        debug.write_debug(debug.LINE(), "selfcheck-error---", traceback.print_exc())

def robotclient():
    try:
        while get_ping_result():
            time.sleep(5)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((setting.appserverip, 8082))

        lastrtn = {}
        RecvTread(s).start()

        # Server_Socket().start()
        i = 0
        while True:
            rtn = selfcheck()
            if i == 0 or rtn["status"]["cgq_ser_err"] != lastrtn["status"]["cgq_ser_err"] or \
                    rtn["status"]["camera_status"] != lastrtn["status"]["camera_status"]:
                json_packed = utils.pack2bytes(rtn)
                print([123456, json_packed])
                s.send(json_packed)
            lastrtn = rtn
            if setting.find_fire_flag:
                # 火警报警
                rtn1 = {"message_type": "find_fire", "status": {"robotname":setting.robotname}}
                json_packed = utils.pack2bytes(rtn1)
                print(json_packed)
                s.send(json_packed)
            if setting.fault_warning_flag:
            # if 1 == 10:
                # 运行故障报警
                rtn1 = {"message_type": "fault_warning", "status": {"robotname":setting.robotname}}
                json_packed = utils.pack2bytes(rtn1)
                print(json_packed)
                s.send(json_packed)
            if setting.running_warning_flag:
            # if 1 == 1:
                # 巡视异常报警
                rtn1 = {"message_type": "running_warning", "status": {"robotname":setting.robotname}}
                json_packed = utils.pack2bytes(rtn1)
                print(json_packed)
                s.send(json_packed)
            i = i + 1
            if i == 10:
                i = 0
            print(time.strftime("%Y-%m-%d %X"))
            time.sleep(10)
        s.close()
    except:
        Server_Socket().stop()
        s.close()
        print("错误的结束")
        debug.write_debug(debug.LINE(), "selfcheck-error---", traceback.print_exc())

if __name__ == "__main__":
    robotclient()














