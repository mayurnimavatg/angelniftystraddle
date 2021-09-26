# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 12:49:12 2021

@author: neera
"""


from smartapi import SmartConnect
import numpy as np 
import pandas as pd 

def login(api,userid,password):
    ab = None
    n = 0 
    while ab == None: 
        try:
            obj=SmartConnect(api_key=api) 
            data = obj.generateSession(userid,password)
            if data['status'] == False :
                raise Exception(f"Unable to Login into {userid}")
            ab = "done"
            return obj
        except: 
            n = n+1
            if n ==10:
                print(f"Unable to login into {userid}")
                ab = "done"
                return None 

def get_ltp(obj, exc,symbol,token):
    n = 0 
    ab = None
    while ab == None: 
        try: 
            data = obj.ltpData( exc,symbol,token)
            ltp = data['data']['ltp']
            if data['status'] == False: 
                raise Exception
            ab = "done"
            return ltp
        except:
            n = n+1
            if n >= 5: 
                ab = "done"
                # print(f"Unable to fetch ltp of {symbol}")
                return None


def find_sym(obj, stk,typ,token_df ):
    m = token_df.loc[token_df['name'] == str("NIFTY")] 
    m = m.replace('', np.nan)
    m = m.dropna()
    m['expiry'] = pd.to_datetime(m['expiry'])
    m = m.sort_values(by='expiry', ascending=True)
    g = m.groupby('expiry')  
    lst = list(g.groups.keys())
    ab = None
    n = 0 
    while ab == None:
        try: 
            nam = "NIFTY" + lst[n].strftime("%d%b%y").upper()+ str(stk) + typ
            tok = m.loc[m['symbol'] == nam].iloc[0]['token']
            if get_ltp(obj,"NFO",nam,tok ) == None:
                raise Exception 
            ab = "done"
            return nam, tok
        except:
            n = n+1
            if n >= 10:
                ab = "done"
                print(f"Symbol for {stk} not found")
                return None
    
def get_order_status(x,orderid): 
    x = pd.DataFrame.from_dict(x['data'])
    status = x.loc[x['orderid'] == str(int(orderid))].iloc[0]['status']
    return status

def order_book(obj):
    n = 0 
    ab = None
    while ab == None: 
        try:
            x = obj.orderBook()
            if x['status'] == False: 
                raise Exception 
            ab = "done"
            return x
        except:
            n = n +1 
            if n == 10 : 
                ab = "done"
                print("order book was not fetched")
                return None

def trade_book(obj):
    n = 0 
    ab = None
    while ab == None: 
        try:
            x = obj.tradeBook()
            if x['status'] == False: 
                raise Exception 
            ab = "done"
            return x
        except:
            n = n +1 
            if n == 10 : 
                ab = "done"
                print("trade book was not fetched")
                return None
            
def get_fill_price(x, orderid):
    x = pd.DataFrame.from_dict(x['data'])
    fillp = x.loc[x['orderid'] == str(int(orderid))].iloc[0]['fillprice']
    return fillp

def get_fill_time(x, orderid):
    x = pd.DataFrame.from_dict(x['data'])
    fillp = x.loc[x['orderid'] == str(int(orderid))].iloc[0]['filltime']
    return fillp


def place_ord(obj,sym,tok,trans,ord_typ, pri, tripri,quan,variety = "Normal", prod = "INTRADAY",exc = "NFO"):
    ab = None
    n = 0 
    while ab == None:
        try:
            orderparams = {
                "variety": variety,
                "tradingsymbol": sym,
                "symboltoken": str(int(tok)),
                "transactiontype": trans,
                "exchange": exc,
                "ordertype": ord_typ,
                "producttype": prod,
                "duration": "DAY",
                "price": pri,
                "triggerprice": tripri, 
                "squareoff": "0",
                "stoploss": "0",
                "quantity": quan
                }
    
            orderId=obj.placeOrder(orderparams)
            ab = 'done'
            return (orderId)
        except Exception as e:
            n = n+1
            if n == 10:
                print("Failed to place order")
                return None
                ab = "done"
                print(e)
                

def cancel_orders(orderid, obj): 
    ab = None
    n = 0
    while ab == None:
        try:
            can = obj.cancelOrder(int(orderid), variety = "STOPLOSS")
            # print(can)
            if can['status'] == False:
                raise Exception
            ab = "done"
        except: 
            n = n+1
            if n == 10: 
                print(f'orderid : {orderid} did not cancel')
                ab = "done"
                