// server.js
const express = require('express');
const session = require('express-session');
const flash = require('connect-flash');
const multer = require('multer');
const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const { PythonShell } = require('python-shell');
const { promisify } = require('util');
const execAsync = promisify(exec);

const app = express();
const PORT = 5000;

// التكوين
const BASE_DIR = path.join(__dirname, 'scripts');
const OUTPUT_FILE = path.join(__dirname, 'last_output.txt');

// إنشاء المجلدات إذا لم تكن موجودة
if (!fsSync.existsSync(BASE_DIR)) {
    fsSync.mkdirSync(BASE_DIR, { recursive: true });
}

// إعدادات multer لرفع الملفات
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, BASE_DIR);
    },
    filename: (req, file, cb) => {
        cb(null, file.originalname);
    }
});
const upload = multer({ 
    storage: storage,
    fileFilter: (req, file, cb) => {
        if (file.originalname.endsWith('.py')) {
            cb(null, true);
        } else {
            cb(new Error('يجب رفع ملفات بايثون فقط'));
        }
    }
});

// تخزين العمليات الجارية
const processes = new Map();

// إعدادات Express
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(session({
    secret: 'your-secret-key-here-change-it',
    resave: false,
    saveUninitialized: true
}));
app.use(flash());

// Middleware للرسائل
app.use((req, res, next) => {
    res.locals.messages = req.flash();
    next();
});

// قالب HTML (نفس القالب مع تعديلات بسيطة للمسارات)
const HTML_TEMPLATE = `<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌟 منصة استضافة وتشغيل سكريبتات بايثون</title>
    <style>
        /* نفس الـ CSS السابق مع تعديل المسارات */
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
        
        <% if (messages.success) { %>
            <% messages.success.forEach(function(msg) { %>
                <div class="flash-message flash-success"><%= msg %></div>
            <% }); %>
        <% } %>
        
        <% if (messages.error) { %>
            <% messages.error.forEach(function(msg) { %>
                <div class="flash-message flash-error"><%= msg %></div>
            <% }); %>
        <% } %>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number"><%= scripts.length %></div>
                <div class="stat-label">إجمالي السكريبتات</div>
            </div>
            <div class="stat-card">
                <div class="stat-number"><%= activeCount %></div>
                <div class="stat-label">قيد التشغيل</div>
            </div>
            <div class="stat-card">
                <div class="stat-number"><%= stoppedCount %></div>
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
                    <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
                        <input type="file" id="fileInput" name="file" class="file-input" accept=".py" onchange="document.getElementById('uploadForm').submit()">
                    </form>
                    
                    <form action="/create" method="post" style="margin-top: 20px;">
                        <h3>أو إنشاء سكريبت جديد</h3>
                        <input type="text" name="script_name" placeholder="اسم السكريبت (مثال: script.py)" required style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ddd;">
                        <textarea name="script_content" rows="5" placeholder="اكتب كود البايثون هنا..." required style="width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ddd; font-family: monospace;"></textarea>
                        <button type="submit" class="btn">💾 إنشاء السكريبت</button>
                    </form>
                </div>
                
                <div class="card">
                    <h2>⚙️ إجراءات سريعة</h2>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <a href="/restart_all" class="btn btn-warning" onclick="return confirm('هل أنت متأكد من إعادة تشغيل جميع السكريبتات؟')">🔄 إعادة تشغيل الكل</a>
                        <a href="/stop_all" class="btn btn-danger" onclick="return confirm('هل أنت متأكد من إيقاف جميع السكريبتات؟')">⏹️ إيقاف الكل</a>
                    </div>
                </div>
            </div>
            
            <div>
                <div class="card">
                    <h2>📋 السكريبتات المتاحة</h2>
                    <% if (scripts.length > 0) { %>
                        <ul class="script-list">
                            <% scripts.forEach(function(script) { %>
                                <li class="script-item">
                                    <div class="script-info">
                                        <div class="script-name"><%= script.name %></div>
                                        <div class="script-status <%= script.running ? 'status-active' : 'status-stopped' %>">
                                            <%= script.running ? '🟢 قيد التشغيل' : '🔴 متوقف' %>
                                        </div>
                                        <% if (script.pid) { %>
                                            <div style="font-size: 0.8em; color: #666;">PID: <%= script.pid %></div>
                                        <% } %>
                                    </div>
                                    <div class="script-actions">
                                        <% if (script.running) { %>
                                            <a href="/stop/<%= script.name %>" class="btn btn-small btn-danger" onclick="return confirm('إيقاف <%= script.name %>؟')">⏹️ إيقاف</a>
                                        <% } else { %>
                                            <a href="/run/<%= script.name %>" class="btn btn-small btn-success">▶️ تشغيل</a>
                                        <% } %>
                                        <a href="/view/<%= script.name %>" class="btn btn-small btn-warning">📝 عرض</a>
                                        <a href="/delete/<%= script.name %>" class="btn btn-small btn-danger" onclick="return confirm('حذف <%= script.name %>؟')">🗑️ حذف</a>
                                        <a href="/download/<%= script.name %>" class="btn btn-small">📥 تحميل</a>
                                    </div>
                                </li>
                            <% }); %>
                        </ul>
                    <% } else { %>
                        <div style="text-align: center; padding: 40px; color: #999;">
                            <p style="font-size: 48px;">📂</p>
                            <p>لا توجد سكريبتات مرفوعة بعد</p>
                        </div>
                    <% } %>
                </div>
                
                <% if (output) { %>
                    <div class="card">
                        <h2>📤 مخرجات التشغيل</h2>
                        <div class="output-area"><%= output %></div>
                        <div style="margin-top: 10px;">
                            <a href="/clear_output" class="btn btn-small">🧹 مسح المخرجات</a>
                        </div>
                    </div>
                <% } %>
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
                    console.log('تم تحديث الحالة:', data);
                })
                .catch(err => console.error('خطأ في التحديث:', err));
        }, 30000);
    </script>
</body>
</html>`;

