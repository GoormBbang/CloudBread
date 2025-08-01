# OCR 백엔드 서버 이미지 생성 및 로컬 테스트

이 문서는 Python Flask 기반의 OCR API 서버를 Docker 이미지로 만들고, 로컬 환경에서 테스트하는 과정을 담고 있습니다.

## 1. 프로젝트 파일 구성

먼저, `ocr-server`이라는 이름의 폴더를 만들고 아래와 같이 파일을 구성합니다.

```

/ocr-server/
├── app.py          # Python OCR 서버 코드
├── requirements.txt  # 필요한 Python 라이브러리 목록
└── Dockerfile      # 컨테이너 이미지를 만들기 위한 스크립트

````

## 2. app.py (OCR 서버 코드)

Flask와 pytesseract를 사용하여 이미지를 인식하는 API를 작성합니다.

```python
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import io

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
````

## 3. requirements.txt (필요 라이브러리)

```
Flask
Pillow
pytesseract
```

## 4. Dockerfile (이미지 빌드 스크립트)

python:3.12-slim 이미지를 기반으로 시스템 패키지와 파이썬 라이브러리를 설치합니다. 한글 인식을 위해 tesseract-ocr-kor 패키지를 추가했습니다.

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    tesseract-ocr-kor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
```

## 5. Docker 이미지 빌드 및 실행

**이미지 빌드:**
`ocr-server` 폴더에서 아래 명령어를 실행합니다.

```bash
docker build -t ocr-server:latest .
```

**기존 컨테이너 삭제 (선택 사항):**
포트 충돌이나 이름 중복을 방지하기 위해 이전에 실행했던 컨테이너를 삭제합니다.

```bash
docker rm -f ocr-server
```

**컨테이너 실행:**
로컬 PC의 5001번 포트를 컨테이너의 5000번 포트에 연결하여 실행합니다. 5000번 포트가 이미 사용 중일 수 있으므로 5001번을 사용합니다.

```bash
docker run -d -p 5001:5000 --name ocr-server ocr-server:latest
```

## 6. OCR API 테스트

텍스트가 포함된 이미지 파일(`test.png`)을 준비하고 `curl` 명령어를 사용해 서버에 요청을 보냅니다.

```bash
curl -X POST -F "file=@./test.png" http://localhost:5001/ocr
```

정상적으로 실행되면 이미지에서 인식된 텍스트가 JSON 형태로 반환됩니다.


---

<br>
<br>
<br>

# OCR Docker 이미지 Docker Hub에 푸시하고 Kubernetes에 배포하기

먼저, 로컬에서 성공적으로 테스트했던 `my-ocr-server:latest` 이미지를 Docker Hub에 업로드합니다.

## 1. Docker Hub 로그인

```bash
docker login
````

명령어를 실행하고 Docker Hub 사용자 이름과 비밀번호를 입력합니다.

## 2. 이미지 태그 지정

`[Docker Hub ID]/ocr-server:v1` 형식으로 이미지에 태그를 지정합니다.

```bash
docker tag ocr-server:latest [Docker Hub ID]/ocr-server:v1
```


## 3. 이미지 푸시

태그를 지정한 이미지를 Docker Hub에 푸시합니다.

```bash
docker push [Docker Hub ID]/ocr-server:v1
```

---

# 2단계: 백엔드 네임스페이스 및 리소스 YAML 파일 작성

이제 쿠버네티스 클러스터에 배포할 YAML 파일을 작성합니다. `image:` 주소만 Docker Hub 주소로 변경하면 됩니다.

## ocr-backend-deployment.yaml

```yaml
# ocr-backend-deployment.yaml
# OCR 서버의 Deployment와 Service를 하나의 파일로 정의

apiVersion: apps/v1
kind: Deployment
metadata:
  name: ocr-server-deployment
  namespace: backend # backend 네임스페이스에 배포
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ocr-server
  template:
    metadata:
      labels:
        app: ocr-server
    spec:
      containers:
      - name: ocr-server-container
        # 이미지 주소를 Docker Hub 주소로 변경합니다.
        image: [Docker Hub ID]/ocr-server:v1
        ports:
        - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: ocr-server-service
  namespace: backend # backend 네임스페이스에 배포
spec:
  selector:
    app: ocr-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: ClusterIP # 클러스터 내부에서만 접근 가능하도록 설정
```

