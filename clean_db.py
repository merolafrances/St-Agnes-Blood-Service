from database import SessionLocal, Donor, BloodRequest, LoginLog

db = SessionLocal()

# مسح كل المتبرعين
db.query(Donor).delete()
# مسح كل الطلبات
db.query(BloodRequest).delete()
# مسح سجلات الدخول
db.query(LoginLog).delete()

db.commit()
db.close()

print("تم تنظيف قاعدة البيانات بنجاح، السيستم جاهز للرفع! 🚀")