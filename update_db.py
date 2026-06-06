from app import app, db
from sqlalchemy import text

def update_db():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE news ADD COLUMN attachment_path VARCHAR(300)'))
                conn.execute(text('ALTER TABLE news ADD COLUMN attachment_name VARCHAR(200)'))
                conn.commit()
            print("Database updated successfully.")
        except Exception as e:
            print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_db()
