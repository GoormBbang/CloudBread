# Streamlit 프론트엔드: CloudBread OCR

이 문서는 Streamlit 기반의 OCR 프론트엔드 애플리케이션을 Docker 이미지로 만들고, 백엔드와 연동하여 테스트 및 배포하는 과정을 안내합니다.

## 주요 기능

- **일반 OCR**: Tesseract를 사용하여 이미지에서 텍스트를 추출합니다.
- **영양성분 분석**: Naver OCR API를 통해 영양성분표 이미지를 분석하고, 구조화된 JSON 데이터로 결과를 제공합니다.
  - 칼로리, 나트륨, 탄수화물, 당류, 지방, 포화지방, 트랜스지방, 콜레스테롤, 단백질, **칼슘** 정보 추출
  - 사용자 친화적인 메트릭 형태로 영양성분 표시
  - 디버깅용 전체 OCR 텍스트 제공

## 1. 프로젝트 파일 구성

```
/demo/
├── app.py            # Streamlit 프론트엔드 코드
├── requirements.txt  # Python 라이브러리 목록
├── Dockerfile        # 컨테이너 이미지 빌드 스크립트
└── demo-frontend-deployment.yaml # Kubernetes 배포 정의
```

## 2. app.py (Streamlit 프론트엔드 코드)

사용자가 OCR 모드를 선택하고 이미지를 업로드하면, 백엔드 서버로 요청을 보내고 결과를 표시합니다.

```python
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
```

> **참고**: `BASE_URL`은 쿠버네티스 클러스터 내에서 백엔드 서비스(`ocr-server-service`)를 찾기 위한 주소입니다. 로컬에서 테스트할 경우, 이 값을 `http://localhost:5001`로 변경하여 사용하세요.

## 3. 로컬 테스트

1.  **백엔드 서버 실행**: `ocr` 디렉토리의 `README.md`를 참고하여 백엔드 Docker 컨테이너를 실행합니다.
2.  **프론트엔드 실행**: `demo` 디렉토리에서 아래 명령어를 실행하여 프론트엔드 Docker 컨테이너를 빌드하고 실행합니다.

    ```bash
    # Docker 이미지 빌드
    docker build -t demo-frontend:latest .

    # Docker 컨테이너 실행 (8501 포트 사용)
    docker run -d -p 8501:8501 demo-frontend:latest
    ```
3.  **웹 브라우저 접속**: [http://localhost:8501](http://localhost:8501)에 접속하여 애플리케이션을 테스트합니다.

## 4. Kubernetes 배포

1.  **이미지 빌드 및 푸시**: 멀티-아키텍처를 지원하는 이미지를 빌드하여 Docker Hub에 푸시합니다.

    ```bash
    # buildx 빌더 생성 및 사용 (최초 1회)
    docker buildx create --name mybuilder
    docker buildx use mybuilder

    # 멀티-아키텍처 이미지 빌드 및 푸시
    docker buildx build --platform linux/amd64,linux/arm64 \
      -t [Docker Hub ID]/demo-frontend:latest --push .
    ```
    > `[Docker Hub ID]`를 실제 Docker Hub 사용자 ID로 변경하세요.

2.  **배포 파일 수정**: `demo-frontend-deployment.yaml` 파일의 `image` 필드를 방금 푸시한 이미지 주소로 변경합니다.

    ```yaml
    # ...
      containers:
      - name: demo-frontend-container
        image: [Docker Hub ID]/demo-frontend:latest # <-- 이 부분을 수정
    # ...
    ```

3.  **Kubernetes에 배포**:

    ```bash
    # frontend 네임스페이스 생성
    kubectl create namespace frontend

    # Deployment 및 Service 배포
    kubectl apply -f demo-frontend-deployment.yaml
    ```

4.  **외부 접속 확인**: `LoadBalancer` 타입의 서비스에 외부 IP가 할당되면, 해당 IP로 접속하여 배포된 애플리케이션을 확인할 수 있습니다.

    ```bash
    kubectl get services -n frontend
    ```
