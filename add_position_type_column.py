import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

print('資料庫位置：', DB_PATH)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 檢查是否已有該欄位
try:
    c.execute("PRAGMA table_info(office_work_detail)")
    cols = [r[1] for r in c.fetchall()]
    if 'position_type' in cols:
        print('欄位 position_type 已存在，無需修改。')
    else:
        print('新增欄位 position_type 到 office_work_detail')
        c.execute('ALTER TABLE office_work_detail ADD COLUMN position_type TEXT')
        conn.commit()
        print('完成。')
except Exception as e:
    print('發生錯誤:', e)
finally:
    conn.close()
