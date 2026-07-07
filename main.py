import os
import requests
import json
import xml.etree.ElementTree as ET

url = "https://rate.bot.com.tw/xrt/xml/day"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

try:
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    
    # 解析台銀標準 XML 結構
    root = ET.fromstring(response.text)
    
    currency_list = ["USD", "JPY", "EUR", "CNY", "KRW", "GBP", "AUD"]
    results = []
    
    # 尋找 XML 中所有的 Coordinate 節點
    for entry in root.findall('.//Coordinate'):
        cur_node = entry.find('Currency')
        if cur_node is not None and cur_node.text:
            currency = cur_node.text.strip().upper()
            
            if currency in currency_list:
                sb_node = entry.find('SpotBuy')
                ss_node = entry.find('SpotSell')
                
                # 轉換為浮點數，若無資料則為 0.0
                spot_buy = float(sb_node.text) if (sb_node is not None and sb_node.text) else 0.0
                spot_sell = float(ss_node.text) if (ss_node is not None and ss_node.text) else 0.0
                
                # 計算即期中價 (買入與賣出皆大於 0 才計算，否則取大者)
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
                
    # 將整理好的台銀官方數據送往 Google 試算表
    web_app_url = os.environ.get("GOOGLE_WEBAPP_URL")
    if web_app_url:
        payload = {"rates": results}
        res = requests.post(web_app_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        print("試算表同步結果:", res.text)
    else:
        print("未偵測到 GOOGLE_WEBAPP_URL 環境變數")
        
except Exception as e:
    print("執行發生錯誤:", str(e))
    raise e
