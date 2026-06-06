import os
import smtplib
import ssl
import logging
from email.message import EmailMessage
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from models import (db, OfficeResponsibility, OfficeWorkDetail, OfficeSchedule, News, Program,
                    AboutStat, AboutBusiness, IndexHeroStat, IndexFeature, AboutIntro,
                    ProgramField, CoopPackage, CoopInstitution, SiteConfig,
                    AdmissionsRequirement, ProgramStep, StudentBenefit, ContactSubmission,
                    Faculty, Gallery, GalleryImage,
                    SOPPage, SOPCategory, SOPStep, SOPAlert, SOPNote, VisitorLog, RecruitmentVideo,
                    taipei_now)
from sqlalchemy import func
import requests

from werkzeug.utils import secure_filename
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here_change_it')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'gallery'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'news'), exist_ok=True)

# SMTP Configuration
app.config['SMTP_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['SMTP_USERNAME'] = os.environ.get('SMTP_USERNAME', '37003@cyvs.tyc.edu.tw')
app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD', 'xgveulwyrpwhaksp')
app.config['EMAIL_SENDER'] = os.environ.get('EMAIL_SENDER', '37003@cyvs.tyc.edu.tw')
app.config['EMAIL_RECIPIENT'] = os.environ.get('EMAIL_RECIPIENT', '12001@CYVS.TYC.EDU.TW')

db.init_app(app)

def delete_file_if_exists(url_path):
    """Delete a file from the filesystem given its URL path (e.g. /static/uploads/...)."""
    if not url_path:
        return
    # Convert URL path to filesystem path
    rel = url_path.lstrip('/')
    full_path = os.path.join(os.path.dirname(__file__), rel)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass

# ─── Frontend Routes ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    news_items = News.query.order_by(News.date.desc()).limit(3).all()
    hero_stats = IndexHeroStat.query.order_by(IndexHeroStat.order).all()
    index_features = IndexFeature.query.order_by(IndexFeature.order).all()
    program_fields = ProgramField.query.order_by(ProgramField.order).limit(3).all()
    return render_template('index.html', news=news_items,
                           hero_stats=hero_stats,
                           index_features=index_features,
                           program_fields=program_fields)

@app.route('/about')
def about():
    stats = AboutStat.query.order_by(AboutStat.order).all()
    businesses = AboutBusiness.query.order_by(AboutBusiness.order).all()
    intros = AboutIntro.query.order_by(AboutIntro.order).all()
    return render_template('about.html', stats=stats, businesses=businesses, intros=intros)

@app.route('/office')
def office():
    responsibilities = OfficeResponsibility.query.order_by(OfficeResponsibility.order).all()
    return render_template('office.html', responsibilities=responsibilities)

@app.route('/programs')
def programs():
    program_fields = ProgramField.query.order_by(ProgramField.order).all()
    timeline_steps = ProgramStep.query.order_by(ProgramStep.order).all()
    benefits = StudentBenefit.query.order_by(StudentBenefit.order).all()
    configs = {c.key: c.value for c in SiteConfig.query.all()}
    return render_template('programs.html', program_fields=program_fields,
                           timeline_steps=timeline_steps, benefits=benefits, configs=configs)

@app.route('/videos')
def videos():
    page = request.args.get('page', 1, type=int)
    # fetch videos with pagination wrapper (8 per page)
    pagination = RecruitmentVideo.query.order_by(RecruitmentVideo.order).paginate(page=page, per_page=8, error_out=False)
    return render_template('videos.html', pagination=pagination)

@app.route('/admissions')
def admissions():
    requirements = AdmissionsRequirement.query.order_by(AdmissionsRequirement.order).all()
    configs = {c.key: c.value for c in SiteConfig.query.all()}
    return render_template('admissions.html', configs=configs, requirements=requirements)

@app.route('/cooperative')
def cooperative():
    coop_packages = CoopPackage.query.order_by(CoopPackage.order).all()
    institutions = CoopInstitution.query.order_by(CoopInstitution.order).all()
    return render_template('cooperative.html', coop_packages=coop_packages, institutions=institutions)

@app.route('/news')
def news():
    news_items = News.query.order_by(News.date.desc()).all()
    return render_template('news.html', news=news_items)

@app.route('/faculty')
def faculty():
    faculty_members = Faculty.query.order_by(Faculty.order).all()
    return render_template('faculty.html', faculty=faculty_members)

@app.route('/gallery')
def gallery():
    gallery_items = Gallery.query.order_by(Gallery.order).all()
    # Convert each Gallery item and its images to dictionaries for JSON serialization in the template
    serializable_gallery_items = []
    for item in gallery_items:
        item_dict = item.to_dict()
        # The to_dict() for Gallery already includes images as dictionaries, so no further action needed here
        serializable_gallery_items.append(item_dict)
    return render_template('gallery.html', gallery=serializable_gallery_items)

@app.route('/contact')
def contact():
    configs = {c.key: c.value for c in SiteConfig.query.all()}
    return render_template('contact.html', configs=configs)

@app.route('/sop-flowchart')
def sop_flowchart():
    sop_pages = SOPPage.query.order_by(SOPPage.id).all()
    if not sop_pages:
        abort(404)
    # Convert all pages to dict
    pages_data = [p.to_dict() for p in sop_pages]
    return render_template('sop_flowchart.html', sop_pages=pages_data)

def send_contact_email(data):
    recipient = app.config['EMAIL_RECIPIENT']
    sender = app.config['EMAIL_SENDER']
    username = app.config['SMTP_USERNAME']
    password = app.config['SMTP_PASSWORD']
    server_host = app.config['SMTP_SERVER']
    server_port = app.config['SMTP_PORT']

    # 1. Persist submission immediately
    submission = ContactSubmission(
        name=data.get('name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        country=data.get('country', ''),
        type=data.get('type', ''),
        msg=data.get('msg', ''),
        email_sent=False
    )
    
    try:
        db.session.add(submission)
        db.session.commit()
    except Exception as e:
        app.logger.error(f'Failed to record submission to DB: {e}')

    # 2. Validation
    if not username or not password or username.strip() == "" or password.strip() == "":
        error_msg = 'SMTP_USERNAME 或 SMTP_PASSWORD 尚未在 .env 檔案中設定。請參考 .env.example 並填寫您的 Gmail 帳號與「應用程式密碼」。'
        app.logger.error(error_msg)
        submission.error_message = error_msg
        db.session.commit()
        raise RuntimeError(error_msg)

    # 3. Construct Message
    message = EmailMessage()
    message['Subject'] = f"線上諮詢表單：[{data.get('type', '未指定')}] {data.get('name','')}"
    # Use the authenticated SMTP username as the From address to satisfy Gmail/Outlook
    message['From'] = username
    message['To'] = recipient
    message['Reply-To'] = data.get('email', username)
    
    body = [
        f"姓名: {data.get('name','')}",
        f"電子信箱: {data.get('email','')}",
        f"聯絡電話: {data.get('phone','')}",
        f"國籍: {data.get('country','')}",
        f"諮詢類型: {data.get('type','')}",
        '',
        '諮詢內容：',
        data.get('msg','')
    ]
    message.set_content('\n'.join(body))

    # 4. Send Email
    context = ssl.create_default_context()
    app.logger.info(f"Attempting to send email to {recipient} via {server_host}:{server_port} as {username}")
    
    try:
        with smtplib.SMTP(server_host, server_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(username, password)
            server.send_message(message)
        
        app.logger.info('Contact email sent successfully')
        submission.email_sent = True
        submission.error_message = None
        db.session.commit()
        
    except Exception as exc:
        error_detail = f"{type(exc).__name__}: {str(exc)}"
        app.logger.error(f'Error sending contact email: {error_detail}')
        submission.error_message = error_detail
        db.session.commit()
        raise

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json or {}
    required = ['name', 'email', 'type', 'msg']
    missing = [key for key in required if not data.get(key)]
    if missing:
        return jsonify({'error': '缺少必填欄位', 'fields': missing}), 400
    try:
        send_contact_email(data)
    except Exception as exc:
        return jsonify({'error': '郵件寄送失敗，請稍後再試。', 'details': str(exc)}), 500
    return jsonify({'message': '已送出，感謝您的諮詢。'})


@app.route('/api/contact-submissions', methods=['GET'])
def api_contact_submissions():
    # simple session check instead of decorator to avoid ordering issues
    if not session.get('admin_logged_in'):
        return jsonify({'error': '未授權'}), 401
    items = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

# ─── Admin Auth ───────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/login.html', error='帳號或密碼錯誤')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# ─── API: 處室業務職掌 ─────────────────────────────────────────────────────────

@app.route('/api/office', methods=['GET', 'POST'])
@login_required
def api_office():
    if request.method == 'GET':
        items = OfficeResponsibility.query.order_by(OfficeResponsibility.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = OfficeResponsibility(
        title=data['title'], name=data['name'],
        responsibilities=data['responsibilities'], order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/office/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_office_detail(id):
    item = OfficeResponsibility.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.title = data['title']
        item.name = data['name']
        item.responsibilities = data['responsibilities']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

def delete_file_if_exists(file_url):
    if file_url and file_url.startswith('/static/uploads/'):
        file_path = os.path.join(os.getcwd(), file_url.lstrip('/'))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Failed to delete file {file_path}: {e}")

# ─── API: 最新消息 ─────────────────────────────────────────────────────────────

@app.route('/api/news', methods=['GET', 'POST'])
@login_required
def api_news():
    if request.method == 'GET':
        items = News.query.order_by(News.date.desc()).all()
        return jsonify([i.to_dict() for i in items])
    
    # Handle POST with potential file upload
    title = request.form.get('title')
    content = request.form.get('content')
    tag = request.form.get('tag')
    external_link = request.form.get('external_link')
    
    item = News(title=title, content=content, tag=tag, external_link=external_link)
    
    file = request.files.get('attachment')
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        filename = secure_filename(f"news_{int(time.time())}{ext}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'news', filename)
        file.save(filepath)
        item.attachment_path = f"/static/uploads/news/{filename}"
        item.attachment_name = file.filename
        
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/news/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_news_detail(id):
    item = News.query.get_or_404(id)
    if request.method == 'PUT':
        item.title = request.form.get('title', item.title)
        item.content = request.form.get('content', item.content)
        item.tag = request.form.get('tag', item.tag)
        item.external_link = request.form.get('external_link', item.external_link)
        
        file = request.files.get('attachment')
        if file and file.filename:
            # Delete old file if exists
            if item.attachment_path:
                old_path = os.path.join(os.getcwd(), item.attachment_path.lstrip('/'))
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            ext = os.path.splitext(file.filename)[1]
            filename = secure_filename(f"news_{id}_{int(time.time())}{ext}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'news', filename)
            file.save(filepath)
            item.attachment_path = f"/static/uploads/news/{filename}"
            item.attachment_name = file.filename
            
        db.session.commit()
        return jsonify(item.to_dict())
    
    # DELETE
    if item.attachment_path:
        old_path = os.path.join(os.getcwd(), item.attachment_path.lstrip('/'))
        if os.path.exists(old_path):
            os.remove(old_path)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 關於我們 — 統計數字 ──────────────────────────────────────────────────

@app.route('/api/about-stats', methods=['GET', 'POST'])
@login_required
def api_about_stats():
    if request.method == 'GET':
        items = AboutStat.query.order_by(AboutStat.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = AboutStat(label=data['label'], value=data['value'], order=data.get('order', 0))
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/about-stats/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_about_stats_detail(id):
    item = AboutStat.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.label = data['label']
        item.value = data['value']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 關於我們 — 核心業務清單 ──────────────────────────────────────────────

@app.route('/api/about-business', methods=['GET', 'POST'])
@login_required
def api_about_business():
    if request.method == 'GET':
        items = AboutBusiness.query.order_by(AboutBusiness.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = AboutBusiness(text=data['text'], order=data.get('order', 0))
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/about-business/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_about_business_detail(id):
    item = AboutBusiness.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.text = data['text']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 首頁英雄數據 ───────────────────────────────────────────────────────────
@app.route('/api/index-hero-stats', methods=['GET', 'POST'])
@login_required
def api_index_hero_stats():
    if request.method == 'GET':
        items = IndexHeroStat.query.order_by(IndexHeroStat.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = IndexHeroStat(label=data['label'], value=data['value'], order=data.get('order', 0))
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/index-hero-stats/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_index_hero_stats_detail(id):
    item = IndexHeroStat.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.label = data['label']
        item.value = data['value']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 首頁特色說明 ─────────────────────────────────────────────────────────
@app.route('/api/index-features', methods=['GET', 'POST'])
@login_required
def api_index_features():
    if request.method == 'GET':
        items = IndexFeature.query.order_by(IndexFeature.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = IndexFeature(icon=data['icon'], title=data['title'], description=data['description'], order=data.get('order', 0))
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/index-features/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_index_features_detail(id):
    item = IndexFeature.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.icon = data['icon']
        item.title = data['title']
        item.description = data['description']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 關於我們簡介內容 ───────────────────────────────────────────────────
@app.route('/api/about-intros', methods=['GET', 'POST'])
@login_required
def api_about_intros():
    if request.method == 'GET':
        items = AboutIntro.query.order_by(AboutIntro.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = AboutIntro(
        title=data['title'], subtitle=data['subtitle'],
        body=data['body'], order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/about-intros/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_about_intros_detail(id):
    item = AboutIntro.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.title = data['title']
        item.subtitle = data['subtitle']
        item.body = data['body']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 招生科系 ─────────────────────────────────────────────────────────────

@app.route('/api/program-fields', methods=['GET', 'POST'])
@login_required
def api_program_fields():
    if request.method == 'GET':
        items = ProgramField.query.order_by(ProgramField.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = ProgramField(
        icon=data['icon'], name=data['name'],
        description=data['description'], order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/program-fields/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_program_fields_detail(id):
    item = ProgramField.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.icon = data['icon']
        item.name = data['name']
        item.description = data['description']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 建教合作方案 ─────────────────────────────────────────────────────────

@app.route('/api/coop-packages', methods=['GET', 'POST'])
@login_required
def api_coop_packages():
    if request.method == 'GET':
        items = CoopPackage.query.order_by(CoopPackage.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = CoopPackage(
        badge=data['badge'], name=data['name'], subtitle=data['subtitle'],
        features=data['features'], is_featured=data.get('is_featured', False),
        order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/coop-packages/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_coop_packages_detail(id):
    item = CoopPackage.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.badge = data['badge']
        item.name = data['name']
        item.subtitle = data['subtitle']
        item.features = data['features']
        item.is_featured = data.get('is_featured', False)
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 建教合作機構 ─────────────────────────────────────────────────────────

@app.route('/api/coop-institutions', methods=['GET', 'POST'])
@login_required
def api_coop_institutions():
    if request.method == 'GET':
        items = CoopInstitution.query.order_by(CoopInstitution.order).all()
        return jsonify([i.to_dict() for i in items])
    # POST: supports multipart form (logo upload) or JSON
    name = request.form.get('name') or (request.json or {}).get('name', '')
    category = request.form.get('category', '')
    industry = request.form.get('industry', '')
    location = request.form.get('location', '')
    description = request.form.get('description', '')
    order_val = int(request.form.get('order', 0) or (request.json or {}).get('order', 0))
    logo_url = None
    file = request.files.get('logo')
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        filename = secure_filename(f"institution_{int(time.time())}{ext}")
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'institutions'), exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'institutions', filename)
        file.save(filepath)
        logo_url = f"/static/uploads/institutions/{filename}"
    item = CoopInstitution(name=name, category=category, industry=industry, location=location,
                           description=description, logo_url=logo_url, order=order_val)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/coop-institutions/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_coop_institutions_detail(id):
    item = CoopInstitution.query.get_or_404(id)
    if request.method == 'PUT':
        item.name = request.form.get('name', item.name)
        item.category = request.form.get('category', item.category)
        item.industry = request.form.get('industry', item.industry)
        item.location = request.form.get('location', item.location)
        item.description = request.form.get('description', item.description)
        item.order = int(request.form.get('order', item.order))
        file = request.files.get('logo')
        if file and file.filename:
            delete_file_if_exists(item.logo_url)
            ext = os.path.splitext(file.filename)[1]
            filename = secure_filename(f"institution_{id}_{int(time.time())}{ext}")
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'institutions'), exist_ok=True)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'institutions', filename)
            file.save(filepath)
            item.logo_url = f"/static/uploads/institutions/{filename}"
        db.session.commit()
        return jsonify(item.to_dict())
    delete_file_if_exists(item.logo_url)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 網站設定 ─────────────────────────────────────────────────────────────

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def api_config():
    if request.method == 'GET':
        items = SiteConfig.query.all()
        return jsonify([i.to_dict() for i in items])
    # POST: batch upsert {key: value, ...}
    data = request.json
    for key, value in data.items():
        item = SiteConfig.query.filter_by(key=key).first()
        if item:
            item.value = value
        # Unknown keys from frontend are ignored (label comes from DB)
    db.session.commit()
    return jsonify({'message': 'Saved'})

# ─── API: 師資陣容 ─────────────────────────────────────────────────────────────

@app.route('/api/faculty', methods=['GET', 'POST'])
@login_required
def api_faculty():
    if request.method == 'GET':
        items = Faculty.query.order_by(Faculty.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = Faculty(
        name=data['name'], title=data['title'],
        description=data.get('description', ''),
        expertise=data.get('expertise', ''),
        image_url=data.get('image_url', ''),
        order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/faculty/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_faculty_detail(id):
    item = Faculty.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.name = data['name']
        item.title = data['title']
        item.description = data.get('description', item.description)
        item.expertise = data.get('expertise', item.expertise)
        item.image_url = data.get('image_url', item.image_url)
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 處室詳細職掌 ─────────────────────────────────────────────────────────

@app.route('/api/office/work-detail', methods=['GET', 'POST'])
@login_required
def api_office_work_detail():
    if request.method == 'GET':
        items = OfficeWorkDetail.query.order_by(OfficeWorkDetail.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = OfficeWorkDetail(
        category=data['category'],
        title=data['title'],
        content=data['content'],
        order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/office/work-detail/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_office_work_detail_id(id):
    item = OfficeWorkDetail.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.category = data['category']
        item.title = data['title']
        item.content = data['content']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 處室時程規劃 ─────────────────────────────────────────────────────────

@app.route('/api/office/schedule', methods=['GET', 'POST'])
@login_required
def api_office_schedule():
    if request.method == 'GET':
        items = OfficeSchedule.query.order_by(OfficeSchedule.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = OfficeSchedule(
        category=data['category'],
        time_range=data['time_range'],
        task=data['task'],
        order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/office/schedule/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_office_schedule_id(id):
    item = OfficeSchedule.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.category = data['category']
        item.time_range = data['time_range']
        item.task = data['task']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 招生影片 ─────────────────────────────────────────────────────────────

@app.route('/api/videos', methods=['GET', 'POST'])
@login_required
def api_videos():
    if request.method == 'GET':
        items = RecruitmentVideo.query.order_by(RecruitmentVideo.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = RecruitmentVideo(
        title=data.get('title', ''),
        description=data.get('description', ''),
        youtube_url=data.get('youtube_url', ''),
        order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/videos/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_videos_detail(id):
    item = RecruitmentVideo.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.title = data.get('title', item.title)
        item.description = data.get('description', item.description)
        item.youtube_url = data.get('youtube_url', item.youtube_url)
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 活動剪影 ─────────────────────────────────────────────────────────────

@app.route('/api/gallery', methods=['GET', 'POST'])
@login_required
def api_gallery():
    if request.method == 'GET':
        items = Gallery.query.order_by(Gallery.order).all()
        return jsonify([i.to_dict() for i in items])
    
    # Handle new gallery item with multiple file uploads
    if request.method == 'POST':
        title = request.form.get('title', '未命名活動')
        description = request.form.get('description', '')
        category = request.form.get('category', '')
        order_base = int(request.form.get('order', 0))

        # Create the main Gallery item
        gallery_item = Gallery(
            title=title,
            description=description,
            category=category,
            order=order_base
        )
        db.session.add(gallery_item)
        db.session.flush() # Flush to get the gallery_item.id

        files = request.files.getlist('images')
        if not files or all(not file.filename for file in files):
            db.session.rollback() # Rollback the gallery_item creation
            return jsonify({'error': '未選擇任何圖片'}), 400

        for i, file in enumerate(files):
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = secure_filename(f"gallery_{int(time.time())}_{i}{ext}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'gallery', filename)
                file.save(filepath)
                
                image_url = f"/static/uploads/gallery/{filename}"
                gallery_image = GalleryImage(
                    gallery_id=gallery_item.id,
                    image_url=image_url,
                    order=i # Or use a more sophisticated ordering if needed
                )
                db.session.add(gallery_image)
        
        db.session.commit()
        return jsonify(gallery_item.to_dict())

@app.route('/api/gallery/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_gallery_detail(id):
    item = Gallery.query.get_or_404(id)
    if request.method == 'PUT':
        item.title = request.form.get('title', item.title)
        item.description = request.form.get('description', item.description)
        item.category = request.form.get('category', item.category)
        item.order = int(request.form.get('order', item.order))

        # Handle new image uploads
        new_files = request.files.getlist('images')
        for i, file in enumerate(new_files):
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = secure_filename(f"gallery_{int(time.time())}_{id}_{i}{ext}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'gallery', filename)
                file.save(filepath)
                image_url = f"/static/uploads/gallery/{filename}"
                gallery_image = GalleryImage(
                    gallery_id=item.id,
                    image_url=image_url,
                    order=len(item.images) + i # Append to existing images
                )
                db.session.add(gallery_image)
        
        # Handle image deletions
        deleted_image_ids = request.form.getlist('deleted_image_ids')
        for image_id in deleted_image_ids:
            img_to_delete = GalleryImage.query.get(image_id)
            if img_to_delete and img_to_delete.gallery_id == item.id:
                delete_file_if_exists(img_to_delete.image_url)
                db.session.delete(img_to_delete)

        db.session.commit()
        return jsonify(item.to_dict())
    
    # For DELETE request
    for image in item.images:
        delete_file_if_exists(image.image_url)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 僑生危機處理 SOP 流程圖 ──────────────────────────────────────────────

@app.route('/api/sop-page', methods=['GET', 'POST'])
@login_required
def api_sop_page():
    if request.method == 'GET':
        sop_pages = SOPPage.query.order_by(SOPPage.id).all()
        return jsonify([p.to_dict() for p in sop_pages])
    
    data = request.json
    # Create SOPPage
    sop_page = SOPPage(
        title=data['title'],
        subtitle=data['subtitle'],
        principle=data['principle']
    )
    db.session.add(sop_page)
    db.session.flush() # Get ID for relationships

    # Add categories, steps, alerts
    for cat_data in data.get('categories', []):
        category = SOPCategory(
            sop_page_id=sop_page.id,
            name=cat_data['name'],
            color_class=cat_data['color_class'],
            order=cat_data.get('order', 0)
        )
        db.session.add(category)
        db.session.flush()

        for step_data in cat_data.get('steps', []):
            step = SOPStep(
                sop_category_id=category.id,
                step_num_label=step_data['step_num_label'],
                title=step_data['title'],
                description=step_data['description'],
                responsibilities=step_data['responsibilities'],
                order=step_data.get('order', 0)
            )
            db.session.add(step)
        
        for alert_data in cat_data.get('alerts', []):
            alert = SOPAlert(
                sop_category_id=category.id,
                message=alert_data['message'],
                order=alert_data.get('order', 0)
            )
            db.session.add(alert)

    # Add notes
    for note_data in data.get('notes', []):
        note = SOPNote(
            sop_page_id=sop_page.id,
            label=note_data['label'],
            body=note_data['body'],
            order=note_data.get('order', 0)
        )
        db.session.add(note)

    db.session.commit()
    return jsonify(sop_page.to_dict())

@app.route('/api/sop-page/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_sop_page_detail(id):
    sop_page = SOPPage.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify(sop_page.to_dict())

    if request.method == 'PUT':
        data = request.json
        sop_page.title = data['title']
        sop_page.subtitle = data['subtitle']
        sop_page.principle = data['principle']

        # Update categories, steps, alerts (simplified: delete all and recreate)
        for category in sop_page.categories:
            db.session.delete(category)
        for note in sop_page.notes:
            db.session.delete(note)
        db.session.flush()

        for cat_data in data.get('categories', []):
            category = SOPCategory(
                sop_page_id=sop_page.id,
                name=cat_data['name'],
                color_class=cat_data['color_class'],
                order=cat_data.get('order', 0)
            )
            db.session.add(category)
            db.session.flush()

            for step_data in cat_data.get('steps', []):
                step = SOPStep(
                    sop_category_id=category.id,
                    step_num_label=step_data['step_num_label'],
                    title=step_data['title'],
                    description=step_data['description'],
                    responsibilities=step_data['responsibilities'],
                    order=step_data.get('order', 0)
                )
                db.session.add(step)
            
            for alert_data in cat_data.get('alerts', []):
                alert = SOPAlert(
                    sop_category_id=category.id,
                    message=alert_data['message'],
                    order=alert_data.get('order', 0)
                )
                db.session.add(alert)
        
        for note_data in data.get('notes', []):
            note = SOPNote(
                sop_page_id=sop_page.id,
                label=note_data['label'],
                body=note_data['body'],
                order=note_data.get('order', 0)
            )
            db.session.add(note)

        db.session.commit()
        return jsonify(sop_page.to_dict())

    if request.method == 'DELETE':
        db.session.delete(sop_page)
        db.session.commit()
        return jsonify({'message': 'Deleted'})




# ─── API: 招生資格要求 ─────────────────────────────────────────────────────────

@app.route('/api/admissions-requirements', methods=['GET', 'POST'])
@login_required
def api_admissions_requirements():
    if request.method == 'GET':
        items = AdmissionsRequirement.query.order_by(AdmissionsRequirement.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = AdmissionsRequirement(
        icon=data['icon'], title=data['title'],
        description=data['description'], order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/admissions-requirements/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_admissions_requirements_detail(id):
    item = AdmissionsRequirement.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.icon = data['icon']
        item.title = data['title']
        item.description = data['description']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 專班學程規劃步驟 ─────────────────────────────────────────────────────

@app.route('/api/program-steps', methods=['GET', 'POST'])
@login_required
def api_program_steps():
    if request.method == 'GET':
        items = ProgramStep.query.order_by(ProgramStep.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = ProgramStep(
        step_num=data['step_num'], tag=data['tag'], title=data['title'],
        description=data['description'], order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/program-steps/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_program_steps_detail(id):
    item = ProgramStep.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.step_num = data['step_num']
        item.tag = data['tag']
        item.title = data['title']
        item.description = data['description']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 學生福利卡片 ─────────────────────────────────────────────────────────

@app.route('/api/student-benefits', methods=['GET', 'POST'])
@login_required
def api_student_benefits():
    if request.method == 'GET':
        items = StudentBenefit.query.order_by(StudentBenefit.order).all()
        return jsonify([i.to_dict() for i in items])
    data = request.json
    item = StudentBenefit(
        icon=data['icon'], title=data['title'],
        description=data['description'], order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/student-benefits/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_student_benefits_detail(id):
    item = StudentBenefit.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        item.icon = data['icon']
        item.title = data['title']
        item.description = data['description']
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify(item.to_dict())
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── API: 網站分析 (Analytics) ───────────────────────────────────────────────────

def get_country_from_ip(ip):
    if not ip or ip in ('127.0.0.1', 'localhost', '::1'):
        return '臺灣 (Local)'
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == 'success':
                return data.get('country')
    except Exception as e:
        app.logger.warning(f"Error fetching IP country logic: {e}")
    return 'Unknown'

@app.route('/api/analytics/visit', methods=['POST'])
def api_analytics_visit():
    data = request.get_json(force=True, silent=True) or {}
    url = data.get('url', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    # Check if this IP recently created a log to cache country
    recent = VisitorLog.query.filter_by(ip_address=ip).order_by(VisitorLog.timestamp.desc()).first()
    country = recent.country if recent and recent.country != 'Unknown' else get_country_from_ip(ip)

    log = VisitorLog(ip_address=ip, country=country, url=url)
    db.session.add(log)
    db.session.commit()
    return jsonify({'visit_id': log.id}), 201

@app.route('/api/analytics/duration', methods=['POST'])
def api_analytics_duration():
    data = request.get_json(force=True, silent=True) or {}
    visit_id = data.get('visit_id')
    duration = data.get('duration', 0)
    if visit_id:
        log = VisitorLog.query.get(visit_id)
        if log:
            log.duration = int(duration)
            db.session.commit()
            return jsonify({'status': 'ok'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/analytics/stats', methods=['GET'])
@login_required
def api_analytics_stats():
    from datetime import datetime, timedelta
    now = taipei_now()
    thirty_days_ago = now - timedelta(days=30)
    
    # Using SQLite strftime to group by date
    daily_visitors_query = db.session.query(
        func.strftime('%Y-%m-%d', VisitorLog.timestamp).label('date'),
        func.count(func.distinct(VisitorLog.ip_address))
    ).filter(VisitorLog.timestamp >= thirty_days_ago).group_by('date').order_by('date').all()
    
    top_pages_query = db.session.query(
        VisitorLog.url, func.count(VisitorLog.id).label('views')
    ).group_by(VisitorLog.url).order_by(db.text('views DESC')).limit(10).all()

    countries_query = db.session.query(
        VisitorLog.country, func.count(VisitorLog.id).label('count')
    ).group_by(VisitorLog.country).order_by(db.text('count DESC')).all()

    avg_duration = db.session.query(func.avg(VisitorLog.duration)).scalar() or 0

    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_visitors = db.session.query(func.count(func.distinct(VisitorLog.ip_address))).filter(VisitorLog.timestamp >= first_day_of_month).scalar() or 0

    twenty_days_ago = now - timedelta(days=20)
    recent_logs_query = VisitorLog.query.filter(
        VisitorLog.timestamp >= twenty_days_ago
    ).order_by(VisitorLog.timestamp.desc()).all()
    recent_logs = [log.to_dict() for log in recent_logs_query]

    return jsonify({
        'daily_visitors': [{'date': r[0], 'count': r[1]} for r in daily_visitors_query],
        'top_pages': [{'url': r[0], 'views': r[1]} for r in top_pages_query],
        'countries': [{'country': r[0] or 'Unknown', 'count': r[1]} for r in countries_query],
        'avg_duration': round(float(avg_duration), 1),
        'monthly_visitors': monthly_visitors,
        'recent_logs': recent_logs
    })

# ─── Bootstrap ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # --- 原有種子資料 ---
        if not OfficeResponsibility.query.first():
            db.session.add(OfficeResponsibility(title='主任', name='王大明',
                responsibilities='綜理處室業務\n規劃國際交流專案', order=1))
            db.session.add(OfficeResponsibility(title='組長', name='李小華',
                responsibilities='辦理僑生專班招生\n輔導學生在台生活', order=2))
        if not News.query.first():
            db.session.add(News(title='112學年度僑生專班熱烈招生中',
                content='歡迎東南亞僑生踴躍報名...', tag='招生快訊'))

        # --- 關於我們 — 統計數字 ---
        if not AboutStat.query.first():
            for order, label, value in [
                (1, '合作企業數', '45+'),
                (2, '畢業就業率', '95%'),
                (3, '年均招生人數', '80+'),
            ]:
                db.session.add(AboutStat(label=label, value=value, order=order))

        # --- 關於我們 — 核心業務清單 ---
        if not AboutBusiness.query.first():
            businesses = [
                '東南亞 3+4 產學攜手合作僑生專班辦理',
                '僑生建教合作業務媒合與管理',
                '海外招生說明暨赴境參訪活動',
                '僑生入學輔導、學習追蹤與生涯規劃',
                '國際合作備忘錄 (MOU) 簽訂與執行',
                '師資培訓、僑生華語輔導課程',
                '企業端建教合作契約洽談與管理',
                '政府及僑委會計畫申請與核銷',
            ]
            for i, text in enumerate(businesses, 1):
                db.session.add(AboutBusiness(text=text, order=i))

        # --- 首頁英雄數據 ---
        if not IndexHeroStat.query.first():
            hero_items = [
                ('合作國家', '6', 1),
                ('在校僑生', '150+', 2),
                ('合作企業', '45+', 3),
                ('辦學年數', '12 年', 4),
            ]
            for label, value, order in hero_items:
                db.session.add(IndexHeroStat(label=label, value=value, order=order))

        # --- 首頁特色說明 ---
        if not IndexFeature.query.first():
            features = [
                ('🎓', '完整學程規劃', '3+4 七年一貫學程，結合學科與實務，為海外僑生打造職涯全方位學習路徑。', 1),
                ('🏭', '產學攜手合作', '與優質企業合作實習、勞動保障與薪資補貼並重。', 2),
                ('🏠', '完善生活輔導', '提供宿舍、華語生活輔導與行政支援，讓僑生在台安心學習與生活。', 3),
            ]
            for icon, title, desc, order in features:
                db.session.add(IndexFeature(icon=icon, title=title, description=desc, order=order))

        # --- 關於我們簡介 ---
        if not AboutIntro.query.first():
            db.session.add(AboutIntro(
                title='培育雙語技術人才',
                subtitle='為僑生創造最佳學習與就業環境',
                body='啟英高中國際處成立以來，致力推動東南亞僑生教育，透過嚴謹的課程規劃與產業合作，\n培育具備雙語能力及職業技術的優秀人才，為僑生在台灣創造最佳學習與就業環境。',
                order=1
            ))

        # --- 招生科系 ---
        if not ProgramField.query.first():
            fields = [
                ('⚙️', '機械製造', 'CNC 加工、精密機械製造、模具製造，結合國內一流科技製造業建教實習。', 1),
                ('🔌', '電機工程', '工業配電、自動控制、PLC程式編輯與電控維修，對接自動化製造廠。', 2),
                ('🍽️', '餐飲管理', '中西餐烹調技術、烘焙食品與餐廳經營管理，媒合知名餐飲集團。', 3),
                ('💻', '資訊科技', '電腦網路架設、微處理器控制、程式設計基礎，對接高科技組裝廠。', 4),
                ('🏨', '觀光旅遊', '旅遊景點規劃、觀光導覽、飯店前台管理，對接星級旅館與度假村。', 5),
                ('💄', '美容美髮', '時尚美髮造型、彩妝設計、美容美體保養，對接知名連鎖美髮沙龍。', 6),
            ]
            for icon, name, desc, order in fields:
                db.session.add(ProgramField(icon=icon, name=name, description=desc, order=order))

        # --- 建教合作方案 ---
        if not CoopPackage.query.first():
            packages = [
                ('基礎方案', '一般建教合作', '適合中小企業',
                 '提供 1–5 名技術學員\n標準週輪調或學期輪調制\n專責老師定期到廠關懷\n學校協辦全套入境與工作證手續\n畢業後提供一般求職媒合',
                 False, 1),
                ('推薦方案', '深度夥伴合作', '適合中大型及製造服務業',
                 '提供 6–20 名技術學員\n共同客製化校內術科培訓課程\n引進企業「師徒制」在廠指導\n合作開展品牌聯合招生宣傳\n優先爭取教育部與僑委會政策補貼\n免費提供東南亞市場布局諮詢',
                 True, 2),
                ('旗艦方案', '策略聯盟合作', '適合集團型及跨國企業',
                 '提供 20 名以上技術學員\n獨立專班式客製化課程與學分對接\n企業招牌與精神標識進駐校內宣傳\n簽立校級策略聯盟合作備忘錄(MOU)\n優先對接科大端大專院校產學資源',
                 False, 3),
            ]
            for badge, name, subtitle, features, is_featured, order in packages:
                db.session.add(CoopPackage(
                    badge=badge, name=name, subtitle=subtitle,
                    features=features, is_featured=is_featured, order=order
                ))

        # --- 網站設定 ---
        if not SiteConfig.query.first():
            configs = [
                ('contact_address', '桃園市中壢區吉林路38號 啟英高中 國際處', '學校地址'),
                ('contact_phone', '+886-3-4523036 轉 國際事務處', '聯絡電話'),
                ('contact_email', 'international@cyvs.tyc.edu.tw', '電子信箱'),
                ('contact_hours', '週一至週五 08:00 – 17:00 (例假日除外)', '服務時間'),
                ('contact_line', '@cyvs_international — 僑生線上諮詢第一優先管道', 'LINE 官方帳號'),
                ('admissions_schedule',
                 '每年 1–3 月辦理海外招生宣傳說明會，5 月底截止報名申請，7–8 月進行資格審查並核發通知，9 月正式入學開學。',
                 '📅 重要時程'),
                ('admissions_documents',
                 '護照影本、近三個月戶籍謄本（中文）、國中成績單與畢業證書（需經駐外單位驗證）、近期照片2張、健康檢查證明書。',
                 '📄 必備文件'),
                ('admissions_fees',
                 '高職期間享有免學費補助。雜費與書籍費可由政府相關補助支付。建教實習期間的薪資補貼可用於負擔全額生活費用。',
                 '💳 費用說明'),
                ('program_salary', 'NT$ 27,470 起 (依基本工資調整)', '每月薪資補貼'),
            ]
            for key, value, label in configs:
                db.session.add(SiteConfig(key=key, value=value, label=label))

        # --- 招生資格要求 ---
        if not AdmissionsRequirement.query.first():
            reqs = [
                ('🌏', '國籍資格', '持有中華民國國籍（海外護照/無戶籍國民），或父母一方具備中華民國國籍且在東南亞出生或長年居住之華裔青年。', 1),
                ('📚', '學歷要求', '完成當地國中（初中）九年義務教育同等學力，且持有當地學校核發之正式畢業證書與完整成績單正本。', 2),
                ('🔢', '年齡條件', '入學年度當年 9 月 1 日前需年滿 15 歲，且原則上未超過 18 歲（特殊情形需陳報教育部專案核准後辦理）。', 3),
            ]
            for icon, title, desc, order in reqs:
                db.session.add(AdmissionsRequirement(icon=icon, title=title, description=desc, order=order))

        # --- 專班學程規劃步驟 ---
        if not ProgramStep.query.first():
            steps = [
                (1, '高一 — 海外招生', '海外招募與入台準備', '由本校國際處前往東南亞各地辦理招生說明會，協助學生辦理入學申請、健康檢查、護照及相關入境文件。', 1),
                (2, '高一至高二 — 基礎學習', '專業基礎課程 + 建教實習', '結合學科課程與職場實習，學生以週輪調方式，在校學習與企業實習交替進行，快速建立職業技能。', 2),
                (3, '高三 — 深化實務', '深化實習 + 升學輔導', '增加實習比重，同時準備技術士證照考試及大學技術院校入學，國際處全程協助升學申請流程。', 3),
                (4, '大學四年', '技術院校四年學程', '銜接合作之技術學院或科技大學，取得學士學位，持續深化職業技能，同步享有合法打工及實習機會。', 4),
                (5, '畢業後', '就業媒合 / 返鄉發展', '七年完整學程畢業後，可選擇留台就業（合作企業優先錄用，通過評估可轉為正式白領白卡身分）或返鄉發展。', 5),
            ]
            for step_num, tag, title, desc, order in steps:
                db.session.add(ProgramStep(step_num=step_num, tag=tag, title=title, description=desc, order=order))

        # --- 學生福利特色卡片 ---
        if not StudentBenefit.query.first():
            benefits = [
                ('💰', '建教薪資收入保障', '建教輪調實習期間，每月享有生活津貼，標準不低於台灣勞動部核定之基本工資，保障在台就學基本生活所需。', 1),
                ('🏠', '完善宿舍與起居照顧', '學校提供安全、設備完善的校內宿舍，並有生輔老師24小時專責管理與陪伴，定期舉辦健康檢測與節慶聚會。', 2),
                ('📖', '華語補救與學科強化', '針對入學新生提供免費的線上與實體華語補救課程，協助快速適應中文授課環境與台灣日常生活交流。', 3),
                ('🏥', '全民健保與醫療協助', '入台註冊後即協助申辦加入健保，享有在台全程醫療保障。學生有病痛或緊急就醫時，由導師與宿管全程協助陪伴。', 4),
                ('🎓', '無憂升學與升學對接', '國際處專業升學輔導團隊，於高三階段協助備妥各項直升對接科技大學的文件與行政手續，直升管道通暢無虞。', 5),
                ('✈️', '入出境與證照行政服務', '入台簽證申請、居留證（ARC）延期、工作許可證的展延與申辦，均由國際處單一窗口專人收件代辦，免除繁瑣流程。', 6),
            ]
            for icon, title, desc, order in benefits:
                db.session.add(StudentBenefit(icon=icon, title=title, description=desc, order=order))

        # --- 僑生危機處理SOP流程圖 種子資料 ---
        if not SOPPage.query.first():
            sop_page = SOPPage(
                title="僑生危機事件處置標準作業程序（SOP）",
                subtitle="產學攜手合作僑生專班・學生管理與危機處理手冊",
                principle="核心原則：安全第一・輔導優先・紀律導正"
            )
            db.session.add(sop_page)
            db.session.flush()

            # Category 1: 校內事件
            cat_teal = SOPCategory(
                sop_page_id=sop_page.id, name="一、校內事件", color_class="teal", order=1
            )
            db.session.add(cat_teal)
            db.session.flush()
            db.session.add_all([
                SOPStep(
                    sop_category_id=cat_teal.id, step_num_label="1", title="發現與確認",
                    description="宿舍老師（舍監）每日定時查房點名，發現學生無故未歸、酗酒、鬥毆或違規使用電器等事實。",
                    responsibilities="宿舍老師・僑生組・生輔組", order=1
                ),
                SOPStep(
                    sop_category_id=cat_teal.id, step_num_label="2", title="即時通報",
                    description="第一時間通報生輔組長、校安、僑生組及專班導師；若涉及受傷則立即送醫，涉及違法行為則通報轄區警政單位。",
                    responsibilities="宿舍老師・僑生組・生輔組", order=2
                ),
                SOPStep(
                    sop_category_id=cat_teal.id, step_num_label="3", title="聯繫與紀錄",
                    description="僑生組及專班導師應立即聯繫海外家長說明情況。行政人員須詳實填寫「案件處理單」並記錄事件經過。",
                    responsibilities="專班導師・行政窗口", order=3
                ),
                SOPStep(
                    sop_category_id=cat_teal.id, step_num_label="4", title="懲處與輔導",
                    description="依《學生宿舍生活公約》執行懲處（如愛舍服務、校規處分）。轉介輔導組建立 A、B 輔導卡，實施諮商。",
                    responsibilities="生輔組・僑生組・獎懲委員會・輔導室", order=4
                ),
            ])

            # Category 2: 校外／實習事件
            cat_purple = SOPCategory(
                sop_page_id=sop_page.id, name="二、校外／實習事件", color_class="purple", order=2
            )
            db.session.add(cat_purple)
            db.session.flush()
            db.session.add_all([
                SOPStep(
                    sop_category_id=cat_purple.id, step_num_label="1", title="廠家通報",
                    description="學生於實習崗位發生偏差行為（如酗酒影響工作、無故缺職），廠商「業師」立即通知駐廠輔導老師。",
                    responsibilities="合作機構負責人員・駐廠輔導老師", order=1
                ),
                SOPStep(
                    sop_category_id=cat_purple.id, step_num_label="2", title="實地訪視",
                    description="駐廠老師每 2 週至少一次至現場瞭解狀況，並作成訪視紀錄。若涉及勞資爭議，需啟動協調機制。",
                    responsibilities="駐廠輔導老師・建教組", order=2
                ),
                SOPStep(
                    sop_category_id=cat_purple.id, step_num_label="3", title="處置與轉安置",
                    description="若因行為偏差遭「退廠」，學校應啟動「回校加強關懷輔導訓練」，並評估是否「轉安置」至其他廠商。",
                    responsibilities="建教組・建教合作委員會", order=3
                ),
                SOPStep(
                    sop_category_id=cat_purple.id, step_num_label="4", title="重大事故報備",
                    description="發生重大校外事故時，啟動「僑務委員會僑生僑護緊急聯絡系統」通報僑委會。",
                    responsibilities="國際處・僑生組", order=4
                ),
            ])

            # Category 3: 特殊事件
            cat_coral = SOPCategory(
                sop_page_id=sop_page.id, name="三、特殊事件", color_class="coral", order=3
            )
            db.session.add(cat_coral)
            db.session.flush()
            db.session.add_all([
                SOPStep(
                    sop_category_id=cat_coral.id, step_num_label="1", title="行蹤不明（潛逃）",
                    description="發現失聯超過 24 小時，除聯繫家長與推薦單位，應立即報警，並通報內政部移民署與僑務委員會。",
                    responsibilities="僑生組・生輔組", order=1
                ),
                SOPStep(
                    sop_category_id=cat_coral.id, step_num_label="2", title="非法工作",
                    description="發現從事與簽證目的不符或非法打工（如逾時工讀），應給予法規再教育並通報勞政機關。情節嚴重者撤銷學籍。",
                    responsibilities="僑生組・教務處", order=2
                ),
                SOPStep(
                    sop_category_id=cat_coral.id, step_num_label="3", title="學籍中止（退學）",
                    description="學生若因學業／操行不及格或違反校規遭「退學」，學校應即發函通知，其僑生身分於退學後即刻中止。",
                    responsibilities="僑生組・註冊組", order=3
                ),
                SOPStep(
                    sop_category_id=cat_coral.id, step_num_label="4", title="辦理出境",
                    description="中止僑生身分或撤銷學籍之學生，必須立即自費返回原居留地，不得在台居留。",
                    responsibilities="僑生組・僑委會・移民署", order=4
                ),
            ])
            db.session.add(SOPAlert(
                sop_category_id=cat_coral.id, message="緊急通報：立即聯繫移民署與僑委會，啟動僑護緊急聯絡系統", order=1
            ))

            db.session.add_all([
                SOPNote(
                    sop_page_id=sop_page.id, label="身分警告",
                    body="僑生身分以「就學」為前提。一旦因違反校規遭退學，將無法重新申請回國就學。", order=1
                ),
                SOPNote(
                    sop_page_id=sop_page.id, label="輔導機制",
                    body="配合「親師認輔」機制，請輔導室協助學生減輕思鄉壓力與文化衝擊，從根本預防危機發生。", order=2
                ),
                SOPNote(
                    sop_page_id=sop_page.id, label="紀錄完整性",
                    body="所有處置歷程、會議紀錄、家長意見及改善情形（如「案件處理單」），均需妥善保存備查，以應對建教考核與評鑑。", order=3
                ),
            ])

        # --- 師資陣容 ---
        if not Faculty.query.first():
            members = [
                ('王主任', '國際事務處主任', '負責國際交流專案規劃與僑生招生政策。', '教育管理、國際交流', '', 1),
                ('李老師', '僑生輔導組長', '輔導僑生在台生活與學習，協助適應環境。', '學生輔導、華語教學', '', 2),
                ('張師傅', '建教合作導師', '對接企業實習端，技術指導與實習追蹤。', '機械製造、職業安全', '', 3),
            ]
            for name, title, desc, exp, img, order in members:
                db.session.add(Faculty(name=name, title=title, description=desc, expertise=exp, image_url=img, order=order))

        # --- 活動剪影 ---
        if not Gallery.query.first():
            gallery_items = [
                ('僑生春節祭祖活動', '每年春節前夕舉辦祭祖大典，傳承中華文化。', 'https://images.unsplash.com/photo-1528495612343-9ca9f4a4de28?q=80&w=1000', '校園活動', 1),
                ('企業參訪 - 科技大廠', '帶領建教班學生實地走訪合作企業，瞭解職場環境。', 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=1000', '企業參訪', 2),
                ('華語演講比賽', '鼓勵僑生展現華語學習成果，提升自信心。', 'https://images.unsplash.com/photo-1475721027785-f74eccf877e2?q=80&w=1000', '學術競賽', 3),
            ]
            for title, desc, img, cat, order in gallery_items:
                db.session.add(Gallery(title=title, description=desc, image_url=img, category=cat, order=order))

        db.session.commit()

    app.run(debug=True, host='0.0.0.0', port=8510)
