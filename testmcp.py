#!/usr/bin/env python
"""Test MCP blog creation directly.  Run: python testmcp.py

Also pass --clean to delete the test post afterward:
  python testmcp.py --clean
"""

import os, sys, argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from atlas.models import BlogPost, User


def test_create():
    db_path = settings.DATABASES["default"]["NAME"]
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    print(f"Database size: {os.path.getsize(db_path):,} bytes\n")

    author = User.objects.filter(role="superadmin").first()
    if not author:
        print("ERROR: No superadmin user exists. Create one first.")
        return None

    title = "Test Post — Debugging MCP Blog Creation"
    slug = _unique_slug(title)

    post = BlogPost.objects.create(
        title=title,
        slug=slug,
        subtitle="Automated test post",
        category="capital-strategy",
        excerpt="Quick test to verify MCP blog creation works end-to-end.",
        content="<p>If you can read this on the blog, the write pipeline works.</p>",
        read_time=1,
        is_published=True,
        published_at=timezone.now(),
        author=author,
    )

    print("SUCCESS — post created")
    print(f"  ID     : {post.id}")
    print(f"  Slug   : {post.slug}")
    print(f"  Author : {post.author.email}")
    return post


def _unique_slug(title):
    base = slugify(title)[:350]
    slug = base
    c = 1
    while BlogPost.objects.filter(slug=slug).exists():
        slug = f"{base}-{c}"
        c += 1
    return slug


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Delete test post after creation")
    args = parser.parse_args()

    print("=== MCP Blog Write Test ===\n")
    try:
        post = test_create()
        if post and args.clean:
            post.delete()
            print("\nTest post deleted (--clean).")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
