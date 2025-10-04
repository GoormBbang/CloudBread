# AI Services Kubernetes 배포

## 📁 구조

```
CloudBread/
├── chatbot/
│   ├── deployment.yaml          # Chatbot 배포
│   └── README.md
├── food_recommend/
│   ├── deployment.yaml          # Food Recommend 배포
│   └── README.md
└── ai-services-ingress.yaml     # AI 서비스 통합 Ingress
```

## 🚀 전체 배포

### 1. 네임스페이스 생성
```bash
kubectl create namespace ai-services
```

### 2. Secret 생성 (챗봇용)
```bash
kubectl create secret generic chatbot-server-env -n ai-services \
  --from-literal=GEMINI_API_KEY='your-gemini-api-key'
```

### 3. 서비스 배포
```bash
# Food Recommend 배포
kubectl apply -f food_recommend/deployment.yaml

# Chatbot 배포
kubectl apply -f chatbot/deployment.yaml

# 통합 Ingress 배포
kubectl apply -f ai-services-ingress.yaml
```

### 4. 배포 확인
```bash
kubectl get pods -n ai-services
kubectl get svc -n ai-services
kubectl get ingress -n ai-services
```

## 📋 Ingress 라우팅

| 경로 | 서비스 | 포트 |
|------|--------|------|
| `/api/food/*` | food-recommend-server-svc | 80 |
| `/api/chatbot/*` | chatbot-server-svc | 80 |

## 🌐 API 문서

- **Food Recommend**: `http://cloudbread.133.186.213.185.nip.io/api/food/docs`
- **Chatbot**: `http://cloudbread.133.186.213.185.nip.io/api/chatbot/docs`

## 🔄 개별 서비스 재배포

각 서비스 폴더의 README.md 참조:
- [Chatbot 배포 가이드](./chatbot/README.md)
- [Food Recommend 배포 가이드](./food_recommend/README.md)

