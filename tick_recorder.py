import os
import time
import json
from datetime import datetime, time as dt_time
from sk_api_strict import 群益API

class 即時資料紀錄器:
    def __init__(self, 股票清單, 日期字串=None):
        self.日期字串 = 日期字串 or datetime.now().strftime("%Y%m%d")
        self.股票清單 = 股票清單
        self.資料庫 = {股票: [] for 股票 in 股票清單}
        self.儲存資料夾 = "./ticks"
        os.makedirs(self.儲存資料夾, exist_ok=True)
        self.測試標記 = {股票: False for 股票 in 股票清單}

    def 當收到即時資料(self, 股票代號, _):
        價格 = api.get_price(股票代號)
        if 價格 is not None:
            現在時間 = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            一筆資料 = {
                "時間": 現在時間,
                "價格": 價格,
                "成交量": 1
            }
            self.資料庫[股票代號].append(一筆資料)
            if not self.測試標記[股票代號]:
                print(f"[測試] 收到即時資料：{股票代號} - {價格}")
                self.測試標記[股票代號] = True
            else:
                print(f"[即時] [{現在時間}] {股票代號} - {價格}")

    def 儲存資料(self):
        for 股票代號, 資料 in self.資料庫.items():
            if 資料:
                檔案路徑 = os.path.join(self.儲存資料夾, f"{self.日期字串}_{股票代號}.json")
                with open(檔案路徑, "w", encoding="utf-8") as f:
                    json.dump(資料, f, indent=2, ensure_ascii=False)

def 等待開盤(首支股票):
    print("[等待中] 等待開盤...（預計09:00）")
    最後一筆資料 = api.get_last_tick(首支股票)
    if 最後一筆資料:
        print(f"[等待中] 上一筆資料：{首支股票} - {最後一筆資料['價格']} @ {最後一筆資料['時間']}")
    else:
        print(f"[警告] 無法取得{首支股票}的最後成交資料")

    while datetime.now().time() < dt_time(9, 0):
        time.sleep(5)

    print("[開盤] 開始記錄即時資料...")

def 是否收盤():
    return datetime.now().time() >= dt_time(13, 30)

def 主程序():
    global api
    try:
        股票輸入 = input("請輸入股票代號(以逗號分隔): ")
        股票清單 = [s.strip() for s in 股票輸入.split(",") if s.strip()]
        print(f"[設定] 新增股票：{','.join(股票清單)}")

        api = 群益API()
        api.stocks_to_subscribe = 股票清單
        api.登入("USERNAME", "PASSWORD")  # 請替換成真實帳號密碼

        紀錄器 = 即時資料紀錄器(股票清單)
        首支股票 = 股票清單[0]
        等待開盤(首支股票)

        最後狀態時間 = time.time()
        while not 是否收盤():
            價格 = api.get_price(首支股票)
            if 價格 is not None:
                現在時間 = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[即時] [{現在時間}] {首支股票} 最新價格 - {價格}")

            time.sleep(1)
            if time.time() - 最後狀態時間 >= 1800:
                print(f"[狀態] [{datetime.now().strftime('%H:%M:%S')}] 紀錄器運作正常")
                最後狀態時間 = time.time()

        print("[收盤] 市場已收盤，開始儲存資料...")
        紀錄器.儲存資料()
        print("[完成] 資料儲存成功，程式結束。")

    except KeyboardInterrupt:
        print("\n[警告] 手動中斷，儲存資料...")
        紀錄器.儲存資料()
        print("[完成] 資料儲存完成，程式結束。")

if __name__ == "__main__":
    主程序()
