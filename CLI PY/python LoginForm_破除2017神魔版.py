from comtypes.client import GetModule, CreateObject, GetEvents
import os
import time

# 匯入 SKCOM.dll COM 模組（相對路徑或絕對路徑皆可）
dll_path = os.path.abspath("SKCOM.dll")
GetModule(dll_path)
import comtypes.gen.SKCOMLib as sk

# ✅ 建立 SKReplyLib 並綁定公告事件（這是 2017 的解法核心）
class SKReplyEvent:
    def OnReplyMessage(self, uid, msg):
        print(f"[公告] {uid}: {msg}")
        return 0

print("[1] 建立 SKReplyLib...")
m_pSKReply = CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
reply_event = SKReplyEvent()
global_reply_handler = GetEvents(m_pSKReply, reply_event)
print("[1] SKReplyLib 已建立並綁定公告事件 ✅")

# ✅ 建立 SKCenterLib 並啟動 Debug 記錄資料夾
print("[2] 建立 SKCenterLib...")
m_pSKCenter = CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
log_dir = os.path.abspath("./debuglog")
os.makedirs(log_dir, exist_ok=True)
m_pSKCenter.SKCenterLib_Debug(log_dir)
print(f"[2] Debug Log 已設置於 {log_dir} ✅")

# ✅ 執行登入
print("[3] 嘗試登入中...")
account = input("R124457999：")
password = input("123jacky0：")
ret = m_pSKCenter.SKCenterLib_Login(account, password)

if ret == 0:
    print("[3] ✅ 登入成功！")
else:
    print(f"[3] ❌ 登入失敗，錯誤代碼：{ret}")

# 等待 3 秒確保公告事件能接收到
print("[4] 等待公告事件（3 秒）...")
time.sleep(3)
print("[結束] 測試完成 ✅")
