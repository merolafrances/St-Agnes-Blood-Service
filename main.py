import io
import csv
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Donor, User, Base, BloodRequest, LoginLog
from pydantic import BaseModel
from sqlalchemy import desc
from typing import Optional
from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


# بناء الجداول لو مش موجودة
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blood Donation Service API")
app = FastAPI(title="Blood Donation Service API")

# الزقي السطر ده هنا تحتها على طول
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency للحصول على جلسة الداتابيز
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# Pydantic Models (قوالب استقبال البيانات)
# ==========================================
class BloodRequestCreate(BaseModel):
    patient_name: str
    hospital: str
    companion_phone: str
    patient_age: int
    blood_type: str
    notes: str | None = None

class StatusUpdate(BaseModel):
    last_contact: str | None = None
    contact_result: str | None = None
    last_donation: str | None = None
    notes: str | None = None
    last_called_by: str | None = None  # <--- السطر الجديد    

class LoginRequest(BaseModel):
    phone: str
    pin: str
class RegisterRequest(BaseModel):
    name: str
    phone: str
    pin: str    

from pydantic import BaseModel

# 1. الموديل اللي هيستقبل البيانات من صفحة الدخول (اسم وباسورد بس)
class UserAuth(BaseModel):
    username: str
    password: str

# 2. دالة تسجيل حساب جديد
@app.post("/api/register")
def register_user(user: UserAuth, db: Session = Depends(get_db)):
    # بندور بالاسم مش بالتليفون
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        return {"status": "error", "message": "هذا الحساب موجود بالفعل."}
    
    new_db_user = User(username=user.username, hashed_password=user.password)
    db.add(new_db_user)
    db.commit()
    return {"status": "success", "message": "تم إنشاء الحساب بنجاح"}



# ==========================================
# مسارات صفحات الويب (Frontend Routes)
# ==========================================

# الصفحة الرئيسية (صفحة تسجيل الدخول)
@app.get("/")
def serve_login_page():
    return FileResponse("login.html")

# صفحة الخدام (البحث)
@app.get("/app")
def serve_app_page():
    return FileResponse("index.html")

# صفحة الأدمن (لوحة التحكم)
@app.get("/admin")
def serve_admin_page():
    return FileResponse("admin.html")

# ==========================================
# مسارات الـ API (Backend Routes)
# ==========================================

# 1. مسار إعداد مستخدمين للتجربة
@app.get("/setup_users")
def setup_users(db: Session = Depends(get_db)):
    # حساب الأدمن (ميرولا)
    admin = db.query(User).filter(User.phone == "01000000000").first()
    if not admin:
        admin_user = User(
            name="ميرولا", 
            phone="01000000000", 
            pin="1234", 
            role="admin"
        )
        db.add(admin_user)
        
    # حساب خادم للتجربة (مي)
    volunteer = db.query(User).filter(User.phone == "01111111111").first()
    if not volunteer:
        volunteer_user = User(
            name="مي", 
            phone="01111111111", 
            pin="0000", 
            role="volunteer"
        )
        db.add(volunteer_user)
        
    db.commit()
    return {"message": "تم إنشاء الحسابات بنجاح! تقدري دلوقتي تعملي Login"}


# مسار يفتح صفحة إنشاء الحساب
@app.get("/register")
def serve_register_page():
    from fastapi.responses import FileResponse
    return FileResponse("register.html")


# مسار استلام بيانات الحساب الجديد وحفظها في الداتابيز
@app.post("/api/register")
def register_user(new_user: RegisterRequest, db: Session = Depends(get_db)):
    # نتأكد إن الرقم مش متسجل قبل كده
    existing_user = db.query(User).filter(User.phone == new_user.phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="رقم الموبايل ده متسجل بيه حساب قبل كده")
    
    # إنشاء الحساب الجديد (أوتوماتيك بينزل كخادم)
    user = User(
        name=new_user.name,
        phone=new_user.phone,
        pin=new_user.pin,
        role="volunteer"  
    )
    db.add(user)
    db.commit()
    
    return {"message": "تم إنشاء الحساب بنجاح! تقدر تسجل دخول دلوقتي"}

@app.get("/api/donors")
def get_donors(
    page: int = 1, 
    limit: int = 50, 
    blood_type: str | None = None, 
    address: str | None = None, 
    db: Session = Depends(get_db)
):
    query = db.query(Donor)
    
    # فلاتر البحث
    if blood_type:
        query = query.filter(Donor.blood_type == blood_type)
    if address:
        query = query.filter(Donor.address.contains(address))
        
    # حساب العدد الإجمالي للنتيجة
    total = query.count()
    
    # جلب البيانات بالصفحات (Pagination)
    donors = query.offset((page - 1) * limit).limit(limit).all()
    
    # إرسال البيانات في "العلب" اللي الفرونت إند مستنيها
    return {
        "total": total,
        "data": donors
    }
