#encoding:utf-8
import sys
import os
import math
import numpy as np
import serial

import utils
import dealfire
import setting
import errorflag
import fenbushi


def main():
    # 打开右传感器
    ser_r = utils.serial_open(setting.fenbushi_port,bps=9600)
    if ser_r == "error":
        sys.exit(errorflag.flag["001"])
    else:
        print("右传感器串口打开成功！")
        setting.ser_r = True
    fenbushi.get_ser_str_fen_none(ser_r)



if __name__ == '__main__':
    main()