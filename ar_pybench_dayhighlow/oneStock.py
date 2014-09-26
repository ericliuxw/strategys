# -*- coding: cp936 -*-
#from break2UpDown import break2UpDown
import ConfigParser
import logging
import PLInfo
import NetPLInfo
import ExeInfo
#import MySQLdb
'''
# "application" code
logging.debug("debug message")
logging.info("info message")
logging.warn("warn message")
logger.error("error message")
liuxianwei20120911

exeInfo.txt:
symbol,nLastShare, fLastPx, nH, nM, nS,iEnterOrdTimes,m_dMaxChangePx,m_dMinChangePx,
m_dOpenPrice, m_dDayHigh, m_dDayLow, m_iAllTicks/Minutes,m_dAllVolume/Minutes,m_iEnterWay,m_dSendSpread,m_chQuoteDate
plInfo.txt:
dPLTotal, GetTotalMktPL(), GetTotalNetPL(),m_dMaxTotalPL, m_dMinTotalPL, m_iTotalExeVolume, m_chQuoteDate
'''

SIDE_BUY = '1'
SIDE_SELL = '2'

SIGNAL_COVER = 'Y'

quoteOk = 0
selected = 0

dateFile = open('curdate.tmp','r')
QuoteDate = dateFile.read()
print QuoteDate
dateFile.close()

plInfo = PLInfo.PLInfo()
plInfo.SetRecordPLinfo(1)
plInfo.SetQuoteDate(QuoteDate)
plInfo.SetBurnedMoney(-5000)

#print "111"

    
class oneStock(object):
    QuoteDate = QuoteDate
    configFl = ConfigParser.RawConfigParser()
    configFl.read('stgyBench.ini')
    useStocks =  {}
    #print "222"
    openTime = configFl.getint("tradestocks", "opentime")
    IFopenTime = configFl.getint("tradestocks", "ifopentime")
    
    stockN = configFl.getint("tradestocks", "count")
    stockNi = 0
    while stockNi < stockN:
        keyName = "stock_" + str(stockNi)
        useStocks[configFl.get("tradestocks", keyName)] = 1
        stockNi = stockNi + 1     
    def __init__(self,symbol,enter,cxl, signalClient, bench):#
        self.symbol = symbol
        self.enter = enter
        self.cxl = cxl
        self.signalClient = signalClient
        self.bench = bench
        self.Clear()
        #config
        self.multip = 1
        
        
        config = ConfigParser.RawConfigParser()
        config.read('stgyBench.ini')
        self.confFirstTkTime = config.getint("oneStock", "confFirstTkTime")
        self.confBuyTime = config.getint("oneStock", "confBuyTime")
        self.confBuyVib = config.getfloat("oneStock", "confBuyVib")
        self.ifcode = config.get("oneStock", "ifCode")
        self.cuCode = config.get("oneStock", "cuCode")
        self.confOutUpDown = config.getfloat("oneStock", "confOutUpDown")
        try:
            self.multip = config.getint("oneStock", symbol[0])
        except:
            try:
                self.multip = config.getint("oneStock", symbol[1:3])
            except:
                self.multip = 1
        
        #print "oneStock init Ok"
    def Clear(self):
        self.Levshare = 0
        self.trading = 1
        self.position = 0;
        self.openshare = 0;
        self.entershare = 0;#between enter and order accept
        self.enterSigPx = 0.0
        self.enterBigNum = 0
        self.stopPx = 0.0
        self.dealMaxPx = 0.0
        self.dealMinPx = 0.0
        self.enterPx = 0.0
        self.outTimes = 0
        
        self.tickN = 0
        self.dayHighPx = 0.0
        self.dayLowPx = 99999.0
        self.secSat = 0
        
        self.forceStop = 0
        self.enterTime = 0
        self.lastPx = 0.0
        self.lastTime = 0
        self.lastTotalShare = 0
        self.lastOrdId = ""
        oneStock.confOpenTime = 33000#33000
        oneStock.confCoverTime = 53100#54000
        oneStock.bitPx = 0.0
        self.afterTime = 0
        self.signalDirect = 0
        self.oneNetPL = NetPLInfo.NetPLInfo()
        self.oneNetPL.setSymbol(self.symbol)
        self.oneNetPL.SetQuoteDate(QuoteDate)
        self.exeInfo = ExeInfo.ExeInfo()
        self.exeInfo.SetRecordExeInfo(1)
        self.exeInfo.SetQuoteDate(QuoteDate)
        
#    def getQuoteDate():
#        return QuoteDate
    def onEnterSignal(self, signal,price,stop_price,share):
        self.signalDirect = signal
        self.enterSigPx = price
        self.enterBigNum = 0
        self.stopPx = stop_price
        #self.procEnterOrd(32400, price, share)
        
    def onQuote(self, time, price, share):
        if(self.symbol == "BEGIN"):
            plInfo.Clear()
            plInfo.SetQuoteDate(self.QuoteDate)
