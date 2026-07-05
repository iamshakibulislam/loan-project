#!/usr/bin/env python
"""Atlas Fund Capital — Blog MCP Server.

Run:  python mcp_blog_server.py

MCP endpoint:  http://localhost:8001/mcp/blog

Connect Claude.ai at Settings → Developer → MCP Servers → Add Server
  URL:  http://<your-host>:8001/mcp/blog
  Transport: Streamable HTTP
"""

import os
import re
import sys

# ---- Bootstrap Django ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from django.utils import timezone
from django.utils.text import slugify
from asgiref.sync import sync_to_async

# ---- Imports after Django setup ----
from mcp.server.fastmcp import FastMCP

# ---- Config ----
SITE_URL = os.environ.get("SITE_URL", "https://atlasfundcapital.com")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8001"))

# ---- Category Selector ----
CATEGORIES = [
    ("capital-strategy", "Capital Strategy", [
        "capital", "funding", "raise", "investment", "equity", "debt",
        "financing round", "venture", "growth capital", "working capital",
        "funding strategy",
    ]),
    ("preparation", "Preparation", [
        "prepare", "ready", "documentation", "financial statements",
        "business plan", "pitch deck", "due diligence", "credit score",
        "application", "qualify", "eligibility", "checklist", "requirements",
    ]),
    ("government-programs", "Government Programs", [
        "government", "federal", "state program", "grant", "subsidy",
        "stimulus", "government-backed", "usda", "treasury",
        "government loan", "public program",
    ]),
    ("access-to-capital", "Access to Capital", [
        "access to capital", "lender", "bank loan", "alternative lending",
        "borrower", "credit access", "funding access", "loan options",
        "financing options", "capital sources", "where to get",
    ]),
    ("market-analysis", "Market Analysis", [
        "market", "trends", "industry report", "economic", "forecast",
        "analysis", "data", "statistics", "research", "outlook", "sector",
        "benchmark",
    ]),
    ("strategy", "Strategy", [
        "strategy", "planning", "roadmap", "growth plan", "expansion",
        "scale", "optimization", "efficiency", "restructuring", "pivot",
        "business model",
    ]),
    ("cash-flow", "Cash Flow", [
        "cash flow", "cashflow", "revenue", "expenses", "profitability",
        "working capital", "liquidity", "burn rate", "runway",
        "receivables", "payables", "collections", "invoicing",
    ]),
    ("industry-focus", "Industry Focus", [
        "industry", "sector", "niche", "vertical", "healthcare",
        "construction", "retail", "restaurant", "manufacturing",
        "technology", "real estate", "hospitality", "transportation",
        "logistics", "agriculture", "specific industry",
    ]),
    ("sba-loans", "SBA Loans", [
        "sba", "small business administration", "7a", "504", "sba express",
        "sba loan", "government guaranteed", "sba program", "microloan",
        "disaster loan",
    ]),
    ("business-growth", "Business Growth", [
        "grow", "growth", "expand", "hire", "new market", "scale up",
        "revenue growth", "customer acquisition", "launch", "new product",
        "diversify", "franchise", "merger", "acquisition",
    ]),
]


