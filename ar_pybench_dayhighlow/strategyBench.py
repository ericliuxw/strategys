#-*- encoding: gb2312 -*-
import datetime
#import socket
import threading
import logging
from oneStock import *
from stgytools import *
import MsgPacket
from TcpClient import TcpClient
gtcpCli = TcpClient()
    
cliName = 'stgy1'
pname = 'ben1'
mktName = 'fut1'

runFlag = runningFlag()              
class strategyBench(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.onlyOneMsg = 0
        self.stockDict = {}
        self.clOrdeId = 0
        self.timeDeq = []
        self.timesec = 0
        self.timeasc = ''
        self.canRecvQuote = 1
        now = datetime.datetime.now()
        self.nowDay = now.strftime('%Y-%m-%d')
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S',
                    filename='stgyBenchLog' + self.nowDay + '.log',
                    filemode='a+')
        if(len(oneStock.QuoteDate) > 4):
            self.nowDay = oneStock.QuoteDate
        #print("dbDate:"+self.nowDay)
        #self.db = dbk.dbk(self.nowDay,1)

        self.prot = MsgPacket.MsgPacket()
        
    def run(self):
        print "now strategy bench processing..."
        gtcpCli.sendmsg(self.prot.writereg(pname))
        print "begin sub ts"
        gtcpCli.sendmsg(self.prot.writesub('ts'))
        #psleep = poolSleep()
        testOn = 0
        packNum = 0
        while True:
            if(not runFlag.getRun()):
                print "quit from stgyTmp\n"
                break
            dataOne = gtcpCli.get()
            if dataOne is None:
                continue
            #logging.debug(dataOne)
            #psleep.sleep(0, self.timeasc)
            if testOn == 0 :
                testOn = 1
                print dataOne 
            packNum = packNum + 1
            if packNum%10000 == 0:
                    time.sleep(0.001)
            self.prot.parse(dataOne)
            print dataOne
            self.procOneTick(dataOne,self.prot)
            gtcpCli.pop()
        
    def procOneTick(self,rawDataOne,dataOne):
        
        #print rawDataOne
        symbol = dataOne.get_str("symbol")
        if(symbol == "END"):
            print "symbol == END"
        elif(symbol == "BEGIN"):
            self.canRecvQuote = 1
