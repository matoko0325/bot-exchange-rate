import os
import requests
import json
import xml.etree.ElementTree as ET

url = "https://rate.bot.com.tw/xrt/xml/day"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

print("開始向台灣銀行下載 XML 資料...")

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'utf-8'
    
    print(f"台銀連線狀態碼: {response.status_code}")
    
    # 檢查是否拿到正確的 XML，而不是被防火牆擋下來的網頁 HTML
    if "<Coordinate>" not in response.text:
        print("⚠️ 警告：下載到的內容似乎不是正確的匯率 XML！")
        print("內容前 200 字元:", response.text[:200])
    
    root = ET.fromstring(response.text)
    
    currency_list = ["USD", "JPY", "EUR", "CNY", "KRW", "GBP", "AUD"]
    results = []
    
    # 尋找所有節點
    entries = root.findall('.//Coordinate')
    print(f"總共找到 {len(entries)} 個幣別資料節點")
    
    for entry in entries:
        cur_node = entry.find('Currency')
        if cur_node is not None and cur_node.text:
            currency = cur_node.text.strip().upper()
            
            if currency in currency_list:
                sb_node = entry.find('SpotBuy')
                ss_node = entry.find('SpotSell')
                
                # 安全轉換浮點數，防範空值
                spot_buy = 0.0
                spot_sell = 0.0
                try:
                    if sb_node is not None and sb_node.text and sb_node.text.strip():
                        spot_buy = float(sb_node.text.strip())
                    if ss_node is not None and ss_node.text and ss_node.text.strip():
                        spot_sell = float(ss_node.text.strip())
                except Exception as num_err:
                    print(f"數字轉換失敗 ({currency}): {str(num_err)}")
                
                # 計算中價
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

    print(f"成功解析出符合的幣別共 {len(results)} 種: { [r['code'] for r in results] }")
                
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
    print("❌ 終極捕捉：執行過程中發生致命錯誤！")
    print("錯誤詳細訊息:", str(e))
