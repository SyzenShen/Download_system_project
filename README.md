# Download_system_project（文件上传下载与断点续传示例）

一个包含 Django 后端与 Vue 前端的文件上传/下载示例项目，支持：
- 大文件分片上传（断点续传、取消、恢复）
- 下载断点续传（Range/流式）
- 真实本地文件删除（取消下载时清理残留）
- 中文文件名兼容（浏览器保存时不乱码）
- 账号注册/登录与 Token 认证（前后端联动）

> 提示：项目示例代码以教学演示为主，适合学习与二次开发。

## 功能特性
- 上传
  - 常规表单上传、ModelForm 上传、Ajax 上传
  - 前端分片上传（Chunked Upload）+ 后端断点续传接口
  - 记录并展示原始文件名（`original_filename`）
- 下载
  - 后端 ID 路由安全下载：`/file/download/<id>/`
  - Range 断点续传与流式传输（避免大文件占用内存）
  - 设置 `Content-Disposition` 同时含 `filename*`（UTF-8）与 ASCII 回退，中文名不乱码
- 前端（Vue）
  - 基于 Pinia 管理上传/下载状态
  - 支持选择保存目录、缓存目录句柄与文件名
  - 取消下载时优先使用目录句柄直接删除本地文件，失败则回退到截断清空

## 技术栈
- 后端：Django、Django REST Framework、Token Authentication
- 前端：Vue 3、Vite、Pinia、Axios
- 浏览器特性：File System Access API（需要 Chromium 内核浏览器）

## 目录结构
```
file_upload/ # 上传相关：视图、表单、模型、DRF API、分片上传接口与模板
file_download/ # 下载相关：视图与路由（包含按ID下载的新接口）
frontend/ # 前端源码（Vite+Vue3+Pinia）
file_project/ # Django 项目配置与根路由
media/ # 媒体文件根目录（通过 settings.MEDIA_ROOT/URL 提供）
authentication/ # 简单的注册/登录/用户资料
manage.py # Django 管理入口
```
## 快速开始

### 后端（Django）
1. 创建虚拟环境并安装依赖（示例）
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install django djangorestframework
```
1. 数据库初始化与启动

   ```bash
   python manage.py migrate
```

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

2. 创建超级用户（可选）

   ```bash
   python manage.py createsuperuser
   ```

3. 访问：

   - 文件列表页（后端模板）：`http://localhost:8000/file/`
   - 按ID下载（示例）：`http://localhost:8000/file/download/<id>/`

### 前端（Vue）

1. 安装依赖

   ```bash
   cd frontend && npm install
   ```

2. 启动开发服务器

   ```bash
   npm run dev
   ```

3. 默认端口通常为 `http://localhost:5173/`（根据你的 Vite 配置为准）

> 前端与后端联动：登录后，前端将 `Token` 存储到 `localStorage` 并用于调用 `/api/files/...` 接口。

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

## 接口概览（部分）

- 列表：`GET /api/files/`（Token）
- 上传（直传）：`POST /api/files/upload/`（Token）
- 下载（断点续传）：`GET /api/files/<id>/download/`（支持 `Range`，Token）
- 删除：`POST /api/files/<id>/delete/`（Token）
- 分片上传：
  - 初始化：`POST /api/files/chunked/init/`
  - 写分片：`PUT /api/files/chunked/<session_id>/chunk`（携带 `Content-Range`）
  - 完成：`POST /api/files/chunked/<session_id>/complete/`
  - 取消：`POST /api/files/chunked/<session_id>/cancel/`

> 认证：参考 `authentication/urls.py`，包含注册、登录、登出、用户资料等。

## 中文文件名与乱码问题

- 列表页（后端模板）已改为显示 `original_filename`，避免显示编码后的存储路径。
- 下载时视图设置 `Content-Disposition`：
  - `filename*` 使用 UTF-8 百分号编码（RFC 5987）
  - 同时提供 ASCII 回退 `filename`，兼容旧浏览器
- 前端列表组件也优先显示 `original_filename`，保持一致。

## 浏览器兼容性

- 断点续传与 `File System Access API` 相关功能需要现代 Chromium 浏览器（如 Chrome）。
- 非支持浏览器会回退到 Blob 下载，无法做到无提示的目录删除与免二次授权。

## 常见问题

- 看不到文件或下载失败？
  - 确认 `media/` 可写，`settings.MEDIA_ROOT`/`MEDIA_URL` 正确配置。
  - 检查登录状态与 Token。
- 中文名仍异常？
  - 清理浏览器缓存后重试；
  - 确认使用的是按 ID 下载路由 `/file/download/<id>/`；
  - 查看响应头 `Content-Disposition` 是否包含 `filename*`。
- 分片上传失败？
  - 检查 `Content-Range` 格式；
  - 确认 `session.uploaded_size` 与 `total_size` 一致后再 `complete`。

## 免责声明

本项目为示例性质，不建议直接用于生产。安全策略（权限、限速、黑名单、审计等）需根据实际业务补充与完善。
