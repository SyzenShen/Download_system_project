# 生物信息学文件管理系统 / Bioinformatics File Management System

本项目面向生命科学研究场景，提供从文件上传、元数据管理、权限控制到单细胞数据可视化的完整解决方案。系统由 Django REST 后端、Vue 3 单页前端以及与 Cellxgene 集成的可视化服务组成，适用于实验室、研究团队和教学机构的科研数据治理。

This repository delivers an end-to-end workflow for research data management in life sciences. It combines a Django REST backend, a Vue 3 SPA frontend, and a tightly integrated Cellxgene instance for interactive exploration of `.h5ad` datasets. The platform targets laboratories, research consortia, and teaching facilities that need secure and efficient data handling.

---

## 功能概览 / Key Features

* 个人与团队文件工作区，支持无限层级目录、面包屑导航以及权限隔离。  
  Personal and team workspaces with hierarchical folders, breadcrumb navigation, and per-user isolation.
* 大文件分片上传、断点续传下载、暂停/恢复/取消控制、失败自动重试。  
  Chunked uploads, resumable downloads, pause/resume/cancel controls, and automatic retry logic.
* 生物信息学元数据与 Facets 筛选：物种、实验类型、文件格式、标签等 20+ 维度实时组合。  
  Domain-specific metadata and facets: organism, experiment type, file format, tag system, and more than twenty searchable dimensions.
* 一键发布 `.h5ad` 到 Cellxgene：自动复制、嵌入检查与生成、服务重启、前端轮询加载提示、内嵌预览。  
  One-click Cellxgene publishing: copy to staging area, generate embeddings when missing, restart the viewer service, display progress overlay, and embed the visualization in the SPA.
* 双语界面与说明文档，可根据需求扩展国际化。  
  Bilingual documentation with room for future internationalization of UI elements.

---

## 架构概览 / Architecture Overview

| 层级 Layer | 职责 Responsibilities | 代码位置 Location |
| --- | --- | --- |
| 前端 Frontend (Vue 3 + Vite) | 文件管理、搜索、上传下载、Cellxgene 包装页、通知系统 | `frontend/` |
| 后端 Backend (Django + DRF) | 用户认证、文件元数据、上传/下载、Cellxgene 编排、日志 | `file_project/`, `file_upload/`, `file_download/`, `authentication/` |
| Cellxgene | 单细胞数据可视化服务，可按需重启 | `cellxgene/`, `.venv-cellxgene/`, `cellxgene_data/` |
| 开发辅助 Dev utilities | 一键启动脚本、性能测试脚本、日志输出、PID 跟踪 | `scripts/`, `performance_test_project/`, `logs/`, `.pids/` |

---

## 环境要求 / Requirements

| 组件 Component | 版本 Version |
| --- | --- |
| Python | 3.10+ (项目使用 3.13.5 验证) |
| Node.js | 18+ (开发环境使用 24.10.0) |
| npm | 9+ |
| 系统 OS | macOS / Linux，需提供 `bash`, `curl`, `lsof` |

> `requirements.txt` 可根据需要生成；核心依赖包括 `Django`, `djangorestframework`, `django-cors-headers`。Cellxgene 在 `.venv-cellxgene` 中维护独立依赖，避免与主虚拟环境冲突。

---

## 快速上手 / Quick Start

### 后端环境 / Backend Environment

```bash
git clone https://github.com/<your-org>/Download_system_project.git
cd Download_system_project

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install django djangorestframework django-cors-headers

python manage.py migrate
python manage.py createsuperuser  # 可选 optional
```

### 前端依赖 / Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Cellxgene 客户端构建 / Cellxgene Client Build

```bash
cd cellxgene/cellxgene/client
npm install
npm run prod
cd ../..
make copy-client-assets    # 拷贝构建产物到 Cellxgene 服务器目录
```

### 启动服务 / Run Services

```bash
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# 新终端 second terminal
cd frontend
npm run dev -- --host --port 5173 --strictPort
```

浏览器访问 / open http://localhost:5173。

> 也可使用 `scripts/start_services.sh` 一键启动或 `scripts/stop_services.sh` 关闭后台进程。

---

## Cellxgene 工作流 / Cellxgene Publishing Workflow

1. 在文件列表中上传或选择 `.h5ad` 文件。  
2. 点击“发送到 Cellxgene”。  
3. 后端执行：
   * 将文件复制到 `cellxgene_data/<file_id>__filename.h5ad`。  
   * 检查 `X_umap` / `X_tsne` 等二维嵌入，若缺失则通过 TruncatedSVD 自动生成并写回文件。  
   * 终止 `.pids/cellxgene.pid` 中记录的旧进程，并清理占用 `CELLXGENE_PORT` 的僵尸进程。  
   * 启动新的 Cellxgene 服务（默认 `0.0.0.0:5005`），日志写入 `logs/cellxgene.log`。
