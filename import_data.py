import pandas as pd
from database import SessionLocal, Donor, engine, Base

# السطر ده وظيفته يبني الجدول على النضافة لو مش موجود
Base.metadata.create_all(bind=engine)

def safe_float(value):
    if value is None: return None
    try: return float(value)
    except (ValueError, TypeError): return None

def safe_int(value):
    if value is None: return None
    try: return int(value)
    except (ValueError, TypeError): return None

def clean_blood_type(value):
    if not value or pd.isna(value): return None
    val = str(value).upper().replace(" ", "")
    if val == "A_": return "A-"
    if val == "AB+_": return "AB+"
    if val == "B+'": return "B+"
    return val

def clean_address(value):
    if not value or pd.isna(value): 
        return None
        
    # بنمسح المسافات الزيادة وبنوحد الحروف 
    val = str(value).strip()
    val = val.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه')
    
    # السكن والمغتربين
    if "سكن" in val or "سنتر" in val or "اسيوط الجديده" in val:
        if not val.startswith("اسيوط"):
            return "اسيوط - " + val
        return val
        
    # قرى ديروط
    dairut_villages = [
        "كوم بوها", "كمبوه", "ابو جبل", "ابوجبل", "ويصا", "وصيا", "ويصه", 
        "صنب", "ساو", "ظاهر", "ضاهر", "مندره", "مساره", "كودي", "ببلاو", "ديروط الشريف"
    ]
    
    is_dairut = any(village in val for village in dairut_villages)
    
    if is_dairut:
        if not val.startswith("ديروط") and not val.startswith("دديروط"):
            return "ديروط - " + val
        return val
        
    if val == "دديروط" or val == "ديررروط":
        return "ديروط"

    return val

print("جاري قراءة ملف الإكسيل...")
df = pd.read_excel("donors.xlsx")
df.columns = df.columns.str.strip()
df = df.where(pd.notnull(df), None)

db = SessionLocal()

print("جاري مسح الداتا القديمة (لو موجودة)...")
db.query(Donor).delete()
db.commit()

print("جاري إدخال البيانات المظبوطة...")
for index, row in df.iterrows():
    phone = str(row.get("رقم الهاتف")) if row.get("رقم الهاتف") else None
    if phone and phone.endswith('.0'):
        phone = phone[:-2]

    new_donor = Donor(
        id=safe_int(row.get("Donor ID")),
        name=row.get("الاسم"),
        birth_year=safe_int(row.get("سنة الميلاد")),
        phone=phone,
        address=clean_address(row.get("العنوان")),
        blood_type=clean_blood_type(row.get("الفصيلة")),
        weight=safe_float(row.get("الوزن")),
        height=safe_float(row.get("الطول")),
        notes=row.get("ملاحظات"),
        status=row.get("حالة المتبرع") if row.get("حالة المتبرع") else "متاح"
    )
    db.add(new_donor)

db.commit()
db.close()
print("تم إدخال كل المتبرعين بنجاح والداتا رجعت بتفاصيلها!")