#!/usr/bin/env python
#!-*- coding:utf-8 -*-

from flask import Flask,render_template,request,session

app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="546sdafwerxcvSERds549fwe8rdxfsaf98we1r2"
))

app.config.from_envvar('AUTOSQLI_SETTINGS', silent=True)

app.secret_key = "34$#4564dsfaWEERds/*-()^=sadfWE89SA"

@app.route('/index')
def settings_views():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings_settings_info():
    return render_template('info.html')
    # if request.method == 'GET':

@app.route('/action/startask', methods=['GET', 'POST'])
def action_startask():
    return render_template('startask.html')

@app.route('/action/status')
def action_status():
    return render_template('status.html')

if __name__ == '__main__':
    app.run()