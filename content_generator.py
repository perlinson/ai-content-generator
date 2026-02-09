#!/usr/bin/env python3
"""
AI Content Generator - 多平台内容生成器
支持文章、社交媒体、营销文案自动化生成
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Platform(Enum):
    """支持的平台"""
    BLOG = "blog"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    WEIBO = "weibo"
    ZHIHU = "zhihu"
    MEDIUM = "medium"


class ContentType(Enum):
    """内容类型"""
    ARTICLE = "article"
    POST = "post"
    CAPTION = "caption"
    AD_COPY = "ad_copy"
    PRODUCT_DESC = "product_description"
    HEADLINE = "headline"
    SUMMARY = "summary"


@dataclass
class ContentTemplate:
    """内容模板"""
    name: str
    platform: str
    content_type: str
    prompt: str
    variables: List[str]
    min_length: int
    max_length: int
    tone: str
    examples: List[str]


@dataclass
class GeneratedContent:
    """生成的内容"""
    id: str
    platform: str
    content_type: str
    title: str
    body: str
    tags: List[str]
    hashtags: List[str]
    created_at: str
    quality_score: float
    variants: List[str]


class ContentTemplates:
    """内容模板库"""
    
    TEMPLATES = {
        Platform.BLOG.value: {
            ContentType.ARTICLE.value: ContentTemplate(
                name="技术博客文章",
                platform=Platform.BLOG.value,
                content_type=ContentType.ARTICLE.value,
                prompt=""""/role: 资深技术博主
/tone: 专业但易懂
/length: 1500-3000字
/format: 
- 引人入胜的开头
- 清晰的结构
- 代码示例
- 实践建议
- 总结展望

请撰写一篇关于{topic}的技术文章。""",
                variables=["topic"],
                min_length=1500,
                max_length=3000,
                tone="professional",
                examples=[
                    "Python异步编程完全指南",
                    "微服务架构实战心得"
                ]
            )
        },
        Platform.TWITTER.value: {
            ContentType.POST.value: ContentTemplate(
                name="技术分享推文",
                platform=Platform.TWITTER.value,
                content_type=ContentType.POST.value,
                prompt=""""/role: 技术专家
/tone: 简洁有力
/length: 200-280字符
/format:
- 核心观点
- 简要解释
- 1-2个代码片段或数据
- CTA互动

分享关于{topic}的见解：""",
                variables=["topic"],
                min_length=100,
                max_length=280,
                tone="engaging",
                examples=[
                    "🧵 Python 技巧 #1:",
                    "刚学到的..."
                ]
            ),
            ContentType.HEADLINE.value: ContentTemplate(
                name="病毒式标题",
                platform=Platform.TWITTER.value,
                content_type=ContentType.HEADLINE.value,
                prompt=""""/role: 标题党大师
/tone: 吸引眼球
/length: 80-100字符
/techniques:
- 数字具体化
- 痛点解决
- 反常识
- 紧迫感

为"{topic}"创作5个爆款标题：""",
                variables=["topic"],
                min_length=50,
                max_length=100,
                tone="clickbait",
                examples=[
                    "7个让你效率翻倍的Python技巧",
                    "这个误区让90%的程序员中招"
                ]
            )
        },
        Platform.WEIBO.value: {
            ContentType.POST.value: ContentTemplate(
                name="微博推广文案",
                platform=Platform.WEIBO.value,
                content_type=ContentType.POST.value,
                prompt=""""/role: 生活方式博主
/tone: 亲切有趣
/length: 100-200字
/elements:
- 热点结合
- 个人故事
- 轻松幽默
- 话题标签

分享关于{topic}的感受：""",
                variables=["topic"],
                min_length=50,
                max_length=200,
                tone="casual",
                examples=[
                    "救命！这个真的绝了！",
                    "姐妹们快看过来！！"
                ]
            )
        },
        Platform.LINKEDIN.value: {
            ContentType.POST.value: ContentTemplate(
                name="职场洞察",
                platform=Platform.LINKEDIN.value,
                content_type=ContentType.POST.value,
                prompt=""""/role: 职场导师
