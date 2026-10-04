#!/usr/bin/env python3
"""
clean_exercises.py
Accurately re-extracts Exercise A across all days from data.html,
stripping all bracket corruptions, duplicate spaces around blanks,
orphan trailing brackets in sentences, and residual URLs in word banks.
Updates days_data.json and vocab_data.js.
"""
import json
import re
from bs4 import BeautifulSoup

def clean_txt(s):
    if not s: return ''
    s = s.replace('\xa0', ' ').replace('\u200b', '')
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

def has_vietnamese(text):
    vn_chars = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    return any(c in vn_chars for c in text.lower())

def clean_sentence(sent):
    sent = clean_txt(sent)
    # Normalize blanks: ___ [1] or ___  [1] or ___1 -> ___[1]
    sent = re.sub(r'___\s*\[\s*(\d+)\s*\]', r'___[\1]', sent)
    sent = re.sub(r'___\s*(\d+)', r'___[\1]', sent)
    # Remove trailing brackets, dots, spaces
    sent = re.sub(r'\s*[\.\[\]\(\)]+\s*$', '', sent).strip()
    # If trailing bracket of blank was stripped like ___[\d+
    if re.search(r'___\[\d+$', sent):
        sent += ']'
    if not sent.endswith('?') and not sent.endswith('.'):
        sent += '.'
    return sent

def clean_translation(trans):
    trans = clean_txt(trans)
    # Remove orphan brackets at start and end
    trans = re.sub(r'^\s*\]+\s*', '', trans)
    trans = re.sub(r'\s*\[+\s*$', '', trans)
    trans = re.sub(r'\[\s+', '[', trans)
    trans = re.sub(r'\s+\]', ']', trans)
    # Balance brackets if unbalanced
    open_b = trans.count('[')
    close_b = trans.count(']')
    if open_b > close_b:
        trans += ']' * (open_b - close_b)
    elif close_b > open_b:
        trans = ('[' * (close_b - open_b)) + trans
    return trans

def extract_day_exercises(raw_html):
    if 'VIẾT CÂU' not in raw_html:
        return []
    s_idx = raw_html.find('VIẾT CÂU')
    e_idx = raw_html.find('B. GAME QUIZIZZ')
    if e_idx == -1: e_idx = raw_html.find('B. GAME QUIZIZZ')
    if e_idx == -1: e_idx = raw_html.find('B. GAME')
    if e_idx == -1: e_idx = raw_html.find('B. GAME')
    if e_idx == -1: e_idx = len(raw_html)
    sub = raw_html[s_idx:e_idx]

    matches = list(re.finditer(r'(?:<br\s*/?>|\n|\))\s*(?:<b>)?\s*(?:<br\s*/?>)?\s*(\d+)[\.\)]\s*(?:</b>)?', sub))
    questions = []
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
            clean_l = clean_txt(lh_txt)
            if not clean_l or clean_l.startswith('=>'):
                continue
            if 'B. GAME' in clean_l or 'CƠ CẤU' in clean_l or 'TRẢ BÀI' in clean_l or 'forms.gle' in clean_l:
                break
                
            if '___' in clean_l:
                s_lines.append(clean_l)
            elif has_vietnamese(clean_l):
                t_lines.append(clean_l)
            else:
                # English word bank tokens line
                # Split by 2+ spaces or tabs to preserve multi-word phrases (e.g. PERFORMANCE APPRAISALS)
                toks = [t.strip() for t in re.split(r' {2,}|\t+', lh_txt) if t.strip()]
                for t in toks:
                    if 'http' in t or 'wayground' in t or 'forms.gle' in t:
                        continue
                    c = re.sub(r'^[\[\]\(\)\.\,\;\:\s\d]+|[\[\]\(\)\.\,\;\:\s]+$', '', t).strip()
                    c = re.sub(r'[\[\]]', '', c).strip()
                    if c and len(c) > 1 and not has_vietnamese(c):
                        bank_tokens.append(c)

        sent = clean_sentence(' '.join(s_lines))
        trans = clean_translation(' '.join(t_lines))

        questions.append({
            'number': q_num,
            'sentence': sent,
            'translation': trans,
            'word_bank': bank_tokens
        })
    return questions

def main():
    print("Reading data.html...")
    with open('data.html', 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f, 'html.parser')

    items = soup.find_all('li', class_=lambda c: c and 'tfGBod' in c)
    extracted_by_day = {}
    for item in items:
        title_el = item.find('span', class_=lambda c: c and 'Vu2fZd' in c)
        title = title_el.get_text(strip=True) if title_el else ''
        m = re.search(r'DAY\s*(\d+)', title, re.I)
        if not m: continue
        day_num = int(m.group(1))
        bq = item.find('div', class_='bqKF7d')
        if not bq: continue
        qs = extract_day_exercises(str(bq))
        extracted_by_day[day_num] = qs

    print(f"Extracted exercises for {len(extracted_by_day)} days.")

    # Load days_data.json
    print("Updating days_data.json...")
    with open('days_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Attach verified answer keys for Day 0
    d0_answers = {
        1: ['company', 'holds', 'PERFORMANCE APPRAISALS', 'every'],
        2: ['Those', 'publish', 'APPROVAL', 'author'],
        3: ['library', 'stocks', 'PERIODICALS', 'annually'],
        4: ['approve', 'BUDGET PROPOSAL', 'ALTERNATIVE', 'conference'],
        5: ['RENEWAL', 'entitle', 'a wide variety of', 'benefits', 'innovative', 'effective'],
        6: ['Proceeds', 'fundraising event', 'are intended to', 'support', 'INNITIATIVES', 'bilingual education'],
        7: ['main', 'OBJECTIVE', 'volunteer campaign', 'DISPOSAL OF', 'unnecessary waste', 'alongside', 'plants'],
        8: ['inquiries about', 'warranty policy', 'do not hesitate to contact', 'REPRESENTATIVES', 'extension']
    }

    for day_obj in data['days']:
        d_num = day_obj['day']
        if d_num in extracted_by_day and extracted_by_day[d_num]:
            if 'exercise_a' not in day_obj or not day_obj['exercise_a']:
                day_obj['exercise_a'] = {
                    "title": "VIẾT CÂU HOÀN CHỈNH",
                    "form_url": "",
                    "raw_text": "",
                    "questions": []
                }
            day_obj['exercise_a']['questions'] = extracted_by_day[d_num]
            if d_num == 0:
                for q in day_obj['exercise_a']['questions']:
                    if q['number'] in d0_answers:
                        q['answers'] = d0_answers[q['number']]
        if 'dan_do' in day_obj and day_obj['dan_do']:
            day_obj['dan_do'] = re.sub(r'\s*\n\s*\]', ']', day_obj['dan_do'])

    # Save updated days_data.json
    with open('days_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved days_data.json.")

    # Update vocab_data.js
    print("Updating vocab_data.js...")
    with open('all_vocabulary.json', 'r', encoding='utf-8') as f:
        all_vocab = json.load(f)

    with open('vocab_data.js', 'w', encoding='utf-8') as f:
        f.write('window.DAYS_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')
        f.write('window.ALL_VOCABULARY = ' + json.dumps(all_vocab, ensure_ascii=False) + ';\n')
    print("Saved vocab_data.js.")

    print("Verification:")
    d0_q2 = data['days'][0]['exercise_a']['questions'][1]
    print(f"Day 0 Q2 Sentence   : {d0_q2['sentence']}")
    print(f"Day 0 Q2 Translation: {d0_q2['translation']}")
    print(f"Day 0 Q2 Word Bank  : {d0_q2['word_bank']}")

if __name__ == '__main__':
    main()
