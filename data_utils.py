import os
import json
import shutil

def init_data_file(base_dir):
    """Initialize data file if it doesn't exist, using default template if available."""
    data_file = os.path.join(base_dir, "prompt_stash_data.json")
    default_file = os.path.join(base_dir, "default_prompt_stash_data.json")
    
    if not os.path.exists(data_file):
        # Create default data structure
        default_data = {
            "lists": {
                "default": {
                    "Instructions": "📝 Quick Tips:\n\n• 'Use Input' takes text from input node\n• 'Use Prompt' uses text from prompt box (input node won't run)\n\n• Prompt saves only if 'Save Name' is filled\n• Saving to an existing name overwrites it\n\n• Use 'List' dropdown to select prompt lists\n• Manage lists with the Prompt Stash Manager node\n\n• Saved prompts persist between sessions\n• All nodes share the same prompt library",
                }
            }
        }
        
        try:
            # If default template exists, use it instead
            if os.path.exists(default_file):
                shutil.copy2(default_file, data_file)
            else:
                # Otherwise use the minimal default data
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2)
        except Exception as e:
            print(f"Error initializing data file: {e}")
            # If all else fails, create with minimal structure
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({"lists": {"default": {}}}, f, indent=2)

    return data_file