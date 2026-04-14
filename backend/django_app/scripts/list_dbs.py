import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def list_dbs():
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("SELECT datname FROM pg_database;")
        dbs = cur.fetchall()
        print("--- Databases ---")
        for db in dbs:
            print(db[0])
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_dbs()