/tone: 专业真诚
/length: 800-1500字符
/structure:
- 问题引入
- 亲身经历
- 方法论
- 行动建议

分享关于{topic}的职场心得：""",
                variables=["topic"],
                min_length=500,
                max_length=1500,
                tone="professional",
                examples=[
                    "5年职场教会我的",
                    "关于晋升那些事"
                ]
            )
        },
        Platform.ZHIHU.value: {
            ContentType.ARTICLE.value: ContentTemplate(
                name="知乎回答/文章",
                platform=Platform.ZHIHU.value,
                content_type=ContentType.ARTICLE.value,
                prompt=""""/role: 领域专家
/tone: 理性分析
/length: 1000-5000字
/format:
- 问题拆解
- 原因分析
- 解决方案
- 案例支撑

回答：{question}""",
                variables=["question"],
                min_length=500,
                max_length=5000,
                tone="analytical",
                examples=[
                    "为什么Python这么流行？",
                    "如何入门机器学习？"
                ]
            )
        }
    }


class AIContentGenerator:
    """AI内容生成器"""
    
    def __init__(self):
        self.templates = ContentTemplates()
        self.generation_history = []
        self.quality_scores = []
    
    def get_available_platforms(self) -> List[Dict]:
        """获取可用平台"""
        return [
            {"id": p.value, "name": p.name, "icon": self._get_platform_icon(p)}
            for p in Platform
        ]
    
    def _get_platform_icon(self, platform: Platform) -> str:
        icons = {
            Platform.BLOG: "📝",
            Platform.TWITTER: "🐦",
            Platform.INSTAGRAM: "📷",
            Platform.LINKEDIN: "💼",
            Platform.WEIBO: "🔹",
            Platform.ZHIHU: "知乎",
            Platform.MEDIUM: "📰"
        }
        return icons.get(platform, "📄")
    
    def get_templates_for_platform(self, platform: Platform) -> List[Dict]:
        """获取平台可用模板"""
        templates = self.templates.TEMPLATES.get(platform.value, {})
        return [
            {
                "id": ct.value,
                "name": t.name,
                "type": t.content_type,
                "tone": t.tone,
                "length": f"{t.min_length}-{t.max_length}字",
                "examples": t.examples[:2]
            }
            for ct, t in templates.items()
        ]
    
    def generate_content(
        self,
        platform: Platform,
        content_type: ContentType,
        topic: str,
        tone: str = "neutral",
        language: str = "zh"
    ) -> GeneratedContent:
        """生成内容"""
        
        # 获取模板
        template = self.templates.TEMPLATES.get(
            platform.value, {}
        ).get(content_type.value)
        
        if not template:
            raise ValueError(f"模板不存在: {platform.value}/{content_type.value}")
        
        # 构建提示词
        prompt = template.prompt.replace(f"{{{template.variables[0]}}}", topic)
        if language == "en":
            prompt = f"/language: English\n{prompt}"
        
        # 模拟AI生成（实际应调用LLM API）
        content = self._simulate_generation(prompt, template, topic)
        
        # 生成标签和话题
        tags = self._generate_tags(topic, platform)
        hashtags = self._generate_hashtags(topic, platform)
        
        # 计算质量分数
        quality_score = self._calculate_quality(content, template)
        
        # 创建内容对象
        generated = GeneratedContent(
            id=self._generate_id(topic, platform),
            platform=platform.value,
            content_type=content_type.value,
            title=self._generate_title(topic, content_type),
            body=content,
            tags=tags,
            hashtags=hashtags,
            created_at=datetime.now().isoformat(),
            quality_score=quality_score,
            variants=self._generate_variants(content, platform)
        )
        
        # 保存历史
        self.generation_history.append(generated)
        self.quality_scores.append(quality_score)
        
        logger.info(f"生成了内容: {generated.platform}/{generated.content_type} (质量: {quality_score:.2f})")
        
        return generated
    
    def _simulate_generation(
        self, 
        prompt: str, 
        template: ContentTemplate,
        topic: str
    ) -> str:
        """模拟内容生成（实际应调用AI API）"""
        
        # 根据模板类型生成不同内容
        if "技术博客" in template.name or "技术文章" in template.name:
            return f"""# {topic}完全指南

