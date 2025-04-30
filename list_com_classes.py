import winreg

def list_com_classes():
    print("📦 掃描本機已註冊的 COM 類別（32-bit WOW6432Node）...")
    key_path = r"Software\WOW6432Node\Classes"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as root:
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(root, i)
                    if subkey.lower().startswith("sk") or "capital" in subkey.lower():
                        print("🔎", subkey)
                    i += 1
                except OSError:
                    break
    except Exception as e:
        print(f"⚠️ 無法打開登錄檔：{e}")

list_com_classes()
