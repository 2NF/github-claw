# 多媒体处理平台

图片 / 音频 / 视频的**压缩**与**格式转换**。前端 Vue 3 + Vite（多页面：首页、图片、音频、视频、任务记录），后端 Flask + SQLite + FFmpeg + Pillow。

## 运行

依赖：Python 3.9+、Node 18+、FFmpeg（需含 libx264/libvpx-vp9/libmp3lame/libvorbis）。

```bash
./run.sh          # 安装依赖、构建前端并启动，访问 http://127.0.0.1:5000
```

开发模式：`python3 backend/app.py` + `cd frontend && npm run dev`（Vite 代理 /api 到 5000 端口）。
环境变量：`PORT`、`HOST`、`MEDIA_DATA_DIR`（默认 `backend/data`，存放 SQLite 与上传/输出文件）。

## 示例数据

`python3 make_samples.py` 生成（已提交）`samples/` 下的示例 png/jpg/wav/mp4，可直接在页面上传测试。

## 测试

```bash
cd backend && python3 -m pytest -q   # 覆盖图片/音频/视频所有压缩与转换格式、错误处理、任务生命周期
```

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/tasks | multipart：`file`、`action`(compress/convert)、`target_format`，可选 `quality`(图片)、`max_width`、`bitrate`/`sample_rate`(音频)、`crf`/`height`(视频) |
| GET | /api/tasks[?kind=] | 任务列表 |
| GET | /api/tasks/<id> | 任务状态（pending/processing/done/failed） |
| GET | /api/tasks/<id>/download | 下载结果（`?inline=1` 预览） |
| DELETE | /api/tasks/<id> | 删除任务与文件 |
| GET | /api/stats, /api/formats | 统计、支持格式 |

任务在后台线程池异步处理，前端轮询状态。