// دالة لاستخراج المكتبات المستوردة من كود بايثون
function extractImportedPackages(code) {
    const importRegex = /^\s*import\s+([a-zA-Z0-9_]+)|^\s*from\s+([a-zA-Z0-9_]+)\s+import/gm;
    const packages = new Set();
    let match;
    
    while ((match = importRegex.exec(code)) !== null) {
        if (match[1]) packages.add(match[1]);
        if (match[2]) packages.add(match[2]);
    }
    
    return Array.from(packages);
}

// دالة لتثبيت المكتبات المفقودة
async function installMissingPackages(scriptPath) {
    try {
        const code = await fs.readFile(scriptPath, 'utf8');
        const packages = extractImportedPackages(code);
        
        const installed = [];
        const failed = [];
        
        for (const pkg of packages) {
            try {
                // التحقق من تثبيت المكتبة
                await execAsync(`python -c "import ${pkg}"`);
            } catch (error) {
                // تثبيت المكتبة إذا لم تكن موجودة
                try {
                    await execAsync(`pip install ${pkg}`);
                    installed.push(pkg);
                } catch (installError) {
                    failed.push(pkg);
                }
            }
        }
        
        return { installed, failed };
    } catch (error) {
        return { installed: [], failed: [error.message] };
    }
}

// تشغيل سكريبت
async function runScriptAsync(scriptName, scriptPath) {
    try {
        // تثبيت المكتبات المطلوبة
        const { installed, failed } = await installMissingPackages(scriptPath);
        
        // تشغيل السكريبت
        const pythonProcess = spawn('python', [scriptPath]);
        
        const processInfo = {
            process: pythonProcess,
            pid: pythonProcess.pid,
            startTime: Date.now(),
            installedPackages: installed,
            failedPackages: failed
        };
        
        processes.set(scriptName, processInfo);
        
        // جمع المخرجات
        let stdout = '';
        let stderr = '';
        
        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        pythonProcess.on('close', async (code) => {
            if (stdout || stderr) {
                const output = `\n\n=== ${scriptName} ===\nSTDOUT:\n${stdout}\nSTDERR:\n${stderr}\n`;
                await fs.appendFile(OUTPUT_FILE, output);
            }
            processes.delete(scriptName);
        });
        
        return { success: true, pid: pythonProcess.pid, installed, failed };
    } catch (error) {
        return { success: false, error: error.message, installed: [], failed: [] };
    }
}

