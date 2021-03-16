#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import utils
import setting
import binascii
import configparser


def get_ser_str_fen_none(ser_f):
    n = 0
    flag = None
    flag_num = 0
    while 1:
        data = str(binascii.b2a_hex(ser_f.read(1)))[2:-1]
        if data != "":
            if data == "bb":
                n = 1
            else:
                n = n + 1
            # print([n, data])
            if data == "aa":
                n = 0
            if n == 3:
                if data == "01":
                    # print("data[3] == 01")
                    head_angle = "BBCC010001DDAA"
                    ser_f.write(head_angle.encode("gbk"))
                elif data == "02":
                    flag_num = flag_num + 1
                    flag = "fire_poi"
                else:
                    flag_num = 0
                    flag = None
            if n == 4:
                if flag == "fire_poi" and flag_num > 5:
                    setting.fen_find_fire_flag = True
                    setting.fenbushi_num = data
                    if len(setting.fenbushi_poilist) > 0:
                        pass
                    else:
                        conf = configparser.ConfigParser()
                        conf.read(setting.fenbushi_file)
                        pois = conf[data]["poilist"].split(";")
                        for poi in pois:
                            zs = poi.split(",")
                            # print(zs)
                            for ix in range(len(zs)):
                                zs[ix] = float(zs[ix])
                            setting.fenbushi_poilist.append(zs)
            # print(setting.fenbushi_poilist)

def get_ser_str_fen_none1(ser_l):
    n = 0
    while 1:
        data = str(binascii.b2a_hex(ser_l.read(1)))[2:-1]
        if data != "":
            if data == "bb":
                n = 1
            else:
                n = n + 1
            # print([n, data])
            if data == "aa":
                n = 0
            if n == 3:
                if data == "02":
                    setting.find_fire_flag = True

if __name__ == "__main__":
    get_ser_str_fen_none('111')