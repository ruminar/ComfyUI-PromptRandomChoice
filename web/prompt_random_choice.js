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

            const selectedTitle = message?.selected_text_title?.[0] ?? "(empty)";
            const repeatIndex = Number(message?.repeat_index?.[0] ?? 0);
            const changeEvery = Number(message?.change_every?.[0] ?? 1);

            if (changeEvery <= 1) {
                this.title = `Choice: ${shorten(selectedTitle)}`;
            } else {
                this.title = `Choice: ${shorten(selectedTitle)} (${repeatIndex}/${changeEvery})`;
            }

            this.setDirtyCanvas?.(true, true);
            app.graph?.setDirtyCanvas?.(true, true);
        };
    },
});
