import time

# Exposed by Comfy.
from server import PromptServer
from comfy.comfy_types import CheckLazyMixin

from . import data_utils


class PromptStashPassthrough(CheckLazyMixin):

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
                    "tooltip": "Optional prompt (passthrough when enabled)",
                    "lazy": True
                }),
                "prompt_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter prompt text"
                }),
                "pause_to_edit": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Yes",
                    "label_off": "No"
                }),
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
                pause_to_edit=False,
                unique_id=None,
                extra_pnginfo=None):
        # Update the prompt text based on use_input_text toggle
        output_text = prompt_text
        if use_external and external is not None:
            output_text = external
            # Send update to frontend to update prompt widget
            PromptServer.instance.send_sync("prompt-stash-update-prompt", {"node_id": unique_id, "prompt": external})

        # Handle pausing if pause_to_edit is enabled
        if pause_to_edit:
            # Set status to paused and notify frontend
            data_utils.status_by_id[unique_id] = "paused"
            PromptServer.instance.send_sync("prompt-stash-enable-continue", {"node_id": unique_id})

            # Wait in loop until continued
            while data_utils.status_by_id.get(unique_id) == "paused":
                time.sleep(0.1)

            # Get the edited text that was sent with the continue signal
            if unique_id in data_utils.edited_text_by_id:
                output_text = data_utils.edited_text_by_id[unique_id]
                del data_utils.edited_text_by_id[unique_id]

            # Clean up status
            if unique_id in data_utils.status_by_id:
                del data_utils.status_by_id[unique_id]

        if (use_external and external is not None) or (pause_to_edit):

            # Handle both list and dict formats of extra_pnginfo
            workflow = None
            if isinstance(extra_pnginfo, list) and len(extra_pnginfo) > 0:
                workflow = extra_pnginfo[0].get("workflow")
            elif isinstance(extra_pnginfo, dict):
                workflow = extra_pnginfo.get("workflow")

            if workflow:
                node = next((x for x in workflow["nodes"] if str(x["id"]) == str(unique_id)), None)
                if node and "widgets_values" in node:
                    # Note: forceInput fields (like 'text') don't count in the widget_values indexing
                    node["widgets_values"][0] = False  # Force use_input_text to False
                    node["widgets_values"][1] = output_text  # Update the prompt text
                    node["widgets_values"][2] = False  # Force pause_to_edit to False

        return (output_text,)
