# 宝塔面板部署指南 — 快滴收 · HS智能查询系统

本文档详细介绍如何将 HS智能查询系统 部署到宝塔面板（BT Panel）服务器上，适用于生产环境。

---

## 1. 环境要求

| 项目 | 最低要求 |
|------|----------|
| **操作系统** | CentOS 7+ / Ubuntu 18.04+ / Debian 9+ |
| **Python** | 3.8 及以上（推荐 3.10） |
| **pip** | 最新稳定版 |
| **宝塔面板** | 7.x 及以上版本 |
| **内存** | 建议 1GB 以上 |
| **磁盘** | 建议 10GB 以上可用空间 |

---

## 2. 宝塔面板准备

### 2.1 安装 Python 项目管理器

1. 登录宝塔面板后台
2. 进入 **软件商店**
3. 搜索 **Python项目管理器**（宝塔官方插件）
4. 点击 **安装**，等待安装完成

> 如果软件商店中找不到该插件，请确保宝塔面板已更新到最新版本。

### 2.2 安装 Nginx

1. 进入 **软件商店**
2. 搜索 **Nginx**
3. 选择最新稳定版，点击 **安装**
4. 安装完成后确认 Nginx 状态为"运行中"

### 2.3 安装 Python 环境

如果服务器尚未安装 Python 3.8+，可通过以下方式安装：

```bash
# CentOS
yum install python3 python3-pip -y

# Ubuntu / Debian
apt update && apt install python3 python3-pip python3-venv -y
```

---

## 3. 部署步骤

### 3.1 上传代码

1. 在宝塔面板中进入 **文件** 管理
2. 进入目录 `/www/wwwroot/`
3. 创建目录 `hs_query_system`
4. 将项目所有文件上传到 `/www/wwwroot/hs_query_system/`

目录结构应如下所示：

```
/www/wwwroot/hs_query_system/
├── app.py              # Flask 主应用
├── ai_service.py       # AI 服务模块
├── external_api.py     # 外部数据源集成
├── models.py           # 数据库模型
├── init_data.py        # 数据库初始化脚本
├── requirements.txt    # Python 依赖
├── data/
│   └── hs_system.db    # SQLite 数据库
├── static/             # 静态资源
└── templates/          # HTML 模板
```

### 3.2 设置文件权限

```bash
# 设置项目目录所有者
chown -R www:www /www/wwwroot/hs_query_system/

# 设置目录权限
chmod -R 755 /www/wwwroot/hs_query_system/

# 确保 data 目录可写
chmod -R 775 /www/wwwroot/hs_query_system/data/
```

### 3.3 Python 项目管理器配置

1. 进入宝塔面板 **软件商店** → **Python项目管理器** → **设置**
2. 点击 **添加项目**，填写以下配置：

| 配置项 | 值 |
|--------|-----|
| **项目名称** | hs_query_system |
| **项目路径** | /www/wwwroot/hs_query_system |
| **项目启动文件** | app.py |
| **启动命令** | `python3 app.py` |
| **端口** | 5000 |
| **Python版本** | 选择已安装的 Python 3.x |
| **是否开机启动** | 是 |

3. 点击 **确定** 保存配置

### 3.4 安装依赖

在宝塔面板的 Python 项目管理器中，找到刚创建的项目，点击 **模块** 或 **pip管理**，安装以下依赖：

```bash
cd /www/wwwroot/hs_query_system
pip3 install -r requirements.txt
```

如果 `requirements.txt` 不存在，手动安装核心依赖：

```bash
pip3 install flask requests beautifulsoup4 lxml pyhscodes
```

### 3.5 初始化数据库

```bash
cd /www/wwwroot/hs_query_system
python3 init_data.py
```

---

## 4. Nginx 反向代理配置

### 4. 添加站点

1. 在宝塔面板中进入 **网站** → **添加站点**
2. 填写域名（如 `hs.yourdomain.com`）
3. 根目录可设为 `/www/wwwroot/hs_query_system`（仅用于存放静态文件）
4. PHP版本选择 **纯静态**

### 4. 配置反向代理

点击站点 **设置** → **反向代理** → **添加反向代理**：

