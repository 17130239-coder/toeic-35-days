import json
import re

print("Loading data...")
with open("wayground_cloned_quizzes.json", "r", encoding="utf-8") as f:
    cloned_quizzes = json.load(f)

with open("days_data.json", "r", encoding="utf-8") as f:
    days_data_full = json.load(f)

days_data = days_data_full["days"]

with open("all_vocabulary.json", "r", encoding="utf-8") as f:
    all_vocab = json.load(f)

QUIZIZZ_CORRECT_MEMES = [
    "quiz_media/memes/cm14.jpg",
    "quiz_media/memes/cm16.jpg",
    "quiz_media/memes/cm25.jpg",
    "quiz_media/memes/cm27.jpg",
    "quiz_media/memes/cm33.jpg",
    "quiz_media/memes/cm36.jpg"
]
QUIZIZZ_WRONG_MEMES = [
    "quiz_media/memes/wm8.jpg",
    "quiz_media/memes/wm9.jpg",
    "quiz_media/memes/wm11.jpg",
    "quiz_media/memes/wm12.jpg",
    "quiz_media/memes/wm18.jpg",
    "quiz_media/memes/wm21.jpg"
]

def format_question(raw_q):
    raw_options = raw_q.get("options", [])
    
    # Check if this is an image choice question
    is_image_options = (
        raw_q.get("question_format") == "image_options" or 
        any(bool(o.get("image")) for o in raw_options if isinstance(o, dict))
    )
    
    q_format = raw_q.get("question_format")
    q_type = raw_q.get("type")
    
    if is_image_options:
        img_urls = [o.get("image") for o in raw_options if isinstance(o, dict) and o.get("image")]
        labels = ["Hình A", "Hình B", "Hình C", "Hình D", "Hình E"][:len(img_urls)]
        options = labels
        option_images = img_urls
        has_image_options = True
        q_format = "single_choice"
        type_str = "image_options"
        type_label = "📸 Chọn Tranh"
        correct_answers = ["Hình A"]
        correct_answer = "Hình A"
    elif q_format == "fill_blank" or q_type == "BLANK" or len(raw_options) == 0:
        options = []
        option_images = []
        has_image_options = False
        q_format = "fill_blank"
        type_str = "fill_blank"
        type_label = "Điền Từ"
        c_ans = raw_q.get("correct_answers") or [raw_q.get("correct_answer")]
        correct_answers = [str(a).strip() for a in c_ans if a and str(a).strip()]
        correct_answer = raw_q.get("correct_answer") or (correct_answers[0] if correct_answers else "")
    elif q_format == "multiple_choice" or q_type == "MSQ":
        options = [o.get("text", "") if isinstance(o, dict) else str(o) for o in raw_options]
        option_images = []
        has_image_options = False
        q_format = "multiple_choice"
        type_str = "multiple_choice"
        type_label = "Đa Tuyển"
        correct_answers = [str(a).strip() for a in raw_q.get("correct_answers", []) if a and str(a).strip()]
        correct_answer = ", ".join(correct_answers)
    else:
        options = [o.get("text", "") if isinstance(o, dict) else str(o) for o in raw_options]
        option_images = []
        has_image_options = False
        q_format = "single_choice"
        type_str = "single_choice"
        type_label = "Trắc Nghiệm"
        correct_answers = [str(a).strip() for a in raw_q.get("correct_answers", []) if a and str(a).strip()]
        correct_answer = raw_q.get("correct_answer") or (correct_answers[0] if correct_answers else "")

    # TTS audio text fallback
    audio_text = ""
    for ca in correct_answers:
        if ca and re.match(r'^[A-Za-z\s\'-]+$', ca):
            audio_text = ca
            break
    if not audio_text and raw_q.get("question") and re.match(r'^[A-Za-z\s\'-]+$', raw_q.get("question")):
        audio_text = raw_q.get("question")

    return {
        "id": raw_q.get("id"),
        "quizizz_id": raw_q.get("quizizz_id"),
        "question": raw_q.get("question") or "Chọn đáp án đúng nhất:",
        "raw_html": raw_q.get("raw_html") or raw_q.get("question"),
        "question_format": q_format,
        "type": type_str,
        "type_label": type_label,
        "has_image_options": has_image_options,
        "image": raw_q.get("image") or "",
        "audio_url": raw_q.get("audio_url") or "",
        "audio_text": audio_text,
        "phonetic": raw_q.get("phonetic") or "",
        "options": options,
        "option_images": option_images,
        "raw_options": raw_options,
        "correct_answers": correct_answers,
        "correct_answer": correct_answer,
        "explanation": raw_q.get("explanation") or "",
        "explanation_html": raw_q.get("explanation_html") or "",
        "time_limit": raw_q.get("time_limit", 20),
        "points": raw_q.get("points", 1000)
    }

