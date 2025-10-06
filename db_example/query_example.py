from db_connection import get_connection

TABLES = [
    "food_nutrients",
    "foods",
    "health_types",
    "meal_plan_items",
    "meal_plans",
    "nutrients",
]

def print_table_rows(table_name, limit=5):
    """지정한 테이블에서 limit개 행을 조회하여 출력"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
            rows = cursor.fetchall()
            print(f"\n📄 {table_name} (최대 {limit}개):")
            if not rows:
                print("  (데이터 없음)")
            for row in rows:
                print(f"  {row}")
    except Exception as e:
        print(f"⚠️  {table_name} 테이블 조회 실패: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    for table in TABLES:
        print_table_rows(table, 5)
