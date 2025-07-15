import os
import json

# Exposed by Comfy.
from server import PromptServer
from comfy.comfy_types import CheckLazyMixin

from .data_utils import load_prompts, save_prompt, delete_prompt


class PromptStashSaver(CheckLazyMixin):

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {},
            "optional": {
                "use_external": ("BOOLEAN", {
                    "default": False,
                    "label_on": "‘external’ input",
                    "label_off": "local text box"
                }),
                "external": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "tooltip": "Optional prompt passthrough (when enabled)",
                    "lazy": True
                }),
                "prompt_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter prompt text"
                }),
                "save_as_key": ("STRING", {
                    "default": "",
                    "placeholder": "Enter key to save as"
                }),
                "load_saved": ("COMBO", {
                    "default": "None"
                }),  # Will be populated with actual prompts
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process"
    CATEGORY = "utils"

    # CheckLazyMixin
    def check_lazy_status(self, use_external=False, **kwargs):
        if use_external:
            return ["external"]
        return []

    def process(self,
                use_external=False,
                external="",
                prompt_text="",
                save_as_key="",
                load_saved="None",
                prompt_lists="default",
                unique_id=None,
                extra_pnginfo=None):
        output_text = prompt_text

        if use_external and external is not None:
            output_text = external

            # Send update to frontend to update prompt textarea.
            PromptServer.instance.send_sync("prompt-stash-update-prompt", {"node_id": unique_id, "prompt": external})

            # Handle both list and dict formats of extra_pnginfo.
            workflow = None
            if isinstance(extra_pnginfo, list) and len(extra_pnginfo) > 0:
                workflow = extra_pnginfo[0].get("workflow")
            elif isinstance(extra_pnginfo, dict):
                workflow = extra_pnginfo.get("workflow")

            if workflow:
                node = next((x for x in workflow["nodes"] if str(x["id"]) == str(unique_id)), None)
                if node and "widgets_values" in node:
                    # Update the values in metadata.
                    # Widget (not input) indices, in INPUT_TYPES order.
                    node["widgets_values"][0] = False  # use_external
                    node["widgets_values"][1] = output_text  # prompt_text

        return (output_text,)
