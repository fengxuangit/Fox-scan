#!/usr/bin/env python
#!-*- coding:utf-8 -*-
import json
import time
import sys
import requests
import re
import urllib2
import base64
import threading
import multiprocessing
import ipdb
from urlparse import urlparse
from func import XMLDOM,Tools,SPIDER_HEADER,getrootdomain
from bs4 import BeautifulSoup
from models import MySQLHander

HEADER={'Content-Type': 'application/json'}

#定义MYSQL句併
mysql = MySQLHander()

#threading锁
lock = threading.Lock()

#taskid的队列
taskid_thread_Dict=[]

global writelist,blacklist,rootdomain,blackdomain

def setting_init():
    sql = "select writelist,blacklist,rootdomain,blackdomain from settings where id=1"
    mysql.query(sql)
    resource = mysql.fetchOneRow()
    self.writelist,self.blacklist,self.rootdomain,self.blackdomain = list(resource)

class SqlMapAction(object):
    def __init__(self):
        xml = XMLDOM()
        self.db = MySQLHander()
        self.address = xml.GetElementByName('sqlmap').strip()

    def _get_server(self):
        sql = "select server from settings where id = 1"
        self.db.query(sql)
        server = self.db.fetchOneRow()[0]
        if server == None:
            return False
        return server

    def NewTaskId(self, **kwargs):
        url = "{0}/task/new".format(self.address)
        response = json.loads(requests.get(url).text)
        if response['success']:
            db = MySQLHander()
            taskid = response['taskid']
            sql = "insert into task(`target`, `taskid`, `server`) VALUES (\"{0}\", \"{1}\", \"{2}\")"\
            .format(kwargs['target'], taskid, self.address)
            if db.insert(sql) == 0L:
                print "Apply New TaskId Success!"
            else:
                print "Apply New Task Fail"
            del db
            return taskid
        else:
            return False

    def Set_Options(self, **kwargs):
        server = self._get_server()
        if server == False:
            return False
        url = "{0}/option/{1}/set".format(server, kwargs['taskid'])
        if "options" in kwargs:
            data = json.dumps(kwargs['options'])
        else:
            data = json.dumps({})
        response = json.loads(requests.post(url, data=data, headers=HEADER).text)
        if response['success']:
            message = "{0} Set Options successfully".format(time.strftime("[*%H:%M:%S]"))
            print(message)
            return True
        else:
            return False

    def update_settings(self, kwargs):
        sql = "update settings set server=\"{0}\", writelist=\"{1}\", blacklist=\"{2}\", proxyaddr=\"{3}\"," \
              "rootdomain=\"{4}\", blackdomain = \"{5}\" where id=1 ".format(kwargs.form['sqlmapaddr'], \
              kwargs.form['writelist'],kwargs.form['blacklist'],\
              kwargs.form['proxyaddr'], getrootdomain(kwargs.form['target']), getrootdomain(kwargs.url))
        mysql.update(sql)

    def start_scan(self, taskid, target):
        server = self._get_server()
        url = "{0}/scan/{1}/start".format(server, taskid)
        data = json.dumps({"url":target})
        response = json.loads(requests.post(url,data=data, headers=HEADER).text)
        if response['success'] == True:
            print "[!] start task {0} sucess".format(taskid)
            t = multiprocessing.Process(target=Thread_Handle,args=(taskid,target,))
            taskid_thread_Dict.append(taskid)
            t.start()
            return True
        else:
            return False

    def StopTask(self, tasklist):
        if isinstance(tasklist, list) == False:
            return False
        return True
        flag = True
        for taskid in tasklist:
            server = self._get_server()
            url = "{0}/scan/{1}/stop".format(server, taskid)
            response = json.loads(requests.get(url,None).text)
            if requests['success'] == True:
                print "[!] stop task {0} ok!".format(taskid)
            else:
                flag = False
                print "[!] stop task {0} failed!".format(taskid)
        return flag      

    def Start_Spider(self, taskid, target):
        t = threading.Thread(target=Spider_Handle,args=(taskid,target,))
        t.start()

    def DeleteAllTask(self):
        sql = "select target,data from task where success=1"
        mysql.query(sql)
        slist = mysql.fetchAllRows()
        for line in slist:
            sql = "insert into successlist(`target` ,`data`) values (\"{0}\")".format(line[0], line[1])
            mysql.insert(sql)
        sql = "delete from task"
        mysql.update(sql)
        print "[!] task schedule has been clear!"

