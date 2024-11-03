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
                "text": ("STRING", {"default": "", "defaultInput": True, "tooltip": "Optional input text", "lazy": True}),
                "prompt_text": ("STRING", {"multiline": True, "default": "", "placeholder": "Enter prompt text"}),
                "save_as_key": ("STRING", {"default": "", "placeholder": "Enter key to save as or load"}),
                "use_input_text": ("BOOLEAN", {"default": False, "label_on": "Use Input", "label_off": "Use Prompt"}),
                "load_saved": ("STRING", {"default": "None"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process"
    CATEGORY = "utils"

    def check_lazy_status(self, text=None, prompt_text="", save_as_key="", use_input_text=False, load_saved="None", unique_id=None):
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
                        "prompts": data.get("saved_prompts", {})
                    })
                    return data
            except Exception as e:
                print(f"Error loading prompts: {e}")
        return {"saved_prompts": {}, "node_states": {}}

    def save_data(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def save_prompt(self, save_as_key, prompt, unique_id):
        if not save_as_key or not prompt:
            return False
            
        self.data["saved_prompts"][save_as_key] = prompt
        success = self.save_data()
        
        if success:
            # Notify all nodes of the update
            PromptServer.instance.send_sync("prompt-stash-update-all", {
                "prompts": self.data["saved_prompts"]
            })
        return success

    def delete_prompt(self, save_as_key, unique_id):
        if save_as_key in self.data["saved_prompts"]:
            del self.data["saved_prompts"][save_as_key]
            success = self.save_data()
            
            if success:
                # Notify all nodes of the update
                PromptServer.instance.send_sync("prompt-stash-update-all", {
                    "prompts": self.data["saved_prompts"]
                })
            return success
        return False

    # def save_node_state(self, unique_id, current_prompt, selected_prompt):
    #     self.data["node_states"][unique_id] = {
    #         "current_prompt": current_prompt,
    #         "selected_prompt": selected_prompt
    #     }
    #     return self.save_data()

    # def get_node_state(self, unique_id):
    #     return self.data["node_states"].get(unique_id, {
    #         "current_prompt": "",
    #         "selected_prompt": "None"
    #     })

    def process(self, text="", prompt_text="", save_as_key="", use_input_text=False, load_saved="None", unique_id=None):

        # Handle saving if save_as_key is provided
        # if save_as_key:
        #     self.save_prompt(save_as_key, prompt_text, unique_id)

        # Update the prompt text based on use_input_text toggle
        output_text = prompt_text
        if use_input_text and text is not None:  # Check if text input exists
            output_text = text
            # Send update to frontend to update prompt widget
            PromptServer.instance.send_sync("prompt-stash-update-prompt", {
                "node_id": unique_id,
                "prompt": text
            })

        # Save the current state, probably not needed since ComfyUI auto saves the current state
        # self.save_node_state(unique_id, output_text, load_saved)
        
        return (output_text,)