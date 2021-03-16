#encoding:utf-8

import setting

def get_dump_energy(msg):
    dump_energy = ""
    if msg['message_type'] == 'report_obd_status':
        # 修改后
        obd_list = msg['obd'].split(" ")
        voltage = obd_list[0]
        ampere = obd_list[1]
        dump_energy = obd_list[5]
        setting.robotcharge = dump_energy
        if setting.charge_status:
            if float(dump_energy) >= float(setting.maxcharge):
                setting.stopcharger_flag = True
        else:
            if float(dump_energy) <= float(setting.mincharge):
                print(["充电计数：", setting.num_charge])
                if setting.num_charge > 5:
                    setting.num_charge = 0
                    setting.charge_flag = True
                    setting.charge_status = True
                else:
                    setting.num_charge = setting.num_charge + 1
            else:
                setting.num_charge = 0
    return dump_energy

