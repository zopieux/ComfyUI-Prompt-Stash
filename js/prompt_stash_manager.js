import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "phazei.PromptStashManager",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "PromptStashManager") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                // Adjust the node size if needed
                this.computeSize = function () {
                    return [230, 110];  // Adjust dimensions as needed
                };

                // Find our widgets
                const newListNameWidget = this.widgets.find(w => w.name === "new_list_name");
                const existingListsWidget = this.widgets.find(w => w.name === "existing_lists");

                // Update widget labels
                newListNameWidget.label = "New List Name";
                existingListsWidget.label = "Existing Lists";

                // Initialize the existingListsWidget as a combo box
                if (existingListsWidget) {
                    existingListsWidget.type = "combo";
                    existingListsWidget.options = existingListsWidget.options || {};
                    existingListsWidget.options.values = ["default"];
                    existingListsWidget.value = "default";
                }

                // State tracking
                this.data = { lists: ["default"] };

                // Add "Add" Button
                this.addWidget("button", "Add", null, () => {
                    const listName = newListNameWidget.value.trim();
                    if (!listName) {
                        // Do not allow empty
                        return;
                    }

                    api.fetchApi('/prompt_stash_saver/add_list', {
                        method: 'POST',
                        body: JSON.stringify({
                            list_name: listName
                        })
                    }).then(response => response.json()).then(data => {
                        if (data.success) {
                            // Clear the newListNameWidget
                            newListNameWidget.value = "";
                            existingListsWidget.value = listName
                            this.serialize_widgets = true;
                            app.graph.setDirtyCanvas(true, true);
                        } else {
                            // Handle failure, maybe display a message
                        }
                    });
                });

                // Add "Delete" Button
                this.addWidget("button", "Delete", null, () => {
                    const currentLists = existingListsWidget.options.values;
                    const selectedList = existingListsWidget.value;
                    if (selectedList && currentLists.length > 1) { //selectedList !== "default") {
                        // Get current list and find index of deleted item
                        const deletedItemIndex = currentLists.indexOf(selectedList);

                        api.fetchApi('/prompt_stash_saver/delete_list', {
                            method: 'POST',
                            body: JSON.stringify({
                                list_name: selectedList
                            })
                        }).then(response => response.json()).then(data => {
                            if (data.success) {
                                let newSelection = "default";

                                // Remove the deleted item from the list in case the listener hasn't updated yet
                                const availableLists = currentLists.filter(v => v !== selectedList);

                                // Select next item based on position
                                if (availableLists.length > 0) {
                                    if (deletedItemIndex >= availableLists.length) {
                                        // If we deleted the last item, select the new last item
                                        newSelection = availableLists[availableLists.length - 1];
                                    } else {
                                        // Otherwise, select the item at the same index
                                        newSelection = availableLists[deletedItemIndex];
                                    }
                                }

                                existingListsWidget.value = newSelection;

                                this.serialize_widgets = true;
                                app.graph.setDirtyCanvas(true, true);
                            } else {
                                // Handle failure, maybe display a message
                            }
                        });
                    } else {
                        // Maybe show a message that "default" cannot be deleted
                    }
                });

                this.addWidget("button", "(Clear All Paused)", null, () => {
                    api.fetchApi('/prompt_stash_passthrough/clear_all', {
                        method: 'POST'
                    });
                });

                // Listen for updates from server
                api.addEventListener("prompt-stash-update-all", (event) => {
                    this.data = event.detail;
                    if (existingListsWidget && event.detail.lists) {
                        // Update lists dropdown
                        const listNames = Object.keys(event.detail.lists);
                        existingListsWidget.options.values = listNames;

                        // If current selected value is no longer in the list, reset to "default"
                        if (!listNames.includes(existingListsWidget.value)) {
                            existingListsWidget.value = "default";
                        }

                        this.serialize_widgets = true;
                        app.graph.setDirtyCanvas(true, true);
                    }
                });

                // Request initial state
                api.fetchApi('/prompt_stash_saver/init', {
                    method: 'POST',
                    body: JSON.stringify({
                        node_id: this.id
                    })
                }).then(response => response.json()).then(data => {
                    this.data = data;
                    if (existingListsWidget && data.lists) {
                        // Update lists dropdown
                        const listNames = Object.keys(data.lists);
                        existingListsWidget.options.values = listNames;

                        // If current selected value is no longer in the list, reset to "default"
                        if (!listNames.includes(existingListsWidget.value)) {
                            existingListsWidget.value = "default";
                        }

                        this.serialize_widgets = true;
                        app.graph.setDirtyCanvas(true, true);
                    }
                });
            };
        }
    }
});
