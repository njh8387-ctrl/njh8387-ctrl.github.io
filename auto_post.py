#!/usr/bin/env python3
"""
블로그 자동 포스트 생성기
- Gemini API로 우리 봇 코드/경험 기반 글 작성
- Hugo 빌드 → GitHub Pages 자동 배포
- 크론: 2일마다 실행
"""

import os
import sys
import json
import random
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# === 설정 ===
BLOG_DIR = Path("/home/administrator/.openclaw/workspace/algo-trading-blog")
POSTS_DIR = BLOG_DIR / "content" / "posts"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCBlfPYPYiu63JKjPjgvYnkHuVNM8wc-Os")
GEMINI_MODEL = "gemini-2.5-flash-lite"
HUGO_BIN = os.path.expanduser("~/bin/hugo")

# === 우리 프로그램 소스 (참고용) ===
SOURCE_FILES = {
    "v23_maker": "/home/administrator/.openclaw/workspace/deribit_trade_bot/v23_maker.py",
    "us_momentum_bot": "/home/administrator/.openclaw/workspace/kis_stock/us_momentum_bot.py",
    "rug_hunter": "/home/administrator/.openclaw/workspace/rug-hunter/src/index.ts",
}

# === 주제 풀 (실제 경험 기반) ===
TOPIC_POOL = [
    {
        "title_hint": "EMA Crossover Strategy",
        "source": "v23_maker",
        "focus": "EMA10/EMA50 크로스오버 + MACD 필터를 사용한 BTC 퍼페추얼 트레이딩",
        "snippet_lines": (300, 380),
    },
    {
        "title_hint": "Choppy Market Detection",
        "source": "v23_maker",
        "focus": "횡보장 감지 로직 (CHOP_THRESHOLD, 10분 모멘텀) — 왜 필요한지, 구현법",
        "snippet_lines": (40, 55),
    },
    {
        "title_hint": "Trailing Stop Loss",
        "source": "v23_maker",
        "focus": "트레일링 스톱 구현 — 고점 대비 하락률로 익절하는 전략",
        "snippet_lines": (130, 180),
    },
    {
        "title_hint": "Pre-market Momentum Scanner",
        "source": "us_momentum_bot",
        "focus": "미국 장전 급등주 스캔 — Alpaca API + 뉴스 스코어링",
        "snippet_lines": (700, 800),
    },
    {
        "title_hint": "Position Recovery After Crash",
        "source": "us_momentum_bot",
        "focus": "봇 크래시 후 브로커 싱크로 포지션 자동 복구하는 로직",
        "snippet_lines": (1254, 1310),
    },
    {
        "title_hint": "Daily Loss Limit & Auto-Halt",
        "source": "us_momentum_bot",
        "focus": "일일 손실 한도 초과 시 자동 거래 중단 + PnL 회복 시 재개",
        "snippet_lines": (1100, 1160),
    },
    {
        "title_hint": "Rug Pull Detection with AI",
        "source": "rug_hunter",
        "focus": "온체인 데이터로 러그풀 토큰 탐지 — 실시간 모니터링 시스템",
        "snippet_lines": (1, 80),
    },
    {
        "title_hint": "API Rate Limiting in Trading Bots",
        "source": "v23_maker",
        "focus": "거래소 API 레이트 리밋 관리 — 콜 최소화, 에러 핸들링",
        "snippet_lines": (200, 260),
    },
    {
        "title_hint": "Building a Token Refresh System",
        "source": "us_momentum_bot",
        "focus": "한국투자증권 OAuth 토큰 자동 갱신 시스템",
        "snippet_lines": (400, 470),
    },
    {
        "title_hint": "From $86 to $100: Surviving Drawdowns",
        "source": "v23_maker",
        "focus": "소액으로 시작한 트레이딩 봇의 드로다운 생존기 — 실전 에퀴티 곡선",
        "snippet_lines": (1, 50),
    },
    {
        "title_hint": "Real-time News Scoring for Stock Picks",
        "source": "us_momentum_bot",
        "focus": "뉴스 헤드라인 기반 종목 스코어링 시스템 구현",
        "snippet_lines": (800, 900),
    },
    {
        "title_hint": "Running 5 Trading Bots on a Single Server",
        "source": "v23_maker",
        "focus": "WSL2에서 5개 봇 동시 운영 — 메모리 관리, 크래시 복구, 모니터링",
        "snippet_lines": (1, 30),
    },
]


def get_existing_posts():
    """기존 포스트 제목 목록."""
    posts = []
    for f in POSTS_DIR.glob("*.md"):
        with open(f) as fh:
            for line in fh:
                if line.startswith("title:"):
                    posts.append(line.split('"')[1] if '"' in line else line.split(":")[1].strip())
                    break
    return posts


