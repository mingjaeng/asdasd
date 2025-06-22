import os
import json
import time

from django.conf import settings
from django.http import JsonResponse, Http404
from django.shortcuts import render
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

COMPANY_CODES = {
    "데브시스터즈": "194480",
    "한선엔지니어링": "060560",
    "고려제강": "002240",
    "메카로": "089010",
    "셀바스헬스케어": "208370",
    "성우하이텍": "015750",
}

def home_redirect(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'index.html')

def get_stock_code(company_name):
    search_url = f"https://finance.naver.com/search/searchList.naver?query={company_name}"
    res = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')
    a_tag = soup.select_one('ul.searchList li a')
    if a_tag and 'code=' in a_tag.get('href'):
        return a_tag['href'].split('code=')[-1]
    return None

def get_stock_info(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')
    try:
        price = soup.select_one('p.no_today span.blind').text
        change = soup.select_one('p.no_exday span.blind').text
        rate = soup.select('p.no_exday span')[-1].text.strip()
        return price, change, rate
    except:
        return None, None, None

def get_economic_indicators():
    indicators = {}
    try:
        res = requests.get('https://finance.naver.com/marketindex/', headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        indicators['USD_KRW'] = soup.select_one('div.market1 span.value').text.strip()
    except:
        indicators['USD_KRW'] = None

    try:
        res2 = requests.get('https://finance.naver.com/sise/', headers={'User-Agent': 'Mozilla/5.0'})
        soup2 = BeautifulSoup(res2.text, 'html.parser')
        indicators['KOSPI'] = soup2.select_one('#KOSPI_now').text.strip()
        indicators['KOSDAQ'] = soup2.select_one('#KOSDAQ_now').text.strip()
    except:
        indicators['KOSPI'] = indicators['KOSDAQ'] = None

    return indicators

def stock_info_api(request):
    company_name = request.GET.get('name')
    if not company_name:
        return JsonResponse({'error': '기업명을 입력하세요'}, status=400)

    code = get_stock_code(company_name)
    if not code:
        return JsonResponse({'error': '종목코드를 찾을 수 없습니다'}, status=404)

    price, change, rate = get_stock_info(code)
    econ = get_economic_indicators()

    result = {
        '기업명': company_name,
        '종목코드': code,
        '현재가': price,
        '전일비': change,
        '등락률': rate,
        'USD_KRW': econ['USD_KRW'],
        'KOSPI': econ['KOSPI'],
        'KOSDAQ': econ['KOSDAQ'],
    }
    return JsonResponse(result)

def crawl_company_info(code):
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = f"https://navercomp.wisereport.co.kr/v2/company/c1020001.aspx?cmp_cd={code}"
    driver.get(url)
    time.sleep(2)

    try:
        address = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[1]/td').text.strip()
        homepage = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[2]/td[1]/a').get_attribute("href").strip()
        ceo = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[3]/td[2]').text.strip()
        establishment_date = driver.find_element(By.XPATH, '//*[@id="cTB201"]/tbody/tr[3]/td[1]').text.strip()

        return {
            "본사주소": address,
            "홈페이지": homepage,
            "대표이사": ceo,
            "설립일": establishment_date
        }
    except Exception as e:
        print("[크롤링 오류]", e)
        return {}
    finally:
        driver.quit()

def calculate_indicators(financial_data, year):
    def find_value(items, name):
        for item in items:
            if item.get('account_nm') == name:
                try:
                    return float(str(item.get('thstrm_amount', '0')).replace(',', ''))
                except ValueError:
                    return 0
        return 0

    income_statement = financial_data.get(f'포괄손익계산서_{year}', [])
    balance_sheet = financial_data.get(f'재무상태표_{year}', [])

    당기순이익 = find_value(income_statement, '당기순이익(손실)')
    영업이익 = find_value(income_statement, '영업이익(손실)')
    매출액 = find_value(income_statement, '매출액')
    자본총계 = find_value(balance_sheet, '자본총계')
    자산총계 = find_value(balance_sheet, '자산총계')
    부채총계 = find_value(balance_sheet, '부채총계')
    유동자산 = find_value(balance_sheet, '유동자산')
    유동부채 = find_value(balance_sheet, '유동부채')
    발행주식수 = find_value(balance_sheet, '자본금') / 5000 if find_value(balance_sheet, '자본금') else 0

    indicators = {}
    try:
        indicators['ROE'] = round(당기순이익 / 자본총계 * 100, 2) if 자본총계 else None
        indicators['ROA'] = round(당기순이익 / 자산총계 * 100, 2) if 자산총계 else None
        indicators['영업이익률'] = round(영업이익 / 매출액 * 100, 2) if 매출액 else None
        indicators['순이익률'] = round(당기순이익 / 매출액 * 100, 2) if 매출액 else None
        indicators['부채비율'] = round(부채총계 / 자본총계 * 100, 2) if 자본총계 else None
        indicators['유동비율'] = round(유동자산 / 유동부채 * 100, 2) if 유동부채 else None
        indicators['EPS'] = round(당기순이익 / 발행주식수, 2) if 발행주식수 else None
        indicators['BPS'] = round(자본총계 / 발행주식수, 2) if 발행주식수 else None
        indicators['PER'] = None
        indicators['PBR'] = None
    except Exception as e:
        print(f"[지표 계산 오류] {e}")
    return indicators

def company_detail(request, company_name):
    if company_name not in COMPANY_CODES:
        raise Http404("존재하지 않는 기업입니다.")

    base_path = os.path.join(settings.BASE_DIR, 'capstone_app', 'static', 'data_all')
    years = ['2024', '2023', '2022']  # 내림차순으로 수정

    financial_data = {}

    for year in years:
        for sheet in ['재무상태표', '포괄손익계산서', '현금흐름표']:
            filename = f"{COMPANY_CODES[company_name]}_{year}_{sheet}.json"
            filepath = os.path.join(base_path, filename)
            try:
                with open(filepath, encoding='utf-8') as f:
                    financial_data[f'{sheet}_{year}'] = json.load(f)
            except FileNotFoundError:
                financial_data[f'{sheet}_{year}'] = []

    economic_path = os.path.join(base_path, 'economic_index.json')
    try:
        with open(economic_path, encoding='utf-8') as f:
            original_econ = json.load(f)
            economic_index = {
                "USD_KRW": original_econ.get("USD/KRW"),
                "KOSPI": original_econ.get("KOSPI"),
                "KOSDAQ": original_econ.get("KOSDAQ"),
            }
    except FileNotFoundError:
        economic_index = {}

    company_info = crawl_company_info(COMPANY_CODES[company_name])
    indicators_by_year = {
        year: calculate_indicators(financial_data, year)
        for year in years
    }

    report_filename = f"{company_name}_report.html"
    report_url = f"/static/output/{report_filename}"

    return render(request, "company_detail.html", {
        'company_name': company_name,
        'company_info': company_info,
        'financial_data': financial_data,
        'economic_index': economic_index,
        'indicators_by_year': indicators_by_year,
        'report_url': report_url,
        'years': years,
    })
