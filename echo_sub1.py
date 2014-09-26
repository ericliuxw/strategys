#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    file: echo_client.py
    author: darkbull
    date: 2011-07-22
    desc:
        
'''

import socket
import uuid
import random
import protcl 
protcl = protcl.protcl()
get_string = lambda: uuid.uuid4().hex * random.randint(1, 100)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connt = sock.connect(('127.0.0.1', 1111))
print connt
reg = protcl.writereg('clt1')
print reg
ssize = sock.send(reg)
print ssize
rdata = sock.recv(1024)
print rdata
ssize = sock.send(protcl.writesub('ts'))
rdata = sock.recv(1024)
print rdata
print 'begin test...'
rdata = ''
n = 1200000000000
while n:
    print 'in test...' + str(n)
    rdata += sock.recv(1024)
    print rdata
    #print '\n'
#    #sdata = get_string()
#    
#    ssize = sock.send(protcl.writesub('ts'))
#    rdata = sock.recv(1024)
#    print str(ssize) + ",-"
#    rdata = ''
#    try_count = 10
#    while try_count and len(rdata) < ssize:
#        rdata += sock.recv(1024)
#        try_count -= 1
#        print rdata
#    #assert(rdata == sdata)
    n -= 1
print rdata
sock.close()
