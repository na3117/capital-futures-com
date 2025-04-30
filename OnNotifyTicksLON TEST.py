from comtypes.client import GetModule
import os

# 對 SKCOM.dll 建立型別庫（會自動建立 gen.SKCOMLib）
dll_path = os.path.join(os.path.dirname(__file__), "SKCOM.dll")
GetModule(dll_path)

# 匯入封裝後的 COM 類別
import comtypes.gen.SKCOMLib as sk

# 印出 QuoteLib 所支援的所有事件（function）
print("⚙️ SKQuoteLib 所有事件：")
for attr in dir(sk.ISKQuoteLib):
    if attr.startswith("On"):
        print("🧩", attr)
