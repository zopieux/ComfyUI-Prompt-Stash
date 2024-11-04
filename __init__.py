from .prompt_stash_saver_node import PromptStashSaver
from .prompt_stash_manager_node import PromptStashManager
from aiohttp import web
from server import PromptServer

@PromptServer.instance.routes.post("/prompt_stash_saver/save")
async def save_prompt(request):
    json_data = await request.json()
    node = PromptStashSaver()
    success = node.save_prompt(json_data["title"], json_data["prompt"], json_data["list_name"], json_data["node_id"])
    return web.json_response({"success": success})

@PromptServer.instance.routes.post("/prompt_stash_saver/delete")
async def delete_prompt(request):
    json_data = await request.json()
    node = PromptStashSaver()
    success = node.delete_prompt(json_data["title"], json_data["list_name"], json_data["node_id"])
    return web.json_response({"success": success})

@PromptServer.instance.routes.post("/prompt_stash_saver/init")
async def init_node(request):
    json_data = await request.json()
    node = PromptStashSaver()
    data = {
        "lists": node.data["lists"]
    }
    return web.json_response(data)

@PromptServer.instance.routes.post("/prompt_stash_saver/get_prompt")
async def get_prompt(request):
    json_data = await request.json()
    node = PromptStashSaver()
    list_name = json_data["list_name"]
    if list_name not in node.data["lists"]:
        list_name = "default"
    prompt = node.data["lists"][list_name].get(json_data["title"], "")
    return web.json_response({"prompt": prompt})

@PromptServer.instance.routes.post("/prompt_stash_saver/add_list")
async def add_list(request):
    json_data = await request.json()
    node = PromptStashManager()
    success = node.add_list(json_data["list_name"])
    return web.json_response({"success": success})

@PromptServer.instance.routes.post("/prompt_stash_saver/delete_list")
async def delete_list(request):
    json_data = await request.json()
    node = PromptStashManager()
    success = node.delete_list(json_data["list_name"])
    return web.json_response({"success": success})

NODE_CLASS_MAPPINGS = {
    "PromptStashSaver": PromptStashSaver,
    "PromptStashManager": PromptStashManager
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptStashSaver": "Prompt Stash Saver",
    "PromptStashManager": "Prompt Stash Manager"
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]