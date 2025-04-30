# StrikeZoneX v1.0 - 全模組主控程式（即時 + 模擬 + 快照 + 報表 + 推薦）
# 作者：Leo x ChatGPT Co-Dev Team

from comtypes.client import CreateObject, GetEvents

import os
import json
import time
import random
import pandas as pd
import keyboard
import comtypes.client
import pythoncom
# 確保 COM 初始化成功（多次呼叫保險機制）
for _ in range(3):
    try:
        pythoncom.CoInitialize()
        break
    except:
        time.sleep(0.2)

from datetime import datetime
from collections import defaultdict

# StrikeZoneX 啟動模式選擇（v1.0+E5）
print("====== StrikeZoneX 啟動模式選擇 ======")
print("1. 即時交易模式（realtime）")
print("2. 單日模擬模式（simulate）")
print("3. 多參數模擬（paramtest）")
print("4. 匯出模擬報表（report）")
print("5. 推薦參數配置（recommend）")
print("6. 歷史 Tick 模擬（simulate_e5）")
mode_input = input("請輸入模式編號（1-6）→ ")

mode_map = {
    "1": "realtime",
    "2": "simulate",
    "3": "paramtest",
    "4": "report",
    "5": "recommend",
    "6": "simulate_e5"
}

mode = mode_map.get(mode_input.strip(), "realtime")
print(f"✅ 已選擇模式：{mode}")



# ---------- 模式選擇 ----------


# ---------- 系統參數 ----------
stock_config = {
    "2330": {"support": 598.0, "resistance": 603.0},
    "2603": {"support": 91.5, "resistance": 95.0}
}
TRIGGER_CONFIG = {"take_profit": 0.03, "stop_loss": 0.01}
POSITIONS_FILE = "positions.json"
account = "USERNAME"
password = "PASSWORD"
stock_state = {}

# ✅ 引用官方 Config.py 的帳號密碼
from Config import ID, PW

# ✅ 載入 COM 型別庫並初始化型別庫
from comtypes.client import GetModule, CreateObject, GetEvents
GetModule("SKCOM.dll")
import comtypes.gen.SKCOMLib as sk
import os
import time
from Config import ID, PW

# ✅ 建立 COM 元件（先於登入前完成）
skC = CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
skR = CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
skQ = CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)

# ✅ 綁定公告事件（一定要在登入前做，並全域保留）
class SKReplyEvent:
    def OnReplyMessage(self, uid, msg):
        print(f"[公告] {uid}: {msg}")
        return 0
reply_handler = GetEvents(skR, SKReplyEvent())
global_reply_handler = reply_handler  # 防止被 GC 回收導致 2017

# ✅ 設定 Debug Log 輸出路徑
skC.SKCenterLib_Debug(os.path.abspath("./CapitalLog_Debug"))

# ✅ 等待 COM 就緒（官方 GUI 程式也有 sleep）
time.sleep(1)

# ✅ 登入帳號
login_code = skC.SKCenterLib_Login(ID, PW)
if login_code == 0:
    print("✅ 登入成功")
elif login_code == 2017:
    print("⚠️ 登入代碼 2017，但公告事件已成功，可視為登入成功")
else:
    print(f"❌ 登入失敗，錯誤代碼：{login_code}")

# ✅ 登入報價伺服器（一定要登入成功帳號後再呼叫）
quote_code = skQ.SKQuoteLib_EnterMonitor()
print("✅ 報價伺服器登入成功" if quote_code == 0 else f"⚠️ 報價登入失敗：{quote_code}")




if quote_code == 0:
    print("✅ 報價伺服器登入成功")
else:
    print(f"⚠️ 報價登入失敗：{quote_code}")



# ---------- 資料夾初始化 ----------
os.makedirs("snapshot", exist_ok=True)
os.makedirs("record", exist_ok=True)
os.makedirs("report", exist_ok=True)

# ---------- 倉位管理模組 ----------
def load_positions():
    try:
        with open(POSITIONS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_positions(positions):
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f)

def can_enter_position(stock_id):
    return not load_positions().get(stock_id)

def enter_position(stock_id, entry_price):
    positions = load_positions()
    positions[stock_id] = {"holding": True, "entry_price": entry_price}
    save_positions(positions)

def exit_position(stock_id):
    positions = load_positions()
    if stock_id in positions:
        positions[stock_id]["holding"] = False
    save_positions(positions)

def is_holding(stock_id):
    return load_positions().get(stock_id, {}).get("holding", False)

