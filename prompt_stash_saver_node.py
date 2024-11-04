import os
import json
import folder_paths
from server import PromptServer

class PromptStashSaver:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_file = os.path.join(self.base_dir, "prompt_stash_data.json")
        self.data = self.load_data()

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
            },
            "optional": {
                "use_input_text": ("BOOLEAN", {"default": False, "label_on": "Use Input", "label_off": "Use Prompt"}),
                "text": ("STRING", {"default": "", "defaultInput": True, "tooltip": "Optional input text", "lazy": True}),
                "prompt_text": ("STRING", {"multiline": True, "default": "", "placeholder": "Enter prompt text"}),
                "save_as_key": ("STRING", {"default": "", "placeholder": "Enter key to save as"}),
                "load_saved": ("STRING", {"default": "None"}), # Will be populated with actual prompts
                "prompt_lists": ("STRING", {"default": "default"}), # Will be populated with actual lists
            },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process"
    CATEGORY = "utils"

    def check_lazy_status(self, text="", prompt_text="", save_as_key="", prompt_lists="default", use_input_text=False, load_saved="None", unique_id=None):
        # Only need the text input if use_input_text is True
        needed = []
        if use_input_text:
            needed.append("text")
        return needed

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Broadcast initial data to all nodes
                    PromptServer.instance.send_sync("prompt-stash-update-all", {
                        "lists": data.get("lists", {"default": {}})
                    })
                    return data
            except Exception as e:
                print(f"Error loading prompts: {e}")
        return {"lists": {"default": {}}}

    def save_data(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def save_prompt(self, save_as_key, prompt, list_name, unique_id):
        save_as_key = save_as_key.strip()
        if not save_as_key or not prompt:
            return False
            
        if list_name not in self.data["lists"]:
            list_name = "default"
            
        self.data["lists"][list_name][save_as_key] = prompt
        success = self.save_data()
        
        if success:
            # Notify all nodes of the update
            PromptServer.instance.send_sync("prompt-stash-update-all", {
                "lists": self.data["lists"]
            })
        return success

    def delete_prompt(self, save_as_key, list_name, unique_id):
        if list_name not in self.data["lists"]:
            return False
            
        if save_as_key in self.data["lists"][list_name]:
            del self.data["lists"][list_name][save_as_key]
            success = self.save_data()
            
            if success:
                # Notify all nodes of the update
                PromptServer.instance.send_sync("prompt-stash-update-all", {
                    "lists": self.data["lists"]
                })
            return success
        return False

    def process(self, text="", prompt_text="", save_as_key="", prompt_lists="default", use_input_text=False, load_saved="None", unique_id=None):
        # Update the prompt text based on use_input_text toggle
        output_text = prompt_text
        if use_input_text and text is not None:
            output_text = text
            # Send update to frontend to update prompt widget
            PromptServer.instance.send_sync("prompt-stash-update-prompt", {
                "node_id": unique_id,
                "prompt": text
            })
        
        return (output_text,)