#encoding:utf-8
import sys
import os
import math
import numpy as np
import serial

import utils
import setting
import errorflag


def main():
    # 打开右传感器
    ser_r = utils.serial_open("COM11", bps=9600)
    if ser_r == "error":
        sys.exit(errorflag.flag["001"])
    else:
        print("右传感器串口打开成功！")
        ser_r.write("X".encode("gbk"))  # 启动右侧传感器




if __name__ == '__main__':
    main()