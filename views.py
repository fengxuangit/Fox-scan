#!/usr/bin/env python
#!-*- coding:utf-8 -*-

import json
import threading
import multiprocessing

from flask import Flask,render_template,request,session,jsonify,redirect

from libs.action import SqlMapAction,Spider_Handle,Save_Success_Target
from libs.func import Tools
from libs.models import MySQLHander
from libs.action import Action
from libs.proxy import run_proxy

app = Flask(__name__)

mysql = MySQLHander()

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="546sdafwerxcvSERds549fwe8rdxfsaf98we1r2"
))

app.config.from_envvar('AUTOSQLI_SETTINGS', silent=True)

app.secret_key = "34$#4564dsfaWEERds/*-()^=sadfWE89SA"

SqlMap = SqlMapAction()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index')
def settings_views():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings_settings_info():
    return render_template('info.html')

#TODO user=session['user']
@app.route('/action/startask', methods=['GET', 'POST'])
def action_startask():
    if request.method == 'GET':
        return render_template('startask.html')
    else:
        #删除之前的任务
        SqlMap.DeleteAllTask()
        #转换为sqlmap的设置
        options = Tools.do_sqlmap_options(request.form)
        #更新整体的设置
        SqlMap.update_settings(request)
        #线程启动任务，后台运行,没有join
        t = threading.Thread(target=Spider_Handle,args=(request.form['target'],options,))
        t.start()
        # t = threading.Thread(target=Save_Success_Target,args=())
        # t.start()
        return redirect('/action/showtask')
        return "<html><script>alert('success add new target');window.location.href='/action/showtask';</script></html>"
    return "<html><script>alert('add new target Faild');history.back();</script></html>"

@app.route('/action/showtask', methods=['GET'])
def action_showtask():
    data = {"number":0, "data":[]}
    if request.args.has_key('action') and request.args['action'] == "refresh":
        condition = ""
        sql = "select taskid,target,success,status from task where action=0"
        mysql.query(sql)
        #获取正在扫描的URL
        num = 0
        for line in mysql.fetchAllRows():
            num += 1
            data['data'].append({"taskid":line[0], "target":line[1], "success":line[2], "status":line[3]})
            condition = "taskid = \"{0}\" and ".format(line[0])
        #更新状态,下次就不取ACTION为1的了。
        # if condition != "":
        #     sql = "update task set action=1 where {0}".format(condition[:-4])
        #     mysql.update(sql)
        data['number'] = num
        return json.dumps(data)
    return render_template('showtask.html')

@app.route('/action/showjson', methods=['GET'])
def action_showjson():
    data = {"number":0, "data":[]}
    condition = ""
    sql = "select taskid,target,success,status from task where action=0"
    mysql.query(sql)
    #获取正在扫描的URL
    num = 0
    for line in mysql.fetchAllRows():
        num += 1
        data['data'].append({"taskid":line[0], "target":line[1], "success":line[2], "status":line[3]})
        condition = "taskid = \"{0}\" and ".format(line[0])
    data['number'] = num
    return json.dumps(data)

@app.route('/action/stoptask')
def action_status():
    if request.args['taskidlist'] != "":
        taskidlist = []
        if request.args['taskidlist'].find(",") > 0:
            taskidlist = request.args['taskidlist'].split(',')
        else:
            taskidlist.append(request.args['taskidlist'])
    return json.dumps({"status":SqlMap.StopTask(taskidlist)})


if __name__ == '__main__':
    app.run()