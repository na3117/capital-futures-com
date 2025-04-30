from comtypes.automation import IDispatch, VARIANT

class 回報事件接收器:
    def __init__(self, 外部控制器=None):
        self.外部控制器 = 外部控制器

    def OnReplyMessage(self, this, 使用者ID, 訊息內容, 型態):
        print(f"🧩 [公告回報] 使用者ID={使用者ID} 訊息內容={訊息內容} 型態={型態}")
        try:
            if hasattr(型態, "_obj") and hasattr(型態._obj, "value"):
                型態值 = 型態._obj.value
            elif hasattr(型態, "value"):
                型態值 = 型態.value
            else:
                型態值 = int(型態)

            if self.外部控制器:
                self.外部控制器.已收到公告 = True

            if 型態值 == 3001:
                print("🟢 [登入成功] 收到3001公告 ✅")
                if self.外部控制器:
                    self.外部控制器.登入成功 = True
            elif 型態值 == 3003 or 型態值 == 4002:
                print("🔵 [伺服器連線完成] 收到3003或4002公告 ✅")
                if self.外部控制器:
                    self.外部控制器.伺服器已連線 = True
            else:
                print(f"🟠 [其他公告] 型態={型態值}，無需特別處理")

        except Exception as e:
            print(f"⚠️ [錯誤] OnReplyMessage 解包失敗：{e}")

        return -1

class 行情事件接收器:
    def __init__(self, 外部控制器=None):
        self.外部控制器 = 外部控制器

    def OnConnection(self, nKind, nCode):
        print(f"📢 [行情OnConnection] nKind={nKind}, nCode={nCode}")
        if nKind == 3001 and nCode == 0:
            print("🟢 [行情伺服器連線成功] Stocks Ready ✅")
            if self.外部控制器:
                self.外部控制器.行情伺服器連線完成 = True
                # 🔥這裡真正去小額Request一支股票啟動伺服器流
                try:
                    ret = self.外部控制器.報價物件.SKQuoteLib_RequestStocks(0, "2330")
                    if ret != 0:
                        print(f"[警告] 初始化訂閱2330失敗，錯誤碼={ret}")
                    else:
                        print("🟢 [初始化訂閱成功] 已成功訂閱 2330 ✅")
                except Exception as e:
                    print(f"[錯誤] 嘗試初始化訂閱2330時失敗：{e}")