## 引言

在当今快速发展的技术世界中，{topic}已经成为了一个不可忽视的重要话题。无论你是初学者还是资深开发者，掌握{topic}都将为你的职业生涯带来巨大的帮助。

## 什么是{topic}？

{topic}是[领域]中最具影响力的技术/概念之一。它主要解决以下问题：

- 提高开发效率
- 降低维护成本
- 提升系统性能

## 核心原理

{topic}的核心思想可以概括为三个要点：

### 1. 原理一

详细的原理解释...

### 2. 原理二

详细的原理解释...

### 3. 原理三

详细的原理解释...

## 实战示例

```python
# {topic}示例代码
def example_function():
    # 代码示例
    result = process_data()
    return result
```

## 应用场景

{topic}在实际工作中的应用场景非常广泛：

1. **场景一** - 具体应用...
2. **场景二** - 具体应用...
3. **场景三** - 具体应用...

## 最佳实践

基于多年的经验总结，以下是{topic}的最佳实践：

1. **实践一** - 具体建议
2. **实践二** - 具体建议
3. **实践三** - 具体建议

## 常见问题

### Q1: {topic}学习曲线陡峭吗？

A: 入门其实很简单，深入需要时间...

### Q2: 需要什么基础？

A: 建议先掌握...

## 总结

{topic}是一个值得深入学习的技术/概念。希望本文能帮助你更好地理解和应用{topic}。

---

💬 你对{topic}有什么看法？欢迎在评论区交流！"""
        
        elif "推文" in template.name or "Twitter" in template.name:
            return f"""🧵 关于{topic}，分享几个关键洞察：

{topic}正在改变我们工作的方式。

核心观点：
→ 效率提升300%
→ 成本降低50%
→ 体验翻倍

关键数据支持这一结论。

你有什么经验？👇

