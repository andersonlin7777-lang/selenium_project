from selenium import webdriver # allow launching browser
from selenium.webdriver.chrome.service import Service # 1. 新增這一行
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By # allow search with parameters
from webdriver_manager.chrome import ChromeDriverManager#讓chrome自動下載
from selenium.webdriver.support.ui import WebDriverWait # allow waiting for page to load
from selenium.webdriver.support import expected_conditions as EC # determine whether the web page has loaded
from selenium.common.exceptions import TimeoutException # handling timeout situation
import pandas as pd

#有了webdriver_manager就不需要指定路徑，而會自動下載
#chromedriver_path = 'C:/Users/User/Desktop/learn/selenium_project/chromedriver/chromedriver.exe' # Change this to your own chromedriver path!

def create_webdriver():
    driver_option = webdriver.ChromeOptions()
    driver_option.add_argument("--incognito")
    driver_option.add_experimental_option("detach", True)#讓瀏覽器在腳本結束後保持開啟

    #service = Service(executable_path=chromedriver_path)#建立Service 物件
    #使用 service 和 options 參數啟動瀏覽器
    #修改這裡：讓 Service 自動去下載並獲取路徑
    #ChromeDriverManager().install() 會回傳下載好的執行檔路徑
    service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(service=service, options=driver_option)

# Open the website
browser = create_webdriver()
browser.get("https://github.com/collections/machine-learning")

# Extract all projects
projects = browser.find_elements(By.XPATH, "//h1[@class='h3 lh-condensed']")

# Extract information for each project
project_list = {}
for proj in projects:
    try:
        proj_name = proj.text.strip() #取得專案名稱 (h1 標籤內的文字)
        #取得超連結 (注意 XPATH 開頭的角括號與點號)
        # 使用 .//a 表示「從當前這個 proj 元素底下」開始找 a 標籤
        proj_url = proj.find_element(By.XPATH, ".//a").get_attribute('href')
        project_list[proj_name] = proj_url
    except Exception as e:#Exception 是「種類」，e 是「細節」
        print(f"擷取個別專案時發生錯誤: {e}")

# Close connection
browser.quit()


# Extracting data
#project_df = pd.DataFrame.from_dict(project_list, orient = 'index')
#將字典轉換成 DataFrame
project_df = pd.DataFrame.from_dict(project_list, orient='index', columns=['URL'])
#重新命名索引 (讓表格更好看)
project_df.index.name = 'Project Name'

# Export project dataframe to CSV
project_df.to_csv('project_list.csv')