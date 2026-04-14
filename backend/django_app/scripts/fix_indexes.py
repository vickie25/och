import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("Checking for conflicting index...")
        cur.execute("DROP INDEX IF EXISTS curriculum_tracks_slug_869ab9cd_like;")
        print("Conflicting index dropped (if it existed).")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix()
