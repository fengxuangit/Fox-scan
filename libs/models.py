#!/usr/bin/env python
#!-*- coding:utf-8 -*-

import os
import MySQLdb

from func import XMLDOM

class MySQLHander(object):
    def __init__(self):
        xml = XMLDOM()
        host     = xml.GetElementByName('mysql/host').strip()
        username = xml.GetElementByName('mysql/username').strip()
        password = xml.GetElementByName('mysql/password').strip()
        port     = xml.GetElementByName('mysql/port').strip()
        database = xml.GetElementByName('mysql/database').strip()
        charset  = xml.GetElementByName('mysql/charset').strip()
        try:
            self._conn = MySQLdb.connect(host=host,
                         port=int(port),
                         user=username,
                         passwd=password,
                         db=database,
                         charset=charset)
        except MySQLdb.Error, e:
            self.error_code = e.args[0]
            error_msg = 'MySQL error! ', e.args[0], e.args[1]
            print error_msg
              
            if self._timecount < self._TIMEOUT:
                interval = 5
                self._timecount += interval
                time.sleep(interval)
                return self.__init__(dbconfig)
            else:
                raise Exception(error_msg)
            
        self._cur = self._conn.cursor()
        self._instance = MySQLdb


    def query(self,sql):
        try:
            self._cur.execute("SET NAMES utf8")
            result = self._cur.execute(sql)
        except MySQLdb.Error, e:
            self.error_code = e.args[0]
            print "DATABASE ERROR: ",e.args[0],e.args[1]
            result = False
        return result

    def update(self,sql):
        try:
            self._cur.execute("SET NAMES utf8")
            result = self._cur.execute(sql)
            self._conn.commit()
        except MySQLdb.Error, e:
            self.error_code = e.args[0]
            print "DATABASE ERROR: ",e.args[0],e.args[1]
            result = False
        return result
    
    def insert(self,sql):
        try:
            self._cur.execute("SET NAMES utf8")
            self._cur.execute(sql)
            self._conn.commit()
            return self._conn.insert_id()
        except MySQLdb.Error, e:
            self.error_code = e.args[0]
            print "DATABASE ERROR: ",e.args[0],e.args[1]
            return False

    def fetchAllRows(self):
        return self._cur.fetchall()

    def fetchOneRow(self):
        return self._cur.fetchone()

    def getRowCount(self):
        return self._cur.rowcount
              
    def commit(self):
        self._conn.commit()
            
    def rollback(self):
        self._conn.rollback()
       
    def __del__(self):
        try:
            self._cur.close()
            self._conn.close()
        except:
            pass
    
    def close(self):
        self.__del__()

class SqlMapTask(object):
    pass
