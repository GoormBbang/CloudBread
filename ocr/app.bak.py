from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import io

# Tesseract-OCR 경로 설정 (필요에 따라 수정)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)