## 1. Dockerfile 준비

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


---
## 2. Dockerfile 빌드 및 실행 (로컬)

**이미지 빌드:** `ocr-server` 폴더에서 아래 명령어를 실행합니다.

```bash
docker build -t ocr-server:latest .
```

**컨테이너 실행:** 로컬 PC의 5001번 포트를 컨테이너의 5000번 포트에 연결하여 실행합니다.

```bash
docker run --env-file ./.env -d -p 5001:5000 ocr-server:latest
```


---
## 3. Docker 이미지 Docker Hub에 Push

먼저, 로컬에서 성공적으로 테스트했던 `my-ocr-server:latest` 이미지를 Docker Hub에 업로드합니다.

#### 1. Docker Hub 로그인

```bash
docker login
```

명령어를 실행하고 Docker Hub 사용자 이름과 비밀번호를 입력합니다.

#### 2. 이미지 태그 지정

`[Docker Hub ID]/ocr-server:v1` 형식으로 이미지에 태그를 지정합니다.

```bash
docker tag ocr-server:latest [Docker Hub ID]/ocr-server:v1
```

#### 3. 이미지 푸시

태그를 지정한 이미지를 Docker Hub에 푸시합니다.

```bash
docker push [Docker Hub ID]/ocr-server:v1
```


---
## 4. (번외) Kubernetes ImagePull 오류 해결: 아키텍처 불일치

### 4-1. 문제 현상

Kubernetes Pod이 `ImagePullBackOff` 상태에 머물며, 로그의 **Events** 섹션에 다음과 같은 메시지가 반복적으로 나타납니다:

```

Failed to pull image "yunseocloud/ocr-server\:v1": rpc error: code = NotFound desc = failed to pull and unpack image "docker.io/yunseocloud/ocr-server\:v1": no match for platform in manifest: not found

```

이 오류는 Docker Hub에 `yunseocloud/ocr-server:v1`이라는 이름의 이미지가 존재하더라도, **쿠버네티스 클러스터가 사용하는 플랫폼에 맞는 이미지가 존재하지 않음**을 의미합니다.

### 4-2. 원인 분석

이 문제는 주로 **CPU 아키텍처 불일치**로 인해 발생합니다.

- M1/M2/M3 칩이 탑재된 Mac에서 Docker 이미지를 빌드할 경우, 기본적으로 `arm64` 아키텍처로 이미지가 생성됩니다.
- 반면, 대부분의 클라우드 서버(예: NHN Cloud의 워커 노드)는 `amd64` 아키텍처를 사용합니다.

이러한 불일치로 인해, 쿠버네티스는 `arm64` 기반 이미지를 실행할 수 없고, 해당 플랫폼에 맞는 이미지가 없다는 오류를 발생시키게 됩니다.

### 4-3. 해결 방법: 멀티 아키텍처 이미지로 빌드 및 푸시

`docker buildx`를 사용하면 여러 아키텍처를 지원하는 멀티 플랫폼 이미지를 생성할 수 있습니다.

```bash
# buildx 빌더 생성 및 설정
docker buildx create --name multi_arch_builder
docker buildx use multi_arch_builder

# amd64와 arm64를 모두 지원하는 이미지 빌드 및 푸시
docker buildx build --platform linux/amd64,linux/arm64 -t [Docker Hub ID]/ocr-server:v1 --push .
```
### 4-4. 이후 조치

이미지를 위 방식으로 다시 빌드하고 푸시한 후, 기존의 Kubernetes 리소스를 다시 적용합니다:

```bash
kubectl apply -f ocr-backend-deployment.yaml
```

Pod이 **Running 상태**로 전환되면 문제가 해결된 것입니다. 더 이상 `ImagePullBackOff`나 `no match for platform` 오류가 발생하지 않아야 합니다.