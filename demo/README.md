# Streamlit 프론트엔드 이미지 생성 및 로컬 테스트

이 문서는 Streamlit 기반의 OCR 프론트엔드 애플리케이션을 Docker 이미지로 만들고, 로컬에서 백엔드와 연동하여 테스트하는 과정을 담고 있습니다.

## 1. 프로젝트 파일 구성

`demo-frontend` 폴더를 만들고 아래와 같이 파일을 구성합니다.

```

/demo-frontend/
├── app.py            # Streamlit 프론트엔드 코드
├── requirements.txt  # 필요한 Python 라이브러리 목록
└── Dockerfile        # 컨테이너 이미지를 만들기 위한 스크립트

````

## 2. app.py (Streamlit 프론트엔드 코드)

백엔드 서버로 POST 요청을 보내는 Streamlit 웹 앱을 작성합니다.

```python
import streamlit as st
import requests
import json

# 백엔드 서버 URL (로컬 테스트용)
# 쿠버네티스 배포 시: http://ocr-server-service.ocr-backend/ocr
BACKEND_URL = "http://localhost:5001/ocr"

st.title("OCR Streamlit 애플리케이션")
st.write("이미지를 업로드하고 OCR 버튼을 누르면 텍스트를 인식합니다.")

uploaded_file = st.file_uploader("이미지를 업로드하세요...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="업로드된 이미지", use_column_width=True)
    
    if st.button("OCR 실행"):
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
````

> 참고: `BACKEND_URL`을 `localhost:5001`로 지정하여 이전에 실행한 OCR 백엔드 컨테이너와 통신하도록 설정했습니다.

## 3. requirements.txt (필요 라이브러리)

```
streamlit
requests
```

## 4. Dockerfile (이미지 빌드 스크립트)

`python:3.12-slim` 이미지를 기반으로 Streamlit을 설치하고 웹 앱을 실행합니다.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

## 5. Docker 이미지 빌드 및 실행

**이미지 빌드:**
`demo-frontend` 폴더에서 아래 명령어를 실행합니다.

```bash
docker build -t demo-frontend:latest .
```

**기존 컨테이너 삭제 (선택 사항):**

```bash
docker rm -f demo-frontend
```

**컨테이너 실행:**
로컬 PC의 8080번 포트를 컨테이너의 8501번 포트에 연결하여 실행합니다.

```bash
docker run -d -p 8501:8501 --name demo-frontend demo-frontend:latest
```

## 6. 프론트엔드 테스트

백엔드 컨테이너(`ocr-server`)가 5001번 포트에서 실행 중인지 확인하세요.
웹 브라우저를 열고 [http://localhost:8501](http://localhost:8501)에 접속하여 프론트엔드 앱을 테스트합니다.

---

<br>
<br>
<br>
<br>

# Kubernetes에 Streamlit 프론트엔드 배포하기

## 1단계: 프론트엔드 코드 수정 및 이미지 빌드/푸시

### 🔧 app.py 수정

`demo` 폴더의 `app.py` 파일을 열고, **백엔드 서버 URL을 Kubernetes용으로 변경**합니다.

```python
import streamlit as st
import requests
import json

# 쿠버네티스 배포용 백엔드 URL
# [서비스이름].[네임스페이스이름] 형태의 DNS 주소를 사용
BACKEND_URL = "http://ocr-server-service.backend:80/ocr"

st.title("OCR Streamlit 애플리케이션")
st.write("이미지를 업로드하고 OCR 버튼을 누르면 텍스트를 인식합니다.")

uploaded_file = st.file_uploader("이미지를 업로드하세요...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="업로드된 이미지", use_column_width=True)

    if st.button("OCR 실행"):
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
```

### 🏗️ 멀티-아키텍처 이미지 빌드 및 푸시

`demo` 폴더에서 다음 명령어를 실행합니다:

```bash
# buildx 빌더가 이미 설정되어 있다고 가정
docker buildx build --platform linux/amd64,linux/arm64 \
  -t [Docker Hub ID]/demo-frontend:v1 --push .
```

> 📌 `[Docker Hub ID]` 부분을 실제 Docker Hub 사용자 ID로 변경하세요.

---

## 2단계: frontend 네임스페이스 및 리소스 YAML 파일 작성

이제 프론트엔드를 Kubernetes에 배포하기 위한 YAML 파일을 작성합니다.
**Service는 외부 접속을 허용하기 위해 `LoadBalancer` 타입**으로 설정합니다.

### 📄 `demo-frontend-deployment.yaml`

```yaml
# demo-frontend-deployment.yaml
# 프론트엔드 Deployment와 Service 정의

apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-frontend-deployment
  namespace: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo-frontend
  template:
    metadata:
      labels:
        app: demo-frontend
    spec:
      containers:
      - name: demo-frontend-container
        image: [Docker Hub ID]/demo-frontend:v1 # ← 빌드한 이미지 주소
        ports:
        - containerPort: 8501
---
apiVersion: v1
kind: Service
metadata:
  name: demo-frontend-service
  namespace: frontend
spec:
  selector:
    app: demo-frontend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8501
  type: LoadBalancer
```

> ⚠️ 반드시 `image:` 항목의 주소를 `[Docker Hub ID]/demo-frontend:v1`로 변경하세요.

---

## 3단계: Kubernetes에 배포하기

### 🌱 네임스페이스 생성

```bash
kubectl create namespace frontend
```

### 🚀 YAML 파일 적용

```bash
kubectl apply -f demo-frontend-deployment.yaml
```

---

## 4단계: 배포 상태 및 외부 접속 확인

### ✅ 배포 리소스 확인

```bash
kubectl get all -n frontend
```

* `Pod`의 `STATUS`가 `Running`인지 확인
* `Service`의 `EXTERNAL-IP`가 할당되었는지 확인
  (LoadBalancer 타입은 IP 할당까지 약간의 시간이 걸릴 수 있음)

### 🌐 웹 브라우저 접속

```bash
kubectl get services -n frontend
```

* `demo-frontend-service`의 `EXTERNAL-IP` 값을 확인
* 브라우저에서 `http://[EXTERNAL-IP]`로 접속하면 Streamlit 앱에 접속 가능

---

## ✅ 결과

* 프론트엔드는 `frontend` 네임스페이스에
* 백엔드는 `backend` 네임스페이스에 각각 배포됨
* 프론트엔드 앱을 통해 OCR 기능 사용 가능

이제 완전한 OCR 애플리케이션이 쿠버네티스 환경에서 정상 작동합니다 🎉