import streamlit as st
import requests
import json

# 백엔드 서버 URL (쿠버네티스 배포 후 변경될 주소)
# 로컬 테스트 시에는 'http://localhost:5001/ocr' 사용
# 쿠버네티스 배포 시에는 [서비스이름].[네임스페이스이름] 형태의 DNS 주소를 사용

# BACKEND_URL = "http://localhost:5001/ocr"
BACKEND_URL = "http://ocr-server-service.backend:80/ocr"

st.title("OCR Streamlit 애플리케이션")
st.write("이미지를 업로드하고 OCR 버튼을 누르면 텍스트를 인식합니다.")

uploaded_file = st.file_uploader("이미지를 업로드하세요...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
    
    if st.button("OCR 실행"):
        # 파일을 백엔드로 전송
        files = {'file': uploaded_file.getvalue()}
        
        try:
            response = requests.post(BACKEND_URL, files=files)
            
            if response.status_code == 200:
                result_text = response.json().get('text')
                st.subheader("인식 결과:")
                st.text(result_text)
            else:
                st.error(f"백엔드 서버 오류: {response.status_code}")
                st.write(response.json())
        except requests.exceptions.ConnectionError:
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")