import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def inspect():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        print("--- Tables ---")
        cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        tables = cur.fetchall()
        for t in tables:
            print(t[0])
            
        print("\n--- Indexes ---")
        cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public';")
        indexes = cur.fetchall()
        for i in indexes:
            print(i[0])
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
