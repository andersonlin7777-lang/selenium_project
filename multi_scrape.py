import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures

chromedriver_path = r'C:/Users/User/Desktop/learn/selenium_project/chromedriver/chromedriver.exe'

def create_webdriver():
    driver_option = webdriver.ChromeOptions()
    driver_option.add_argument("--incognito")
    return webdriver.Chrome(service=Service(executable_path=chromedriver_path), options=driver_option)

# 修訂：讓函式同時接收 name 和 url
def scrape_url_detail(name, url): # <--- 這裡增加了 name 參數
    """子進程任務：進入專案頁面並回傳完整資料"""
    browser = create_webdriver()
    try:
        browser.get(url)
        page_title = browser.title
        # 回傳包含「名稱、網址、標題」的字典
        data = {
            "Project Name": name, 
            "URL": url, 
            "Page Title": page_title
        }
    except Exception as e:
        data = {"Project Name": name, "URL": url, "Error": str(e)}
    finally:
        browser.quit()
    return data

if __name__ == "__main__":
    # --- 第一階段：獲取基本清單 ---
    main_browser = create_webdriver()
    main_browser.get("https://github.com/andersonlin7777-lang?tab=repositories")
    
    # 根據你的新目標網址修正 XPath
    projects = main_browser.find_elements(By.XPATH, "//a[@itemprop='name codeRepository']")
    
    # 我們將資料存成 (name, url) 的列表，方便後面並行處理
    tasks = []
    for proj in projects:
        try:
            tasks.append((proj.text.strip(), proj.get_attribute('href')))
        except:
            continue
    main_browser.quit()
    print(f"成功取得 {len(tasks)} 個專案，準備並行抓取細節...")

    # --- 第二階段：並行抓取詳細資訊 ---
    final_results = [] # 用來存儲所有子進程回傳的字典
    with ProcessPoolExecutor(max_workers=2) as executor:
        # 修訂：提交任務時同時傳入名稱與網址
        #executor.submit() 並不會立刻回傳抓取結果（因為網頁還在跑）。
        #它回傳的是一個「承諾」或「憑據」，我們稱之為 Future（未來物件）
        future_to_info = {executor.submit(scrape_url_detail, n, u): n for n, u in tasks}
        #當某個「呼叫器」震動時（代表 as_completed(future_to_info) 偵測到任務完成了）
        #我們就能透過這個呼叫器，去字典裡查到這份餐點到底是什麼名字。
        for future in concurrent.futures.as_completed(future_to_info):
            res = future.result()
            final_results.append(res)
            print(f"完成: {res.get('Project Name')}")

    # --- 第三階段：整合並儲存資料 ---
    # 修訂：直接將字典列表轉換成 DataFrame
    df = pd.DataFrame(final_results)
    
    # 調整欄位順序（選用）
    df = df[["Project Name", "URL", "Page Title"]]
    
    # 儲存為 CSV
    df.to_csv('multi_project_complete_list.csv', index=False, encoding='utf-8-sig')
    print("\n[完成] 完整資料已儲存至 multi_project_complete_list.csv")