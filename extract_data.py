#!/usr/bin/env python3
"""
Extract 35 Days Vocabulary & Wayground data from data.html
"""
import re
import json
import os
from bs4 import BeautifulSoup

def clean_text(s):
    if not s:
        return ""
    # normalize spaces
    s = re.sub(r'[\r\t\xa0]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()

def parse_html():
    html_path = '/Users/andynguyen/workspace/35-days/data.html'
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    items = soup.find_all('li', class_=lambda c: c and 'tfGBod' in c)
    print(f"Found {len(items)} items in Google Classroom DOM")

    days_data = []

    for item in items:
        # Title
        title_el = item.find('span', class_=lambda c: c and 'Vu2fZd' in c)
        title = title_el.get_text(strip=True) if title_el else ""
        
        m_day = re.search(r'DAY\s*(\d+)', title, re.IGNORECASE)
        day_num = int(m_day.group(1)) if m_day else None
        if day_num is None:
            continue

        # Dates
        due_el = item.find('span', string=re.compile(r'Due\s+', re.I))
        due_date = due_el.get_text(strip=True) if due_el else ""
        
        posted_el = item.find('span', string=re.compile(r'Posted\s+', re.I))
        posted_date = posted_el.get_text(strip=True) if posted_el else ""

        # Main content box
        bq = item.find('div', class_='bqKF7d')
        raw_html = str(bq) if bq else ""
        full_text = bq.get_text('\n', strip=True) if bq else ""

        # Extract links
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

        # Parse Reminder [DẶN DÒ]
        dan_do = ""
        if '[DẶN DÒ]' in full_text:
            p_start = full_text.find('[DẶN DÒ]')
            m_next = re.search(r'(?:📚\s*DAY\s*\d+|📚\s*\[\s*DAY\s*\d+)', full_text)
            if m_next and m_next.start() > p_start:
                dan_do = full_text[p_start:m_next.start()].strip()
            else:
                # Up to first numbered vocab item
                m_num = re.search(r'\n1\.\s*[A-Za-z]', full_text)
                if m_num:
                    dan_do = full_text[p_start:m_num.start()].strip()

        # Parse Wayground section details
        wg_info = {
            "urls": [w['url'] for w in wayground_links],
            "game_codes": [w['game_code'] for w in wayground_links if w['game_code']],
            "title": "",
            "target_days": [],
            "raw_text": ""
        }
        
        m_wg_section = re.search(r'(?:B\.\s*GAME QUIZIZZ[^\n]*|GAME QUIZIZZ[^\n]*)', full_text, re.IGNORECASE)
        if m_wg_section:
            wg_sub = full_text[m_wg_section.start():]
            wg_info["raw_text"] = wg_sub.strip()
            
            # extract target days e.g. DAY [18 + 19 + 35] or DAY [0 + 1]
            m_td = re.search(r'DAY\s*\[([0-9\s\+\,]+)\]', wg_sub, re.IGNORECASE)
            if m_td:
                days_str = m_td.group(1)
                nums = [int(n.strip()) for n in re.findall(r'\d+', days_str)]
                wg_info["target_days"] = nums
            else:
                # check for single day or specific title
                m_single = re.search(r'DAY\s*(\d+)', wg_sub, re.IGNORECASE)
                if m_single:
                    wg_info["target_days"] = [int(m_single.group(1))]
                elif 'TÍNH TỪ' in wg_sub.upper():
                    wg_info["target_days"] = [6, 7] # TÍNH TỪ ĐUÔI ING & ED
                else:
                    wg_info["target_days"] = [day_num]
            
            first_line = wg_sub.split('\n')[0].strip()
            wg_info["title"] = first_line

        # Parse Exercise A (Sentence completion)
        exercise_a = {
            "title": "VIẾT CÂU HOÀN CHỈNH",
            "form_url": form_links[0]['url'] if form_links else "",
            "raw_text": "",
            "questions": []
        }
        
        m_ex_start = re.search(r'(?:A\.\s*VIẾT CÂU|A\.\s*BÀI TẬP|BÀI TẬP VỀ NHÀ|A\.\xa0VIẾT CÂU)', full_text)
        if m_ex_start:
            sub = full_text[m_ex_start.start():]
            p_end = re.search(r'B\.\s*GAME QUIZIZZ', sub)
            ex_body = sub[:p_end.start()] if p_end else sub
            exercise_a["raw_text"] = ex_body.strip()
            
            # Parse questions: 1. ... 2. ...
            q_chunks = re.split(r'\n(?=\d+\.\s*(?:___|\[|You|The|Our|After|It|Willis|In|She|He|We|They|A|An))', ex_body)
            for chunk in q_chunks[1:]: # skip preamble
                chunk = chunk.strip()
                if not chunk:
                    continue
                m_qnum = re.match(r'^(\d+)\.\s*', chunk)
                q_num = int(m_qnum.group(1)) if m_qnum else len(exercise_a["questions"]) + 1
                q_content = chunk[m_qnum.end():] if m_qnum else chunk
                
                # Split lines
                lines = [l.strip() for l in q_content.split('\n') if l.strip()]
                if not lines:
                    continue
                
                # First line(s) usually have the English sentence with blanks ___[1]
                sentence_lines = []
                trans_lines = []
                bank_lines = []
                
                state = 'sentence'
                for l in lines:
                    if '___[' in l or state == 'sentence' and not any(vn in l.lower() for vn in ['bởi vì', 'sau ', 'chúng tôi', 'bạn phải', 'cửa hàng', 'thật ', 'khi ', 'sự ', 'được ', 'nếu ']):
                        sentence_lines.append(l)
                        if '___[' in l and len(sentence_lines) >= 2:
                            state = 'trans'
                    elif state == 'sentence' and any(vn in l.lower() for vn in ['bởi vì', 'sau ', 'chúng tôi', 'bạn phải', 'cửa hàng', 'thật ', 'khi ', 'sự ', 'được ', 'nếu ']):
                        state = 'trans'
                        trans_lines.append(l)
                    elif state == 'trans':
                        # Check if this line looks like word bank
                        # Word banks have multiple words separated by multiple spaces or tabs
                        if '   ' in l or '\t' in l or re.search(r'[A-Za-z\s]{3,}\s{2,}[A-Za-z\s]{3,}', l) or l.isupper():
                            state = 'bank'
                            bank_lines.append(l)
                        else:
                            trans_lines.append(l)
                    elif state == 'bank':
                        bank_lines.append(l)
                
                sentence_text = ' '.join(sentence_lines).strip()
                trans_text = ' '.join(trans_lines).strip()
                bank_text = ' '.join(bank_lines).strip()
                
                # Split word bank tokens
                tokens = [t.strip() for t in re.split(r'\s{2,}|\t+', bank_text) if t.strip()]
                if not tokens and bank_text:
                    tokens = [bank_text]
                
                exercise_a["questions"].append({
                    "number": q_num,
                    "sentence": sentence_text,
                    "translation": trans_text,
                    "word_bank": tokens,
                    "raw": chunk
                })

        # Parse Vocabulary Items
        # Vocab section is between title / reminder and Exercise / Wayground
        v_start = 0
        m_day_header = re.search(r'📚\s*(?:\[\s*)?DAY\s*\d+', full_text)
        if m_day_header:
            v_start = m_day_header.end()
        
        v_end = len(full_text)
        m_stop = re.search(r'(?:📝\s*BÀI TẬP|A\.\s*VIẾT CÂU|📍\s*VIẾT MỖI TỪ|📍\s*YÊU CẦU|B\.\s*GAME QUIZIZZ)', full_text[v_start:])
        if m_stop:
            v_end = v_start + m_stop.start()
            
        vocab_section = full_text[v_start:v_end].strip()
        
        # Parse individual vocab entries: 1. Term ... 2. Term ...
        vocab_entries = []
        # split by numbered items: newline followed by digit.
        parts = re.split(r'\n(?=\d+[\.\)]\s*[A-Za-z])', '\n' + vocab_section)
        
        v_idx = 1
        for part in parts:
            part = part.strip()
            if not part:
                continue
            m_num = re.match(r'^(\d+)[\.\)]\s*(.+)', part, re.DOTALL)
            if not m_num:
                continue
            
            p_num = int(m_num.group(1))
            body = m_num.group(2).strip()
            
            # Extract term (first line or up to phonetic / pos)
            first_line = body.split('\n')[0].strip()
            
            # Try to extract term, phonetic, POS, meaning
            # Example: "Warranty policy /ˈwɔːrənti ˈpɑːləsi/ (n.phrase): Chính sách bảo hành."
            phonetic_match = re.search(r'(/[^\n/]+/)', body)
            phonetic = phonetic_match.group(1) if phonetic_match else ""
            
            pos_match = re.search(r'\((?:n\.phrase|n|v|adj|adv|v/n|n/v|prep|conj|phrase|idiom|collocation)[^\)]*\)', body, re.IGNORECASE)
            pos = pos_match.group(0) if pos_match else ""
            
            # Term is before phonetic or POS
            term = first_line
            if phonetic and phonetic in first_line:
                term = first_line[:first_line.find(phonetic)].strip()
            elif pos and pos in first_line:
                term = first_line[:first_line.find(pos)].strip()
            term = re.sub(r'[\:\=\-\~]+$', '', term).strip()
            
            # Synonyms: look for '= Word' or '~ Word'
            synonyms = []
            for m_syn in re.finditer(r'[\=\~]\s*([A-Za-z\s\-\']+?)(?:\s*/[^\n/]+/|\s*[\=\:\n\(])', body):
                s_word = m_syn.group(1).strip()
                if s_word and len(s_word) > 1 and s_word.lower() not in ['s.th', 's.o', 's.b', 'the', 'a', 'an']:
                    if s_word not in synonyms:
                        synonyms.append(s_word)

            # Meaning: look for Vietnamese text after ':' or '= Meaning :'
            meaning = ""
            m_col = re.search(r'\:\s*([^\n\=]+)', body)
            if m_col:
                cand = m_col.group(1).strip()
                # verify it has Vietnamese characters or latin text
                meaning = cand
            else:
                # Find lines that contain Vietnamese characters
                for l in body.split('\n')[1:]:
                    l = l.strip()
                    if re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', l, re.I):
                        meaning = l
                        break

            # Examples: lines starting with E.g: or ->
            examples = []
            for m_eg in re.finditer(r'(?:E\.g|Ex|Ví dụ)\s*:\s*([^\n]+)(?:\n\(([^\)]+)\))?', body, re.I):
                en_eg = m_eg.group(1).strip()
                vi_eg = m_eg.group(2).strip() if m_eg.group(2) else ""
                examples.append({"en": en_eg, "vi": vi_eg})

            vocab_entries.append({
                "id": f"d{day_num}_w{p_num}",
                "index": p_num,
                "term": term if term else first_line,
                "phonetic": phonetic,
                "pos": pos,
                "meaning": meaning,
                "synonyms": synonyms,
                "examples": examples,
                "raw_text": part
            })
            v_idx += 1

        days_data.append({
            "day": day_num,
            "title": f"DAY {day_num}",
            "original_title": title,
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

    # Sort days by day number (0 to 35)
    days_data.sort(key=lambda d: d["day"])
    print(f"Successfully processed {len(days_data)} days (DAY 0 to DAY {days_data[-1]['day']})")
    
    total_vocab = sum(len(d["vocabulary"]) for d in days_data)
    total_exercises = sum(len(d["exercise_a"]["questions"]) for d in days_data)
    print(f"Total vocabulary items extracted: {total_vocab}")
    print(f"Total exercise questions extracted: {total_exercises}")
    
    # Collect all unique Wayground games
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
                    "raw_text": d["wayground"]["raw_text"]
                }
            else:
                # Merge target days
                for td in d["wayground"]["target_days"]:
                    if td not in wg_games[gc]["target_days"]:
                        wg_games[gc]["target_days"].append(td)
                        wg_games[gc]["target_days"].sort()

    print(f"Total unique Wayground game codes: {len(wg_games)}")

    out_file = '/Users/andynguyen/workspace/35-days/days_data.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "total_days": len(days_data),
                "total_vocabulary": total_vocab,
                "total_exercises": total_exercises,
                "total_wayground_games": len(wg_games)
            },
            "days": days_data,
            "wayground_games": list(wg_games.values())
        }, f, ensure_ascii=False, indent=2)

    print(f"Data saved to {out_file}")

if __name__ == '__main__':
    parse_html()
