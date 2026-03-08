from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify, send_file
import subprocess
import sys
import os
import asyncio
import importlib
import re
import threading
import time
import signal
from werkzeug.utils import secure_filename
import json
from functools import wraps

# قالب HTML للواجهة
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌟 منصة استضافة وتشغيل سكريبتات بايثون</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-align: center;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            margin-top: 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }
        
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            background: #e8eaff;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 48px;
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .file-input {
            display: none;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: #333;
        }
        
        .btn-warning {
            background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
            color: #333;
        }
        
        .script-list {
            list-style: none;
            padding: 0;
        }
        
        .script-item {
            background: #f8f9ff;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            border: 1px solid #e0e0e0;
            transition: all 0.3s;
        }
        
        .script-item:hover {
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
            transform: translateX(5px);
        }
        
        .script-info {
            flex: 1;
        }
        
        .script-name {
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        
        .script-status {
            font-size: 0.9em;
            padding: 3px 10px;
            border-radius: 15px;
            display: inline-block;
        }
        
        .status-active {
            background: #84fab0;
            color: #1a5a1a;
        }
        
        .status-stopped {
            background: #ffb8b8;
            color: #a00;
        }
        
        .script-actions {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }
        
        .btn-small {
            padding: 5px 15px;
            font-size: 14px;
        }
        
        .output-area {
            background: #1e1e2f;
            color: #fff;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 20px;
        }
        
        .flash-message {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            animation: slideIn 0.3s ease;
        }
        
        .flash-success {
            background: #84fab0;
            color: #1a5a1a;
        }
        
        .flash-error {
            background: #ffb8b8;
            color: #a00;
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(-20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
        }
        
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            .script-item {
                flex-direction: column;
                align-items: stretch;
            }
            
            .script-actions {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 منصة استضافة وتشغيل بايثون</h1>
        <div class="subtitle">رفع، تشغيل، وإدارة سكريبتات بايثون بكل سهولة</div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ scripts|length }}</div>
                <div class="stat-label">إجمالي السكريبتات</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ active_count }}</div>
                <div class="stat-label">قيد التشغيل</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stopped_count }}</div>
                <div class="stat-label">متوقفة</div>
            </div>
        </div>
        
        <div class="grid">
            <div>
                <div class="card">
                    <h2>📤 رفع سكريبت جديد</h2>
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <div class="upload-icon">📁</div>
                        <h3>اضغط لرفع ملف بايثون</h3>
                        <p style="color: #999;">يدعم ملفات .py فقط</p>
                    </div>
                    <form id="uploadForm" action="{{ url_for('upload_script') }}" method="post" enctype="multipart/form-data">
                        <input type="file" id="fileInput" name="file" class="file-input" accept=".py" onchange="document.getElementById('uploadForm').submit()">
                    </form>
                    
                    <form action="{{ url_for('create_script') }}" method="post" style="margin-top: 20px;">
                        <h3>أو إنشاء سكريبت جديد</h3>
                        <input type="text" name="script_name" placeholder="اسم السكريبت (مثال: script.py)" required style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ddd;">
                        <textarea name="script_content" rows="5" placeholder="اكتب كود البايثون هنا..." required style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ddd; font-family: monospace;"></textarea>
                        <button type="submit" class="btn">💾 إنشاء السكريبت</button>
                    </form>
                </div>
                
                <div class="card">
                    <h2>⚙️ إجراءات سريعة</h2>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <a href="{{ url_for('restart_all') }}" class="btn btn-warning" onclick="return confirm('هل أنت متأكد من إعادة تشغيل جميع السكريبتات؟')">🔄 إعادة تشغيل الكل</a>
                        <a href="{{ url_for('stop_all') }}" class="btn btn-danger" onclick="return confirm('هل أنت متأكد من إيقاف جميع السكريبتات؟')">⏹️ إيقاف الكل</a>
                    </div>
                </div>
            </div>
            
            <div>
                <div class="card">
                    <h2>📋 السكريبتات المتاحة</h2>
                    {% if scripts %}
                        <ul class="script-list">
                            {% for script in scripts %}
                                <li class="script-item">
                                    <div class="script-info">
                                        <div class="script-name">{{ script.name }}</div>
                                        <div class="script-status {% if script.running %}status-active{% else %}status-stopped{% endif %}">
                                            {% if script.running %}🟢 قيد التشغيل{% else %}🔴 متوقف{% endif %}
                                        </div>
                                        {% if script.pid %}
                                            <div style="font-size: 0.8em; color: #666;">PID: {{ script.pid }}</div>
                                        {% endif %}
                                    </div>
                                    <div class="script-actions">
                                        {% if script.running %}
                                            <a href="{{ url_for('stop_script', script_name=script.name) }}" class="btn btn-small btn-danger" onclick="return confirm('إيقاف {{ script.name }}؟')">⏹️ إيقاف</a>
                                        {% else %}
                                            <a href="{{ url_for('run_script', script_name=script.name) }}" class="btn btn-small btn-success">▶️ تشغيل</a>
                                        {% endif %}
                                        <a href="{{ url_for('view_script', script_name=script.name) }}" class="btn btn-small btn-warning">📝 عرض</a>
                                        <a href="{{ url_for('delete_script', script_name=script.name) }}" class="btn btn-small btn-danger" onclick="return confirm('حذف {{ script.name }}؟')">🗑️ حذف</a>
                                        <a href="{{ url_for('download_script', script_name=script.name) }}" class="btn btn-small">📥 تحميل</a>
                                    </div>
                                </li>
                            {% endfor %}
                        </ul>
                    {% else %}
                        <div style="text-align: center; padding: 40px; color: #999;">
                            <p style="font-size: 48px;">📂</p>
                            <p>لا توجد سكريبتات مرفوعة بعد</p>
                        </div>
                    {% endif %}
                </div>
                
                {% if output %}
                    <div class="card">
                        <h2>📤 مخرجات التشغيل</h2>
                        <div class="output-area">{{ output }}</div>
                        <div style="margin-top: 10px;">
                            <a href="{{ url_for('clear_output') }}" class="btn btn-small">🧹 مسح المخرجات</a>
                        </div>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div id="loadingModal" class="modal">
        <div class="modal-content" style="text-align: center;">
            <div class="loading" style="width: 50px; height: 50px;"></div>
            <h3 style="margin-top: 20px;">جاري التنفيذ...</h3>
        </div>
    </div>
    
    <script>
        function showLoading() {
            document.getElementById('loadingModal').style.display = 'flex';
        }
        
        // إخفاء رسائل الفلاش بعد 5 ثوان
        setTimeout(() => {
            document.querySelectorAll('.flash-message').forEach(el => el.remove());
        }, 5000);
        
        // تفعيل السحب والإفلات
        const uploadArea = document.querySelector('.upload-area');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.background = '#e8eaff';
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.background = '#f8f9ff';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.background = '#f8f9ff';
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].name.endsWith('.py')) {
                document.getElementById('fileInput').files = files;
                document.getElementById('uploadForm').submit();
            } else {
                alert('الرجاء رفع ملف بايثون فقط (.py)');
            }
        });
        
        // تحديث تلقائي كل 30 ثانية
        setInterval(() => {
            fetch('/api/scripts_status')
                .then(response => response.json())
                .then(data => {
                    // تحديث الحالة دون إعادة تحميل الصفحة
                    console.log('تم تحديث الحالة:', data);
                })
                .catch(err => console.error('خطأ في التحديث:', err));
        }, 30000);
    </script>
