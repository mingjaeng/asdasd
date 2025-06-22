import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 크롬드라이버 경로 (직접 경로 설정)
chrome_driver_path = r'C:\chromedriver\chromedriver.exe'

# 크롬 옵션 설정
options = Options()
options.add_argument('--headless')  # 창 없이 실행
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# 크롬 드라이버 실행
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# 기업명과 종목코드
companies = {
    "고려제강": "001140",
    "데브시스터즈": "194480",
    "메카로": "241770",
    "성우하이텍": "015750",
    "셀바스헬스케어": "208370"
}

# 저장 경로
output_dir = r"C:\Users\user\Desktop\website-main\capstone_app\static\data_all\investment"
os.makedirs(output_dir, exist_ok=True)

# 크롤링 시작
for company, code in companies.items():
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    driver.get(url)
    time.sleep(2)

    data = {
        "수익성지표": {},
        "안정성지표": {},
        "성장성지표": {},
        "투자/가치평가지표": {}
    }

    try:
        table = driver.find_element(By.XPATH, '//*[@id="content"]/div[2]/div[2]/div[2]/div[3]/table')
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        for row in rows:
            try:
                title = row.find_element(By.TAG_NAME, "th").text.strip()
                values = row.find_elements(By.TAG_NAME, "td")
                if len(values) >= 3:
                    val_2024 = values[0].text.strip()
                    val_2023 = values[1].text.strip()
                    val_2022 = values[2].text.strip()

                    # 지표 종류 자동 분류
                    if "ROE" in title or "ROA" in title or "영업이익률" in title:
                        data["수익성지표"][title] = {
                            "2024": val_2024,
                            "2023": val_2023,
                            "2022": val_2022,
                        }
                    elif "부채비율" in title or "유동비율" in title:
                        data["안정성지표"][title] = {
                            "2024": val_2024,
                            "2023": val_2023,
                            "2022": val_2022,
                        }
                    elif "성장" in title or "매출" in title:
                        data["성장성지표"][title] = {
                            "2024": val_2024,
                            "2023": val_2023,
                            "2022": val_2022,
                        }
                    else:
                        data["투자/가치평가지표"][title] = {
                            "2024": val_2024,
                            "2023": val_2023,
                            "2022": val_2022,
                        }
            except Exception:
                continue

    except Exception as e:
        print(f"{company}에서 오류 발생:", e)

    # 저장
    filepath = os.path.join(output_dir, f"{company}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{company} 저장 완료")

driver.quit()
