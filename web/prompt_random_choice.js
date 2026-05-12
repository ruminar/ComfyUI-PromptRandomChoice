import { app } from "../../scripts/app.js";

const EXTENSION_NAME = "ruminar.PromptRandomChoice";
const NODE_NAME = "PromptRandomChoice";

function shorten(text, maxLength = 40) {
    const value = String(text ?? "");
    if (value.length <= maxLength) {
        return value;
    }
    return value.slice(0, maxLength - 3) + "...";
}

app.registerExtension({
    name: EXTENSION_NAME,

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (String(nodeData?.name ?? "") !== NODE_NAME) {
            return;
        }

        const originalOnExecuted = nodeType.prototype.onExecuted;

        nodeType.prototype.onExecuted = function (message) {
            originalOnExecuted?.apply(this, arguments);

            const selected = message?.selected_text?.[0] ?? "";
            if (selected) {
                this.title = `Choice: ${shorten(selected)}`;
            } else {
                this.title = "Prompt Random Choice";
            }

            this.setDirtyCanvas?.(true, true);
            app.graph?.setDirtyCanvas?.(true, true);
        };
    },
});
