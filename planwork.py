#encoding:utf-8
import configparser
import traceback
import math

import setting
import debug
import utils

def getplanwork():
    conf = configparser.ConfigParser()
    conf.read(setting.planworkfile)
    sections = conf.sections()
    for i in sections:
        starttime = conf[i]["starttime"]
        endtime = conf[i]["endtime"]
        if utils.JudjeTime(starttime,endtime).judje():
            if setting.workingstatus == i:
                if len(setting.poilist) > 0:
                    break
                continue
            else:
                setting.workingstatus = i
                list1 = []
                if len(conf[i]["poilist"]) > 1:
                    pois = conf[i]["poilist"].split(";")
                    for poi in pois:
                        zs = poi.split(",")
                        for ix in range(len(zs)):
                            zs[ix] = float(zs[ix])
                        list1.append(zs)
                setting.poilist = list1
                break

def get_planwork_command():
    try:
        move_flag = False
        command_goal = {}
        if len(setting.poilist) > 0:
            if setting.goal_position == []:
                setting.goal_position = setting.poilist.pop(0)
                move_flag = True
            else:
                if utils.judge_arrive_flag(setting.goal_position[0], setting.goal_position[1], setting.robotPosx1, setting.robotPosy1, 0.1):
                    utils.print2txt("到达目标附件！")
                    utils.print2txt(["当前机器人位置：--", setting.robotPosx1, setting.robotPosy1])
                    print("到达目标附件！")
                    print(["当前机器人位置：--", setting.robotPosx1, setting.robotPosy1])
                    print(["目标位置：--", setting.goal_position[0], setting.goal_position[1]])
                    setting.goal_position = setting.poilist.pop(0)  #这是个啥操作
                    move_flag = True  #是不是需要这样
                else:
                    utils.print2txt("未到达目标附近！")
                    utils.print2txt(["当前机器人位置：--", setting.robotPosx1, setting.robotPosy1])
                    print("未到达目标附近！")
                    print(["当前机器人位置：--", setting.robotPosx1, setting.robotPosy1])
                    print(["目标位置：--", setting.goal_position[0], setting.goal_position[1]])
        if move_flag:
            command_goal = setting.command_goal
            command_goal["x"] = setting.goal_position[0]
            command_goal["y"] = setting.goal_position[1]
            command_goal["yaw"] = setting.goal_position[2]
        return move_flag, command_goal
    except:
        debug.write_debug(debug.LINE(), "main---", traceback.print_exc())