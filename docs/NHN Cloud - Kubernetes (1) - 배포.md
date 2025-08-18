## 1. NHN Cloud NKS접속

[NHN Cloud CONSOLE](https://k-paas.console.nhncloud.com/project/KcFiGwCb/container/nhn-kubernetes-service-nks)

ID: contest2
PW: contest2!


---
## 2. kubeconfig.yaml 

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ...
    server: https://6ffd2c02-nks-kr1.container.nhncloud.com:6443
  name: "nks_kpaas-contest-2_6ffd2c02-bb28-4d4e-a4e3-2468d0235b2b"
contexts:
- context:
    cluster: "nks_kpaas-contest-2_6ffd2c02-bb28-4d4e-a4e3-2468d0235b2b"
    user: "nks_kpaas-contest-2_6ffd2c02-bb28-4d4e-a4e3-2468d0235b2b"
  name: "nks_kpaas-contest-2_6ffd2c02-bb28-4d4e-a4e3-2468d0235b2b"
current-context: "nks_kpaas-contest-2_6ffd2c02-bb28-4d4e-a4e3-2468d0235b2b"
kind: Config
preferences: {}
users:
- name: "nks_kpaas-contest-2_6ffd2c02-bb28-4d4e-a4e3-2468d0235b2b"
  user:
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZ...
    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJ...
```

### 2-1. kubeconfig.yaml 등록

```bash
KUBECONFIG=~/.kube/config:/path/to/cluster1.yaml:/path/to/cluster2.yaml \
  kubectl config view --merge --flatten > /tmp/config

mv /tmp/config ~/.kube/config
```

### 2-2. 작업 contexts 전환

```bash
kubectl config get-contexts
kubectl config use-context my-cluster
```


---
## 3. Deployment.yaml & Service.yaml

- **Deployment** → “앱(컨테이너)을 어떻게 실행/유지할지 정의하는 것”
    
- **Service** → “그 앱에 어떻게 접근할지 정의하는 것”

### 3-1. Deployment (애플리케이션 실행/관리자)

**정의**
- Pod(컨테이너 집합)을 생성하고, 원하는 개수(Replica)로 유지하며, 업데이트/롤백을 관리하는 컨트롤러 리소스.
- 즉, **“이 앱을 몇 개, 어떤 설정으로 항상 돌려라”** 를 쿠버네티스에 알려주는 역할.

**주요 기능**
1. **Replica 관리**
    - replicas: 3 → 동일한 Pod 3개를 항상 유지.
    - 하나 죽으면 자동으로 새로운 Pod 생성.
    
2. **롤링 업데이트 (Rolling Update)**
    - 이미지 버전 바꿀 때 Pod를 하나씩 교체해서 무중단 배포.
    
3. **롤백 (Rollback)**
    - 문제가 생기면 이전 버전으로 되돌릴 수 있음.
    
4. **Self-healing (자가복구)**
    - Pod가 죽거나 노드에서 사라지면 자동으로 다시 스케줄링해서 살려줌.
#### ocr/ocr-backend-deployment.yaml
```yaml
apiVersion: apps/v1                 # 사용할 쿠버네티스 API 버전 (Deployment는 apps/v1을 사용)
kind: Deployment                    # 리소스 종류: Deployment
metadata:
  name: ocr-server-deployment       # Deployment 이름 (클러스터 내에서 유일해야 함)
  namespace: backend                # 배포할 네임스페이스 (없으면 default 네임스페이스에 생성됨)
spec:
  replicas: 1                       # 유지할 Pod 개수 (복제본 수)
  selector:                         # 어떤 Pod를 이 Deployment가 관리할지 선택하는 기준
    matchLabels:
      app: ocr-server               # app=ocr-server 라벨을 가진 Pod들을 관리 대상으로 함
  template:                         # Pod 템플릿 정의 (새 Pod를 어떻게 만들지 지정)
    metadata:
      labels:
        app: ocr-server             # Pod에 붙일 라벨 (Service selector 등과 매칭됨)
    spec:
      containers:                   # Pod 안에 포함될 컨테이너 목록
      - name: ocr-server-container  # 컨테이너 이름
        image: [Docker Hub ID]/ocr-server:v1  # 사용할 컨테이너 이미지 (예: myid/ocr-server:v1)
        ports:
        - containerPort: 5000       # 컨테이너가 리슨하는 포트 (앱이 열어둔 포트)
```

### 3-2. Service (네트워크 접근 창구)

**정의**
- 여러 Pod에 접근하기 위한 **고정된 네트워크 엔드포인트**를 제공.
- Pod는 죽었다 살아나면 IP가 바뀌는데, Service는 항상 같은 주소를 보장.
- **Load Balancer** 역할도 수행해서 여러 Pod에 트래픽 분산.  

**Service 타입**
1. **ClusterIP (기본값)**
    - 클러스터 내부에서만 접근 가능.
    - 예: 백엔드 DB, 내부 API 서버.
    
2. **NodePort**
    - 클러스터 외부에서 \<NodeIP>:\<Port>로 접근 가능.
    - 로컬 개발, 간단한 테스트에 사용.
    
3. **LoadBalancer**
    - 클라우드 환경(AWS, GCP, Azure 등)에서 외부 Load Balancer를 자동 생성.
    - 외부 트래픽을 받아서 Pod로 전달.
    
4. **ExternalName**
    - 쿠버네티스 외부 도메인에 트래픽을 프록시함.
#### ocr/ocr-backend-service.yaml
```yaml
apiVersion: v1                   # 사용할 쿠버네티스 API 버전 (Service는 v1)
kind: Service                    # 리소스 종류: Service
metadata:
  name: ocr-server-service       # Service 이름 (클러스터 내에서 유일해야 함)
  namespace: backend             # 배포할 네임스페이스 (없으면 default 네임스페이스에 생성됨)
spec:
  selector:                      # 어떤 Pod들에 트래픽을 전달할지 선택하는 기준
    app: ocr-server              # 라벨 app=ocr-server 를 가진 Pod들을 대상으로 함
  ports:                         # Service가 노출할 포트 설정
    - protocol: TCP              # 사용할 네트워크 프로토콜 (기본값은 TCP)
      port: 80                   # Service가 클러스터 내에서 노출할 포트 (고정 IP와 함께 사용됨)
      targetPort: 5000           # 실제 Pod 컨테이너가 열어둔 포트 (containerPort와 매칭)
  type: ClusterIP                # Service 타입: 클러스터 내부에서만 접근 가능 (기본값)
```

#### 3-2-1. 포트 연결
```
클러스터 내부의 다른 Pod
        │
        │  요청: http://ocr-server-service:80
        ▼
┌─────────────────────┐
│ Service (port=80)   │
│   고정 IP + DNS      │
└─────────────────────┘
        │
        │ (포워딩)
        ▼
┌─────────────────────┐
│ Pod (컨테이너)        │
│   targetPort=5000   │ ← OCR 서버 앱이 여기서 실행 중
└─────────────────────┘
```

- `http://[Service 이름].[namespace 이름]:80
---
## 4. 배포 (Deploy)

### 4-1. 네임스페이스 생성

```bash
kubectl create namespace backend
```

### 4-2. YAML 파일 적용

```bash
kubectl apply -f ocr-backend-deployment.yaml
kubectl apply -f ocr-backend-service.yaml
```

### 4-3. 배포 상태 확인

```bash
# backend 네임스페이스의 모든 리소스 확인
kubectl get all -n backend

# Pod이 Running 상태인지 확인
kubectl get pods -n backend

# Service가 ClusterIP 타입으로 생성되었는지 확인
kubectl get services -n backend
```

