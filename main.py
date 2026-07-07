import os
import requests
import json
import csv

# 改用台銀官方每日當天最新牌告匯率 CSV 檔（盤後、非營業時間依然有數據）
url = "https://rate.bot.com.tw/xrt/flcsv/0/day"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

print("開始向台灣銀行下載每日匯率 CSV 資料...")

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'utf-8'
    
    print(f"台銀連線狀態碼: {response.status_code}")
    
    # 讀取 CSV 內容
    lines = response.text.splitlines()
    reader = csv.reader(lines)
    
    currency_list = ["USD", "JPY", "EUR", "CNY", "KRW", "GBP", "AUD"]
    results = []
    
    # 台銀 CSV 格式：
    # 欄位 0: 幣別, 欄位 2: 本行即期買入, 欄位 12: 本行即期賣出
    for row in reader:
        if not row or len(row) < 13:
            continue
            
        currency = row[0].strip().upper()
        if currency in currency_list:
            try:
                # 去除可能包含的空格
                spot_buy_str = row[2].strip()
                spot_sell_str = row[12].strip()
                
                # 轉換為數字，若為 '-' 或空值則設為 0.0
                spot_buy = float(spot_buy_str) if spot_buy_str and spot_buy_str != '-' else 0.0
                spot_sell = float(spot_sell_str) if spot_sell_str and spot_sell_str != '-' else 0.0
                
                # 計算即期中價
                if spot_buy > 0 and spot_sell > 0:
                    spot_mid = round((spot_buy + spot_sell) / 2, 4)
                else:
                    spot_mid = round(max(spot_buy, spot_sell), 4)
                    
                results.append({
                    "code": currency,
                    "spotBuy": spot_buy,
                    "spotSell": spot_sell,
                    "spotMid": spot_mid
                })
            except Exception as row_err:
                print(f"解析幣別 {currency} 欄位失敗: {str(row_err)}")

    print(f"成功解析出符合的幣別共 {len(results)} 種: {[r['code'] for r in results]}")
                
    # 將整理好的台銀官方數據送往 Google 試算表
    web_app_url = os.environ.get("GOOGLE_WEBAPP_URL")
    if web_app_url and results:
        payload = {"rates": results}
        res = requests.post(web_app_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
        print("試算表同步回傳結果:", res.text)
    elif not web_app_url:
        print("❌ 錯誤：未在 GitHub Settings 中偵測到 GOOGLE_WEBAPP_URL 環境變數")
    else:
        print("⚠️ 警告：解析出來的匯率清單為空，未發送至 Google 試算表")
        
except Exception as e:
    print("❌ 執行過程中發生致命錯誤！")
    print("錯誤詳細訊息:", str(e))
    raise e