# مسار إحصائيات لوحة التحكم
@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_donors = db.query(Donor).count()
    contacted_donors = db.query(Donor).filter(Donor.last_contact != None).count()
    donated_donors = db.query(Donor).filter(Donor.contact_result == "تم التبرع").count()
    
    return {
        "total": total_donors,
        "contacted": contacted_donors,
        "donated": donated_donors
    }

# مسار تصدير البيانات إلى ملف CSV (إكسيل)
@app.get("/api/export")
def export_donors(db: Session = Depends(get_db)):
    donors = db.query(Donor).all()
    
    output = io.StringIO()
    # إضافة BOM عشان الإكسيل يقرأ العربي صح من غير ما الحروف تضرب
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # كتابة رأس الجدول (أسامي العواميد)
    writer.writerow([
        "الرقم التسلسلي", "الاسم", "فصيلة الدم", "المنطقة", "رقم الهاتف", 
        "تاريخ آخر تواصل", "نتيجة التواصل", "تاريخ التبرع", "الخادم المتابع", "الملاحظات"
    ])
    
    # كتابة بيانات المتبرعين
    for d in donors:
        writer.writerow([
            d.id, d.name, d.blood_type, d.address, d.phone,
            d.last_contact, d.contact_result, d.last_donation, d.last_called_by, d.notes
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=donors_export.csv"}
    )

# 4. مسار تحديث حالة المتبرع (تسجيل أو مسح المكالمة)
@app.put("/donors/{donor_id}/status")
def update_donor_status(donor_id: int, update_data: StatusUpdate, db: Session = Depends(get_db)):
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="المتبرع غير موجود")
    
    # بيحدث الداتا باللي جاي من الواجهة (سواء داتا جديدة من الخادم، أو null من الأدمن عشان يمسح)
    donor.last_contact = update_data.last_contact
    donor.contact_result = update_data.contact_result
    donor.last_donation = update_data.last_donation
    donor.notes = update_data.notes
    
        
    db.commit()
    return {"message": "تم التحديث بنجاح"}

# مسار سري لترقية حسابك ومسح الحسابات الوهمية
@app.get("/make_me_admin/{my_phone}")
def make_me_admin(my_phone: str, db: Session = Depends(get_db)):
    # 1. ترقية حسابك الحقيقي لأدمن
    real_user = db.query(User).filter(User.phone == my_phone).first()
    if not real_user:
        return {"error": "لم يتم العثور على حساب بهذا الرقم"}
    
    real_user.role = "admin"
    
    # 2. مسح الحسابات التجريبية القديمة
    dummy_admin = db.query(User).filter(User.phone == "01000000000").first()
    if dummy_admin:
        db.delete(dummy_admin)
        
    dummy_vol = db.query(User).filter(User.phone == "01111111111").first()
    if dummy_vol:
        db.delete(dummy_vol)
        
    db.commit()
    return {"message": "عاش يا هندسة! تم ترقيتك لأدمن ومسح الحسابات القديمة. اعملي Login من جديد."}

# --- كود طلبات الدم ---

class BloodRequestCreate(BaseModel):
    patient_name: str
    hospital: str
    companion_phone: str
    patient_age: int
    blood_type: str
    notes: Optional[str] = None

@app.post("/api/requests")
def create_blood_request(req: BloodRequestCreate, db: Session = Depends(get_db)):
    new_request = BloodRequest(
        patient_name=req.patient_name,
        hospital=req.hospital,
        companion_phone=req.companion_phone,
        patient_age=req.patient_age,
        blood_type=req.blood_type,
        notes=req.notes
    )
    db.add(new_request)
    db.commit()
    return {"message": "تم إرسال الطلب بنجاح", "status": "success"}

# كلاس مخصص لتحديث الطلبات عشان الإيرور 422 يختفي
class RequestStatusUpdate(BaseModel):
    status: str
    handled_by: str | None = None

# مسار تعديل حالة الطلب
@app.put("/api/requests/{request_id}/status")
def update_request_status(request_id: int, req_data: RequestStatusUpdate, db: Session = Depends(get_db)):
    req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not req:
        return {"status": "error", "message": "الطلب غير موجود"}
    
    req.status = req_data.status
    if req_data.handled_by:
        req.handled_by = req_data.handled_by
        
    db.commit()
    return {"status": "success", "message": f"تم تحديث حالة الطلب بواسطة {req.handled_by}"}

# 1. مسار لإضافة طلب جديد (ده اللي الصفحة العامة هتبعت عليه)
@app.post("/api/requests")
def create_blood_request(req: BloodRequestCreate, db: Session = Depends(get_db)):
    new_request = BloodRequest(
        patient_name=req.patient_name,
        hospital=req.hospital,
        companion_phone=req.companion_phone,
        patient_age=req.patient_age,
        blood_type=req.blood_type,
        notes=req.notes
    )
    db.add(new_request)
    db.commit()
    return {"message": "تم إرسال الطلب بنجاح", "status": "success"}

# 2. مسار لجلب الطلبات (عشان نعرضها للأدمن والخدام)
@app.get("/api/requests")
def get_blood_requests(db: Session = Depends(get_db)):
    # بنجيب الطلبات ونرتبها من الأحدث للأقدم
    requests = db.query(BloodRequest).order_by(desc(BloodRequest.created_at)).all()
    return {"data": requests}

