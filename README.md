# 文件管理系统 (File Management System)

一个功能完整的文件管理系统，包含 Django 后端与 Vue 3 前端，支持：
- 🗂️ **层级文件夹管理** - 创建、删除、导航文件夹结构
- 📤 **大文件分片上传** - 断点续传、暂停、恢复、取消上传
- 📥 **断点续传下载** - Range请求、暂停、恢复、取消下载
- 🔐 **用户认证系统** - 注册、登录、个人资料管理
- 🎨 **现代化界面** - 响应式设计、列表/网格视图切换
- 🌐 **中文文件名支持** - 完美处理中文文件名，无乱码
- 🚀 **高性能** - 流式传输、内存优化、大文件支持(100GB+)

> 💡 这是一个生产级别的文件管理系统，具备完整的功能和良好的用户体验。

## ✨ 核心功能

### 📁 文件夹管理
- **层级结构** - 支持无限层级的文件夹嵌套
- **面包屑导航** - 清晰的路径导航和快速跳转
- **文件夹操作** - 创建、重命名、删除、移动文件夹
- **权限控制** - 用户只能访问自己的文件夹

### 📤 文件上传
- **多种上传方式** - 拖拽上传、点击选择、批量上传
- **分片上传** - 大文件自动分片，支持断点续传
- **实时进度** - 上传进度条、速度显示、剩余时间
- **上传控制** - 暂停、恢复、取消上传操作
- **文件验证** - 文件大小、类型验证

### 📥 文件下载
- **断点续传** - 支持Range请求，可暂停恢复下载
- **批量下载** - 文件夹打包下载
- **下载管理** - 下载队列、进度监控
- **本地文件管理** - 智能清理未完成的下载文件

### 🔐 用户系统
- **邮箱注册** - 使用邮箱作为用户名
- **安全认证** - Token认证、密码强度验证
- **个人资料** - 用户信息管理、头像上传
- **权限隔离** - 用户数据完全隔离

## 🛠️ 技术栈

### 后端技术
- **Django 4.x** - Web框架
- **Django REST Framework** - API框架
- **Token Authentication** - 认证系统
- **SQLite** - 数据库（可配置其他数据库）
- **CORS Headers** - 跨域支持

### 前端技术
- **Vue 3** - 前端框架
- **Vite** - 构建工具
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP客户端
- **响应式CSS** - 现代化UI设计

### 浏览器特性
- **File System Access API** - 高级文件操作（Chrome/Edge）
- **Fetch API** - 网络请求
- **Web Streams** - 流式处理
- **Service Worker** - 后台处理（可选）

## 📁 项目结构

```
📦 Download_system_project/
├── 🗂️ authentication/          # 用户认证模块
│   ├── models.py              # 自定义用户模型
│   ├── views.py               # 认证视图
│   ├── serializers.py         # API序列化器
│   └── validators.py          # 密码验证器
├── 🗂️ file_upload/            # 文件上传模块
│   ├── models.py              # 文件和文件夹模型
│   ├── api_views.py           # REST API视图
│   ├── chunked_api_views.py   # 分片上传API
│   └── serializers.py         # 序列化器
├── 🗂️ file_download/          # 文件下载模块
│   ├── views.py               # 下载视图
│   └── urls.py                # 下载路由
├── 🗂️ frontend/               # Vue前端应用
│   ├── src/
│   │   ├── components/        # Vue组件
│   │   │   ├── FileDisplay.vue      # 文件显示组件
│   │   │   ├── FolderTree.vue       # 文件夹树组件
│   │   │   ├── UploadDialog.vue     # 上传对话框
│   │   │   └── NewFolderDialog.vue  # 新建文件夹对话框
│   │   ├── views/             # 页面视图
│   │   │   ├── FileList.vue         # 文件列表页
│   │   │   ├── Login.vue            # 登录页
│   │   │   ├── Register.vue         # 注册页
│   │   │   └── Profile.vue          # 个人资料页
│   │   ├── stores/            # Pinia状态管理
│   │   │   ├── auth.js              # 认证状态
│   │   │   └── files.js             # 文件管理状态
│   │   └── router/            # 路由配置
│   ├── package.json           # 前端依赖
│   └── vite.config.js         # Vite配置
├── 🗂️ file_project/           # Django项目配置
│   ├── settings.py            # 项目设置
│   ├── urls.py                # 主路由
│   └── wsgi.py                # WSGI配置
├── 🗂️ media/                  # 用户上传文件存储
└── manage.py                  # Django管理脚本
```
## 🚀 快速开始

