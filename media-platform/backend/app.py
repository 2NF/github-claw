"""Flask backend for the multimedia processing platform."""
import os
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

import processors

BASE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE, "..", "frontend", "dist")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY, kind TEXT, action TEXT, original_name TEXT,
  target_format TEXT, params TEXT, status TEXT, error TEXT,
  input_path TEXT, output_path TEXT, input_size INTEGER, output_size INTEGER,
  created_at TEXT, finished_at TEXT
);
"""


def create_app(data_dir=None, max_workers=2):
    app = Flask(__name__)
    data_dir = data_dir or os.environ.get("MEDIA_DATA_DIR") or os.path.join(BASE, "data")
    up, out = os.path.join(data_dir, "uploads"), os.path.join(data_dir, "outputs")
    os.makedirs(up, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    db_path = os.path.join(data_dir, "media.db")
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
    pool = ThreadPoolExecutor(max_workers=max_workers)
    app.config["POOL"] = pool

    def connect():
        c = sqlite3.connect(db_path, timeout=30)
        c.row_factory = sqlite3.Row
        return c

    with connect() as c:
        c.executescript(SCHEMA)

    def db():
        if "db" not in g:
            g.db = connect()
        return g.db

    @app.teardown_appcontext
    def close(_):
        d = g.pop("db", None)
        if d:
            d.close()

    def public(row):
        d = dict(row)
        for k in ("input_path", "output_path"):
            d.pop(k, None)
        d["ratio"] = round(1 - d["output_size"] / d["input_size"], 4) if d["output_size"] and d["input_size"] else None
        return d

    def run_task(tid):
        c = connect()
        try:
            t = c.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
            c.execute("UPDATE tasks SET status='processing' WHERE id=?", (tid,))
            c.commit()
            import json
            params = json.loads(t["params"])
            params["action"] = t["action"]
            try:
                processors.process(t["kind"], t["input_path"], t["output_path"], t["target_format"], params)
                c.execute("UPDATE tasks SET status='done', output_size=?, finished_at=? WHERE id=?",
                          (os.path.getsize(t["output_path"]), datetime.now(timezone.utc).isoformat(), tid))
            except Exception as e:
                c.execute("UPDATE tasks SET status='failed', error=?, finished_at=? WHERE id=?",
                          (str(e), datetime.now(timezone.utc).isoformat(), tid))
            c.commit()
        finally:
            c.close()

    @app.get("/api/formats")
    def formats():
        return jsonify({"output": processors.OUTPUT_FORMATS, "ffmpeg": bool(processors.ffmpeg_path())})

    @app.post("/api/tasks")
    def create_task():
        import json
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify(error="缺少文件"), 400
        kind = processors.detect_kind(f.filename)
        form_kind = request.form.get("kind")
        if not kind:
            return jsonify(error="不支持的文件类型"), 400
        if form_kind and form_kind != kind:
            return jsonify(error=f"文件类型与所选类别({form_kind})不符"), 400
        action = request.form.get("action", "compress")
        if action not in ("compress", "convert"):
            return jsonify(error="action 必须是 compress 或 convert"), 400
        src_ext = os.path.splitext(f.filename)[1].lstrip(".").lower()
        fmt = (request.form.get("target_format") or "").lower()
        if not fmt:
            fmt = src_ext
        if fmt == "jpeg":
            fmt = "jpg"
        if fmt not in processors.OUTPUT_FORMATS[kind]:
            if action == "compress" and not request.form.get("target_format"):
                fmt = {"image": "jpg", "audio": "mp3", "video": "mp4"}[kind]
            else:
                return jsonify(error=f"不支持的目标格式: {fmt}"), 400
        params = {k: request.form[k] for k in ("quality", "max_width", "bitrate", "sample_rate", "crf", "height")
                  if request.form.get(k)}
        tid = uuid.uuid4().hex
        name = secure_filename(f.filename) or f"file.{src_ext}"
        ip = os.path.join(up, f"{tid}.{src_ext}")
        op = os.path.join(out, f"{tid}.{fmt}")
        f.save(ip)
        db().execute(
            "INSERT INTO tasks (id,kind,action,original_name,target_format,params,status,input_path,output_path,"
            "input_size,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (tid, kind, action, f.filename, fmt, json.dumps(params), "pending", ip, op, os.path.getsize(ip),
             datetime.now(timezone.utc).isoformat()))
        db().commit()
        pool.submit(run_task, tid)
        row = db().execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        return jsonify(public(row)), 201

    @app.get("/api/tasks")
    def list_tasks():
        sql, args = "SELECT * FROM tasks", []
        if request.args.get("kind"):
            sql += " WHERE kind=?"
            args.append(request.args["kind"])
        rows = db().execute(sql + " ORDER BY created_at DESC LIMIT 200", args).fetchall()
        return jsonify([public(r) for r in rows])

    @app.get("/api/tasks/<tid>")
    def get_task(tid):
        r = db().execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        return (jsonify(public(r)), 200) if r else (jsonify(error="任务不存在"), 404)

    @app.get("/api/tasks/<tid>/download")
    def download(tid):
        r = db().execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        if not r:
            return jsonify(error="任务不存在"), 404
        if r["status"] != "done":
            return jsonify(error="任务未完成"), 409
        base = os.path.splitext(r["original_name"])[0]
        return send_file(r["output_path"], as_attachment=request.args.get("inline") != "1",
                         download_name=f"{base}_{r['action']}.{r['target_format']}")

    @app.delete("/api/tasks/<tid>")
    def delete(tid):
        r = db().execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        if not r:
            return jsonify(error="任务不存在"), 404
        for p in (r["input_path"], r["output_path"]):
            if p and os.path.exists(p):
                os.remove(p)
        db().execute("DELETE FROM tasks WHERE id=?", (tid,))
        db().commit()
        return jsonify(ok=True)

    @app.get("/api/stats")
    def stats():
        rows = db().execute(
            "SELECT kind, COUNT(*) n, SUM(status='done') done, SUM(status='failed') failed, "
            "SUM(CASE WHEN status='done' THEN input_size ELSE 0 END) in_size, "
            "SUM(CASE WHEN status='done' THEN output_size ELSE 0 END) out_size FROM tasks GROUP BY kind").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def spa(path):
        if path.startswith("api/"):
            return jsonify(error="not found"), 404
        if not os.path.isdir(DIST):
            return "前端未构建，请在 frontend 目录运行 npm run build", 404
        full = os.path.join(DIST, path)
        if path and os.path.isfile(full):
            return send_from_directory(DIST, path)
        # multi-page: /image -> image.html, otherwise index.html
        page = path.strip("/") + ".html"
        if path and os.path.isfile(os.path.join(DIST, page)):
            return send_from_directory(DIST, page)
        return send_from_directory(DIST, "index.html")

    return app


if __name__ == "__main__":
    create_app().run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)))