class Action:
    @staticmethod
    def SaveData(target, data):
        sql = ""
        if len(data['data']) == 0:
            sql = "update task set success=0 where target=\"{0}\"".format(target)
        else:
            sql = "update task set data=\"{0}\",success=1 where target=\"{1}\"".format(\
                Tools.dict2base64(data['data'][0]['value'][0]['data']), target)
        mysql.update(sql)
        return

    @staticmethod
    def GetStatusInfo(taskid):
        '''
        :param taskid:
        :return: status,success
        '''
        sql = "select target,status,success from task where taskid=\"{0}\" ".format(taskid)
        mysql.query(sql)
        data = mysql.fetchOneRow()
        result = {"target":data[0], "status":data[1], "success":data[2]}
        return result

    @staticmethod
    def GetTaskidList():
        return taskid_thread_Dict

    @staticmethod
    def GetStatus():
        data = []
        for taskid in taskid_thread_Dict:
            result = Action.GetStatusInfo(taskid)
            data.append(result)
        return data


class Spider(object):
    def __init__(self):
        sql = "select writelist,blacklist,rootdomain,blackdomain from settings where id=1"
        mysql.query(sql)
        resource = mysql.fetchOneRow()
        self.writelist,self.blacklist,self.rootdomain,self.blackdomain = list(resource)

    #如果以http开头就返回整个链接，否则就拼接URL
    def geturl(self, url, href):
        url = urlparse(url)
        return "{0}://{1}/{2}/{3}".format(url.scheme, url.netloc, url.path, href)

    def SpiderGetLink(self, url):
        content = requests.get(url, headers=SPIDER_HEADER).text
        #得到设置信息表
        result = set()
        soup = BeautifulSoup(content, "lxml")
        for a in soup.find_all('a'):
            #将a标签中的值挨个取出来
            href = a['href']
            domain = self.geturl(url, href)
            data = self.Analysis(domain)
            if data != None:
                result.add(data)
        return result

    def Analysis(self, url):
        #判断是否是同源网站
        def fuckotherdomain(href, rootdomain, blackdomain):
            #如果找到不需要匹配的域名就退出
            if href.find(blackdomain) >= 0:
                return None
            if href.find(rootdomain) >= 0:
                return href
            return None
        if url.startswith('http'):
            if fuckotherdomain(url, self.rootdomain, self.blackdomain) != None:
                pass
            else:
                return None
        else:
            return None
        flag = False
        link = urlparse(url)
        #Matching white list first 首先匹配白名单,如果匹配到那么就优先添加
        for types in self.writelist.split(','):
            if link.path.find(types) >= 0:
                return url
        #Matching white list Second 首先匹配黑名单
        for types in self.blacklist.split(','):
            if link.path.find(types) >=0:
                flag = True
        #if match blacklist then continue 匹配到黑名单就推出
        if flag:
            return None
        return url


def Thread_Handle(taskid, target):
    lock.acquire()
    sql = SqlMapAction()
    server = sql._get_server()
    url_status = "{0}/scan/{1}/status".format(server, taskid)
    url_log = "{0}/scan/{1}/log".format(server, taskid)
    url_data="{0}/scan/{1}/data".format(server, taskid)
    response_status = json.loads(requests.get(url_status,None).text)['status']
    while response_status != "terminated" and response_status!="deleting":
        time.sleep(2)
        response_status = json.loads(requests.get(url_status,None).text)['status']
        sql = "update `task` set status = \"{0}\" where taskid=\"{1}\"".format(response_status, taskid)
        mysql.update(sql)
    response_data = json.loads(requests.get(url_data, None).text)
    if response_data==None:
        return False
    Action.SaveData(target, response_data)
    lock.release()
    return True

def Spider_Handle(target, options={}):
    result = set()
    spider = Spider()
    #得到页面的链接
    result = spider.SpiderGetLink(target)
    result.add(target)
    saction = SqlMapAction()
    for url in result:
        taskid = saction.NewTaskId(target=url)
        if taskid:
            saction.Set_Options(taskid=taskid, options=options)
            saction.start_scan(taskid, target)

def ProxyHander(request={}):
    if request['method'] == "GET":
        options = {}
    elif request['method'] == "POST":
        options = {"data":request['body']}
    else:
        return
    saction = SqlMapAction()
    spider = Spider()
    url = spider.Analysis(request['uri'])
    if url == None:
        return
    taskid = saction.NewTaskId(target=url)
    if taskid:
        saction.Set_Options(taskid=taskid, options=options)
        saction.start_scan(taskid, url)

#异步 定时查看数据库里成功的目标保存到successlist表中
def Save_Success_Target():
    while True:
        sql = "select taskid,target,data from task where success=1 and action=0"
        mysql.query(sql)
        resource = mysql.fetchAllRows()
        if resource != None:
            for line in resource:
                sql = "update successlist set target='{0}', data='{1}'".format(line[1], line[2])
                mysql.update(sql)
                sql = "update task set action=1 where taskid='{0}'".format(line[0])
                mysql.update(sql)
                print '[*] save success target {0}'.format(line[1])
        else:
            time.sleep(3)


if __name__ == '__main__':
    Spider_Handle("http://fengxuan.com//webapp/discuz72/", {})
