import os
import sys
import json
import re
import urllib.request
import urllib.error
import concurrent.futures
import time

AUDIO_DIR = "quiz_media/audio"
IMAGE_DIR = "quiz_media/images"
MEME_DIR = "quiz_media/memes"

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(MEME_DIR, exist_ok=True)

MAPPING_FILE = "quiz_media/media_mapping.json"
mapping = {}
if os.path.exists(MAPPING_FILE):
    try:
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception:
        mapping = {}

# Load cloned quizzes
with open("wayground_cloned_quizzes.json", "r", encoding="utf-8") as f:
    cloned = json.load(f)

audio_urls = set()
image_urls = set()

for g in cloned.values():
    for q in g.get("questions", []):
        if q.get("audio_url"):
            audio_urls.add(q["audio_url"])
        if q.get("image"):
            image_urls.add(q["image"])
        for o in q.get("options", []):
            if isinstance(o, dict) and o.get("image"):
                image_urls.add(o["image"])
        em = q.get("explanation_media", {})
        if em.get("audio"):
            audio_urls.add(em["audio"])
        if em.get("image"):
            image_urls.add(em["image"])

MEMES = [
    "https://cf.quizizz.com/join/img/correct_meme/cm14.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm16.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm25.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm27.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm33.jpg",
    "https://cf.quizizz.com/join/img/correct_meme/cm36.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm8.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm9.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm11.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm12.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm18.jpg",
    "https://cf.quizizz.com/join/img/wrong_meme/wm21.jpg"
]

print(f"Total audio URLs: {len(audio_urls)}")
print(f"Total image URLs: {len(image_urls)}")
print(f"Total meme URLs: {len(MEMES)}")

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def get_clean_name(url):
    clean = url.split("?")[0].split("/")[-1]
    clean = re.sub(r'[^a-zA-Z0-9_-]', '_', clean)
    if not clean:
        import hashlib
        clean = hashlib.md5(url.encode()).hexdigest()[:16]
    return clean

def download_audio(url):
    if url in mapping and os.path.exists(mapping[url]) and os.path.getsize(mapping[url]) > 0:
        return url, mapping[url], True
    
    clean_name = get_clean_name(url)
    if not clean_name.endswith(".mp3"):
        filename = f"{clean_name}.mp3"
    else:
        filename = clean_name
    local_path = os.path.join(AUDIO_DIR, filename)
    
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        mapping[url] = local_path
        return url, local_path, True
        
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                with open(local_path, "wb") as out:
                    out.write(data)
                mapping[url] = local_path
                return url, local_path, True
        except Exception as e:
            if attempt == 2:
                print(f"Failed audio {url}: {e}")
                return url, None, False
            time.sleep(1)

def download_image(url):
    if url in mapping and os.path.exists(mapping[url]) and os.path.getsize(mapping[url]) > 0:
        return url, mapping[url], True
        
    clean_name = get_clean_name(url)
    
    # Try download and detect extension from Content-Type
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                ct = resp.headers.get("Content-Type", "")
                ext = ".jpg"
                if "webp" in ct:
                    ext = ".webp"
                elif "png" in ct:
                    ext = ".png"
                elif "gif" in ct:
                    ext = ".gif"
                elif "jpeg" in ct:
                    ext = ".jpg"
                
                if not any(clean_name.endswith(e) for e in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                    filename = f"{clean_name}{ext}"
                else:
                    filename = clean_name
                
                local_path = os.path.join(IMAGE_DIR, filename)
                data = resp.read()
                with open(local_path, "wb") as out:
                    out.write(data)
                mapping[url] = local_path
                return url, local_path, True
        except Exception as e:
            if attempt == 2:
                print(f"Failed image {url}: {e}")
                return url, None, False
            time.sleep(1)

def download_meme(url):
    if url in mapping and os.path.exists(mapping[url]) and os.path.getsize(mapping[url]) > 0:
        return url, mapping[url], True
    name = url.split("/")[-1]
    local_path = os.path.join(MEME_DIR, name)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            with open(local_path, "wb") as out:
                out.write(data)
            mapping[url] = local_path
            return url, local_path, True
    except Exception as e:
        print(f"Failed meme {url}: {e}")
        return url, None, False

print("Starting concurrent media download (audio, images, memes)...")
t0 = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=35) as ex:
    # Submit audios
    audio_futs = [ex.submit(download_audio, u) for u in audio_urls]
    # Submit images
    image_futs = [ex.submit(download_image, u) for u in image_urls]
    # Submit memes
    meme_futs = [ex.submit(download_meme, u) for u in MEMES]

    done_count = 0
    total_count = len(audio_futs) + len(image_futs) + len(meme_futs)
    all_futs = audio_futs + image_futs + meme_futs
    
    for fut in concurrent.futures.as_completed(all_futs):
        done_count += 1
        if done_count % 100 == 0 or done_count == total_count:
            print(f"Progress: {done_count}/{total_count} ({done_count/total_count*100:.1f}%) in {time.time()-t0:.1f}s")

# Save mapping
with open(MAPPING_FILE, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"All media downloaded! Total mapped: {len(mapping)} files in {time.time()-t0:.1f}s")
