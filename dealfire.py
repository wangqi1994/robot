#encoding:utf-8
import cv2
import math
import time
import numpy as np
import traceback
from datetime import datetime
from icecream import ic

import debug
import utils
import setting
import forMapFile

def time_str():
	return f'{datetime.now()}|> '
ic.configureOutput(prefix=time_str,includeContext=True)


# ===============判断啥时候可以获取角度：str==FNone ===============
def get_ser_str_f_none(ser_name):
    # print([ser_name, ser_name.in_waiting])
    if ser_name.in_waiting:
        # print("1111111")
        str_code = ser_name.read(1).decode("gb18030", "ignore")
        if str_code == "F":
            str_code_one = ser_name.read(4).decode("gbk")
            utils.print2txt(["收到数据1：", str_code_one])
            print("收到数据1：", str_code_one)
            if str_code_one == 'NONE':
                setting.find_fire_flag = True


# ===============判断啥时候可以获取角度：str==FNone ===============
def get_ser_str_f_none1(ser_name):
    # print([ser_name, ser_name.in_waiting])
    if ser_name.in_waiting:
        # print("1111111")
        str_code = ser_name.read(1).decode("gb18030", "ignore")
        if str_code == "F":
            str_code_one = ser_name.read(4).decode("gbk")
            utils.print2txt(["收到数据1：", str_code_one])
            print("收到数据1：", str_code_one)
            if str_code_one == 'NONE':
                setting.find_fire_flag = True

# ================获取单眼角度：angle================
def get_eye_angle(code_str):
    angle_list = code_str.split(',')
    float_angle_list = utils.str2float(angle_list)
    angle = utils.detect_outliter(float_angle_list)
    return angle
# ================获取单眼角度：angle================

# ===============
def get_ser_str(ser_name):
    eye_angle = 0
    if ser_name.in_waiting:
        str_code = ser_name.read(1).decode("gb18030", "ignore")
        if str_code == "A":
            str_code_one = ser_name.read(1).decode("gb18030", "ignore")
            print("R or L:", str_code_one)
            if str_code_one == 'R' or str_code_one == 'L':
                USART_flag = True
                str_code_plus = ""
                while USART_flag:
                    str_code_two = str(ser_name.read(1).decode("gb18030", "ignore"))
                    if str_code_two != 'D':
                        str_code_plus += str_code_two
                    else:
                        str_code_eye_angle = str_code_plus[:-1]
                        ser_name.close()
                        eye_angle = get_eye_angle(str_code_eye_angle)
                        break
    return eye_angle

