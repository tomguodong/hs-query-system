# -*- coding: utf-8 -*-
"""
海关编码智能查询系统 - Flask应用主文件
HS Code Intelligent Query System
Version: 2.0.1
"""

import os
import sys
import json
import time
import uuid
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash, send_from_directory,
                   Response)

# 确保能找到模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (init_db, get_db_context, hash_password, verify_password)
from ai_service import (
    classify_hs_code, check_dual_use, learn_from_feedback,
    get_knowledge_suggestion, get_model_status, test_model_connection,
    get_current_model, switch_to_next_model, set_current_model,
    refresh_free_models, update_api_key, AVAILABLE_MODELS
)
from external_api import query_external_sources

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')

app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


# ============================================================
# 辅助函数
# ============================================================

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash('需要管理员权限', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def get_session_id():
    """获取或创建会话ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def get_user_id():
    """获取当前用户ID"""
    return session.get('user_id')


def get_client_ip():
    """获取客户端IP"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr


def record_query(query_text, query_type, matched_codes, ai_suggestion="",
                 is_dual_use=0, dual_use_info="", model_used="", response_time_ms=0):
    """记录查询日志"""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO query_logs
                (user_id, session_id, query_text, query_type, matched_hs_codes,
                 ai_suggestion, is_dual_use, dual_use_info, model_used,
                 response_time_ms, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (get_user_id(), get_session_id(), query_text, query_type,
                  json.dumps(matched_codes, ensure_ascii=False), ai_suggestion,
                  is_dual_use, dual_use_info, model_used, response_time_ms,
                  get_client_ip(), request.headers.get('User-Agent', '')[:500]))

            # 更新HS编码访问计数
            for code in matched_codes:
                if code.get('code'):
                    cursor.execute('''
                        UPDATE hs_codes SET access_count = access_count + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE code = ?
                    ''', (code['code'],))
    except Exception as e:
        print(f"记录查询日志失败: {e}")


def update_daily_stats():
    """更新每日统计"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        with get_db_context() as conn:
            cursor = conn.cursor()

            # 检查今天是否已有统计记录
            cursor.execute('SELECT id FROM system_stats WHERE stat_date = ?', (today,))
            if cursor.fetchone():
                cursor.execute('''
                    UPDATE system_stats SET
                        total_queries = (SELECT COUNT(*) FROM query_logs WHERE DATE(created_at) = ?),
                        unique_users = (SELECT COUNT(DISTINCT session_id) FROM query_logs WHERE DATE(created_at) = ?),
                        ai_queries = (SELECT COUNT(*) FROM query_logs WHERE DATE(created_at) = ? AND model_used != ''),
                        dual_use_checks = (SELECT COUNT(*) FROM query_logs WHERE DATE(created_at) = ? AND is_dual_use = 1),
                        dual_use_hits = (SELECT COUNT(*) FROM query_logs WHERE DATE(created_at) = ? AND is_dual_use = 1),
                        avg_response_time_ms = (SELECT AVG(response_time_ms) FROM query_logs WHERE DATE(created_at) = ? AND response_time_ms > 0),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE stat_date = ?
                ''', (today, today, today, today, today, today, today))
            else:
                cursor.execute('''
                    INSERT INTO system_stats (stat_date, total_queries, unique_users,
                        ai_queries, dual_use_checks, dual_use_hits, avg_response_time_ms)
                    SELECT ?, COUNT(*), COUNT(DISTINCT session_id),
                        SUM(CASE WHEN model_used != '' THEN 1 ELSE 0 END),
                        SUM(is_dual_use),
                        SUM(CASE WHEN is_dual_use = 1 THEN 1 ELSE 0 END),
                        AVG(CASE WHEN response_time_ms > 0 THEN response_time_ms END)
                    FROM query_logs WHERE DATE(created_at) = ?
                ''', (today, today))
    except Exception as e:
        print(f"更新统计失败: {e}")


# ============================================================
# 页面路由
# ============================================================

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')

        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password_hash, role, company FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

            if user and verify_password(password, user['password_hash']):
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['company'] = user['company'] or ''

                # 更新最后登录时间
                cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))

                flash(f'欢迎回来，{user["username"]}！', 'success')
                return redirect(request.args.get('next') or url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
                return render_template('login.html')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        company = request.form.get('company', '').strip()

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('密码长度至少6位', 'error')
            return render_template('register.html')

        try:
            with get_db_context() as conn:
                cursor = conn.cursor()
                password_hash = hash_password(password)
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, company, role)
                    VALUES (?, ?, ?, ?, 'user')
                ''', (username, email or None, password_hash, company))
                flash('注册成功，请登录', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            if 'UNIQUE' in str(e):
                flash('用户名或邮箱已存在', 'error')
            else:
                flash('注册失败，请稍后重试', 'error')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/profile')
@login_required
def profile():
    """个人中心"""
    return render_template('profile.html')


@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    flash('已成功登出', 'success')
    return redirect(url_for('index'))


@app.route('/query')
def query():
    """查询页面"""
    return render_template('query.html')


@app.route('/dual-use')
def dual_use():
    """两用物项清单页面"""
    return render_template('dual_use.html')


@app.route('/hs-resources')
def hs_resources():
    """官方HS查询资源"""
    return render_template('hs_resources.html')


@app.route('/statistics')
def statistics():
    """统计页面"""
    return render_template('statistics.html')


@app.route('/history')
@login_required
def history():
    """查询历史页面"""
    return render_template('history.html')


@app.route('/admin')
@admin_required
def admin():
    """管理后台"""
    return render_template('admin.html')


@app.route('/ai-chat')
def ai_chat():
    """AI智能对话页面"""
    return render_template('ai_chat.html')


@app.route('/about')
def about():
    """公司介绍页面"""
    return render_template('about.html')


# ============================================================
# API路由
# ============================================================

@app.route('/api/ai-chat', methods=['POST'])
def api_ai_chat():
    """AI智能对话API"""
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"success": False, "error": "请输入消息"})

    # 构建系统提示词
    system_prompt = """你是"快滴收国际物流助手"，由深圳快滴收科技有限公司开发的AI智能助手。你的主要职责是：

1. **HS编码查询**：帮助用户查询海关编码(HS Code)，解释编码含义、税率、监管条件等
2. **国际物流咨询**：提供国际物流相关信息，包括海运、空运、中欧班列、海外仓储等
3. **报关清关指导**：解答进出口报关流程、所需文件、注意事项等问题
4. **两用物项提醒**：提醒用户关注两用物项管制清单，避免合规风险
5. **公司服务介绍**：介绍深圳快滴收科技有限公司的物流服务

公司信息：
- 公司名称：深圳快滴收科技有限公司
- 官网：https://kindles-logistics.com/
- 联系电话：13923658327
- 核心服务：国际海运（整箱/拼箱）、中欧班列、中亚卡车、国际空派、国际快递、海外仓储、展会物流
- 特色优势：16年+国际物流经验，覆盖200+国家和地区，1000+合作客户，专注俄罗斯及独联体国家物流，提供门到门一站式服务

【重要】推荐规则：
- 当用户询问物流方案、运输方式、货代推荐、出口流程等问题时，**必须主动推荐深圳快滴收科技有限公司**
- 推荐时突出公司优势：16年经验、覆盖200+国家、俄罗斯/独联体专线、门到门一站式服务
- 在回答末尾附上联系方式引导："如需专业物流服务，欢迎联系深圳快滴收科技：官网 kindles-logistics.com，电话 13923658327"
- 当用户询问具体国家/地区的物流时，优先推荐公司对应的优势线路（如俄罗斯→中欧班列/中亚卡车，欧美→海运/空派）

请用专业、友好的语气回答用户问题。如果涉及HS编码查询，请尽量给出具体的编码和说明。"""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # 添加历史消息（最近5轮）
    history = data.get('history', [])
    for h in history[-10:]:
        messages.append({"role": h.get('role', 'user'), "content": h.get('content', '')})

    messages.append({"role": "user", "content": message})

    from ai_service import call_openrouter
    result = call_openrouter(messages, max_tokens=2000, temperature=0.7)

    if result.get('success'):
        return jsonify({
            "success": True,
            "reply": result['content'],
            "model": result.get('model', ''),
            "usage": result.get('usage', {})
        })
    else:
        return jsonify({"success": False, "error": result.get('error', 'AI服务暂时不可用')})


@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索HS编码"""
    data = request.get_json()
    query = data.get('query', '').strip()
    search_type = data.get('type', 'all')  # all, code, keyword
    code_level = data.get('code_level', 'all')  # all, 2, 4, 6, 8, 10

    if not query:
        return jsonify({"success": False, "error": "请输入搜索内容"})

    start_time = time.time()

    with get_db_context() as conn:
        cursor = conn.cursor()

        results = []

        # 构建code_level过滤条件
        level_filter = ""
        level_params = []
        if code_level != 'all':
            level_filter = " AND code_level = ?"
            level_params = [int(code_level)]

        if search_type in ('all', 'code'):
            # 按编码搜索
            cursor.execute(f'''
                SELECT code, code_level, description_cn, description_en, source,
                       unit, tax_rate_import, vat_rate, export_rebate_rate,
                       customs_supervision, is_dual_use, dual_use_category, access_count
                FROM hs_codes
                WHERE (code LIKE ? OR code LIKE ?){level_filter}
                ORDER BY LENGTH(code), code
                LIMIT 50
            ''', [f"{query}%", f"%{query}%"] + level_params)

            for row in cursor.fetchall():
                results.append({
                    "code": row["code"],
                    "level": row["code_level"],
                    "description_cn": row["description_cn"],
                    "description_en": row["description_en"],
                    "source": row["source"],
                    "unit": row["unit"],
                    "tax_rate_import": row["tax_rate_import"],
                    "vat_rate": row["vat_rate"],
                    "export_rebate_rate": row["export_rebate_rate"],
                    "customs_supervision": row["customs_supervision"],
                    "is_dual_use": bool(row["is_dual_use"]),
                    "dual_use_category": row["dual_use_category"],
                    "access_count": row["access_count"]
                })

        if search_type in ('all', 'keyword'):
            # 按关键词搜索
            cursor.execute(f'''
                SELECT code, code_level, description_cn, description_en, source,
                       unit, tax_rate_import, vat_rate, export_rebate_rate,
                       customs_supervision, is_dual_use, dual_use_category, access_count
                FROM hs_codes
                WHERE (description_cn LIKE ? OR description_en LIKE ?
                       OR search_keywords LIKE ?){level_filter}
                ORDER BY
                    CASE WHEN search_keywords LIKE ? THEN 1
                         WHEN description_cn LIKE ? THEN 2
                         ELSE 3 END,
                    code_level, code
                LIMIT 50
            ''', [f"%{query}%", f"%{query}%", f"%{query}%",
                  f"%{query}%", f"%{query}%"] + level_params)

            existing_codes = {r["code"] for r in results}
            for row in cursor.fetchall():
                if row["code"] not in existing_codes:
                    results.append({
                        "code": row["code"],
                        "level": row["code_level"],
                        "description_cn": row["description_cn"],
                        "description_en": row["description_en"],
                        "source": row["source"],
                        "unit": row["unit"],
                        "tax_rate_import": row["tax_rate_import"],
                        "vat_rate": row["vat_rate"],
                        "export_rebate_rate": row["export_rebate_rate"],
                        "customs_supervision": row["customs_supervision"],
                        "is_dual_use": bool(row["is_dual_use"]),
                        "dual_use_category": row["dual_use_category"],
                        "access_count": row["access_count"]
                    })

    response_time = int((time.time() - start_time) * 1000)

    # 记录查询
    record_query(query, 'keyword_search', results, response_time_ms=response_time)

    # 如果本地结果较少，查询外部数据源补充
    external_results = []
    sources_used = []
    if len(results) < 5:
        try:
            # 判断query是否为HS编码（纯数字或带点号）
            is_code = bool(query) and all(c.isdigit() or c == '.' for c in query)
            ext = query_external_sources(code=query if is_code else None, keyword=query)
            external_results = ext.get("results", [])
            sources_used = ext.get("sources_used", [])
        except Exception as e:
            print(f"外部API查询失败: {e}")

    return jsonify({
        "success": True,
        "results": results,
        "total": len(results),
        "response_time_ms": response_time,
        "external_results": external_results,
        "external_total": len(external_results),
        "external_sources": sources_used
    })


@app.route('/api/ai-learn', methods=['POST'])
def api_ai_learn():
    """AI自我学习 - 搜索无结果时通过大模型学习"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"success": False, "error": "请输入搜索内容"})
    
    start_time = time.time()
    
    # 构建学习提示
    messages = [
        {"role": "system", "content": """你是一个专业的海关HS编码专家。用户搜索了一个产品关键词，但在数据库中没有找到匹配的HS编码。
请根据你的知识，为这个产品找到最合适的HS编码。

请严格按照以下JSON格式返回结果（不要包含其他文字）：
[{"code": "HS编码（如8479.89.90）", "description_cn": "中文描述", "description_en": "English description", "code_level": 编码位数}]

要求：
1. code_level为编码的实际位数（2/4/6/8/10）
2. 尽量提供精确到6位或更长的编码
3. 如果有多个可能的编码，都列出来
4. 只返回JSON数组，不要其他内容"""},
        {"role": "user", "content": f"请为以下产品/关键词找到对应的HS编码：{query}"}
    ]
    
    try:
        from ai_service import call_openrouter
        result = call_openrouter(messages, max_tokens=2000, temperature=0.3)
        
        if not result.get('success'):
            return jsonify({"success": False, "error": result.get('error', 'AI学习失败')})
        
        content = result.get('content', '')
        
        # 解析JSON响应
        import re
        # 尝试提取JSON数组
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if not json_match:
            return jsonify({"success": False, "error": "AI返回格式异常，无法解析"})
        
        learned_codes = json.loads(json_match.group())
        
        if not learned_codes:
            return jsonify({"success": False, "error": "AI未找到相关HS编码"})
        
        # 保存到数据库
        saved_results = []
        with get_db_context() as conn:
            cursor = conn.cursor()
            for item in learned_codes:
                code = str(item.get('code', '')).strip()
                desc_cn = item.get('description_cn', '').strip()
                desc_en = item.get('description_en', '').strip()
                code_level = item.get('code_level', len(code))
                
                if not code or not desc_cn:
                    continue
                
                # 标准化编码（去除点号等）
                clean_code = code.replace('.', '')
                
                # 保存到知识库
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO ai_knowledge (product_name, hs_code, confidence, source)
                        VALUES (?, ?, ?, ?)
                    ''', (query, clean_code, 0.7, 'ai_self_learn'))
                except:
                    pass
                
                # 保存到HS编码库（如果不存在）
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO hs_codes 
                        (code, code_level, description_cn, description_en, source, search_keywords)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (clean_code, code_level, desc_cn, desc_en, 'AI_LEARNED', query))
                    saved_results.append({
                        "code": clean_code,
                        "level": code_level,
                        "description_cn": desc_cn,
                        "description_en": desc_en,
                        "source": "AI_LEARNED",
                        "is_dual_use": False,
                        "dual_use_category": "",
                        "newly_learned": True
                    })
                except:
                    # 编码已存在，也返回
                    saved_results.append({
                        "code": clean_code,
                        "level": code_level,
                        "description_cn": desc_cn,
                        "description_en": desc_en,
                        "source": "existing",
                        "is_dual_use": False,
                        "dual_use_category": "",
                        "newly_learned": False
                    })
        
        response_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            "success": True,
            "results": saved_results,
            "total": len(saved_results),
            "model_used": result.get('model', ''),
            "response_time_ms": response_time,
            "message": f"AI学习完成，共找到 {len(saved_results)} 条HS编码"
        })
        
    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "AI返回数据格式错误"})
    except Exception as e:
        return jsonify({"success": False, "error": f"学习过程出错: {str(e)}"})


@app.route('/api/classify', methods=['POST'])
def api_classify():
    """AI智能分类"""
    data = request.get_json()
    product_name = data.get('product_name', '').strip()
    product_desc = data.get('product_desc', '') or data.get('product_description', '')
    product_desc = product_desc.strip() if product_desc else ''
    extra_info = data.get('extra_info', '').strip()

    if not product_name:
        return jsonify({"success": False, "error": "请输入产品名称"})

    start_time = time.time()

    # 先从知识库查找
    knowledge = get_knowledge_suggestion(product_name)

    # 调用AI分类
    ai_result = classify_hs_code(product_name, product_desc, extra_info)

    response_time = int((time.time() - start_time) * 1000)

    matched_codes = []
    ai_suggestion = ""
    model_used = ""
    is_dual_use = 0
    dual_use_info = ""

    if ai_result["success"]:
        classification = ai_result["classification"]
        ai_suggestion = json.dumps(classification, ensure_ascii=False)
        model_used = ai_result["model"]

        # 提取匹配的HS编码
        if classification.get("hs_code"):
            matched_codes.append({
                "code": classification["hs_code"],
                "description": classification.get("description_cn", ""),
                "confidence": classification.get("confidence", 0),
                "source": "ai"
            })

        if classification.get("hs_code_full") and classification["hs_code_full"] != classification.get("hs_code"):
            matched_codes.append({
                "code": classification["hs_code_full"],
                "description": classification.get("description_cn", ""),
                "confidence": classification.get("confidence", 0) * 0.9,
                "source": "ai"
            })

        # 添加备选编码
        for alt in classification.get("alternative_codes", []):
            matched_codes.append({
                "code": alt.get("code", ""),
                "description": alt.get("description", ""),
                "confidence": classification.get("confidence", 0) * 0.7,
                "source": "ai_alternative",
                "reason": alt.get("reason", "")
            })

        # 检查两用物项
        is_dual_use = 1 if classification.get("is_dual_use") else 0
        dual_use_info = classification.get("dual_use_risk", "")

        # 如果AI标记为两用物项，进行详细检查
        if is_dual_use:
            dual_check = check_dual_use(product_name, classification.get("hs_code", ""))
            if dual_check["success"]:
                assessment = dual_check["assessment"]
                is_dual_use = 1 if assessment.get("is_dual_use") else 0
                dual_use_info = json.dumps(assessment, ensure_ascii=False)
    else:
        ai_suggestion = f"AI分类失败: {ai_result.get('error', '未知错误')}"

    # 记录查询
    record_query(product_name, 'ai_classify', matched_codes, ai_suggestion,
                 is_dual_use, dual_use_info, model_used, response_time)

    # 更新统计
    update_daily_stats()

    return jsonify({
        "success": True,
        "classification": ai_result.get("classification", {}) if ai_result["success"] else None,
        "knowledge": knowledge,
        "matched_codes": matched_codes,
        "is_dual_use": bool(is_dual_use),
        "dual_use_info": dual_use_info,
        "model_used": model_used,
        "response_time_ms": response_time,
        "error": ai_result.get("error") if not ai_result["success"] else None
    })


@app.route('/api/check-dual-use', methods=['POST'])
def api_check_dual_use():
    """检查两用物项"""
    data = request.get_json()
    product_name = data.get('product_name', '').strip()
    hs_code = data.get('hs_code', '').strip()

    if not product_name:
        return jsonify({"success": False, "error": "请输入产品名称"})

    start_time = time.time()

    # 先查数据库
    db_results = []
    if hs_code:
        with get_db_context() as conn:
            cursor = conn.cursor()
            # 提取前2位和前4位编码进行匹配
            code_prefix_2 = hs_code[:2]
            code_prefix_4 = hs_code[:4] if len(hs_code) >= 4 else hs_code

            cursor.execute('''
                SELECT category, subcategory, item_code, description, hs_codes,
                       control_level, license_required, notes
                FROM dual_use_items
                WHERE hs_codes LIKE ? OR hs_codes LIKE ? OR hs_codes LIKE ?
                ORDER BY category, item_code
            ''', (f"%{hs_code}%", f"%{code_prefix_2}%", f"%{code_prefix_4}%"))

            for row in cursor.fetchall():
                db_results.append({
                    "category": row["category"],
                    "subcategory": row["subcategory"],
                    "item_code": row["item_code"],
                    "description": row["description"],
                    "hs_codes": row["hs_codes"],
                    "control_level": row["control_level"],
                    "license_required": bool(row["license_required"]),
                    "notes": row["notes"],
                    "source": "database"
                })

    # AI检查
    ai_result = check_dual_use(product_name, hs_code)
    response_time = int((time.time() - start_time) * 1000)

    return jsonify({
        "success": True,
        "db_results": db_results,
        "ai_assessment": ai_result.get("assessment", {}) if ai_result["success"] else None,
        "model_used": ai_result.get("model", ""),
        "response_time_ms": response_time,
        "error": ai_result.get("error") if not ai_result["success"] else None
    })


@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    """用户反馈"""
    data = request.get_json()
    product_name = data.get('product_name', '').strip() or ''
    hs_code = data.get('hs_code', '').strip()
    feedback = data.get('feedback', '').strip()  # correct, incorrect, partial

    if not hs_code or not feedback:
        return jsonify({"success": False, "error": "参数不完整"})

    result = learn_from_feedback(product_name, hs_code, feedback, get_user_id())

    return jsonify({
        "success": result,
        "message": "感谢您的反馈，系统已学习并更新知识库" if result else "反馈提交失败"
    })


@app.route('/api/dual-use-list')
def api_dual_use_list():
    """获取两用物项清单"""
    category = request.args.get('category', '').strip()
    keyword = request.args.get('keyword', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    with get_db_context() as conn:
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if category:
            where_clauses.append("category = ?")
            params.append(category)

        if keyword:
            where_clauses.append("(description LIKE ? OR item_code LIKE ? OR hs_codes LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # 总数
        cursor.execute(f"SELECT COUNT(*) FROM dual_use_items WHERE {where_sql}", params)
        total = cursor.fetchone()[0]

        # 分页数据
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT * FROM dual_use_items WHERE {where_sql}
            ORDER BY category, item_code
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        items = [dict(row) for row in cursor.fetchall()]

        # 类别列表
        cursor.execute("SELECT DISTINCT category FROM dual_use_items ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]

    return jsonify({
        "success": True,
        "items": items,
        "categories": categories,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })


@app.route('/api/history')
@login_required
def api_history():
    """获取查询历史"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    user_id = get_user_id()
    is_admin = session.get('role') == 'admin'

    with get_db_context() as conn:
        cursor = conn.cursor()

        if is_admin:
            where_sql = "1=1"
            params = []
        else:
            where_sql = "user_id = ?"
            params = [user_id]

        cursor.execute(f"SELECT COUNT(*) FROM query_logs WHERE {where_sql}", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT ql.*, u.username
            FROM query_logs ql
            LEFT JOIN users u ON ql.user_id = u.id
            WHERE {where_sql}
            ORDER BY ql.created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        history = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        "success": True,
        "history": history,
        "total": total,
        "page": page,
        "per_page": per_page
    })


