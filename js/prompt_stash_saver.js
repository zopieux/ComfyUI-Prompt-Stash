import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "phazei.PromptStashSaver",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "PromptStashSaver") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);

                // this.size and this.setSize, neither worked, but this does?
                this.computeSize = function() {
                    return [210, 200];
                };

                // Find our widgets
                const promptWidget = this.widgets.find(w => w.name === "prompt_text");
                const saveKeyWidget = this.widgets.find(w => w.name === "save_as_key");
                const loadSavedWidget = this.widgets.find(w => w.name === "load_saved");
                const useInputWidget = this.widgets.find(w => w.name === "use_input_text");
                
                // State tracking
                this.isLoadingPrompt = false;
                this.currentSaveOperation = null;
                
                // Update widget names/labels - do not change ".name", will break synch with py
                saveKeyWidget.label = "Save Name";
                loadSavedWidget.label = "Load Saved";
                useInputWidget.label = "Use ____";

                // Initialize the combo widget
                if (loadSavedWidget) {
                    loadSavedWidget.type = "combo";
                    loadSavedWidget.options = loadSavedWidget.options || {};
                    loadSavedWidget.options.values = ["None"];
                }

                // Add watchers for both prompt and key changes
                promptWidget.callback = (value, e) => {
                    const savedPromptKey = loadSavedWidget.value;
                    if (savedPromptKey !== "None" && this.data?.prompts) {
                        const savedPrompt = this.data.prompts[savedPromptKey];
                        // Only clear selection if the prompt text doesn't match the saved value
                        if (promptWidget.value !== savedPrompt) {
                            loadSavedWidget.value = "None";
                            this.serialize_widgets = true;
                            app.graph.setDirtyCanvas(true, true);
                        }
                    }
                };

                saveKeyWidget.callback = () => {
                    const savedPromptKey = loadSavedWidget.value;
                    if (savedPromptKey !== "None") {
                        // Only clear selection if the key doesn't match the selected value
                        if (saveKeyWidget.value !== savedPromptKey) {
                            loadSavedWidget.value = "None";
                            this.serialize_widgets = true;
                            app.graph.setDirtyCanvas(true, true);
                        }
                    }
                 };

                // Add Save Button
                this.addWidget("button", "Save Prompt", null, () => {
                    if (saveKeyWidget.value && promptWidget.value) {
                        const promptToSave = promptWidget.value;
                        const keyToSave = saveKeyWidget.value;
                        
                        api.fetchApi('/prompt_stash_saver/save', {
                            method: 'POST',
                            body: JSON.stringify({
                                title: keyToSave,
                                prompt: promptToSave,
                                node_id: this.id
                            })
                        });
                        // Immediately set the value without waiting for server
                        loadSavedWidget.value = keyToSave;
                    }
                });

                // Add Delete Button
                this.addWidget("button", "Delete Selected", null, () => {
                    if (loadSavedWidget.value !== "None") {
                        const deletedItemValue = loadSavedWidget.value;
                        // Get current list and find index of deleted item
                        const currentList = loadSavedWidget.options.values;
                        const deletedItemIndex = currentList.indexOf(deletedItemValue);

                        api.fetchApi('/prompt_stash_saver/delete', {
                            method: 'POST',
                            body: JSON.stringify({
                                title: deletedItemValue,
                                node_id: this.id
                            })
                        }).then(() => {
                            let newSelection = "None";
                            const currentList = loadSavedWidget.options.values;

                            // Remove the current value from the list in case listener hasn't triggered yet
                            const availablePrompts = currentList.filter(v => v !== deletedItemValue);

                            // Select next item based on position
                            if (availablePrompts.length > 1) {  // > 1 because "None" is always present
                                if (deletedItemIndex >= availablePrompts.length) {
                                    // If we deleted the last item, take the new last item
                                    newSelection = availablePrompts[availablePrompts.length - 1];
                                } else {
                                    // Otherwise take the item that was at this index
                                    newSelection = availablePrompts[deletedItemIndex];
                                }
                            }

                            loadSavedWidget.value = newSelection;

                            if (newSelection === "None") {
                                promptWidget.value = "";
                                saveKeyWidget.value = "";
                            } else {
                                // Load the newly selected prompt
                                this.loadPrompt(newSelection, promptWidget, saveKeyWidget);
                            }
                            
                            this.serialize_widgets = true;
                            app.graph.setDirtyCanvas(true, true);
                        });
                    }
                });

                // Helper function to load a prompt
                this.loadPrompt = (value, promptWidget, saveKeyWidget) => {
                    if (value === "None") {
                        this.isLoadingPrompt = true;
                        promptWidget.value = "";
                        saveKeyWidget.value = "";
                        this.isLoadingPrompt = false;
                        this.serialize_widgets = true;
                        app.graph.setDirtyCanvas(true, true);
                        return;
                    }
                    
                    api.fetchApi('/prompt_stash_saver/get_prompt', {
                        method: 'POST',
                        body: JSON.stringify({
                            title: value,
                            node_id: this.id
                        })
                    }).then(response => response.json())
                    .then(data => {
                        if (data.prompt) {
                            this.isLoadingPrompt = true;
                            promptWidget.value = data.prompt;
                            saveKeyWidget.value = value;
                            this.isLoadingPrompt = false;
                            this.serialize_widgets = true;
                            app.graph.setDirtyCanvas(true, true);
                        }
                    });
                };

                // Handle prompt selection changes
                loadSavedWidget.callback = (value) => {
                    this.loadPrompt(value, promptWidget, saveKeyWidget);
                };

                // Listen for initial data
                api.addEventListener("prompt-stash-update-all", (event) => {
                    this.data = {prompts: event.detail.prompts};
                    if (loadSavedWidget && event.detail.prompts) {
                        loadSavedWidget.options.values = ["None", ...Object.keys(event.detail.prompts)];
                        this.setDirtyCanvas(true, true);
                    }
                });

                // Listen for text updates from input
                api.addEventListener("prompt-stash-update-prompt", (event) => {
                    if (String(event.detail.node_id) === String(this.id)) {
                        if (promptWidget) {
                            promptWidget.value = event.detail.prompt;
                            saveKeyWidget.value = ""
                            this.serialize_widgets = true;
                            app.graph.setDirtyCanvas(true, true);
                        }
                    }
                });

                // Request initial state
                api.fetchApi('/prompt_stash_saver/init', {
                    method: 'POST',
                    body: JSON.stringify({
                        node_id: this.id
                    })
                });
            };
        }
    }
});