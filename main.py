import os
import requests
import json
import xml.etree.ElementTree as ET

url = "https://rate.bot.com.tw/xrt/xml/day"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
response = requests.get(url, headers=headers)
response.encoding = 'utf-8'

currency_list = ["USD", "JPY", "EUR", "CNY", "KRW", "GBP", "AUD"]
results = []

try:
    # 使用柔軟的解析方式，同時支援 Coordinate 或其底下的任何子節點
    root = ET.fromstring(response.text)
    
    # 遍歷所有包含 Currency 的節點
    for entry in root.date_elements if hasattr(root, 'date_elements') else root.iter():
        currency_node = entry.find('Currency') or entry.find('currency')
        if currency_node is not None and currency_node.text:
            currency = currency_node.text.strip().toUpperCase() if hasattr(currency_node.text, 'toUpperCase') else currency_node.text.strip()
            
            if currency in currency_list:
                # 相容大小寫與底線格式
                sb_node = entry.find('SpotBuy') or entry.find('spot_buy') or entry.find('spotbuy')
                ss_node = entry.find('SpotSell') or entry.find('spot_sell') or entry.find('spotsell')
                
                spot_buy = float(sb_node.text) if sb_node is not None and sb_node.text else 0.0
                spot_sell = float(ss_node.text) if ss_node is not None and ss_node.text else 0.0
                spot_mid = round((spot_buy + spot_sell) / 2, 4) if (spot_buy and spot_sell) else round(spot_buy, 4)
                
                results.append({
                    "code": currency,
                    "spotBuy": spot_buy,
                    "spotSell": spot_sell,
                    "spotMid": spot_mid
                })

    # 將結果送出
    web_app_url = os.environ.get("GOOGLE_WEBAPP_URL")
    if web_app_url:
        payload = {"rates": results}
        res = requests.post(web_app_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        print("試算表同步結果:", res.text)
        
except Exception as e:
    print("解析失敗:", str(e))
        payload = {"rates": results}
        res = requests.post(web_app_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        print("試算表同步結果:", res.text)
        
except Exception as e:
    print("解析失敗:", str(e))