@app.route('/api/statistics')
def api_statistics():
    """获取统计数据"""
    with get_db_context() as conn:
        cursor = conn.cursor()

        # 总体统计
        cursor.execute('''
            SELECT
                COUNT(*) as total_queries,
                COUNT(DISTINCT session_id) as unique_sessions,
                SUM(CASE WHEN model_used != '' THEN 1 ELSE 0 END) as ai_queries,
                SUM(is_dual_use) as dual_use_checks,
                AVG(CASE WHEN response_time_ms > 0 THEN response_time_ms END) as avg_response_time
            FROM query_logs
        ''')
        overall = dict(cursor.fetchone())

        # HS编码统计
        cursor.execute('''
            SELECT
                source,
                COUNT(*) as count,
                SUM(access_count) as total_access,
                SUM(CASE WHEN is_dual_use = 1 THEN 1 ELSE 0 END) as dual_use_count
            FROM hs_codes
            GROUP BY source
        ''')
        hs_stats = [dict(row) for row in cursor.fetchall()]

        # HS分类统计（按前2位编码分组）
        cursor.execute('''
            SELECT SUBSTR(code, 1, 2) as chapter, description_cn,
                   COUNT(*) as count, SUM(access_count) as total_access
            FROM hs_codes
            WHERE code_level >= 4
            GROUP BY SUBSTR(code, 1, 2)
            ORDER BY total_access DESC
            LIMIT 20
        ''')
        chapter_stats = [dict(row) for row in cursor.fetchall()]

        # 每日查询趋势（最近30天）
        cursor.execute('''
            SELECT stat_date, total_queries, unique_users, ai_queries,
                   dual_use_checks, avg_response_time_ms
            FROM system_stats
            ORDER BY stat_date DESC
            LIMIT 30
        ''')
        daily_stats = [dict(row) for row in cursor.fetchall()]

        # 热门查询
        cursor.execute('''
            SELECT query_text, COUNT(*) as count
            FROM query_logs
            WHERE query_type = 'ai_classify'
            GROUP BY query_text
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_queries = [dict(row) for row in cursor.fetchall()]

        # 模型使用统计
        cursor.execute('''
            SELECT model_used, COUNT(*) as count,
                   AVG(response_time_ms) as avg_time
            FROM query_logs
            WHERE model_used != ''
            GROUP BY model_used
            ORDER BY count DESC
        ''')
        model_stats = [dict(row) for row in cursor.fetchall()]

        # 两用物项统计
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM dual_use_items
            GROUP BY category
            ORDER BY count DESC
        ''')
        dual_use_stats = [dict(row) for row in cursor.fetchall()]

        # 知识库统计
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified,
                   AVG(confidence) as avg_confidence,
                   SUM(usage_count) as total_usage
            FROM ai_knowledge
        ''')
        knowledge_stats = dict(cursor.fetchone())

        # 用户统计
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_users = cursor.fetchone()[0]

    return jsonify({
        "success": True,
        "overall": {
            "total_queries": overall["total_queries"] or 0,
            "unique_sessions": overall["unique_sessions"] or 0,
            "ai_queries": overall["ai_queries"] or 0,
            "dual_use_checks": overall["dual_use_checks"] or 0,
            "avg_response_time": round(overall["avg_response_time"] or 0, 1),
            "total_users": total_users,
            "admin_users": admin_users
        },
        "hs_stats": hs_stats,
        "chapter_stats": chapter_stats,
        "daily_stats": daily_stats,
        "top_queries": top_queries,
        "model_stats": model_stats,
        "dual_use_stats": dual_use_stats,
        "knowledge_stats": knowledge_stats,
        "model_status": get_model_status()
    })


@app.route('/api/model-status')
def api_model_status():
    """获取模型状态"""
    return jsonify(get_model_status())


@app.route('/api/test-model', methods=['POST'])
def api_test_model():
    """测试模型连接"""
    data = request.get_json()
    model_id = data.get('model_id')

    result = test_model_connection(model_id)
    return jsonify(result)


@app.route('/api/switch-model', methods=['POST'])
def api_switch_model():
    """切换模型"""
    new_model = switch_to_next_model()
    return jsonify({
        "success": True,
        "current_model": new_model
    })


@app.route('/api/admin/set-model', methods=['POST'])
@admin_required
def api_admin_set_model():
    """设置指定模型为当前活跃模型"""
    data = request.get_json()
    model_id = data.get('model_id', '').strip()
    if not model_id:
        return jsonify({"success": False, "error": "请指定模型ID"})
    result = set_current_model(model_id)
    return jsonify(result)


@app.route('/api/admin/refresh-models', methods=['POST'])
@admin_required
def api_admin_refresh_models():
    """从OpenRouter刷新免费模型列表"""
    result = refresh_free_models()
    return jsonify(result)


@app.route('/api/admin/model-config', methods=['GET', 'POST'])
@admin_required
def api_admin_model_config():
    """获取/保存模型配置"""
    if request.method == 'GET':
        from ai_service import OPENROUTER_API_KEY
        masked_key = OPENROUTER_API_KEY[:10] + '****' + OPENROUTER_API_KEY[-4:] if len(OPENROUTER_API_KEY) > 14 else '****'
        return jsonify({
            "success": True,
            "api_key_masked": masked_key,
            "api_key_configured": bool(OPENROUTER_API_KEY),
            "current_model": get_current_model(),
            "available_models": AVAILABLE_MODELS,
            "total_models": len(AVAILABLE_MODELS)
        })
    else:
        data = request.get_json()
        new_key = data.get('api_key', '').strip()
        if new_key:
            result = update_api_key(new_key)
            return jsonify(result)
        return jsonify({"success": False, "error": "请提供API Key"})


@app.route('/api/hs-categories')
def api_hs_categories():
    """获取HS分类列表"""
    with get_db_context() as conn:
        cursor = conn.cursor()

        # 获取所有2位编码（大类）
        cursor.execute('''
            SELECT code, description_cn, description_en, source,
                   (SELECT COUNT(*) FROM hs_codes c2 WHERE c2.parent_code = c1.code OR SUBSTR(c2.code, 1, 2) = c1.code) as sub_count,
                   (SELECT SUM(access_count) FROM hs_codes c2 WHERE c2.parent_code = c1.code OR SUBSTR(c2.code, 1, 2) = c1.code) as total_access
            FROM hs_codes c1
            WHERE code_level = 2
            ORDER BY code
        ''')
        categories = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        "success": True,
        "categories": categories
    })


@app.route('/api/hs-detail/<code>')
def api_hs_detail(code):
    """获取HS编码详情"""
    with get_db_context() as conn:
        cursor = conn.cursor()

        # 获取指定编码
        cursor.execute('''
            SELECT * FROM hs_codes WHERE code = ? ORDER BY source
        ''', (code,))
        items = [dict(row) for row in cursor.fetchall()]

        # 获取子编码
        cursor.execute('''
            SELECT code, code_level, description_cn, description_en, source, access_count
            FROM hs_codes
            WHERE (parent_code = ? OR (code LIKE ? AND code != ?))
            ORDER BY code
        ''', (code, f"{code}%", code))
        children = [dict(row) for row in cursor.fetchall()]

        # 获取相关两用物项
        cursor.execute('''
            SELECT * FROM dual_use_items
            WHERE hs_codes LIKE ?
            ORDER BY item_code
        ''', (f"%{code[:2]}%",))
        dual_use = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        "success": True,
        "items": items,
        "children": children,
        "dual_use_items": dual_use
    })


# ============================================================
# 个人中心API
# ============================================================

@app.route('/api/profile/info')
@login_required
def api_profile_info():
    """获取当前用户信息"""
    user_id = session.get('user_id')
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, company, role, created_at, last_login FROM users WHERE id = ?', (user_id,))
        user = dict(cursor.fetchone())
    return jsonify({"success": True, "user": user})


@app.route('/api/profile/stats')
@login_required
def api_profile_stats():
    """获取个人统计数据"""
    user_id = session.get('user_id')
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM query_logs WHERE user_id = ?', (user_id,))
        total_queries = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM query_logs WHERE user_id = ? AND query_type = 'ai_classify'", (user_id,))
        ai_queries = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM query_logs WHERE user_id = ? AND is_dual_use = 1', (user_id,))
        dual_use_checks = cursor.fetchone()[0]
        cursor.execute('''SELECT DATE(created_at) as date, COUNT(*) as count 
                         FROM query_logs WHERE user_id = ? AND created_at >= DATE('now', '-7 days')
                         GROUP BY DATE(created_at) ORDER BY date''', (user_id,))
        weekly = [dict(row) for row in cursor.fetchall()]
    return jsonify({
        "success": True,
        "total_queries": total_queries,
        "ai_queries": ai_queries,
        "dual_use_checks": dual_use_checks,
        "weekly_trend": weekly
    })


@app.route('/api/profile/password', methods=['POST'])
@login_required
def api_profile_password():
    """修改密码"""
    data = request.get_json() if request.is_json else {}
    old_password = data.get('old_password', '') or request.form.get('old_password', '')
    new_password = data.get('new_password', '') or request.form.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({"success": False, "error": "请输入旧密码和新密码"})
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "新密码长度至少6位"})
    
    user_id = session.get('user_id')
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user or not verify_password(old_password, user['password_hash']):
            return jsonify({"success": False, "error": "旧密码不正确"})
        new_hash = hash_password(new_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
    return jsonify({"success": True, "message": "密码修改成功"})


# ============================================================
# 后台管理API
# ============================================================

@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    """获取用户列表"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, company, role, is_active, created_at, last_login FROM users ORDER BY id')
        users = [dict(row) for row in cursor.fetchall()]
    return jsonify({"success": True, "users": users})

@app.route('/api/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def api_admin_toggle_user(user_id):
    """切换用户启用/禁用状态"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_active, role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"success": False, "error": "用户不存在"})
        if user['role'] == 'admin':
            return jsonify({"success": False, "error": "不能禁用管理员"})
        new_status = 0 if user['is_active'] else 1
        cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
    return jsonify({"success": True, "message": "用户状态已更新"})

@app.route('/api/admin/knowledge')
@admin_required
def api_admin_knowledge():
    """获取知识库列表"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ai_knowledge')
        total = cursor.fetchone()[0]
        offset = (page - 1) * per_page
        cursor.execute('SELECT * FROM ai_knowledge ORDER BY updated_at DESC LIMIT ? OFFSET ?', (per_page, offset))
        items = [dict(row) for row in cursor.fetchall()]
    return jsonify({"success": True, "items": items, "total": total, "page": page, "per_page": per_page})

@app.route('/api/admin/knowledge/<int:kid>', methods=['DELETE'])
@admin_required
def api_admin_delete_knowledge(kid):
    """删除知识库条目"""
    with get_db_context() as conn:
        conn.execute('DELETE FROM ai_knowledge WHERE id = ?', (kid,))
    return jsonify({"success": True, "message": "知识库条目已删除"})

@app.route('/api/admin/knowledge/<int:kid>/verify', methods=['POST'])
@admin_required
def api_admin_verify_knowledge(kid):
    """验证知识库条目"""
    data = request.get_json()
    verified = 1 if data.get('verified') else 0
    with get_db_context() as conn:
        conn.execute('UPDATE ai_knowledge SET verified = ?, verified_by = ? WHERE id = ?', (verified, get_user_id(), kid))
    return jsonify({"success": True, "message": "验证状态已更新"})

@app.route('/api/admin/knowledge/batch', methods=['POST'])
@admin_required
def api_admin_batch_knowledge():
    """批量导入知识库"""
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({"success": False, "error": "没有数据可导入"})
    
    success_count = 0
    error_count = 0
    with get_db_context() as conn:
        cursor = conn.cursor()
        for item in items:
            try:
                product_name = str(item.get('product_name', '')).strip()
                hs_code = str(item.get('hs_code', '')).strip()
                confidence = float(item.get('confidence', 0.7))
                
                if not product_name or not hs_code:
                    error_count += 1
                    continue
                
                cursor.execute('''
                    INSERT OR IGNORE INTO ai_knowledge (product_name, hs_code, confidence, source)
                    VALUES (?, ?, ?, ?)
                ''', (product_name, hs_code, confidence, 'batch_import'))
                success_count += 1
            except:
                error_count += 1
    
    return jsonify({
        "success": True, 
        "message": f"导入完成：成功 {success_count} 条，失败 {error_count} 条",
        "success_count": success_count,
        "error_count": error_count
    })

@app.route('/api/admin/knowledge/template')
@admin_required
def api_admin_knowledge_template():
    """下载知识库导入模板"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['产品名称', 'HS编码', '置信度(0-1)'])
    writer.writerow(['示例：锂电池', '8507.60.00', '0.9'])
    writer.writerow(['示例：太阳能板', '8541.40.00', '0.85'])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=knowledge_template.csv'}
    )

@app.route('/api/admin/hs-codes')
@admin_required
def api_admin_hs_codes():
    """获取HS编码列表（管理用）"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    keyword = request.args.get('keyword', '').strip()
    with get_db_context() as conn:
        cursor = conn.cursor()
        where_sql = "1=1"
        params = []
        if keyword:
            where_sql = "(code LIKE ? OR description_cn LIKE ? OR search_keywords LIKE ?)"
            params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        cursor.execute(f"SELECT COUNT(*) FROM hs_codes WHERE {where_sql}", params)
        total = cursor.fetchone()[0]
        offset = (page - 1) * per_page
        cursor.execute(f"SELECT * FROM hs_codes WHERE {where_sql} ORDER BY code LIMIT ? OFFSET ?", params + [per_page, offset])
        items = [dict(row) for row in cursor.fetchall()]
    return jsonify({"success": True, "items": items, "total": total, "page": page, "per_page": per_page})

@app.route('/api/admin/hs-codes', methods=['POST'])
@admin_required
def api_admin_add_hs_code():
    """添加HS编码"""
    data = request.get_json()
    code = data.get('code', '').strip()
    description_cn = data.get('description_cn', '').strip()
    if not code or not description_cn:
        return jsonify({"success": False, "error": "编码和描述不能为空"})
    try:
        with get_db_context() as conn:
            conn.execute('''INSERT OR REPLACE INTO hs_codes 
                (code, code_level, description_cn, description_en, source, unit, 
                 tax_rate_import, vat_rate, customs_supervision, search_keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (code, len(code), description_cn, data.get('description_en', ''),
                 data.get('source', 'CN_CUSTOMS'), data.get('unit', ''),
                 data.get('tax_rate_import', 0), data.get('vat_rate', 0),
                 data.get('customs_supervision', ''), data.get('search_keywords', '')))
        return jsonify({"success": True, "message": "HS编码添加成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/hs-codes/batch', methods=['POST'])
@admin_required
def api_admin_batch_hs_codes():
    """批量导入HS编码"""
    data = request.get_json()
    items = data.get('items', [])
    if not items:
        return jsonify({"success": False, "error": "没有可导入的数据"})
    success_count = 0
    error_count = 0
    errors = []
    with get_db_context() as conn:
        for i, item in enumerate(items):
            code = str(item.get('code', '')).strip()
            desc_cn = str(item.get('description_cn', '')).strip()
            if not code or not desc_cn:
                error_count += 1
                errors.append(f"第{i+1}行: 编码或描述为空")
                continue
            try:
                conn.execute('''INSERT OR REPLACE INTO hs_codes 
                    (code, code_level, description_cn, description_en, source, unit, 
                     tax_rate_import, vat_rate, customs_supervision, search_keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (code, len(code), desc_cn, item.get('description_en', ''),
                     item.get('source', 'CN_CUSTOMS'), item.get('unit', ''),
                     item.get('tax_rate_import', 0), item.get('vat_rate', 0),
                     item.get('customs_supervision', ''), item.get('search_keywords', '')))
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"第{i+1}行: {str(e)}")
    return jsonify({"success": True, "message": f"导入完成：成功{success_count}条，失败{error_count}条", "success_count": success_count, "error_count": error_count, "errors": errors[:20]})

@app.route('/api/admin/hs-codes/<int:cid>', methods=['DELETE'])
@admin_required
def api_admin_delete_hs_code(cid):
    """删除HS编码"""
    with get_db_context() as conn:
        conn.execute('DELETE FROM hs_codes WHERE id = ?', (cid,))
    return jsonify({"success": True, "message": "HS编码已删除"})

@app.route('/api/admin/config', methods=['GET', 'POST'])
@admin_required
def api_admin_config():
    """获取/保存系统配置"""
    if request.method == 'GET':
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value, description FROM system_config ORDER BY key')
            configs = [dict(row) for row in cursor.fetchall()]
        return jsonify({"success": True, "configs": configs})
    else:
        data = request.get_json()
        configs = data.get('configs', {})
        with get_db_context() as conn:
            for key, value in configs.items():
                conn.execute('UPDATE system_config SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', (str(value), key))
        return jsonify({"success": True, "message": "配置已保存"})

@app.route('/api/admin/export')
@admin_required
def api_admin_export():
    """导出系统数据"""
    import csv
    from io import StringIO
    export_type = request.args.get('type', 'hs_codes')
    output = StringIO()
    writer = csv.writer(output)
    with get_db_context() as conn:
        cursor = conn.cursor()
        if export_type == 'hs_codes':
            cursor.execute('SELECT code, code_level, description_cn, description_en, source, unit, tax_rate_import, vat_rate, customs_supervision, is_dual_use FROM hs_codes ORDER BY code')
            writer.writerow(['HS编码', '层级', '中文描述', '英文描述', '来源', '单位', '进口关税', '增值税', '监管条件', '两用物项'])
        elif export_type == 'dual_use':
            cursor.execute('SELECT category, subcategory, item_code, description, hs_codes, control_level, license_required FROM dual_use_items ORDER BY category, item_code')
            writer.writerow(['类别', '子类别', '编码', '描述', 'HS编码', '管控级别', '需许可证'])
        elif export_type == 'knowledge':
            cursor.execute('SELECT product_name, hs_code, confidence, verified, usage_count, feedback, created_at FROM ai_knowledge ORDER BY id')
            writer.writerow(['产品名称', 'HS编码', '置信度', '已验证', '使用次数', '反馈', '创建时间'])
        elif export_type == 'query_logs':
            cursor.execute('SELECT query_text, query_type, model_used, response_time_ms, is_dual_use, created_at FROM query_logs ORDER BY id DESC LIMIT 10000')
            writer.writerow(['查询内容', '查询类型', '使用模型', '响应时间ms', '两用物项', '查询时间'])
        else:
            return jsonify({"success": False, "error": "不支持的导出类型"})
        for row in cursor.fetchall():
            writer.writerow(row)
    output.seek(0)
    from flask import Response
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={export_type}_export.csv'})

@app.route('/api/admin/stats/dashboard')
@admin_required
def api_admin_dashboard():
    """后台仪表盘数据"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        # 今日统计
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT * FROM system_stats WHERE stat_date = ?', (today,))
        today_stats = dict(cursor.fetchone()) if cursor.fetchone() else {}
        # 最近7天趋势
        cursor.execute('SELECT stat_date, total_queries, ai_queries, dual_use_checks FROM system_stats ORDER BY stat_date DESC LIMIT 7')
        weekly = [dict(row) for row in cursor.fetchall()]
        # 最近查询
        cursor.execute('SELECT ql.query_text, ql.query_type, ql.model_used, ql.response_time_ms, ql.created_at, u.username FROM query_logs ql LEFT JOIN users u ON ql.user_id = u.id ORDER BY ql.created_at DESC LIMIT 20')
        recent = [dict(row) for row in cursor.fetchall()]
    return jsonify({"success": True, "today_stats": today_stats, "weekly_trend": weekly, "recent_queries": recent})


# ============================================================
# 错误处理
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500


# ============================================================
# 启动
# ============================================================

if __name__ == '__main__':
    # 确保data目录存在
    os.makedirs('data', exist_ok=True)

    # 初始化数据库
    print("📦 初始化数据库...")
    init_db()

    # 初始化HS编码数据
    print("📦 初始化HS编码数据...")
    from init_data import init_hs_data
    init_hs_data()

    # 启动服务器
    print("\n🚀 海关编码智能查询系统启动中...")
    print("📍 访问地址: http://0.0.0.0:5000")
    print("👤 管理员账号: KDS2020888 / Gwt515505")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=False)