| 配置项 | 值 |
|--------|-----|
| **代理名称** | hs_query |
| **目标URL** | `http://127.0.0.1:5000` |

或直接编辑站点的 Nginx 配置文件（**设置** → **配置文件**），替换为以下内容：

```nginx
server {
    listen 80;
    server_name hs.yourdomain.com;  # 替换为你的域名

    # 访问日志
    access_log /www/wwwlogs/hs_query_system.log;
    error_log /www/wwwlogs/hs_query_system.error.log;

    # 客户端请求体大小限制
    client_max_body_size 16m;

    # 静态文件缓存配置
    location /static/ {
        alias /www/wwwroot/hs_query_system/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 反向代理到 Flask 应用
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（可选，用于AI聊天等实时功能）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 60s;

        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

配置完成后点击 **保存**，Nginx 会自动重载配置。

---

## 5. SSL 证书配置

### 5.1 申请 Let's Encrypt 免费证书

1. 进入站点 **设置** → **SSL** → **Let's Encrypt**
2. 勾选域名
3. 点击 **申请**
4. 申请成功后开启 **强制HTTPS**

### 5.2 SSL 配置（自动生成）

宝塔面板会自动在 Nginx 配置中添加 SSL 相关设置。确认配置中包含以下内容：

```nginx
server {
    listen 443 ssl http2;
    server_name hs.yourdomain.com;

    ssl_certificate    /www/server/panel/vhost/cert/hs.yourdomain.com/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/hs.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # ... 其余配置同上 ...
}