### 环境要求
- **Python 3.8+**
- **Node.js 16+**
- **现代浏览器** (Chrome/Edge/Firefox)

### 1️⃣ 克隆项目
```bash
git clone <repository-url>
cd Download_system_project
```

### 2️⃣ 后端设置 (Django)

#### 创建虚拟环境
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

#### 安装依赖
```bash
pip install django djangorestframework django-cors-headers
```

#### 数据库初始化
```bash
python manage.py migrate
```

#### 创建超级用户（可选）
```bash
python manage.py createsuperuser
```

#### 启动后端服务
```bash
python manage.py runserver
```
🌐 后端服务运行在: `http://localhost:8000`

### 3️⃣ 前端设置 (Vue)

#### 安装依赖
```bash
cd frontend
npm install
```

#### 启动前端服务
```bash
npm run dev
```
🌐 前端应用运行在: `http://localhost:5173`

### 4️⃣ 开始使用

1. **注册账号**: 访问 `http://localhost:5173/register`
2. **登录系统**: 使用注册的邮箱和密码登录
3. **管理文件**: 上传、下载、组织您的文件
4. **创建文件夹**: 建立层级文件夹结构

> 💡 **提示**: 首次使用建议先注册一个账号，然后体验完整的文件管理功能。

## 关键模块说明

### 上传（后端）

- 视图与表单：
  - `file_upload/views.py`：常规上传、ModelForm 上传、Ajax 上传
  - `file_upload/forms.py`：校验与 `original_filename` 写入
- 分片上传（Chunked）：
  - `file_upload/chunked_api_views.py`：
    - `POST /api/files/chunked/init/` 初始化会话（返回 `session_id`）
    - `PUT/POST /api/files/chunked/<session_id>/chunk` 写入分片（通过 `Content-Range`）
    - `POST /api/files/chunked/<session_id>/complete/` 归档存储为 `File` 记录
    - `POST /api/files/chunked/<session_id>/cancel/` 取消并清理临时文件

### 下载（后端）

- 按ID安全下载：
  - 路由：`file_download/urls.py` -> `path('download/<int:file_id>/', ...)`
  - 视图：`file_download/views.py` -> `file_download_by_id`
  - 中文文件名兼容：
    - `Content-Disposition` 同时附带 `filename*`（UTF-8 percent-encoding）与 ASCII 回退
    - 现代浏览器优先支持 `filename*`，中文名显示正确
- 旧版路径下载（兼容示例，基于文件路径，不建议生产使用）：
  - `re_path(r'^download/(?P<file_path>.*)/$', ...)`

### 前端断点续传与下载

- 入口：`frontend/src/stores/files.js`
- 主要能力：
  - 上传：记录上传进度、暂停、恢复、取消
  - 下载：支持 Range、暂停、恢复、取消
  - 目录句柄缓存：`downloadDirHandles` 与 `downloadFilenames`
    - 优先使用已授权的目录句柄删除取消下载时的本地文件，避免重复弹窗
    - 删除失败时回退到将文件截断为 0 字节，保证没有残留内容

## 📡 API 接口文档

### 🔐 认证接口
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| `POST` | `/api/auth/register/` | 用户注册 | ❌ |
| `POST` | `/api/auth/login/` | 用户登录 | ❌ |
| `POST` | `/api/auth/logout/` | 用户登出 | ✅ |
| `GET` | `/api/auth/profile/` | 获取用户信息 | ✅ |
| `PUT` | `/api/auth/profile/update/` | 更新用户信息 | ✅ |

### 📁 文件夹接口
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| `GET` | `/api/files/folders/` | 获取文件夹列表 | ✅ |
| `POST` | `/api/files/folders/` | 创建文件夹 | ✅ |
| `GET` | `/api/files/folders/all/` | 获取所有文件夹 | ✅ |
| `GET` | `/api/files/folders/<id>/` | 获取文件夹详情 | ✅ |
| `DELETE` | `/api/files/folders/<id>/` | 删除文件夹 | ✅ |
| `GET` | `/api/files/folders/<id>/breadcrumb/` | 获取面包屑导航 | ✅ |

