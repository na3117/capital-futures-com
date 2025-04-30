import pandas as pd
from datetime import datetime, timedelta

def simulate_strategy(tick_df, support, resistance):
    """
    模組 B：模擬支撐壓力策略（含觸價後延遲成交判定）
    """
    trades = []
    position = None
    entry_time, entry_price, entry_reason = None, None, None
    delay_seconds = 3  # N 秒內需成交
    price_range = 0.005

    # 計算進場範圍
    support_min = support * (1 - price_range)
    support_max = support * (1 + price_range)
    resistance_min = resistance * (1 - price_range)
    resistance_max = resistance * (1 + price_range)

    tick_df['time'] = pd.to_datetime(tick_df['time'])

    i = 0
    while i < len(tick_df) - 1:
        row1 = tick_df.iloc[i]
        row2 = tick_df.iloc[i + 1]
        t1, p1 = row1['time'], row1['price']
        t2, p2 = row2['time'], row2['price']

        # 若尚未持倉，檢查進場條件
        if position is None:
            # 支撐進場條件：兩筆都落在支撐區間
            if support_min <= p1 <= support_max and support_min <= p2 <= support_max:
                confirm_until = t2 + timedelta(seconds=delay_seconds)
                j = i + 2
                while j < len(tick_df) and tick_df.iloc[j]['time'] <= confirm_until:
                    if support_min <= tick_df.iloc[j]['price'] <= support_max:
                        # 模擬成交，使用第2筆的價格進場
                        position = 'long'
                        entry_time = t2
                        entry_price = p2
                        entry_reason = '支撐觸價進場'
                        break
                    j += 1

            # 壓力進場條件：兩筆都落在壓力區間
            elif resistance_min <= p1 <= resistance_max and resistance_min <= p2 <= resistance_max:
                confirm_until = t2 + timedelta(seconds=delay_seconds)
                j = i + 2
                while j < len(tick_df) and tick_df.iloc[j]['time'] <= confirm_until:
                    if resistance_min <= tick_df.iloc[j]['price'] <= resistance_max:
                        # 模擬成交，使用第2筆的價格進場
                        position = 'short'
                        entry_time = t2
                        entry_price = p2
                        entry_reason = '壓力觸價進場'
                        break
                    j += 1

        # 已持倉，檢查停利停損或時間平倉
        elif position:
            current_time = row2['time']
            current_price = row2['price']

            stop_loss_price = entry_price * (1 - 0.01) if position == 'long' else entry_price * (1 + 0.01)
            take_profit_price = entry_price * (1 + 0.02) if position == 'long' else entry_price * (1 - 0.02)

            exit_reason = None

            # 停損判斷
            if (position == 'long' and current_price <= stop_loss_price) or \
               (position == 'short' and current_price >= stop_loss_price):
                exit_reason = '停損'

            # 停利判斷
            elif (position == 'long' and current_price >= take_profit_price) or \
                 (position == 'short' and current_price <= take_profit_price):
                exit_reason = '停利'

            # 時間強制平倉
            elif current_time.hour == 13 and current_time.minute >= 0:
                exit_reason = '13:00 強制平倉'

            if exit_reason:
                profit = (current_price - entry_price) * 1000 if position == 'long' else (entry_price - current_price) * 1000
                hold_time = (current_time - entry_time).total_seconds()
                trades.append({
                    '進場時間': entry_time.strftime("%H:%M:%S"),
                    '進場價格': round(entry_price, 2),
                    '方向': '多單' if position == 'long' else '空單',
                    '進場理由': entry_reason,
                    '出場時間': current_time.strftime("%H:%M:%S"),
                    '出場價格': round(current_price, 2),
                    '出場理由': exit_reason,
                    '損益': round(profit, 0),
                    '持倉時間': f"{int(hold_time // 60)}分{int(hold_time % 60)}秒"
                })
                position = None
                entry_time, entry_price, entry_reason = None, None, None

        i += 1

    return trades
