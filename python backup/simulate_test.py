import pandas as pd
from simulate_support_resistance import simulate_strategy

# 匯入 Tick CSV（請確認檔案名稱與路徑正確）
tick_df = pd.read_csv("C:/Users/Le0/Desktop/api/tick_2330_20240415.csv")

# 確保欄位名稱正確（必要時強制改名）
tick_df.columns = ['time', 'price', 'volume']

# 呼叫模擬策略函式
support = 598
resistance = 602
trades = simulate_strategy(tick_df, support, resistance)

# 印出交易結果
for trade in trades:
    print(trade)