def detect_category(title, content, subtitle=""):
    text = f"{title} {subtitle} {content}".lower()
    scores = []
    for slug, _label, keywords in CATEGORIES:
        score = sum(text.count(kw.lower()) for kw in keywords)
        scores.append((slug, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[0][0] if scores[0][1] > 0 else "business-growth"


def get_label(slug):
    for s, label, _ in CATEGORIES:
        if s == slug:
            return label
    return "Business Growth"


# ---- DB Helpers ----
def _generate_slug(title):
    from atlas.models import BlogPost
    base = slugify(title)[:350] or "untitled-post"
    s = base
    c = 1
    while BlogPost.objects.filter(slug=s).exists():
        s = f"{base}-{c}"
        c += 1
    return s


def _calc_read_time(content):
    text = re.sub(r"<[^>]+>", "", content)
    text = re.sub(r"\s+", " ", text).strip()
    words = len(text.split()) if text else 0
    return max(1, round(words / 200))


def _auto_excerpt(content):
    text = re.sub(r"<[^>]+>", " ", content)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= 550:
        return text
    return text[:550] + "..."


# ---- MCP Server ----
mcp = FastMCP(
    "atlas-blog-mcp",
    streamable_http_path="/mcp/blog",
    json_response=True,
    host=MCP_HOST,
    port=MCP_PORT,
)


# ---- Sync helpers for Django ORM (called via sync_to_async) ----
def _sync_create_blog_post(title, content, subtitle, excerpt, author_email):
    from atlas.models import BlogPost, User

    cat_slug = detect_category(title, content, subtitle)
    if not excerpt:
        excerpt = _auto_excerpt(content)

    slug = _generate_slug(title)
    read_time = _calc_read_time(content)

    author = None
    if author_email:
        author = User.objects.filter(email=author_email).first()
    if not author:
        author = User.objects.filter(role="superadmin").first()

    post = BlogPost.objects.create(
        title=title,
        slug=slug,
        subtitle=subtitle or "",
        category=cat_slug,
        excerpt=excerpt,
        content=content,
        read_time=read_time,
        is_published=True,
        published_at=timezone.now(),
        author=author,
    )

    url = f"{SITE_URL}/blog/{post.slug}/"
    return (
        f"Blog post created and published successfully!\n\n"
        f'Title: "{post.title}"\n'
        f"Category: {get_label(cat_slug)} (auto-detected)\n"
        f"Slug: {post.slug}\n"
        f"Read Time: {post.read_time} min\n"
        f"Published At: {post.published_at}\n"
        f"URL: {url}\n\n"
        f"Remember to upload a featured image manually via the superadmin blog editor."
    )


def _sync_list_recent_posts(limit):
    from atlas.models import BlogPost
    limit = min(limit or 5, 20)
    posts = list(BlogPost.objects.filter(is_published=True).order_by("-published_at")[:limit])
    if not posts:
        return "No published blog posts found."
    lines = ["Recent blog posts:", ""]
    for p in posts:
        lines.append(
            f"- [{p.title}]({SITE_URL}/blog/{p.slug}/) — "
            f"{p.category} — {p.read_time} min read ({p.published_at})"
        )
    return "\n".join(lines)


# ---- MCP Tools ----
@mcp.tool()
async def create_blog_post(
    title: str,
    content: str,
    subtitle: str = "",
    excerpt: str = "",
    author_email: str = "",
) -> str:
    """Create and publish a new blog post on Atlas Fund Capital.

    Auto-published immediately. Category is auto-detected from content.
    Featured image must be uploaded manually later via the superadmin editor.

    Args:
        title: Blog post title — SEO-optimized, compelling (max 300 chars)
        content: Full HTML body. Use H1/H2/H3 headings, paragraphs, lists,
            blockquotes. No images (added manually later).
        subtitle: Optional subtitle shown below title on detail page
        excerpt: Brief summary for listing cards (max 600 chars). Auto-generated if empty.
        author_email: Email of author. Uses superadmin if omitted.
    """
    return await sync_to_async(_sync_create_blog_post)(
        title, content, subtitle, excerpt, author_email
    )


@mcp.tool()
async def list_recent_posts(limit: int = 5) -> str:
    """List recently published blog posts.

    Args:
        limit: Number of posts (default 5, max 20)
    """
    return await sync_to_async(_sync_list_recent_posts)(limit)


# ----
if __name__ == "__main__":
    print(f"Atlas Blog MCP Server starting on {MCP_HOST}:{MCP_PORT}")
    print(f"MCP endpoint: http://{MCP_HOST}:{MCP_PORT}/mcp/blog")
    mcp.run(transport="streamable-http")
