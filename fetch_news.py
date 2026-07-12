"""
무료 RSS 피드 + 기사 페이지의 메타 요약(meta description) + 무료 시세 API로
매일 아침 주요 뉴스와 증시 현황을 모으는 스크립트.
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
    "주식": "https://www.hankyung.com/feed/finance",
}

MARKET_SYMBOLS = {
    "코스피": "^KS11",
    "코스닥": "^KQ11",
    "원/달러": "KRW=X",
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


def fetch_market():
    """Yahoo Finance 무료 조회 API로 코스피/코스닥/환율 시세를 가져온다."""
    market = {}
    for name, symbol in MARKET_SYMBOLS.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice")
            prev = meta.get("previousClose") or meta.get("chartPreviousClose")
            change = round(price - prev, 2) if price is not None and prev else None
            pct = round((change / prev) * 100, 2) if change is not None and prev else None
            market[name] = {
                "price": round(price, 2) if price is not None else None,
                "change": change,
                "pct": pct,
            }
        except Exception as e:
            print(f"{name} 시세를 가져오지 못했습니다: {e}")
            market[name] = None
    return market


def describe_move(pct):
    """등락률을 자연스러운 한국어 표현으로 변환한다."""
    if pct is None:
        return None
    if pct >= 2:
        return "큰 폭으로 상승했어요"
    if pct >= 0.5:
        return "상승했어요"
    if pct > -0.5:
        return "보합 수준을 유지했어요"
    if pct > -2:
        return "하락했어요"
    return "큰 폭으로 하락했어요"


def build_market_commentary(market):
    """실제 지수 등락 데이터를 바탕으로 오늘의 시황 요약 문장을 자동 생성한다.
    AI를 쓰지 않고 숫자 기반 규칙으로 문장을 조립하므로 비용이 들지 않는다."""
    kospi = market.get("코스피")
    kosdaq = market.get("코스닥")
    fx = market.get("원/달러")

    sentences = []

    if kospi and kospi.get("pct") is not None:
        arrow = "▲" if kospi["pct"] >= 0 else "▼"
        sentences.append(
            f"코스피는 전일 대비 {arrow}{abs(kospi['pct'])}% {describe_move(kospi['pct'])} "
            f"({kospi['price']:,}선)."
        )
    if kosdaq and kosdaq.get("pct") is not None:
        arrow = "▲" if kosdaq["pct"] >= 0 else "▼"
        sentences.append(
            f"코스닥은 {arrow}{abs(kosdaq['pct'])}% {describe_move(kosdaq['pct'])} "
            f"({kosdaq['price']:,}선)."
        )
    if fx and fx.get("pct") is not None:
        direction = "상승" if fx["pct"] >= 0 else "하락"
        sentences.append(
            f"원/달러 환율은 {abs(fx['pct'])}% {direction}한 {fx['price']:,}원에 거래되고 있어요."
        )

    if not sentences:
        return "오늘의 시황 데이터를 아직 불러오지 못했어요."

    if kospi and kosdaq and kospi.get("pct") is not None and kosdaq.get("pct") is not None:
        if kospi["pct"] >= 0.5 and kosdaq["pct"] >= 0.5:
            sentences.append("코스피·코스닥이 동반 강세를 보이며 투자심리가 개선된 모습이에요.")
        elif kospi["pct"] <= -0.5 and kosdaq["pct"] <= -0.5:
            sentences.append("코스피·코스닥이 동반 약세를 보이며 투자심리가 위축된 모습이에요.")

    return " ".join(sentences)


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

    market = fetch_market()
    market_commentary = build_market_commentary(market)

    output = {
        "date": now.strftime("%Y년 %m월 %d일 ") + ["월", "화", "수", "목", "금", "토", "일"][now.weekday()] + "요일",
        "generated_at": now.isoformat(),
        "market": market,
        "market_commentary": market_commentary,
        "articles": articles,
    }

    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {len(articles)}건, 시세 {len([m for m in market.values() if m])}건")


if __name__ == "__main__":
    main()
