from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import markdown
from pymdownx import superfences, highlight, tilde, caret, mark, betterem, details
from datetime import datetime, timedelta, timezone
import re, random

app = Flask(__name__)

# 固定 SECRET_KEY
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'error-wiki-secret-key-2024-dev-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///errors.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Login 配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '🔐 请先登录'
login_manager.remember_cookie_duration = timedelta(days=365)
login_manager.session_protection = 'strong'

# Session 配置
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=365)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

db = SQLAlchemy(app)

# ========== Markdown 转换器 ==========
md = markdown.Markdown(extensions=[
    'extra',                    # 表格、代码块、脚注
    'toc',                      # 目录
    'tables',                   # 表格增强
    'fenced_code',              # 围栏代码块
    
    # ====== 扩展 ======
    'pymdownx.superfences',     # 嵌套代码块
    'pymdownx.highlight',       # 代码高亮
    'pymdownx.tilde',           # ~~删除线~~ 和 ~下标~
    'pymdownx.caret',           # ^上标^
    'pymdownx.mark',            # ==高亮==
    'pymdownx.betterem',        # 更智能的粗斜体
    'pymdownx.details',         # ??? 折叠块 ???
    'pymdownx.inlinehilite',    # 行内代码高亮 `#!python print(1)`
    'pymdownx.keys',            # 键盘按键 ++ctrl+alt+del++
    'pymdownx.emoji',           # :smile: → 😊
    'pymdownx.magiclink',       # 自动识别链接
    'pymdownx.tasklist',        # 任务列表 - [ ] 
    'pymdownx.tabbed',          # 添加标签页支持
    
    'attr_list',                # {: style="color: red" }
    'md_in_html',               # Markdown 内嵌 HTML
])

def render_custom_tabs(content):
    """将 ;;; tab xxx 语法转换为 HTML 标签页"""
    if not content:
        return content
    
    # 匹配 ;;; tab 标题和内容
    pattern = r';;; tab (.+?)\n(.*?)(?=\n;;; tab |$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        return content
    
    # 生成唯一 ID
    tab_id = f"tab-{random.randint(1000, 9999)}"
    
    # 构建标签页 HTML
    html = f'<div class="custom-tabs" id="{tab_id}">'
    
    # 标签头
    html += '<div class="custom-tab-headers">'
    for idx, (title, _) in enumerate(matches):
        active_class = 'active' if idx == 0 else ''
        html += f'<div class="custom-tab-header {active_class}" data-tab="{idx}">{title.strip()}</div>'
    html += '</div>'
    
    # 标签内容
    html += '<div class="custom-tab-contents">'
    for idx, (_, body) in enumerate(matches):
        active_class = 'active' if idx == 0 else ''
        # 递归渲染 body 里的 Markdown
        body_html = render_markdown(body.strip())
        html += f'<div class="custom-tab-content {active_class}" data-tab="{idx}">{body_html}</div>'
    html += '</div>'
    
    html += '</div>'
    
    # JavaScript 初始化
    html += f'''
    <script>
    (function() {{
        const container = document.getElementById('{tab_id}');
        if (!container || container.dataset.tabsInitialized) return;
        container.dataset.tabsInitialized = 'true';
        
        const headers = container.querySelectorAll('.custom-tab-header');
        const contents = container.querySelectorAll('.custom-tab-content');
        
        headers.forEach(header => {{
            header.addEventListener('click', () => {{
                const tabIndex = header.dataset.tab;
                
                headers.forEach(h => h.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                
                header.classList.add('active');
                container.querySelector(`.custom-tab-content[data-tab="${{tabIndex}}"]`).classList.add('active');
            }});
        }});
    }})();
    </script>
    '''
    
    return html

def render_markdown(text):
    """将 Markdown 文本转换为 HTML"""
    if not text:
        return ''
    
    # 检查是否包含自定义标签页语法
    if ';;; tab' in text:
        # 直接交给 render_custom_tabs 处理
        return render_custom_tabs(text)
    
    # 普通 Markdown 渲染
    return md.convert(text)

# 注册 Jinja 过滤器
app.jinja_env.filters['markdown'] = render_markdown

# ========== 用户角色常量 ==========
ROLE_ADMIN = 'admin'
ROLE_MODERATOR = 'moderator'
ROLE_USER = 'user'

# 条目状态常量
STATUS_PRIVATE_DRAFT = 'private_draft'
STATUS_DRAFT = 'draft'
STATUS_PUBLISHED = 'published'
STATUS_REJECTED = 'rejected'

