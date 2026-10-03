#!/usr/bin/env python3
"""
Comprehensive, High-Precision Extractor and Quiz Generator
for 35-Days Vocabulary Course & Wayground Clone
"""
import re
import json
import random
from bs4 import BeautifulSoup

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
                m_col = re.search(r'\:\s*([^\n\=]+)', body)
                if m_col and has_vietnamese(m_col.group(1)):
                    meaning = clean_text(m_col.group(1))
                else:
                    for l in lines:
                        if has_vietnamese(l):
                            # clean punctuation
                            cleaned_l = re.sub(r'^[0-9\.\:\-\~]+\s*', '', l)
                            cleaned_l = re.sub(r'^[\(\[][^\)\]]+[\)\]]\s*', '', cleaned_l)
                            if cleaned_l:
                                meaning = clean_text(cleaned_l)
                                break

                # Examples
                examples = []
                for m_eg in re.finditer(r'(?:E\.g|Ex|Ví dụ|Eg)\s*:\s*([^\n]+)(?:\n\(([^\)]+)\))?', body, re.I):
                    en_eg = clean_text(m_eg.group(1))
                    vi_eg = clean_text(m_eg.group(2)) if m_eg.group(2) else ""
                    if en_eg:
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
            phonetic = v["phonetic"]
            pos = v["pos"]
            synonyms = v.get("synonyms", [])
            examples = v.get("examples", [])

            if not meaning or not term:
                continue

            # Question Type 1: English Term -> Vietnamese Meaning
            other_meanings = [x["meaning"] for x in distractor_pool + target_pool if x["meaning"] and x["meaning"] != meaning]
            if len(other_meanings) >= 3:
                distractors = random.sample(other_meanings, 3)
                opts = distractors + [meaning]
                random.shuffle(opts)
                questions.append({
                    "id": f"q_{gc}_{q_id}",
                    "type": "word_to_meaning",
                    "type_label": "Nghĩa Của Từ",
                    "question": f"Từ '{term}' {pos} có nghĩa là gì?",
                    "audio_text": term,
                    "phonetic": phonetic,
                    "options": opts,
                    "correct_answer": meaning,
                    "explanation": f"'{term}' {phonetic} {pos} có nghĩa là: {meaning}.",
                    "points": 1000,
                    "time_limit": 20
                })
                q_id += 1

            # Question Type 2: Vietnamese Meaning -> English Term
            other_terms = [x["term"] for x in distractor_pool + target_pool if x["term"] and x["term"] != term]
            if len(other_terms) >= 3:
                distractors = random.sample(other_terms, 3)
                opts = distractors + [term]
                random.shuffle(opts)
                questions.append({
                    "id": f"q_{gc}_{q_id}",
                    "type": "meaning_to_word",
                    "type_label": "Chọn Từ Tiếng Anh",
                    "question": f"Từ tiếng Anh nào mang nghĩa: '{meaning}'?",
                    "audio_text": term,
                    "phonetic": phonetic,
                    "options": opts,
                    "correct_answer": term,
                    "explanation": f"Đáp án chính xác là '{term}' {phonetic}.",
                    "points": 1000,
                    "time_limit": 20
                })
                q_id += 1

            # Question Type 3: Synonyms
            if synonyms:
                syn_word = synonyms[0]
                other_words = [x["term"] for x in distractor_pool if x["term"] != term and x["term"] != syn_word]
                if len(other_words) >= 3:
                    distractors = random.sample(other_words, 3)
                    opts = distractors + [syn_word]
                    random.shuffle(opts)
                    questions.append({
                        "id": f"q_{gc}_{q_id}",
                        "type": "synonym",
                        "type_label": "Từ Đồng Nghĩa",
                        "question": f"Từ nào đồng nghĩa (synonym) với '{term}'?",
                        "audio_text": term,
                        "phonetic": phonetic,
                        "options": opts,
                        "correct_answer": syn_word,
                        "explanation": f"'{term}' = {', '.join(synonyms)}: {meaning}.",
                        "points": 1200,
                        "time_limit": 25
                    })
                    q_id += 1

            # Question Type 4: Sentence Context
            if examples and len(examples) > 0:
                eg = examples[0]
                en_sentence = eg["en"]
                vi_trans = eg.get("vi", "")
                
                # Blank out root of term
                root = term.split()[0]
                if len(root) >= 4 and root.lower() in en_sentence.lower():
                    pattern = re.compile(re.escape(root), re.IGNORECASE)
                    blanked = pattern.sub("________", en_sentence, count=1)
                    other_terms = [x["term"] for x in distractor_pool if x["term"] != term]
                    if len(other_terms) >= 3:
                        distractors = random.sample(other_terms, 3)
                        opts = distractors + [term]
                        random.shuffle(opts)
                        questions.append({
                            "id": f"q_{gc}_{q_id}",
                            "type": "fill_blank",
                            "type_label": "Điền Từ Vào Câu",
                            "question": f"Điền từ thích hợp vào chỗ trống:\n\n\"{blanked}\"" + (f"\n\n({vi_trans})" if vi_trans else ""),
                            "audio_text": en_sentence,
                            "phonetic": phonetic,
                            "options": opts,
                            "correct_answer": term,
                            "explanation": f"Câu hoàn chỉnh: \"{en_sentence}\"\n({vi_trans})",
                            "points": 1500,
                            "time_limit": 30
                        })
                        q_id += 1

        # Question Type 5: Listening challenge
        if target_pool:
            listen_sample = random.sample(target_pool, min(3, len(target_pool)))
            for lv in listen_sample:
                l_term = lv["term"]
                other_terms = [x["term"] for x in distractor_pool if x["term"] != l_term]
                if len(other_terms) >= 3:
                    distractors = random.sample(other_terms, 3)
                    opts = distractors + [l_term]
                    random.shuffle(opts)
                    questions.append({
                        "id": f"q_{gc}_{q_id}",
                        "type": "audio_listening",
                        "type_label": "🎧 Nghe & Chọn Từ",
                        "question": "Hãy lắng nghe phát âm và chọn từ chính xác:",
                        "audio_text": l_term,
                        "phonetic": lv.get("phonetic", ""),
                        "options": opts,
                        "correct_answer": l_term,
                        "explanation": f"Từ được phát âm là '{l_term}' {lv.get('phonetic', '')}: {lv.get('meaning', '')}",
                        "points": 1200,
                        "time_limit": 25
                    })
                    q_id += 1

        random.shuffle(questions)
        game["questions"] = questions[:20]

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
                "total_questions": sum(len(g["questions"]) for g in wg_games.values())
            },
            "games": list(wg_games.values())
        }, f, ensure_ascii=False, indent=2)

    # JS files for instant file:// & http:// loading
    with open('/Users/andynguyen/workspace/35-days/vocab_data.js', 'w', encoding='utf-8') as f:
        f.write('window.DAYS_DATA = ' + json.dumps({"metadata": {"total_days": len(days_data)}, "days": days_data}, ensure_ascii=False) + ';\n')
        f.write('window.ALL_VOCABULARY = ' + json.dumps(all_vocab, ensure_ascii=False) + ';\n')

    with open('/Users/andynguyen/workspace/35-days/wayground_data.js', 'w', encoding='utf-8') as f:
        f.write('window.WAYGROUND_QUIZZES = ' + json.dumps({"games": list(wg_games.values())}, ensure_ascii=False) + ';\n')

    print("\nExtraction & Generation successfully updated!")
    print(f"- days_data.json: {len(days_data)} days, {len(all_vocab)} words, {sum(len(d['exercise_a']['questions']) for d in days_data)} exercise questions")
    print(f"- wayground_quizzes.json: {len(wg_games)} games, {sum(len(g['questions']) for g in wg_games.values())} quiz questions")

if __name__ == '__main__':
    extract_all()