# Process each cloned quiz
processed_cloned = {}
for code, g in cloned_quizzes.items():
    formatted_questions = [format_question(q) for q in g.get("questions", [])]
    processed_cloned[code] = {
        "game_code": code,
        "room_hash": g.get("room_hash", ""),
        "title": g.get("title", f"Game {code}"),
        "days": g.get("days", []),
        "requirement": g.get("requirement", ""),
        "primary_url": g.get("primary_url", f"https://quizizz.com/join?gc={code}"),
        "backup_urls": g.get("backup_urls", []),
        "all_urls": g.get("all_urls", []),
        "total_questions": len(formatted_questions),
        "questions": formatted_questions
    }

print(f"Processed {len(processed_cloned)} cloned games.")

# Map to days_data
cloned_list = list(processed_cloned.values())
for d in days_data:
    day_num = d["day"]
    matching = [q for q in cloned_list if day_num in q.get("days", [])]
    
    best_quiz = None
    if matching:
        exact = [q for q in matching if len(q.get("days", [])) == 1]
        if exact:
            best_quiz = exact[0]
        else:
            milestone = [q for q in matching if max(q.get("days", [])) == day_num]
            if milestone:
                milestone.sort(key=lambda x: len(x.get("days", [])))
                best_quiz = milestone[0]
            else:
                matching.sort(key=lambda x: len(x.get("days", [])))
                best_quiz = matching[0]

    if not best_quiz and day_num == 0 and "28423016" in processed_cloned:
        best_quiz = processed_cloned["28423016"]

    if best_quiz:
        d["cloned_quiz"] = best_quiz
        if "wayground" not in d:
            d["wayground"] = {}
        d["wayground"]["primary_code"] = best_quiz["game_code"]
        d["wayground"]["primary_url"] = best_quiz["primary_url"]
        d["wayground"]["requirement"] = best_quiz["requirement"]
        d["wayground"]["permanent_title"] = best_quiz["title"]
        d["wayground"]["cloned_questions_count"] = len(best_quiz["questions"])
        d["wayground"]["related_cloned_games"] = [
            {
                "game_code": q["game_code"],
                "title": q["title"],
                "days": q.get("days", []),
                "total_questions": len(q.get("questions", [])),
                "requirement": q.get("requirement", ""),
                "primary_url": q.get("primary_url", "")
            }
            for q in matching if q["game_code"] != best_quiz["game_code"]
        ]

print("Mapped to days_data successfully!")

# Compile wayground games (with backup code aliases)
compiled_games = {}
for code, q in processed_cloned.items():
    compiled_games[code] = {
        "game_code": code,
        "title": q["title"],
        "primary_day": q["days"][-1] if q.get("days") else 0,
        "target_days": q.get("days", []),
        "requirement": q.get("requirement", ""),
        "reward": "TRẢ BÀI LỌT [TOP 3] HAI LẦN LIÊN TIẾP ĐƯỢC THƯỞNG 30K",
        "url": q.get("primary_url", ""),
        "backup_urls": q.get("backup_urls", []),
        "all_urls": q.get("all_urls", []),
        "is_authentic_cloned": True,
        "questions": q["questions"]
    }
    for b_url in q.get("backup_urls", []):
        m = re.search(r'gc=(\d+)', b_url)
        if m:
            b_code = m.group(1)
            if b_code not in compiled_games:
                alias_game = dict(compiled_games[code])
                alias_game["game_code"] = b_code
                alias_game["url"] = b_url
                compiled_games[b_code] = alias_game

# Save updated files
with open("days_data.json", "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "total_days": len(days_data),
            "total_vocabulary": len(all_vocab),
            "total_exercises": sum(len(d["exercise_a"]["questions"]) for d in days_data),
            "total_wayground_games": len(compiled_games)
        },
        "days": days_data
    }, f, ensure_ascii=False, indent=2)

with open("wayground_quizzes.json", "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "total_games": len(compiled_games),
            "total_questions": sum(len(g["questions"]) for g in compiled_games.values()),
            "correct_memes": QUIZIZZ_CORRECT_MEMES,
            "wrong_memes": QUIZIZZ_WRONG_MEMES
        },
        "correct_memes": QUIZIZZ_CORRECT_MEMES,
        "wrong_memes": QUIZIZZ_WRONG_MEMES,
        "games": list(compiled_games.values())
    }, f, ensure_ascii=False, indent=2)

with open("vocab_data.js", "w", encoding="utf-8") as f:
    f.write("window.DAYS_DATA = " + json.dumps({"metadata": {"total_days": len(days_data)}, "days": days_data}, ensure_ascii=False) + ";\n")
    f.write("window.ALL_VOCABULARY = " + json.dumps(all_vocab, ensure_ascii=False) + ";\n")

with open("wayground_data.js", "w", encoding="utf-8") as f:
    f.write("window.WAYGROUND_QUIZZES = " + json.dumps({
        "games": list(compiled_games.values()),
        "correct_memes": QUIZIZZ_CORRECT_MEMES,
        "wrong_memes": QUIZIZZ_WRONG_MEMES
    }, ensure_ascii=False) + ";\n")

print("Generated all datasets successfully!")
