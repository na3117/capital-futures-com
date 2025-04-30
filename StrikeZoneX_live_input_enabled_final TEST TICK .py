
"""
StrikeZoneX 即時模式（含 C、D 模組判斷）
"""
from comtypes.client import GetEvents  # ← 加這一行
from sk_api_strict import SKAPI
import comtypes.client
import comtypes.gen.SKCOMLib as sk
from comtypes import POINTER
from datetime import datetime, timedelta
import json
import os

# === 基本參數設定 ===
target_stocks = {
    "2330": {"support": 598, "resistance": 602},
    "8222": {"support": 125, "resistance": 128},
    "1736": {"support": 78, "resistance": 82}
}

TICK_HISTORY = {}
POSITIONS = {}
TRADES = []

price_range = 0.005
stop_loss_pct = 0.01
take_profit_pct = 0.02
entry_delay_seconds = 3


# === 即時進場判斷 ===
ALERTED = {}  # ← 這行放在 TICK_HISTORY = {} 底下

def try_entry(stock_id):
    ticks = TICK_HISTORY[stock_id]
    if len(ticks) < 2 or POSITIONS.get(stock_id):
        return

    if stock_id not in ALERTED:
        ALERTED[stock_id] = {"support": False, "resistance": False}

    t1, p1 = ticks[-2]
    t2, p2 = ticks[-1]
    s = target_stocks[stock_id]["support"]
    r = target_stocks[stock_id]["resistance"]

    support_min = s * (1 - price_range)
    support_max = s * (1 + price_range)
    resistance_min = r * (1 - price_range)
    resistance_max = r * (1 + price_range)

    now = t2

    # 支撐觀察提醒
    if support_min <= p1 <= support_max and support_min <= p2 <= support_max and not POSITIONS.get(stock_id):
        if not ALERTED[stock_id]["support"]:
            print(f"👀 觀察中：{stock_id} 連續觸及支撐區，尚未進場（方向：做多）")
            ALERTED[stock_id]["support"] = True

    # 壓力觀察提醒
    elif resistance_min <= p1 <= resistance_max and resistance_min <= p2 <= resistance_max and not POSITIONS.get(stock_id):
        if not ALERTED[stock_id]["resistance"]:
            print(f"👀 觀察中：{stock_id} 連續觸及壓力區，尚未進場（方向：做空）")
            ALERTED[stock_id]["resistance"] = True

    # 支撐進場條件
    if support_min <= p1 <= support_max and support_min <= p2 <= support_max:
        POSITIONS[stock_id] = {
            "type": "long",
            "entry_time": now,
            "entry_price": p2,
            "entry_reason": "支撐觸價進場"
        }
        ALERTED[stock_id]["support"] = False

    # 壓力進場條件
    elif resistance_min <= p1 <= resistance_max and resistance_min <= p2 <= resistance_max:
        POSITIONS[stock_id] = {
            "type": "short",
            "entry_time": now,
            "entry_price": p2,
            "entry_reason": "壓力觸價進場"
        }
        ALERTED[stock_id]["resistance"] = False


