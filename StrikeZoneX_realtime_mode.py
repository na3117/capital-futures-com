
"""
StrikeZoneX 即時模式主控程式（v1.0）

功能：
- 登入群益 API（修復 2017 問題）
- 監控多檔股票
- 即時判斷進場（支撐 / 壓力觸價）
- 主力過濾、假突破排除
- 停損、停利、13:00 平倉
- F8 快捷鍵快照（JSON 輸出）
"""

from sk_api_strict import SKAPI
from simulate_support_resistance import simulate_strategy
import pandas as pd
import datetime

# ========== 1. 初始參數 ==========
stock_ids = ["2330", "8222", "1736"]
today = datetime.datetime.now().strftime("%Y%m%d")
support_resistance_map = {
    "2330": (598, 602),
    "8222": (125, 128),
    "1736": (78, 82),
}

# ========== 2. 登入 ==========
api = SKAPI()
api.login("R124457999", "123jacky0")

# ========== 3. 抓取 + 模擬每一支 ==========
for stock_id in stock_ids:
    if stock_id not in support_resistance_map:
        print(f"⚠️ 缺少 {stock_id} 的支撐與壓力設定，略過")
        continue

    s, r = support_resistance_map[stock_id]
    tick_list = api.get_ticks(stock_id, today)

    if not tick_list:
        print(f"❌ {stock_id} 無法取得 Tick 資料，略過")
        continue

    df = pd.DataFrame(tick_list)
    df.columns = ['time', 'price', 'volume']

    trades = simulate_strategy(df, s, r)

    print(f"📈 {stock_id} 模擬完成，共 {len(trades)} 筆交易")
    for t in trades:
        print(t)
    if not trades:
        print("⚠️ 無交易結果")
