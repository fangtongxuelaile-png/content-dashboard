# -*- coding: utf-8 -*-
"""小豚当家内容看板 — 暗金主题CSS（与AI大赛汇报风格一致）"""

DARK_GOLD_CSS = """
<style>
/* ── 全局重置 ── */
:root {
  --bg-primary: #0A0E17;
  --bg-card: #111827;
  --bg-elevated: #1A2332;
  --gold: #C9A84C;
  --gold-light: rgba(201,168,76,0.15);
  --gold-glow: rgba(201,168,76,0.25);
  --blue: #4C8AC9;
  --blue-light: rgba(76,138,201,0.15);
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --success: #22C55E;
  --warning: #F59E0B;
  --danger: #EF4444;
}

/* 页面容器 */
.block-container {
  padding-top: 1.2rem !important;
  padding-bottom: 2rem !important;
  max-width: 1600px !important;
  background-color: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}

/* ── 左侧边栏（深蓝底色，与AI汇报一致）── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #08101f 0%, #0c1829 50%, #0a1526 100%) !important;
  border-right: 1px solid rgba(201,168,76,0.10) !important;
}
[data-testid="stSidebar"] * {
  color: #cfe3ff !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"],
[data-testid="stSidebar"] [data-testid="stMultiselect"] {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] button[kind="primary"] {
  background: linear-gradient(135deg, rgba(201,168,76,0.25), rgba(201,168,76,0.12)) !important;
  border: 1px solid var(--gold) !important;
  color: var(--gold) !important;
  font-weight: 600 !important;
  border-radius: 6px !important;
}

/* ── Hero 标题区 ── */
.hero-banner {
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 20px;
  color: white;
  background:
    radial-gradient(circle at 12% 18%, rgba(201,168,76,0.12), transparent 35%),
    radial-gradient(circle at 88% 70%, rgba(76,138,201,0.08), transparent 35%),
    linear-gradient(135deg, #0d1320 0%, #111b30 50%, #162d52 100%);
  border: 1px solid rgba(201,168,76,0.14);
  box-shadow: 0 12px 32px rgba(0,0,0,0.25);
}
.hero-title {
  font-size: 28px;
  font-weight: 900;
  margin: 0;
  letter-spacing: 0.5px;
  color: #fff;
}
.hero-sub {
  color: var(--text-secondary);
  margin-top: 8px;
  font-size: 13.5px;
}

/* ── KPI 指标卡片 ── */
[data-testid="stMetric"] {
  background: linear-gradient(180deg, var(--bg-card), #0d1420) !important;
  border: 1px solid rgba(201,168,76,0.12) !important;
  border-radius: 14px !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.20), inset 0 1px 0 rgba(255,255,255,0.03) !important;
  padding: 18px 20px !important;
  position: relative;
  overflow: hidden;
}
[data-testid="stMetric"]:before {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--gold), var(--blue));
  opacity: 0.7;
}
[data-testid="stMetricLabel"] {
  color: var(--text-muted) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
[data-testid="stMetricValue"] {
  font-size: 28px !important;
  font-weight: 900 !important;
  color: var(--text-primary) !important;
}
[data-testid="stMetricDelta"] {
  font-size: 13px !important;
  font-weight: 700 !important;
}
[data-testid="stMetricDelta"][data-negative="true"] { color: var(--danger) !important; }
[data-testid="stMetricDelta"][data-negative="false"] { color: var(--success) !important; }

/* ── 区块标题 ── */
.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 24px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(201,168,76,0.10);
}
.section-header h3 {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
}
.section-header .badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--gold-light);
  color: var(--gold);
  font-weight: 600;
  letter-spacing: 0.03em;
}

/* ── 状态标签 ── */
.status-tag {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.status-待排期 { background: rgba(100,116,139,0.15); color: #94A3B8; }
.status-素材制作中 { background: rgba(76,138,201,0.15); color: #60A5FA; }
.status-待审核 { background: rgba(245,158,11,0.15); color: #FBBF24; }
.status-已发布 { background: rgba(34,197,94,0.15); color: #4ADE80; }
.status-异常 { background: rgba(239,68,68,0.15); color: #F87171; }
.status-已下架 { background: rgba(148,163,184,0.10); color: #9CA3AF; }

/* ── 表格样式 ── */
.stDataFrame {
  background: var(--bg-card) !important;
  border: 1px solid rgba(201,168,76,0.10) !important;
  border-radius: 12px !important;
  overflow: hidden;
}
.stDataFrame thead th {
  background: #1E293B !important;
  color: var(--text-secondary) !important;
  font-weight: 700 !important;
  font-size: 12.5px !important;
  text-align: left !important;
  padding: 10px 14px !important;
  position: sticky;
  top: 0;
  z-index: 2;
}
.stDataFrame tbody td {
  padding: 8px 14px !important;
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
  font-size: 13px !important;
  color: var(--text-secondary) !important;
}
.stDataFrame tbody tr:hover td {
  background: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
}

/* ── 图表容器 ── */
.chart-container {
  background: var(--bg-card);
  border: 1px solid rgba(201,168,76,0.10);
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}
.js-plotly-plot .plotly .modebar { background: rgba(17,24,39,0.85) !important; }

/* ── 按钮 ── */
button[kind="primary"] {
  background: linear-gradient(135deg, rgba(201,168,76,0.22), rgba(201,168,76,0.10)) !important;
  border: 1px solid var(--gold) !important;
  color: var(--gold) !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}
button[kind="primary"]:hover {
  background: linear-gradient(135deg, rgba(201,168,76,0.35), rgba(201,168,76,0.18)) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(201,168,76,0.15) !important;
}
button[kind="secondary"] {
  background: rgba(255,255,255,0.05) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
}

/* ── 对话框/弹窗 ── */
[data-testid="stDialog"] .stDialog > div:first-child {
  background: var(--bg-elevated) !important;
  border: 1px solid rgba(201,168,76,0.18) !important;
  border-radius: 16px !important;
}

/* ── 文件上传 ── */
[data-testid="stFileUploader"] {
  border: 1px dashed rgba(201,168,76,0.25) !important;
  border-radius: 14px !important;
  background: rgba(201,168,76,0.03) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid rgba(201,168,76,0.10) !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
  color: var(--text-primary) !important;
  font-weight: 700 !important;
}

/* ── 隐藏 Streamlit 默认装饰 ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {display: none !important;}

/* ── 分隔线 ── */
.gold-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(201,168,76,0.25), transparent);
  margin: 20px 0;
  border: none;
}
</style>
"""


