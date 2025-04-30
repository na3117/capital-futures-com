import os
import time
import comtypes.client
from sk_reply_handler import 回報事件接收器, 行情事件接收器

# 載入 COM 元件
comtypes.client.GetModule(os.path.split(os.path.realpath(__file__))[0] + r"\SKCOM.dll")
import comtypes.gen.SKCOMLib as sk

class 群益API:
    def __init__(self):
        print("[初始化] 建立 COM 元件：SKCenterLib、SKReplyLib、SKOrderLib、SKQuoteLib")
        self.中心物件 = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        self.回報物件 = comtypes.client.CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
        self.下單物件 = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
        self.報價物件 = comtypes.client.CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)

        self.登入成功 = False
        self.伺服器已連線 = False
        self.行情伺服器連線完成 = False
        self.帳號清單 = []
        self.stocks_to_subscribe = []

        print("[初始化] 註冊事件處理器...")
        self.回報事件 = 回報事件接收器(外部控制器=self)
        self.回報處理器 = comtypes.client.GetEvents(self.回報物件, self.回報事件)
        print("✅ 已註冊 SKReplyLib.OnReplyMessage")

        self.下單事件 = 回報事件接收器(外部控制器=self)
        self.下單處理器 = comtypes.client.GetEvents(self.下單物件, self.下單事件)
        print("✅ 已註冊 SKOrderLib.OnAccount 及相關事件")

        self.行情事件 = 行情事件接收器(外部控制器=self)
        self.行情處理器 = comtypes.client.GetEvents(self.報價物件, self.行情事件)
        print("✅ 已註冊 SKQuoteLib.OnConnection 及行情事件")

        time.sleep(1)

        print("[初始化] 連接行情伺服器 EnterMonitor()...")
        ret = self.報價物件.SKQuoteLib_EnterMonitor()
        if ret != 0:
            raise Exception(f"[錯誤] EnterMonitor失敗，錯誤碼={ret}")
        print("[初始化] 行情伺服器連線指令送出 ✅")

        print("[初始化] 小額訂閱一支股票 Tick（2330）啟動伺服器流...")
        ret = self.報價物件.SKQuoteLib_RequestTicks(0, "2330")
        if ret != 0:
            print(f"[警告] 小額訂閱Tick 2330失敗，錯誤碼={ret}")
        else:
            print("[初始化] 小額訂閱Tick 2330成功 ✅")

        print("[等待中] 等待行情伺服器 Stocks Ready（3001）...")
        等待秒數 = 0
        while not self.行情伺服器連線完成 and 等待秒數 < 30:
            time.sleep(1)
            等待秒數 += 1
            print(f"[等待中] 第 {等待秒數} 秒...", end='\r')
        if not self.行情伺服器連線完成:
            raise Exception("[錯誤] 等待行情伺服器Stocks Ready超時 ❌")
        print("\n[完成] 行情伺服器連線成功 ✅")