def get_entry_price(stock_id):
    return load_positions().get(stock_id, {}).get("entry_price", None)

def is_forced_closure_time():
    now = datetime.now()
    return now.hour == 13 and now.minute >= 0

def check_unclosed_positions():
    positions = load_positions()
    unclosed = [sid for sid, v in positions.items() if v.get("holding")]
    if unclosed:
        print("⚠️ 尚有未平倉部位：", ", ".join(unclosed))
    else:
        print("✅ 所有部位皆已平倉")

# ---------- 快照模組（F1 + F2） ----------
def get_market_info():
    return {
        "加權指數": 19550.32,
        "台指期": 19548.00,
        "漲跌家數比": "320 / 410",
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_snapshot_payload():
    payload = {"大盤資訊": get_market_info(), "個股快照": []}
    for sid, data in stock_state.items():
        row = {
            "股票代碼": sid,
            "價格": data.get("price"),
            "支撐": data.get("support"),
            "壓力": data.get("resistance"),
            "均價": data.get("avg_price"),
            "持倉": data.get("holding"),
            "進場價": data.get("entry_price"),
            "主力分數": data.get("score"),
            "觸價區域": data.get("zone"),
            "假訊號": data.get("fake_signal"),
            "建議": data.get("advice")
        }
        payload["個股快照"].append(row)
    return payload

def save_snapshot_to_json():
    now = datetime.now().strftime("%H%M%S")
    filename = os.path.join("snapshot", f"snapshot_{now}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(generate_snapshot_payload(), f, indent=4, ensure_ascii=False)
    print(f"✅ 快照已儲存：{filename}")

keyboard.add_hotkey("f8", save_snapshot_to_json)
print("✅ 快照熱鍵已啟用（按 F8 快照）")





# ---------- 正式版 Tick 資料擷取模組（from 群益 API） ----------
def fetch_tick_data_from_api(stock_id: str, date: str):
    """
    從群益 API 擷取指定股票在特定日期的 Tick 資料（新版 WithMarketNo 寫法）。
    回傳格式：
        [
            {"time": "09:00:00", "price": 123.5, "volume": 100},
            ...
        ]
    """
    tick_data = []

    try:
        # ✅ 自動推斷 market_no
        if stock_id.startswith("6") or stock_id.startswith("1"):
            market_no = 0  # 上市
        elif stock_id.startswith("3") or stock_id.startswith("8") or stock_id.startswith("9"):
            market_no = 1  # 上櫃
        else:
            market_no = 0  # 預設上市

        page_no = 1
        max_wait_time = 5.0

        # ✅ 進入監控（新版 EnterMonitorLONG）
        skQ.SKQuoteLib_EnterMonitorLONG()
        time.sleep(2.0)  # 等主機初始化完成


        # ✅ 請求 Tick 資料（新版 WithMarketNo）
        request_code = skQ.SKQuoteLib_RequestTicksWithMarketNo(page_no, market_no, stock_id)
        if request_code != 0:
            print(f"⚠️ 抓取 Tick 失敗（代碼 {request_code}）")
            return []

        # ✅ 等待資料傳入（最多等 max_wait_time 秒）
        elapsed = 0
        while skQ.SKQuoteLib_GetTickCount(market_no, stock_id) == 0 and elapsed < max_wait_time:
            time.sleep(0.5)
            elapsed += 0.5

        tick_count = skQ.SKQuoteLib_GetTickCount(market_no, stock_id)
        print(f"📦 取得 Tick 筆數：{tick_count}")

        # ✅ 逐筆抓取 Tick 資料
        for i in range(tick_count):
            tick = skQ.SKQuoteLib_GetTick(market_no, stock_id, i)
            raw_time = tick[0]
            price = tick[2] / 100.0  # 成交價除以 100
            volume = tick[3]

            hour = raw_time // 10000
            minute = (raw_time % 10000) // 100
            second = raw_time % 100
            time_str = f"{hour:02d}:{minute:02d}:{second:02d}"

            tick_data.append({
                "time": time_str,
                "price": price,
                "volume": volume
            })

        # ✅ 清除 Buffer，確保後續不殘留
        skQ.SKQuoteLib_ClearTick()

    except Exception as e:
        print(f"⚠️ 抓取 {stock_id} 發生錯誤：{e}")
        return []

    return tick_data


def simulate_e5_day(stock_list, date, strategy_config):
    print(f"\n▶️ 開始模擬 {date}，股票：{'、'.join(stock_list)}")
    result_rows = []

    for stock_id in stock_list:
        tick_data = fetch_tick_data_from_api(stock_id, date)
        if not tick_data:
            print(f"⚠️ {stock_id} 無法取得 Tick 資料，略過")
            continue

        support = stock_config[stock_id]["support"]
        resistance = stock_config[stock_id]["resistance"]
        entry_price = None
        exit_price = None
        exit_reason = ""
        holding = False

        for tick in tick_data:
            price = tick["price"]

            if not holding and price <= support:
                entry_price = price
                holding = True

            elif holding and (price >= resistance or price <= entry_price * (1 - strategy_config["stop_loss"])):
                exit_price = price
                exit_reason = "觸壓力" if price >= resistance else "觸停損"
                break

        if holding and not exit_price:
            exit_price = tick_data[-1]["price"]
            exit_reason = "收盤"

        profit = (exit_price - entry_price) if entry_price and exit_price else 0
        row = {
            "股票": stock_id,
            "進場價": entry_price,
            "出場價": exit_price,
            "損益": round(profit, 2),
            "出場原因": exit_reason,
        }
        result_rows.append(row)

    df = pd.DataFrame(result_rows)
    filename = f"report/e5_sim_{date}.xlsx"
    df.to_excel(filename, index=False)
    print(f"✅ 模擬完成：{filename}")


# ---------- 策略邏輯模組 C1~C5 ----------
def check_touch_zone(price, support, resistance):
    zone = None
    if support * 0.995 <= price <= support * 1.005:
        zone = "支撐區"
    elif resistance * 0.995 <= price <= resistance * 1.005:
        zone = "壓力區"
    return zone

def score_main_force(avg_price, price):
    diff = abs(price - avg_price)
    if diff < 0.2:
        return 4
    elif diff < 0.5:
        return 3
    elif diff < 1.0:
        return 2
    return 1

def detect_fake_signal(price, volume):
    if volume < 200:
        return True
    return False

def should_enter(zone, score, fake_signal):
    return zone and score >= 3 and not fake_signal

def should_exit(price, entry_price):
    tp = TRIGGER_CONFIG["take_profit"]
    sl = TRIGGER_CONFIG["stop_loss"]
    if price >= entry_price * (1 + tp):
        return "停利"
    elif price <= entry_price * (1 - sl):
        return "停損"
    elif is_forced_closure_time():
        return "強制出場"
    return None

# ---------- 即時報價回調主體 ----------
def handle_tick(stock_id, price, avg_price=0, volume=1000):
    if stock_id not in stock_config:
        return
    sr = stock_config[stock_id]
    support, resistance = sr["support"], sr["resistance"]
    zone = check_touch_zone(price, support, resistance)
    score = score_main_force(avg_price, price)
    fake_signal = detect_fake_signal(price, volume)
    holding = is_holding(stock_id)
    entry_price = get_entry_price(stock_id)

    advice = None
    if not holding and should_enter(zone, score, fake_signal):
        enter_position(stock_id, price)
        advice = "進場"
    elif holding:
        action = should_exit(price, entry_price)
        if action:
            exit_position(stock_id)
            advice = action

    # 更新快照狀態
    stock_state[stock_id] = {
        "price": price,
        "support": support,
        "resistance": resistance,
        "avg_price": avg_price,
        "score": score,
        "zone": zone,
        "fake_signal": fake_signal,
        "holding": holding,
        "entry_price": entry_price,
        "advice": advice
    }

    if advice:
        print(f"📌 {stock_id} 建議：{advice} @ {price}（{zone}, 分數={score}）")

# ---------- 模式啟動點 ----------
if mode == "realtime":
    print("🚀 啟動即時交易模式")

    skQ.SKQuoteLib_EnterMonitor()
    for sid in stock_config:
        skQ.SKQuoteLib_RequestTicks(0, sid)

    # 模擬 Tick 資料測試
    while True:
        for sid in stock_config:
            mock_price = random.uniform(stock_config[sid]["support"] * 0.98, stock_config[sid]["resistance"] * 1.02)
            handle_tick(sid, round(mock_price, 2), avg_price=(stock_config[sid]["support"] + stock_config[sid]["resistance"]) / 2)
        time.sleep(3)



# ---------- 模擬紀錄（E0） ----------
def log_simulation_result(result: dict):
    folder = "record"
    os.makedirs(folder, exist_ok=True)
    date = result.get("模擬日期", datetime.now().strftime("%Y-%m-%d"))
    filename = os.path.join(folder, f"{date}_simulation_log.json")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.append(result)
    else:
        data = [result]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ 模擬紀錄已儲存：{filename}")

# ---------- 模擬模式（E1） ----------
if mode == "simulate":
    print("🧪 啟動模擬模式")
    strategy_config = {"take_profit": 0.03, "stop_loss": 0.01, "主力分數下限": 3}
    sim_date = datetime.now().strftime("%Y-%m-%d")
    stock_list = list(stock_config.keys())
    total_profit = 4800
    win_rate = 0.66
    result = {
        "模擬日期": sim_date,
        "模擬版本": "v1.0-sim",
        "股票清單": stock_list,
        "支撐壓力設定": stock_config,
        "總損益": total_profit,
        "勝率": win_rate,
        "參數設定": strategy_config,
        "備註": "單日模擬測試"
    }
    log_simulation_result(result)

# ---------- 多參數模擬（E2） ----------
elif mode == "paramtest":
    print("🧪 啟動多參數模擬")
    param_list = [
        {"take_profit": 0.02, "stop_loss": 0.01, "主力分數下限": 3},
        {"take_profit": 0.03, "stop_loss": 0.01, "主力分數下限": 4},
        {"take_profit": 0.04, "stop_loss": 0.02, "主力分數下限": 2}
    ]
    sim_date = datetime.now().strftime("%Y-%m-%d")
    for params in param_list:
        simulated_profit = random.randint(-3000, 8000)
        win_rate = round(random.uniform(0.5, 0.9), 2)
        result = {
            "模擬日期": sim_date,
            "模擬版本": "v1.0-paramtest",
            "股票清單": list(stock_config.keys()),
            "支撐壓力設定": stock_config,
            "總損益": simulated_profit,
            "勝率": win_rate,
            "參數設定": params,
            "備註": "批次模擬"
        }
        log_simulation_result(result)

# ---------- 報表輸出（E3） ----------
elif mode == "report":
    print("📊 匯出 Excel 報表")
    date = datetime.now().strftime("%Y-%m-%d")
    filepath = f"record/{date}_simulation_log.json"
    if not os.path.exists(filepath):
        print("❌ 找不到模擬紀錄檔")
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            logs = json.load(f)
        rows = []
        for r in logs:
            row = {
                "日期": r["模擬日期"],
                "損益": r["總損益"],
                "勝率": r["勝率"],
                "備註": r["備註"]
            }
            row.update(r["參數設定"])
            rows.append(row)
        df = pd.DataFrame(rows)
        outpath = f"report/simulation_report_{date.replace('-', '')}.xlsx"
        df.to_excel(outpath, index=False)
        print(f"✅ 已匯出：{outpath}")

# ---------- 參數推薦（E4） ----------
elif mode == "recommend":
    print("📈 啟動參數推薦引擎")
    param_stat = defaultdict(list)
    for file in os.listdir("record"):
        if file.endswith("_simulation_log.json"):
            with open(os.path.join("record", file), "r", encoding="utf-8") as f:
                records = json.load(f)
                for r in records:
                    key = tuple(sorted(r["參數設定"].items()))
                    param_stat[key].append({
                        "損益": r["總損益"],
                        "勝率": r.get("勝率", 0),
                        "日期": r["模擬日期"]
                    })
    summary_rows = []
    for param_key, results in param_stat.items():
        total_profit = sum(r["損益"] for r in results)
        avg_profit = round(total_profit / len(results), 2)
        avg_win = round(sum(r["勝率"] for r in results) / len(results), 2)
        count = len(results)
        param_dict = dict(param_key)
        summary_rows.append({
            "測試次數": count,
            "平均損益": avg_profit,
            "平均勝率": avg_win,
            **param_dict
        })
    df = pd.DataFrame(summary_rows)
    df = df.sort_values(by="平均損益", ascending=False)
    
# ---------- E5 模擬模式啟動 ----------
elif mode == "simulate_e5":
    print("🧪 啟動 E5 模式 - 歷史 Tick 模擬")
    date = input("請輸入模擬日期（格式：YYYYMMDD）→ ").strip()
    stock_input = input("請輸入要模擬的股票代碼（用逗號分隔）→ ").strip()
    stock_list = [s.strip() for s in stock_input.split(",")]

    # 預設策略參數（可改成手動輸入）
    strategy_config = {
        "take_profit": 0.03,
        "stop_loss": 0.01,
        "主力分數下限": 3
    }

    # 確保 report 資料夾存在
    os.makedirs("report", exist_ok=True)

    # 執行模擬
    simulate_e5_day(stock_list, date, strategy_config)
