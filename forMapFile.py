# import base64
import numpy as np
import math
import cv2
# from Firerobot.firerobot_backend.firerobot_backend.server import receive2dic, Utils, command_goal, pack2bytes


def pix2me(size, _pix):
    col = size[0] / 2
    row = size[1] / 2
    _x = (_pix[0] - row) * 0.05000000074505806
    _y = (col - _pix[1]) * 0.05000000074505806
    return _x, _y


def me2pix(size, me):
    col = size[0] / 2
    row = size[1] / 2
    _x = me[0] / 0.05000000074505806 + row
    _y = col - me[1] / 0.05000000074505806
    return int(_x), int(_y)


def search_fire(image, fire_pose, robot_pose):
    maps = image
    maps_size = np.array(maps)  # 获取图像行和列大小
    height = maps_size.shape[0]  # 行数->y
    width = maps_size.shape[1]  # 列数->x

    star = {'pose': robot_pose, 'cost': 700, 'parent': robot_pose}  # 起点
    end = {'pose': fire_pose, 'cost': 0, 'parent': fire_pose}  # 终点

    open_list = []  # open列表，存储可能路径
    close_list = [star]  # close列表，已走过路径
    step_size = 2  # 搜索步长。
    # 步长太小，搜索速度就太慢。步长太大，可能直接跳过障碍，得到错误的路径
    # 步长大小要大于图像中最小障碍物宽度
    count_time = 0
    while True:
        count_time += 1
        s_point = close_list[-1]['pose']  # 获取close列表最后一个点位置，S点
        add = ([0, step_size], [0, -step_size], [step_size, 0], [-step_size, 0])  # 可能运动的四个方向增量
        for i in range(len(add)):
            x = s_point[0] + add[i][0]  # 检索超出图像大小范围则跳过
            if x < 0 or x >= width:
                continue
            y = s_point[1] + add[i][1]
            if y < 0 or y >= height:  # 检索超出图像大小范围则跳过
                continue
            r_cost = np.sqrt(pow((x - star['pose'][0]), 2) + pow((y - star['pose'][1]), 2))  # 计算机器人代价
            f_cost = np.sqrt(pow((x - end['pose'][0]), 2) + pow((y - end['pose'][1]), 2))  # 计算火源代价
            t_cost = r_cost + f_cost  # 总代价
            if f_cost < 20:  # 当逐渐靠近终点时，搜索的步长变小
                step_size = 1
            add_point = {'pose': (x, y), 'cost': t_cost, 'parent': s_point}  # 更新位置
            count = 0
            for m in open_list:
                if m['pose'] == add_point['pose']:
                    count += 1
            for m in close_list:
                if m['pose'] == add_point['pose']:
                    count += 1
            if count == 0:  # 新增点不在open和close列表中
                if maps[y, x] >= 220:  # 非障碍物
                    open_list.append(add_point)
        t_point = {'pose': robot_pose, 'cost': 10000, 'parent': robot_pose}
        for j in range(len(open_list)):  # 寻找代价最小点
            if open_list[j]['cost'] < t_point['cost']:
                t_point = open_list[j]
        for j in range(len(open_list)):  # 在open列表中删除t点
            if t_point == open_list[j]:
                open_list.pop(j)
                break
        close_list.append(t_point)  # 在close列表中加入t点
        if t_point['pose'] == end['pose']:  # 找到终点！！
            print("找到终点")
            break

        if count_time > 15000:
            print('路径求解超时')
            break
    # 逆向搜索找到路径
    road = [close_list[-1]]
    point = road[-1]

    while True:
        for i in close_list:
            if i['pose'] == point['parent']:  # 找到父节点
                point = i
                road.append(point)
        if point == star:
            print("路径搜索完成")
            break

    for i in road:  # 返回该到的路径点
        # cv2.circle(information_map, i['pose'], 1, (0, 0, 200), -1)
        # 如果路径点与火源的距离大于3m小于10m，发送位置信息
        dis = np.sqrt(pow((i['pose'][0] - fire_pose[0]), 2) + pow((i['pose'][1] - fire_pose[1]), 2))
        m_dis = dis * 0.05000000074505806
        if 10 >= m_dis >= 3:
            m_pose = pix2me(image.shape, i['pose'])
            return m_pose


def move_back(image, fire_pose, robot_pose):
    robot_pose = pix2me(image.shape, robot_pose)
    return robot_pose