# 3. مسار لتغيير حالة الطلب (مثلاً من عاجل لـ "تم التوفير")
@app.put("/api/requests/{request_id}/status")
def update_request_status(request_id: int, status: str, db: Session = Depends(get_db)):
    req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    req.status = status
    db.commit()
    return {"message": "تم تحديث حالة الطلب"}

from fastapi.responses import FileResponse

@app.get("/request")
def serve_request_page():
    # تأكدي إن اسم الملف request.html مكتوب صح
    return FileResponse("request.html")

from fastapi.responses import FileResponse

@app.get("/login")
def serve_login_page():
    return FileResponse("login.html")

from pydantic import BaseModel
from sqlalchemy import desc, func

# 1. موديل بيانات التسجيل والدخول
class UserCreate(BaseModel):
    username: str
    password: str

class StatusUpdate(BaseModel):
    status: str
    handled_by: str = None

from pydantic import BaseModel

# --- تعريف الموديل اللي هيستقبل البيانات من المتصفح ---
class UserAuth(BaseModel):
    username: str
    password: str

# --- مسار تسجيل حساب جديد للخادم ---
@app.post("/api/register")
def register_user(user: UserAuth, db: Session = Depends(get_db)):
    # بندور على المستخدم بالـ username مش بالـ phone
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        return {"status": "error", "message": "هذا الحساب موجود بالفعل، يرجى اختيار اسم آخر."}
    
    new_db_user = User(username=user.username, hashed_password=user.password)
    db.add(new_db_user)
    db.commit()
    return {"status": "success", "message": "تم إنشاء الحساب بنجاح."}

@app.post("/api/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    # 1. بنطابق الاسم والباسورد
    db_user = db.query(User).filter(User.username == user.username, User.hashed_password == user.password).first()
    
    if not db_user:
        return {"status": "error", "message": "بيانات الدخول غير صحيحة"}
    
    # 2. بنسجل الدخول في كراسة الحضور (LoginLog)
    new_log = LoginLog(username=db_user.username)
    db.add(new_log)
    db.commit()

    # 3. بنفتحله الباب
    return {"status": "success", "username": db_user.username}


# 4. مسار تعديل حالة الطلب (عشان يضيف اسم الخادم)
@app.put("/api/requests/{request_id}/status")
def update_request_status(request_id: int, req_data: StatusUpdate, db: Session = Depends(get_db)):
    req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not req:
        return {"status": "error", "message": "الطلب غير موجود"}
    req.status = req_data.status
    if req_data.handled_by:
        req.handled_by = req_data.handled_by
    db.commit()
    return {"status": "success", "message": f"تم تحديث حالة الطلب بواسطة {req.handled_by}"}

# 5. مسار إحصائيات الخدام (عشان يقولك كل خادم قفل كام طلب)
@app.get("/api/stats/servants")
def get_servants_stats(db: Session = Depends(get_db)):
    stats = db.query(BloodRequest.handled_by, func.count(BloodRequest.id))\
              .filter(BloodRequest.handled_by.isnot(None))\
              .group_by(BloodRequest.handled_by).all()
    return {"data": [{"servant": s[0], "count": s[1]} for s in stats]}

from fastapi.responses import FileResponse

# دي الصفحة الرئيسية اللي الناس بتطلب منها الدم
@app.get("/")
def serve_home_page():
    return FileResponse("index.html")

# دي بوابة الخدام اللي هتحطيلها الباسورد (2122021)
@app.get("/login")
def serve_login_page():
    return FileResponse("login.html")

# دي لوحة التحكم اللي فيها الجداول (صفحة الأدمن)
@app.get("/admin-panel")
def serve_admin_page():
    return FileResponse("admin.html")

@app.get("/")
@app.get("/index")
def read_index():
    return FileResponse("index.html")

# كلاس مخصص لتحديث الطلبات
class RequestStatusUpdate(BaseModel):
    status: str
    handled_by: str | None = None

# مسار تعديل حالة الطلب
@app.put("/api/requests/{request_id}/status")
def update_request_status(request_id: int, req_data: RequestStatusUpdate, db: Session = Depends(get_db)):
    req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not req:
        return {"status": "error", "message": "الطلب غير موجود"}
    
    req.status = req_data.status
    if req_data.handled_by:
        req.handled_by = req_data.handled_by
        
    db.commit()
    return {"status": "success", "message": f"تم تحديث حالة الطلب بواسطة {req.handled_by}"}

@app.get("/login_logs")
def get_login_logs(db: Session = Depends(get_db)):
    logs = db.query(LoginLog).order_by(desc(LoginLog.login_time)).all()
    
    # هنا بنترجم البيانات بإيدينا عشان السيرفر يفهمها ويبعتها صح
    result = []
    for log in logs:
        result.append({
            "username": log.username,
            "login_time": log.login_time.isoformat() if log.login_time else None
        })
        
    return {"data": result}
@app.get("/logs")
def get_logs_page():
    return FileResponse("logs.html")