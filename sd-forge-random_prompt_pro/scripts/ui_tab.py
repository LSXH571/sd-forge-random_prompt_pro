import os
import sys
import gradio as gr
from modules import script_callbacks
import random
import time
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from core import build_prompt, reset_seed, DEFAULT_APIS

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
API_CACHE = {}

def clear_api_cache():
    global API_CACHE
    API_CACHE.clear()
    return "API缓存已清理"

def generate(character, blacklist, use_api, api_choice, custom_api, use_local):
    random.seed(time.time_ns())
    reset_seed()
    prompt = build_prompt(character, blacklist, use_api, api_choice, custom_api, use_local)
    if not prompt or len(prompt.strip()) == 0:
        return "1girl, masterpiece, best quality, ultra detailed, beautiful background, cinematic lighting", "⚠ 无可用标签，已使用默认提示词"
    return prompt, "生成成功"

def ranbooru_get_images(num, source, custom_api_url, search_tags):
    try:
        url = ""
        random.seed(time.time_ns())

        if not search_tags.strip():
            search_tags = "random"
        
        if custom_api_url.strip():
            url = custom_api_url.strip().format(limit=num, tags=search_tags)
        else:
            api_map = {
                "Safebooru": "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}",
                "Gelbooru": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}",
                "Danbooru": "https://danbooru.donmai.us/posts.json?limit={limit}&tags={tags}",
                "Konachan": "https://konachan.com/post.json?limit={limit}&tags={tags}",
                "Yandere": "https://yande.re/post.json?limit={limit}&tags={tags}",
                "Lolibooru": "https://lolibooru.moe/post.json?limit={limit}&tags={tags}",
                "Xbooru": "https://xbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}",
                "Rule35": "https://rule35.xyz/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags={tags}"
            }
            url = api_map[source].format(limit=num, tags=search_tags)

        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
        imgs, prompts = [], []

        items = data.get("post", data) if isinstance(data, dict) else data
        if items:
            random.shuffle(items)
        
        for item in items[:num]:
            img_url = item.get("file_url") or item.get("image_url")
            tag = item.get("tags") or item.get("tag_string", "")
            if img_url:
                imgs.append(img_url)
                prompts.append(tag)

        while len(prompts) < 12:
            prompts.append("")

        return imgs, *prompts, f"获取成功 {len(imgs)} 张"
    except Exception as e:
        empty = [""] * 12
        return [], *empty, f"错误：{str(e)[:40]}"

def ranbooru_refresh(num, source, custom_api_url, search_tags):
    random.seed(time.time_ns())
    reset_seed()
    return ranbooru_get_images(num, source, custom_api_url, search_tags)

def on_tab():
    with gr.Blocks() as demo:
        gr.Markdown("## 提示词生成")
        with gr.Tabs():
            with gr.TabItem("提示词生成"):
                character = gr.Textbox(label="角色 / 关键词")
                blacklist = gr.Textbox(label="禁用标签")
                use_api = gr.Checkbox(label="启用API", value=False)
                api_choice = gr.Dropdown(choices=list(DEFAULT_APIS.keys()), label="选择API")
                custom_api = gr.Textbox(label="自定义API")
                use_local = gr.Checkbox(label="启用本地TXT", value=True)
                output = gr.Textbox(label="生成的提示词", lines=3)
                status = gr.Textbox(label="状态")

                with gr.Row():
                    gen_btn = gr.Button("生成")
                    send_btn = gr.Button("发送到Txt2Img")
                    reset_btn = gr.Button("重置种子")
                    clear_cache_btn = gr.Button("清理缓存")

                gen_btn.click(generate, inputs=[character,blacklist,use_api,api_choice,custom_api,use_local], outputs=[output,status])
                send_btn.click(None, inputs=[output], outputs=[status], _js="""(p)=>{const t=gradioApp().querySelector('#txt2img_prompt textarea');if(t){t.value=p;t.dispatchEvent(new Event("input"));}return "✅ 已发送";}""")
                reset_btn.click(reset_seed, outputs=[status])
                clear_cache_btn.click(clear_api_cache, outputs=[status])

            with gr.TabItem("Ranbooru 随机图库"):
                gr.Markdown("### 随机图片获取")
                with gr.Row():
                    pic_num = gr.Slider(minimum=1, maximum=12, value=4, step=1, label="图片数量")
                    pic_src = gr.Dropdown([
                        "Safebooru",
                        "Gelbooru",
                        "Danbooru",
                        "Konachan",
                        "Yandere",
                        "Lolibooru",
                        "Xbooru",
                        "Rule35"
                    ], label="图源", value="Safebooru")
                
                custom_api_rb = gr.Textbox(label="自定义API {limit} {tags}")
                search_tags = gr.Textbox(label="搜索标签（不输入则随机）", value="")
                gallery = gr.Gallery(label="预览", columns=4, height=400)

                with gr.Row():
                    p1 = gr.Textbox(label="图1", lines=2)
                    s1 = gr.Button("发送到Txt2Img")
                with gr.Row():
                    p2 = gr.Textbox(label="图2", lines=2)
                    s2 = gr.Button("发送到Txt2Img")
                with gr.Row():
                    p3 = gr.Textbox(label="图3", lines=2)
                    s3 = gr.Button("发送到Txt2Img")
                with gr.Row():
                    p4 = gr.Textbox(label="图4", lines=2)
                    s4 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p5 = gr.Textbox(label="图5", lines=2)
                    s5 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p6 = gr.Textbox(label="图6", lines=2)
                    s6 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p7 = gr.Textbox(label="图7", lines=2)
                    s7 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p8 = gr.Textbox(label="图8", lines=2)
                    s8 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p9 = gr.Textbox(label="图9", lines=2)
                    s9 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p10 = gr.Textbox(label="图10", lines=2)
                    s10 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p11 = gr.Textbox(label="图11", lines=2)
                    s11 = gr.Button("发送到Txt2Img")
                with gr.Row(visible=False):
                    p12 = gr.Textbox(label="图12", lines=2)
                    s12 = gr.Button("发送到Txt2Img")

                boxes = [p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12]
                btns = [s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12]
                rb_status = gr.Textbox(label="状态")

                for btn, box in zip(btns, boxes):
                    btn.click(None, inputs=[box], outputs=[], _js="""(p)=>{const t=gradioApp().querySelector('#txt2img_prompt textarea');if(t){t.value=p;t.dispatchEvent(new Event("input"));}}""")

                with gr.Row():
                    get_btn = gr.Button("获取图片")
                    refresh_btn = gr.Button("刷新重新抓取")
                    clear_rb_cache = gr.Button("清理API缓存")

                def update_vis(n):
                    res = []
                    for i in range(12):
                        res.append(gr.update(visible=i<n))
                    return res
                pic_num.change(update_vis, inputs=pic_num, outputs=[p1.parent,p2.parent,p3.parent,p4.parent,p5.parent,p6.parent,p7.parent,p8.parent,p9.parent,p10.parent,p11.parent,p12.parent])

                get_btn.click(ranbooru_get_images, inputs=[pic_num,pic_src,custom_api_rb,search_tags], outputs=[gallery,*boxes,rb_status])
                refresh_btn.click(ranbooru_refresh, inputs=[pic_num,pic_src,custom_api_rb,search_tags], outputs=[gallery,*boxes,rb_status])
                clear_rb_cache.click(clear_api_cache, outputs=[rb_status])

    return [(demo, "提示词生成", "prompt_plugin")]

script_callbacks.on_ui_tabs(on_tab)
