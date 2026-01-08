import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager#讓chromedriver自動下載
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures



def create_webdriver(path):
    driver_option = webdriver.ChromeOptions()
    driver_option.add_argument("--incognito")
    # 如果不想看到視窗一直跳出來，可以取消下面這行的註解開啟無頭模式
    # driver_option.add_argument("--headless") 
    service = Service(executable_path=path)
    return webdriver.Chrome(service=service, options=driver_option)

def scrape_youtube_detail(name, url, driver_path):
    #傳入 driver_path
    browser = create_webdriver(driver_path)
    try:
        browser.get(url)
        # 1. 建立等待物件 (最多等 10 秒)
        wait = WebDriverWait(browser, 10)

        # 2. 根據圖片定位：在 #info 標籤下的 span
        # 使用 CSS Selector 定位 "#info span"
        try:
            #使用了 wait：程式會變得很聰明，它會每隔 0.5 秒去「探頭」看一下資料出來了沒
            # ，直到抓到為止（或是超過你設定的 10 秒）
            #EC (Expected Conditions)：這是我們預期的條件。
            #presence_of_element_located：意思只要這個元素的「程式碼」出現在網頁背後的 HTML 樹狀結構中，就算成功
            views_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#info span")))
            views_text = views_element.text # 這裡會拿到 "1.5M views"
        except:
            views_text = "N/A" # 如果抓不到則顯示 N/A

        # 回傳包含「名稱、網址、標題」的字典
        data = {
            "title": name, 
            "URL": url, 
            "views": views_text
        }
    except Exception as e:
        data = {"title": name, "URL": url, "Error": str(e)}
    finally:
        browser.quit()
    return data
#多工處理一定要寫這一段，作為防火牆，避免重複迴圈
if __name__ == "__main__":
    # --- 預備階段：先下載驅動程式 ---
    stable_driver_path = ChromeDriverManager().install()

# --- 第一階段：獲取基本清單 ---
    main_browser = create_webdriver(stable_driver_path)
    main_browser.get("https://www.youtube.com/@theMITmonk/videos")
    
    # 等待影片清單加載
    WebDriverWait(main_browser, 10).until(EC.presence_of_element_located((By.ID, "video-title")))

    # 定位影片區塊
    projects = main_browser.find_elements(By.XPATH, "//h3[@class='style-scope ytd-rich-grid-media']")

    # 我們將資料存成 (name, url) 的列表，方便後面並行處理
    tasks = []
    for proj in projects:
        try:
            proj_title = proj.find_element(By.XPATH, ".//a").get_attribute('title')
            proj_url = proj.find_element(By.XPATH, ".//a").get_attribute('href')
            tasks.append((proj_title, proj_url))
        except:
            continue
    main_browser.quit()
    print(f"成功取得 {len(tasks)} 個youtube網站，準備並行抓取細節...")

    # --- 第二階段：並行抓取詳細資訊 ---
    final_results = [] # 用來存儲所有子進程回傳的字典
    with ProcessPoolExecutor(max_workers=2) as executor:

        # 請改為這樣，把路徑也傳進去
        future_to_info = {executor.submit(scrape_youtube_detail, n, u, stable_driver_path): n for n, u in tasks}

        for future in concurrent.futures.as_completed(future_to_info):
            res = future.result()
            final_results.append(res)
            print(f"完成: {res.get('title')}")

    # --- 第三階段：整合並儲存資料 ---
    # 修訂：直接將字典列表轉換成 DataFrame
    df = pd.DataFrame(final_results)
    
    # 調整欄位順序（選用）
    df = df[["title", "URL", "views"]]
    
    # 儲存為 CSV
    df.to_csv('multi_youtube_complete_list.csv', index=False, encoding='utf-8-sig')
    print("\n[完成] 完整資料已儲存至 multi_youtubes_complete_list.csv")