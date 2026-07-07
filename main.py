import os
import requests
import json
import xml.etree.ElementTree as ET

# 1. 直接向台銀下載官方 XML (GitHub 伺服器不會被封鎖)
url = "https://rate.bot.com.tw/xrt/xml/day"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(url, headers=headers)
response.encoding = 'utf-8'

# 2. 解析台銀公告的即期匯率並計算中價
currency_list = ["USD", "JPY", "EUR", "CNY", "KRW", "GBP", "AUD"]
results = []

try:
    root = ET.fromstring(response.text)
    for entry in root.findall('Coordinate'):
        currency = entry.find('Currency').text.strip() if entry.find('Currency') is not None else ""
        if currency in currency_list:
            spot_buy = float(entry.find('SpotBuy').text) if entry.find('SpotBuy') is not None else 0.0
            spot_sell = float(entry.find('SpotSell').text) if entry.find('SpotSell') is not None else 0.0
            
            # 計算台銀即期中價
            spot_mid = round((spot_buy + spot_sell) / 2, 4) if (spot_buy and spot_sell) else 0.0
            
            results.append({
                "code": currency,
                "spotBuy": spot_buy,
                "spotSell": spot_sell,
                "spotMid": spot_mid
            })
            
    # 3. 將資料發送到你的 Google 試算表接收通道
    web_app_url = os.environ.get("GOOGLE_WEBAPP_URL")
    if web_app_url and results:
        payload = {"rates": results}
        res = requests.post(web_app_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        print("試算表同步結果:", res.text)
        
except Exception as e:
    print("解析失敗:", str(e))
