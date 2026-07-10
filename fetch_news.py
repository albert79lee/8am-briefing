"""
무료 RSS 피드 + 기사 페이지의 메타 요약(meta description)으로
매일 아침 주요 뉴스를 헤드라인+요약과 함께 모으는 스크립트.
Anthropic API 등 유료 API를 전혀 쓰지 않아 추가 비용이 들지 않습니다.
"""
import json
import datetime
import html
import re
import xml.etree.ElementTree as ET
import urllib.request

FEEDS = {
    "정치": "https://www.hankyung.com/feed/politics",
    "사회": "https://www.hankyung.com/feed/society",
    "경제": "https://www.hankyung.com/feed/economy",
    "반도체": "https://www.hankyung.com/feed/it",
    "해외": "https://www.hankyung.com/feed/international",
}

ITEMS_PER_CATEGORY = 2
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BriefingBot/1.0)"}


def fetch_feed(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if title and link:
            items.append({"headline": title, "url": link, "pub_date": pub_date})
    return items


def fetch_summary(article_url):
    """기사 페이지의 meta description(언론사가 직접 작성한 요약)을 가져온다."""
    try:
        req = urllib.request.Request(article_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_text = resp.read().decode("utf-8", errors="ignore")
        pattern = (
            r'<meta[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])'
            r'[^>]+content=["\']([^"\']+)["\']'
        )
        m = re.search(pattern, html_text, re.IGNORECASE)
        if not m:
            pattern2 = (
                r'<meta[^>]+content=["\']([^"\']+)["\']'
                r'[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])'
            )
            m = re.search(pattern2, html_text, re.IGNORECASE)
        if m:
            return html.unescape(m.group(1)).strip()
    except Exception as e:
        print(f"요약 추출 실패 ({article_url}): {e}")
    return ""


def main():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)

    articles = []
    for category, url in FEEDS.items():
        try:
            items = fetch_feed(url)[:ITEMS_PER_CATEGORY]
        except Exception as e:
            print(f"{category} 피드를 가져오지 못했습니다: {e}")
            items = []
        for it in items:
            summary = fetch_summary(it["url"])
            articles.append({
                "category": category,
                "headline": it["headline"],
                "summary": summary,
                "points": [],
                "source": "한국경제",
                "url": it["url"],
                "foot": it["pub_date"],
            })

    output = {
        "date": now.strftime("%Y년 %m월 %d일 ") + ["월", "화", "수", "목", "금", "토", "일"][now.weekday()] + "요일",
        "generated_at": now.isoformat(),
        "articles": articles,
    }

    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {len(articles)}건")


if __name__ == "__main__":
    main()
