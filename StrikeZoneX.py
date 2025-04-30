from sk_api_strict import SKAPI
from simulate_support_resistance import simulate_strategy
import pandas as pd

# === 登入與資料取得 ===
api = SKAPI()
api.login("R124457999", "123jacky0")
tick_list = api.get_ticks("2330", "20250415")
print(f"✅ 成功取得 Tick 筆數：{len(tick_list)}")
if not tick_list:
    print("❌ Tick 資料為空，請確認代碼與日期")
    exit()

print(tick_list[:5])  # 顯示前五筆確認


# === 資料轉為 DataFrame 並格式標準化 ===
import pandas as pd
from simulate_support_resistance import simulate_strategy

tick_df = pd.DataFrame(tick_list)
tick_df.columns = ['time', 'price', 'volume']  # 對應中文：時間、價格、單量

# === 模擬條件 ===
support = 598
resistance = 602

# === 執行模擬 ===
trades = simulate_strategy(tick_df, support, resistance)

# === 輸出模擬結果 ===
for t in trades:
    print(t)

if not trades:
    print("⚠️ 本次模擬無交易發生")