##            k = candle()
##            k.symbol = symbol
##            self.sendToStgyClientK(k)   
        if(0 == self.canRecvQuote):
            return
        
        if not oneStock.useStocks.has_key(symbol):
            return
        
        cmd = dataOne.get_long("cmd")
        msgType = dataOne.get_long("msg_type")
        if(self.stockDict.has_key(symbol)):
            oneStk = self.stockDict.get(symbol)
        else:
            oneStk = oneStock(symbol, self.enterOrder, self.cxlOrder, self.signalClient, self)
            self.stockDict[symbol] = oneStk

        if(cmd == dataOne.REQ_CHINAFUT_SIGNAL):
            signal = dataOne.get_str("signal")
            price = dataOne.get_double("price")
            stop_price = dataOne.get_double("stop_price")
            share = dataOne.get_long("share")
            oneStk.onEnterSignal(signal,price,stop_price,share)
            logging.critical(rawDataOne)
            return#####处理客户端请求后直接返回，后续全部是处理市场返回消息的
        elif(cmd == dataOne.RESP_CHINAFUT_QUOTE):
            upTime = dataOne.get_str("update_time")
            self.timeasc = upTime
            try:
                self.timeDeq = upTime.split(':')
            except:
                logging.warn(rawDataOne)
                return
            price = dataOne.get_double("last_px")
            share = dataOne.get_long("last_share")
            try:     
                self.timeSec = int(self.timeDeq[0])*3600 + int(self.timeDeq[1])*60 + int(self.timeDeq[2])
            except:
                logging.warn(rawDataOne)
                return
            oneStk.onQuote(self.timeSec, price, share)
            return#####处理处理市场返回的行情后直接返回，后续全部是处理市场返回交易消息的
            
        elif(cmd == dataOne.CMD_CONN):
            print rawDataOne
            logging.warn(rawDataOne)
            return
        if msgType == 0:
            print rawDataOne
            logging.error(rawDataOne)
            return
        ###trade proccess
        dataOne.set_value('time',self.timeasc)
        logging.critical(rawDataOne)
        self.procFutMktTrade(msgType,symbol,oneStk,dataOne)
            
    def procFutMktTrade(self,msgType,symbol,oneStk,node):        
        clOrderId = node.get_str("client_order_id")
        orderId = node.get_str("order_id")
        side = node.get_str("side")
        exeId = node.get_str("exe_id") 
        lastShare = node.get_long("last_share")
        lastPx = node.get_double("last_px")
        print msgType,symbol
        
        {
            self.prot.RESP_ORDER_ACCEPT:lambda:oneStk.onOrderAccept(clOrderId,orderId,side,lastShare),
            self.prot.RESP_ORDER_REJECT:lambda:oneStk.onOrderReject(clOrderId,orderId,side,lastShare),
            self.prot.RESP_CXL_ACCEPT:lambda:oneStk.onCxlAccept(orderId,side),
            self.prot.RESP_CXL_REJECT:lambda:oneStk.onCxlReject(orderId,side),
            self.prot.RESP_ORDER_CXLED:lambda:oneStk.onCxlExe(orderId,side,lastShare),
            self.prot.RESP_ORDER_EXE:lambda:oneStk.onOrderExe(orderId,side,exeId, lastPx,lastShare),
            
        }[msgType]()
            
    def signalClient(self, symbol, signal):
        #self.clOrdeId = self.clOrdeId + 1
        self.prot.clear()
        self.prot.set_long("cmd", self.prot.REQ_CHINAFUTU_TRADE)
        self.prot.set_long("msg_type", self.prot.REQ_ORDER_CXL)
        self.prot.set_long("signal", signal)
        self.prot.set_long("future_id", symbol)
        msg = self.prot.writeans(cliName,'')
        logging.critical(msg)
        gtcpCli.sendmsg(msg)
        
    def cxlOrder(self, symbol, orderId):
        self.clOrdeId = self.clOrdeId + 1
        self.prot.clear()
        self.prot.set_long("cmd", self.prot.REQ_CHINAFUT_TRADE)
        self.prot.set_long("msg_type", self.prot.REQ_ORDER_CXL)
        self.prot.set_long("client_order_id", self.clOrdeId)
        self.prot.set_long("order_id", orderId)
        self.prot.set_long("future_id", symbol)
        msg = self.prot.writereq(pname,mktName)
        logging.critical(msg)
        gtcpCli.sendmsg(msg)
        
    def enterOrder(self, symbol, side, price, share):
        self.clOrdeId = self.clOrdeId + 1
        self.prot.clear()
        self.prot.set_long("cmd", self.prot.REQ_CHINAFUT_TRADE)
        self.prot.set_long("msg_type", self.prot.REQ_ORDER_ENTER)
        self.prot.set_value("symbol", symbol)
        self.prot.set_long("client_order_id", self.clOrdeId)
        self.prot.set_char("side", side)
        self.prot.set_double("price", price)
        self.prot.set_long("share", share)
        self.prot.set_value("future_id", symbol)
        msg = self.prot.writereq(pname,mktName)
        logging.critical(msg)
        gtcpCli.sendmsg(msg)
        
        return self.clOrdeId

    def oneCandle(self,candle):
        #pass
        self.sendToStgyClientK(candle)

    def sendToStgyClientK(self, candle):
        self.prot.clear()
        self.prot.set_long("cmd", self.prot.RESP_CHINAFUT_QUOTE)
        self.prot.set_long("msg_type", self.prot.MSG_CONN)##error 
        self.prot.set_value("symbol", candle.symbol)
        self.prot.set_double("open", candle.open)
        self.prot.set_double("close", candle.close)
        self.prot.set_double("high", candle.high)
        self.prot.set_double("low", candle.low)
        self.prot.set_long("share", candle.share)
        self.prot.set_long("count", candle.count)
        self.prot.set_long("time", candle.time)
        self.prot.set_long("lowTime", candle.lowTime)
        self.prot.set_long("highTime", candle.highTime) 
        self.prot.set_double("macd", candle.macd)
        self.prot.set_double("avg1", candle.avg1)
        self.prot.set_double("avg2", candle.avg2)
        msg = self.prot.writepub('kline')
        logging.critical(msg)
        gtcpCli.sendmsg(msg)

if __name__ == '__main__':
    #tcpServ.connect(ADDR)
    print "now enter main:"
    sockret = gtcpCli.init(9992, 1111)
    if sockret < 0:
        print "tcpCli.init error"
    else:
        print "now we start ..."
        tmpThread = strategyBench()
        tmpThread.start()
        #time.sleep(2)
        #gtcpCli.start()
        tmpThread.join()
