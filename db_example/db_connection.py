import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """MySQL DB 연결 생성"""
    return pymysql.connect(
        host=os.getenv('DB_HOST', '192.168.1.8'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME', 'cloudbread'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def test_connection():
    """DB 연결 테스트"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version")
            result = cursor.fetchone()
            print(f"✅ DB 연결 성공! MySQL Version: {result['version']}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return False


if __name__ == "__main__":
    test_connection()

