#!/usr/bin/env python
#!-*- coding:utf-8 -*-

import json

from flask import Flask,render_template,request,session

from libs.action import SqlMapAction
from libs.func import Tools
from libs.action import Action

app = Flask(__name__)

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
        taskid = SqlMap.NewTaskId(user="fengxuan", target=request.form['target'])
        if taskid:
            options = Tools.do_sqlmap_options(request.form)
            if SqlMap.Set_Options(taskid=taskid, options=options):
                SqlMap.start_scan(taskid, request.form['target'])
            else:
                #没有取到服务器地址异常处理。
                pass
            return "<html><script>alert('success add new target');window.location.href='/action/showtask';</script></html>"
        return "<html><script>alert('add new target Faild');history.back();</script></html>"

@app.route('/action/showtask', methods=['GET'])
def action_showtask():
    data = Action.GetStatus()
    if request.args.has_key('action') and request.args['action'] == "refresh":
        return json.dumps(data)
    return render_template('showtask.html', data=data)

@app.route('/action/status')
def action_status():
    return render_template('status.html')

if __name__ == '__main__':
    app.run()