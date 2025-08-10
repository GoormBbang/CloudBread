from flask import Flask, request, jsonify
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import io
import requests
import json
import os
import uuid
import re

load_dotenv()

app = Flask(__name__)

# Naver OCR API Gateway URL and Secret Key
# IMPORTANT: Set these as environment variables in your deployment environment
NAVER_OCR_APIGW_URL = os.getenv("NAVER_OCR_APIGW_URL")
NAVER_OCR_SECRET_KEY = os.getenv("NAVER_OCR_SECRET_KEY")

# 기존 Tesseract OCR 엔드포인트
@app.route('/ocr', methods=['POST'])
def perform_ocr():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            image = Image.open(io.BytesIO(file.read()))
            text = pytesseract.image_to_string(image, lang='kor+eng')
            return jsonify({"text": text}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Naver OCR API를 이용한 영양성분 분석 엔드포인트
@app.route('/ocr/nutrition', methods=['POST'])
def ocr_nutrition():
    if not NAVER_OCR_APIGW_URL or not NAVER_OCR_SECRET_KEY:
        return jsonify({"error": "OCR API environment variables are not set."} ), 500

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            image_bytes = file.read()
            
            headers = {
                "X-OCR-SECRET": NAVER_OCR_SECRET_KEY,
                "Content-Type": "application/json"
            }
            
            payload = {
                "version": "V2",
                "requestId": str(uuid.uuid4()),
                "timestamp": 0,
                "lang": "ko",
                "images": [
                    {
                        "format": file.mimetype.split('/')[-1],
                        "name": file.filename,
                        "data": image_bytes.decode('latin1') # base64 encoding in later step
                    }
                ]
            }

            # In a real implementation, you would do base64 encoding.
            # For now, we are sending it as latin1 decoded string.
            # This will likely fail, but it's a placeholder for the real implementation.
            import base64
            payload['images'][0]['data'] = base64.b64encode(image_bytes).decode('utf-8')


            response = requests.post(NAVER_OCR_APIGW_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            ocr_result = response.json()
            
            # OCR 결과에서 텍스트 추출
            full_text = ""
            for image in ocr_result.get("images", []):
                for field in image.get("fields", []):
                    full_text += field.get("inferText", "") + " "

            # 영양성분 정보 구조화
            nutrition_data = parse_nutrition_text(full_text)

            return jsonify(nutrition_data), 200

        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"API request failed: {e}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

def parse_nutrition_text(text):
    """
    OCR로 추출된 텍스트에서 영양성분 정보를 파싱하여 JSON으로 구조화합니다.
    This is a placeholder implementation.
    A more robust implementation would use regex and NLP techniques.
    """
    
    nutrition_data = {}
    
    # Example of how to parse the text. This is highly dependent on the OCR output format.
    # This is a very basic example and will need to be improved.
    
    # 칼로리 (kcal)
    calories_match = re.search(r'열량\s*(\d+)\s*kcal', text)
    if calories_match:
        nutrition_data['calories'] = {'value': int(calories_match.group(1)), 'unit': 'kcal'}

    # 나트륨 (mg)
    sodium_match = re.search(r'나트륨\s*(\d+)\s*mg', text)
    if sodium_match:
        nutrition_data['sodium'] = {'value': int(sodium_match.group(1)), 'unit': 'mg'}

    # 탄수화물 (g)
    carbs_match = re.search(r'탄수화물\s*(\d+)\s*g', text)
    if carbs_match:
        nutrition_data['carbohydrates'] = {'total': {'value': int(carbs_match.group(1)), 'unit': 'g'}}
        
        # 당류 (g)
        sugars_match = re.search(r'당류\s*(\d+)\s*g', text)
        if sugars_match:
            nutrition_data['carbohydrates']['sugars'] = {'value': int(sugars_match.group(1)), 'unit': 'g'}

    # 지방 (g)
    fat_match = re.search(r'지방\s*(\d+)\s*g', text)
    if fat_match:
        nutrition_data['fat'] = {'total': {'value': int(fat_match.group(1)), 'unit': 'g'}}
        
        # 포화지방 (g)
        sat_fat_match = re.search(r'포화지방\s*(\d+)\s*g', text)
        if sat_fat_match:
            nutrition_data['fat']['saturated_fat'] = {'value': int(sat_fat_match.group(1)), 'unit': 'g'}
            
        # 트랜스지방 (g)
        trans_fat_match = re.search(r'트랜스지방\s*(\d+)\s*g', text)
        if trans_fat_match:
            nutrition_data['fat']['trans_fat'] = {'value': int(trans_fat_match.group(1)), 'unit': 'g'}

    # 콜레스테롤 (mg)
    cholesterol_match = re.search(r'콜레스테롤\s*(\d+)\s*mg', text)
    if cholesterol_match:
        nutrition_data['cholesterol'] = {'value': int(cholesterol_match.group(1)), 'unit': 'mg'}

    # 단백질 (g)
    protein_match = re.search(r'단백질\s*(\d+)\s*g', text)
    if protein_match:
        nutrition_data['protein'] = {'value': int(protein_match.group(1)), 'unit': 'g'}

    return nutrition_data


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
