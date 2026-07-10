"""
매일 새벽 실행되어 주요 뉴스를 검색·요약하고 data/latest.json에 저장하는 스크립트.
GitHub Actions가 매일 08:00(KST)에 이 스크립트를 자동으로 실행합니다.
"""
import os
import json
import datetime
import re
import requests

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"

CATEGORIES = ["정치", "사회", "경제", "반도체", "해외"]

PROMPT = """지금은 한국 시간 기준 오늘 아침이야. 아래 5개 카테고리 각각에서 최신 주요 뉴스를 2건씩,
총 10건을 웹 검색으로 확인한 뒤 한국어로 정리해줘.

카테고리: 정치, 사회, 경제(경제·주식), 반도체(반도체·IT), 해외

각 기사마다 다음을 포함해야 해:
- 실제로 검색해서 확인한, 오늘 또는 최근 1~2일 내의 신뢰할 수 있는 언론사 기사
- 원문 기사의 실제 URL (검색 결과에 나온 정확한 링크)
- 헤드라인 1줄
- 3문장 내외의 한국어 요약 (기사 내용을 바탕으로, 문장을 그대로 베끼지 말고 자연스럽게 풀어서)
- 핵심 포인트 2개 (짧은 불릿)
- 언론사명
- 짧은 한 줄 코멘트(foot)

아래 JSON 형식으로만 응답해. 다른 설명이나 마크다운 코드블록 없이 순수 JSON 배열만 출력해:

[
  {
    "category": "정치",
    "headline": "...",
    "summary": "...",
    "points": ["...", "..."],
    "source": "...",
    "url": "https://...",
    "foot": "..."
  }
]
"""


def call_claude():
    api_key = os.environ["ANTHROPIC_API_KEY"]
    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 6000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": PROMPT}],
        },
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    text_parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    return "\n".join(text_parts)


def extract_json(text):
    # ```json ... ``` 코드블록이 섞여 나올 경우 대비
    text = re.sub(r"```json|```", "", text)
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("응답에서 JSON 배열을 찾지 못했습니다:\n" + text[:500])
    return json.loads(text[start:end])


def main():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)

    raw_text = call_claude()
    articles = extract_json(raw_text)

    # 카테고리 값 정규화
    for a in articles:
        cat = a.get("category", "")
        if cat not in CATEGORIES:
            for c in CATEGORIES:
                if c in cat:
                    a["category"] = c
                    break

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