def get_plotly_template():
    """Plotly暗金配色模板"""
    return dict(
        layout=dict(
            paper_bgcolor='#0A0E17',
            plot_bgcolor='#111827',
            font=dict(color='#F1F5F9', family='Noto Sans SC, sans-serif'),
            title=dict(font=dict(size=18, color='#C9A84C', family='Noto Serif SC, serif')),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.04)',
                linecolor='rgba(255,255,255,0.08)',
                tickfont=dict(color='#94A3B8', size=11)
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.04)',
                linecolor='rgba(255,255,255,0.08)',
                tickfont=dict(color='#94A3B8', size=11)
            ),
            legend=dict(
                font=dict(color='#94A3B8', size=11),
                bgcolor='rgba(17,24,39,0.8)',
                bordercolor='rgba(201,168,76,0.12)'
            ),
            margin=dict(t=40, r=20, b=50, l=60)
        )
    )


# 平台配置
PLATFORMS = [
    {"id": 1, "name": "CID",       "icon": "💰", "color": "#C9A84C"},
    {"id": 2, "name": "抖音达人",   "icon": "🎵", "color": "#FE2C55"},
    {"id": 3, "name": "种草通",     "icon": "🌱", "color": "#22C55E"},
    {"id": 4, "name": "B站达人",    "icon": "📺", "color": "#00A1D6"},
    {"id": 5, "name": "B站投放",    "icon": "📡", "color": "#00A1D6"},
    {"id": 6, "name": "小红书KOC",  "icon": "🔴", "color": "#FF2442"},
    {"id": 7, "name": "视频号",     "icon": "💚", "color": "#07C160"},
]

STATUS_OPTIONS = ["待排期", "素材制作中", "待审核", "已发布", "已下架", "异常"]
STATUS_COLORS = {
    "待排期": "#94A3B8",
    "素材制作中": "#60A5FA",
    "待审核": "#FBBF24",
    "已发布": "#4ADE80",
    "异常": "#F87171",
    "已下架": "#9CA3AF",
}

CREATOR_TYPES = ["KOL", "KOC", "自营", "品牌"]
CONTENT_TYPES = ["视频", "图文", "直播", "短视频"]