# === 即時出場判斷 ===
def try_exit(stock_id):
    if stock_id not in POSITIONS:
        return

    ticks = TICK_HISTORY[stock_id]
    current_time, current_price = ticks[-1]
    pos = POSITIONS[stock_id]

    entry_price = pos["entry_price"]
    entry_time = pos["entry_time"]
    position_type = pos["type"]

    stop_loss_price = entry_price * (1 - stop_loss_pct) if position_type == 'long' else entry_price * (1 + stop_loss_pct)
    take_profit_price = entry_price * (1 + take_profit_pct) if position_type == 'long' else entry_price * (1 - take_profit_pct)

    exit_reason = None

    if (position_type == "long" and current_price <= stop_loss_price) or        (position_type == "short" and current_price >= stop_loss_price):
        exit_reason = "停損"

    elif (position_type == "long" and current_price >= take_profit_price) or          (position_type == "short" and current_price <= take_profit_price):
        exit_reason = "停利"

    elif current_time.hour == 13:
        exit_reason = "13:00 強制平倉"

    if exit_reason:
        profit = (current_price - entry_price) * 1000 if position_type == 'long' else (entry_price - current_price) * 1000
        hold_time = (current_time - entry_time).total_seconds()
        TRADES.append({
            "股票": stock_id,
            "進場時間": entry_time.strftime("%H:%M:%S"),
            "進場價格": round(entry_price, 2),
            "方向": "多單" if position_type == "long" else "空單",
            "進場理由": pos["entry_reason"],
            "出場時間": current_time.strftime("%H:%M:%S"),
            "出場價格": round(current_price, 2),
            "出場理由": exit_reason,
            "損益": round(profit, 0),
            "持倉時間": f"{int(hold_time // 60)}分{int(hold_time % 60)}秒"
        })
        del POSITIONS[stock_id]
        print(f"✅ 出場：{exit_reason}，損益 {round(profit, 0)}")


# === Tick 接收事件處理 ===


# === Tick 接收回調 ===

def on_tick(stock_id, n_count):
    stock_id = str(stock_id)  # ✅ 確保是字串
    now = datetime.now()

    price = api.get_price(stock_id)
    if price is None:
        print(f"⚠️ 模擬 Tick 測試失敗：{stock_id} 沒有價格資料")
        return

    print(f"📥 Tick received: {stock_id} - {price}")

    if stock_id not in TICK_HISTORY:
        TICK_HISTORY[stock_id] = []
    TICK_HISTORY[stock_id].append((now, price))
    if len(TICK_HISTORY[stock_id]) > 100:
        TICK_HISTORY[stock_id] = TICK_HISTORY[stock_id][-100:]

    try_entry(stock_id)
    try_exit(stock_id)

# ✅ 正確放在 on_tick() 之後的事件類別
class TickEvent:
    def OnNotifyTicks(self, sMarketNo, sStockidx, nPtr, nCount):
        stock = api.sk_quote.SKQuoteLib_GetStockByIndex(sMarketNo, sStockidx)
        stock_id = stock.bstrStockNo
        on_tick(stock_id, nCount)

    
        
        
        

            


# === 主流程開始 ===

# === 使用者輸入股票與支撐壓力設定 ===
target_stocks = {}
print("請輸入股票代碼與支撐/壓力（格式：2330 598 602），輸入 done 結束：")
while True:
    line = input("→ ")
    if line.lower() == "done":
        break
    try:
        stock_id, support, resistance = line.strip().split()
        target_stocks[stock_id] = {
            "support": float(support),
            "resistance": float(resistance)
        }
    except:
        print("⚠️ 輸入格式錯誤，請重新輸入")

if not target_stocks:
    print("❌ 未輸入任何股票，結束程式")
    exit()

stock_list = ", ".join(target_stocks.keys())
print(f"✅ 已確認 {stock_list} 成功新增")

api = SKAPI()
api.stocks_to_subscribe = list(target_stocks.keys())
api.login("R124457999", "123jacky0")
api.set_tick_callback(on_tick)

tick_event_handler = TickEvent()
tick_event_hook = GetEvents(api.sk_quote, tick_event_handler)
print("✅ TickEvent 註冊完成")

# 手動觸發每支股票的 Tick 接收（上市 0，上櫃 1）
for stock_id in target_stocks:
    api.sk_quote.SKQuoteLib_RequestTicks(0, stock_id)  # 如果是上櫃記得改 1
    print(f"▶️ 已對 {stock_id} 發出 RequestTicks")

# 等報價伺服器連線穩定（等 OnConnect 回傳成功）
import time
time.sleep(2)

# === 測試 Tick 接收是否正常綁定 ===
print("🧪 模擬 Tick 測試 on_tick() 是否正常")
on_tick("2330", 1)

    

# 註冊 Tick 事件


