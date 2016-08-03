#!/usr/bin/env python
#!-*- coding:utf-8 -*-
import os
import xml.etree.cElementTree as ET 

class XMLDOM(object):    
    def __init__(self):
        xml = ET.parse("{0}/config.xml".format(os.path.split(os.path.realpath(__file__))[0]))
        self.tree = xml.getroot()

    def GetElementByName(self, name):
        return self.tree.find(name)
        

if __name__ == '__main__':
    xml = XMLDOM()
    name = "mysql/username"