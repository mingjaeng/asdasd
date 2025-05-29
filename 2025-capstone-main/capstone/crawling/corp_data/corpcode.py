import requests
import zipfile
import io

api_key = '3f137e287df400d204dfc01605363fbe7b310bcb'
url = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}'

# 요청 보내기
response = requests.get(url)

if response.status_code == 200:
    # 응답 내용을 메모리 내 ZIP 파일로 처리
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall('capstone/corp_data')  # 원하는 경로에 압축 풀기
    print('CORPCODE.xml 다운로드 및 압축 해제 완료!')
else:
    print(f'오류 발생: {response.status_code}')