import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
  name: "phazei.PromptStashSaver",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === "PromptStashSaver") {
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);

        // this.size and this.setSize, neither worked, but this does?
        this.computeSize = function () {
          return [210, 220]; // Slightly taller to accommodate new dropdown
        };

        // Find our widgets
        const promptWidget = this.widgets.find((w) => w.name === "prompt_text");
        const saveKeyWidget = this.widgets.find((w) => w.name === "save_as_key");
        const loadSavedWidget = this.widgets.find((w) => w.name === "load_saved");
        const useExternalWidget = this.widgets.find((w) => w.name === "use_external");

        // State tracking
        this.prompts = {};

        // Update widget names/labels - do not change ".name", will break synch with py
        saveKeyWidget.label = "Save name";
        loadSavedWidget.label = "Load named prompt…";
        useExternalWidget.label = "Prompt source";

        const AUTOSAVE = "[autosave] ";
        const NO_VALUE = "[none]";

        const markDirty = () => {
          this.serialize_widgets = true;
          app.graph.setDirtyCanvas(true, true);
        };

        const updateSavedPrompts = (prompts) => {
          this.prompts = prompts || {};
          const keys = Object.keys(this.prompts);
          keys.sort((a, b) => {
            const asA = a.startsWith(AUTOSAVE),
              asB = b.startsWith(AUTOSAVE);
            return asA != asB
              ? asA
                ? 1
                : -1
              : a.localeCompare(b, "en", {
                  sensitivity: "base",
                  numeric: true,
                });
          });
          loadSavedWidget.options.values = [NO_VALUE, ...keys];
          markDirty();
        };

        // Helper function to load a prompt.
        const loadPrompt = (key) => {
          const data = this.prompts[key];
          const hasPrompt = key !== NO_VALUE && !!data.prompt?.length;
          promptWidget.value = hasPrompt ? data.prompt : "";
          saveKeyWidget.value = hasPrompt ? key : "";
          markDirty();
        };

        // Initialize the combo widgets
        if (loadSavedWidget) {
          loadSavedWidget.type = "combo";
          loadSavedWidget.options = loadSavedWidget.options || {};
          loadSavedWidget.options.values = [NO_VALUE];
        }

        useExternalWidget.callback = (useExternal) => {
          if (!useExternal && loadSavedWidget.value !== NO_VALUE) {
            loadPrompt(loadSavedWidget.value);
          }
        };

        // Add watchers for both prompt and key changes
        promptWidget.callback = (value, e) => {
          const savedPromptKey = loadSavedWidget.value;
          if (savedPromptKey !== NO_VALUE && this.data?.prompts) {
            const savedPrompt = this.data.prompts[savedPromptKey];
            // Only clear selection if the prompt text doesn't match the saved value
            if (promptWidget.value !== savedPrompt) {
              loadSavedWidget.value = NO_VALUE;
              markDirty();
            }
          }
        };

        saveKeyWidget.callback = () => {
          saveKeyWidget.value = saveKeyWidget.value.trim();
          const savedPromptKey = loadSavedWidget.value;
          if (savedPromptKey !== NO_VALUE) {
            // Only clear selection if the key doesn't match the selected value
            if (saveKeyWidget.value !== savedPromptKey) {
              loadSavedWidget.value = NO_VALUE;
              markDirty();
            }
          }
        };

        const savePrompt = (keyToSave, promptToSave) => {
          api.fetchApi("/prompt_stash_saver/save", {
            method: "POST",
            body: JSON.stringify({
              key: keyToSave,
              prompt: promptToSave,
              node_id: this.id,
            }),
          });
        };

        // Add Save Button
        this.addWidget("button", "Save prompt", null, () => {
          if (saveKeyWidget.value && promptWidget.value) {
            const keyToSave = saveKeyWidget.value.trim();
            const promptToSave = promptWidget.value;
            savePrompt(keyToSave, promptToSave);
            // Immediately set the value without waiting for server
            loadSavedWidget.value = keyToSave;
          }
        });

        // Add Delete Button
        this.addWidget("button", "Delete selected", null, () => {
          if (loadSavedWidget.value === NO_VALUE) return;
          const deletedItemKey = loadSavedWidget.value;
          const availableKeys = loadSavedWidget.options.values;
          const deletedItemIndex = availableKeys.indexOf(deletedItemKey);
          if (deletedItemIndex === -1) return;
          api
            .fetchApi("/prompt_stash_saver/delete", {
              method: "POST",
              body: JSON.stringify({
                key: deletedItemKey,
                node_id: this.id,
              }),
            })
            .then(() => {
              let newSelection = NO_VALUE;
              const currentList = loadSavedWidget.options.values;
              // Remove the current value from the list in case listener hasn't triggered yet
              const availablePrompts = currentList.filter((v) => v !== deletedItemKey);
              // Select next item based on position
              if (availablePrompts.length > 1) {
                // > 1 because "None" is always present
                if (deletedItemIndex >= availablePrompts.length) {
                  // If we deleted the last item, take the new last item
                  newSelection = availablePrompts[availablePrompts.length - 1];
                } else {
                  // Otherwise take the item that was at this index
                  newSelection = availablePrompts[deletedItemIndex];
                }
              }

              loadSavedWidget.value = newSelection;

              if (newSelection === NO_VALUE) {
                promptWidget.value = "";
                saveKeyWidget.value = "";
              } else {
                // Load the newly selected prompt
                loadPrompt(newSelection);
              }

              markDirty();
            });
        });

        // Handle prompt selection changes
        loadSavedWidget.callback = (value) => {
          loadPrompt(value);
        };

        // Listen for updates from server
        api.addEventListener("prompt-stash-update-all", ({ detail: { prompts } }) => {
          updateSavedPrompts(prompts || {});
        });

        // Listen for text updates from input
        api.addEventListener("prompt-stash-update-prompt", ({ detail: { prompt, node_id } }) => {
          if (String(node_id) !== String(this.id)) return;
          if (!promptWidget) return;
          const wouldBeLost = this.prompts[loadSavedWidget.value]?.prompt !== promptWidget.value;
          if (promptWidget.value?.length && promptWidget.value != prompt && wouldBeLost) {
            const key = `${AUTOSAVE}Node ${node_id}`;
            savePrompt(key, promptWidget.value);
            loadSavedWidget.value = key;
          }
          promptWidget.value = prompt;
          saveKeyWidget.value = "";
          markDirty();
        });

        // Request initial state
        api.fetchApi("/prompt_stash_saver/init", { method: "POST" });
      };
    }
  },
});