#            for (d,oneStk) in self.bench.stockDict.items():
#                oneStk.Clear()
            
        totalShare = share
        share = share - self.lastTotalShare
        if(share < 1):
            return
        self.lastTotalShare = totalShare
        
        global quoteOk,selected
        if(not quoteOk):
            print "quote receve: ",self.symbol,time,price, share
            quoteOk = 1
        

        self.exeInfo.QuoteUpdateExeInfo(time, price, share)
        plInfo.QuoteUpdateMktPL(time, self.symbol,self.multip, self.position, self.enterPx, price)
        #if(self.symbol == self.confTickStock):
        #    logging.info(self.symbol + ":onQuote:" + str(time) + "," + str(price) + "," + str(share))
        self.lastTime = time
        self.lastPx = price
        self.procOutPos(price)
        self.procEnterOrd(time, price, share)

                   
    ##############         proc      #########################
    def procEnterOrd(self,time, price, share):
        price = float(price)
        share = int(share)
        if(time > oneStock.confCoverTime or plInfo.GetBurnedMoneyFlag()):
            self.forceStop = 1
            return
        
        if(self.openshare != 0 or self.position != 0 or self.entershare != 0):
            return
        
        if self.symbol[0] == 'I' and self.symbol[1] == 'F':
            if time > oneStock.IFopenTime:
                self.tickN = self.tickN + 1
                
        else:
            if time > oneStock.openTime:
                self.tickN = self.tickN + 1
                
        if self.tickN > 0 and self.tickN <= 100:
            if price > self.dayHighPx :
                self.dayHighPx = price
            if price < self.dayLowPx:
                self.dayLowPx = price
        if self.secSat == 0 and self.tickN > 100:
            #print "tick > 100"
            if price >= self.dayHighPx :
                self.dayHighPx = price
                self.secSat = 1
            if price <= self.dayLowPx:
                self.dayLowPx = price
                self.secSat = 1 
        if self.secSat > 0:
            print "in secSat"
            if price >= self.dayHighPx:
                self.enterOrder(self.symbol, SIDE_BUY, price + price * self.confBuyVib *0.5, 1)
            if price <= self.dayLowPx:
                self.enterOrder(self.symbol, SIDE_SELL, price - price* self.confBuyVib *0.5, 1)        
            
               
    def procOutPos(self,price): 
        if(self.position == 0):
            if(self.openshare == 0):
                pass
            elif(self.openshare > 0):
                pass
            elif(self.openshare < 0):
                pass
            
        elif(self.position > 0):#long pos               
            if(self.checkOut(0, price) == 1):
                self.outTimes = self.outTimes + 1
                if(self.outTimes > 2):
                    self.forceStop = 1
            if(self.forceStop):
                if(self.lastTime > self.enterTime + 20 and self.openshare != 0):
                    logging.debug("date:" + QuoteDate + "," + self.symbol + ",procOutPos;long;" + "self.lastTime:" + str(self.lastTime)
                                  + "self.enterTime:" + str(self.enterTime)
                                  + "self.openshare:" + str(self.openshare)
                                  + "self.lastOrdId:" + self.lastOrdId )
                    self.cxlOrder(self.symbol, self.lastOrdId)
                if(self.openshare == 0 and self.entershare == 0):
                    self.enterOrder(self.symbol, SIDE_SELL, price - oneStock.bitPx, 1)
            
        elif(self.position < 0):#short pos
            if(self.checkOut(0, price) == 1):
                self.outTimes = self.outTimes + 1
                if(self.outTimes > 2):
                    self.forceStop = 1
            if(self.forceStop):
                if(self.lastTime > self.enterTime + 20 and self.openshare != 0):
                    self.cxlOrder(self.symbol,self.lastOrdId)
                if(self.openshare == 0 and self.entershare == 0):
                    self.enterOrder(self.symbol, SIDE_BUY, price + oneStock.bitPx, 1)

                    
    def checkOut(self, secNow,  price):
        if(self.dealMaxPx < price):
            self.dealMaxPx = price
        if(self.dealMinPx > price):
            self.dealMinPx = price
            
        if(self.position > 0):
            #
            lossPer = self.dealMaxPx - price
            #不同出仓方法的参数最后都可以转化成止损价
            if(lossPer > 150 or lossPer > self.dealMaxPx * self.confOutUpDown):#盈利多少百分点后回调多少百分点出仓
                return 1
        elif(self.position < 0):
            lossPer = price - self.dealMinPx
            #不同出仓方法的参数最后都可以转化成止损价
            if(lossPer > 150 or self.dealMinPx * self.confOutUpDown):
                return 1

        if secNow > 53700:
            return 1  
    ######################enter event #########################
    def signalClient(self, symbol, signal):
        self.signalClient(symbol, signal)
        
    def enterOrder(self, symbol,side, price, share):
        self.entershare = share
        #print "enterOrder"
        self.enter(symbol, side,  price, share)
    def cxlOrder(self, symbol, orderId):
        #print "cxl"
        self.cxl(symbol, orderId)

    #######################on event ###########################    
    def onOrderAccept(self, clOrderId, orderId,side,lastShare):
        if(self.trading == 0):
            return
        logging.error("date:" + QuoteDate + "," + self.symbol + ",onOrderAccept;" + ",time:" + str(self.lastTime) + ",openshare:" + str(self.openshare) + ",position:" + str(self.position)
                      + ",clOrderId:" + clOrderId + "orderId:" + orderId +  ",side:" + str(side) + ",lastShare:" + str(lastShare))
        
        if(side == SIDE_BUY):
            self.openshare = self.openshare + lastShare
        elif(side == SIDE_SELL):
            self.openshare = self.openshare - lastShare
            
        self.lastOrdId = orderId
        
        self.entershare = 0

    def onOrderReject(self, clOrderId,orderId,side,lastShare):
        if(self.trading == 0):
            return
        logging.error("date:" + QuoteDate + "," + self.symbol  + ",onOrderReject;" + ",time:" + str(self.lastTime) + ",openshare:" + str(self.openshare) + ",position:" + str(self.position)
                      +  ",clOrderId:" + clOrderId + "orderId:" + orderId +  ",side:" + str(side) + ",lastShare:" + str(lastShare))
        
        if(side == SIDE_BUY):
            if(self.openshare != 0):
                self.openshare = self.openshare - lastShare
        elif(side == SIDE_SELL):
            if(self.openshare != 0):
                self.openshare = self.openshare + lastShare
            
        self.lastOrdId = ""
        
        self.entershare = 0

    def onCxlAccept(self, orderId,side):
        if(self.trading == 0):
            return
        logging.error("date:" + QuoteDate + "," + self.symbol  + ",onCxlAccept;" + ",time:" + str(self.lastTime) + ",openshare:" + str(self.openshare) + ",position:" + str(self.position)
                      + ",orderId:" + orderId +  ",side:" + int(side))

    def onCxlReject(self, orderId,side):
        if(self.trading == 0):
            return
        if(self.openshare != 0):
            logging.error("date:" + QuoteDate + "," + self.symbol  + ",onCxlReject;" + ",time:" + str(self.lastTime) + ",openshare:" + str(self.openshare) + ",position:" + str(self.position)
                          + ",orderId:" + orderId +  ",side:" + str(side) + ",openshare:" + str(self.openshare))
            self.openshare = 0
        
    def onCxlExe(self, orderId,side,lastShare): #lxw server need todo
        if(self.trading == 0):
            return
        logging.error("date:" + QuoteDate + "," + self.symbol  + ",onCxlExe;" + ",openshare:" + str(self.openshare) + ",position:" + str(self.position)
                      + ",orderId:" + orderId +  ",side:" + str(side) + ",lastShare:" + str(lastShare))
        if(side == SIDE_BUY):
            self.openshare = self.openshare - lastShare
        elif(side == SIDE_SELL):
            self.openshare = self.openshare + lastShare

    def onOrderExe(self, orderId,side, exeId, price, lastShare):
        if(self.trading == 0):
            return        
        logging.error("date:" + QuoteDate + "," + self.symbol  + ",onOrderExe;" + ",time:" + str(self.lastTime) + ",openshare:" + str(self.openshare) + ",position:" + str(self.position)
                      + ",lastOrdId:" + self.lastOrdId + ",orderId:" + orderId + ",exeId:" + exeId
                      +  ",side:" + str(side) + ",lastShare:" + str(lastShare)
                      + ",EnterNum:" + str(self.oneNetPL.GetEnterNum()) + ",OneNetPL:" + str(self.oneNetPL.GetOneNetPL()))

        self.oneNetPL.CalcOneStockPL(self.position,self.lastTime,self.multip, side, lastShare, price)
        self.exeInfo.ExeUpdateExeInfo(self.symbol, self.lastTime, self.oneNetPL.GetEnterNum(), side, lastShare, price)
        
        if(side == SIDE_BUY):
            if(len(self.lastOrdId) > 1):
                self.openshare = self.openshare - lastShare
            self.position = self.position + lastShare
        elif(side == SIDE_SELL):
            if(len(self.lastOrdId) > 1):
                self.openshare = self.openshare + lastShare
            self.position = self.position - lastShare

        plInfo.UpdateNetPL(self.symbol, self.oneNetPL.GetOneNetPL(), lastShare)
##        if(self.position == 0):
##            self.signalClient(self.symbol, SIGNAL_COVER)
        #reset
        self.outTimes = 0
        self.enterPx = price
        self.dealMaxPx = price
        self.dealMinPx = price
        self.lastOrdId = ""
        self.entershare = 0
        self.forceStop = 0

def main():
    pass
    #test = oneStock("111",0,0, 0, 0)
if __name__ == '__main__':
    pass
#    import oneStock
#    oneStock.main()
    