# 传感器在中间和右边
def get_fire_pos1(α_angle, β_angle, pos):
    # 传感器的角度
    a = α_angle / 180 * math.pi
    b = β_angle / 180 * math.pi
    # 火源的位置坐标
    f_pos_x = None
    f_pos_y = None
    # ①非特殊角
    if 0 < a < 90 and 0 < b < 90:
        print(["火源在第一象限，0 < a < 90 and 0 < b < 90", a, b])
        f_pos_x = (0.3 * math.tan(a)) / (math.tan(b) - math.tan(a)) + 0.3
        f_pos_y = (0.3 * math.tan(a) * math.tan(b)) / (math.tan(b) - math.tan(a))
    elif 0 < a < 90 and 90 < b < 180:
        print(["火源在第一象限，0 < a < 90 and 90 < b < 180", a, b])
        f_pos_x = (0.3 * math.tan(b)) / (math.tan(b) - math.tan(a))
        f_pos_y = (0.3 * math.tan(a) * math.tan(b)) / (math.tan(b) - math.tan(a))
    elif 90 < a < 180 and 90 < b < 180:
        print(["火源在第二象限，90 < a < 180 and 90 < b < 180", a, b])
        f_pos_x = (0.3 * math.tan(b)) / (math.tan(b) - math.tan(a))
        f_pos_y = (0.3 * math.tan(a) * math.tan(b)) / (math.tan(b) - math.tan(a))
    elif 180 < a < 270 and 180 < b < 270:
        print(["火源在第三象限，180 < a < 270 and 180 < b < 270", a, b])
        f_pos_x = (0.3 * math.tan(b)) / (math.tan(a) - math.tan(b))
        f_pos_y = (0.3 * math.tan(a) * math.tan(b)) / (math.tan(a) - math.tan(b))
    elif 270 < a < 360 and 180 < b < 270:
        print(["火源在第四象限，270 < a < 360 and 180 < b < 270", a, b])
        f_pos_x = (0.3 * math.tan(b)) / (math.tan(b) - math.tan(a))
        f_pos_y = (0.3 * math.tan(a) * math.tan(b)) / (math.tan(a) - math.tan(b))
    elif 270 < a < 360 and 270 < b < 360:
        print(["火源在第四象限，270 < a < 360 and 270 < b < 360", a, b])
        f_pos_x = (0.3 * math.tan(b)) / (math.tan(b) - math.tan(a))
        f_pos_y = (0.3 * math.tan(a) * math.tan(b)) / (math.tan(a) - math.tan(b))
    # ②特殊角
    else:
        if a == 90 and 90 < b < 180:
            f_pos_x = 0
            f_pos_y = -0.3 * math.tan(b)
        elif a == 270 and 180 < b < 270:
            f_pos_x = 0
            f_pos_y = -0.3 * math.tan(b)
        elif b == 90 and 0 < a < 90:
            f_pos_x = 0.3
            f_pos_y = 0.3 * math.tan(a)
        elif b == 270 and 270 < a < 360:
            f_pos_x = 0.3
            f_pos_y = 0.3 * math.tan(a)
        else:
            print([a, b, "角度无法构成三角形！"])

    rb_x, rb_y, rb_yaw = pos
    para_1 = np.matrix([f_pos_x, f_pos_y, 1])
    para_2 = np.matrix([[math.cos(rb_yaw), math.sin(rb_yaw), 0],
                        [-math.sin(rb_yaw), math.cos(rb_yaw), 0],
                        [0, 0, 1]])
    para_3 = np.matrix([[1, 0, 0], [0, 1, 0], [rb_x, rb_y, 1]])
    out_num = para_1 * para_2 * para_3
    out_num_new = np.array(out_num)
    out_tuple = (out_num_new[0][0], out_num_new[0][1], out_num_new[0][2])
    f_ac_pos = (round(out_tuple[0], 4), round(out_tuple[1], 4))
    setting.find_fire_pos = [round(out_tuple[0], 4), round(out_tuple[1], 4)]
    print([f_ac_pos, a])
    return f_ac_pos, a