// الصفحة الرئيسية
app.get('/', async (req, res) => {
    try {
        const files = await fs.readdir(BASE_DIR);
        const scripts = [];
        let activeCount = 0;
        let stoppedCount = 0;
        
        for (const file of files) {
            if (file.endsWith('.py')) {
                const filePath = path.join(BASE_DIR, file);
                const stats = await fs.stat(filePath);
                const isRunning = processes.has(file);
                
                const scriptInfo = {
                    name: file,
                    running: isRunning,
                    size: stats.size,
                    modified: stats.mtime
                };
                
                if (isRunning) {
                    scriptInfo.pid = processes.get(file).pid;
                    activeCount++;
                } else {
                    stoppedCount++;
                }
                
                scripts.push(scriptInfo);
            }
        }
        
        // قراءة آخر مخرجات
        let output = null;
        try {
            output = await fs.readFile(OUTPUT_FILE, 'utf8');
        } catch (error) {
            // الملف غير موجود
        }
        
        // استخدام EJS أو أي محرك قوالب
        res.send(require('ejs').render(HTML_TEMPLATE, {
            scripts,
            activeCount,
            stoppedCount,
            output,
            messages: req.flash()
        }));
    } catch (error) {
        req.flash('error', 'حدث خطأ: ' + error.message);
        res.redirect('/');
    }
});

// رفع سكريبت
app.post('/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        req.flash('error', 'لم يتم رفع الملف');
    } else {
        req.flash('success', `✅ تم رفع ${req.file.originalname} بنجاح`);
    }
    res.redirect('/');
});

// إنشاء سكريبت جديد
app.post('/create', async (req, res) => {
    const { script_name, script_content } = req.body;
    
    if (!script_name || !script_name.endsWith('.py')) {
        req.flash('error', 'اسم الملف غير صالح. يجب أن ينتهي بـ .py');
        return res.redirect('/');
    }
    
    const filePath = path.join(BASE_DIR, script_name);
    
    try {
        await fs.writeFile(filePath, script_content);
        req.flash('success', `✅ تم إنشاء ${script_name} بنجاح`);
    } catch (error) {
        req.flash('error', 'حدث خطأ: ' + error.message);
    }
    
    res.redirect('/');
});

// تشغيل سكريبت
app.get('/run/:scriptName', async (req, res) => {
    const scriptName = req.params.scriptName;
    const scriptPath = path.join(BASE_DIR, scriptName);
    
    try {
        await fs.access(scriptPath);
        
        if (processes.has(scriptName)) {
            req.flash('error', '⚠️ السكريبت قيد التشغيل بالفعل');
            return res.redirect('/');
        }
        
        const result = await runScriptAsync(scriptName, scriptPath);
        
        if (result.success) {
            let msg = `✅ تم تشغيل ${scriptName} بنجاح (PID: ${result.pid})`;
            if (result.installed.length > 0) {
                msg += `\n📦 تم تثبيت: ${result.installed.join(', ')}`;
            }
            if (result.failed.length > 0) {
                msg += `\n❌ فشل تثبيت: ${result.failed.join(', ')}`;
            }
            req.flash('success', msg);
        } else {
            req.flash('error', `❌ فشل تشغيل ${scriptName}: ${result.error}`);
        }
    } catch (error) {
        req.flash('error', '❌ السكريبت غير موجود');
    }
    
    res.redirect('/');
});

// إيقاف سكريبت
app.get('/stop/:scriptName', (req, res) => {
    const scriptName = req.params.scriptName;
    
    if (processes.has(scriptName)) {
        const processInfo = processes.get(scriptName);
        processInfo.process.kill();
        processes.delete(scriptName);
        req.flash('success', `⏹️ تم إيقاف ${scriptName}`);
    } else {
        req.flash('error', `⚠️ ${scriptName} غير قيد التشغيل`);
    }
    
    res.redirect('/');
});

