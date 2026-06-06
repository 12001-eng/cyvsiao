from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta

def taipei_now():
    """取得台北時間 (UTC+8)"""
    return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)

db = SQLAlchemy()

class OfficeResponsibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    responsibilities = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'name': self.name,
            'responsibilities': self.responsibilities,
            'order': self.order
        }

class OfficeWorkDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False) # e.g., 'director', 'overseas', 'coop', 'collab'
    position_type = db.Column(db.String(50), nullable=True) # e.g., 'director', 'overseas_lead', 'coop_lead', 'overseas_staff', 'coop_staff'
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'position_type': self.position_type,
            'title': self.title,
            'content': self.content,
            'order': self.order
        }

class OfficeSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False) # e.g., 'overseas', 'coop'
    time_range = db.Column(db.String(100), nullable=False) # e.g., '2月 - 4月'
    task = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'time_range': self.time_range,
            'task': self.task,
            'order': self.order
        }

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=taipei_now)
    attachment_path = db.Column(db.String(300), nullable=True)
    attachment_name = db.Column(db.String(200), nullable=True)
    external_link = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tag': self.tag,
            'date': self.date.strftime('%Y-%m-%d'),
            'attachment_path': self.attachment_path,
            'attachment_name': self.attachment_name,
            'external_link': self.external_link
        }

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

# --- 關於我們 ---
class AboutStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)   # e.g. "合作企業數"
    value = db.Column(db.String(20), nullable=False)   # e.g. "45+"
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {'id': self.id, 'label': self.label, 'value': self.value, 'order': self.order}

class AboutBusiness(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {'id': self.id, 'text': self.text, 'order': self.order}

class IndexHeroStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(50), nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {'id': self.id, 'label': self.label, 'value': self.value, 'order': self.order}

class IndexFeature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'icon': self.icon,
            'title': self.title,
            'description': self.description,
            'order': self.order
        }

class AboutIntro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subtitle = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'body': self.body,
            'order': self.order
        }

# --- 招生科系 ---
class ProgramField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(10), nullable=False)        # emoji
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'icon': self.icon, 'name': self.name,
            'description': self.description, 'order': self.order
        }

# --- 建教合作方案 ---
class CoopPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.String(50), nullable=False)       # e.g. "基礎方案"
    name = db.Column(db.String(50), nullable=False)        # e.g. "一般建教合作"
    subtitle = db.Column(db.String(100), nullable=False)   # e.g. "適合中小企業"
    features = db.Column(db.Text, nullable=False)          # newline-separated items
    is_featured = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'badge': self.badge, 'name': self.name,
            'subtitle': self.subtitle, 'features': self.features,
            'is_featured': self.is_featured, 'order': self.order
        }

# --- 建教合作機構 ---
class CoopInstitution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)       # 機構名稱
    category = db.Column(db.String(50), nullable=True)     # 科別分類 (資訊科/時尚科/餐管科)
    industry = db.Column(db.String(50), nullable=True)     # 行業別
    location = db.Column(db.String(50), nullable=True)     # 所在地區
    description = db.Column(db.Text, nullable=True)        # 簡介
    logo_url = db.Column(db.String(255), nullable=True)    # LOGO 圖片路徑
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'category': self.category,
            'industry': self.industry, 'location': self.location,
            'description': self.description,
            'logo_url': self.logo_url, 'order': self.order
        }

# --- 網站設定（鍵值對）---
class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'key': self.key, 'value': self.value, 'label': self.label}

# --- 招生資格要求 ---
class AdmissionsRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(10), nullable=False)        # emoji
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'icon': self.icon, 'title': self.title,
            'description': self.description, 'order': self.order
        }

# --- 專班學程規劃步驟 ---
class ProgramStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step_num = db.Column(db.Integer, nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'step_num': self.step_num, 'tag': self.tag,
            'title': self.title, 'description': self.description, 'order': self.order
        }

