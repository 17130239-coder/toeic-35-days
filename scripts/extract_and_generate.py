#!/usr/bin/env python3
"""
Comprehensive, High-Precision Extractor and Quiz Generator
for 35-Days Vocabulary Course & Wayground Clone
"""
import os
import re
import json
import random
from bs4 import BeautifulSoup
from image_catalog import get_word_image, QUIZIZZ_CORRECT_MEMES, QUIZIZZ_WRONG_MEMES

VN_CHARS = set('àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ')
IPA_CHARS = set('ˈˌəɪʊɒæɑːɔːɜːʌθðʃʒŋɡ:')

def clean_text(s):
    if not s:
        return ""
    s = re.sub(r'[\r\t\xa0]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def has_vietnamese(s):
    return any(c in VN_CHARS for c in s)

def is_true_ipa(s):
    inner = s.strip('/ \t\xa0')
    if not inner:
        return False
    # Check if contains IPA specific symbols
    if any(c in inner for c in IPA_CHARS):
        # Exclude English words that accidentally got inside slashes
        bad_words = {'effort', 'employee', 'assume', 'go', 'take', 'put', 'vital', 'has', 'be', 'crucial', 'force', 'regular'}
        words = set(re.findall(r'[a-zA-Z]+', inner.lower()))
        if words & bad_words:
            return False
        return True
    return False

def extract_examples(body):
    examples = []
    matches = list(re.finditer(r'(?:E\.g|Ex|Ví dụ|Eg)\s*:\s*', body, re.IGNORECASE))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end].strip()
        
        # In chunk, find parentheses translation
        m_paren = re.search(r'\(([^)]+)\)', chunk, re.DOTALL)
        if m_paren:
            en_raw = chunk[:m_paren.start()]
            vi_raw = m_paren.group(1)
        elif ':' in chunk:
            c_idx = chunk.find(':')
            after = chunk[c_idx+1:].strip()
            if has_vietnamese(after):
                en_raw = chunk[:c_idx]
                vi_raw = after
            else:
                first_nl = chunk.find('\n\n')
                en_raw = chunk[:first_nl] if first_nl != -1 else chunk
                vi_raw = ''
        else:
            first_nl = chunk.find('\n\n')
            en_raw = chunk[:first_nl] if first_nl != -1 else chunk
            vi_raw = ''
            
        en = clean_text(' '.join([l.strip() for l in en_raw.split('\n') if l.strip()])).strip(' -:')
        vi = clean_text(' '.join([l.strip() for l in vi_raw.split('\n') if l.strip()])).strip(' -:')
        
        # Clean punctuation spacing: "abruptly ." -> "abruptly."
        en = re.sub(r'\s+([,\.\?!;:])', r'\1', en)
        vi = re.sub(r'\s+([,\.\?!;:])', r'\1', vi)
        
        # Clean split suffixes caused by HTML formatting tags: "lower ed" -> "lowered"
        en = re.sub(r'\b(\w+)\s+(ed|ing|s|ly|d|es)\b', r'\1\2', en)
        
        if en:
            examples.append({'en': en, 'vi': vi})
    return examples

