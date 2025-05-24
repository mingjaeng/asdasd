import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

CHROMEDRIVER_PATH = "C:/Users/yt/Downloads/chromedriver.exe"

# 크롬 드라이버 설정
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 필요 없으면 주석 처리
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# 필요한 항목만 추출하는 함수
def get_selected_balance_data(stock_code):
    driver = get_driver()

    url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}&target=finsum_more"
    driver.get(url)
    time.sleep(2)

    try:
        driver.switch_to.frame("coinfo_cp")
    except Exception as e:
        print("iframe 진입 실패:", e)
        driver.quit()
        return None

    # 필요한 항목 리스트
    needed_items = [
        "자산총계", "부채총계", "자본총계",
        "유동자산", "유동부채", "발행주식수", "주가"
    ]

    data = {}

    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            try:
                title = row.find_element(By.TAG_NAME, "th").text.strip()
                if title in needed_items:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    values = [cell.text.strip().replace(',', '') for cell in cells]
                    data[title] = values
            except Exception:
                continue
    except Exception as e:
        print("데이터 추출 중 오류:", e)
        driver.quit()
        return None

    driver.quit()
    return data

# 년도별로 JSON 저장
def save_yearly_data(company_name, data, years):
    yearly_data = {year: {} for year in years}

    for key, values in data.items():
        for i, year in enumerate(years):
            if i < len(values):
                yearly_data[year][key] = values[i]

    for year, ydata in yearly_data.items():
        filename = f"selected_balance_data_{company_name}_{year}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(ydata, f, ensure_ascii=False, indent=4)
        print(f"{company_name} - {year} 재무상태표 일부 데이터 저장 완료: {filename}")

# 실행부
def main():
    companies = {
        "AP위성": "052860",
        "데브시스터즈": "194480",
        "한선엔지니어링": "060560",
        "고려제강": "002240",
        "메카로": "089010",
        "미래에셋증권": "006800",
        "폴라리스AI": "230360",
        "로보로보": "100660",
        "셀바스헬스케어": "208370",
        "성우하이텍": "015750",
    }

    years = ['2024', '2023', '2022']

    for name, code in companies.items():
        print(f"{name}({code}) 재무항목 크롤링 중...")
        data = get_selected_balance_data(code)
        if data:
            save_yearly_data(name, data, years)
        else:
            print(f"{name} 데이터 수집 실패.")
        time.sleep(1)

if __name__ == "__main__":
    main()