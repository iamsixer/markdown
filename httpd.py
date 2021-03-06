#!/usr/bin/python
# coding: utf-8

import os
import sys
import urllib
import codecs
import glob
import commands
import time
import re
import BaseHTTPServer
import SocketServer

wwwpath = sys.argv[1]
pypath = os.path.realpath(sys.path[0]) 

actions = {
    "/editor":"/html/editor.html",
    "/":"/html/index.html",
}

def transDicts(params):
    dicts={}
    if len(params)==0:
        return
    params = params.split('&')
    for param in params:
        keyvalue = param.split('=')
        key = keyvalue[0]
        value = keyvalue[1]
        value = urllib.unquote_plus(value).decode("utf-8", 'ignore')
        dicts[key] = value
    return dicts

class WebRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.splitquery(self.path)
        action = query[0]
        queryParams = {}

        if '?' in self.path:
            if query[1]:#接收get参数
                queryParams = transDicts(query[1])
 
        fn = action 
        if action=='/getmd':
            name = 'temp.md'
            if queryParams.has_key('name'):
                name = queryParams['name']
            if name[-3:]!=".md":
                name += ".md"
            fn = "%s/md/%s" % (wwwpath,name)
        elif actions.has_key(action):
            fn = "%s%s" % (wwwpath, actions[action])
        else:
            fn = "%s%s" % (wwwpath, self.path)
        fn = fn.replace("/",os.sep)
        print(fn)
        
        content = ""
        if os.path.isfile(fn):
            f = open(fn, "rb")
            content = f.read()
            f.close()

        self.send_response(200)
        if fn[-3:]==".js":
            self.send_header("Content-type","application/x-javascript")
        elif fn[-4:]==".css":
            self.send_header("Content-type","text/css")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        content = ""
        if self.path=='/uploadimg':
            r,content = self.deal_post_img()
            if r:
                self.send_response(200)
            else:
                self.send_response(400)
        else:
            datas = self.rfile.read(int(self.headers['content-length']))
            queryParams = {}
            if datas:
                queryParams = transDicts(datas)
            if self.path=='/savemd':
                content = "保存失败"
                if queryParams.has_key('name') and queryParams.has_key('mdtext'):
                    name = queryParams['name']
                    mdtext = queryParams['mdtext']
                    fn = "%s/md/%s" % (wwwpath,name)
                    fn = fn.replace("/",os.sep)

                    f = codecs.open(fn, "w", "utf-8")
                    f.write(mdtext)
                    f.close()

                    content = "保存成功"
            elif self.path=='/update':
                content = "更新成功"
                cmd = "python %s/tohtml.py %s" % (pypath,wwwpath)
                status, output = commands.getstatusoutput(cmd)
                print(output)
            self.send_response(200)

        self.end_headers()
        self.wfile.write(content)

    def deal_post_img(self):
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line)
        if not fn:
            return (False, "Can't find out file name...")
        fn = "%s-%s" % (time.strftime("%Y-%m-%d"),fn[0])
        fname = "%s/img/%s" % (wwwpath,fn)
        fname = fname.replace("/",os.sep)
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        try:
            out = open(fname, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                 
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "%s" % fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")

class ThreadingServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

def run(port=8080):
    serveraddr = ('', port)
    serv = ThreadingServer(serveraddr, WebRequestHandler)
    print 'Server Started at port:', port
    serv.serve_forever()

if __name__=='__main__':
    run()