#Tech #{topic.replace(' ', '')} #AI"""
        
        elif "微博" in template.name:
            return f"""救命！姐妹们！{topic}真的绝了！！！🙀

最近在研究{topic}，没想到效果这么惊艳！

✨ 具体感受：
- 操作简单
- 效果明显
- 性价比高

姐妹们一定要试试！冲冲冲！💪

#{topic} #好物分享 #生活技巧"""
        
        elif "职场" in template.name or "LinkedIn" in template.name:
            return f"""💼 关于{topic}，分享一段真实的职场经历。

3年前，我对{topic}一无所知。
2年前，我开始接触并学习。
现在，{topic}已经成为我工作中最重要的技能之一。

关键转变发生在：

📌 第一次认知突破
📌 第一次实践尝试  
📌 第一次获得认可

给职场新人的建议：

1️⃣ 不要怕犯错
2️⃣ 持续学习
3️⃣ 建立个人品牌

{topic}的时代已经到来，你准备好了吗？

#职场成长 #技能提升 #{topic}"""
        
        else:
            return f"""关于{topic}的深度分析：

{topic}是当前最受关注的话题之一。本文将从多个角度进行全面解读。

## 为什么{topic}如此重要？

- 技术创新驱动
- 市场需求旺盛
- 应用场景广泛

## 核心观点

{topic}的核心价值在于...

## 发展趋势

未来{topic将朝着以下方向发展：

→ 更加智能化
→ 更加普及化
→ 更加个性化

## 结论

{topic}值得每个人关注和学习。

你对{topic}有什么看法？"""
    
    def _generate_title(self, topic: str, content_type: ContentType) -> str:
        """生成标题"""
        titles = {
            ContentType.ARTICLE: [
                f"关于{topic}，你需要知道的一切",
                f"{topic}完全指南：从入门到精通",
                f"为什么{topic}如此重要？",
                f"{topic}的终极解答",
                f"深入理解{topic}"
            ],
            ContentType.POST: [
                f"关于{topic}的思考",
                f"{topic}：我的几点看法",
                f"聊聊{topic}",
                f"关于{topic}，分享给需要的人"
            ],
            ContentType.AD_COPY: [
                f"限时福利！{topic}免费领！",
                f"发现了{topic}的神仙用法！",
                f"后悔没早点知道的{topic}技巧！",
                f"{topic}，让生活更美好！"
            ]
        }
        
        import random
        return random.choice(titles.get(content_type, titles[ContentType.ARTICLE]))
    
    def _generate_tags(self, topic: str, platform: Platform) -> List[str]:
        """生成标签"""
        base_tags = [topic]
        
        if platform == Platform.TWITTER:
            return ["Tech", "AI", topic.replace(" ", "")]
        elif platform == Platform.WEIBO:
            return [f"#{topic}#", "#好物分享#", "#生活日记#"]
        elif platform == Platform.ZHIHU:
            return ["编程", "技术", topic.replace(" ", "")]
        else:
            return base_tags
    
    def _generate_hashtags(self, topic: str, platform: Platform) -> List[str]:
        """生成话题标签"""
        tags = [f"#{topic.replace(' ', '')}#"]
        
        if platform == Platform.TWITTER:
            tags.extend(["#Tech", "#Innovation", "#AI"])
        elif platform == Platform.INSTAGRAM:
            tags.extend(["#tech", "#innovation", "#coding"])
        
        return tags[:5]
    
    def _generate_variants(self, content: str, platform: Platform) -> List[str]:
        """生成变体"""
        variants = []
        
        # 短版本
        if len(content) > 500:
            variants.append(content[:300] + "...")
        
        # 提问版本
        variants.append(content + "\n\n你对这个问题怎么看？")
        
        # 号召版本
        variants.append(content + "\n\n觉得有用的话，记得点赞收藏！")
        
        return variants
    
    def _calculate_quality(self, content: str, template: ContentTemplate) -> float:
        """计算质量分数"""
        score = 0.5
        
        # 长度检查
        length = len(content)
        if template.min_length <= length <= template.max_length:
            score += 0.2
        
        # 结构检查
        if "\n" in content:
            score += 0.1
        if "#" in content or "##" in content:
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_id(self, topic: str, platform: Platform) -> str:
        """生成内容ID"""
        timestamp = datetime.now().timestamp()
        raw = f"{topic}{platform.value}{timestamp}"
        return hashlib.md5(raw.encode()).hexdigest()[:8]
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        return {
            "total_generated": len(self.generation_history),
            "avg_quality": sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0,
            "by_platform": self._count_by_platform(),
            "by_type": self._count_by_type()
        }
    
    def _count_by_platform(self) -> Dict[str, int]:
        """按平台统计"""
        counts = {}
        for c in self.generation_history:
            counts[c.platform] = counts.get(c.platform, 0) + 1
        return counts
    
    def _count_by_type(self) -> Dict[str, int]:
        """按类型统计"""
        counts = {}
        for c in self.generation_history:
            counts[c.content_type] = counts.get(c.content_type, 0) + 1
        return counts


def demo():
    """演示"""
    generator = AIContentGenerator()
    
    # 显示可用平台
    print("=" * 50)
    print("🤖 AI内容生成器")
    print("=" * 50)
    print("\n可用平台:")
    for p in generator.get_available_platforms():
        print(f"  {p['icon']} {p['name']}")
    
    # 生成示例内容
    print("\n" + "=" * 50)
    print("📝 生成示例内容...")
    print("=" * 50)
    
    # 技术博客
    content = generator.generate_content(
        platform=Platform.BLOG,
        content_type=ContentType.ARTICLE,
        topic="Python异步编程"
    )
    
    print(f"\n标题: {content.title}")
    print(f"平台: {content.platform}")
    print(f"质量分数: {content.quality_score:.2f}")
    print(f"\n标签: {', '.join(content.tags)}")
    print(f"话题: {', '.join(content.hashtags)}")
    print(f"\n内容预览 ({len(content.body)}字):")
    print("-" * 40)
    print(content.body[:500] + "...")
    
    # 统计
    print("\n" + "=" * 50)
    print("📊 统计信息:")
    stats = generator.get_statistics()
    print(f"  总生成数: {stats['total_generated']}")
    print(f"  平均质量: {stats['avg_quality']:.2f}")


if __name__ == "__main__":
    demo()
