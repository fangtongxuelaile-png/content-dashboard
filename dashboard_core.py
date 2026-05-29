# -*- coding: utf-8 -*-
"""小豚当家内容看板 — 数据引擎（SQLite + CRUD）"""
from __future__ import annotations
import sqlite3
import os
import json
import datetime
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── 数据库路径 ──
_DB_DIR = Path(__file__).parent / "data"
_DB_DIR.mkdir(exist_ok=True)
DB_PATH = _DB_DIR / "content_db.sqlite"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # WAL mode disabled for cloud read-only filesystem compatibility
    # conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """首次启动时建表"""
    conn = get_conn()
    c = conn.cursor()

    # 平台表
    c.execute("""
        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '📋',
            color TEXT DEFAULT '#C9A84C',
            sort_order INTEGER DEFAULT 0
        )
    """)

    # 内容主表
    c.execute("""
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            creator_type TEXT DEFAULT 'KOC',
            creator_name TEXT DEFAULT '',
            status TEXT DEFAULT '待排期',
            plan_date TEXT,
            pub_date TEXT,
            content_type TEXT DEFAULT '视频',
            material_status TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (platform_id) REFERENCES platforms(id)
        )
    """)

    # 效果数据表
    c.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            views REAL DEFAULT 0,
            likes REAL DEFAULT 0,
            comments REAL DEFAULT 0,
            shares REAL DEFAULT 0,
            collects REAL DEFAULT 0,
            clicks REAL DEFAULT 0,
            ctr REAL DEFAULT 0,
            cpc REAL DEFAULT 0,
            cpe REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            gmv REAL DEFAULT 0,
            roi REAL DEFAULT 0,
            conversion_rate REAL DEFAULT 0,
            FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE
        )
    """)

    # 插入默认平台（如果为空）
    count = c.execute("SELECT COUNT(*) FROM platforms").fetchone()[0]
    if count == 0:
        platforms = [
            (1, "CID",       "💰", "#C9A84C", 1),
            (2, "抖音达人",   "🎵", "#FE2C55", 2),
            (3, "种草通",     "🌱", "#22C55E", 3),
            (4, "B站达人",    "📺", "#00A1D6", 4),
            (5, "B站投放",    "📡", "#00A1D6", 5),
            (6, "小红书KOC",  "🔴", "#FF2442", 6),
            (7, "视频号",     "💚", "#07C160", 7),
        ]
        c.executemany(
            "INSERT INTO platforms (id,name,icon,color,sort_order) VALUES (?,?,?,?,?)",
            platforms
        )

    conn.commit()
    conn.close()


# ── CRUD: 内容表 ──

def add_content(data: Dict[str,Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO contents
          (platform_id, title, creator_type, creator_name, status,
           plan_date, pub_date, content_type, material_status, note, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("platform_id"), data.get("title",""),
        data.get("creator_type","KOC"), data.get("creator_name",""),
        data.get("status","待排期"),
        data.get("plan_date"), data.get("pub_date"),
        data.get("content_type","视频"), data.get("material_status",""),
        data.get("note",""), now, now
    ))
    content_id = cur.lastrowid
    conn.commit()
    conn.close()
    return content_id


def update_content(cid: int, data: Dict[str,Any]):
    conn = get_conn()
    fields = []
    vals = []
    for k,v in data.items():
        if k in ("id",): continue
        fields.append(f"{k}=?")
        vals.append(v)
    vals.append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    fields.append("updated_at=?")
    vals.append(cid)
    sql = f"UPDATE contents SET {','.join(fields)} WHERE id=?"
    conn.execute(sql, vals)
    conn.commit()
    conn.close()


def delete_content(cid: int):
    conn = get_conn()
    conn.execute("DELETE FROM metrics WHERE content_id=?", (cid,))
    conn.execute("DELETE FROM contents WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def get_contents(
    platform_ids: Optional[List[int]] = None,
    statuses: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    conn = get_conn()
    sql = """
        SELECT c.*, p.name as platform_name, p.icon as platform_icon, p.color as platform_color
        FROM contents c JOIN platforms p ON c.platform_id=p.id
        WHERE 1=1
    """
    params: list = []

    if platform_ids:
        placeholders = ",".join("?" * len(platform_ids))
        sql += f" AND c.platform_id IN ({placeholders})"
        params.extend(platform_ids)

    if statuses:
        placeholders = ",".join("?" * len(statuses))
        sql += f" AND c.status IN ({placeholders})"
        params.extend(statuses)

    if date_from:
        sql += " AND (c.plan_date >= ? OR c.pub_date >= ?)"
        params.extend([date_from, date_from])

    if date_to:
        sql += " AND (c.plan_date <= ? OR c.pub_date <= ?)"
        params.extend([date_to, date_to])

    if search:
        sql += " AND (c.title LIKE ? OR c.creator_name LIKE ? OR c.note LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])

    sql += " ORDER BY c.updated_at DESC"

    if limit:
        sql += f" LIMIT {limit}"

    rows = conn.execute(sql, params).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_content_by_id(cid: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute(
        "SELECT c.*, p.name as platform_name, p.icon as platform_icon "
        "FROM contents c JOIN platforms p ON c.platform_id=p.id WHERE c.id=?", (cid,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── CRUD: 效果数据 ──

def add_metrics(content_id: int, data: Dict[str,Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO metrics
          (content_id, date, views, likes, comments, shares, collects,
           clicks, ctr, cpc, cpe, cost, gmv, roi, conversion_rate)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        content_id,
        data.get("date",""),
        data.get("views",0), data.get("likes",0), data.get("comments",0),
        data.get("shares",0), data.get("collects",0), data.get("clicks",0),
        data.get("ctr",0), data.get("cpc",0), data.get("cpe",0),
        data.get("cost",0), data.get("gmv",0), data.get("roi",0),
        data.get("conversion_rate",0)
    ))
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return mid


def get_metrics_by_content(content_id: int) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM metrics WHERE content_id=? ORDER BY date DESC",
        (content_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 聚合查询（KPI）──

def get_kpi(filters: Optional[Dict]=None) -> Dict[str,Any]:
    """返回顶部4个KPI指标"""
    conn = get_conn()
    base_sql = "SELECT COUNT(*) as cnt FROM contents c WHERE 1=1"
    params = []

    if filters and filters.get("platform_ids"):
        ph = ",".join("?"*len(filters["platform_ids"]))
        base_sql += f" AND c.platform_id IN ({ph})"
        params.extend(filters["platform_ids"])

    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    # 待排期数
    pending = conn.execute(base_sql + " AND status='待排期'", params).fetchone()[0]

    # 本周已发布
    published = conn.execute(base_sql + " AND status='已发布' AND pub_date>=? AND pub_date<=?",
                             params + [week_ago, today]).fetchone()[0]

    # 异常预警
    alert = conn.execute(base_sql + " AND status='异常'", params).fetchone()[0]

    # 平均CPE
    cpe_row = conn.execute("""
        SELECT AVG(m.cpe) as avg_cpe
        FROM metrics m JOIN contents c ON m.content_id=c.id
        WHERE 1=1 AND m.cpe > 0
    """).fetchone()
    avg_cpe = round(cpe_row[0], 2) if cpe_row and cpe_row[0] else 0.0

    # 总内容数
    total = conn.execute(base_sql.replace("COUNT(*) as cnt","COUNT(*) as cnt"), params).fetchone()[0]

    conn.close()
    return {
        "pending": pending,
        "published_this_week": published,
        "alerts": alert,
        "avg_cpe": avg_cpe,
        "total": total,
    }


def get_platform_summary() -> List[Dict]:
    """各平台汇总统计"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.id, p.name, p.icon, p.color,
               COUNT(c.id) as total_count,
               SUM(CASE WHEN c.status='已发布' THEN 1 ELSE 0 END) as published_count,
               SUM(CASE WHEN c.status IN ('异常','待审核') THEN 1 ELSE 0 END) as pending_count,
               COALESCE(SUM(m.views),0) as total_views,
               COALESCE(SUM(m.likes),0) as total_likes,
               COALESCE(SUM(m.cost),0) as total_cost,
               ROUND(AVG(m.cpe),2) as avg_cpe
        FROM platforms p
        LEFT JOIN contents c ON c.platform_id=p.id
        LEFT JOIN metrics m ON m.content_id=c.id
        GROUP BY p.id
        ORDER BY p.sort_order
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_timeline_data(platform_ids=None, date_from=None, date_to=None):
    """甘特图/时间线数据"""
    conn = get_conn()
    sql = """
        SELECT c.id, c.title, c.plan_date, c.pub_date, c.status,
               p.name as platform_name, p.color as platform_color, p.icon
        FROM contents c JOIN platforms p ON c.platform_id=p.id
        WHERE c.plan_date IS NOT NULL
    """
    params = []

    if platform_ids:
        ph = ",".join("?"*len(platform_ids))
        sql += f" AND c.platform_id IN ({ph})"
        params.extend(platform_ids)

    if date_from:
        sql += " AND c.plan_date >= ?"
        params.append(date_from)

    if date_to:
        sql += " AND c.plan_date <= ?"
        params.append(date_to)

    sql += " ORDER BY c.plan_date ASC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_performance_trend(days=30):
    """效果趋势数据（按日聚合）"""
    conn = get_conn()
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    rows = conn.execute("""
        SELECT m.date,
               SUM(m.views) as views,
               SUM(m.likes) as likes,
               SUM(m.comments) as comments,
               SUM(m.shares) as shares,
               SUM(m.cost) as cost,
               AVG(m.cpe) as cpe,
               AVG(m.ctr) as ctr
        FROM metrics m
        WHERE m.date >= ?
        GROUP BY m.date ORDER BY m.date
    """, (since,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Mock 数据填充（演示用）──

def seed_demo_data():
    """填充示例数据用于展示效果"""
    conn = get_conn()
    existing = conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0]
    if existing > 10:
        conn.close()
        return False

    demo_contents = [
        # CID
        {"platform_id":1,"title":"H43 鲸瞳摄像头·京东种草图文","creator_type":"KOL","creator_name":"科技测评老王","status":"已发布","plan_date":"2026-05-20","pub_date":"2026-05-22","content_type":"图文","note":"京东好价榜TOP3"},
        {"platform_id":1,"title":"X10 室内机·天猫聚划算专场","creator_type":"自营","creator_name":"品牌官方","status":"素材制作中","plan_date":"2026-06-01","pub_date":None,"content_type":"视频","note":"需要3D渲染素材"},
        {"platform_id":1,"title":"H41 全景版·618预售预热","creator_type":"KOC","creator_name":"数码小趴菜","status":"待审核","plan_date":"2026-05-28","pub_date":None,"content_type":"短视频","note":""},

        # 抖音达人
        {"platform_id":2,"title":"@李佳琦推荐：4G摄像头实测","creator_type":"KOL","creator_name":"李佳琦","status":"已发布","plan_date":"2026-05-15","pub_date":"2026-05-18","content_type":"直播","note":"GMV 12万+"},
        {"platform_id":2,"title":"@疯狂小杨哥·安防搞笑植入","creator_type":"KOL","creator_name":"疯狂小杨哥","status":"待审核","plan_date":"2026-05-30","pub_date":None,"content_type":"视频","note":"剧本已确认"},
        {"platform_id":2,"title":"@数码博主阿杰·H43开箱","creator_type":"KOC","creator_name":"数码博主阿杰","status":"素材制作中","plan_date":"2026-06-03","pub_date":None,"content_type":"短视频","note":"样品已寄出"},
        {"platform_id":2,"title":"@宝妈生活馆·儿童监控场景","creator_type":"KOC","creator_name":"宝妈生活馆","status":"待排期","plan_date":"2026-06-08","pub_date":None,"content_type":"视频","note":""},

        # 种草通
        {"platform_id":3,"title":"小红书种草通·H43合集投放","creator_type":"KOC","creator_name":"多账号矩阵","status":"已发布","plan_date":"2026-05-18","pub_date":"2026-05-20","content_type":"图文","note":"5篇图文，总互动8k+"},
        {"platform_id":3,"title":"种草通·X10室内机评测文","creator_type":"自营","creator_name":"品牌官方","status":"异常","plan_date":"2026-05-25","pub_date":"2026-05-26","content_type":"图文","note":"被平台限流，需换标题重发"},

        # B站达人
        {"platform_id":4,"title":"@影视飓风Tim·H43专业评测","creator_type":"KOL","creator_name":"影视飓风Tim","status":"待审核","plan_date":"2026-06-02","pub_date":None,"content_type":"视频","note":"样片已交付"},
        {"platform_id":4,"title":"@老师好我叫何同学·AI安防科普","creator_type":"KOL","creator_name":"何同学","status":"待排期","plan_date":"2026-06-15","pub_date":None,"content_type":"视频","note":"沟通中，档期未定"},

        # B站投放
        {"platform_id":5,"title":"B站信息流·H41产品页投放","creator_type":"品牌","creator_name":"品牌投放","status":"素材制作中","plan_date":"2026-06-01","pub_date":None,"content_type":"视频","note":"信息流视频制作中"},

        # 小红书KOC
        {"platform_id":6,"title":"@居家少女小七·车位监控笔记","creator_type":"KOC","creator_name":"居家少女小七","status":"已发布","plan_date":"2026-05-22","pub_date":"2026-05-24","content_type":"图文","note":"收藏300+，评论80+"},
        {"platform_id":6,"title":"@数码极客Leo·H43 vs 萤石对比","creator_type":"KOC","creator_name":"数码极客Leo","status":"已发布","plan_date":"2026-05-19","pub_date":"2026-05-21","content_type":"图文","note":"点赞500+"},
        {"platform_id":6,"title":"@母婴达人小鹿·婴儿看护场景","creator_type":"KOC","creator_name":"母婴达人小鹿","status":"待排期","plan_date":"2026-06-05","pub_date":None,"content_type":"图文","note":""},

        # 视频号
        {"platform_id":7,"title":"视频号·H43新品发布会回放","creator_type":"自营","creator_name":"品牌官方","status":"已发布","plan_date":"2026-05-16","pub_date":"2026-05-16","content_type":"视频","note":"播放量2.1w"},
        {"platform_id":7,"title":"视频号·车主真实使用分享","creator_type":"KOC","creator_name":"问界车友会","status":"素材制作中","plan_date":"2026-06-04","pub_date":None,"content_type":"视频","note":"M7车主拍摄"},
    ]

    for dc in demo_contents:
        add_content(dc)

    # 填充部分效果数据
    metrics_demo = [
        # 已发布的条目给效果数据
        (1,  "2026-05-22", 12500, 380, 95, 42, 210, 520, 4.16, 1.2, 3.45, 1794, 28500, 15.88, 0.23),
        (4,  "2026-05-18", 280000, 15000, 8500, 12000, 35000, 45000, 16.07, 2.8, 1.85, 126000, 1200000, 9.52, 0.32),
        (7,  "2026-05-20", 8500, 420, 78, 35, 165, 310, 3.65, 0.9, 4.12, 279, 15600, 55.91, 0.19),
        (11, "2026-05-26", 3200, 180, 22, 8, 56, 98, 3.06, 0.5, 5.62, 49, 2100, 42.86, 0.15),
        (13, "2026-05-24", 6800, 340, 65, 28, 142, 260, 3.82, 0.75, 3.89, 195, 9800, 50.26, 0.21),
        (14, "2026-05-21", 9200, 480, 112, 48, 198, 365, 3.97, 0.82, 3.72, 299, 13400, 44.82, 0.22),
        (17, "2026-05-16", 21000, 890, 320, 145, 680, 1280, 6.10, 1.1, 2.58, 1408, 42000, 29.83, 0.28),
    ]

    for m in metrics_demo:
        add_metrics({
            "content_id": m[0], "date": m[1],
            "views": m[2], "likes": m[3], "comments": m[4],
            "shares": m[5], "collects": m[6], "clicks": m[7],
            "ctr": m[8], "cpc": m[9], "cpe": m[10],
            "cost": m[11], "gmv": m[12], "roi": m[13],
            "conversion_rate": m[14]
        })

    conn.close()
    return True