// حذف سكريبت
app.get('/delete/:scriptName', async (req, res) => {
    const scriptName = req.params.scriptName;
    const scriptPath = path.join(BASE_DIR, scriptName);
    
    // إيقاف السكريبت إذا كان يعمل
    if (processes.has(scriptName)) {
        processes.get(scriptName).process.kill();
        processes.delete(scriptName);
    }
    
    try {
        await fs.unlink(scriptPath);
        req.flash('success', `✅ تم حذف ${scriptName}`);
    } catch (error) {
        req.flash('error', '❌ الملف غير موجود');
    }
    
    res.redirect('/');
});

// عرض محتوى السكريبت
app.get('/view/:scriptName', async (req, res) => {
    const scriptName = req.params.scriptName;
    const scriptPath = path.join(BASE_DIR, scriptName);
    
    try {
        const content = await fs.readFile(scriptPath, 'utf8');
        res.send(`
        <html dir="rtl">
        <head>
            <title>${scriptName}</title>
            <style>
                body { font-family: monospace; padding: 20px; background: #1e1e2f; color: #fff; }
                pre { background: #2d2d3f; padding: 20px; border-radius: 10px; overflow: auto; }
                .btn { 
                    background: #667eea; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 5px;
                    display: inline-block;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <a href="/" class="btn">⬅️ العودة</a>
            <h2>${scriptName}</h2>
            <pre>${content}</pre>
        </body>
        </html>
        `);
    } catch (error) {
        req.flash('error', '❌ السكريبت غير موجود');
        res.redirect('/');
    }
});

// تحميل السكريبت
app.get('/download/:scriptName', (req, res) => {
    const scriptName = req.params.scriptName;
    const scriptPath = path.join(BASE_DIR, scriptName);
    
    res.download(scriptPath, scriptName, (err) => {
        if (err) {
            req.flash('error', '❌ السكريبت غير موجود');
            res.redirect('/');
        }
    });
});

// إعادة تشغيل الكل
app.get('/restart_all', async (req, res) => {
    // إيقاف جميع السكريبتات
    for (const [scriptName, processInfo] of processes) {
        processInfo.process.kill();
    }
    processes.clear();
    
    // تشغيل جميع السكريبتات
    let successCount = 0;
    const files = await fs.readdir(BASE_DIR);
    
    for (const file of files) {
        if (file.endsWith('.py')) {
            const scriptPath = path.join(BASE_DIR, file);
            const result = await runScriptAsync(file, scriptPath);
            if (result.success) successCount++;
        }
    }
    
    req.flash('success', `♻️ تم إعادة تشغيل ${successCount} سكريبت`);
    res.redirect('/');
});

// إيقاف الكل
app.get('/stop_all', (req, res) => {
    const count = processes.size;
    
    for (const [scriptName, processInfo] of processes) {
        processInfo.process.kill();
    }
    processes.clear();
    
    req.flash('success', `⏹️ تم إيقاف ${count} سكريبت`);
    res.redirect('/');
});

// مسح المخرجات
app.get('/clear_output', async (req, res) => {
    try {
        await fs.unlink(OUTPUT_FILE);
        req.flash('success', '🧹 تم مسح المخرجات');
    } catch (error) {
        // الملف غير موجود
    }
    res.redirect('/');
});

// API للحصول على حالة السكريبتات
app.get('/api/scripts_status', async (req, res) => {
    const status = {};
    const files = await fs.readdir(BASE_DIR);
    
    for (const file of files) {
        if (file.endsWith('.py')) {
            status[file] = {
                running: processes.has(file)
            };
        }
    }
    
    res.json(status);
});

// تشغيل الخادم
app.listen(PORT, '0.0.0.0', () => {
    console.log("=".repeat(50));
    console.log("🚀 منصة استضافة بايثون - جاهزة للعمل!");
    console.log("=".repeat(50));
    console.log(`📁 مجلد السكريبتات: ${path.resolve(BASE_DIR)}`);
    console.log(`🌐 الواجهة: http://localhost:${PORT}`);
    console.log("=".repeat(50));
    console.log("✅ تم التهيئة بنجاح!");
    console.log("=".repeat(50));
});

// تنظيف العمليات عند إغلاق الخادم
process.on('SIGINT', () => {
    console.log('\n🛑 جاري إيقاف جميع العمليات...');
    for (const [scriptName, processInfo] of processes) {
        processInfo.process.kill();
    }
    process.exit();
});
