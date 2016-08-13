#!/usr/bin/env python
#!-*- coding:utf-8 -*-
import json
import time
import sys
import requests
import ipdb

from func import XMLDOM
from models import MySQLHander
from func import Logger

HEADER={'Content-Type': 'application/json'}

class SqlMapAction(object):
    def __init__(self):
        xml = XMLDOM()
        self.db = MySQLHander()
        self.address = xml.GetElementByName('sqlmap').strip()

    def _get_server(self, taskid):
        sql = "select server from task where taskid = \"{0}\"".format(taskid)
        self.db.query(sql)
        server = self.db.fetchOneRow()[0]
        return server

    def NewTaskId(self, **kwargs):
        url = "{0}/task/new".format(self.address)
        response = json.loads(requests.get(url).text)
        if response['success']:
            db = MySQLHander()
            taskid = response['taskid']
            sql = "insert into task(`user`, `target`, `taskid`, `server`) VALUES (\"{0}\", \"{1}\", \"{2}\", \"{3}\")"\
            .format(kwargs['user'], kwargs['target'], taskid, self.address)
            if db.insert(sql) == 0L:
                print "Apply New TaskId Success!"
            else:
                print "Apply New Task Fail"
            del db
            return taskid
        else:
            return False

    def Set_Options(self, **kwargs):
        server = self._get_server(kwargs['taskid'])
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

    def start_scan(self, taskid):
        server = self._get_server(taskid)
        url = "{0}/scan/{1}/start".format(server, taskid)
        response = json.loads(requests.post(url,None,{'Content-Type': 'application/json'}).text)
        if response['success'] == True:
            print "[!] start task {0} sucess".format(taskid)

if __name__ == '__main__':
    sqlmap = SqlMapAction()
    print sqlmap.NewTaskId(user="fengxuan", target="http://www.baidu.com")
