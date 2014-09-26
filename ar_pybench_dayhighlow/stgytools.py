#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

'''
#from MemPool import *
#import TcpNoBuffer
import time
class runningFlag():
    def __init__(self):
        self.run = 1
    def getRun(self):
        return self.run
    def setNotRun(self):
        self.run = 0

class poolSleep():
    def __init__(self):
        self.dallN = 0
    def sleep(self,dlen, time):
        if(dlen > 400 ):
            #notSleep = 1
            #print( "time:" + str(time) + ",the rawData dlen > 400,not sleep to proc")
            self.dallN = self.dallN + 1
            if(self.dallN%10000 == 0):
                time.sleep(0.001)
                self.dallN = 0
        return 0
          

       
if __name__ == '__main__':
    pass