def search_five(image, fire_pose, robot_pose):
    maps = image
    maps_size = np.array(maps)  # 获取图像行和列大小
    height = maps_size.shape[0]  # 行数->y
    width = maps_size.shape[1]  # 列数->x

    star = {'pose': fire_pose, 'cost': 0, 'parent': fire_pose}  # 起点

    open_list = []  # open列表，存储可能路径
    close_list = [star]  # close列表，已走过路径
    back_list = []  # 用于存储距离大于5m，并且位置在机器人与火源的射线周边上
    count_time = 0

    while True:
        count_time += 1
        s_point = close_list[-1]['pose']    # 获取close列表最后一个点位置，S点
        add = ([0, 1],              # 上
               [0, -1],             # 下
               [1, 0],              # 右
               [-1, 0],             # 左
               )                            # 可能运动的四个方向增量
        for i in range(len(add)):
            x = s_point[0] + add[i][0]  # 检索超出图像大小范围则跳过
            if x < 0 or x >= width:
                continue
            y = s_point[1] + add[i][1]
            if y < 0 or y >= height:  # 检索超出图像大小范围则跳过
                continue
            r_cost = np.sqrt(pow((x - star['pose'][0]), 2) + pow((y - star['pose'][1]), 2))  # 计算火源代价
            add_point = {'pose': (x, y), 'cost': r_cost, 'parent': s_point}  # 更新位置
            count = 0
            for m in open_list:
                if m['pose'] == add_point['pose']:
                    count += 1
            for m in close_list:
                if m['pose'] == add_point['pose']:
                    count += 1
            if count == 0:  # 新增点o不在pen和close列表中
                if maps[y, x] >= 220:  # 非障碍物
                    open_list.append(add_point)

                    #需要 > 3m
                    if (3 / 0.05000000074505806) <= open_list[-1]['cost'] <= (10 / 0.05000000074505806):
                        final_pose = open_list[-1]['pose']
                        d1 = np.array([fire_pose[0] - robot_pose[0], fire_pose[1] - robot_pose[1]])
                        d2 = np.array([fire_pose[0] - final_pose[0], fire_pose[1] - final_pose[1]])
                        lx = np.sqrt(d1.dot(d1))
                        ly = np.sqrt(d2.dot(d2))
                        cos_angle = d1.dot(d2) / (lx * ly)
                        angle = np.arccos(cos_angle)
                        if angle < math.pi / 2:
                            m_pose = pix2me(image.shape, open_list[-1]['pose'])
                            print("找到的位置正好在机器人后方，机器人向后方移动")
                            return m_pose
                        else:
                            back_list.append(open_list[-1])
            close_list.append(add_point)    # 表示已经走过的路径
        if close_list[-1]['cost'] > (10 / 0.05000000074505806):
            break
    for back_pose in back_list:
        mx = back_pose['pose'][0]
        my = back_pose['pose'][1]
        k = (robot_pose[1] - fire_pose[1]) / (robot_pose[0] - fire_pose[0])
        y = k * (mx - fire_pose[0]) + fire_pose[1]
        if (k > 0 and my >= y) or (k < 0 and my <= y):
            print('机器人左前方有安全位置，机器人先向左移动，再向前移动到安全位置')
            return move_back(image, fire_pose, robot_pose)
        else:
            print('机器人右前方有安全位置，机器人先向右移动，再向前移动到安全位置')
            return move_back(image, fire_pose, robot_pose)
    print('安全位置求解失败，火源周围10m is not 安全距离，直接让机器人移动到稍远的地方')
    return move_back(image, fire_pose, robot_pose)


def move_to(image, fire_pose, robot_pose):
    distance = np.sqrt(pow((fire_pose[0] - robot_pose[0]), 2) + pow((fire_pose[1] - robot_pose[1]), 2))
    print(distance)
    if distance > 10:
        f_pose = search_fire(image, me2pix(image.shape, fire_pose), me2pix(image.shape, robot_pose))
    elif 3 <= distance <= 10:
        f_pose = robot_pose
    else:
        f_pose = search_five(image, me2pix(image.shape, fire_pose), me2pix(image.shape, robot_pose))
    print(f_pose)
    return f_pose


# def do_get_map_file(s):
#     # 获取图像信息
#     for i in range(100):
#         msg = receive2dic(s)
#         if 'content' in msg.keys():
#             sss = msg['content']
#             temp = base64.b64decode(sss)
#             with open('./' + "map.png", "wb") as fp:
#                 fp.write(temp)
#             break
#
#     real_pose = ()
#
#     # 获取机器人位置
#     for i in range(100):
#         msg = receive2dic(s)
#         if msg['message_type'] == 'report_pos_vel_status':
#             ss_pose = msg['pose']
#             real_pose = (ss_pose['x'], ss_pose['y'])
#             break
#     # 读取图像， 将火源位置发出来
#     img = cv2.imread('./map.png', cv2.IMREAD_UNCHANGED)
#     image = img
#
#     i_size = img.shape
#     print(i_size)
#     cv2.namedWindow('src')
#     cv2.setMouseCallback('src', on_mouse)
#     cv2.imshow('src', img)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
#
#     para = Utils.getParameters()
#     fire_pose_str = para["fire_pos"]
#     fire_pose = fire_pose_str[1: -1].split(',')
#
#     robot_pose = real_pose
#
#     c_goal = move2fire(image, me2pix(fire_pose), me2pix(robot_pose))
#     command_goal['x'] = c_goal[0]
#     command_goal['y'] = c_goal[1]
#     print('goal: ', command_goal)
#     json_packed = pack2bytes(command_goal)
#     s.send(json_packed)
#     global Fire_Flag
#     Fire_Flag = False

