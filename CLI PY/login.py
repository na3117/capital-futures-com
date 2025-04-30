import comtypes.client
from comtypes.client import CreateObject, GetEvents
import pythoncom
import time

# 匯入 COM 類型庫（確保 SKCOM.dll 路徑正確）
comtypes.client.GetModule(r'./x64/SKCOM.dll')
import comtypes.gen.SKCOMLib as sk

# 建立 COM 物件
skC = CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
skQ = CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)
skR = CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)

# -- Step 1: 設定 Log 路徑與 Debug --
skC.SKCenterLib_SetLogPath("C:\\CapitalLog")  # 可自定資料夾路徑
skC.SKCenterLib_Debug(True)

# -- Step 2: 註冊公告事件（防止 2017 錯誤）--
class ReplyHandler:
    def OnReplyMessage(self, bstrUserID, bstrMessage):
        return -1

global_reply_hook = GetEvents(skR, ReplyHandler())

# -- Step 3: 登入帳號（請改為你的帳密） --
user_id = "USERNAME"
password = "PASSWORD"
nCode = skC.SKCenterLib_Login(user_id, password)
print("登入回傳：", nCode, skC.SKCenterLib_GetReturnCodeMessage(nCode))
time.sleep(1)

# -- Step 4: 啟動報價主機連線 --
nCode = skQ.SKQuoteLib_EnterMonitorLONG()
print("報價主機連線結果：", nCode, skC.SKCenterLib_GetReturnCodeMessage(nCode))
time.sleep(1)

# -- Step 5: 註冊 Tick 通知 --
class TickHandler:
    def OnNotifyTicksLONG(self, sMarketNo, sStockidx, nPtr):
        print("收到 Tick 通知事件（OnNotifyTicksLONG）")

tick_hook = GetEvents(skQ, TickHandler())

# -- Step 6: 要求特定商品 Tick --
# 市場別 1 = 上市、2 = 上櫃、3 = 興櫃；商品代號 = 字串
market_no = 1
stock_no = "2330"  # 例如台積電
skQ.SKQuoteLib_RequestTicksWithMarketNo(market_no, stock_no)

# -- Step 7: 等待接收 --
print("等待 Tick 資料...")
while True:
    pythoncom.PumpWaitingMessages()
    time.sleep(0.1)