def read_source_snippet(source_key, lines):
    """소스 코드 스니펫 읽기."""
    filepath = SOURCE_FILES.get(source_key)
    if not filepath or not os.path.exists(filepath):
        return "(source not available)"
    
    start, end = lines
    result = []
    with open(filepath) as f:
        for i, line in enumerate(f, 1):
            if start <= i <= end:
                result.append(line.rstrip())
            if i > end:
                break
    return "\n".join(result)


def generate_post(topic, existing_titles):
    """Gemini API로 포스트 생성."""
    snippet = read_source_snippet(topic["source"], topic["snippet_lines"])
    
    prompt = f"""You are a technical blogger who builds real trading bots.
Write a blog post about: {topic['focus']}

Title hint: {topic['title_hint']} (make it catchy, don't use this exact title)

Here's actual code from our bot for reference:
```python
{snippet[:3000]}
```

Requirements:
- 1500-2500 words
- Include code snippets (simplified from the real code above)
- Share real lessons learned (what went wrong, what worked)
- Conversational tone, like explaining to a friend
- Include a "Key Takeaways" section at the end
- Don't mention specific API keys, secrets, or account numbers
- Write in English

Existing posts (avoid overlap): {', '.join(existing_titles)}

Output ONLY the blog post content in markdown (no frontmatter, I'll add that).
Start with the first paragraph directly."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 4096,
        }
    }
    
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text


def create_slug(title):
    """제목에서 slug 생성."""
    slug = title.lower()
    for ch in ['"', "'", ",", ".", "!", "?", ":", ";", "(", ")", "$", "%", "+", "#"]:
        slug = slug.replace(ch, "")
    slug = slug.replace(" ", "-").replace("--", "-").strip("-")
    return slug[:60]


def save_post(title, content, tags):
    """마크다운 파일 저장."""
    now = datetime.now()
    slug = create_slug(title)
    filename = f"{slug}.md"
    filepath = POSTS_DIR / filename
    
    frontmatter = f"""---
title: "{title}"
date: {now.strftime('%Y-%m-%dT%H:%M:%S+09:00')}
draft: false
tags: {json.dumps(tags)}
description: "Real lessons from building automated trading bots"
---

"""
    with open(filepath, "w") as f:
        f.write(frontmatter + content)
    
    print(f"✅ Post saved: {filepath}")
    return filepath


def build_and_deploy():
    """Hugo 빌드 + git push."""
    os.chdir(BLOG_DIR)
    
    # Hugo 빌드
    result = subprocess.run([HUGO_BIN], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Hugo build failed: {result.stderr}")
        return False
    print(f"✅ Hugo build OK")
    
    # Git push
    subprocess.run(["git", "add", "."], capture_output=True)
    msg = f"Auto-post: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    subprocess.run(["git", "commit", "-m", msg], capture_output=True)
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode != 0:
        # Try master
        result = subprocess.run(["git", "push", "origin", "master"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Deployed to GitHub Pages")
        return True
    else:
        print(f"❌ Git push failed: {result.stderr}")
        return False


def main():
    existing = get_existing_posts()
    print(f"📝 Existing posts: {len(existing)}")
    
    # 이미 쓴 주제 피하고 랜덤 선택
    available = [t for t in TOPIC_POOL if t["title_hint"] not in [e for e in existing]]
    if not available:
        available = TOPIC_POOL  # 전부 소진되면 리셋
    
    topic = random.choice(available)
    print(f"🎯 Topic: {topic['title_hint']}")
    print(f"📂 Source: {topic['source']}")
    
    # Gemini로 글 생성
    print("✍️ Generating with Gemini...")
    content = generate_post(topic, existing)
    
    # 제목 추출 (첫 줄이 # 이면 그걸 사용)
    lines = content.strip().split("\n")
    title = topic["title_hint"]
    if lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
        content = "\n".join(lines[1:]).strip()
    
    # 태그 결정
    tag_map = {
        "v23_maker": ["trading-bot", "crypto", "bitcoin", "deribit", "python"],
        "us_momentum_bot": ["stocks", "momentum", "trading-bot", "python", "us-market"],
        "rug_hunter": ["crypto", "defi", "security", "rug-pull", "typescript"],
    }
    tags = tag_map.get(topic["source"], ["trading", "python", "automation"])
    
    # 저장
    save_post(title, content, tags)
    
    # 빌드 & 배포
    build_and_deploy()
    
    print(f"\n🎉 Done! New post about '{title}' is live.")


if __name__ == "__main__":
    main()
