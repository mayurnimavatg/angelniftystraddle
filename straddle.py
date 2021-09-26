# -*- coding: utf-8 -*-
"""
Created on Wed Sep 22 21:06:54 2021

@author: neera
"""

import pandas as pd
import json 
import time
import datetime
import requests
from smartapi import SmartConnect, SmartWebSocket
from support import angel
import sys


url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
d = requests.get(url).json()
token_df = pd.DataFrame.from_dict(d)


acc = pd.read_csv(r"acc.csv").iloc[-1]
obj = angel.login(acc['api'],acc['userid'],acc['password'])
if obj != None:
    print("--> Login Successful")
    acc = {'userid':acc['userid'], "obj":obj, "trades":{}, "data" : {}, "op" : False}
else: 
    time.sleep(2)
    print("--> Login was not suggessful")
    obj=SmartConnect(api_key=acc['api']) 
    data = obj.generateSession(acc['userid'],acc['password'])
    print(f"--> Issue with Login : {data['message']}")
    time.sleep(5)
    print("--> Closing the program")
    time.sleep(10)
    sys.exit()
    
    
trades = {}
placed = False 


def order_placing(): 
    global placed, trades, obj,token_df
    
    dat = datetime.datetime.now()
    
    if dat.time() >= datetime.time(9,20) and placed == False : 
        placed = True 
        nif_pri = angel.get_ltp(obj,"NSE", "NIFTY","26000")
        
        print(f"--> NIFTY trading at {nif_pri}")
        
        cst = round(nif_pri/50)*50
        
        ce_stk = angel.find_sym(obj,cst + 100 ,"CE",token_df)
        pe_stk =  angel.find_sym(obj,cst - 100 ,"PE",token_df)
        
        print(f"--> CE Strike Price : {ce_stk[0]}")
        print(f"--> PE Strike Price : {pe_stk[0]}")
        
        ce_orderid = angel.place_ord(obj, ce_stk[0],ce_stk[1],"SELL",'MARKET', "0", "0","50",variety = "NORMAL", prod = "CARRYFORWARD",exc = "NFO")
        pe_orderid = angel.place_ord(obj, pe_stk[0],pe_stk[1],"SELL",'MARKET', "0", "0","50",variety = "NORMAL", prod = "CARRYFORWARD",exc = "NFO")
        
        time.sleep(2)
        
        tb = angel.trade_book(obj)
         
        ce_fill_pri = angel.get_fill_price(tb, ce_orderid) 
        pe_fill_pri = angel.get_fill_price(tb, pe_orderid) 
        
        print(f"--> CE filled at {ce_fill_pri}")
        print(f"--> PE filled at {pe_fill_pri}")
        
        slpri_ce = round(ce_fill_pri + (ce_fill_pri *50/100) , 1)
        slpri_ce_s = round(slpri_ce + (slpri_ce*20/100), 1)
        
        slpri_pe = round(pe_fill_pri + (pe_fill_pri *50/100) , 1)
        slpri_pe_s = round(slpri_pe + (slpri_pe*20/100), 1)
        
        ce_orderid = angel.place_ord(obj, ce_stk[0],ce_stk[1],"BUY",'STOPLOSS_LIMIT', slpri_ce_s , slpri_ce,"50",variety = "STOPLOSS", prod = "CARRYFORWARD",exc = "NFO")
        pe_orderid = angel.place_ord(obj, pe_stk[0],pe_stk[1],"BUY",'STOPLOSS_LIMIT', slpri_pe_s , slpri_pe,"50",variety = "STOPLOSS", prod = "CARRYFORWARD",exc = "NFO")
        
        print("--> Placing SL-L orders.")
         
        trades = {1 : {"symbol" : ce_stk[0], "token": ce_stk[1], "selltime" : dat.strftime("%H:%M:%S"), "sellprice" : ce_fill_pri, "slid" :ce_orderid, "date" : dat.date(), "quantity": 50, "pos": "open"}, 
                  2 : {"symbol" : pe_stk[0], "token": pe_stk[1], "selltime" : dat.strftime("%H:%M:%S"), "sellprice" : pe_fill_pri, "slid": pe_orderid, "date" : dat.date() , "quantity" :  50, "pos": "open"}}
        
    
        
    if placed == True and dat.time() >= datetime.time(15,25):
       
        tb = angel.trade_book(obj)
        tbdf =  pd.DataFrame.from_dict(tb['data'])
        tb_lst = tbdf['orderid'].to_list()
        
        for i in trades : 
            if trades[i]['slid'] in tb_lst :
                trades[i]['buyprice'] = angel.get_fill_price(tb, trades[i]['slid']) 
                trades[i]['buytime'] = angel.get_fill_time(tb, trades[i]['slid']) 
                print(f"--> SL was triggered in {trades[i]['symbol']}")
            
            else : 
                xm = trades[i]
                
                angel.cancel_orders(trades[i]['slid'], obj)
                
                ord_id = angel.place_ord(obj, xm['symbol'], xm['token'],"BUY",'MARKET', "0", "0","50",variety = "NORMAL", prod = "CARRYFORWARD",exc = "NFO")
                
                time.sleep(2)
                
                tb = angel.trade_book(obj)
                
                print(f"Squared off open position in {trades[i]['symbol']}")
                trades[i]['buyprice'] = angel.get_fill_price(tb, ord_id) 
                trades[i]['buytime'] = angel.get_fill_time(tb, ord_id) 
                
        try : 
            dx = pd.read_csv(r"trades.csv")
        except : 
            dx = pd.DataFrame()
        
        res = pd.DataFrame.from_dict(trades).transpose()
        del res['slid']
        res['pnl'] = (res['sellprice'] - res['buyprice']) * res['quantity']
        
        dx = dx.append(res)
        
        dx.to_csv(r"trades.csv", index = False)
        
        print("--> All trades done. Closing the Program")
        time.sleep(10)
        sys.exit()
        

while True: 
    try: 
        order_placing()
    except Exception as e : 
        print(e)
    time.sleep(5)
                
                
                
