import os
from app import app, db
from sqlalchemy import text, inspect

def fix_db():
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('news')]
        print(f"Current columns in 'news' table: {columns}")
        
        with db.engine.connect() as conn:
            if 'attachment_path' not in columns:
                print("Adding attachment_path column...")
                conn.execute(text('ALTER TABLE news ADD COLUMN attachment_path VARCHAR(300)'))
            if 'attachment_name' not in columns:
                print("Adding attachment_name column...")
                conn.execute(text('ALTER TABLE news ADD COLUMN attachment_name VARCHAR(200)'))
            conn.commit()
        print("Database schema check completed.")

if __name__ == "__main__":
    fix_db()