# 传感器在两边
def get_fire_pos(α_angle, β_angle, pos):
    # n° ---> nπ
    α_radian = α_angle / 180 * math.pi
    β_radian = β_angle / 180 * math.pi
    rad_1 = 2 * math.tan(α_radian) * math.tan(β_radian) / (math.tan(α_radian) + math.tan(β_radian))
    rad_2 = 2 * math.tan(α_radian)
    rad_3 = 2 * math.tan(β_radian)
    para_f_x = (math.tan(α_radian) + math.tan(β_radian)) / \
               (math.tan(β_radian) - math.tan(α_radian))
    para_f_y = (math.tan(α_radian) * math.tan(β_radian)) / \
               (math.tan(β_radian) - math.tan(α_radian))
    # 特殊值部分
    γ_angle = 0
    if (α_angle or β_angle) == (90 or 270):
        if α_angle == (90 or 270):
            # f_rc_pos : relative coordinates to the robot
            if α_angle == 90:
                f_rc_pos_x = 0.3
                f_rc_pos_y = -0.6 * math.tan(β_radian)
            else:
                f_rc_pos_x = -0.3
                f_rc_pos_y = -0.6 * math.tan(β_radian)
            # α= 90° 或 α= 270°时，γ的计算值+180°
            γ_radian = math.atan(rad_3)
            γ_angle = round(γ_radian * 180 / math.pi + 180, 1)
        else:
            if β_angle == 90:
                f_rc_pos_x = 0.3
                f_rc_pos_y = -0.6 * math.tan(α_radian)
                # β = 90°时，γ的值为原计算值
                γ_radian = math.atan(rad_2)
                γ_angle = round(γ_radian * 180 / math.pi, 1)
            else:
                f_rc_pos_x = 0.3
                f_rc_pos_y = 0.6 * math.tan(α_radian)
                # β = 270°时，γ的值为360°-原计算值
                γ_radian = math.atan(rad_2)
                γ_angle = round(360 - (γ_radian * 180 / math.pi), 1)
    else:
        if 0 < α_angle < 90:
            # case_01
            if 0 < β_angle < 90:
                γ_radian = math.atan(rad_1)
                γ_angle = round(γ_radian * 180 / math.pi, 1)
            # case_03
            if 90 < β_angle < 180:
                γ_radian = math.atan(rad_1)
                γ_origin_angle = round(γ_radian * 180 / math.pi, 1)
                if α_angle < 180 - β_angle:
                    γ_angle = γ_origin_angle
                if α_angle == 180 - β_angle:
                    γ_angle = 90.0
                if α_angle > 180 - β_angle:
                    γ_angle = γ_origin_angle + 180
        # case_05
        if 90 < α_angle < 180 and 90 < β_angle < 180:
            γ_radian = math.atan(rad_1)
            γ_angle = round(γ_radian * 180 / math.pi + 180, 1)
        # case_06
        if 180 < α_angle < 270 and 180 < β_angle < 270:
            γ_radian = math.atan(rad_1)
            γ_angle = round(γ_radian * 180 / math.pi + 180, 1)
        if 270 < α_angle < 360:
            # case_08
            if 180 < β_angle < 270:
                γ_radian = math.atan(rad_1)
                γ_origin_angle = round(γ_radian * 180 / math.pi + 180, 1)
                if 360 - α_angle < β_angle - 180:
                    # γ_angle = γ_origin_angle + 360
                    γ_angle = γ_origin_angle + 180
                if 360 - α_angle == β_angle - 180:
                    γ_angle = 270.0
                if 360 - α_angle > β_angle - 180:
                    γ_angle = γ_origin_angle + 180
                    # γ_angle = γ_origin_angle - 270
            # case_10
            elif 270 < β_angle < 360:
                γ_radian = math.atan(rad_1)
                γ_angle = round(γ_radian * 180 / math.pi + 360, 1)
            else:
                γ_angle = 0.0
                print("角度计算公式可能覆盖不全面，请继续完善！！！")
    # γ_angle = γ_angle - 90.0
    f_rc_pos_x = 0.3 * para_f_x
    f_rc_pos_y = 0.6 * para_f_y

    rb_x, rb_y, rb_yaw = pos
    para_1 = np.matrix([f_rc_pos_x, f_rc_pos_y, 1])
    para_2 = np.matrix([[math.cos(rb_yaw), math.sin(rb_yaw), 0],
                        [-math.sin(rb_yaw), math.cos(rb_yaw), 0],
                        [0, 0, 1]])
    para_3 = np.matrix([[1, 0, 0], [0, 1, 0], [rb_x, rb_y, 1]])
    out_num = para_1 * para_2 * para_3
    out_num_new = np.array(out_num)
    out_tuple = (out_num_new[0][0], out_num_new[0][1], out_num_new[0][2])
    f_ac_pos = (round(out_tuple[0], 4), round(out_tuple[1], 4))
    setting.find_fire_pos = [round(out_tuple[0], 4), round(out_tuple[1], 4)]
    return f_ac_pos, γ_angle

