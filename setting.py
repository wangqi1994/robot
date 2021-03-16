#encoding:utf-8
import os
import json
import time
import configparser


nowtime = time.strftime("%Y%m%d")
#【IP、mac等配置文件】
info_conf = "./config/info.conf"
#【程序报错文件】
debugfile = './log/debug%s.log' % nowtime
#【打印信息输出文件】
outputfile = './log/output%s.txt' % nowtime
#【计划任务文件】
planworkfile = "./config/planworkfile.conf"

if not os.path.exists(info_conf):
	print("IP,MAC配置文件不存在！！")
conf = configparser.ConfigParser()
conf.read(info_conf)
server_ip = conf["info"]["server_ip"]
host_mac = conf["info"]["host_mac"]
robot_mac = conf["info"]["robot_mac"]
mincharge = conf["info"]["mincharge"]
maxcharge = conf["info"]["maxcharge"]
right_eye_port = conf["info"]["right_eye_port"]
left_eye_port = conf["info"]["left_eye_port"]
deluge_gun_port = conf["info"]["deluge_gun_port"]
fenbushi_port = conf["info"]["fenbushi_port"]
yuanhongwai_port = conf["info"]["yuanhongwai_port"]

# [APP服务端]
robotname = ''
appserverip = conf["info"]["appserverip"]

# 是否欠费锁机标志
shutdown_flag = False

# 是否清楚故障报警
clear_warning = False

# 小车故障报警
fault_warning_flag = False

# 巡视异常报警
running_warning_flag = False

#【充电标志、停止充电标志、充电状态标志】
num_charge = 0
charge_flag = False
stopcharger_flag = False
charge_status = False

#【电池电量】
robotcharge = "0.00"

#【小车头部信息】
head_now_angle = 0.00
shuipao_angle = 0.00
head_flag = None
head_flag_angle_1 = False
head_flag_fuwei = False
head_0_flag = False
nishizhenshizhen_xuanzhuan_flag = False
xuanzhuan_flag = 0
judge_angle = False
angle_status = False
judge_angle_h = False
angle_status_h = False
start_angle = None
find_flag = 0
shuipao_penshui_flag = False
shuiyao_stop_penshui_flag = False
second_find_flag = False
miaozhun_flag = False
penshui_end_flag = False
shuipao_taigao = False
dan_miaozhun_flag = False
setangle_right_flag = False

#【当前工作】
workingstatus = ""

#【计划巡逻列表】
poilist = []
fenbushi_poilist = []

#【目标位置坐标】
goal_position = []

# 【1.传感器状态】
ser_r = False
ser_h = False
ser_p = False
ser_f = False

# 【2.摄像头开启状态】
camera_status = False

# 【3.程序启动时间】
run_time = 0

# 【4.机器人导航里程】
distance = 0.00

#【发现火源标志】
find_fire_flag = False
find_fire_pos = []
finish_fire = False

#【分布式传感器配置文件】
fenbushi_file = "./config/fenbushi.conf"

# 【分布式传感器发现火源】
fen_find_fire_flag = False
fenbushi_num = ''

#[分布式传感器位置]
robotPosx12 = 0.000
robotPosy12 = 0.000
robotPosyaw12 = 0.00

#[机器人目标位置]
robotPosx13 = 0.000
robotPosy13 = 0.000
robotPosyaw13 = 0.00

#【串口打开标志】
ser_right_open_flag = False
ser_left_open_flag = False
deluge_gun_angle = None

#【左右眼角度】
left_eye_angle = None
right_eye_angle = None

#【远红外角度】
order_yuanhongwai_angle = None
yuanhongwai_levelAngle = None
yuanhongwai_pitchAngle = None
yuanhongwai_need_find_angle = False

yuanhongwai_levelAngle1 = None
yuanhongwai_pitchAngle1 = None
# 【远红外摄像头实时信息】
yuanhongwai_now_time = None
yuanhongwai_now_time1 = None

#[机器人当前位置]
last_robotPosx1 = 0.00
chongfu_command = 0
robotPosx1 = 0.00
robotPosy1 = 0.00
robotPosyaw1 = 0.00
now_angle = None

#[充电前位置]
robotPosx11 = -8.277
robotPosy11 = -6.048
robotPosyaw11 = 270.767


#【地图文件】
mapfile = "./map.png"

# 注册命令
reg_client_message = {
    "message_type": "register_client",
    "client_type": 3,
    "mac_address": host_mac}

# 获取所有机器人信息
get_all_robot_info_message = {
    "message_type": "get_all_robot_info"}

# 重定位
reset_message = {
    "message_type": "reset",
    "mac_address": robot_mac,
}  # 搜索角度范围（yaw-search_yaw，yaw+search_yaw）


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
    "file_name": "map.png"
}
# -----------------获取地图文件-----------------

# 移动到指定位置与原地旋转（自动导航避障），导航至（detector_x，detector_y，detector_yaw）位置
command_goal = {
    "message_type": "command_goal",
    "robot_mac_address": robot_mac,
    "x": 0.00,
    "y": 0.00,
    "yaw": 0.00,
    # "only_rot": "true",
    # "relative_rot": "true"
}
command_goal1 = {
    "message_type": "command_goal",
    "robot_mac_address": robot_mac,
    "yaw": 0.00,
    "only_rot": "true"
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
    # "charge_point_name": "charge0",
    "position": {"x": -8.460, "y": -5.078, "yaw": 266.478}
}

# 取消充电
cancel_charge = {
    "message_type": "cancel_charge",
    "robot_mac_address": robot_mac,
}

# 取消导航任务（并停止）
cancel_goal = {
    "message_type": "cancel_goal",
    "robot_mac_address": robot_mac, }

# 自动充电
charge_message = {
    "message_type": "charge",
    "robot_mac_address": robot_mac, }

