import urllib.request
import json
import time
import os
import re
from bs4 import BeautifulSoup

os.makedirs("cloned_games_raw", exist_ok=True)

with open("resolved_hashes.json", "r", encoding="utf-8") as f:
    hashes_map = json.load(f)

with open("permanent_games_clean.json", "r", encoding="utf-8") as f:
    permanent_games = json.load(f)

# Load existing vocab for cross-reference
with open("vocab_data.js", "r", encoding="utf-8") as f:
    vocab_text = f.read()

vocab_dict = {}
for m in re.finditer(r'\{[^{}]*"term":\s*"([^"]+)"[^{}]*"meaning":\s*"([^"]+)"', vocab_text):
    t = m.group(1).strip()
    mean = m.group(2).strip()
    vocab_dict[t.lower()] = t

def clean_html_text(html_str):
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "html.parser")
    # Replace <br> with newline
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text().strip()

def fetch_game_questions(room_hash):
    url = "https://game.quizizz.com/play-api/v4/getQuestions"
    req = urllib.request.Request(
        url,
        data=json.dumps({"roomHash": room_hash}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

all_cloned_quizzes = {}
raw_game_files = {}

print(f"Starting clone of {len(hashes_map)} permanent games...")

for idx, (code, meta) in enumerate(hashes_map.items()):
    r_hash = meta["hash"]
    title = meta["title"]
    print(f"[{idx+1}/30] Fetching game {code} (Hash: {r_hash}) - {title[:40]}...")
    
    cache_file = f"cloned_games_raw/{code}_{r_hash}.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as cf:
            raw_data = json.load(cf)
    else:
        try:
            raw_data = fetch_game_questions(r_hash)
            with open(cache_file, "w", encoding="utf-8") as cf:
                json.dump(raw_data, cf, ensure_ascii=False, indent=2)
            time.sleep(0.3)
        except Exception as e:
            print(f"  Error fetching {code}: {e}")
            continue

    raw_qs = raw_data.get("questions", {})
    parsed_questions = []

    for qid, q in raw_qs.items():
        st = q.get("structure", {})
        q_type = q.get("type", "MCQ")
        
        # Query
        query_obj = st.get("query", {})
        q_text_raw = query_obj.get("text") or ""
        q_text = clean_html_text(q_text_raw)
        
        q_image = None
        q_audio = None
        for m in query_obj.get("media", []):
            if m.get("type") == "image" and not q_image:
                q_image = m.get("url")
            elif m.get("type") == "audio" and not q_audio:
                q_audio = m.get("url")
                
        # Explain
        explain_obj = st.get("explain", {})
        exp_text_raw = explain_obj.get("text") or ""
        exp_text = clean_html_text(exp_text_raw)
        
        exp_audio = None
        exp_image = None
        for m in explain_obj.get("media", []):
            if m.get("type") == "audio" and not exp_audio:
                exp_audio = m.get("url")
            elif m.get("type") == "image" and not exp_image:
                exp_image = m.get("url")

        # Options
        raw_options = st.get("options", [])
        parsed_options = []
        is_image_options = False

        for opt in raw_options:
            opt_text = clean_html_text(opt.get("text") or "")
            opt_media = opt.get("media", [])
            opt_img = None
            for om in opt_media:
                if om.get("type") == "image":
                    opt_img = om.get("url")
                    is_image_options = True
                    break
            
            parsed_options.append({
                "id": opt.get("id") or opt.get("_id"),
                "text": opt_text,
                "image": opt_img
            })

        # Determine Question Format
        if is_image_options:
            q_format = "image_options"
        elif q_type == "BLANK" or len(parsed_options) == 0:
            q_format = "fill_blank"
        elif q_type == "MSQ":
            q_format = "multiple_choice"
        else:
            q_format = "single_choice"

        # Determine Correct Answers
        correct_answers = []
        correct_answer_str = ""

        if is_image_options:
            # For 4-image options, usually option 0 or 1 is the primary key.
            # In Quizizz templates, option 0 or matching index
            correct_answers = [parsed_options[0]["id"] if parsed_options else ""]
            correct_answer_str = "Hình ảnh 1"
        elif q_format == "fill_blank":
            # Extract blank answers from explain or query
            # E.g. "In preparation (n) for S.TH"
            m_bold = re.findall(r'<strong[^>]*>(.*?)</strong>', exp_text_raw, re.I)
            cand = [clean_html_text(b) for b in m_bold if b.strip()]
            if cand:
                correct_answers = cand[:3]
                correct_answer_str = cand[0]
            else:
                words = re.findall(r'[A-Za-z]+(?:\s+[A-Za-z]+)*', exp_text)
                if words:
                    correct_answers = [words[0]]
                    correct_answer_str = words[0]
                else:
                    correct_answers = [exp_text.split()[0] if exp_text else ""]
                    correct_answer_str = correct_answers[0]
        else:
            # Check options against explain text
            matched_opts = []
            for opt in parsed_options:
                otxt = opt["text"].strip()
                if not otxt:
                    continue
                # exact word boundary or phrase match in explain
                if re.search(r'\b' + re.escape(otxt) + r'\b', exp_text, re.I):
                    matched_opts.append(otxt)

            if matched_opts:
                correct_answers = matched_opts
                correct_answer_str = ", ".join(matched_opts)
            else:
                # Fallback: check query or options
                if parsed_options:
                    correct_answers = [parsed_options[0]["text"]]
                    correct_answer_str = parsed_options[0]["text"]

        # Time limit
        time_limit = int(q.get("time", 15000)) // 1000
        if time_limit < 5:
            time_limit = 15

        # Phonetic & Audio text
        m_phon = re.search(r'/(.*?)/', exp_text)
        phonetic = f"/{m_phon.group(1)}/" if m_phon else ""

        parsed_questions.append({
            "id": qid,
            "quizizz_id": qid,
            "question": q_text if q_text else "Chọn đáp án đúng nhất:",
            "raw_html": q_text_raw,
            "question_format": q_format,
            "type": q_type,
            "type_label": "📸 Chọn Tranh" if q_format == "image_options" else "Đa Tuyển" if q_format == "multiple_choice" else "Điền Từ" if q_format == "fill_blank" else "Trắc Nghiệm",
            "image": q_image,
            "audio_url": q_audio or exp_audio,
            "phonetic": phonetic,
            "options": parsed_options,
            "option_strings": [o["text"] for o in parsed_options if o["text"]],
            "correct_answers": correct_answers,
            "correct_answer": correct_answer_str,
            "explanation": exp_text,
            "explanation_html": exp_text_raw,
            "explanation_media": {
                "audio": exp_audio,
                "image": exp_image
            },
            "time_limit": time_limit,
            "points": 1000 if q_format == "single_choice" else 1500
        })

    print(f"  Parsed {len(parsed_questions)} real questions for game {code}")

    # Find matching entry in permanent_games_clean
    perm_entry = next((g for g in permanent_games if g["primary_code"] == code), {})
    
    all_cloned_quizzes[code] = {
        "game_code": code,
        "room_hash": r_hash,
        "title": title,
        "days": perm_entry.get("days", []),
        "requirement": perm_entry.get("requirement", ""),
        "primary_url": f"https://quizizz.com/join?gc={code}",
        "backup_urls": perm_entry.get("backup_urls", []),
        "all_urls": perm_entry.get("all_urls", []),
        "total_questions": len(parsed_questions),
        "questions": parsed_questions
    }

print(f"\nFinished cloning! Total quizzes processed: {len(all_cloned_quizzes)}")
total_q = sum(len(q["questions"]) for q in all_cloned_quizzes.values())
print(f"Total authentic questions cloned: {total_q}")

with open("wayground_cloned_quizzes.json", "w", encoding="utf-8") as f:
    json.dump(all_cloned_quizzes, f, ensure_ascii=False, indent=2)

print("Saved to wayground_cloned_quizzes.json")