# 计算左眼角度
def get_left_angle_info(ser_l):
    try:
        print(["开始计算左眼角度"])
        ser_l.write("S".encode("gbk"))  # 启动左侧传感器
        print("左侧传感器打开")
        while True:
            ser_l.write("M".encode("gbk"))
            a = datetime.now()
            while True:
                b = datetime.now()
                if (b-a).seconds > 5:
                    setting.left_eye_angle = None
                    break
                str_code = ser_l.read(1).decode("gb18030", "ignore")
                if str_code == "A":
                    str_code_one = ser_l.read(1).decode("gb18030", "ignore")
                    # print("R or L:", str_code_one)
                    if str_code_one == 'R' or str_code_one == 'L':
                        USART_flag = True
                        str_code_plus = ""
                        while USART_flag:

                            c = datetime.now()
                            if (c - a).seconds > 5:
                                setting.left_eye_angle = None
                                break
                            str_code_two = str(ser_l.read(1).decode("gb18030", "ignore"))
                            if str_code_two != 'D':
                                str_code_plus += str_code_two
                            else:
                                str_code_eye_angle = str_code_plus[:-1]
                                # ser_l.close()
                                setting.left_eye_angle = get_eye_angle(str_code_eye_angle) + 20
                                break

                if setting.left_eye_angle:
                    print("左眼角度：", setting.left_eye_angle)
                    break
            # time.sleep(0.5)
            if setting.finish_fire:
                ser_l.write("X".encode("gbk"))
                ser_l.close()
                break
    except:
        print(["获取左眼角度失败--\n", traceback.print_exc()])
        debug.write_debug(debug.LINE(), "main---", traceback.print_exc())

# 计算右眼角度
def get_right_angle_info(ser_r):
    try:
        print(["开始右眼计算角度"])
        # ser_r.write("L".encode("gbk"))  # 关闭传感器数据
        # ser_r.reset_input_buffer()
        ser_r.write("S".encode("gbk"))  # 启动右侧传感器
        print("右侧传感器打开")
        while True:
            if setting.finish_fire and setting.penshui_end_flag:
                ser_r.write("X".encode("gbk"))
                print([time.strftime("%Y-%m-%d %X"), "瞄准完毕，初始化右眼。。。。。"])
            a = datetime.now()
            while True:
                b = datetime.now()
                if (b-a).seconds > 5:
                    setting.right_eye_angle = None
                    break
                str_code = ser_r.read(1).decode("gb18030", "ignore")
                if str_code == "A":
                    str_code_one = ser_r.read(1).decode("gb18030", "ignore")
                    # print("R or L:", str_code_one)
                    if str_code_one == 'R' or str_code_one == 'L':
                        USART_flag = True
                        str_code_plus = ""
                        while USART_flag:
                            c = datetime.now()
                            if (c-a).seconds > 5:
                                setting.right_eye_angle = None
                                break
                            str_code_two = str(ser_r.read(1).decode("gb18030", "ignore"))
                            if str_code_two != 'D':
                                str_code_plus += str_code_two
                            else:
                                str_code_eye_angle = str_code_plus[:-1]
                                # ser_r.close()
                                setting.right_eye_angle = get_eye_angle(str_code_eye_angle) + 15
                                break

                if setting.right_eye_angle:
                    print("右眼角度：", setting.right_eye_angle)
                    break
            ser_r.write("M".encode("gbk"))
            # time.sleep(0.5)
            if setting.finish_fire:
                ser_r.write("X".encode("gbk"))
                ser_r.close()
                break
    except:
        print(["获取右眼角度失败--\n", traceback.print_exc()])
        debug.write_debug(debug.LINE(), "main---", traceback.print_exc())