# ========== 数据模型 ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default=ROLE_USER)
    bio = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    submitted_errors = db.relationship('ErrorEntry', backref='submitter', lazy=True, 
                                       foreign_keys='ErrorEntry.submitter_id')
    reviewed_errors = db.relationship('ErrorEntry', backref='reviewer', lazy=True,
                                      foreign_keys='ErrorEntry.reviewer_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == ROLE_ADMIN
    
    def is_moderator(self):
        return self.role in [ROLE_ADMIN, ROLE_MODERATOR]
    
    def can_review(self):
        return self.is_moderator()

class ErrorEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    error_code = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(50))
    category = db.Column(db.String(50))
    
    cause_chain = db.Column(db.Text)      # 支持 Markdown
    consequences = db.Column(db.Text)     # 支持 Markdown
    solution = db.Column(db.Text)         # 支持 Markdown
    
    first_seen = db.Column(db.String(50))
    rarity = db.Column(db.String(20))
    fun_fact = db.Column(db.Text)         # 支持 Markdown
    
    status = db.Column(db.String(20), default=STATUS_DRAFT)
    submitter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_comment = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime)

    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 创建时间 
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))  # 更新时间
    
    @property
    def cause_chain_html(self):
        return render_markdown(self.cause_chain)
    
    @property
    def consequences_html(self):
        return render_markdown(self.consequences)
    
    @property
    def solution_html(self):
        return render_markdown(self.solution)
    
    @property
    def fun_fact_html(self):
        return render_markdown(self.fun_fact)
    
    @property
    def notes_html(self):
        return render_markdown(self.notes)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========== 权限装饰器 ==========
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                flash('⚠️ 权限不足', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_moderator():
            flash('⚠️ 需要审核员权限', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ========== 路由 ==========
@app.route('/')
def index():
    recent_errors = ErrorEntry.query.filter_by(status=STATUS_PUBLISHED)\
                                    .order_by(ErrorEntry.id.desc()).limit(6).all()
    platforms = db.session.query(ErrorEntry.platform, db.func.count(ErrorEntry.id))\
                          .filter_by(status=STATUS_PUBLISHED)\
                          .group_by(ErrorEntry.platform).all()
    total_count = ErrorEntry.query.filter_by(status=STATUS_PUBLISHED).count()
    legendary_count = ErrorEntry.query.filter_by(status=STATUS_PUBLISHED, rarity='Legendary').count()
    
    return render_template('index.html',
                         recent_errors=recent_errors,
                         platforms=[p[0] for p in platforms if p[0]],
                         total_count=total_count,
                         legendary_count=legendary_count)

@app.route('/error/<int:error_id>')
def error_detail(error_id):
    error = ErrorEntry.query.get_or_404(error_id)
    if error.status != STATUS_PUBLISHED:
        if not current_user.is_authenticated:
            flash('🔒 该条目尚未发布', 'error')
            return redirect(url_for('index'))
        if not (current_user.is_moderator() or current_user.id == error.submitter_id):
            flash('🔒 该条目尚未发布', 'error')
            return redirect(url_for('index'))
    
    return render_template('error.html', error=error)

@app.route('/error/code/<path:error_code>')
def error_by_code(error_code):
    error = ErrorEntry.query.filter_by(error_code=error_code, status=STATUS_PUBLISHED).first_or_404()
    return render_template('error.html', error=error)

@app.route('/search')
def search_page():
    query = request.args.get('q', '')
    platform_filter = request.args.get('platform', '')
    category_filter = request.args.get('category', '')
    
    errors_query = ErrorEntry.query.filter_by(status=STATUS_PUBLISHED)
    
    if query:
        errors_query = errors_query.filter(
            db.or_(
                ErrorEntry.error_code.contains(query),
                ErrorEntry.title.contains(query),
                ErrorEntry.cause_chain.contains(query)
            )
        )
    
    if platform_filter:
        errors_query = errors_query.filter_by(platform=platform_filter)
    
    if category_filter:
        errors_query = errors_query.filter_by(category=category_filter)
    
    errors = errors_query.order_by(ErrorEntry.error_code).all()
    
    # 所有平台（不受筛选影响）
    platforms = db.session.query(ErrorEntry.platform).distinct().all()
    
    # 分类：根据选中的平台动态过滤
    categories_query = db.session.query(ErrorEntry.category).distinct()
    if platform_filter:
        categories_query = categories_query.filter_by(platform=platform_filter)
    categories = categories_query.all()
    
    return render_template('search.html',
                         errors=errors,
                         query=query,
                         platform_filter=platform_filter,
                         category_filter=category_filter,
                         platforms=[p[0] for p in platforms if p[0]],
                         categories=[c[0] for c in categories if c[0]])

@app.route('/api/categories')
def api_categories():
    """返回指定平台下的所有分类"""
    platform = request.args.get('platform', '')
    
    query = db.session.query(ErrorEntry.category).distinct()
    if platform:
        query = query.filter_by(platform=platform)
    
    categories = [c[0] for c in query.all() if c[0]]
    return jsonify(categories)

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_error():
    if request.method == 'POST':
        action = request.form.get('action')  # 'publish' 或 'draft'
        
        # 馆主/审核员：点「发布」直接发布，点「保存草稿」进草稿箱
        if current_user.is_moderator():
            if action == 'publish':
                status = STATUS_PUBLISHED
            else:
                status = STATUS_PRIVATE_DRAFT
        else:
            # 普通人：点「提交审核」变待审核，点「保存草稿」进草稿箱
            status = STATUS_DRAFT if action == 'publish' else STATUS_PRIVATE_DRAFT
        
        error = ErrorEntry(
            error_code=request.form.get('error_code', '').strip(),
            title=request.form.get('title', '').strip(),
            platform=request.form.get('platform', '').strip(),
            category=request.form.get('category', '').strip(),
            cause_chain=request.form.get('cause_chain', '').strip(),
            consequences=request.form.get('consequences', '').strip(),
            solution=request.form.get('solution', '').strip(),
            first_seen=request.form.get('first_seen', '').strip(),
            rarity=request.form.get('rarity', 'Common'),
            fun_fact=request.form.get('fun_fact', '').strip(),
            notes=request.form.get('notes', '').strip(),
            submitter_id=current_user.id,
            status=status
        )
        
        db.session.add(error)
        db.session.commit()
        
        if status == STATUS_PUBLISHED:
            flash('✅ 提交成功！条目已发布。', 'success')
        elif status == STATUS_DRAFT:
            flash('✅ 已提交审核，等待审核员通过。', 'success')
        else:
            flash('📝 已保存到草稿箱。', 'info')
        
        return redirect(url_for('error_detail', error_id=error.id))
    
    return render_template('submit.html')

@app.route('/my-submissions')
@login_required
def my_submissions():
    submissions = ErrorEntry.query.filter_by(submitter_id=current_user.id)\
                                  .order_by(ErrorEntry.submitted_at.desc()).all()
    return render_template('my_submissions.html', submissions=submissions)

@app.route('/review')
@moderator_required
def review_dashboard():
    pending = ErrorEntry.query.filter_by(status=STATUS_DRAFT)\
                              .order_by(ErrorEntry.submitted_at.desc()).all()
    return render_template('review.html', pending=pending)

@app.route('/review/<int:error_id>', methods=['GET', 'POST'])
@moderator_required
def review_error(error_id):
    error = ErrorEntry.query.get_or_404(error_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        error.reviewer_id = current_user.id
        error.reviewed_at = datetime.now(timezone.utc)
        
        if action == 'approve':
            error.status = STATUS_PUBLISHED
            flash(f'✅ 已通过审核：{error.error_code}', 'success')
        elif action == 'reject':
            error.status = STATUS_REJECTED
            error.review_comment = request.form.get('review_comment', '')
            flash(f'❌ 已驳回：{error.error_code}', 'info')
        
        db.session.commit()
        return redirect(url_for('review_dashboard'))
    
    return render_template('review_detail.html', error=error)

@app.route('/error/<int:error_id>/delete', methods=['POST'])
@login_required
def delete_error(error_id):
    """删除错误条目"""
    error = ErrorEntry.query.get_or_404(error_id)
    
    # 权限检查：审核员可以删任何条目；普通用户只能删自己的草稿或待审核条目
    if not current_user.is_moderator():
        # 普通人只能删自己的，且只能删未发布的
        if error.submitter_id != current_user.id:
            flash('⚠️ 你没有权限删除这个条目', 'error')
            return redirect(url_for('error_detail', error_id=error_id))
        if error.status == STATUS_PUBLISHED:
            flash('⚠️ 已发布的条目不能自行删除，请联系审核员', 'error')
            return redirect(url_for('error_detail', error_id=error_id))
    
    error_code = error.error_code
    db.session.delete(error)
    db.session.commit()
    
    flash(f'🗑️ 已删除：{error_code}', 'success')
    
    # 如果是草稿箱页面触发的删除，返回草稿箱
    referrer = request.referrer
    if referrer and '/drafts' in referrer:
        return redirect(url_for('drafts'))
    
    return redirect(url_for('index'))

@app.route('/error/<int:error_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_error(error_id):
    error = ErrorEntry.query.get_or_404(error_id)
    
    if request.method == 'POST':
        action = request.form.get('action')  # 'publish' 或 'draft'
        
        error.error_code = request.form.get('error_code', '').strip()
        error.title = request.form.get('title', '').strip()
        error.platform = request.form.get('platform', '').strip()
        error.category = request.form.get('category', '').strip()
        error.cause_chain = request.form.get('cause_chain', '').strip()
        error.consequences = request.form.get('consequences', '').strip()
        error.solution = request.form.get('solution', '').strip()
        error.first_seen = request.form.get('first_seen', '').strip()
        error.rarity = request.form.get('rarity', 'Common')
        error.fun_fact = request.form.get('fun_fact', '').strip()
        error.notes = request.form.get('notes', '').strip()
        
        # 处理状态变更
        if current_user.is_moderator():
            # 审核员编辑后自动已发布
            error.status = STATUS_PUBLISHED
        else:
            # 普通人：选「提交审核」变 draft，选「保存草稿」变 private_draft
            error.status = STATUS_DRAFT if action == 'publish' else STATUS_PRIVATE_DRAFT
        
        db.session.commit()
        
        if error.status == STATUS_PUBLISHED:
            flash('✅ 更新成功，条目已发布。', 'success')
        elif error.status == STATUS_DRAFT:
            flash('✅ 已提交审核。', 'success')
        else:
            flash('📝 已保存到草稿箱。', 'info')
        
        return redirect(url_for('error_detail', error_id=error_id))
    
    return render_template('edit.html', error=error)

@app.route('/drafts')
@login_required
def drafts():
    """私人草稿箱"""
    drafts = ErrorEntry.query.filter_by(
        submitter_id=current_user.id,
        status=STATUS_PRIVATE_DRAFT
    ).order_by(ErrorEntry.updated_at.desc() if hasattr(ErrorEntry, 'updated_at') else ErrorEntry.submitted_at.desc()).all()
    
    return render_template('drafts.html', drafts=drafts)

@app.route('/admin/users')
@role_required(ROLE_ADMIN)
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>/role', methods=['POST'])
@role_required(ROLE_ADMIN)
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in [ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER]:
        user.role = new_role
        db.session.commit()
        flash(f'✅ {user.username} 的角色已更新为 {new_role}', 'success')
    return redirect(url_for('admin_users'))

# ========== 认证路由 ==========
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('用户名已被占用')
    
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('邮箱已被注册')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            flash(f'👋 欢迎回来，{user.username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('❌ 用户名或密码错误', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=ROLE_USER
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        login_user(user, remember=True)
        flash('🎉 注册成功！欢迎成为错误档案馆的一员。', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 已退出登录', 'info')
    return redirect(url_for('index'))

# ========== API ==========
@app.route('/api/random')
def random_error():
    import random
    count = ErrorEntry.query.filter_by(status=STATUS_PUBLISHED).count()
    if count == 0:
        return jsonify({'error': 'No entries'}), 404
    
    errors = ErrorEntry.query.filter_by(status=STATUS_PUBLISHED).all()
    error = random.choice(errors)
    return jsonify({'id': error.id, 'code': error.error_code, 'title': error.title})

@app.route('/api/stats')
def api_stats():
    total = ErrorEntry.query.filter_by(status=STATUS_PUBLISHED).count()
    pending = ErrorEntry.query.filter_by(status=STATUS_DRAFT).count()
    
    return jsonify({
        'total': total,
        'pending': pending,
    })
    

# ========== 模板上下文处理器 ==========
@app.context_processor
def utility_processor():
    return {
        'STATUS_PRIVATE_DRAFT': STATUS_PRIVATE_DRAFT,
        'STATUS_DRAFT': STATUS_DRAFT,
        'STATUS_PUBLISHED': STATUS_PUBLISHED,
        'STATUS_REJECTED': STATUS_REJECTED,
        'ROLE_ADMIN': ROLE_ADMIN,
        'ROLE_MODERATOR': ROLE_MODERATOR,
    }

if __name__ == '__main__':
    app.run()