### 📄 文件接口
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| `GET` | `/api/files/` | 获取文件列表 | ✅ |
| `POST` | `/api/files/upload/` | 文件上传 | ✅ |
| `GET` | `/api/files/<id>/download/` | 文件下载 (支持Range) | ✅ |
| `DELETE` | `/api/files/<id>/delete/` | 删除文件 | ✅ |
| `GET` | `/api/files/stats/` | 获取用户统计信息 | ✅ |

### 🔄 分片上传接口
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| `POST` | `/api/files/chunked/init/` | 初始化分片上传 | ✅ |
| `PUT` | `/api/files/chunked/<session_id>/chunk/` | 上传分片 | ✅ |
| `POST` | `/api/files/chunked/<session_id>/complete/` | 完成上传 | ✅ |
| `POST` | `/api/files/chunked/<session_id>/cancel/` | 取消上传 | ✅ |

### 📋 请求示例

#### 用户注册
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
  }'
```

#### 文件上传
```bash
curl -X POST http://localhost:8000/api/files/upload/ \
  -H "Authorization: Token your-token-here" \
  -F "file=@example.txt" \
  -F "upload_method=API"
```

#### 创建文件夹
```bash
curl -X POST http://localhost:8000/api/files/folders/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的文件夹",
    "parent": null
  }'
```

## 🌟 系统特性

### 🔒 安全特性
- **Token认证** - 基于Django REST Framework的Token认证
- **用户隔离** - 每个用户只能访问自己的文件
- **文件验证** - 上传文件大小和类型验证
- **路径安全** - 防止路径遍历攻击
- **CORS配置** - 安全的跨域资源共享设置

### 🚀 性能特性
- **流式传输** - 大文件下载不占用服务器内存
- **分片上传** - 大文件分片上传，提高成功率
- **断点续传** - 上传下载支持断点续传
- **并发控制** - 合理的并发上传下载控制
- **缓存优化** - 静态资源缓存优化

### 🎨 用户体验
- **响应式设计** - 适配桌面和移动设备
- **实时进度** - 上传下载进度实时显示
- **拖拽上传** - 支持拖拽文件上传
- **批量操作** - 支持批量文件操作
- **快捷键支持** - 常用操作快捷键

## 🌐 浏览器兼容性

| 浏览器 | 基础功能 | 高级功能* |
|--------|----------|-----------|
| Chrome 86+ | ✅ | ✅ |
| Edge 86+ | ✅ | ✅ |
| Firefox 80+ | ✅ | ⚠️ |
| Safari 14+ | ✅ | ❌ |

> *高级功能包括：File System Access API、目录选择、本地文件管理

## ❓ 常见问题

<details>
<summary><strong>Q: 无法上传大文件怎么办？</strong></summary>

A: 检查以下设置：
- Django设置中的 `MAX_UPLOAD_SIZE_BYTES`
- Web服务器的上传大小限制
- 网络连接稳定性
- 使用分片上传功能
</details>

<details>
<summary><strong>Q: 中文文件名显示乱码？</strong></summary>

A: 系统已完美支持中文文件名：
- 确保使用最新版本的浏览器
- 检查文件的 `original_filename` 字段
- 清除浏览器缓存后重试
</details>

<details>
<summary><strong>Q: 下载速度慢怎么办？</strong></summary>

A: 优化建议：
- 检查网络连接
- 使用断点续传功能
- 考虑服务器带宽限制
- 尝试分时段下载
</details>

<details>
<summary><strong>Q: 如何备份数据？</strong></summary>

A: 备份方案：
- 定期备份 `media/` 目录
- 导出数据库数据
- 使用批量下载功能
</details>

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. **Fork** 本项目
2. **创建** 特性分支 (`git checkout -b feature/AmazingFeature`)
3. **提交** 更改 (`git commit -m 'Add some AmazingFeature'`)
4. **推送** 到分支 (`git push origin feature/AmazingFeature`)
5. **创建** Pull Request

### 开发规范
- 遵循 PEP 8 Python代码规范
- 使用 Vue 3 Composition API
- 添加适当的注释和文档
- 编写测试用例

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目：
- [Django](https://djangoproject.com/) - Web框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Vite](https://vitejs.dev/) - 构建工具
- [Pinia](https://pinia.vuejs.org/) - 状态管理

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给它一个星标！**

[🐛 报告Bug](../../issues) · [✨ 请求功能](../../issues) · [💬 讨论](../../discussions)

</div>
