import random
import os
import time
import hashlib
import secrets
import re
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
LOCAL_TXT = os.path.join(BASE, "../data/local_tags.txt")

GLOBAL_STATE = {"seed": None}

DEFAULT_APIS = {
    "Safebooru": "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&limit=1",
    "Gelbooru": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1",
    "Konachan": "https://konachan.com/post.json?limit=1",
    "Yande": "https://yande.re/post.json?limit=1",
    "Danbooru": "https://danbooru.donmai.us/posts.json?limit=1&random=true"
}

CONFLICT_GROUPS = [
    {"day", "night"},
    {"smile", "crying"},
    {"open mouth", "closed mouth"},
    {"long hair", "short hair"},
    {"solo", "2girls"},
    {"looking at viewer", "looking away"},
    {"1girl", "1boy"}
]

FALLBACK_TAGS = [
    "blush", "light smile", "hair ornament", "detailed hair",
    "soft lighting", "cinematic lighting", "depth of field",
    "beautiful eyes", "delicate features", "standing", "portrait",
    "upper body", "hair ribbon", "clean background", "outdoors"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def clean_tag(tag):
    tag = tag.strip()
    tag = re.sub(r"[^a-zA-Z0-9_\s\-]", "", tag)
    return tag.lower()

def load_local_txt():
    if os.path.exists(LOCAL_TXT):
        with open(LOCAL_TXT, "r", encoding="utf-8") as f:
            return [clean_tag(t) for t in f.read().split(",") if t.strip()]
    return []

def new_seed():
    raw = f"{time.time_ns()}_{secrets.token_hex(8)}"
    seed = int(hashlib.sha256(raw.encode()).hexdigest(), 16) % (10**12)
    GLOBAL_STATE["seed"] = seed
    return seed

def reset_seed():
    GLOBAL_STATE["seed"] = None
    random.seed(None)
    return "随机种子已重置"

def has_conflict(tag, selected):
    t = clean_tag(tag)
    sel_clean = [clean_tag(s) for s in selected]
    for group in CONFLICT_GROUPS:
        if t in group:
            for s in sel_clean:
                if s in group and s != t:
                    return True
    return False

def fetch_api_tags(api_url):
    for _ in range(2):
        try:
            r = requests.get(api_url, headers=HEADERS, timeout=4)
            r.raise_for_status()
            data = r.json()
            tags = ""
            if isinstance(data, list) and len(data) > 0:
                post = data[0]
                tags = post.get("tag_string") or post.get("tags", "")
            elif isinstance(data, dict) and "post" in data:
                posts = data["post"]
                if isinstance(posts, list) and len(posts) > 0:
                    tags = posts[0].get("tags", "")
            return [clean_tag(t) for t in tags.split() if t]
        except Exception:
            continue
    return []

def build_prompt(
    character,
    blacklist,
    use_api=False,
    api_choice=None,
    custom_api=None,
    use_local=True
):
    seed = new_seed()
    rng = random.Random(seed)
    base_options = [["1girl", "solo"], ["2girls"]]
    result = rng.choice(base_options).copy()

    if character:
        result.append(clean_tag(character))

    pool = []
    if use_api:
        api_list = []
        if custom_api:
            api_list.append(custom_api)
        elif api_choice and api_choice in DEFAULT_APIS:
            api_list.append(DEFAULT_APIS[api_choice])
        else:
            api_list = list(DEFAULT_APIS.values())
        for api_url in api_list:
            tags = fetch_api_tags(api_url)
            if tags:
                pool.extend(tags)
                break

    if use_local:
        pool.extend(load_local_txt())

    if not pool:
        pool = FALLBACK_TAGS.copy()

    pool = list(dict.fromkeys(pool))
    rng.shuffle(pool)

    extra = []
    for t in pool:
        if len(extra) >= 35:
            break
        if not t:
            continue
        if t in result:
            continue
        if has_conflict(t, result + extra):
            continue
        extra.append(t)

    result += extra

    fill_try = 0
    while len(result) < 25 and fill_try < 30:
        cand = rng.choice(FALLBACK_TAGS)
        if cand not in result and not has_conflict(cand, result):
            result.append(cand)
        fill_try += 1

    if blacklist:
        banned = [x.strip().lower() for x in blacklist.split(",")]
        result = [t for t in result if t.lower() not in banned]

    result = list(dict.fromkeys(result))
    result.append("masterpiece")
    result.append("best quality")
    return ", ".join(result)