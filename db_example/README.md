# MySQL DB 접근 예시

NHN Cloud MySQL DB에 Python으로 접근하는 간단한 예시입니다.

## DB 정보

- **내부 IP**: `192.168.1.8` (Kubernetes 클러스터 내부에서 접근)
- **플로팅 IP**: `133.186.240.xxx` (외부에서 접근)
- **포트**: `3306`
- **보안 그룹**: `kpaas-contest-02-mysql-security`

## 설치

```bash
# 패키지 설치
uv pip install -r requirements.txt
```

## 설정

1. `env.template` 파일을 복사해서 `.env` 생성:
```bash
cp env.template .env
```

2. `.env` 파일에 실제 DB 정보 입력:
```env
DB_HOST=192.168.1.8    # 또는 133.186.240.xxx
DB_PORT=3306
DB_NAME=cloudbread
DB_USER=root
DB_PASSWORD=실제_비밀번호
```

## 사용법

### 1. DB 연결 테스트
```bash
python db_connection.py
```

### 2. 테이블 조회 및 쿼리 실행
```bash
python query_example.py
```

### 3. 코드에서 사용
```python
from db_connection import get_connection

# 연결 생성
conn = get_connection()

# 쿼리 실행
with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM users LIMIT 10")
    results = cursor.fetchall()
    for row in results:
        print(row)

# 연결 종료
conn.close()
```

## 주의사항

- `.env` 파일은 Git에 커밋하지 마세요 (민감 정보 포함)
- 클러스터 내부에서는 내부 IP(`192.168.1.8`) 사용
- 로컬 개발 시에는 플로팅 IP(`133.186.240.xxx`) 사용
- 보안 그룹에서 접근 허용된 IP만 연결 가능

