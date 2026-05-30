# -*- coding: utf-8 -*-
"""
小豚当家 · 全平台内容看板（Content Dashboard）
单页综合看板 — 进度排期 + 效果数据
视觉风格：暗金主题（与AI大赛汇报一致）
"""
from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta, datetime
from pathlib import Path

# ── 登录系统配置 ──
USERS = {
    "long520": {"password": "202310", "name": "管理员", "role": "admin"},
    "xiaotun": {"password": "xiaotun888", "name": "小豚运营", "role": "editor"},
    "guest": {"password": "guest2024", "name": "访客", "role": "viewer"},
}

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

# ── 导入自定义模块 ──
from theme import DARK_GOLD_CSS, get_plotly_template, PLATFORMS, STATUS_OPTIONS, STATUS_COLORS, CREATOR_TYPES, CONTENT_TYPES
from dashboard_core import (
    init_db, seed_demo_data,
    get_contents, add_content, update_content, delete_content,
    get_kpi, get_platform_summary, get_timeline_data, get_performance_trend,
    get_content_by_id, get_metrics_by_content,
)

# ── 初始化数据库 ──
init_db()

# ── 注入暗金CSS ──
st.markdown(DARK_GOLD_CSS, unsafe_allow_html=True)

# ── 页面配置 ──
st.set_page_config(
    page_title="小豚当家 · 全平台内容看板",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 登录拦截 ──
if st.session_state.auth_user is None:
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 10vh auto 0;
        padding: 48px 40px;
        background: linear-gradient(145deg, #111827 0%, #0A0E17 100%);
        border: 1px solid rgba(201,168,76,0.25);
        border-radius: 16px;
        box-shadow: 0 24px 64px rgba(0,0,0,0.5), 0 0 40px rgba(201,168,76,0.06);
        text-align: center;
    }
    .login-container h2 {
        color: #C9A84C;
        margin-bottom: 8px;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .login-container p.sub {
        color: #94A3B8;
        font-size: 14px;
        margin-bottom: 32px;
    }
    .login-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(201,168,76,0.3), transparent);
        margin: 24px 0;
    }
    .login-hint {
        color: #64748B;
        font-size: 12px;
        margin-top: 20px;
    }
    .login-hint code {
        background: rgba(201,168,76,0.1);
        color: #C9A84C;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    </style>
    <div class="login-container">
        <div style="font-size:42px;margin-bottom:12px;">🎯</div>
        <h2>小豚当家 · 内容看板</h2>
        <p class="sub">全平台投放内容管理与数据追踪</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        c1, c2, c3 = st.columns([1, 2.5, 1])
        with c2:
            username = st.text_input("账号", placeholder="请输入账号", key="login_user")
            password = st.text_input("密码", placeholder="请输入密码", type="password", key="login_pass")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                login_btn = st.button("🔐 登录", use_container_width=True, type="primary")
            with col_b:
                st.button("🌱 访客演示", use_container_width=True, on_click=lambda: st.session_state.update({"auth_user": "guest"}))
            if login_btn:
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.auth_user = username
                    st.rerun()
                else:
                    st.error("账号或密码错误，请重试")
            st.markdown("""
            <div class="login-hint">
                可用账号：<code>admin</code> / <code>xiaotun</code> / <code>guest</code>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ── 已登录：侧边栏用户信息 ──
user_info = USERS.get(st.session_state.auth_user, {})
with st.sidebar:
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(201,168,76,0.12), rgba(76,138,201,0.08));
        border: 1px solid rgba(201,168,76,0.2);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        text-align: center;
    ">
        <div style="font-size:28px;margin-bottom:6px;">👤</div>
        <div style="color:#C9A84C;font-weight:700;font-size:16px;">{user_info.get('name', '用户')}</div>
        <div style="color:#64748B;font-size:12px;margin-top:2px;">@{st.session_state.auth_user} · {user_info.get('role', '')}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 退出登录", use_container_width=True):
        st.session_state.auth_user = None
        st.rerun()
    st.divider()

# ============================================================
#  辅助函数
# ============================================================

def _slicer(label, options, key):
    """多选筛选器：不选=全选"""
    sk = f"slicer_{key}"
    if not options:
        st.caption(f"{label}: 暂无")
        return []
    all_opts = list(options)
    if sk in st.session_state:
        saved = st.session_state[sk]
        if isinstance(saved, list):
            valid = [v for v in saved if v in all_opts]
            if len(valid) != len(saved):
                st.session_state[sk] = valid
    sel = st.multiselect(label, options=all_opts, default=[], key=sk, placeholder="全选")
    return list(sel) if sel else all_opts


def _status_tag(status: str):
    """渲染状态胶囊标签"""
    color = STATUS_COLORS.get(status, "#94A3B8")
    return f'<span class="status-tag status-{status}">{status}</span>'


def _platform_badge(name: str, icon: str, color: str):
    """平台标签"""
    return f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:12px;padding:2px 10px;border-radius:999px;background:{color}18;color:{color};font-weight:600;">{icon} {name}</span>'


# ============================================================
#  侧边栏
# ============================================================
with st.sidebar:
    # Logo / 标题区
    st.markdown("""
    <div style="text-align:center;padding:24px 0 16px;">
      <div style="font-size:28px;margin-bottom:6px;">🎯</div>
      <div style="font-size:15px;font-weight:800;color:#C9A84C;letter-spacing:0.08em;">内容看板</div>
      <div style="font-size:11px;color:#64748B;margin-top:4px;">XIAOTUNBI DASHBOARD</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("🔍 筛选条件")

    # 平台筛选
    platform_names = [p["name"] for p in PLATFORMS]
    sel_platforms = _slicer("投放平台", platform_names, "platform")

    # 状态筛选
    sel_statuses = _slicer("内容状态", STATUS_OPTIONS, "status")

    # 日期范围
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        d_from = st.date_input("起始日期", value=date.today() - timedelta(days=30), label_visibility="collapsed")
    with col_d2:
        d_to = st.date_input("截止日期", value=date.today() + timedelta(days=14), label_visibility="collapsed")

    # 搜索关键词
    search_kw = st.text_input("🔎 搜索", placeholder="标题/达人/备注...")

    st.markdown("---")

    # 操作按钮
    if st.button("➕ 新增内容", use_container_width=True, key="btn_add"):
        st.session_state["show_add_dialog"] = True
        st.rerun()

    if st.button("📥 批量导入Excel", use_container_width=True, key="btn_import"):
        st.session_state["show_import_dialog"] = True
        st.rerun()

    if st.button("🌱 填充演示数据", use_container_width=True, key="btn_seed"):
        seed_demo_data()
        st.rerun()

    st.markdown("---")
    st.caption(f"💾 数据库: `content_db.sqlite`")


# ============================================================
#  构建筛选参数
# ============================================================
pid_map = {p["name"]: p["id"] for p in PLATFORMS}
sel_pids = [pid_map[n] for n in sel_platforms if n in pid_map] if sel_platforms else None

filters = {"platform_ids": sel_pids}

# 获取数据
all_contents = get_contents(
    platform_ids=sel_pids,
    statuses=sel_statuses,
    date_from=d_from.isoformat(),
    date_to=d_to.isoformat(),
    search=search_kw if search_kw else None
)

kpi = get_kpi(filters)
platform_summary = get_platform_summary()
timeline_data = get_timeline_data(platform_ids=sel_pids, date_from=d_from.isoformat(), date_to=d_to.isoformat())
trend_data = get_performance_trend(days=60)

# Plotly模板
tmpl = get_plotly_template()


# ============================================================
#  主内容区 — Hero Banner
# ============================================================
st.markdown(f"""
<div class="hero-banner">
  <div class="hero-title">🎯 小豚当家 · 全平台内容看板</div>
  <div class="hero-sub">
    统领 CID · 抖音达人 · 种草通 · B站 · 小红书 · 视频号 等 {len(PLATFORMS)} 个投放渠道 &nbsp;|&nbsp;
    共 <b>{kpi['total']}</b> 条内容记录 &nbsp;|&nbsp;
    最后更新：<i>{datetime.now().strftime('%m-%d %H:%M')}</i>
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
#  KPI 卡片行
# ============================================================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="⏳ 待排期", value=str(kpi['pending']), delta=f"共 {kpi['total']} 条")
with c2:
    st.metric(label="✅ 本周已发布", value=str(kpi['published_this_week']), delta_color="normal")
with c3:
    st.metric(label="⚠️ 异常预警", value=str(kpi['alerts']),
              delta_color="inverse" if kpi['alerts'] > 0 else "normal")
with c4:
    avg_cpe_str = f"¥{kpi['avg_cpe']:.2f}" if kpi['avg_cpe'] else "暂无"
    st.metric(label="💰 平均CPE", value=avg_cpe_str)


# ============================================================
#  上半区：进度排期（甘特条）
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
st.markdown("""
<div class="section-header">
  <h3>📅 进度排期</h3>
  <span class="badge">按时间轴展示发布计划 vs 实际进度</span>
</div>
""", unsafe_allow_html=True)

if timeline_data:
    df_timeline = pd.DataFrame(timeline_data)
    # 构建甘特图数据
    gantt_records = []
    for _, row in df_timeline.iterrows():
        start_val = row["plan_date"]
        end_val = row["pub_date"] or row["plan_date"]
        gantt_records.append({
            "Task": f"{row['platform_icon']} {row['title'][:20]}",
            "Start": start_val,
            "Finish": end_val,
            "Platform": row["platform_name"],
            "Status": row["status"],
            "Color": row["platform_color"],
            "ContentID": row["id"],
        })

    df_gantt = pd.DataFrame(gantt_records)

    fig_gantt = px.timeline(
        df_gantt,
        x_start="Start", x_end="Finish",
        y="Task",
        color="Platform",
        hover_data=["Status", "Task"],
        title=""
    )
    fig_gantt.update_layout(**tmpl["layout"])
    fig_gantt.update_traces(marker=dict(opacity=0.75))
    fig_gantt.update_yaxes(autorange="reversed")
    fig_gantt.update_xaxes(rangeslider_visible=False)
    fig_gantt.update_layout(height=max(300, len(df_gantt) * 32 + 80),
                             showlegend=True,
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig_gantt.update_layout(margin=dict(l=10, r=10, t=10, b=40))

    st.plotly_chart(fig_gantt, use_container_width=True)
else:
    st.info("📭 当前筛选条件下暂无排期数据，调整筛选条件或新增内容。")


# ============================================================
#  下半区：效果数据（散点图 + 折线图）
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
st.markdown("""
<div class="section-header">
  <h3>📊 效果数据分析</h3>
  <span class="badge">平台对比 × 趋势追踪</span>
</div>
""", unsafe_allow_html=True)

col_chart_left, col_chart_right = st.columns(2)

# ---- 左：平台对比散点矩阵 ----
with col_chart_left:
    if any(ps.get("total_views",0) > 0 for ps in platform_summary):
        df_ps = [ps for ps in platform_summary if ps.get("total_views",0) > 0]
        scatter_data = [{
            "platform": p["name"],
            "icon": p["icon"],
            "cost": p.get("total_cost", 0) or 0,
            "engagement": (p.get("total_likes",0) or 0) + (p.get("total_comments",0) or 0) + (p.get("total_shares",0) or 0) + (p.get("total_collects",0) or 0),
            "views": p.get("total_views", 0) or 0,
            "content_count": p.get("total_count", 0) or 0,
            "color": p.get("color", "#C9A84C"),
        } for p in df_ps]

        df_scatter = pd.DataFrame(scatter_data)

        fig_scatter = go.Figure()

        for _, row in df_scatter.iterrows():
            fig_scatter.add_trace(go.Scatter(
                x=[row["cost"]],
                y=[row["engagement"]],
                mode='markers+text',
                name=row["icon"] + " " + row["platform"],
                marker=dict(
                    size=max(20, min(50, row["content_count"] * 5)),
                    color=row["color"],
                    opacity=0.7,
                    line=dict(width=1.5, color='white')
                ),
                text=[f"{row['icon']}"],
                textposition="top center",
                textfont=dict(size=14),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "花费: ¥%{x:,.0f}<br>"
                    "互动总量: %{y:,}<br>"
                    "播放量: %{$customdata[0]:,}<br>"
                    "内容数: %{$customdata[1]}<extra></extra>"
                ),
                customdata=[[row["views"], row["content_count"]]]
            ))

        fig_scatter.update_layout(
            xaxis_title="总花费 (¥)",
            yaxis_title="互动总量 (赞+评+转+藏)",
            **tmpl["layout"]
        )
        fig_scatter.update_layout(height=400, showlegend=True)
        fig_scatter.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                               xref="paper", yref="paper",
                               line=dict(dash="dot", color="rgba(255,255,255,0.12)", width=1))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("暂无效果数据，发布内容后录入效果指标即可查看。")

# ---- 右：趋势折线图 ----
with col_chart_right:
    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        fig_trend = go.Figure()
        metrics_to_show = ["views", "likes", "comments", "cost"]

        metric_config = {
            "views": ("播放量", "#C9A84C"),
            "likes": ("点赞", "#FE2C55"),
            "comments": ("评论", "#4C8AC9"),
            "cost": ("花费(¥)", "#22C55E"),
        }

        for m in metrics_to_show:
            if m in df_trend.columns:
                label, color = metric_config[m]
                fig_trend.add_trace(go.Scatter(
                    x=df_trend["date"], y=df_trend[m],
                    mode='lines+markers', name=label,
                    line=dict(width=2, color=color),
                    marker=dict(size=5, opacity=0.7),
                ))

        fig_trend.update_layout(yaxis_type="log", **tmpl["layout"])
        fig_trend.update_layout(height=400, legend_orientation="h",
                                 yaxis_title="数值 (对数)", xaxis_title="")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("暂无趋势数据。")


# ============================================================
#  底部：内容明细表
# ============================================================
st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)
st.markdown("""
<div class="section-header">
  <h3>📋 内容明细</h3>
  <span class="badge">共 {} 条 | 可直接编辑状态</span>
</div>
""".format(len(all_contents)), unsafe_allow_html=True)

if all_contents:
    # 构建可编辑表格
    display_rows = []
    for c in all_contents:
        display_rows.append({
            "ID": c["id"],
            "平台": f"{c['platform_icon']} {c['platform_name']}",
            "标题": c["title"],
            "类型": c["creator_type"],
            "达人": c["creator_name"] or "-",
            "状态": c["status"],
            "计划日期": c["plan_date"] or "-",
            "发布日期": c["pub_date"] or "-",
            "内容形式": c["content_type"],
            "备注": c["note"] or "",
        })

    df_display = pd.DataFrame(display_rows)

    # 使用 data_editor 实现可编辑状态
    edited_df = st.data_editor(
        df_display,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small", disabled=True),
            "平台": st.column_config.TextColumn("平台", width="medium", disabled=True),
            "标题": st.column_config.TextColumn("标题", width="large", disabled=True),
            "类型": st.column_config.TextColumn("类型", width="small", disabled=True),
            "达人": st.column_config.TextColumn("达人", width="medium", disabled=True),
            "状态": st.column_config.SelectboxColumn(
                "状态",
                options=STATUS_OPTIONS,
                required=True,
                width="small"
            ),
            "计划日期": st.column_config.DateColumn("计划日期", format="YYYY-MM-DD", width="medium"),
            "发布日期": st.column_config.DateColumn("发布日期", format="YYYY-MM-DD", width="medium"),
            "内容形式": st.column_config.SelectboxColumn("内容形式", options=CONTENT_TYPES, width="small"),
            "备注": st.column_config.TextColumn("备注", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        height=min(450, max(200, len(display_rows) * 38 + 48)),
        key="content_table_editor"
    )

    # 检测变更并保存
    save_col, export_col = st.columns([1, 4])
    with save_col:
        if st.button("💾 保存修改", type="primary", use_container_width=True):
            changed = False
            for _, row in edited_df.iterrows():
                cid = int(row["ID"])
                orig = next((c for c in all_contents if c["id"] == cid), None)
                if orig and row["状态"] != orig["status"]:
                    update_content(cid, {"status": row["状态"]})
                    changed = True
                if orig and row["计划日期"] != str(orig["plan_date"] or ""):
                    new_plan = row["计划日期"].isoformat() if hasattr(row["计划日期"], 'isoformat') else str(row["计划日期"]) if row["计划日期"] != "-" else None
                    if new_plan != orig["plan_date"]:
                        update_content(cid, {"plan_date": new_plan})
                        changed = True
                if orig and row["发布日期"] != str(orig["pub_date"] or ""):
                    new_pub = row["发布日期"].isoformat() if hasattr(row["发布日期"], 'isoformat') else str(row["发布日期"]) if row["发布日期"] != "-" else None
                    if new_pub != orig["pub_date"]:
                        update_content(cid, {"pub_date": new_pub})
                        changed = True
            if changed:
                st.success("✅ 已保存修改！", icon="check")
                st.rerun()
            else:
                st.info("没有检测到变更。")

    with export_col:
        csv_bytes = df_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 导出CSV",
            data=csv_bytes,
            file_name=f"content_dashboard_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.info("📭 暂无内容记录。点击左侧「➕ 新增内容」或「🌱 填充演示数据」开始。")


# ============================================================
#  新增内容弹窗
# ============================================================
if st.session_state.get("show_add_dialog"):
    with st.dialog("➕ 新增内容记录", width=640):
        with st.form("add_content_form"):
            acol1, acol2 = st.columns(2)

            with acol1:
                plat_opts = {p["name"]: p["id"] for p in PLATFORMS}
                selected_plat = st.selectbox("投放平台*", options=list(plat_opts.keys()))
                ct_type = st.selectbox("内容形式", options=CONTENT_TYPES)
                cr_type = st.selectbox("创作者类型", options=CREATOR_TYPES)

            with acol2:
                cr_name = st.text_input("创作者/达人名称")
                plan_dt = st.date_input("计划日期")
                pub_dt = st.date_input("实际发布日期")

            title_txt = st.text_input("标题*", placeholder="例如：H43 鲸瞳摄像头·抖音达人测评视频")
            mat_status = st.selectbox("素材状态", options=["", "待制作", "制作中", "已完成", "待确认"])
            status_new = st.selectbox("当前状态*", options=STATUS_OPTIONS, index=STATUS_OPTIONS.index("待排期"))
            note_txt = st.text_area("备注", height=60, placeholder="补充说明、特殊要求等...")

            submitted = st.form_submit_button("✅ 提交", type="primary", use_container_width=True)

            if submitted and title_txt.strip():
                new_id = add_content({
                    "platform_id": plat_opts[selected_plat],
                    "title": title_txt.strip(),
                    "creator_type": cr_type,
                    "creator_name": cr_name,
                    "status": status_new,
                    "plan_date": plan_dt.isoformat(),
                    "pub_date": pub_dt.isoformat(),
                    "content_type": ct_type,
                    "material_status": mat_status,
                    "note": note_txt,
                })
                st.session_state.pop("show_add_dialog", None)
                st.success(f"✅ 内容已创建！ID={new_id}")
                st.rerun()


# ============================================================
#  批量导入弹窗
# ============================================================
if st.session_state.get("show_import_dialog"):
    with st.dialog("📥 批量导入 Excel", width=680):
        st.markdown("""
        <div style="background:rgba(201,168,76,0.06);padding:14px;border-radius:8px;border:1px solid rgba(201,168,76,0.15);margin-bottom:16px;">
        <strong>导入格式要求：</strong><br>
        • 支持 .xlsx 或 .csv 文件<br>
        • 必需列：<code>平台</code>、<code>标题</code>、<code>状态</code>（其他列为可选）<br>
        • 平台值：CID / 抖音达人 / 种草通 / B站达人 / B站投放 / 小红书KOC / 视频号<br>
        • 状态值：待排期 / 素材制作中 / 待审核 / 已发布 / 已下架 / 异常
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("选择文件", type=["xlsx", "csv"], help="支持 .xlsx 和 .csv 格式")

        if uploaded_file:
            try:
                ext = uploaded_file.name.split(".")[-1].lower()
                if ext == "xlsx":
                    df_import = pd.read_excel(uploaded_file)
                else:
                    df_import = pd.read_csv(uploaded_file, encoding='utf-8-sig')

                st.dataframe(df_import.head(10))

                pid_map_rev = {p["name"]: p["id"] for p in PLATFORMS}
                imported = 0
                errors = []

                for idx, row in df_import.iterrows():
                    pname = str(row.get("平台","")).strip()
                    title_v = str(row.get("标题","")).strip()
                    status_v = str(row.get("状态","")).strip()

                    if not pname or not title_v:
                        errors.append(f"行{idx+2}: 缺少平台或标题")
                        continue
                    if pname not in pid_map_rev:
                        errors.append(f"行{idx+2}: 未知平台 '{pname}'")
                        continue

                    try:
                        add_content({
                            "platform_id": pid_map_rev[pname],
                            "title": title_v,
                            "status": status_v if status_v in STATUS_OPTIONS else "待排期",
                            "creator_type": str(row.get("类型", "")).strip() or "KOC",
                            "creator_name": str(row.get("达人", "")).strip(),
                            "plan_date": str(row.get("计划日期", "")).split()[0][:10] if pd.notna(row.get("计划日期")) else None,
                            "pub_date": str(row.get("发布日期", "")).split()[0][:10] if pd.notna(row.get("发布日期")) else None,
                            "content_type": str(row.get("内容形式", "")).strip() or "视频",
                            "note": str(row.get("备注", "")).strip(),
                        })
                        imported += 1
                    except Exception as e:
                        errors.append(f"行{idx+2}: {e}")

                st.success(f"✅ 成功导入 {imported} 条记录！")
                if errors:
                    st.warning(f"⚠️ {len(errors)} 行跳过：" + "\n".join(errors[:5]))
                    if len(errors) > 5:
                        st.caption(f"... 还有 {len(errors)-5} 个错误")

                if st.button("关闭并刷新", type="primary"):
                    st.session_state.pop("show_import_dialog", None)
                    st.rerun()

            except Exception as e:
                st.error(f"❌ 解析失败：{e}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("取消", key="cancel_import"):
            st.session_state.pop("show_import_dialog", None)
            st.rerun()


# ── 底部信息 ──
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#4A5568;font-size:11.5px;padding:12px 0;">
  小豚当家 · Content Dashboard v1.0 &nbsp;|&nbsp; Streamlit + SQLite + Plotly
  &nbsp;|&nbsp; 🎨 暗金主题
</div>
""", unsafe_allow_html=True)
