"""
AI Content Monetization API - 内容变现API服务
支持多平台发布、数据分析、收益追踪
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)

# 配置
SECRET_KEY = "your-secret-key-change-this"


# ==================== 数据模型 ====================

@dataclass
class Content:
    """内容数据模型"""
    id: str
    platform: str
    content_type: str
    title: str
    body: str
    tags: List[str]
    hashtags: List[str]
    status: str  # draft, scheduled, published, failed
    scheduled_at: Optional[str]
    published_at: Optional[str]
    created_at: str
    updated_at: str
    
    # 变现数据
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    earnings: float = 0.0


@dataclass
class PlatformAccount:
    """平台账号"""
    id: str
    platform: str
    username: str
    followers: int
    is_connected: bool
    access_token: Optional[str]
    refresh_token: Optional[str]
    token_expires: Optional[str]


@dataclass
class Analytics:
    """分析数据"""
    total_content: int
    total_views: int
    total_engagement: float
    avg_engagement_rate: float
    top_platform: str
    earnings_by_platform: Dict[str, float]
    trends: Dict[str, List]


# ==================== 数据库模拟 ====================

class Database:
    """内存数据库"""
    
    def __init__(self):
        self.contents: Dict[str, Content] = {}
        self.accounts: Dict[str, PlatformAccount] = {}
        self.analytics_cache = None
        self.last_update = datetime.now()
    
    def init_sample_data(self):
        """初始化示例数据"""
        samples = [
            {
                "id": "cnt_001",
                "platform": "twitter",
                "content_type": "post",
                "title": "Python异步编程技巧",
                "body": "🧵 关于Python异步编程，分享几个关键洞察...",
                "tags": ["Python", "异步"],
                "hashtags": ["#Tech", "#Python"],
                "status": "published",
                "scheduled_at": None,
                "published_at": "2026-02-08T10:00:00",
                "views": 12500,
                "likes": 892,
                "shares": 156,
                "comments": 45,
                "earnings": 12.50
            },
            {
                "id": "cnt_002", 
                "platform": "blog",
                "content_type": "article",
                "title": "AI工具完全指南",
                "body": "# AI工具完全指南\n\n在当今...",
                "tags": ["AI", "工具"],
                "hashtags": ["#AI", "#工具"],
                "status": "published",
                "scheduled_at": None,
                "published_at": "2026-02-07T14:00:00",
                "views": 45600,
                "likes": 2340,
                "shares": 890,
                "comments": 123,
                "earnings": 45.80
            },
            {
                "id": "cnt_003",
                "platform": "linkedin",
                "content_type": "post",
                "title": "5年职场教会我的",
                "body": "💼 关于职场成长...",
                "tags": ["职场", "成长"],
                "hashtags": ["#职场", "#成长"],
                "status": "scheduled",
                "scheduled_at": "2026-02-10T09:00:00",
                "published_at": None,
                "views": 0,
                "likes": 0,
                "shares": 0,
                "comments": 0,
                "earnings": 0.0
            }
        ]
        
        for s in samples:
            content = Content(**s)
            self.contents[content.id] = content
        
        # 示例账号
        self.accounts = {
            "acc_001": PlatformAccount(
                id="acc_001",
                platform="twitter",
                username="@tech_creator",
                followers=15000,
                is_connected=True,
                access_token="mock_token_xxx",
                refresh_token=None,
                token_expires=None
            ),
            "acc_002": PlatformAccount(
                id="acc_002",
                platform="blog",
                username="tech-blog.com",
                followers=25000,
                is_connected=True,
                access_token=None,
                refresh_token=None,
                token_expires=None
            )
        }


db = Database()
db.init_sample_data()


# ==================== 工具函数 ====================

def generate_id(prefix: str = "cnt") -> str:
    """生成唯一ID"""
    timestamp = datetime.now().timestamp()
    raw = f"{prefix}{timestamp}"
    return f"{prefix}_{hashlib.md5(raw.encode()).hexdigest()[:8]}"


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        # 简化验证
        g.user_id = "user_001"
        return f(*args, **kwargs)
    return decorated


# ==================== API端点 ====================

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/analytics/overview', methods=['GET'])
@require_auth
def analytics_overview():
    """分析概览"""
    contents = list(db.contents.values())
    
    total_views = sum(c.views for c in contents)
    total_engagement = sum(c.likes + c.shares + c.comments for c in contents)
    total_earnings = sum(c.earnings for c in contents)
    
    # 按平台统计
    platform_stats = {}
    for c in contents:
        if c.platform not in platform_stats:
            platform_stats[c.platform] = {"views": 0, "engagement": 0, "earnings": 0}
        platform_stats[c.platform]["views"] += c.views
        platform_stats[c.platform]["engagement"] += c.likes + c.shares + c.comments
        platform_stats[c.platform]["earnings"] += c.earnings
    
    # 找出最佳平台
    top_platform = max(platform_stats.keys(), 
                      key=lambda p: platform_stats[p]["views"]) if platform_stats else "N/A"
    
    # 计算趋势数据（最近7天）
    trends = {
        "views": [1000 * (i + 1) for i in range(7)],
        "engagement": [100 * (i + 1) for i in range(7)],
        "earnings": [5 * (i + 1) for i in range(7)]
    }
    
    return jsonify({
        "total_content": len(contents),
        "total_views": total_views,
        "total_engagement": total_engagement,
        "avg_engagement_rate": round(total_engagement / total_views * 100, 2) if total_views > 0 else 0,
        "total_earnings": round(total_earnings, 2),
        "top_platform": top_platform,
        "platform_breakdown": platform_stats,
        "trends": trends,
        "last_updated": datetime.now().isoformat()
    })


@app.route('/api/contents', methods=['GET'])
@require_auth
def list_contents():
    """内容列表"""
    contents = list(db.contents.values())
    
    # 过滤参数
    platform = request.args.get('platform')
    status = request.args.get('status')
    
    if platform:
        contents = [c for c in contents if c.platform == platform]
    if status:
        contents = [c for c in contents if c.status == status]
    
    return jsonify({
        "contents": [asdict(c) for c in contents],
        "total": len(contents)
    })


@app.route('/api/contents', methods=['POST'])
@require_auth
def create_content():
    """创建内容"""
    data = request.json
    
    content = Content(
        id=generate_id(),
        platform=data.get('platform', 'blog'),
        content_type=data.get('content_type', 'article'),
        title=data.get('title', ''),
        body=data.get('body', ''),
        tags=data.get('tags', []),
        hashtags=data.get('hashtags', []),
        status='draft',
        scheduled_at=data.get('scheduled_at'),
        published_at=None,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    db.contents[content.id] = content
    
    return jsonify({
        "content": asdict(content),
        "message": "Content created successfully"
    }), 201


@app.route('/api/contents/<content_id>', methods=['GET'])
@require_auth
def get_content(content_id):
    """获取内容"""
    content = db.contents.get(content_id)
    if not content:
        return jsonify({"error": "Content not found"}), 404
    return jsonify({"content": asdict(content)})


@app.route('/api/contents/<content_id>/publish', methods=['POST'])
@require_auth
def publish_content(content_id):
    """发布内容"""
    content = db.contents.get(content_id)
    if not content:
        return jsonify({"error": "Content not found"}), 404
    
    # 模拟发布
    content.status = 'published'
    content.published_at = datetime.now().isoformat()
    content.updated_at = datetime.now().isoformat()
    
    # 模拟数据更新
    content.views = 100
    content.likes = 10
    content.earnings = 1.50
    
    return jsonify({
        "message": "Content published successfully",
        "content": asdict(content)
    })


@app.route('/api/accounts', methods=['GET'])
@require_auth
def list_accounts():
    """账号列表"""
    accounts = list(db.accounts.values())
    return jsonify({
        "accounts": [asdict(a) for a in accounts],
        "total": len(accounts)
    })


@app.route('/api/accounts/<platform>/connect', methods=['POST'])
@require_auth
def connect_account(platform):
    """连接账号"""
    # 模拟OAuth流程
    account = PlatformAccount(
        id=generate_id("acc"),
        platform=platform,
        username=f"new_user_{platform}",
        followers=0,
        is_connected=True,
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        token_expires=(datetime.now() + timedelta(hours=1)).isoformat()
    )
    
    db.accounts[account.id] = account
    
    return jsonify({
        "message": f"Connected to {platform}",
        "account": asdict(account)
    })


@app.route('/api/monetization/earnings', methods=['GET'])
@require_auth
def get_earnings():
    """收益数据"""
    contents = list(db.contents.values())
    
    # 按平台分组
    by_platform = {}
    by_day = {}
    by_month = {}
    
    for c in contents:
        # 按平台
        if c.platform not in by_platform:
            by_platform[c.platform] = 0
        by_platform[c.platform] += c.earnings
        
        # 按天
        if c.published_at:
            day = c.published_at[:10]
            if day not in by_day:
                by_day[day] = 0
            by_day[day] += c.earnings
    
    total = sum(c.earnings for c in contents)
    
    return jsonify({
        "total_earnings": round(total, 2),
        "by_platform": by_platform,
        "by_day": by_day,
        "pending_payout": round(total * 0.7, 2),  # 70%待提现
        "available_payout": round(total * 0.3, 2)  # 30%可提现
    })


@app.route('/api/scheduler/schedule', methods=['POST'])
@require_auth
def schedule_content():
    """定时发布"""
    data = request.json
    content_id = data.get('content_id')
    scheduled_at = data.get('scheduled_at')
    
    content = db.contents.get(content_id)
    if not content:
        return jsonify({"error": "Content not found"}), 404
    
    content.status = 'scheduled'
    content.scheduled_at = scheduled_at
    content.updated_at = datetime.now().isoformat()
    
    return jsonify({
        "message": "Content scheduled successfully",
        "content": asdict(content)
    })


@app.route('/api/recommendations', methods=['GET'])
@require_auth
def get_recommendations():
    """获取推荐"""
    return jsonify({
        "best_times": {
            "twitter": ["09:00", "12:00", "18:00"],
            "blog": ["07:00", "20:00"],
            "linkedin": ["08:00", "10:00"]
        },
        "trending_topics": [
            {"topic": "AI", "growth": "+25%"},
            {"topic": "Python", "growth": "+18%"},
            {"topic": "Automation", "growth": "+15%"}
        ],
        "content_ideas": [
            "5个让你效率翻倍的AI工具",
            "为什么Python仍然是2024最流行的语言",
            "从0到1：AI辅助编程完全指南"
        ]
    })


# ==================== 启动 ====================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