> ⚠️ **주의:** 위 YAML 파일의 `image:` 부분을 반드시 `[Docker Hub ID]/ocr-server:v1`로 변경해야 합니다.

---

# 3단계: Kubernetes에 배포하기

이제 `kubectl` 명령어로 클러스터에 배포합니다.

## 1. backend 네임스페이스 생성

```bash
kubectl create namespace backend
```

## 2. YAML 파일 적용

`ocr-backend-deployment.yaml` 파일이 있는 디렉터리에서 아래 명령어를 실행합니다.

```bash
kubectl apply -f ocr-backend-deployment.yaml
```

---

# 4단계: 배포 상태 확인

마지막으로 배포가 정상적으로 완료되었는지 확인합니다.

```bash
# backend 네임스페이스의 모든 리소스 확인
kubectl get all -n backend

# Pod이 Running 상태인지 확인
kubectl get pods -n backend

# Service가 ClusterIP 타입으로 생성되었는지 확인
kubectl get services -n backend
```

모든 리소스가 **Running** 또는 **ClusterIP** 타입으로 정상 작동한다면, 백엔드 OCR 서버가 쿠버네티스 클러스터에 성공적으로 배포된 것입니다.
이제 프론트엔드 앱은 `ocr-server-service.backend`라는 주소를 통해 이 백엔드에 접근할 수 있게 됩니다.

---

<br>
<br>
<br>
<br>

# Kubernetes ImagePull 오류 해결: 아키텍처 불일치

## 문제 현상

Kubernetes Pod이 `ImagePullBackOff` 상태에 머물며, 로그의 **Events** 섹션에 다음과 같은 메시지가 반복적으로 나타납니다:

```

Failed to pull image "yunseocloud/ocr-server\:v1": rpc error: code = NotFound desc = failed to pull and unpack image "docker.io/yunseocloud/ocr-server\:v1": no match for platform in manifest: not found

```

이 오류는 Docker Hub에 `yunseocloud/ocr-server:v1`이라는 이름의 이미지가 존재하더라도, **쿠버네티스 클러스터가 사용하는 플랫폼에 맞는 이미지가 존재하지 않음**을 의미합니다.

## 원인 분석

이 문제는 주로 **CPU 아키텍처 불일치**로 인해 발생합니다.

- M1/M2/M3 칩이 탑재된 Mac에서 Docker 이미지를 빌드할 경우, 기본적으로 `arm64` 아키텍처로 이미지가 생성됩니다.
- 반면, 대부분의 클라우드 서버(예: NHN Cloud의 워커 노드)는 `amd64` 아키텍처를 사용합니다.

이러한 불일치로 인해, 쿠버네티스는 `arm64` 기반 이미지를 실행할 수 없고, 해당 플랫폼에 맞는 이미지가 없다는 오류를 발생시키게 됩니다.

## 해결 방법

### 방법 1: 멀티 아키텍처 이미지로 빌드 및 푸시

`docker buildx`를 사용하면 여러 아키텍처를 지원하는 멀티 플랫폼 이미지를 생성할 수 있습니다.

```bash
# buildx 빌더 생성 및 설정
docker buildx create --name mybuilder
docker buildx use mybuilder

# amd64와 arm64를 모두 지원하는 이미지 빌드 및 푸시
docker buildx build --platform linux/amd64,linux/arm64 -t [Docker Hub ID]/ocr-server:v1 --push .
```

> `--push` 옵션을 사용하면 `docker push` 없이도 이미지가 자동으로 Docker Hub에 업로드됩니다.

### 방법 2: amd64 전용 이미지로 빌드

단일 아키텍처(`amd64`)만 지원하도록 명시하여 이미지를 빌드할 수도 있습니다.

```bash
# amd64 아키텍처로 이미지 빌드
docker build --platform linux/amd64 -t [Docker Hub ID]/ocr-server:v1 .

# Docker Hub에 푸시
docker push [Docker Hub ID]/ocr-server:v1
```

## 이후 조치

이미지를 위 방식 중 하나로 다시 빌드하고 푸시한 후, 기존의 Kubernetes 리소스를 다시 적용합니다:

```bash
kubectl apply -f ocr-backend-deployment.yaml
```

Pod이 **Running 상태**로 전환되면 문제가 해결된 것입니다.
더 이상 `ImagePullBackOff`나 `no match for platform` 오류가 발생하지 않아야 합니다.