# HTTP 自动跳转 HTTPS
server {
    listen 80;
    server_name hs.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

---

## 6. 进程守护（Supervisor 配置）

如果 Python 项目管理器的进程守护功能不稳定，可手动配置 Supervisor。

### 6.1 安装 Supervisor

```bash
# CentOS
yum install supervisor -y
systemctl enable supervisord
systemctl start supervisord

# Ubuntu / Debian
apt install supervisor -y
systemctl enable supervisor
systemctl start supervisor
```

### 6.2 创建配置文件

创建 Supervisor 配置文件：

```bash
cat > /etc/supervisord.d/hs_query_system.ini << 'EOF'
[program:hs_query_system]
command=/usr/bin/python3 /www/wwwroot/hs_query_system/app.py
directory=/www/wwwroot/hs_query_system
user=www
autostart=true
autorestart=true
startsecs=5
startretries=3
stopwaitsecs=10
redirect_stderr=true
stdout_logfile=/www/wwwlogs/hs_query_system_supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=FLASK_ENV="production"
EOF
```

> 注意：`command` 中的 Python 路径请根据实际安装路径调整，可通过 `which python3` 查看。

### 6.3 启动和管理

```bash
# 重新加载配置
supervisorctl reread
supervisorctl update

# 启动服务
supervisorctl start hs_query_system

# 查看状态
supervisorctl status hs_query_system

# 重启服务
supervisorctl restart hs_query_system

# 停止服务
supervisorctl stop hs_query_system

# 查看日志
supervisorctl tail -f hs_query_system
```

---

## 7. 常见问题排查

### 7.1 端口被占用

**现象：** 启动失败，日志提示 `Address already in use`

```bash
# 查看端口占用情况
netstat -tlnp | grep 5000
# 或
ss -tlnp | grep 5000

# 杀死占用端口的进程
kill -9 <PID>

# 或者修改 app.py 中的端口号
# app.run(host='0.0.0.0', port=5001)
```

### 7.2 权限问题

**现象：** 日志提示 `Permission denied`

```bash
# 检查文件所有者
ls -la /www/wwwroot/hs_query_system/

# 重新设置权限
chown -R www:www /www/wwwroot/hs_query_system/
chmod -R 755 /www/wwwroot/hs_query_system/
chmod -R 775 /www/wwwroot/hs_query_system/data/
```

### 7.3 依赖安装失败

**现象：** `pip install` 报错

```bash
# 升级 pip
pip3 install --upgrade pip

# 使用国内镜像源安装
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果某个包安装失败，尝试单独安装并查看详细错误
pip3 install <package_name> -v

# 常见问题：缺少编译依赖
# CentOS
yum install python3-devel gcc -y

# Ubuntu / Debian
apt install python3-dev gcc build-essential -y
```

### 7.4 Nginx 502 Bad Gateway

**现象：** 访问网站返回 502 错误

```bash
# 1. 检查 Flask 应用是否在运行
supervisorctl status hs_query_system
# 或
ps aux | grep app.py

# 2. 检查端口是否正常监听
netstat -tlnp | grep 5000

# 3. 检查 Nginx 反向代理配置
nginx -t

# 4. 查看 Flask 应用日志
tail -f /www/wwwlogs/hs_query_system_supervisor.log
```

### 7.5 静态文件 404

**现象：** 页面样式丢失，静态文件返回 404

```bash
# 检查静态文件目录是否存在
ls -la /www/wwwroot/hs_query_system/static/

# 检查 Nginx 配置中的 alias 路径是否正确
# 确保路径末尾有斜杠
```

---

## 8. 性能优化建议

### 8.1 启用 Gunicorn（生产环境推荐）

将 Flask 内置开发服务器替换为 Gunicorn，显著提升并发处理能力：

```bash
pip3 install gunicorn
```

修改 Supervisor 配置中的 `command`：

```ini
command=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 app:app
```

参数说明：
- `-w 4`：4个工作进程（建议设置为 CPU核心数 x 2 + 1）
- `-b 127.0.0.1:5000`：绑定地址和端口
- `--timeout 120`：请求超时时间（秒），外部API查询可能较慢
- `app:app`：模块名:Flask实例名

### 8.2 SQLite 优化

系统已启用 WAL 模式，如需进一步优化：

```bash
# 进入项目目录
cd /www/wwwroot/hs_query_system

# 使用 Python 执行优化
python3 -c "
import sqlite3
conn = sqlite3.connect('data/hs_system.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.execute('PRAGMA cache_size=-64000')  # 64MB 缓存
conn.execute('PRAGMA temp_store=MEMORY')
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.close()
print('SQLite 优化完成')
"
```

### 8.3 Nginx 开启 Gzip 压缩

在 Nginx 配置的 `http` 块中添加（宝塔面板通常已默认开启）：

```nginx
gzip on;
gzip_min_length 1k;
gzip_comp_level 4;
gzip_types text/plain text/css application/json application/javascript text/xml;
gzip_vary on;
```

### 8.4 定时任务

设置宝塔面板 **计划任务**，定期维护：

| 任务类型 | 执行周期 | 脚本内容 |
|----------|----------|----------|
| Shell脚本 | 每天凌晨3点 | `cd /www/wwwroot/hs_query_system && python3 -c "import sqlite3; conn=sqlite3.connect('data/hs_system.db'); conn.execute('VACUUM'); conn.close()"` |
| Shell脚本 | 每周日凌晨2点 | `cd /www/wwwroot/hs_query_system && tar -czf /backup/hs_system_$(date +%Y%m%d).tar.gz data/hs_system.db` |

### 8.5 日志轮转

创建日志轮转配置，防止日志文件过大：

```bash
cat > /etc/logrotate.d/hs_query_system << 'EOF'
/www/wwwlogs/hs_query_system*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www www
    postrotate
        supervisorctl restart hs_query_system > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

## 附录：部署检查清单

- [ ] Python 3.8+ 已安装
- [ ] 宝塔面板 Python 项目管理器已安装
- [ ] Nginx 已安装并运行
- [ ] 项目代码已上传至 `/www/wwwroot/hs_query_system/`
- [ ] 文件权限已正确设置（www:www）
- [ ] Python 依赖已安装（`pip install -r requirements.txt`）
- [ ] 数据库已初始化（`python3 init_data.py`）
- [ ] Flask 应用可正常启动
- [ ] Nginx 反向代理已配置
- [ ] SSL 证书已申请并启用
- [ ] Supervisor 进程守护已配置
- [ ] 防火墙已放行 80/443 端口
- [ ] 域名 DNS 已正确解析
- [ ] 网站可通过域名正常访问

---

<p align="center">
  <strong>快滴收 · HS智能查询系统</strong>
  <br>
  <em>部署完成后，请访问您的域名验证系统是否正常运行</em>
</p>