# --- 學生福利卡片 ---
class StudentBenefit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(10), nullable=False)        # emoji
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'icon': self.icon, 'title': self.title,
            'description': self.description, 'order': self.order
        }


# --- 師資陣容 ---
class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    expertise = db.Column(db.String(250), nullable=True)   # 專長
    image_url = db.Column(db.String(255), nullable=True)   # 照片連結
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'expertise': self.expertise,
            'image_url': self.image_url,
            'order': self.order
        }

# --- 活動剪影 ---
class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(100), nullable=True)    # 例如：校園活動、企業參訪
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=taipei_now)
    images = db.relationship('GalleryImage', backref='gallery', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'order': self.order,
            'created_at': self.created_at.strftime('%Y-%m-%d'),
            'images': [image.to_dict() for image in self.images]
        }

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gallery_id = db.Column(db.Integer, db.ForeignKey('gallery.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0) # To maintain order of images within a gallery item

    def to_dict(self):
        return {
            'id': self.id,
            'image_url': self.image_url,
            'order': self.order
        }

class SOPPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(255), nullable=False)
    principle = db.Column(db.String(255), nullable=False)
    
    categories = db.relationship('SOPCategory', backref='sop_page', lazy=True, cascade="all, delete-orphan")
    notes = db.relationship('SOPNote', backref='sop_page', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'principle': self.principle,
            'categories': [category.to_dict() for category in sorted(self.categories, key=lambda x: x.order)],
            'notes': [note.to_dict() for note in sorted(self.notes, key=lambda x: x.order)]
        }

class SOPCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sop_page_id = db.Column(db.Integer, db.ForeignKey('sop_page.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color_class = db.Column(db.String(50), nullable=False) # e.g., "teal", "purple", "coral"
    order = db.Column(db.Integer, default=0)

    steps = db.relationship('SOPStep', backref='sop_category', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('SOPAlert', backref='sop_category', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'sop_page_id': self.sop_page_id,
            'name': self.name,
            'color_class': self.color_class,
            'order': self.order,
            'steps': [step.to_dict() for step in sorted(self.steps, key=lambda x: x.order)],
            'alerts': [alert.to_dict() for alert in sorted(self.alerts, key=lambda x: x.order)]
        }

class SOPStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sop_category_id = db.Column(db.Integer, db.ForeignKey('sop_category.id'), nullable=False)
    step_num_label = db.Column(db.String(10), nullable=False) # e.g., "1"
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsibilities = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'sop_category_id': self.sop_category_id,
            'step_num_label': self.step_num_label,
            'title': self.title,
            'description': self.description,
            'responsibilities': self.responsibilities,
            'order': self.order
        }

class SOPAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sop_category_id = db.Column(db.Integer, db.ForeignKey('sop_category.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'sop_category_id': self.sop_category_id,
            'message': self.message,
            'order': self.order
        }

class SOPNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sop_page_id = db.Column(db.Integer, db.ForeignKey('sop_page.id'), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'sop_page_id': self.sop_page_id,
            'label': self.label,
            'body': self.body,
            'order': self.order
        }

# --- 聯絡表單提交記錄 ---
class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(100), nullable=True)
    msg = db.Column(db.Text, nullable=False)
    email_sent = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=taipei_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'country': self.country,
            'type': self.type,
            'msg': self.msg,
            'email_sent': self.email_sent,
            'error_message': self.error_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# --- 網站分析記錄 (Website Analytics) ---
class VisitorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    url = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=taipei_now)
    duration = db.Column(db.Integer, default=0) # 停留時間 (秒)

    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'country': self.country,
            'url': self.url,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': self.duration
        }

# --- 招生影片 (Recruitment Videos) ---
class RecruitmentVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    youtube_url = db.Column(db.String(500), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def embed_url(self):
        import re
        url = self.youtube_url or ""
        match = re.search(r'(?:v=|youtu\.be/|embed/)([^&?]+)', url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"
        return url

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'youtube_url': self.youtube_url,
            'order': self.order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