VOCAB_SPECIFIC_OVERRIDES = {
    (1, 4): {"term": "Be severely damaged", "pos": "(phrase)", "phonetic": "/biː sɪˈvɪrli ˈdæmɪdʒd/", "meaning": "Bị thiệt hại một cách nghiêm trọng"},
    (3, 4): {"term": "Be exchanged for S.TH", "pos": "(phrase)", "phonetic": "/biː ɪksˈtʃeɪndʒd fɔːr/", "meaning": "Được trao đổi lấy cái gì"},
    (4, 1): {"term": "Have/ Has/ Be yet to do S.TH", "pos": "(grammar pattern)", "phonetic": "/hæv jɛt tuː duː/", "meaning": "Chưa làm gì (vẫn chưa diễn ra)"},
    (5, 4): {"term": "Price quote", "pos": "(n.phrase)", "phonetic": "/praɪs kwəʊt/", "meaning": "Bảng báo giá"},
    (6, 3): {"term": "Linking Verbs (Become / Remain)", "pos": "(grammar)", "phonetic": "/bɪˈkʌm/, /rɪˈmeɪn/", "meaning": "Động từ nối + Tính từ (Trở nên, trở thành / Duy trì)"},
    (7, 2): {"term": "Salary increase", "pos": "(n.phrase)", "phonetic": "/ˈsæləri ɪnˈkriːs/", "meaning": "Sự tăng lương"},
    (8, 2): {"term": "Mergers and Acquisitions (M&A)", "pos": "(n.phrase)", "phonetic": "/ˈmɜːrdʒərz ənd ˌækwɪˈzɪʃnz/", "meaning": "Sáp nhập và thâu tóm doanh nghiệp"},
    (9, 6): {"term": "Conveniently located", "pos": "(adj.phrase)", "phonetic": "/kənˈviːniəntli ˈləʊkeɪtɪd/", "meaning": "Tọa lạc ở vị trí thuận tiện"},
    (10, 4): {"term": "Exceed (shareholder expectations)", "pos": "(v)", "phonetic": "/ɪkˈsiːd/", "meaning": "Vượt quá kỳ vọng của cổ đông"},
    (10, 6): {"term": "Highly / Widely regarded", "pos": "(adj.phrase)", "phonetic": "/ˈhaɪli rɪˈɡɑːrdɪd/", "meaning": "Được đánh giá cao, được kính trọng"},
    (12, 2): {"term": "S.O be likely to do S.TH", "pos": "(phrase)", "phonetic": "/bi ˈlaɪkli tuː duː/", "meaning": "Ai đó rất có thể / có khả năng làm gì"},
    (12, 5): {"term": "In honor of S.O/S.TH", "pos": "(prep.phrase)", "phonetic": "/ɪn ˈɑːnər əv/", "meaning": "Nhằm tôn vinh, tưởng niệm ai/cái gì"},
    (13, 2): {"meaning": "Dịch vụ nổi bật, xuất sắc"},
    (13, 5): {"term": "Prepositions & Adverbs + Numbers", "pos": "(grammar)", "phonetic": "/fɔːr/, /wɪˈðɪn/, /ˈoʊvər/", "meaning": "Giới từ / trạng từ đi kèm số lượng/thời gian (Trong suốt, Trong vòng, Hơn, Lên đến...)"},
    (14, 1): {"term": "Lower", "pos": "(adj / v)", "phonetic": "/ˈləʊər/", "meaning": "Thấp hơn (adj) / Hạ thấp, giảm bớt (v)"},
    (14, 2): {"term": "Reach peak / At peak", "pos": "(collocation)", "phonetic": "/riːtʃ piːk/", "meaning": "Đạt tới đỉnh điểm / Ở mức đỉnh cao"},
    (15, 4): {"term": "Take advantage of S.TH", "pos": "(idiom)", "phonetic": "/teɪk ədˈvæntɪdʒ əv/", "meaning": "Tận dụng, khai thác lợi thế của cái gì"},
    (15, 5): {"term": "Come/Go/Take/Put into effect", "pos": "(phrase)", "phonetic": "/ɪntuː ɪˈfekt/", "meaning": "Có hiệu lực thi hành, đi vào áp dụng"},
    (16, 1): {"term": "Lack of S.TH", "pos": "(collocation)", "phonetic": "/læk əv/", "examples": [{"en": "The proposal was delayed due to a lack of funding.", "vi": "Bản đề xuất đã bị trì hoãn do thiếu kinh phí."}]},
    (16, 3): {"term": "Satisfactory", "pos": "(adj)", "examples": [{"en": "Tommy failed to provide satisfactory answers to the reporters' questions.", "vi": "Tommy không thể đưa ra được câu trả lời thỏa đáng cho các câu hỏi của phóng viên."}]},
    (18, 5): {"term": "Keep S.O informed / posted", "pos": "(collocation)", "phonetic": "/kiːp ɪnˈfɔːrmd/", "meaning": "Cập nhật thông tin mới nhất cho ai"},
    (19, 1): {"term": "Retail sales", "pos": "(n.phrase)", "phonetic": "/ˈriːteɪl seɪlz/", "meaning": "Doanh số bán lẻ"},
    (22, 2): {"term": "Worker / Employee productivity", "pos": "(n.phrase)", "phonetic": "/ˌprɑːdʌkˈtɪvəti/", "meaning": "Năng suất làm việc của nhân viên"},
    (22, 5): {"term": "Participate in", "pos": "(v.phrase)", "phonetic": "/pɑːrˈtɪsɪpeɪt ɪn/", "meaning": "Tham gia vào cái gì"},
    (23, 1): {"term": "On behalf of S.O", "pos": "(prep.phrase)", "phonetic": "/ɑːn bɪˈhæf əv/", "meaning": "Thay mặt, đại diện cho ai", "examples": [{"en": "On behalf of the company, I would like to thank you for your dedication.", "vi": "Thay mặt công ty, tôi xin chân thành cảm ơn sự cống hiến của quý vị."}]},
    (24, 2): {"term": "Be/come equipped with S.TH", "pos": "(phrase)", "phonetic": "/bi ɪˈkwɪpt wɪð/", "meaning": "Được trang bị với cái gì"},
    (0, 7): {"phonetic": "/rɪˈnjuːəl/"},
    (2, 5): {"phonetic": "/fɪl aʊt/"},
    (11, 2): {"phonetic": "/kənˈvɪnsɪŋli/"},
    (21, 2): {"phonetic": "/ˈpɜːrmənənt/"},
    (21, 3): {"phonetic": "/ˌɪnspəˈreɪʃn sɔːrs/"},
    (21, 4): {"phonetic": "/ˈɪnkʌm/"},
    (21, 5): {"phonetic": "/ɪˈkwɪpmənt məˈʃiːnəri ˌmɑːdərnəˈzeɪʃn/"},
    (24, 4): {"phonetic": "/strəˈtiːdʒɪkli/"},
    (25, 1): {"phonetic": "/ɪn ən əˈtempt/"},
    (25, 2): {"phonetic": "/stæf məˈræl/"},
    (26, 4): {"phonetic": "/reɪz əˈwernəs/"},
    (28, 6): {"phonetic": "/ˈdrɔːɪŋ/"},
    (30, 4): {"phonetic": "/ˌdɑːmɪˈneɪʃn/"},
    (32, 5): {"phonetic": "/ɪnˈsentɪv/"},
    (34, 1): {"phonetic": "/rɪˈfreɪn/"},
    (35, 6): {"phonetic": "/səˈspend/"},
    (30, 5): {"term": "Interfere with", "pos": "(v.phrase)", "phonetic": "/ˌɪntərˈfɪr wɪð/", "meaning": "Can thiệp, gây cản trở chuyện gì"}
}