# 获取角度位置等信息
'''
def get_angle_info(ser_r, ser_l):
    print(["开始计算角度"])
    while True:
        if not setting.ser_open_flag:
            ser_r.write("L".encode("gbk"))  # 关闭传感器数据
            ser_r.reset_input_buffer()
            ser_r.write("S".encode("gbk"))  # 启动右侧传感器
            print("右侧传感器打开")
            ser_l.write("S".encode("gbk"))  # 启动左侧传感器
            print("左侧传感器打开")
            setting.ser_open_flag = True
        while True:
            # serial_open(ser_l)
            # left_eye_angle = get_ser_str(ser_l)
            left_eye_angle = None

            # if ser_l.in_waiting:
            str_code = ser_l.read(1).decode("gb18030", "ignore")
            if str_code == "A":
                str_code_one = ser_l.read(1).decode("gb18030", "ignore")
                print("R or L:", str_code_one)
                if str_code_one == 'R' or str_code_one == 'L':
                    USART_flag = True
                    str_code_plus = ""
                    while USART_flag:
                        str_code_two = str(ser_l.read(1).decode("gb18030", "ignore"))
                        if str_code_two != 'D':
                            str_code_plus += str_code_two
                        else:
                            str_code_eye_angle = str_code_plus[:-1]
                            # ser_l.close()
                            left_eye_angle = get_eye_angle(str_code_eye_angle)
                            break

            if left_eye_angle:
                print("左眼角度：", left_eye_angle)
                break
        while True:
            # right_eye_angle = get_ser_str(ser_r)
            right_eye_angle = None

            # if ser_r.in_waiting:
            str_code = ser_r.read(1).decode("gb18030", "ignore")
            if str_code == "A":
                str_code_one = ser_r.read(1).decode("gb18030", "ignore")
                print("R or L:", str_code_one)
                if str_code_one == 'R' or str_code_one == 'L':
                    USART_flag = True
                    str_code_plus = ""
                    while USART_flag:
                        str_code_two = str(ser_r.read(1).decode("gb18030", "ignore"))
                        if str_code_two != 'D':
                            str_code_plus += str_code_two
                        else:
                            str_code_eye_angle = str_code_plus[:-1]
                            # ser_r.close()
                            right_eye_angle = get_eye_angle(str_code_eye_angle)
                            break

            if right_eye_angle:
                print("右眼角度：", right_eye_angle)
                break
        rb_pos = [setting.robotPosx1, setting.robotPosy1, setting.robotPosyaw1]
        utils.print2txt(["当前机器人位置：--", rb_pos])
        fire_pos, deluge_gun_angle = get_fire_pos(left_eye_angle, right_eye_angle, rb_pos)
        print(["当前机器人位置：--", rb_pos, "水炮旋转角度：--", deluge_gun_angle])
        setting.deluge_gun_angle = deluge_gun_angle
        time.sleep(0.5)
        # if not setting.ser_open_flag:
        #     print("停止测试角度，跳出循环111111111111111")
        #     ser_r.write("A".encode("gbk"))  # 启动右侧传感器
        #     print("右侧传感器关闭")
        #     ser_l.write("A".encode("gbk"))  # 启动左侧传感器
        #     print("左侧传感器关闭")

# 获取角度位置等信息
def a_get_angle_info(ser_r, ser_l):
    while True:
        # serial_open(ser_l)
        left_eye_angle = get_ser_str(ser_l)
        if left_eye_angle:
            print("第二次左眼角度：", left_eye_angle)
            break
    while True:
        right_eye_angle = get_ser_str(ser_r)
        if right_eye_angle:
            print("第二次右眼角度：", right_eye_angle)
            break
    rb_pos = [setting.robotPosx1, setting.robotPosy1, setting.robotPosyaw1]
    utils.print2txt(["第二次当前机器人位置：--", rb_pos])
    fire_pos, deluge_gun_angle = get_fire_pos(left_eye_angle, right_eye_angle, rb_pos)
    print(["第二次当前机器人位置：--", rb_pos, "第二次水炮旋转角度：--", deluge_gun_angle])
    return deluge_gun_angle
'''
def set_deluge_gun_angle(ser1, deluge_gun_angle):
    # ser1 = utils.serial_open(setting.deluge_gun_port)
    dosend_str_code = "AS" + str(deluge_gun_angle) + "D"
    result = ser1.write(dosend_str_code.encode("gbk"))
    time.sleep(2)
    ser1.write("FN".encode("gbk"))
    ser1.close()

