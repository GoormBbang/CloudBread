import streamlit as st
import requests
import json
import os

# Docker 컨테이너에서 호스트 머신에 접근하기 위해 'host.docker.internal'을 사용합니다.
# 이 주소는 demo-frontend 컨테이너가 호스트의 5001번 포트에서 실행 중인 ocr-server에 접근할 수 있도록 합니다.
# 쿠버네티스 배포 시에는 이 값을 "http://ocr-server-service.backend:80"으로 변경해야 합니다.
BASE_URL = "http://host.docker.internal:5001"

st.title("☁️ CloudBread OCR")
st.write("이미지를 업로드하고 원하는 OCR 작업을 선택하세요.")

# OCR 모드 선택
ocr_mode = st.radio(
    "OCR 모드를 선택하세요:",
    ("일반 OCR", "영양성분 분석")
)

uploaded_file = st.file_uploader("이미지 업로드", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)

    if st.button("OCR 실행"):
        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        endpoint = ""

        if ocr_mode == "일반 OCR":
            endpoint = f"{BASE_URL}/ocr"
        elif ocr_mode == "영양성분 분석":
            endpoint = f"{BASE_URL}/ocr/nutrition"

        if endpoint:
            try:
                with st.spinner('인식 중...'):
                    response = requests.post(endpoint, files=files)
                
                if response.status_code == 200:
                    st.subheader("✅ 인식 결과")
                    if ocr_mode == "일반 OCR":
                        result_text = response.json().get('text')
                        st.text_area("추출된 텍스트", result_text, height=200)
                    elif ocr_mode == "영양성분 분석":
                        result_data = response.json()
                        
                        # 영양성분 데이터 표시
                        if 'nutrition' in result_data:
                            st.subheader("🍎 영양성분 정보")
                            nutrition = result_data['nutrition']
                            
                            # 칼로리
                            if 'calories' in nutrition:
                                st.metric("칼로리", f"{nutrition['calories']['value']} {nutrition['calories']['unit']}")
                            
                            # 주요 영양성분을 컬럼으로 나누어 표시
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if 'sodium' in nutrition:
                                    st.metric("나트륨", f"{nutrition['sodium']['value']} {nutrition['sodium']['unit']}")
                                if 'carbohydrates' in nutrition:
                                    carbs = nutrition['carbohydrates']['total']
                                    st.metric("탄수화물", f"{carbs['value']} {carbs['unit']}")
                                    if 'sugars' in nutrition['carbohydrates']:
                                        sugars = nutrition['carbohydrates']['sugars']
                                        st.metric("당류", f"{sugars['value']} {sugars['unit']}")
                                if 'protein' in nutrition:
                                    st.metric("단백질", f"{nutrition['protein']['value']} {nutrition['protein']['unit']}")
                            
                            with col2:
                                if 'fat' in nutrition:
                                    fat = nutrition['fat']['total']
                                    st.metric("지방", f"{fat['value']} {fat['unit']}")
                                    if 'saturated_fat' in nutrition['fat']:
                                        sat_fat = nutrition['fat']['saturated_fat']
                                        st.metric("포화지방", f"{sat_fat['value']} {sat_fat['unit']}")
                                    if 'trans_fat' in nutrition['fat']:
                                        trans_fat = nutrition['fat']['trans_fat']
                                        st.metric("트랜스지방", f"{trans_fat['value']} {trans_fat['unit']}")
                                if 'cholesterol' in nutrition:
                                    st.metric("콜레스테롤", f"{nutrition['cholesterol']['value']} {nutrition['cholesterol']['unit']}")
                                if 'calcium' in nutrition:
                                    st.metric("칼슘", f"{nutrition['calcium']['value']} {nutrition['calcium']['unit']}")
                        
                        # 전체 OCR 텍스트 표시 (디버깅용)
                        if 'full_text' in result_data:
                            with st.expander("🔍 OCR 전체 텍스트 (디버깅용)"):
                                st.text_area("추출된 전체 텍스트", result_data['full_text'], height=200)
                        
                        # 원본 JSON 데이터도 확장 가능한 영역에 표시
                        with st.expander("📄 원본 JSON 데이터"):
                            st.json(result_data)
                else:
                    st.error(f"백엔드 서버 오류: {response.status_code}")
                    try:
                        st.error(response.json().get('error'))
                    except json.JSONDecodeError:
                        st.error("응답 내용을 JSON으로 파싱할 수 없습니다.")
                        st.text(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"백엔드 서버에 연결할 수 없습니다: {e}")