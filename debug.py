#encoding:utf-8
import os
import sys
import time
import traceback
import setting

debugfile = setting.debugfile

def LINE():
    return traceback.extract_stack()[-2][1]

def write_debug(line, module, errdata = None):
    nowtime = time.strftime("%Y-%m-%d %X")
    if errdata is None:
        err_data = '\n %s %s [line:%s]: ' %(nowtime,module,line)
        f = open(debugfile,'a+')
        f.write(err_data)
        traceback.print_exc(file = f)
        f.flush()
        f.close()
    else:
        #print >> sys.stderr,'%s %s [line:%s]: %s' %(nowtime,module,line,errdata)
        err_data = '\n %s %s [line:%s]: %s\n' %(nowtime,module,line,errdata)
        print('%s -------%s' %('11111', err_data))
        f = open(debugfile,'a+')
        f.write(err_data)
        #traceback.print_exc(file = f)
        f.flush()
        f.close()