</body>
</html>
'''

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-it'

# التكوين
BASE_DIR = "scripts"
OUTPUT_FILE = "last_output.txt"
os.makedirs(BASE_DIR, exist_ok=True)

# قاموس لتخزين العمليات الجارية
processes = {}
process_lock = threading.Lock()

# دالة لتثبيت المكتبات المفقودة
def install_missing_packages(script_path):
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        # البحث عن المكتبات المستوردة
        imported_packages = set(re.findall(r"^\s*import\s+([a-zA-Z0-9_]+)|^\s*from\s+([a-zA-Z0-9_]+)\s+import", code, re.MULTILINE))
        packages = {pkg for group in imported_packages for pkg in group if pkg}
        
        installed = []
        failed = []
        
        for package in packages:
            try:
                __import__(package)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
                    installed.append(package)
                except:
                    failed.append(package)
        
        return installed, failed
    except Exception as e:
        return [], [str(e)]

# تشغيل سكريبت
def run_script_async(script_name, script_path):
    try:
        # تثبيت المكتبات المطلوبة
        installed, failed = install_missing_packages(script_path)
        
        # تشغيل السكريبت
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        with process_lock:
            processes[script_name] = {
                'process': process,
                'pid': process.pid,
                'start_time': time.time(),
                'installed_packages': installed,
                'failed_packages': failed
            }
        
        return True, process.pid, installed, failed
    except Exception as e:
        return False, str(e), [], []

# الصفحة الرئيسية
@app.route('/')
def index():
    scripts = []
    active_count = 0
    stopped_count = 0
    
    for filename in os.listdir(BASE_DIR):
        if filename.endswith('.py'):
            file_path = os.path.join(BASE_DIR, filename)
            is_running = filename in processes and processes[filename]['process'].poll() is None
            
            script_info = {
                'name': filename,
                'running': is_running,
                'size': os.path.getsize(file_path),
                'modified': time.ctime(os.path.getmtime(file_path))
            }
            
            if is_running:
                script_info['pid'] = processes[filename]['pid']
                active_count += 1
            else:
                stopped_count += 1
                
            scripts.append(script_info)
    
    # قراءة آخر مخرجات
    output = None
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            output = f.read()
    
    return render_template_string(
        HTML_TEMPLATE, 
        scripts=scripts, 
        active_count=active_count,
        stopped_count=stopped_count,
        output=output
    )

# رفع سكريبت
@app.route('/upload', methods=['POST'])
def upload_script():
    if 'file' not in request.files:
        flash('لم يتم اختيار ملف', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('لم يتم اختيار ملف', 'error')
        return redirect(url_for('index'))
    
    if not file.filename.endswith('.py'):
        flash('الرجاء رفع ملف بايثون فقط (.py)', 'error')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(BASE_DIR, filename)
    file.save(file_path)
    
    flash(f'✅ تم رفع {filename} بنجاح', 'success')
    return redirect(url_for('index'))

# إنشاء سكريبت جديد
@app.route('/create', methods=['POST'])
def create_script():
    script_name = request.form.get('script_name', '').strip()
    script_content = request.form.get('script_content', '').strip()
    
    if not script_name or not script_name.endswith('.py'):
        flash('اسم الملف غير صالح. يجب أن ينتهي بـ .py', 'error')
        return redirect(url_for('index'))
    
    script_name = secure_filename(script_name)
    file_path = os.path.join(BASE_DIR, script_name)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    flash(f'✅ تم إنشاء {script_name} بنجاح', 'success')
    return redirect(url_for('index'))

# تشغيل سكريبت
@app.route('/run/<script_name>')
def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    
    if not os.path.exists(script_path):
        flash('❌ السكريبت غير موجود', 'error')
        return redirect(url_for('index'))
    
    if script_name in processes and processes[script_name]['process'].poll() is None:
        flash('⚠️ السكريبت قيد التشغيل بالفعل', 'error')
        return redirect(url_for('index'))
    
    success, result, installed, failed = run_script_async(script_name, script_path)
    
    if success:
        msg = f'✅ تم تشغيل {script_name} بنجاح (PID: {result})'
        if installed:
            msg += f'\n📦 تم تثبيت: {", ".join(installed)}'
        if failed:
            msg += f'\n❌ فشل تثبيت: {", ".join(failed)}'
        flash(msg, 'success')
    else:
        flash(f'❌ فشل تشغيل {script_name}: {result}', 'error')
    
    return redirect(url_for('index'))

# إيقاف سكريبت
@app.route('/stop/<script_name>')
def stop_script(script_name):
    with process_lock:
        if script_name in processes:
            process_info = processes[script_name]
            if process_info['process'].poll() is None:
                process_info['process'].terminate()
                try:
                    process_info['process'].wait(timeout=5)
                except subprocess.TimeoutError:
                    process_info['process'].kill()
                flash(f'⏹️ تم إيقاف {script_name}', 'success')
            del processes[script_name]
        else:
            flash(f'⚠️ {script_name} غير قيد التشغيل', 'error')
    
    return redirect(url_for('index'))

# حذف سكريبت
@app.route('/delete/<script_name>')
def delete_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    
    # إيقاف السكريبت إذا كان يعمل
    with process_lock:
        if script_name in processes:
            if processes[script_name]['process'].poll() is None:
                processes[script_name]['process'].terminate()
                try:
                    processes[script_name]['process'].wait(timeout=5)
                except subprocess.TimeoutError:
                    processes[script_name]['process'].kill()
            del processes[script_name]
    
    # حذف الملف
    if os.path.exists(script_path):
        os.remove(script_path)
        flash(f'✅ تم حذف {script_name}', 'success')
    else:
        flash('❌ الملف غير موجود', 'error')
    
    return redirect(url_for('index'))

# عرض محتوى السكريبت
@app.route('/view/<script_name>')
def view_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    
    if not os.path.exists(script_path):
        flash('❌ السكريبت غير موجود', 'error')
        return redirect(url_for('index'))
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return f'''
    <html dir="rtl">
    <head>
        <title>{script_name}</title>
        <style>
            body {{ font-family: monospace; padding: 20px; background: #1e1e2f; color: #fff; }}
            pre {{ background: #2d2d3f; padding: 20px; border-radius: 10px; overflow: auto; }}
            .btn {{ 
                background: #667eea; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px;
                display: inline-block;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <a href="/" class="btn">⬅️ العودة</a>
        <h2>{script_name}</h2>
        <pre>{content}</pre>
    </body>
    </html>
    '''

# تحميل السكريبت
@app.route('/download/<script_name>')
def download_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    
    if not os.path.exists(script_path):
        flash('❌ السكريبت غير موجود', 'error')
        return redirect(url_for('index'))
    
    return send_file(script_path, as_attachment=True)

# إعادة تشغيل الكل
@app.route('/restart_all')
def restart_all():
    # إيقاف جميع السكريبتات
    with process_lock:
        for script_name, process_info in list(processes.items()):
            if process_info['process'].poll() is None:
                process_info['process'].terminate()
                try:
                    process_info['process'].wait(timeout=5)
                except subprocess.TimeoutError:
                    process_info['process'].kill()
        
        processes.clear()
    
    # تشغيل جميع السكريبتات
    success_count = 0
    for filename in os.listdir(BASE_DIR):
        if filename.endswith('.py'):
            script_path = os.path.join(BASE_DIR, filename)
            success, result, _, _ = run_script_async(filename, script_path)
            if success:
                success_count += 1
    
    flash(f'♻️ تم إعادة تشغيل {success_count} سكريبت', 'success')
    return redirect(url_for('index'))

# إيقاف الكل
@app.route('/stop_all')
def stop_all():
    with process_lock:
        for script_name, process_info in list(processes.items()):
            if process_info['process'].poll() is None:
                process_info['process'].terminate()
                try:
                    process_info['process'].wait(timeout=5)
                except subprocess.TimeoutError:
                    process_info['process'].kill()
        
        count = len(processes)
        processes.clear()
    
    flash(f'⏹️ تم إيقاف {count} سكريبت', 'success')
    return redirect(url_for('index'))

# مسح المخرجات
@app.route('/clear_output')
def clear_output():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    flash('🧹 تم مسح المخرجات', 'success')
    return redirect(url_for('index'))

# API للحصول على حالة السكريبتات
@app.route('/api/scripts_status')
def scripts_status():
    status = {}
    for filename in os.listdir(BASE_DIR):
        if filename.endswith('.py'):
            status[filename] = {
                'running': filename in processes and processes[filename]['process'].poll() is None
            }
    return jsonify(status)

# الصفحة الرئيسية مع دعم تشغيل asyncio
@app.before_request
def before_request():
    # التحقق من العمليات المنتهية
    with process_lock:
        for script_name in list(processes.keys()):
            if processes[script_name]['process'].poll() is not None:
                # جمع المخرجات
                stdout, stderr = processes[script_name]['process'].communicate()
                if stdout or stderr:
                    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"\n\n=== {script_name} ===\n")
                        if stdout:
                            f.write(f"STDOUT:\n{stdout}\n")
                        if stderr:
                            f.write(f"STDERR:\n{stderr}\n")
                
                del processes[script_name]

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 منصة استضافة بايثون - جاهزة للعمل!")
    print("=" * 50)
    print(f"📁 مجلد السكريبتات: {os.path.abspath(BASE_DIR)}")
    print(f"🌐 الواجهة: http://localhost:5000")
    print("=" * 50)
    print("✅ تم التهيئة بنجاح!")
    print("=" * 50)
    
    # تشغيل التطبيق
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
