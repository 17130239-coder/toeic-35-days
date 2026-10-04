import json
import os
import re

MAPPING_FILE = "quiz_media/media_mapping.json"
if not os.path.exists(MAPPING_FILE):
    print("Mapping file does not exist yet!")
    exit(1)

with open(MAPPING_FILE, "r", encoding="utf-8") as f:
    mapping = json.load(f)

print(f"Loaded mapping with {len(mapping)} URLs.")

with open("wayground_cloned_quizzes.json", "r", encoding="utf-8") as f:
    cloned = json.load(f)

replaced_audio = 0
replaced_image = 0

for g in cloned.values():
    for q in g.get("questions", []):
        if q.get("audio_url") and q["audio_url"] in mapping:
            q["audio_url"] = mapping[q["audio_url"]]
            replaced_audio += 1
        if q.get("image") and q["image"] in mapping:
            q["image"] = mapping[q["image"]]
            replaced_image += 1
        for opt in q.get("options", []):
            if isinstance(opt, dict) and opt.get("image") and opt["image"] in mapping:
                opt["image"] = mapping[opt["image"]]
                replaced_image += 1
        em = q.get("explanation_media", {})
        if em.get("audio") and em["audio"] in mapping:
            em["audio"] = mapping[em["audio"]]
        if em.get("image") and em["image"] in mapping:
            em["image"] = mapping[em["image"]]

with open("wayground_cloned_quizzes.json", "w", encoding="utf-8") as f:
    json.dump(cloned, f, ensure_ascii=False, indent=2)

print(f"Updated wayground_cloned_quizzes.json: {replaced_audio} audios, {replaced_image} images replaced with local paths!")
