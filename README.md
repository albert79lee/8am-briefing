# 8시 브리핑 — 매일 아침 자동 뉴스 요약 앱

## 준비물
- GitHub 계정 (무료, github.com 에서 가입)
- Anthropic API 키 (console.anthropic.com 에서 발급, 유료 종량제)

## 설정 순서

### 1. GitHub 저장소 만들기
1. github.com 가입 후 로그인
2. 우측 상단 `+` → `New repository` 클릭
3. Repository name: `8am-briefing` (원하는 이름으로 가능)
4. `Public` 선택 (GitHub Pages 무료 사용을 위해)
5. `Create repository` 클릭

### 2. 이 파일들 업로드
1. 방금 만든 저장소 페이지에서 `Add file` → `Upload files` 클릭
2. 압축 풀린 이 폴더 안의 모든 파일/폴더를 통째로 끌어다 놓기
   (`.github` 폴더도 반드시 포함되어야 자동 실행이 됩니다)
3. `Commit changes` 클릭

### 3. API 키 등록 (비밀 저장)
1. 저장소 페이지에서 `Settings` → 왼쪽 메뉴 `Secrets and variables` → `Actions`
2. `New repository secret` 클릭
3. Name: `ANTHROPIC_API_KEY`
4. Value: 발급받은 API 키 붙여넣기
5. `Add secret` 클릭

### 4. GitHub Pages 켜기 (웹앱 주소 만들기)
1. `Settings` → 왼쪽 메뉴 `Pages`
2. `Source`를 `Deploy from a branch`로 설정
3. Branch: `main`, 폴더: `/ (root)` 선택 후 `Save`
4. 1~2분 뒤 상단에 `https://<사용자아이디>.github.io/8am-briefing/` 주소가 생성됨

### 5. 첫 브리핑 수동 실행해보기 (선택)
1. 저장소 상단 `Actions` 탭 클릭
2. `Daily 8AM Briefing` 워크플로우 선택
3. `Run workflow` 버튼으로 지금 바로 한 번 실행 가능
4. 성공하면 `data/latest.json` 파일이 최신 뉴스로 업데이트됨

이후로는 **매일 한국시간 오전 8시에 자동으로 실행**되어 `data/latest.json`이 갱신됩니다.

### 6. 폰 홈 화면에 추가하기
1. 폰의 브라우저(iPhone: Safari / Android: Chrome)로 4번에서 만든 주소 접속
2. **iPhone**: 하단 공유 버튼 → `홈 화면에 추가`
3. **Android**: 우측 상단 메뉴(⋮) → `홈 화면에 추가` 또는 `앱 설치`
4. 홈 화면에 생긴 아이콘을 누르면 앱처럼 열림

## 참고
- 매일 발생하는 비용은 Anthropic API 호출 1회분(웹 검색 포함)뿐이며, GitHub Actions와 Pages는 개인 사용 범위에서 무료입니다.
- 스케줄 시간을 바꾸고 싶으면 `.github/workflows/daily-briefing.yml` 안의
  `cron: "0 23 * * *"` 를 수정하세요 (UTC 기준, KST = UTC+9).
- 카테고리나 기사 개수를 바꾸고 싶으면 `fetch_news.py` 안의 `PROMPT`를 수정하세요.
