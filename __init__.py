from .prompt_stash_saver_node import PromptStashSaver
from aiohttp import web
from server import PromptServer

@PromptServer.instance.routes.post("/prompt_stash_saver/save")
async def save_prompt(request):
    json_data = await request.json()
    node = PromptStashSaver()
    success = node.save_prompt(json_data["title"], json_data["prompt"], json_data["node_id"])
    return web.json_response({"success": success})

@PromptServer.instance.routes.post("/prompt_stash_saver/delete")
async def delete_prompt(request):
    json_data = await request.json()
    node = PromptStashSaver()
    success = node.delete_prompt(json_data["title"], json_data["node_id"])
    return web.json_response({"success": success})

@PromptServer.instance.routes.post("/prompt_stash_saver/init")
async def init_node(request):
    json_data = await request.json()
    node = PromptStashSaver()
    
    # Create a default empty state if get_node_state doesn't exist or fails
    current_state = {}
    if hasattr(node, 'get_node_state'):
        try:
            current_state = node.get_node_state(json_data["node_id"])
        except:
            pass  # Keep default empty state if anything fails
            
    data = {
        "prompts": node.data["saved_prompts"],
        "current_state": current_state
    }
    return web.json_response(data)

@PromptServer.instance.routes.post("/prompt_stash_saver/get_prompt")
async def get_prompt(request):
    json_data = await request.json()
    node = PromptStashSaver()
    prompt = node.data["saved_prompts"].get(json_data["title"], "")
    return web.json_response({"prompt": prompt})


NODE_CLASS_MAPPINGS = {
    "PromptStashSaver": PromptStashSaver
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptStashSaver": "Prompt Stash Saver"
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]