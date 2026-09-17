import pandas as pd
from database import SessionLocal, Donor
import math

def clean_value(val):
    if pd.isna(val) or val == "":
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return str(val).strip()

def import_smart(file_path):
    print(f"⏳ جاري قراءة البيانات من ملف {file_path} ...")
    
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"❌ خطأ: لم يتم العثور على ملف {file_path}")
        return
        
    db = SessionLocal()
    added_count = 0
    updated_count = 0

    for index, row in df.iterrows():
        # استخراج البيانات وتنظيفها بناءً على أسماء الأعمدة في الإكسيل
        name = clean_value(row.get('الاسم'))
        phone = clean_value(row.get('رقم الهاتف'))
        blood_type = clean_value(row.get('الفصيلة'))
        address = clean_value(row.get('العنوان'))
        notes = clean_value(row.get('ملاحظات'))
        
        # تظبيط الأرقام (العمر والسنة)
        current_age = row.get('العمر الحالي')
        current_age = int(current_age) if pd.notna(current_age) else None
        
        birth_year = row.get('سنة الميلاد')
        birth_year = int(birth_year) if pd.notna(birth_year) else None

        # لو مفيش رقم تليفون، هنتجاهل السطر ده لأن التليفون هو المعرف بتاعنا
        if not phone:
            continue 

        # البحث عن المتبرع في الداتابيز
        existing_donor = db.query(Donor).filter(Donor.phone == phone).first()

        if existing_donor:
            # لو موجود، نحدث البيانات الناقصة بس (التحديث الذكي)
            updated = False
            if not existing_donor.name and name: existing_donor.name = name; updated = True
            if not existing_donor.blood_type and blood_type: existing_donor.blood_type = blood_type; updated = True
            if not existing_donor.address and address: existing_donor.address = address; updated = True
            if not existing_donor.notes and notes: existing_donor.notes = notes; updated = True
            if not existing_donor.current_age and current_age: existing_donor.current_age = current_age; updated = True
            if not existing_donor.birth_year and birth_year: existing_donor.birth_year = birth_year; updated = True
            
            if updated:
                updated_count += 1
        else:
            # لو مش موجود، نضيفه كمتبرع جديد
            new_donor = Donor(
                name=name,
                phone=phone,
                blood_type=blood_type,
                address=address,
                notes=notes,
                current_age=current_age,
                birth_year=birth_year
            )
            db.add(new_donor)
            added_count += 1

    db.commit()
    db.close()
    
    print(f"✅ تمت العملية بنجاح!")
    print(f"➕ تم إضافة {added_count} متبرع جديد.")
    print(f"🔄 تم تحديث بيانات {updated_count} متبرع حالي.")

if __name__ == "__main__":
    import_smart("new_data.xlsx")