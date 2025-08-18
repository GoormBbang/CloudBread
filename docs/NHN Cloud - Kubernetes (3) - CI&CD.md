## 1. NHN Cloud Pipeline 접속

[NHN Cloud CONSOLE](https://k-paas.console.nhncloud.com/project/KcFiGwCb/dev-tools/pipeline#pipeline-management)

---
## 2. CD 파이프라인

시작 -> Build Stage -> Deploy Stage

### 2-1. Build Stage

1. **Helm Chart 기반 매니페스트 생성**
    
    - 렌더링 엔진: HELM3 라고 되어 있어서, Helm Chart를 기반으로 실제 K8s 매니페스트(YAML)를 생성(bake)합니다.
    - 쉽게 말하면 Helm 템플릿 + values 파일 → 최종 Deployment, Service 같은 YAML 파일을 “구워내는(bake)” 단계예요.
    
2. **소스 관리**
    
    - 소스는 GitHub 저장소(github-states-contest-2)에서 가져오고 있습니다.
    - 즉, 저장소에 있는 Helm 차트(ocr-server)를 읽어와서 빌드.
    
3. **출력**
    
    - 최종적으로 **쿠버네티스가 적용할 수 있는 manifest 파일 세트**를 산출합니다.
    - 이게 다음 단계인 **Deploy-Stage**에서 실제 클러스터(backend 네임스페이스)에 배포됩니다.

### 2-2. Deploy Stage

1. **클러스터에 매니페스트 적용**
    
    - Build 단계에서 생성된 Kubernetes manifest(Deployment, Service 등)를 지정된 네임스페이스(backend)에 실제로 배포합니다.
    - 내부적으로는 kubectl apply -f ... 또는 Helm의 helm upgrade --install ... 과 유사한 동작을 수행합니다.
    
2. **리소스 생성 및 업데이트**
    
    - Deployment → 새로운 Pod 생성 및 롤링 업데이트 수행
    - Service → Pod와 연결되는 네트워크 엔드포인트 보장
    - 기존에 배포된 리소스가 있으면 업데이트, 없으면 새로 생성합니다.
    
3. **롤링 업데이트 관리**
    
    - 기존 Pod들을 하나씩 새 버전으로 교체하면서 무중단 배포를 지원합니다.
    - 문제가 발생하면 이전 버전으로 롤백 가능하도록 이력이 남습니다.
    
4. **네임스페이스 단위 배포**
    
    - 설정에 나온 대로 backend 네임스페이스 안에서만 리소스를 생성/관리합니다.
    - 같은 클러스터라도 네임스페이스를 다르게 하면 충돌 없이 여러 환경(예: dev, test, prod) 배포 가능.

## 3. Helm Chart

### 3-1. Helm이란?

- **Helm**은 쿠버네티스의 **패키지 매니저** 역할을 합니다.
- 리눅스에서 apt, yum, brew 같은 게 있듯이, 쿠버네티스에서는 **Helm**을 써서 앱을 설치하고 관리합니다.
- 단순한 kubectl apply -f ... 방식보다 훨씬 체계적이고 재사용성이 좋습니다.

---

### 3-2. Helm Chart란?

- Helm에서 사용하는 **패키지 단위**를 **Chart**라고 부릅니다.
- 하나의 Chart는 “특정 애플리케이션을 쿠버네티스에 배포하는 방법”을 정의한 **템플릿 묶음**입니다.
- Chart 안에는 보통 이런 파일/구조가 들어 있습니다:

```
mychart/
  Chart.yaml        # 차트 메타데이터 (이름, 버전, 설명 등)
  values.yaml       # 기본 설정값 (사용자가 override 가능)
  templates/        # 쿠버네티스 리소스 템플릿 (Deployment, Service 등)
    deployment.yaml
    service.yaml
    _helpers.tpl    # 반복되는 값/함수를 정의
```

---

### 3-3. Helm Chart 동작 방식

1. **템플릿화된 매니페스트 작성**
    
    - templates/ 안의 YAML 파일에는 변수({{ }} 형태의 Go template 문법)가 들어 있음.

```
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

- → values.yaml이나 사용자가 넘겨주는 값으로 치환.
    
2. **values.yaml로 값 주입**
    
    - 사용자가 values.yaml에 환경별 설정(이미지 태그, replicas 수 등)을 넣어둠.
    - 배포 시 -f custom-values.yaml로 오버라이드 가능.
        
```
image:
  repository: myid/ocr-server
  tag: v1
replicas: 3
```
    
3. **렌더링(Bake) → 최종 manifest 생성**
    
    - Helm이 템플릿 + values.yaml을 합쳐서 **순수 Kubernetes manifest**로 변환.
    - 이 manifest를 쿠버네티스에 적용(helm install / helm upgrade).
    


---

### 3-4. 간단한 사용 예시 (로컬)

1. Chart 생성

```
helm create ocr-server
```
→ 기본 Chart 구조 생성됨.
    
2. values.yaml 수정

```
image:
  repository: myid/ocr-server
  tag: v1
replicas: 2
```
    
3. 배포

```
helm install ocr-server ./ocr-server -n backend
```
    
4. 업데이트

```
helm upgrade ocr-server ./ocr-server -f values-prod.yaml -n backend
```
  
### 3-5. helm package

- Helm 차트 디렉토리를 **하나의 .tgz 압축 파일**로 패키징합니다.    
- 이 파일은 Chart 저장소(예: Harbor, Artifactory, GitHub Pages 등)에 올려서 공유/배포할 때 사용합니다.

```bash
helm package ./ocr-server
```
    
**실행 결과**
- 현재 디렉토리에 ocr-server-0.1.0.tgz 같은 파일이 생김
    (Chart.yaml 안의 version을 따름)

추후 `템플릿 - 저장소 정보`의 경로에 이 tgz 파일의 위치를 지정해야 합니다.

```
https://api.github.com/repos/GoormBbang/CloudBread/contents/ocr/ocr-server/ocr-server-0.1.0.tgz
```

### 3-6. Helm Chart 예시 `/ocr-server` 
#### `ocr-server/Chart.yaml`
```yaml
apiVersion: v1
name: ocr-server
description: Helm chart for OCR backend (Deployment + Service)
type: application
version: 0.1.0          # 차트 버전
appVersion: "v1"        # 애플리케이션 버전(표시용)
```

#### `ocr-server\values.yaml`
```yaml
namespace: backend

replicaCount: 1

image:
  repository: yunseocloud/ocr-server
  tag: "latest"
  pullPolicy: IfNotPresent

containerPort: 5000

service:
  type: ClusterIP
  port: 80
  targetPort: 5000

# 필요 시 리소스 제한을 켜세요.
resources: {}
#  limits:
#    cpu: 500m
#    memory: 512Mi
#  requests:
#    cpu: 100m
#    memory: 128Mi

# 추가 환경변수가 필요하면 여기에
env: []
envFrom:
- secretRef:     # ConfigMap을 썼다면 secretRef 대신 configMapRef
    name: ocr-server-env
#  - name: TZ
#    value: Asia/Seoul
```

#### ` ocr-server/templates/service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ocr-server-service
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "ocr-server.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  selector:
    app: ocr-server
  ports:
    - protocol: TCP
      port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
```
**.Release**는 Helm이 Chart를 렌더링할 때 주입해주는 **내장 객체** 중 하나이다.
#### `ocr-server/templates/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ocr-server-deployment
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "ocr-server.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
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
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          {{- if .Values.envFrom }}
          envFrom:
            {{- toYaml .Values.envFrom | nindent 12 }}
          {{- end }}
          ports:
            - containerPort: {{ .Values.containerPort }}
          {{- if .Values.env }}
          env:
            {{- toYaml .Values.env | nindent 12 }}
          {{- end }}
          {{- if .Values.resources }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          {{- end }}
```

#### `ocr-server/templates/_helpers.tpl`
```tpl
{{- define "ocr-server.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "ocr-server.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "ocr-server.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "ocr-server.labels" -}}
app.kubernetes.io/name: {{ include "ocr-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "ocr-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ocr-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
```

## 4. CI

파이프라인 관리 상단에 `자동 실행 설정` 클릭

- 깃허브, 또는 이미지 저장소에 새로운 업데이트가 있을 때 위의 CD 파이프라인 자동 실행.
- 이미지 저장소로 설정하였을 경우 배포하는 이미지의 태그가 latest이면 태그란에 기입 필수, 배포하는 이미지의 태그가 latest가 아니라면 공란이여도 작동.

