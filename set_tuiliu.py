# encoding: utf-8
import requests
import re
import time
import hashlib
import datetime
def md5sum(src):
    m = hashlib.md5()
    m.update(src)
    return m.hexdigest()
def a_auth(uri, key, exp):
    p = re.compile("^(rtmp://)?([^/?]+)(/[^?]*)?(\\?.*)?$")
    if not p:
        return None
    m = p.match(uri)
    scheme, host, path, args = m.groups()
    if not scheme: scheme = "rtmp://"
    if not path: path = "/"
    if not args: args = ""
    rand = "0"      # "0" by default, other value is ok
    uid = "0"       # "0" by default, other value is ok
    sstring = "%s-%s-%s-%s-%s" %(path, exp, rand, uid, key)
    hashvalue = md5sum(sstring.encode('utf-8'))
    auth_key = "%s-%s-%s-%s" %(exp, rand, uid, hashvalue)
    if args:
        return "%s%s%s%s&auth_key=%s" %(scheme, host, path, args, auth_key)
    else:
        return "%s%s%s%s?auth_key=%s" %(scheme, host, path, args, auth_key)
def md5(str):
    md5 = hashlib.md5()
    md5.update(str.encode('utf-8'))
    return md5.hexdigest()
def GetCookie():
    cur_time = int(time.time())
    s=requests.session()
    print(s.cookies.get_dict())#先打印一下，此时一般应该是空的。
    loginUrl='http://192.168.137.53/goform/formLogin'
    postData='username=admin&tid='+str(cur_time)+'&access='+md5(str(cur_time)+":"+'123456')
    rs=s.post(loginUrl,postData)
    c=requests.cookies.RequestsCookieJar()#利用RequestsCookieJar获取
    c.set('cookie-name','cookie-value')
    s.cookies.update(c)
    cookie_dict = s.cookies.get_dict()
    return cookie_dict['wsid']
def main():
    wsid = GetCookie()
    uri = "rtmp://chuangneng.shengtu.info/live/streamname"            # original uri
    key = "eGG4Fb2mgYqBnTg6"                         # private key of     authorization
    exp = int(time.time()) + 1 * 3600                   # expiration     time: 1 hour after current itme
    authuri = a_auth(uri, key, exp)                     # auth type:
    url = 'http://192.168.137.53/action/set?subject=rtmp'
    header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
	"Accept": "*/*",
	"Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
	"Accept-Encoding": "gzip, deflate",
	"Content-Type": "text/plain;charset=UTF-8",
	"Content-Length": "395",
	"Origin": "http://192.168.137.53",
	"Connection": "keep-alive",
	"Referer": "http://192.168.137.53/subpages/rtmp.html",
	"Cookie": "bvusername=admin; wsid="+wsid+"; bvlanguage=Chinese; bvpassword=e10adc3949ba59abbe56e057f20f883e"
	}

    body = '''<?xml version="1.0" encoding="utf-8"?>
	<request>
		<rtmp ver="2.0">
			<port>1935</port>
			<youtube_compatible>0</youtube_compatible>
			<push>
				<active>1</active>
				<url>'''
    body += authuri+"</url>"
    body +=	'''<url></url>
				<tsection>0-86400</tsection>
				<tsection>0-0</tsection>
				<tsection>0-0</tsection>
				<tsection>0-0</tsection>
			</push>
		</rtmp>
	</request>'''
    r = requests.post(url, data=body.encode("utf-8"),headers=header)
    print(r)
    print(authuri)
    #print("URL : %s\nAUTH: %s" %(uri, authuri))"""
if __name__ == "__main__":
    main()