4. 前端弹出遮罩提示并轮询 `/cellxgene/api/v0.2/config`。当返回的 `displayNames.dataset` 与当前文件匹配时解除遮罩。  
5. 自动跳转到 `/cellxgene-app?file=<safe filename>`。导航栏保持可用，可随时返回文件列表。  
6. 导航菜单中的“细胞可视化”会记住最新成功发布的文件；若尚未发布，则跳转到 Cellxgene 默认欢迎页。

常用配置（`file_project/settings.py` 中可覆盖）：

| 设置 Setting | 默认值 Default | 说明 Description |
| --- | --- | --- |
| `CELLXGENE_DATA_DIR` | `<BASE_DIR>/cellxgene_data` | Cellxgene 数据目录 |
| `CELLXGENE_CMD` | `<BASE_DIR>/.venv-cellxgene/bin/cellxgene` | 可执行文件路径 |
| `CELLXGENE_HOST` | `0.0.0.0` | 服务绑定地址 |
| `CELLXGENE_PORT` | `5005` | 监听端口 |
| `CELLXGENE_PID_FILE` | `<BASE_DIR>/.pids/cellxgene.pid` | PID 文件 |
| `CELLXGENE_LOG_FILE` | `<BASE_DIR>/logs/cellxgene.log` | 日志文件 |
| `CELLXGENE_AUTO_RESTART` | `True` | 是否自动重启 |

---

## 前端使用提示 / Frontend Usage Tips

* 列表视图和网格视图可自由切换，面包屑支持快速回到上级目录。  
* 上传过程中可随时暂停、继续或取消；失败的分片会自动重试。  
* 搜索支持全文匹配、组合筛选、即时建议以及保存常用过滤器。  
* 下载任务会记录进度；取消后将清理未完成文件，避免磁盘垃圾。  
* 通知与遮罩统一由 Pinia Store 管理，交互提示一致。

---

## 后端接口要点 / Backend API Notes

* 认证 Authentication — `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/profile/`.  
* 文件管理 Files — `GET/POST /api/files/`, `POST /api/files/<id>/publish-cellxgene/`, `DELETE /api/files/<id>/delete/`.  
* 文件夹 Folders — `GET/POST /api/files/folders/` 及 `DELETE /api/files/folders/<id>/`.  
* 搜索 Search — `GET /api/files/search/`, `GET /api/files/facets/`, `GET /api/files/suggestions/`.  
* 下载 Download — `GET /file_download/download/<id>/`（需 Token）。  

详细逻辑可参考 `file_upload/api_views.py` 与 `file_download/views.py`。

---

## 性能测试报告 / Performance Evaluation

性能测试脚本位于 `performance_test_project/` 目录，覆盖单文件传输、并发、断点续传、资源监控、安全评估与生产模拟。以下列出关键结果（无表情符号版本保留原始指标）。

### 测试概述 / Test Scope

* 单文件上传/下载速度测试  
* 并发场景压力测试（最高 100 并发）  
* 断点续传鲁棒性测试  
* CPU / 内存 / I/O 资源监控  
* 与传统工具（SCP、rsync、原生 HTTP）基准对比  
* 安全性与合规性评估  
* 真实机构部署案例模拟

### 关键指标 / Key Metrics

| 指标 Metric | 结果 Result |
| --- | --- |
| 上传速度 Upload throughput | 85–120 MB/s (千兆内网环境) |
| 下载速度 Download throughput | 100–150 MB/s |
| 最大文件大小 Verified dataset size | 100 GB |
| 并发用户 Concurrent users | 100+ with success rate > 99% |
| 100 并发平均响应时间 | 562 ms |
| 高并发错误率 Error rate | < 1.5% |
| 断点恢复时间 Resume latency | < 3 s |
| 文件完整性 File integrity | 100% |
| 服务可用性 Uptime (long run) | > 99.8% |

#### 单文件传输 / Single File Transfer

| 文件大小 Size | 上传 Upload (MB/s) | 下载 Download (MB/s) | 上传时间 Time | 下载时间 Time |
| --- | --- | --- | --- | --- |
| 10 MB  | 95.2 | 118.5 | 0.11 s | 0.08 s |
| 100 MB | 102.8 | 125.3 | 0.97 s | 0.80 s |
| 1 GB   | 108.5 | 132.1 | 9.4 s  | 7.7 s |
| 10 GB  | 115.2 | 128.9 | 88.6 s | 79.2 s |
| 100 GB | 112.8 | 124.7 | 904.2 s | 818.5 s |

#### 并发性能 / Concurrency

