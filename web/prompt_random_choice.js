import { app } from "../../scripts/app.js";

const EXTENSION_NAME = "ruminar.PromptRandomChoice";
const NODE_NAMES = new Set([
    "PromptRandomChoice",
    "PromptRandomChoiceEx",
]);

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
        if (!NODE_NAMES.has(String(nodeData?.name ?? ""))) {
            return;
        }

        const nodeName = String(nodeData?.name ?? "");
        const prefix = nodeName === "PromptRandomChoiceEx" ? "Ex" : "Ch";
        const maxTitleLength = nodeName === "PromptRandomChoiceEx" ? 36 : 40;
        const originalOnExecuted = nodeType.prototype.onExecuted;

        nodeType.prototype.onExecuted = function (message) {
            originalOnExecuted?.apply(this, arguments);

            const selectedTitle = message?.selected_text_title?.[0] ?? "(empty)";
            const repeatIndex = Number(message?.repeat_index?.[0] ?? 0);
            const changeEvery = Number(message?.change_every?.[0] ?? 1);

            if (changeEvery <= 1) {
                this.title = `${prefix}: ${shorten(selectedTitle)}`;
            } else {
                this.title = `${prefix}: ${shorten(selectedTitle)} (${repeatIndex}/${changeEvery})`;
            }

            this.setDirtyCanvas?.(true, true);
            app.graph?.setDirtyCanvas?.(true, true);
        };
    },
});
