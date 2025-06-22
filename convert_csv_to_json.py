import os
import pandas as pd
import json
import re

input_dir = "capstone_app/static/data_all/재무재표"
output_dir = "capstone_app/static/data_all/json_output"

os.makedirs(output_dir, exist_ok=True)

def clean_class_column(val):
    if pd.isna(val):
        return ""
    if isinstance(val, (int, float)):
        return ""
    return str(val)

def is_year_column(col_name):
    # 컬럼명이 숫자(연도)로 시작하면 True (예: '2022', '22', '2022년' 등)
    return bool(re.match(r"^\d{2,4}", col_name))

def process_csv(csv_path):
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', header=1)  # 필요시 header 조정

        base_cols = ["concept_id", "label_ko", "label_en"]
        class_cols = ["class0", "class1", "class2", "class3"]

        # base_cols 체크
        missing = [col for col in base_cols if col not in df.columns]
        if missing:
            print(f"필요한 컬럼 누락: {csv_path} (건너뜀)  누락컬럼: {missing}")
            return

        # class 컬럼 보완
        for col in class_cols:
            if col not in df.columns:
                df[col] = ""
            else:
                df[col] = df[col].apply(clean_class_column)

        # 숫자로 시작하는 모든 컬럼(연도 컬럼) 선택
        year_cols = [col for col in df.columns if is_year_column(col)]

        # 연도 컬럼 결측치 빈문자열 처리
        for col in year_cols:
            df[col] = df[col].apply(lambda x: "" if pd.isna(x) else x)

        # JSON 출력 컬럼
        all_cols = base_cols + class_cols + year_cols

        for col in all_cols:
            if col not in df.columns:
                df[col] = ""

        df_output = df[all_cols]

        json_filename = os.path.splitext(os.path.basename(csv_path))[0] + ".json"
        json_path = os.path.join(output_dir, json_filename)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(df_output.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

        print(f"성공적으로 처리됨: {csv_path} -> {json_path}")

    except Exception as e:
        print(f"처리 중 오류 발생: {csv_path} -> {e}")

def run_all():
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".csv"):
                csv_path = os.path.join(root, file)
                process_csv(csv_path)

if __name__ == "__main__":
    run_all()