print("▶️ 即時監控開始，按 Ctrl+C 中止")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("⛔ 結束監控")
    today = datetime.now().strftime("%Y%m%d")
    os.makedirs("report", exist_ok=True)
    with open(f"report/realtime_{today}.json", "w", encoding="utf-8") as f:
        json.dump(TRADES, f, ensure_ascii=False, indent=2)
    print(f"✅ 已儲存交易紀錄 report/realtime_{today}.json")



import threading
import keyboard

# === 大盤狀態記錄 ===
MARKET_INFO = {
    "price": None,
    "change_pct": None,
    "high": None,
    "is_new_high": False
}

class MarketEvent:
    def OnNotifyQuote(self, sMarketNo, sStockidx):
        stock = api.sk_quote.SKQuoteLib_GetStockByIndex(sMarketNo, sStockidx)
        now_price = stock.m_nClose / 100.0
        change_pct = stock.m_nUpDown / 100.0
        if MARKET_INFO["price"] is not None:
            MARKET_INFO["is_new_high"] = now_price > MARKET_INFO["high"]
        MARKET_INFO["price"] = now_price
        MARKET_INFO["change_pct"] = change_pct
        if MARKET_INFO["high"] is None or now_price > MARKET_INFO["high"]:
            MARKET_INFO["high"] = now_price

# === 快照功能（按 F8 輸出） ===
def get_snapshot():
    snapshot = {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "大盤": {
            "加權指數": MARKET_INFO["price"],
            "漲跌幅": MARKET_INFO["change_pct"],
            "是否創高": MARKET_INFO["is_new_high"]
        },
        "股票": {},
        "多股比較": {}
    }

    max_score = -1
    strongest_stock = None
    max_gain = -9999
    max_gain_stock = None
    triggered_stocks = []

    for stock_id, info in target_stocks.items():
        ticks = TICK_HISTORY.get(stock_id, [])
        current_price = ticks[-1][1] if ticks else None
        pos = POSITIONS.get(stock_id)

        support = info["support"]
        resistance = info["resistance"]
        range_ = support * price_range
        support_zone = (support - range_, support + range_)
        resistance_zone = (resistance - range_, resistance + range_)

        is_in_support = support_zone[0] <= current_price <= support_zone[1] if current_price else False
        is_in_resist = resistance_zone[0] <= current_price <= resistance_zone[1] if current_price else False

        # 模擬主力分數（實際可加強邏輯）
        score = 70 if is_in_support or is_in_resist else 50
        if score > max_score:
            max_score = score
            strongest_stock = stock_id

        if len(ticks) > 1:
            gain = (current_price - ticks[0][1]) / ticks[0][1] * 100
            if gain > max_gain:
                max_gain = gain
                max_gain_stock = stock_id

        if is_in_support or is_in_resist:
            triggered_stocks.append(stock_id)

        snapshot["股票"][stock_id] = {
            "目前價格": current_price,
            "支撐價": support,
            "壓力價": resistance,
            "是否觸支撐區": is_in_support,
            "是否觸壓力區": is_in_resist,
            "是否持倉": bool(pos),
            "進場價格": pos["entry_price"] if pos else None,
            "進場時間": pos["entry_time"].strftime("%H:%M:%S") if pos else None,
            "進場理由": pos["entry_reason"] if pos else None,
            "主力分數": score,
            "建議": "持有觀察" if pos else ("可考慮進場" if is_in_support or is_in_resist else "觀望")
        }

    snapshot["多股比較"] = {
        "主力最強": strongest_stock,
        "漲幅最大": max_gain_stock,
        "觸價中": triggered_stocks
    }

    os.makedirs("snapshot", exist_ok=True)
    filename = datetime.now().strftime("snapshot/f8_%Y%m%d_%H%M%S.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"📸 快照已儲存：{filename}")
    os.system("msg * 快照已儲存")

def monitor_f8():
    while True:
        if keyboard.is_pressed("F8"):
            get_snapshot()
            while keyboard.is_pressed("F8"):
                pass  # 避免重複觸發

threading.Thread(target=monitor_f8, daemon=True).start()
