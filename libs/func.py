#!/usr/bin/env python
#!-*- coding:utf-8 -*-
import os
import logging
import json
import base64
import xml.etree.cElementTree as ET



def getrootpath():
    path = os.path.split(os.path.realpath(__file__))[0]
    return path[:path.rfind("/")]


class XMLDOM(object):    
    def __init__(self):
        xml = ET.parse("{0}/config.xml".format(getrootpath()))
        self.tree = xml.getroot()

    def GetElementByName(self, name):
        return self.tree.find(name).text

class Tools:

    @staticmethod
    def do_sqlmap_options(request):
        options = {}
        for key in request.keys():
            if request[key] == "True":
                options[key] = request[key]
        return options

    @staticmethod
    def dict2base64(dictobj):
        return base64.b64encode(json.dumps(dictobj))

    @staticmethod
    def base642json(string):
        return json.loads(base64.b64decode(string))

if __name__ == '__main__':
    xml = XMLDOM()
    print xml.GetElementByName('sqlmap').strip()