def extract_all():
    html_path = '/Users/andynguyen/workspace/35-days/data.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    items = soup.find_all('li', class_=lambda c: c and 'tfGBod' in c)
    print(f"Total Google Classroom items found: {len(items)}")

    days_data = []

    pos_pat = re.compile(r'\(\s*(?:n\.phrase|n\.|n|v\.|v|adj\.|adj|adv\.|adv|v/n|n/v|adj/n|prep\.|prep|conj\.|conj|phrase|idiom|collocation)\s*\)', re.IGNORECASE)

    for item in items:
        title_el = item.find('span', class_=lambda c: c and 'Vu2fZd' in c)
        raw_title = title_el.get_text(strip=True) if title_el else ""
        
        m_day = re.search(r'\bDAY\s*(\d+)\b', raw_title, re.IGNORECASE)
        if not m_day:
            continue
        day_num = int(m_day.group(1))

        # Dates
        due_el = item.find('span', string=re.compile(r'Due\s+', re.I))
        due_date = due_el.get_text(strip=True) if due_el else ""
        
        posted_el = item.find('span', string=re.compile(r'Posted\s+', re.I))
        posted_date = posted_el.get_text(strip=True) if posted_el else ""

        # Content container
        bq = item.find('div', class_='bqKF7d')
        raw_html = str(bq) if bq else ""
        
        # Replace <br> with newlines to preserve lines accurately
        clean_html = re.sub(r'<br\s*/?>', '\n', raw_html)
        full_text = BeautifulSoup(clean_html, 'html.parser').get_text('\n')

        # Links extraction
        wayground_links = []
        form_links = []
        drive_files = []

        for a in item.find_all('a'):
            href = a.get('href', '').strip()
            link_text = a.get_text(strip=True)
            if not href or href.startswith('#') or href.startswith('/u/0'):
                continue
            
            if 'wayground.com' in href:
                m_gc = re.search(r'gc=(\d+)', href)
                gc = m_gc.group(1) if m_gc else ""
                if href not in [w['url'] for w in wayground_links]:
                    wayground_links.append({'url': href, 'game_code': gc, 'text': link_text})
            elif 'forms.gle' in href or 'docs.google.com/forms' in href:
                if href not in [f['url'] for f in form_links]:
                    form_links.append({'url': href, 'text': link_text})
            elif 'drive.google.com' in href:
                file_type = 'file'
                lt_lower = link_text.lower()
                if '.mp3' in lt_lower or 'audio' in lt_lower:
                    file_type = 'audio'
                elif '.png' in lt_lower or '.jpg' in lt_lower or 'image' in lt_lower:
                    file_type = 'image'
                elif '.mp4' in lt_lower or 'video' in lt_lower:
                    file_type = 'video'
                clean_name = re.sub(r'(Audio|Image|Video)$', '', link_text).strip()
                if clean_name and not any(d['name'] == clean_name for d in drive_files):
                    drive_files.append({'name': clean_name, 'url': href, 'type': file_type})

        # Reminder [DẶN DÒ]
        dan_do = ""
        if '[DẶN DÒ]' in full_text:
            p_start = full_text.find('[DẶN DÒ]')
            m_next = re.search(r'(?:📚\s*DAY\s*\d+|📚\s*\[\s*DAY\s*\d+)', full_text)
            if m_next and m_next.start() > p_start:
                dan_do = clean_text(full_text[p_start:m_next.start()])
            else:
                m_num = re.search(r'\n1\.\s*[A-Za-z]', full_text)
                if m_num:
                    dan_do = clean_text(full_text[p_start:m_num.start()])
            dan_do = re.sub(r'\s*\n\s*\]', ']', dan_do)

        # Wayground info
        wg_info = {
            "urls": [w['url'] for w in wayground_links],
            "game_codes": [w['game_code'] for w in wayground_links if w['game_code']],
            "title": "",
            "target_days": [],
            "raw_text": "",
            "deadline": "",
            "reward": "TRẢ BÀI LỌT [TOP 3] HAI LẦN LIÊN TIẾP ĐƯỢC THƯỞNG 30K"
        }
        
        m_wg = re.search(r'(?:B\.\s*GAME QUIZIZZ[^\n]*|GAME QUIZIZZ[^\n]*)', full_text, re.IGNORECASE)
        if m_wg:
            wg_sub = full_text[m_wg.start():]
            wg_info["raw_text"] = wg_sub.strip()
            
            m_td = re.search(r'DAY\s*\[([0-9\s\+\,]+)\]', wg_sub, re.IGNORECASE)
            if m_td:
                wg_info["target_days"] = [int(n.strip()) for n in re.findall(r'\d+', m_td.group(1))]
            elif 'TÍNH TỪ' in wg_sub.upper():
                wg_info["target_days"] = [6, 7]
            else:
                m_single = re.search(r'DAY\s*(\d+)', wg_sub, re.IGNORECASE)
                if m_single:
                    wg_info["target_days"] = [int(m_single.group(1))]
                else:
                    wg_info["target_days"] = [day_num]
            
            first_line = wg_sub.split('\n')[0].strip()
            wg_info["title"] = first_line
            
            m_dl = re.search(r'HIỆU LỰC ĐẾN\s*([^\n\.]+)', wg_sub, re.IGNORECASE)
            if m_dl:
                wg_info["deadline"] = m_dl.group(1).strip()

        # Parse Vocabulary
        vocab_entries = []
        
        # Day 0: 11 exception nouns
        if day_num == 0:
            ul = bq.find('ul')
            if ul:
                lis = ul.find_all('li')
                for i, li in enumerate(lis):
                    li_text = clean_text(li.get_text())
                    m = re.match(r'^([A-Za-z\s\-]+)\s*(/[^:]+/)\s*(\([^\)]+\))\s*:\s*(.+)$', li_text)
                    if m:
                        vocab_entries.append({
                            "id": f"d0_w{i+1}",
                            "index": i+1,
                            "term": m.group(1).strip(),
                            "phonetic": m.group(2).split(',')[0].strip(),
                            "pos": m.group(3).strip(),
                            "meaning": m.group(4).strip(),
                            "synonyms": [],
                            "examples": [],
                            "raw_text": li_text
                        })

        if not vocab_entries:
            # find vocab boundary
            v_start = 0
            m_day_header = re.search(r'📚\s*(?:\[\s*)?DAY\s*\d+', full_text)
            if m_day_header:
                v_start = m_day_header.end()
            
            v_end = len(full_text)
            m_stop = re.search(r'(?:📝\s*BÀI TẬP|A\.\s*VIẾT CÂU|📍\s*VIẾT MỖI TỪ|📍\s*YÊU CẦU|HIỆN ĐÃ KẾT THÚC|B\.\s*GAME QUIZIZZ)', full_text[v_start:])
            if m_stop:
                v_end = v_start + m_stop.start()
                
            vocab_section = full_text[v_start:v_end].strip()
            
            parts = re.split(r'\n(?=\d+[\.\)]\s*[A-Za-z\u00C0-\u1EF9])', '\n' + vocab_section)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                m_num = re.match(r'^(\d+)[\.\)]\s*(.+)', part, re.DOTALL)
                if not m_num:
                    continue
                p_num = int(m_num.group(1))
                body = m_num.group(2).strip()
                lines = [clean_text(l) for l in body.split('\n') if clean_text(l)]
                if not lines:
                    continue
                
                first_line = lines[0]
                
                # Extract true phonetic of the main term (ONLY before synonyms or definition)
                cut_points = []
                for delim in ['\n(v)', '\n(n)', '\n(adj)', '\n(adv)', '\n(phrase)', '\n(v/n)', ' = ', ' =', '= ', '\n=', ' ~ ', ' ~', '~ ', '\n~', '><', '\n><', ': (v)', ': (n)', ': (adj)', ': (adv)']:
                    idx = body.find(delim)
                    if idx != -1:
                        cut_points.append(idx)

                col_m = re.search(r':\s*([a-zA-ZÀ-ỹ\s]+)', body)
                if col_m:
                    after = col_m.group(1)
                    if any(c in VN_CHARS for c in after):
                        cut_points.append(col_m.start())

                header_end = min(cut_points) if cut_points else len(body)
                header = body[:header_end]

                ipas = [f"/{m.strip('/ ')}/" for m in re.findall(r'/([^/\n]+)/', header)]
                clean_ipas = []
                for ipa in ipas:
                    ipa_clean = ipa.strip('/ ')
                    if not any(bad in ipa_clean.lower() for bad in ['n):', 'v):', 'adj):', 'adv):', 'chuyển phát', 'khiếu nại', 'by', 'bằng', 'over', 'to s.o']):
                        clean_ipas.append(f"/{ipa_clean}/")

                phonetic = clean_ipas[0] if clean_ipas else ""
                
                # POS
                pos_m = pos_pat.search(body)
                pos = pos_m.group(0).strip() if pos_m else ""
                
                # Term determination
                term = first_line
                if ipas and ipas[0] in first_line:
                    term = first_line[:first_line.find(ipas[0])].strip()
                elif pos and pos in first_line:
                    term = first_line[:first_line.find(pos)].strip()
                elif ':' in first_line and not has_vietnamese(first_line[:first_line.find(':')]):
                    term = first_line[:first_line.find(':')].strip()

                # Clean term
                term = re.sub(r'[\:\=\-\~]+$', '', term).strip()
                
                # Special refinements for terms with collocations on line 2
                if len(lines) > 1:
                    l2 = lines[1]
                    if l2 in ['to do S.TH', 'of S.TH', 'of S.O', 'of S.TH/S.O', 'from/by/on S.TH', 'for/of S.TH', 'with S.TH:', '+ Noun']:
                        term = f"{term} {l2.replace(':', '')}".strip()
                    elif term == 'Reach' and 'peak / At peak' in l2:
                        term = 'Reach peak / At peak'
                    elif term == 'Lack' and 'of S.TH' in l2:
                        term = 'Lack of S.TH'
                    elif term == 'Direct' and 'S.TH to S.O' in l2:
                        term = 'Direct S.TH to S.O'
                    elif term == 'On behalf' and 'of S.O' in l2:
                        term = 'On behalf of S.O'

                # Synonyms
                synonyms = []
                for m_syn in re.finditer(r'[\=\~]\s*([A-Za-z\s\-\']+?)(?:\s*/[^\n/]+/|\s*[\=\:\n\(]|\s*$)', body):
                    s_word = m_syn.group(1).strip()
                    if s_word and len(s_word) > 1 and s_word.lower() not in ['s.th', 's.o', 's.b', 'the', 'a', 'an', 'part', 'test']:
                        if s_word not in synonyms and not has_vietnamese(s_word):
                            synonyms.append(s_word)

                # Meaning
                meaning = ""
                colons = [m.start() for m in re.finditer(r':', body)]
                for c_pos in colons:
                    after_c = body[c_pos+1:].strip()
                    lines_after = [l.strip() for l in after_c.split('\n') if l.strip()]
                    if not lines_after:
                        continue
                    first_line = lines_after[0].split('=')[0].split('~')[0].strip()
                    first_line = re.sub(r'^\([a-z\./\s]+\)\s*:\s*', '', first_line, flags=re.I).strip()
                    before_c = body[max(0, c_pos-10):c_pos]
                    if 'hoặc' in before_c:
                        continue
                    if has_vietnamese(first_line):
                        meaning = clean_text(first_line)
                        break

                if not meaning:
                    for l in lines:
                        if has_vietnamese(l):
                            # clean punctuation
                            cleaned_l = re.sub(r'^[0-9\.\:\-\~]+\s*', '', l)
                            cleaned_l = re.sub(r'^[\(\[][^\)\]]+[\)\]]\s*', '', cleaned_l)
                            if cleaned_l:
                                meaning = clean_text(cleaned_l)
                                break

                # Clean meaning
                meaning = re.sub(r'(?:E\.g|Ex|Ví dụ|Eg)\s*:.*', '', meaning, flags=re.I).strip()
                meaning = re.sub(r'[\-\>\=\~\:\•\(\[\{\s]+$', '', meaning).strip()
                if term == 'Bias' and 'thiên vị ai/cái gì' in body:
                    meaning = 'Khuynh hướng, thiên hướng, tính thiên vị (n); Có khuynh hướng, thiên vị (v)'

                # Examples
                examples = extract_examples(body)

                entry = {
                    "id": f"d{day_num}_w{p_num}",
                    "index": p_num,
                    "term": term if term else first_line,
                    "phonetic": phonetic,
                    "pos": pos,
                    "meaning": meaning,
                    "synonyms": synonyms,
                    "examples": examples,
                    "raw_text": part
                }

                # Apply specific overrides for edge cases
                if (day_num, p_num) in VOCAB_SPECIFIC_OVERRIDES:
                    ov = VOCAB_SPECIFIC_OVERRIDES[(day_num, p_num)]
                    for k, v in ov.items():
                        entry[k] = v

                vocab_entries.append(entry)

        # Parse Exercise A cleanly
        # Parse Exercise A cleanly
        exercise_a = {
            "title": "VIẾT CÂU HOÀN CHỈNH",
            "form_url": form_links[0]['url'] if form_links else "",
            "raw_text": "",
            "questions": []
        }
        
        if 'VIẾT CÂU' in raw_html:
            s_idx = raw_html.find('VIẾT CÂU')
            e_idx = raw_html.find('B. GAME QUIZIZZ')
            if e_idx == -1: e_idx = raw_html.find('B. GAME QUIZIZZ')
            if e_idx == -1: e_idx = raw_html.find('B. GAME')
            if e_idx == -1: e_idx = raw_html.find('B. GAME')
            if e_idx == -1: e_idx = len(raw_html)
            sub = raw_html[s_idx:e_idx]

            matches = list(re.finditer(r'(?:<br\s*/?>|\n|\))\s*(?:<b>)?\s*(?:<br\s*/?>)?\s*(\d+)[\.\)]\s*(?:</b>)?', sub))
            for idx, match in enumerate(matches):
                q_num = int(match.group(1))
                start_pos = match.end()
                end_pos = matches[idx+1].start() if idx+1 < len(matches) else len(sub)
                q_chunk = sub[start_pos:end_pos]
                
                chunk_clean = re.sub(r'<u>\s*___\s*</u>', '___', q_chunk)
                lines_html = re.split(r'<br\s*/?>', chunk_clean)
                
                s_lines = []
                t_lines = []
                bank_tokens = []
                
                for lh in lines_html:
                    lh_txt = BeautifulSoup(lh, 'html.parser').get_text().replace('\xa0', ' ')
                    clean_l = clean_text(lh_txt)
                    if not clean_l or clean_l.startswith('=>'):
                        continue
                    if 'B. GAME' in clean_l or 'CƠ CẤU' in clean_l or 'TRẢ BÀI' in clean_l or 'forms.gle' in clean_l:
                        break
                        
                    if '___' in clean_l:
                        s_lines.append(clean_l)
                    elif has_vietnamese(clean_l):
                        t_lines.append(clean_l)
                    else:
                        toks = [t.strip() for t in re.split(r' {2,}|\t+', lh_txt) if t.strip()]
                        for t in toks:
                            if 'http' in t or 'wayground' in t or 'forms.gle' in t:
                                continue
                            c = re.sub(r'^[\[\]\(\)\.\,\;\:\s\d]+|[\[\]\(\)\.\,\;\:\s]+$', '', t).strip()
                            c = re.sub(r'[\[\]]', '', c).strip()
                            if c and len(c) > 1 and not has_vietnamese(c):
                                bank_tokens.append(c)

                sent = clean_text(' '.join(s_lines))
                sent = re.sub(r'___\s*\[\s*(\d+)\s*\]', r'___[\1]', sent)
                sent = re.sub(r'___\s*(\d+)', r'___[\1]', sent)
                sent = re.sub(r'\s*[\.\[\]\(\)]+\s*$', '', sent).strip()
                if re.search(r'___\[\d+$', sent):
                    sent += ']'
                if not sent.endswith('?') and not sent.endswith('.'):
                    sent += '.'

                trans = clean_text(' '.join(t_lines))
                trans = re.sub(r'^\s*\]+\s*', '', trans)
                trans = re.sub(r'\s*\[+\s*$', '', trans)
                trans = re.sub(r'\[\s+', '[', trans)
                trans = re.sub(r'\s+\]', ']', trans)
                open_b = trans.count('[')
                close_b = trans.count(']')
                if open_b > close_b:
                    trans += ']' * (open_b - close_b)
                elif close_b > open_b:
                    trans = ('[' * (close_b - open_b)) + trans

                exercise_a["questions"].append({
                    "number": q_num,
                    "sentence": sent,
                    "translation": trans,
                    "word_bank": bank_tokens
                })

        days_data.append({
            "day": day_num,
            "title": f"DAY {day_num}",
            "original_title": raw_title,
            "due_date": due_date,
            "posted_date": posted_date,
            "dan_do": dan_do,
            "vocabulary": vocab_entries,
            "exercise_a": exercise_a,
            "wayground": wg_info,
            "drive_files": drive_files,
            "raw_html": raw_html,
            "full_text": full_text
        })

    days_data.sort(key=lambda d: d["day"])

    # Google Drive Class Recordings (Video Buổi Học 1 đến 37)
    buoi_file = '/Users/andynguyen/workspace/35-days/buoi_recordings.json'
    BUOI_DATA = {}
    if os.path.exists(buoi_file):
        with open(buoi_file, 'r', encoding='utf-8') as f:
            raw_b = json.load(f)
            BUOI_DATA = {int(k): v for k, v in raw_b.items()}

    for d in days_data:
        day_num = d["day"]
        d_files = d.get("drive_files", [])
        existing_urls = {f.get("url") for f in d_files}

        if day_num == 0 and 1 in BUOI_DATA:
            b1 = BUOI_DATA[1]
            d["video_recording"] = b1
            d["video_recordings"] = [b1]
            if b1["url"] not in existing_urls:
                d_files.insert(0, {"name": f"Video Buổi Học Đầu Tiên: {b1['title']}", "url": b1["url"], "type": "video"})
        elif day_num in BUOI_DATA and day_num < 35:
            b = BUOI_DATA[day_num]
            d["video_recording"] = b
            d["video_recordings"] = [b]
            if b["url"] not in existing_urls:
                d_files.insert(0, {"name": f"Video Buổi Học: {b['title']}", "url": b["url"], "type": "video"})
        elif day_num == 35:
            b35 = BUOI_DATA.get(35)
            b36 = BUOI_DATA.get(36)
            b37 = BUOI_DATA.get(37)
            recs = [b for b in [b35, b36, b37] if b]
            if recs:
                d["video_recording"] = recs[0]
                d["video_recordings"] = recs
            to_add = []
            if b35:
                to_add.append({"name": f"Video Buổi Học: {b35['title']}", "url": b35["url"], "type": "video"})
            if b36:
                to_add.append({"name": f"Video Buổi Học (Ôn thi): {b36['title']}", "url": b36["url"], "type": "video"})
            if b37:
                to_add.append({"name": f"Video Buổi Học (Ôn thi): {b37['title']}", "url": b37["url"], "type": "video"})
            for item in reversed(to_add):
                if item["url"] not in existing_urls:
                    d_files.insert(0, item)
        d["drive_files"] = d_files

    # Flat vocabulary list
    all_vocab = []
    vocab_by_day = {}
    for d in days_data:
        vocab_by_day[d["day"]] = d["vocabulary"]
        for v in d["vocabulary"]:
            entry = dict(v)
            entry["day"] = d["day"]
            all_vocab.append(entry)

    # Ingest valid permanent games from game.html if available
    perm_games = []
    if os.path.exists("game.html"):
        with open("game.html", "r", encoding="utf-8") as f:
            soup_games = BeautifulSoup(f.read(), "html.parser")
        items = soup_games.find_all("div", class_="bqKF7d")
        for it in items:
            text = it.get_text("\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines: continue
            all_links = re.findall(r"https://(?:quizizz|wayground)\.com/join\?gc=(\d+)", text)
            if not all_links: continue
            
            if "🎮" in text:
                parts = re.split(r"🎮\s*", text)
                main_req = ""
                for idx_l, l in enumerate(lines):
                    if "KHÔNG SAI" in l or "STREAKS" in l:
                        main_req = l
                        break
                    elif "YÊU CẦU:" in l and idx_l + 1 < len(lines):
                        main_req = lines[idx_l + 1]
                        break
                for pt in parts[1:]:
                    pt_lines = [l.strip() for l in pt.split("\n") if l.strip()]
                    if not pt_lines: continue
                    title = pt_lines[0]
                    nums = [int(n) for n in re.findall(r"\d+", title)]
                    pt_codes = list(dict.fromkeys(re.findall(r"https://(?:quizizz|wayground)\.com/join\?gc=(\d+)", pt)))
                    if pt_codes:
                        perm_games.append({
                            "title": f"GAME VĨNH VIỄN {title}",
                            "days": nums,
                            "primary_code": pt_codes[0],
                            "backup_codes": pt_codes[1:],
                            "backup_urls": [f"https://quizizz.com/join?gc={c}" for c in pt_codes[1:]],
                            "all_codes": pt_codes,
                            "primary_url": f"https://quizizz.com/join?gc={pt_codes[0]}",
                            "all_urls": [f"https://quizizz.com/join?gc={c}" for c in pt_codes],
                            "requirement": main_req or "Không sai câu nào, đạt đủ streak yêu cầu.",
                            "raw_text": pt.strip()
                        })
                continue

            title = lines[0]
            m_days = re.findall(r"DAY\s*\[(.*?)\]|\[DAY\s*(\d+)\]", text, re.I)
            days_found = []
            for d1, d2 in m_days:
                s = d1 or d2
                days_found.extend([int(n) for n in re.findall(r"\d+", s)])
            days_found = sorted(list(set(days_found)))
            
            req = ""
            for idx_l, l in enumerate(lines):
                if "KHÔNG SAI" in l or "STREAKS" in l:
                    req = l
                    break
                elif "YÊU CẦU:" in l and idx_l + 1 < len(lines):
                    req = lines[idx_l + 1]
                    break
                    
            codes = list(dict.fromkeys(all_links))
            perm_games.append({
                "title": title,
                "days": days_found,
                "primary_code": codes[0],
                "backup_codes": codes[1:],
                "backup_urls": [f"https://quizizz.com/join?gc={c}" for c in codes[1:]],
                "all_codes": codes,
                "primary_url": f"https://quizizz.com/join?gc={codes[0]}",
                "all_urls": [f"https://quizizz.com/join?gc={c}" for c in codes],
                "requirement": req or "Không sai câu nào, đạt đủ streak yêu cầu.",
                "raw_text": text.strip()
            })

    if perm_games:
        with open("permanent_games_clean.json", "w", encoding="utf-8") as f:
            json.dump(perm_games, f, indent=2, ensure_ascii=False)

        for d in days_data:
            day_num = d["day"]
            matching = [g for g in perm_games if day_num in g["days"]]
            best_game = None
            if matching:
                exact = [g for g in matching if len(g["days"]) == 1]
                if exact:
                    best_game = exact[0]
                else:
                    milestone = [g for g in matching if max(g["days"]) == day_num]
                    if milestone:
                        milestone.sort(key=lambda x: len(x["days"]))
                        best_game = milestone[0]
                    else:
                        matching.sort(key=lambda x: len(x["days"]))
                        best_game = matching[0]

            if best_game:
                d["wayground"]["primary_code"] = best_game["primary_code"]
                d["wayground"]["primary_url"] = best_game["primary_url"]
                d["wayground"]["backup_urls"] = best_game["backup_urls"]
                d["wayground"]["all_codes"] = best_game["all_codes"]
                d["wayground"]["all_urls"] = best_game["all_urls"]
                d["wayground"]["requirement"] = best_game["requirement"]
                d["wayground"]["permanent_title"] = best_game["title"]
                d["wayground"]["related_games"] = [
                    {
                        "title": g["title"],
                        "primary_code": g["primary_code"],
                        "primary_url": g["primary_url"],
                        "all_urls": g["all_urls"],
                        "days": g["days"],
                        "requirement": g["requirement"]
                    }
                    for g in matching
                ]

    # Wayground games mapping
    wg_games = {}
    for g in perm_games:
        gc = g["primary_code"]
        target_days = g["days"] if g["days"] else [0]
        wg_games[gc] = {
            "game_code": gc,
            "url": g["primary_url"],
            "backup_urls": g["backup_urls"],
            "all_urls": g["all_urls"],
            "title": g["title"],
            "primary_day": g["days"][-1] if g["days"] else 0,
            "target_days": target_days,
            "requirement": g["requirement"],
            "reward": "TRẢ BÀI LỌT [TOP 3] HAI LẦN LIÊN TIẾP ĐƯỢC THƯỞNG 30K",
            "questions": []
        }
        for bc in g["backup_codes"]:
            if bc not in wg_games:
                wg_games[bc] = dict(wg_games[gc])
                wg_games[bc]["game_code"] = bc
                wg_games[bc]["url"] = f"https://quizizz.com/join?gc={bc}"

    for d in days_data:
        for gc in d["wayground"]["game_codes"]:
            if gc not in wg_games:
                wg_games[gc] = {
                    "game_code": gc,
                    "url": f"https://quizizz.com/join?gc={gc}",
                    "title": d["wayground"]["title"] or f"Wayground Review Day {d['day']}",
                    "primary_day": d["day"],
                    "target_days": d["wayground"]["target_days"] if d["wayground"]["target_days"] else [d["day"]],
                    "deadline": d["wayground"]["deadline"],
                    "reward": d["wayground"]["reward"],
                    "questions": []
                }

    # Generate rich Wayground Quiz questions for each game
    random.seed(42)
    for gc, game in wg_games.items():
        target_days = game["target_days"]
        target_pool = []
        for t_day in target_days:
            target_pool.extend(vocab_by_day.get(t_day, []))
            
        distractor_pool = [v for v in all_vocab if v not in target_pool]
        if not distractor_pool:
            distractor_pool = all_vocab

        questions = []
        q_id = 1

        for v in target_pool:
            term = v["term"]
            meaning = v["meaning"]
            phonetic = v.get("phonetic", "")
            pos = v.get("pos", "")
            synonyms = v.get("synonyms", [])
            examples = v.get("examples", [])

            if not meaning or not term:
                continue

            root_word = term.split()[0]
            clean_term_lower = term.strip().lower()
            term_img = get_word_image(term, q_id)

            # 1. Single Choice: Term -> Meaning (with Question Illustration)
            other_meanings = [x["meaning"] for x in distractor_pool + target_pool if x["meaning"] and x["meaning"] != meaning]
            if len(other_meanings) >= 3:
                distractors = random.sample(other_meanings, 3)
                opts = distractors + [meaning]
                random.shuffle(opts)
                questions.append({
                    "id": f"q_{gc}_{q_id}",
                    "question_format": "single_choice",
                    "type": "word_to_meaning",
                    "type_label": "Đơn Tuyển (Nghĩa Từ)",
                    "question": f"Từ '{term}' {pos} có nghĩa là gì?",
                    "image": term_img,
                    "audio_text": term,
                    "phonetic": phonetic,
                    "options": opts,
                    "correct_answers": [meaning],
                    "correct_answer": meaning,
                    "hint": {
                        "short": f"Từ bắt đầu bằng chữ '{term[0].upper()}...', từ loại: {pos or 'N/A'}.",
                        "phonetic": phonetic,
                        "vietnamese": meaning[:40] + ("..." if len(meaning) > 40 else ""),
                        "first_letter": term[0].upper(),
                        "length": len(term.replace(" ", ""))
                    },
                    "explanation": f"'{term}' {phonetic} {pos} có nghĩa là: {meaning}.",
                    "points": 1000,
                    "time_limit": 20
                })
                q_id += 1

            # 2. Single Choice: Meaning -> Term (with Question Illustration)
            other_terms = [x["term"] for x in distractor_pool + target_pool if x["term"] and x["term"] != term]
            if len(other_terms) >= 3:
                distractors = random.sample(other_terms, 3)
                opts = distractors + [term]
                random.shuffle(opts)
                questions.append({
                    "id": f"q_{gc}_{q_id}",
                    "question_format": "single_choice",
                    "type": "meaning_to_word",
                    "type_label": "Đơn Tuyển (Chọn Từ)",
                    "question": f"Từ tiếng Anh nào mang nghĩa: '{meaning}'?",
                    "image": term_img,
                    "audio_text": term,
                    "phonetic": phonetic,
                    "options": opts,
                    "correct_answers": [term],
                    "correct_answer": term,
                    "hint": {
                        "short": f"Bắt đầu bằng chữ '{term[0].upper()}...', gồm {len(term.replace(' ', ''))} ký tự.",
                        "phonetic": phonetic,
                        "vietnamese": meaning,
                        "first_letter": term[0].upper(),
                        "length": len(term.replace(" ", ""))
                    },
                    "explanation": f"Đáp án chính xác là '{term}' {phonetic}.",
                    "points": 1000,
                    "time_limit": 20
                })
                q_id += 1

            # 3. Photo Identification: Look at picture -> Choose English term (TOEIC Part 1 / Visual Vocab)
            if len(other_terms) >= 3:
                distractors = random.sample(other_terms, 3)
                opts = distractors + [term]
                random.shuffle(opts)
                questions.append({
                    "id": f"q_{gc}_{q_id}",
                    "question_format": "single_choice",
                    "type": "photo_identification",
                    "type_label": "📸 Nhìn Tranh Chọn Từ",
                    "question": "Quan sát bức ảnh dưới đây và chọn từ tiếng Anh mô tả phù hợp nhất:",
                    "image": term_img,
                    "audio_text": term,
                    "phonetic": phonetic,
                    "options": opts,
                    "correct_answers": [term],
                    "correct_answer": term,
                    "hint": {
                        "short": f"Bức ảnh minh họa khái niệm: '{meaning[:35]}...'. Bắt đầu bằng '{term[0].upper()}'.",
                        "phonetic": phonetic,
                        "vietnamese": meaning,
                        "first_letter": term[0].upper(),
                        "length": len(term.replace(" ", ""))
                    },
                    "explanation": f"Bức ảnh mô tả từ '{term}' {phonetic} ({pos}): {meaning}.",
                    "points": 1200,
                    "time_limit": 25
                })
                q_id += 1

            # 4. Image Answer Options: Which picture illustrates the word? (Phương án là hình ảnh!)
            other_vocab_for_img = [x for x in distractor_pool if x["term"] != term and x.get("meaning")]
            if len(other_vocab_for_img) >= 3:
                distractors = random.sample(other_vocab_for_img, 3)
                choices = [v] + distractors
                random.shuffle(choices)
                opts_text = [c["term"] for c in choices]
                opts_imgs = [get_word_image(c["term"]) for c in choices]
                questions.append({
                    "id": f"q_{gc}_{q_id}",
                    "question_format": "single_choice",
                    "type": "image_options",
                    "type_label": "🖼️ Chọn Tranh Minh Họa",
                    "has_image_options": True,
                    "question": f"Bức ảnh nào dưới đây minh họa đúng nhất cho từ '{term}' {pos}?\n(Nghĩa: {meaning})",
                    "image": "",
                    "audio_text": term,
                    "phonetic": phonetic,
                    "options": opts_text,
                    "option_images": opts_imgs,
                    "correct_answers": [term],
                    "correct_answer": term,
                    "hint": {
                        "short": f"Chọn hình ảnh thể hiện đúng nghĩa: '{meaning}'.",
                        "phonetic": phonetic,
                        "vietnamese": meaning
                    },
                    "explanation": f"Hình ảnh tương ứng với '{term}' {phonetic}: {meaning}.",
                    "points": 1200,
                    "time_limit": 25
                })
                q_id += 1

            # 5. Multiple Choice: Multiple Synonyms (khi có 2+ synonyms)
            if synonyms and len(synonyms) >= 2:
                correct_syns = synonyms[:2]
                other_words = [x["term"] for x in distractor_pool if x["term"] not in correct_syns and x["term"] != term]
                if len(other_words) >= 2:
                    distractors = random.sample(other_words, 2)
                    opts = correct_syns + distractors
                    random.shuffle(opts)
                    questions.append({
                        "id": f"q_{gc}_{q_id}",
                        "question_format": "multiple_choice",
                        "type": "multiple_synonyms",
                        "type_label": "Đa Tuyển (Nhiều Đáp Án)",
                        "question": f"Chọn TẤT CẢ các từ/cụm từ đồng nghĩa (synonyms) của '{term}':\n(Chọn 2 đáp án đúng)",
                        "image": term_img,
                        "audio_text": term,
                        "phonetic": phonetic,
                        "options": opts,
                        "correct_answers": correct_syns,
                        "correct_answer": ", ".join(correct_syns),
                        "hint": {
                            "short": f"Có 2 từ đồng nghĩa đúng trong 4 phương án. Nghĩa chung: {meaning}.",
                            "phonetic": phonetic,
                            "vietnamese": meaning
                        },
                        "explanation": f"Các từ đồng nghĩa của '{term}' là: {', '.join(synonyms)}. Nghĩa: {meaning}.",
                        "points": 1500,
                        "time_limit": 30
                    })
                    q_id += 1

            # 6. Fill in the Blank: Sentence Context (Type-in)
            has_blank_sentence = False
            for eg in (examples or []):
                en_sentence = eg.get("en", "")
                vi_trans = eg.get("vi", "")
                
                matched_word = None
                if len(root_word) >= 3 and root_word.lower() in en_sentence.lower():
                    m_w = re.search(r'\b' + re.escape(root_word) + r'\w*\b', en_sentence, re.IGNORECASE)
                    if m_w:
                        matched_word = m_w.group(0)
                elif len(root_word) >= 4:
                    stem = root_word.rstrip('esd')
                    if len(stem) >= 3 and stem.lower() in en_sentence.lower():
                        m_w = re.search(r'\b' + re.escape(stem) + r'\w*\b', en_sentence, re.IGNORECASE)
                        if m_w:
                            matched_word = m_w.group(0)

                if matched_word:
                    blanked = re.sub(r'\b' + re.escape(matched_word) + r'\b', "________", en_sentence, count=1, flags=re.IGNORECASE)
                    valid_answers = list(set([term.strip(), root_word.strip(), clean_term_lower, root_word.lower(), matched_word, matched_word.lower()]))
                    questions.append({
                        "id": f"q_{gc}_{q_id}",
                        "question_format": "fill_blank",
                        "type": "fill_blank_sentence",
                        "type_label": "Điền Từ Khuyết (Tự Gõ)",
                        "question": f"Gõ từ tiếng Anh thích hợp vào chỗ trống:\n\n\"{blanked}\"" + (f"\n\n(Nghĩa gợi ý: {meaning})" if meaning else ""),
                        "image": term_img,
                        "audio_text": en_sentence,
                        "phonetic": phonetic,
                        "options": [],
                        "correct_answers": valid_answers,
                        "correct_answer": term,
                        "hint": {
                            "short": f"Bắt đầu bằng chữ '{term[0].upper()}...', gồm {len(matched_word)} ký tự.",
                            "phonetic": phonetic,
                            "vietnamese": meaning,
                            "first_letter": term[0].upper(),
                            "length": len(matched_word)
                        },
                        "explanation": f"Câu hoàn chỉnh: \"{en_sentence}\"" + (f"\n({vi_trans})" if vi_trans else ""),
                        "points": 1500,
                        "time_limit": 30
                    })
                    q_id += 1
                    has_blank_sentence = True
                    break

            if not has_blank_sentence:
                valid_answers = list(set([term.strip(), root_word.strip(), clean_term_lower, root_word.lower()]))
                questions.append({
                    "id": f"q_{gc}_{q_id}",
                    "question_format": "fill_blank",
                    "type": "fill_blank_vocab",
                    "type_label": "Điền Từ Khuyết (Tự Gõ)",
                    "question": f"Gõ từ tiếng Anh có nghĩa là: '{meaning}'\nPhiên âm: {phonetic}",
                    "image": term_img,
                    "audio_text": term,
                    "phonetic": phonetic,
                    "options": [],
                    "correct_answers": valid_answers,
                    "correct_answer": term,
                    "hint": {
                        "short": f"Từ bắt đầu bằng '{term[0].upper()}...', gồm {len(term.replace(' ', ''))} ký tự.",
                        "phonetic": phonetic,
                        "vietnamese": meaning,
                        "first_letter": term[0].upper(),
                        "length": len(term.replace(" ", ""))
                    },
                    "explanation": f"Từ tiếng Anh chính xác là '{term}' {phonetic}: {meaning}.",
                    "points": 1500,
                    "time_limit": 30
                })
                q_id += 1

        # 7. Multiple Choice: Category / POS questions
        target_nouns = [v["term"] for v in target_pool if "(n)" in v.get("pos", "").lower() or "n." in v.get("pos", "").lower()]
        other_non_nouns = [v["term"] for v in distractor_pool if "(v)" in v.get("pos", "").lower() or "(adj)" in v.get("pos", "").lower()]
        if len(target_nouns) >= 2 and len(other_non_nouns) >= 2:
            c_nouns = random.sample(target_nouns, 2)
            d_words = random.sample(other_non_nouns, 2)
            opts = c_nouns + d_words
            random.shuffle(opts)
            questions.append({
                "id": f"q_{gc}_{q_id}",
                "question_format": "multiple_choice",
                "type": "multiple_pos",
                "type_label": "Đa Tuyển (Nhóm Danh Từ)",
                "question": "Chọn TẤT CẢ các danh từ (Nouns) trong 4 từ sau:\n(Chọn 2 đáp án đúng)",
                "image": get_word_image(c_nouns[0]),
                "audio_text": "Choose all nouns",
                "phonetic": "",
                "options": opts,
                "correct_answers": c_nouns,
                "correct_answer": ", ".join(c_nouns),
                "hint": {
                    "short": "Tìm 2 từ đóng vai trò danh từ (chỉ người, sự vật, hành động/chính sách) trong 4 phương án.",
                    "vietnamese": "Danh từ thường kết thúc bằng đuôi -al, -tion, -ment, -cy, -er..."
                },
                "explanation": f"Các danh từ đúng là: {', '.join(c_nouns)}.",
                "points": 1500,
                "time_limit": 25
            })
            q_id += 1

        # 8. Single Choice: Listening challenge
        if target_pool:
            listen_sample = random.sample(target_pool, min(2, len(target_pool)))
            for lv in listen_sample:
                l_term = lv["term"]
                l_meaning = lv.get("meaning", "")
                other_terms = [x["term"] for x in distractor_pool if x["term"] != l_term]
                if len(other_terms) >= 3:
                    distractors = random.sample(other_terms, 3)
                    opts = distractors + [l_term]
                    random.shuffle(opts)
                    questions.append({
                        "id": f"q_{gc}_{q_id}",
                        "question_format": "single_choice",
                        "type": "audio_listening",
                        "type_label": "🎧 Nghe & Chọn Từ",
                        "question": "Hãy lắng nghe phát âm và chọn từ chính xác:",
                        "image": get_word_image(l_term),
                        "audio_text": l_term,
                        "phonetic": lv.get("phonetic", ""),
                        "options": opts,
                        "correct_answers": [l_term],
                        "correct_answer": l_term,
                        "hint": {
                            "short": f"Nghĩa tiếng Việt: {l_meaning}. Bắt đầu bằng '{l_term[0].upper()}'.",
                            "phonetic": lv.get("phonetic", ""),
                            "vietnamese": l_meaning
                        },
                        "explanation": f"Từ được phát âm là '{l_term}' {lv.get('phonetic', '')}: {l_meaning}",
                        "points": 1200,
                        "time_limit": 25
                    })
                    q_id += 1

        random.shuffle(questions)
        game["questions"] = questions

    # Save outputs
    with open('/Users/andynguyen/workspace/35-days/days_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "total_days": len(days_data),
                "total_vocabulary": len(all_vocab),
                "total_exercises": sum(len(d["exercise_a"]["questions"]) for d in days_data),
                "total_wayground_games": len(wg_games)
            },
            "days": days_data
        }, f, ensure_ascii=False, indent=2)

    with open('/Users/andynguyen/workspace/35-days/all_vocabulary.json', 'w', encoding='utf-8') as f:
        json.dump(all_vocab, f, ensure_ascii=False, indent=2)

    with open('/Users/andynguyen/workspace/35-days/wayground_quizzes.json', 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "total_games": len(wg_games),
                "total_questions": sum(len(g["questions"]) for g in wg_games.values()),
                "correct_memes": QUIZIZZ_CORRECT_MEMES,
                "wrong_memes": QUIZIZZ_WRONG_MEMES
            },
            "correct_memes": QUIZIZZ_CORRECT_MEMES,
            "wrong_memes": QUIZIZZ_WRONG_MEMES,
            "games": list(wg_games.values())
        }, f, ensure_ascii=False, indent=2)

    # JS files for instant file:// & http:// loading
    with open('/Users/andynguyen/workspace/35-days/vocab_data.js', 'w', encoding='utf-8') as f:
        f.write('window.DAYS_DATA = ' + json.dumps({"metadata": {"total_days": len(days_data)}, "days": days_data}, ensure_ascii=False) + ';\n')
        f.write('window.ALL_VOCABULARY = ' + json.dumps(all_vocab, ensure_ascii=False) + ';\n')

    with open('/Users/andynguyen/workspace/35-days/wayground_data.js', 'w', encoding='utf-8') as f:
        f.write('window.WAYGROUND_QUIZZES = ' + json.dumps({
            "games": list(wg_games.values()),
            "correct_memes": QUIZIZZ_CORRECT_MEMES,
            "wrong_memes": QUIZIZZ_WRONG_MEMES
        }, ensure_ascii=False) + ';\n')

    print("\nExtraction & Generation successfully updated!")
    print(f"- days_data.json: {len(days_data)} days, {len(all_vocab)} words, {sum(len(d['exercise_a']['questions']) for d in days_data)} exercise questions")
    print(f"- wayground_quizzes.json: {len(wg_games)} games, {sum(len(g['questions']) for g in wg_games.values())} quiz questions")

if __name__ == '__main__':
    extract_all()
