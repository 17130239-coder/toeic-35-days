import json

with open("wayground_cloned_quizzes.json", "r", encoding="utf-8") as f:
    cloned_quizzes = json.load(f)

with open("days_data.json", "r", encoding="utf-8") as f:
    days_data_full = json.load(f)

days_data = days_data_full["days"]

with open("permanent_games_clean.json", "r", encoding="utf-8") as f:
    perm_games = json.load(f)

with open("all_vocabulary.json", "r", encoding="utf-8") as f:
    all_vocab = json.load(f)

# Memes from Quizizz
QUIZIZZ_CORRECT_MEMES = [
    "https://cf.quizizz.com/join/img/correct_meme/cm14.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm16.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm25.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm27.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm33.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm36.jpg"
]
QUIZIZZ_WRONG_MEMES = [
    "https://cf.quizizz.com/join/img/wrong_meme/wm8.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm9.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm11.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm12.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm18.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm21.jpg"
]

# Map each day to its best authentic cloned quiz
cloned_list = list(cloned_quizzes.values())

for d in days_data:
    day_num = d["day"]
    # Matching quizzes
    matching = [q for q in cloned_list if day_num in q.get("days", [])]
    
    # Priority for best matching quiz
    best_quiz = None
    if matching:
        # Exact single day match
        exact = [q for q in matching if len(q.get("days", [])) == 1]
        if exact:
            best_quiz = exact[0]
        else:
            # Milestone match where this day is the max day in combo
            milestone = [q for q in matching if max(q.get("days", [])) == day_num]
            if milestone:
                milestone.sort(key=lambda x: len(x.get("days", [])))
                best_quiz = milestone[0]
            else:
                matching.sort(key=lambda x: len(x.get("days", [])))
                best_quiz = matching[0]

    # Special handling for Day 0 if not set
    if not best_quiz and day_num == 0:
        if "28423016" in cloned_quizzes:
            best_quiz = cloned_quizzes["28423016"]

    if best_quiz:
        d["cloned_quiz"] = {
            "game_code": best_quiz["game_code"],
            "title": best_quiz["title"],
            "days": best_quiz.get("days", []),
            "requirement": best_quiz.get("requirement", ""),
            "primary_url": best_quiz.get("primary_url", ""),
            "backup_urls": best_quiz.get("backup_urls", []),
            "total_questions": len(best_quiz.get("questions", [])),
            "questions": best_quiz.get("questions", [])
        }
        
        # Update d["wayground"]
        if "wayground" not in d:
            d["wayground"] = {}
        d["wayground"]["primary_code"] = best_quiz["game_code"]
        d["wayground"]["primary_url"] = best_quiz["primary_url"]
        d["wayground"]["requirement"] = best_quiz["requirement"]
        d["wayground"]["permanent_title"] = best_quiz["title"]
        d["wayground"]["cloned_questions_count"] = len(best_quiz["questions"])
        
        # Related combo games
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

print("Mapped authentic cloned quizzes to all 36 days!")

# Compile wayground games list
# 1. Add all 30 authentic cloned quizzes
compiled_games = {}
for code, q in cloned_quizzes.items():
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
    # Add alias for backup codes
    for b_url in q.get("backup_urls", []):
        import re
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

# Write JS bundle files
with open("vocab_data.js", "w", encoding="utf-8") as f:
    f.write("window.DAYS_DATA = " + json.dumps({"metadata": {"total_days": len(days_data)}, "days": days_data}, ensure_ascii=False) + ";\n")
    f.write("window.ALL_VOCABULARY = " + json.dumps(all_vocab, ensure_ascii=False) + ";\n")

with open("wayground_data.js", "w", encoding="utf-8") as f:
    f.write("window.WAYGROUND_QUIZZES = " + json.dumps({
        "games": list(compiled_games.values()),
        "correct_memes": QUIZIZZ_CORRECT_MEMES,
        "wrong_memes": QUIZIZZ_WRONG_MEMES
    }, ensure_ascii=False) + ";\n")

print("Successfully integrated cloned data into days_data.json, vocab_data.js, wayground_quizzes.json, and wayground_data.js!")
print(f"Total compiled games: {len(compiled_games)}")
print(f"Total questions in wayground_data: {sum(len(g['questions']) for g in compiled_games.values())}")
