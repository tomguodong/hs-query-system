# -*- coding: utf-8 -*-
"""
海关编码智能查询系统 - 数据库模型
HS Code Intelligent Query System - Database Models
Version: 1.0.0
"""

import sqlite3
import json
import hashlib
import secrets
from datetime import datetime
from contextlib import contextmanager

DB_PATH = 'data/hs_system.db'


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db_context():
    """数据库上下文管理器"""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库表结构"""
    with get_db_context() as conn:
        cursor = conn.cursor()

        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                company TEXT DEFAULT '',
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                api_key TEXT
            )
        ''')

        # HS编码表（中国海关 + WCO国际）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hs_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                code_level INTEGER DEFAULT 2,
                description_cn TEXT NOT NULL,
                description_en TEXT DEFAULT '',
                source TEXT DEFAULT 'CN_CUSTOMS',
                parent_code TEXT,
                unit TEXT DEFAULT '',
                tax_rate_import REAL DEFAULT 0,
                tax_rate_export REAL DEFAULT 0,
                vat_rate REAL DEFAULT 0,
                export_rebate_rate REAL DEFAULT 0,
                customs_supervision TEXT DEFAULT '',
                ciq_code TEXT DEFAULT '',
                declaration_elements TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                is_dual_use INTEGER DEFAULT 0,
                dual_use_category TEXT DEFAULT '',
                search_keywords TEXT DEFAULT '',
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, source)
            )
        ''')

        # 两用物项清单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dual_use_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                item_code TEXT NOT NULL,
                description TEXT NOT NULL,
                hs_codes TEXT DEFAULT '',
                control_level TEXT DEFAULT '',
                license_required INTEGER DEFAULT 1,
                notes TEXT DEFAULT '',
                effective_date TEXT DEFAULT '',
                source TEXT DEFAULT 'MOFCOM',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 查询记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT DEFAULT '',
                query_text TEXT NOT NULL,
                query_type TEXT DEFAULT 'product_name',
                matched_hs_codes TEXT DEFAULT '[]',
                ai_suggestion TEXT DEFAULT '',
                is_dual_use INTEGER DEFAULT 0,
                dual_use_info TEXT DEFAULT '',
                model_used TEXT DEFAULT '',
                response_time_ms INTEGER DEFAULT 0,
                ip_address TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # AI学习知识库表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                hs_code TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                source TEXT DEFAULT 'ai_suggestion',
                verified INTEGER DEFAULT 0,
                verified_by INTEGER,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                feedback TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (verified_by) REFERENCES users(id)
            )
        ''')

        # 系统统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date TEXT NOT NULL,
                total_queries INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                ai_queries INTEGER DEFAULT 0,
                dual_use_checks INTEGER DEFAULT 0,
                dual_use_hits INTEGER DEFAULT 0,
                top_queries TEXT DEFAULT '[]',
                hs_category_stats TEXT DEFAULT '{}',
                model_usage TEXT DEFAULT '{}',
                avg_response_time_ms REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stat_date)
            )
        ''')

        # 系统配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hs_codes_code ON hs_codes(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hs_codes_desc ON hs_codes(description_cn)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hs_codes_keywords ON hs_codes(search_keywords)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hs_codes_source ON hs_codes(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_query_logs_user ON query_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_query_logs_time ON query_logs(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_knowledge_product ON ai_knowledge(product_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_knowledge_hs ON ai_knowledge(hs_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dual_use_items_code ON dual_use_items(item_code)')

        # 插入默认配置
        default_configs = [
            ('default_model', 'nvidia/nemotron-3-super-120b-a12b:free', '默认AI模型'),
            ('fallback_model', 'minimax/minimax-m2.5:free', '备用AI模型'),
            ('max_search_results', '20', '最大搜索结果数'),
            ('ai_confidence_threshold', '0.7', 'AI建议置信度阈值'),
            ('dual_use_check_enabled', '1', '是否启用两用物项检测'),
            ('learning_enabled', '1', '是否启用AI自我学习'),
            ('version', '1.0.0', '系统版本号'),
        ]
        for key, value, desc in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO system_config (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, desc))

        # 创建默认管理员账户
        admin_password = hash_password('admin123')
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role, company)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', 'admin@hs-system.com', admin_password, 'admin', '系统管理'))
        except sqlite3.IntegrityError:
            pass

        print("✅ 数据库初始化完成")


def hash_password(password):
    """密码哈希"""
    salt = secrets.token_hex(16)
    hash_val = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hash_val}"


def verify_password(password, password_hash):
    """验证密码"""
    salt, hash_val = password_hash.split(':')
    return hashlib.sha256((salt + password).encode()).hexdigest() == hash_val


if __name__ == '__main__':
    init_db()
