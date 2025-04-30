import comtypes.client
from comtypes.gen import SKCOMLib

# 建立中心物件與回報物件
sk_center = comtypes.client.CreateObject(SKCOMLib.SKCenterLib)
sk_reply = comtypes.client.CreateObject(SKCOMLib.SKReplyLib)

# 綁定回報事件
def on_reply_message(this, user_id, message, ntype):
    print(f"[公告回報] user_id={user_id}, message={message}, ntype={ntype}")

reply_event = comtypes.client.GetEvents(sk_reply, on_reply_message)

# 暖機
try:
    sk_center.SKCenterLib_GetUserAccount()
except:
    pass  # 暖機失敗可忽略

# 等待公告（但沒有收到任何回報）
# 此時準備進行 SKCenterLib_Login
ret = sk_center.SKCenterLib_Login("帳號", "密碼")

print(f"Login回傳結果：{ret}")
