import sqlite3

try:
    conn = sqlite3.connect('blood_service.db')
    conn.execute("ALTER TABLE donors ADD COLUMN last_called_by TEXT;")
    conn.commit()
    conn.close()
    print("تم إضافة العمود بنجاح من غير ما نمسح الداتا! 🎉")
except Exception as e:
    print("العمود موجود فعلاً أو فيه مشكلة:", e)