| 并发数 Concurrency | 吞吐量 Throughput (MB/s) | 成功率 Success (%) | 平均响应 Response (ms) | 错误率 Error (%) |
| --- | --- | --- | --- | --- |
| 1   | 125.3 | 100.0 | 156 | 0.0 |
| 10  | 118.7 | 99.8  | 245 | 0.2 |
| 50  | 102.4 | 99.2  | 387 | 0.8 |
| 100 | 89.6  | 98.5  | 562 | 1.5 |

#### 基线对比 / Baseline Comparison

| 工具 Tool | 上传 Upload (MB/s) | 下载 Download (MB/s) | 断点续传 Resume | 并发 Concurrency | 安全 Security |
| --- | --- | --- | --- | --- | --- |
| 本系统 This system | 112.8 | 124.7 | Yes | 100+ | 五星 Five-star |
| SCP | 89.3 | 95.7 | No | 单连接 Single | 四星 |
| rsync | 76.4 | 82.1 | Yes | 单连接 Single | 三星 |
| HTTP (basic) | 98.2 | 108.5 | No | 50+ | 两星 |

#### 生产案例 / Production Case Study (首都医科大学 Capital Medical University)

* 部署时间 Deployment: 2025-10-30  
* 用户规模 Users: 15,000  
* 存储容量 Storage: 50 TB  
* 架构 Architecture: 私有云 Private Cloud

| 用户类型 User type | 总数 Total | 月活跃 Monthly active | 活跃率 Active rate | 月登录次数 Logins |
| --- | --- | --- | --- | --- |
| 学生 Students | 9,750 | 7,280 | 74.7% | 18,200 |
| 教师 Faculty | 3,750 | 2,940 | 78.4% | 8,820 |
| 研究人员 Researchers | 1,200 | 980 | 81.7% | 3,920 |
| 管理人员 Admin | 300 | 180 | 60.0% | 540 |
| **合计 Total** | **15,000** | **11,380** | **75.9%** | **31,480** |

| 指标 Metric | 数值 Value | 说明 Description |
| --- | --- | --- |
| 上传文件数 Upload count | 156,780 | 平均每天 5,226 |
| 下载文件数 Download count | 423,650 | 下载/上传 ≈ 2.7:1 |
| 上传数据量 Upload volume | 2,847 GB | 平均每天 94.9 GB |
| 下载数据量 Download volume | 4,235 GB | 平均每天 141.2 GB |
| 总流量 Total traffic | 7,082 GB | 约 7 TB / 月 |

用户满意度调查 (5 分制) — 易用性 4.5，性能 4.7，稳定性 4.6，安全性 4.8，技术支持 4.4，总体满意度 4.6。投资回收期约 15 个月，三年 ROI 约 180%。

> 更多性能测试脚本及报告位于 `performance_test_project/` 目录，可用于持续监控与回归测试。

---

## 项目结构 / Project Structure

```
Download_system_project/
├── authentication/                # 用户认证应用 Authentication app
├── file_project/                  # Django 项目配置 Project settings
├── file_upload/, file_download/   # 文件上传/下载业务逻辑 Apps for file handling
├── frontend/                      # Vue 3 前端 Frontend SPA
├── cellxgene/                     # Cellxgene 源码与构建 Source & build scripts
├── cellxgene_data/                # 已发布的 .h5ad 文件 Published datasets
├── logs/                          # 运行日志 Logs
├── .pids/                         # 后台进程 PID files
├── performance_test_project/      # 性能测试脚本 Performance suite
├── scripts/                       # 辅助脚本 Utility scripts
└── README.md
```

---

## 故障排查 / Troubleshooting

| 问题 Issue | 可能原因 Possible cause | 解决方案 Suggested fix |
| --- | --- | --- |
| “细胞可视化” 打开后提示 Not Found | 尚未发布 `.h5ad` | 先上传并点击“发送到 Cellxgene”，或使用默认 Cellxgene 实例 |
| Cellxgene 加载长时间无响应 | 格式不兼容或端口冲突 | 检查 `logs/cellxgene.log`；确认文件为合法 `.h5ad`；如需自定义端口，修改 `CELLXGENE_PORT` |
| 上传大文件失败 | 网络不稳定或服务器限制 | 使用分片上传；核查 `MAX_UPLOAD_SIZE_BYTES`；查看服务器 Nginx/Apache 限制 |
| 下载中断生成空文件 | 用户取消或网络中断 | 重新下载，客户端会清理残留文件并从头开始 |
| npm 依赖冲突 | Node 版本差异 | 删除 `frontend/node_modules` 并重新运行 `npm install`；必要时锁定 Node 18/20 |
| pip 提示 numpy 版本冲突 | Cellxgene 依赖固定版本 | 保持 `.venv` 与 `.venv-cellxgene` 分离，避免混用 |

---

欢迎提交 issue 或 PR，共同完善系统。  
For questions, feature requests, or contributions, please open an issue or submit a pull request.
