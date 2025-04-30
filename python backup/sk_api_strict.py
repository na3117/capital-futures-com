import comtypes.client
from ctypes import Structure, c_int, c_short, c_char, c_char_p
from comtypes import byref

class STOCKTICK(Structure):
    _fields_ = [
        ("m_nTime", c_int),
        ("m_nClose", c_int),
        ("m_nQty", c_int),
        ("m_nSimulate", c_short),
        ("m_nUpDown", c_short),
        ("m_nReserved", c_short * 2),
        ("m_cTag", c_char),
        ("m_nBeforeQty", c_int),
        ("m_nAfterQty", c_int),
        ("m_nBid", c_int),
        ("m_nAsk", c_int),
        ("m_nSimulateNo", c_int),
        ("m_cMarketNo", c_char),
        ("m_cMarketNo2", c_char),
        ("m_strBidAsk", c_char_p),
    ]

from comtypes.client import CreateObject, GetEvents
import time
import comtypes.gen.SKCOMLib as sk
from comtypes.automation import IDispatch

class QuoteEvent:
    def __init__(self, on_connected_callback=None, outer=None, quote_lib=None):
        self.on_connected_callback = on_connected_callback
        self.on_tick_callback = None
        self.outer = outer
        self.quote_lib = quote_lib  # ✅ 加這行


    def OnConnection(self, nKind, nCode):
        print(f"🧪 [Debug] OnConnection received: nKind={nKind}, nCode={nCode}")
        if nKind == 3003 and nCode == 0:
            print("✅ 報價連線完成 (3003 STKS_READY)")
            if self.outer:
                self.outer.stocks_ready = True



            if self.on_connected_callback:
                self.on_connected_callback()

    def OnConnect(self, nCode):
        status = "成功" if nCode == 0 else f"失敗（代碼 {nCode}）"
        print(f"📡 報價伺服器連線狀態回傳：{status}")
        if nCode == 0 and self.on_connected_callback:
            self.on_connected_callback()

    def OnNotifyTicksLONG(self, sMarketNo, sStockidx, nPtr, nTickCount):
        try:
            stock = self.quote_lib.SKQuoteLib_GetStockByIndex(sMarketNo, sStockidx)
            stock_id = stock.bstrStockNo
            print(f"📡 [Tick事件LONG] 股票：{stock_id}（index {sStockidx}）筆數：{nTickCount}")
            if self.on_tick_callback:
                self.on_tick_callback(stock_id, nTickCount)
        except Exception as e:
            print(f"⚠️ 無法解析 Tick 事件：{e}")

    def OnNotifyHistoryTicksLONG(self, sMarketNo, sStockidx, nPtr, lDate, lTimehms, lTimemillismicros,
                                  nBid, nAsk, nClose, nQty, nSimulate):
        try:
            stock = api.sk_quote.SKQuoteLib_GetStockByIndex(sMarketNo, sStockidx)
            stock_id = stock.bstrStockNo
            print(f"🕒 [歷史Tick補回] {stock_id} | 時間={lTimehms} 價格={nClose/1000:.2f} 量={nQty}")
            if self.on_tick_callback:
                self.on_tick_callback(stock_id, 1)
        except Exception as e:
            print(f"⚠️ 無法處理歷史 Tick 補回事件：{e}")

from sk_reply_handler import SKReplyEventSink  # 放最上面
self.reply_handler = GetEvents(self.sk_reply, SKReplyEventSink(self))


from comtypes.client import GetEvents
from comtypes.gen.SKCOMLib import SKCenterLib, SKReplyLib

class SKAPI:
    def __init__(self):
        self.sk_center = SKCenterLib()
        self.sk_reply = SKReplyLib()
        self.login_success = False   # 🔥 必加！
        
        # 🔥 在這裡綁事件 (一定要在 sk_reply 建好後)
        self.reply_handler = GetEvents(self.sk_reply, SKReplyEventSink(self))

    def login(self, id, password):
        ret = self.sk_center.SKCenterLib_Login(id, password)
        if ret != 0:
            raise Exception(f"❌ 登入指令失敗 code={ret}")

        print("📥 等待登入公告...")
        timeout = 30
        start = time.time()
        while not self.login_success:
            if time.time() - start > timeout:
                raise Exception("❌ 登入超時：未收到登入公告")
            time.sleep(0.1)

        print("✅ 登入成功！")



    def set_tick_callback(self, on_tick_callback):
        if hasattr(self, "quote_event"):
            self.quote_event.on_tick_callback = on_tick_callback
        else:
            print("⚠️ quote_event 尚未初始化，無法綁定 tick callback")

    def on_quote_connected(self):
        print("🟢 報價伺服器已連線，開始訂閱股票...")
        for stock_id in getattr(self, "stocks_to_subscribe", []):
            market = self.detect_market(stock_id)
            ret1 = self.sk_quote.SKQuoteLib_RequestStocks(market, stock_id)
            ret2 = self.sk_quote.SKQuoteLib_RequestTicks(market, stock_id)
            print(f"✅ 訂閱 {stock_id} 結果：報價 {ret1} / Tick {ret2}")

    def detect_market(self, stock_id: str) -> int:
        if len(stock_id) >= 4:
            prefix = stock_id[:1]
            if prefix == "6" or prefix == "2":
                return 0
            elif prefix == "3" or prefix == "8":
                return 1
            elif prefix.upper() == "F":
                return 2
        return 0

    def get_price(self, stock_id: str):
        try:
            result = self.sk_quote.SKQuoteLib_GetStockByNo(stock_id)
            if isinstance(result, list) and len(result) > 0:
                stock = result[0]
                print(f"🧪 [Debug] {stock_id} 原始報價物件：nClose={stock.nClose}, nOpen={stock.nOpen}, nHigh={stock.nHigh}")
                return stock.nClose / 100.0
            else:
                print(f"⚠️ 無法取得 {stock_id} 報價（回傳值為空或非預期）")
                return None
        except Exception as e:
            print(f"⚠️ 取得 {stock_id} 報價失敗：{e}")
            return None

    def get_ticks(self, stock_id: str, date: str):
        print(f"▶️ 模擬抓取 Tick：{stock_id}，日期：{date}")
        market = self.detect_market(stock_id)
        tick_list = []
        print(f"📥 開始讀取歷史 Tick：{stock_id} / {date}")
        for i in range(2000):
            tick = STOCKTICK()
            result = self.sk_quote.SKQuoteLib_GetTickLONG(stock_id, date, i, byref(tick))
            if result != 0:
                print(f"❌ 第 {i} 筆失敗，錯誤代碼：{result}")
                break
            print(f"✅ Tick[{i}]：時間={tick.m_nTime}, 價格={tick.m_nClose}, 單量={tick.m_nQty}")
            tick_data = {
                "時間": f"{tick.m_nTime // 10000:02d}:{(tick.m_nTime % 10000) // 100:02d}:{tick.m_nTime % 100:02d}",
                "價格": tick.m_nClose / 100.0,
                "單量": tick.m_nQty,
                "成交類別": tick.m_nSimulate,
            }
            tick_list.append(tick_data)
        if not tick_list:
            print(f"⚠️ 結果為空：SKQuoteLib_GetTickLONG 沒有回傳任何 Tick。請確認日期 {date} 是否為交易日。")
        return tick_list