import os
import time
import json
from datetime import datetime, time as dt_time

class TickRecorder:
    def __init__(self, stock_list, date_str=None):
        self.date_str = date_str or datetime.now().strftime("%Y%m%d")
        self.stock_list = stock_list
        self.ticks = {stock: [] for stock in stock_list}
        self.base_dir = "./ticks"
        os.makedirs(self.base_dir, exist_ok=True)

    def on_tick(self, stock_no, tick_data):
        if stock_no in self.ticks:
            self.ticks[stock_no].append(tick_data)

    def save(self):
        for stock_no, data in self.ticks.items():
            if data:
                file_path = os.path.join(self.base_dir, f"{self.date_str}_{stock_no}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

def wait_for_market_open():
    print("等待開盤中...（將於 09:00 自動開始記錄）")
    while datetime.now().time() < dt_time(9, 0):
        time.sleep(5)
    print("\u2705 開盤時間到，開始記錄 Tick 資料...")

def is_market_closed():
    return datetime.now().time() >= dt_time(13, 30)

def main():
    try:
        stock_input = input("請輸入要記錄的股票代號（用逗號分隔）：")
        stock_list = [s.strip() for s in stock_input.split(",") if s.strip()]
        print(f"已確認 {','.join(stock_list)} 成功新增")
        recorder = TickRecorder(stock_list)

        wait_for_market_open()

        last_status_time = time.time()

        while not is_market_closed():
            try:
                now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                for stock in stock_list:
                    fake_tick = {
                        "time": now,
                        "price": 100.0,
                        "volume": 1,
                        "bid": 99.5,
                        "ask": 100.5
                    }
                    recorder.on_tick(stock, fake_tick)

                if time.time() - last_status_time >= 1800:
                    print(f"\u23F3 [{datetime.now().strftime('%H:%M:%S')}] Recorder 運作正常")
                    last_status_time = time.time()

                time.sleep(1)

            except Exception as e:
                print(f"\u274C [{datetime.now().strftime('%H:%M:%S')}] Recorder 發生錯誤：{e}")
                break

        print("\u23F0 收盤時間到，自動儲存 Tick 資料...")
        recorder.save()
        print("\u2705 資料儲存完成，程式結束。")

    except KeyboardInterrupt:
        print("\n\u26A0\uFE0F 偵測到手動中斷，儲存目前已收集的 Tick 資料...")
        recorder.save()
        print("\u2705 資料已保存，程式結束。")

if __name__ == "__main__":
    main()