def set_head_angle(ser_h):
    start_angle = 0.00
    while True:
        head_status = False
        if setting.order_yuanhongwai_angle:
            head_angle = "AS" + str(setting.order_yuanhongwai_angle) + "D"
            ser_h.write(head_angle.encode("gbk"))
            # start_angle = setting.yuanhongwai_levelAngle
            setting.yuanhongwai_levelAngle1 = None
            head_status = True
            setting.order_yuanhongwai_angle = None
        else:
            if setting.finish_fire and setting.penshui_end_flag:
                ser_h.write("X".encode("gbk"))
                print([time.strftime("%Y-%m-%d %X"), "瞄准完毕，初始化云台。。。。。"])
                time.sleep(2)
                setting.penshui_end_flag = False

            if setting.shuipao_penshui_flag:
                print([time.strftime("%Y-%m-%d %X"), "瞄准完毕，开始喷水00000。。。。。"])
                ser_h.write("P".encode("gbk"))
                print([time.strftime("%Y-%m-%d %X"), "瞄准完毕，开始喷水11111。。。。。"])
                setting.shuipao_penshui_flag = False


            if setting.shuiyao_stop_penshui_flag:
                ser_h.write("O".encode("gbk"))
                print([time.strftime("%Y-%m-%d %X"), "未发现货源，停止喷水。。。。。"])
                setting.shuiyao_stop_penshui_flag = False

            if setting.angle_status_h and setting.yuanhongwai_pitchAngle:
                if abs(setting.yuanhongwai_pitchAngle) < 1:
                    start_angle_h = 0 - setting.yuanhongwai_pitchAngle - 11
                    head_angle = "AL" + str(start_angle_h) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    print([time.strftime("%Y-%m-%d %X"), "竖直瞄准时，微调的角度------：", start_angle_h, setting.yuanhongwai_pitchAngle])
                    head_status = True
                    setting.angle_status_h = False
                    setting.judge_angle_h = True
                else:
                    start_angle_h = 0 - setting.yuanhongwai_pitchAngle
                    head_angle = "AL" + str(start_angle_h) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    print([time.strftime("%Y-%m-%d %X"), "竖直瞄准时，转动到的角度：", start_angle_h, setting.yuanhongwai_pitchAngle])
                    head_status = True
                    # setting.angle_status_h = False
                    # setting.judge_angle_h = True
            '''
            if setting.angle_status and setting.miaozhun_flag and setting.setangle_right_flag:
                start_angle = 360 - setting.right_eye_angle
                head_angle = "AS" + str(start_angle) + "D"
                ser_h.write(head_angle.encode("gbk"))
                head_status = True
                setting.setangle_right_flag = False
            '''

            if setting.angle_status and setting.yuanhongwai_levelAngle:
                setting.miaozhun_flag = True
                if abs(setting.yuanhongwai_levelAngle) < 1:
                    start_angle = start_angle - setting.yuanhongwai_levelAngle + 1.3
                    if start_angle < 0:
                        start_angle = start_angle + 360
                    elif start_angle > 360:
                        start_angle = start_angle - 360
                    else:
                        pass
                    head_angle = "AS" + str(start_angle) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    head_status = True
                    setting.angle_status = False
                    setting.judge_angle = True
                else:
                    start_angle = start_angle - (setting.yuanhongwai_levelAngle / 2)
                    if start_angle < 0:
                        start_angle = start_angle + 360
                    elif start_angle > 360:
                        start_angle = start_angle - 360
                    else:
                        pass
                    head_angle = "AS" + str(start_angle) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    time.sleep(0.4)
                    head_status = True
                print([time.strftime("%Y-%m-%d %X"), "水平瞄准时，转动到的角度：", start_angle, "当前观察到的火源图像角度：", setting.yuanhongwai_levelAngle])
                # setting.angle_status = False
                # setting.judge_angle = True

            if setting.angle_status and not setting.miaozhun_flag:
                # pass
                '''
                if not setting.start_angle:
                    setting.start_angle = start_angle
                    if start_angle - 15 > 0:
                        setting.start_angle = start_angle
                if setting.find_flag < 2:
                    if setting.find_flag == 0:

                        # if start_angle == 0:
                        #     head_angle = "AL" + str(-60) + "D"
                        #     print([time.strftime("%Y-%m-%d %X"), "111111111111垂直转动高度", head_angle])
                        #     ser_h.write(head_angle.encode("gbk"))
                        #     while True:
                        #         ser_str = ser_h.read(1).decode("gb18030", "ignore")
                        #         # print([time.strftime("%Y-%m-%d %X"), "111111111111返回信息：", ser_str])
                        #         if ser_str == "R":
                        #             break
                        #         time.sleep(0.01)
                        if start_angle - 15 > 0:
                            start_angle = start_angle - 15
                            head_angle = "AS" + str(start_angle) + "D"
                            ser_h.write(head_angle.encode("gbk"))
                            head_status = True
                        else:
                            setting.find_flag = setting.find_flag + 1
                            start_angle = setting.start_angle
                    elif setting.find_flag == 1:
                        if start_angle + 15 < 360:
                            start_angle = start_angle + 15
                            head_angle = "AS" + str(start_angle) + "D"
                            ser_h.write(head_angle.encode("gbk"))
                            head_status = True
                        else:
                            setting.find_flag = setting.find_flag + 1
                '''
                if setting.head_flag == 3:
                    if start_angle > 340:
                        start_angle = start_angle + 10
                    else:
                        start_angle = start_angle + 15
                    if start_angle == 15:
                        start_angle_h = -20
                        head_angle = "AL" + str(start_angle_h) + "D"
                        ic([time.strftime("%Y-%m-%d %X"), "22222222111111111111垂直转动高度", head_angle])
                        ser_h.write(head_angle.encode("gbk"))
                        while True:
                            ser_str = ser_h.read(1).decode("gb18030", "ignore")
                            if ser_str == "R":
                                break
                            time.sleep(0.01)
                    setting.yuanhongwai_levelAngle1 = None
                    head_angle = "AS" + str(start_angle) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    head_status = True
                    if start_angle > 350:
                        # if setting.nishizhenshizhen_xuanzhuan_flag:
                        setting.head_flag = 4
                    ic([time.strftime("%Y-%m-%d %X"), "222222220000000------------头部旋转的角度：", start_angle])
                elif setting.head_flag == 4:
                    if start_angle < 1:
                        start_angle = 24.00
                    if start_angle > 350:
                        start_angle_h = -10
                        head_angle = "AL" + str(start_angle_h) + "D"
                        ic([time.strftime("%Y-%m-%d %X"), "22222222111111111111垂直转动高度", head_angle])
                        ser_h.write(head_angle.encode("gbk"))
                        while True:
                            ser_str = ser_h.read(1).decode("gb18030", "ignore")
                            if ser_str == "R":
                                break
                            time.sleep(0.01)
                    start_angle = start_angle - 15
                    setting.yuanhongwai_levelAngle1 = None
                    head_angle = "AS" + str(start_angle) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    head_status = True
                    if start_angle < 25:
                        setting.head_flag = 5
                    ic([time.strftime("%Y-%m-%d %X"), "22222222111111111111111---------------头部旋转的角度：", start_angle])

                ic([time.strftime("%Y-%m-%d %X"), "第二次观察当前角度为：", start_angle])

            if setting.yuanhongwai_levelAngle and not setting.angle_status and not setting.angle_status_h:
                yuanhongwai_levelAngle = start_angle - setting.yuanhongwai_levelAngle
                # print([time.strftime("%Y-%m-%d %X"), "摄像头测得的角度：", [setting.yuanhongwai_levelAngle, setting.yuanhongwai_pitchAngle], "当前头部旋转的角度：", start_angle])
                if yuanhongwai_levelAngle < 0:
                    yuanhongwai_levelAngle = yuanhongwai_levelAngle + 360
                setting.yuanhongwai_levelAngle1 = yuanhongwai_levelAngle
                setting.yuanhongwai_now_time1 = datetime.now()
                setting.head_flag = 2

            else:
                if setting.head_flag == 0:
                    # if setting.head_flag_angle_1:
                    #     start_angle = start_angle + 10
                    #     setting.head_flag_angle_1 = False
                    # else:
                        # if start_angle == 10:
                            # start_angle = start_angle + 20
                        # else:
                    if start_angle > 340:
                        start_angle = start_angle + 12
                    else:
                        start_angle = start_angle + 15
                    '''
                    if start_angle == 15:
                        head_angle = "AL" + str(-60) + "D"
                        print([time.strftime("%Y-%m-%d %X"), "111111111111垂直转动高度", head_angle])
                        ser_h.write(head_angle.encode("gbk"))
                        while True:
                            ser_str = ser_h.read(1).decode("gb18030", "ignore")
                            # print([time.strftime("%Y-%m-%d %X"), "111111111111返回信息：", ser_str])
                            if ser_str == "R":
                                break
                            time.sleep(0.01)
                    '''

                    setting.yuanhongwai_levelAngle1 = None
                    head_angle = "AS" + str(start_angle) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    head_status = True
                    if start_angle > 355:
                        # if setting.nishizhenshizhen_xuanzhuan_flag:
                        setting.head_flag = 1
                    print([time.strftime("%Y-%m-%d %X"), "0000000------------头部旋转的角度：", start_angle])
                elif setting.head_flag == 1:
                    if start_angle < 1:
                        start_angle = 360.00
                    if start_angle > 350:
                        start_angle_h = 0 - 20
                        head_angle = "AL" + str(start_angle_h) + "D"
                        print([time.strftime("%Y-%m-%d %X"), "111111111111垂直转动高度", head_angle])
                        ser_h.write(head_angle.encode("gbk"))
                        while True:
                            ser_str = ser_h.read(1).decode("gb18030", "ignore")
                            # print([time.strftime("%Y-%m-%d %X"), "111111111111返回信息：", ser_str])
                            if ser_str == "R":
                                break
                            time.sleep(0.01)
                    start_angle = start_angle - 15
                    setting.yuanhongwai_levelAngle1 = None
                    head_angle = "AS" + str(start_angle) + "D"
                    ser_h.write(head_angle.encode("gbk"))
                    head_status = True
                    if start_angle < 25:
                        # if not setting.nishizhenshizhen_xuanzhuan_flag:
                        setting.head_flag = 0
                    print([time.strftime("%Y-%m-%d %X"), "111111111111111---------------头部旋转的角度：", start_angle])
                else:
                    pass
            if head_status:
                while True:
                    ser_str = ser_h.read(1).decode("gb18030", "ignore")
                    if ser_str == "R":
                        break
                    time.sleep(0.01)
                if setting.angle_status and setting.yuanhongwai_levelAngle:
                    time.sleep(0.5)

        if setting.shuipao_angle > 0.01:
            dosend_str_code = "AL" + str(setting.shuipao_angle) + "D"
            ser_h.write(dosend_str_code.encode("gbk"))
            setting.shuipao_angle = 0.00
            while True:
                ser_str = ser_h.read(1).decode("gb18030", "ignore")
                if ser_str == "R":
                    break
                time.sleep(0.01)
        time.sleep(0.05)

def set_sp_angle(ser_p):
    while True:
        if setting.shuipao_angle > 0.01:
            dosend_str_code = "AS" + str(setting.shuipao_angle) + "D"
            ser_p.write(dosend_str_code.encode("gbk"))
            setting.shuipao_angle = 0.00
        time.sleep(0.3)

# =============获取地图文件=============
def do_get_map_file():
    real_pose = (setting.robotPosx1, setting.robotPosy1)
    # 读取图像， 将火源位置发出来
    img = cv2.imread(setting.mapfile, cv2.IMREAD_UNCHANGED)
    fire_pose = (setting.find_fire_pos[0], setting.find_fire_pos[1])

    c_goal = forMapFile.move_to(img, fire_pose, real_pose)
    return c_goal

if __name__ == "__main__":
    get_fire_pos1(165.152, 188.822, [0,1,0])