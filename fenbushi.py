#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import utils
import setting
import binascii
import configparser


def get_ser_str_fen_none(ser_f):
    n = 0
    while 1:
        data = str(binascii.b2a_hex(ser_f.read(1)))[2:-1]
        if data != "":
            if data == "bb":
                n = 1
            else:
                n = n + 1
            print([n, data])
            if data == "aa":
                n = 0
            if n == 4:
                setting.fen_find_fire_flag = True
                setting.fenbushi_num = data
                conf = configparser.ConfigParser()
                conf.read(setting.fenbushi_file)
                setting.robotPosx12 = conf[data]["robotPosx"]
                setting.robotPosy12 = conf[data]["robotPosy"]
                setting.robotPosyaw12 = conf[data]["robotPosyaw"]

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