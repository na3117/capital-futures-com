import win32com.client

try:
    skcenter = win32com.client.Dispatch("SKCOMLib.SKCenterLib")
    print("✅ 成功建立 SKCenterLib，COM 註冊正常！")
except Exception as e:
    print(f"❌ 失敗：{e}")
