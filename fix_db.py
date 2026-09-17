from database import SessionLocal, Donor

db = SessionLocal()
# هيدور على أي متبرع معندوش منطقة أو معندوش فصيلة دم ويمسحه
deleted = db.query(Donor).filter((Donor.address == None) | (Donor.blood_type == None) | (Donor.address == 'nan')).delete()
db.commit()
db.close()

print(f"🧹 تم تنظيف الداتابيز بنجاح! مسحنا {deleted} متبرع بياناتهم كانت ناقصة.")