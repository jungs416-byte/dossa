import requests
from bs4 import BeautifulSoup
import os

# 텔레그램 설정 (깃허브 Secrets에서 불러옴)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
URL = "http://corearoadbike.com/board/board.php?t_id=Menu31Top6"
DB_FILE = "last_id.txt"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.get(url, params=params)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def check_dossa():
    try:
        # 1. 도싸 페이지 접속 (한글 깨짐 방지를 위해 euc-kr 설정)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 2. 마지막으로 확인했던 글 번호 읽기
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                last_id = f.read().strip()
        else:
            last_id = "0"

        # 3. 게시글 목록 행(tr) 가져오기
        articles = soup.select("tr.bg0, tr.bg1")
        
        new_last_id = last_id
        found_items = []

        for post in articles:
            # 글 번호(ID) 추출
            no_elem = post.select_one(".list_no")
            if not no_elem: continue
            post_id = no_elem.get_text().strip()
            
            # 숫자가 아닌(공지사항 등) 글은 건너뜀
            if not post_id.isdigit(): continue
            
            # 이미 본 글이면 중단
            if int(post_id) <= int(last_id): break 
            
            # 가장 최신 글 번호를 기억
            if new_last_id == last_id:
                new_last_id = post_id

            # 제목과 링크 추출
            title_elem = post.select_one(".list_title a")
            if not title_elem: continue
            
            title = title_elem.get_text().strip()
            # 링크 주소 생성
            raw_link = title_elem['href']
            link = "https://corearoadbike.com/board" + raw_link.lstrip(".")

            # ⭐ 키워드 필터링 (레드 AND 165)
            if "165" in title:
                found_items.append(f"🚲 도싸 신규 매물!\n\n제목: {title}\n링크: {link}")

        # 4. 새 매물이 있으면 텔레그램 발송 및 파일 업데이트
        if found_items:
            for item in reversed(found_items): # 옛날 글부터 순서대로
                send_telegram(item)
            
            with open(DB_FILE, "w") as f:
                f.write(new_last_id)
            print(f"{len(found_items)}개의 새 매물을 찾았습니다.")
        else:
            print("새로운 매물이 없습니다.")

    except Exception as e:
        print(f"스크립트 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    check_dossa()
