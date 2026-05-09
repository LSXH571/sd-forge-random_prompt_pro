import random
import os
import requests

DEFAULT_APIS = {
    "Safebooru": "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}",
    "Gelbooru": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}",
    "Danbooru": "https://danbooru.donmai.us/posts.json?limit={limit}&tags={tags}",
    "Konachan": "https://konachan.com/post.json?limit={limit}&tags={tags}",
    "Yandere": "https://yande.re/post.json?limit={limit}&tags={tags}",
    "Lolibooru": "https://lolibooru.moe/post.json?limit={limit}&tags={tags}",
    "Xbooru": "https://xbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}",
    "Rule35": "https://rule35.xyz/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}"
}

_seed = 0
HEADERS = {"User-Agent":"Mozilla/5.0"}

def reset_seed():
    global _seed
    _seed = random.getrandbits(64)
    random.seed(_seed)

reset_seed()

def fetch_tags_from_api(api_name, custom_api, character):
    tags_list = []
    try:
        tag_str = character.strip() if character.strip() else "random"
        if custom_api.strip():
            url = custom_api.format(limit=30, tags=tag_str)
        else:
            url = DEFAULT_APIS[api_name].format(limit=30, tags=tag_str)
        res = requests.get(url, headers=HEADERS, timeout=8)
        res.raise_for_status()
        data = res.json()
        items = data.get("post", data) if isinstance(data, dict) else data
        if not items:
            return []
        random.shuffle(items)
        for item in items:
            t = item.get("tags") or item.get("tag_string", "")
            if t:
                tags_list.extend([x.strip() for x in t.split(" ") if x.strip()])
    except:
        pass
    return tags_list

def load_local_tags(data_path):
    tags_list = []
    if not os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)
        return tags_list
    for fname in os.listdir(data_path):
        if fname.endswith(".txt"):
            full_path = os.path.join(data_path, fname)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    parts = [t.strip() for t in content.split(",") if t.strip()]
                    tags_list.extend(parts)
            except:
                continue
    return tags_list

def build_prompt(character, blacklist, use_api, api_choice, custom_api, use_local):
    reset_seed()
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
    all_tags = []

    if use_api:
        api_tags = fetch_tags_from_api(api_choice, custom_api, character)
        all_tags.extend(api_tags)

    if use_local:
        local_tags = load_local_tags(data_dir)
        all_tags.extend(local_tags)

    char_tags = [t.strip() for t in character.split(",") if t.strip()]
    all_tags.extend(char_tags)

    black_tags = set([t.strip().lower() for t in blacklist.split(",") if t.strip()])
    filtered = []
    for tag in all_tags:
        if tag.lower() not in black_tags:
            filtered.append(tag)

    filtered = list(set(filtered))
    if len(filtered) == 0:
        return ""

    random.shuffle(filtered)

    person_tags = []
    normal_tags = []
    for t in filtered:
        if any(k in t.lower() for k in ["girl", "boy", "1girl", "2girl", "1boy", "2boy"]):
            person_tags.append(t)
        else:
            normal_tags.append(t)

    person_tags = person_tags[:2]
    need = max(25 - len(person_tags), 0)
    pick_normal = random.sample(normal_tags, min(need, len(normal_tags))) if normal_tags else []
    final = person_tags + pick_normal

    if len(final) < 5:
        default_tags = ["masterpiece", "best quality", "ultra detailed", "beautiful background", "cinematic lighting"]
        final += default_tags

    random.shuffle(final)
    return ", ".join(final)
