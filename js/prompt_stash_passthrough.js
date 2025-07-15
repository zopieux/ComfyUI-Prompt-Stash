import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
  name: "phazei.PromptStashPassthrough",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === "PromptStashPassthrough") {
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        onNodeCreated?.apply(this, arguments);

        // Set node size
        this.computeSize = function () {
          if (this.showContinueButton) {
            return [210, 140];
          }
          return [210, 110]; // Slightly taller to accommodate pause toggle and button
        };

        // Find our widgets
        const promptWidget = this.widgets.find((w) => w.name === "prompt_text");
        const useExternalWidget = this.widgets.find((w) => w.name === "use_external");
        const pauseToEditWidget = this.widgets.find((w) => w.name === "pause_to_edit");

        // Update widget labels - do not change ".name", will break synch with py
        useExternalWidget.label = "Prompt source";
        pauseToEditWidget.label = "Pause to edit";

        // Add button state
        this.showContinueButton = false;
        this.buttonArea = null;

        // Store the original onDrawForeground method
        const origDrawForeground = this.onDrawForeground;

        // Override the onDrawForeground method to draw our button
        this.onDrawForeground = function (ctx, graphcanvas) {
          // Call the original method if it exists
          if (origDrawForeground) {
            origDrawForeground.call(this, ctx, graphcanvas);
          }

          // Only draw the button if we should show it
          if (this.showContinueButton) {
            // Button dimensions and position
            const buttonWidth = 100;
            const buttonHeight = 20;
            const x = this.size[0] - buttonWidth - 10;
            const y = 0 - buttonHeight - 5; // Position at bottom of node

            // Button background
            ctx.fillStyle = "#228B22"; // Same green as your original button
            ctx.beginPath();
            ctx.roundRect(x, y, buttonWidth, buttonHeight, 10);
            ctx.fill();

            // Button text - with explicit white color
            ctx.fillStyle = "#FFFFFF"; // White text for better contrast
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.font = "12px Arial";
            ctx.fillText("Continue", x + buttonWidth / 2, y + buttonHeight / 2);

            // Store button coordinates for click detection
            this.buttonArea = {
              x,
              y,
              width: buttonWidth,
              height: buttonHeight,
            };
          }
        };

        // Store the original onMouseDown method
        const origMouseDown = this.onMouseDown;

        // Override the onMouseDown method to detect button clicks
        this.onMouseDown = function (event, pos, graphcanvas) {
          // Check if clicking on our button
          if (this.showContinueButton && this.buttonArea) {
            const { x, y, width, height } = this.buttonArea;

            // Check if click is inside the button area
            if (pos[0] >= x && pos[0] <= x + width && pos[1] >= y && pos[1] <= y + height) {
              // Get current text value
              const text = promptWidget.value;

              // Handle the button click
              api
                .fetchApi("/prompt_stash_passthrough/continue", {
                  method: "POST",
                  body: JSON.stringify({ node_id: this.id, text }),
                })
                .then((response) => {
                  if (response.ok) {
                    this.showContinueButton = false; // Hide button
                    app.graph.setDirtyCanvas(true, true);
                  }
                })
                .catch((error) => {
                  console.error("Error continuing workflow:", error);
                });

              return true; // Handled the event
            }
          }

          // Otherwise, use the original handler
          if (origMouseDown) {
            return origMouseDown.call(this, event, pos, graphcanvas);
          }
          return false;
        };

        // Listen for enable-continue event
        api.addEventListener("prompt-stash-enable-continue", ({ detail: { node_id } }) => {
          if (String(node_id) !== String(this.id)) return;
          this.showContinueButton = true; // Show continue button
          app.graph.setDirtyCanvas(true, true);
        });

        // Listen for text updates from input
        api.addEventListener("prompt-stash-update-prompt", ({ detail: { node_id, prompt } }) => {
          if (String(node_id) !== String(this.id)) return;
          if (!promptWidget) return;
          promptWidget.value = prompt;
          this.serialize_widgets = true;
          app.graph.setDirtyCanvas(true, true);
        });
      };
    }
  },
});
