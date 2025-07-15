from aiohttp import web

# Exposed by Comfy.
from server import PromptServer

from . import data_utils
from .prompt_stash_passthrough_node import PromptStashPassthrough
from .prompt_stash_saver_node import PromptStashSaver


async def broadcast_update(data):
    await PromptServer.instance.send("prompt-stash-update-all", {"prompts": data})


@PromptServer.instance.routes.post("/prompt_stash_saver/init")
async def init_node(request):
    data = data_utils.load_prompts()
    await broadcast_update(data)
    return web.json_response({
        "prompts": data,
    })


@PromptServer.instance.routes.post("/prompt_stash_saver/save")
async def save_prompt(request):
    d = await request.json()
    data = data_utils.save_prompt(key=d["key"], prompt=d["prompt"])
    await broadcast_update(data)
    return web.json_response({"success": True})


@PromptServer.instance.routes.post("/prompt_stash_saver/delete")
async def delete_prompt(request):
    d = await request.json()
    was_found, data = data_utils.delete_prompt(key=d["key"])
    if was_found:
        await broadcast_update(data)
    return web.json_response({"success": was_found})


@PromptServer.instance.routes.post("/prompt_stash_passthrough/continue")
async def continue_node(request):
    d = await request.json()
    node_id = str(d["node_id"])  # Pour one for type consistency!
    edited_text = d.get("text", "")
    if node_id in data_utils.status_by_id:
        data_utils.edited_text_by_id[node_id] = edited_text
        data_utils.status_by_id[node_id] = "continue"
    return web.json_response({"status": "ok"})


# TODO: Add the button to passthrough UI maybe?
@PromptServer.instance.routes.post("/prompt_stash_passthrough/clear_all")
async def clear_all_paused(request):
    data_utils.status_by_id.clear()
    data_utils.edited_text_by_id.clear()
    return web.json_response({"status": "ok"})


NODE_CLASS_MAPPINGS = {
    "PromptStashPassthrough": PromptStashPassthrough,
    "PromptStashSaver": PromptStashSaver,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptStashPassthrough": "Prompt Stash Passthrough",
    "PromptStashSaver": "Prompt Stash Saver",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
