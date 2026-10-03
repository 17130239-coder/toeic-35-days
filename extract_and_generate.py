#!/usr/bin/env python3
"""
Comprehensive, High-Precision Extractor and Quiz Generator
for 35-Days Vocabulary Course & Wayground Clone
"""
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
    (30, 3): {"term": "Play/Assume a crucial role in", "pos": "(collocation)", "phonetic": "/pleɪ ə roʊl ɪn/", "meaning": "Đóng / đảm nhiệm vai trò then chốt trong việc gì"},
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
                            "phonetic": m.group(2).strip(),
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
                
                # Extract true phonetics
                ipas = [f"/{m.strip('/ ')}/" for m in re.findall(r'/([^/\n]+)/', body) if is_true_ipa(f"/{m}/")]
                phonetic = ', '.join(ipas) if ipas else ""
                
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
        exercise_a = {
            "title": "VIẾT CÂU HOÀN CHỈNH",
            "form_url": form_links[0]['url'] if form_links else "",
            "raw_text": "",
            "questions": []
        }
        
        if 'VIẾT CÂU' in raw_html:
            start_pos = raw_html.find('VIẾT CÂU')
            end_pos = raw_html.find('B. GAME QUIZIZZ')
            sub_html = raw_html[start_pos:end_pos if end_pos != -1 else len(raw_html)]
            
            # Replace <br> with newline
            sub_text = re.sub(r'<br\s*/?>', '\n', sub_html)
            text_block = BeautifulSoup(sub_text, 'html.parser').get_text('\n')
            
            # Split into questions by numbers
            q_chunks = re.split(r'\n\s*(\d+)[\.\)]\s*', '\n' + text_block)
            for i in range(1, len(q_chunks), 2):
                q_num = int(q_chunks[i])
                chunk_text = q_chunks[i+1]
                raw_lines = [l.strip() for l in chunk_text.split('\n') if l.strip()]
                if not raw_lines:
                    continue
                
                s_lines = []
                t_lines = []
                b_lines = []
                phase = 'sent'
                
                for line in raw_lines:
                    if line.startswith('=>'):
                        continue
                    if 'B. GAME QUIZIZZ' in line:
                        break
                    
                    line_has_vn = has_vietnamese(line)
                    
                    if phase == 'sent':
                        if '___' in line or not line_has_vn:
                            s_lines.append(clean_text(line))
                        else:
                            phase = 'trans'
                            t_lines.append(clean_text(line))
                    elif phase == 'trans':
                        if line_has_vn:
                            t_lines.append(clean_text(line))
                        else:
                            phase = 'bank'
                            b_lines.append(line)
                    elif phase == 'bank':
                        if not line_has_vn:
                            b_lines.append(line)
                            
                sent = ' '.join(s_lines).strip()
                trans = ' '.join(t_lines).strip()
                
                # Bank tokens: split on 2 or more spaces or non-breaking spaces
                bank_raw = ' '.join(b_lines)
                tokens = [t.strip() for t in re.split(r'[\xa0\s]{2,}|\t+', bank_raw) if t.strip()]
                if len(tokens) <= 1 and bank_raw:
                    # fallback
                    tokens = [t.strip() for t in bank_raw.split() if t.strip() and t not in ['.', ',', ';']]

                # Clean tokens
                cleaned_tokens = []
                for tk in tokens:
                    c = clean_text(tk)
                    # remove trailing punctuation
                    c = re.sub(r'^[\.\,\;\:\'\"]+|[\.\,\;\:\'\"]+$', '', c).strip()
                    if c and len(c) > 1 and not has_vietnamese(c):
                        cleaned_tokens.append(c)

                exercise_a["questions"].append({
                    "number": q_num,
                    "sentence": sent,
                    "translation": trans,
                    "word_bank": cleaned_tokens
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

    # Flat vocabulary list
    all_vocab = []
    vocab_by_day = {}
    for d in days_data:
        vocab_by_day[d["day"]] = d["vocabulary"]
        for v in d["vocabulary"]:
            entry = dict(v)
            entry["day"] = d["day"]
            all_vocab.append(entry)

    # Wayground games mapping
    wg_games = {}
    for d in days_data:
        for gc in d["wayground"]["game_codes"]:
            if gc not in wg_games:
                wg_games[gc] = {
                    "game_code": gc,
                    "url": f"https://wayground.com/join?gc={gc}",
                    "title": d["wayground"]["title"] or f"Wayground Review Day {d['day']}",
                    "primary_day": d["day"],
                    "target_days": d["wayground"]["target_days"] if d["wayground"]["target_days"] else [d["day"]],
                    "deadline": d["wayground"]["deadline"],
                    "reward": d["wayground"]["reward"],
                    "questions": []
                }
            else:
                for td in d["wayground"]["target_days"]:
                    if td not in wg_games[gc]["target_days"]:
                        wg_games[gc]["target_days"].append(td)
                        wg_games[gc]["target_days"].sort()

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
