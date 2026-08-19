import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const TARGETS = new Map([
    ["RuntimePromptRandomChoice", "flat"],
    ["RuntimePromptRandomChoiceEx", "ex"],
]);
const LIVE_ROUTE = "/prompt_random_choice/runtime_candidate_state";
const DEBOUNCE_MS = 120;
const MAX_TEXT_BYTES = 512 * 1024;
const LIVE_BACKGROUND_TINT = "rgba(255, 210, 70, 0.1)";

function widgetByName(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function hideSavedWidget(widget) {
    if (!widget) return;
    if (!widget.__promptRandomChoiceHidden) {
        widget.__promptRandomChoiceHidden = true;
        widget.type = "hidden";
        widget.hidden = true;
        widget.disabled = true;
        widget.serialize = true;
        widget.options = { ...(widget.options ?? {}), hidden: true };
        widget.computeSize = () => [0, -4];
        widget.draw = () => {};
    }

    const elements = new Set([
        widget.element,
        widget.inputEl,
        widget.domWidget?.element,
        widget.options?.element,
    ]);
    for (const element of elements) {
        if (!(element instanceof HTMLElement)) continue;
        element.hidden = true;
        element.setAttribute("aria-hidden", "true");
        element.style.setProperty("display", "none", "important");
        element.style.setProperty("visibility", "hidden", "important");
        element.style.setProperty("pointer-events", "none", "important");
    }
}

function randomId(prefix) {
    if (globalThis.crypto?.randomUUID) {
        return `${prefix}-${globalThis.crypto.randomUUID()}`;
    }
    return `${prefix}-${Date.now().toString(36)}-${Math.random()
        .toString(36)
        .slice(2)}`;
}

function nodeClass(node) {
    return node.comfyClass ?? node.type;
}

function nodeKind(node) {
    return TARGETS.get(nodeClass(node));
}

function ensureUniqueStateKey(node) {
    const keyWidget = widgetByName(node, "state_key");
    if (!keyWidget) return "";
    let key = typeof keyWidget.value === "string" ? keyWidget.value.trim() : "";
    const duplicate = (app.graph?._nodes ?? []).some((other) => {
        const otherKey = widgetByName(other, "state_key")?.value;
        return (
            other !== node &&
            TARGETS.has(nodeClass(other)) &&
            typeof otherKey === "string" &&
            otherKey.trim() === key
        );
    });
    if (!key || duplicate) {
        key = randomId(`prc-${nodeKind(node) ?? "runtime"}`);
        keyWidget.value = key;
        node.graph?.change?.();
    }
    return key;
}

function characterCount(value) {
    return Array.from(value).length;
}

function utf8ByteCount(value) {
    return new TextEncoder().encode(value).length;
}

function markWorkflowChanged(node) {
    node.graph?.change?.();
    node.setDirtyCanvas?.(true, false);
}

function setStatus(node, status, detail = "") {
    const ui = node.__promptRandomChoiceRuntimeUI;
    if (!ui) return;
    ui.status.textContent = detail ? `${status} · ${detail}` : status;
    ui.status.dataset.state = status;
    ui.status.style.color =
        status === "HARD ERROR" || status === "SYNC ERROR"
            ? "rgba(255,155,135,0.98)"
            : status === "LIVE"
              ? "rgba(165,255,195,0.95)"
              : status === "SYNCING"
                ? "rgba(255,220,135,0.95)"
                : "rgba(215,215,225,0.9)";
}

function setStateStatus(node, state) {
    const status = state?.input_status;
    if (status === "hard_error") {
        setStatus(node, "HARD ERROR", state?.error ?? "unsupported syntax");
    } else if (status === "incomplete") {
        const revision = Number(state?.revision ?? 0);
        setStatus(
            node,
            "EDITING / SYNTAX INCOMPLETE",
            revision > 0
                ? `using revision ${revision}`
                : "no accepted revision yet",
        );
    } else {
        const revision = Number(state?.revision ?? 0);
        setStatus(node, "LIVE", `revision ${revision}`);
    }
}

function renderCount(node, value) {
    const ui = node.__promptRandomChoiceRuntimeUI;
    if (!ui) return;
    const bytes = utf8ByteCount(value);
    ui.count.textContent =
        bytes > MAX_TEXT_BYTES
            ? `${characterCount(value)} characters · ${bytes} / ${MAX_TEXT_BYTES} bytes`
            : `${characterCount(value)} characters`;
    ui.count.style.color =
        bytes > MAX_TEXT_BYTES
            ? "rgba(255,155,135,0.98)"
            : "rgba(210,210,220,0.72)";
}

function setLocalText(node, value, { sync = false, dirty = false } = {}) {
    const text = typeof value === "string" ? value : String(value ?? "");
    const optionsWidget = widgetByName(node, "options_text");
    const ui = node.__promptRandomChoiceRuntimeUI;
    const changed = Boolean(optionsWidget && optionsWidget.value !== text);
    if (changed) optionsWidget.value = text;
    if (ui && ui.textarea.value !== text) ui.textarea.value = text;
    renderCount(node, text);
    if (dirty && changed) markWorkflowChanged(node);
    if (sync) scheduleSync(node, text);
    return text;
}

function scheduleSync(node, value, immediate = false) {
    const sync = node.__promptRandomChoiceRuntimeSync;
    if (!sync) return;
    sync.desiredText = value;
    clearTimeout(sync.timer);
    if (!sync.inFlight && sync.acknowledgedText === value) return;
    setStatus(node, "EDITING");
    sync.timer = setTimeout(
        () => void flushSync(node),
        immediate ? 0 : DEBOUNCE_MS,
    );
}

async function responseError(response) {
    try {
        const payload = await response.json();
        return payload?.error ?? `${response.status} ${response.statusText}`;
    } catch {
        return `${response.status} ${response.statusText}`;
    }
}

async function flushSync(node) {
    const sync = node.__promptRandomChoiceRuntimeSync;
    if (!sync || sync.composing || sync.inFlight) return;
    clearTimeout(sync.timer);
    sync.timer = null;
    sync.inFlight = true;
    try {
        while (!sync.composing && sync.acknowledgedText !== sync.desiredText) {
            const sentText = sync.desiredText;
            if (utf8ByteCount(sentText) > MAX_TEXT_BYTES) {
                throw new Error(`Text exceeds the ${MAX_TEXT_BYTES}-byte server limit`);
            }
            const sequence = ++sync.nextSequence;
            setStatus(node, "SYNCING");
            const response = await api.fetchApi(LIVE_ROUTE, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    state_key: ensureUniqueStateKey(node),
                    node_kind: nodeKind(node),
                    text: sentText,
                    client_id: sync.clientId,
                    client_sequence: sequence,
                }),
            });
            if (!response.ok) throw new Error(await responseError(response));
            const payload = await response.json();
            sync.acknowledgedText = sentText;
            sync.revision = payload?.state?.revision ?? sync.revision;
            if (sync.desiredText === sentText) setStateStatus(node, payload?.state);
        }
    } catch (error) {
        console.error("[PromptRandomChoice] Runtime sync failed", error);
        setStatus(node, "SYNC ERROR", String(error?.message ?? error));
    } finally {
        sync.inFlight = false;
    }
}

function buildUI(node) {
    const optionsWidget = widgetByName(node, "options_text");
    const keyWidget = widgetByName(node, "state_key");
    if (!optionsWidget || !keyWidget) return;
    hideSavedWidget(optionsWidget);
    hideSavedWidget(keyWidget);
    if (node.__promptRandomChoiceRuntimeUI) return;

    const root = document.createElement("div");
    Object.assign(root.style, {
        display: "flex",
        flexDirection: "column",
        gap: "5px",
        width: "100%",
        height: "100%",
        boxSizing: "border-box",
        padding: "2px 0",
    });
    const textarea = document.createElement("textarea");
    textarea.spellcheck = false;
    textarea.placeholder = "Candidates used when this Runtime node executes";
    Object.assign(textarea.style, {
        width: "100%",
        height: "100%",
        minHeight: "64px",
        flex: "1 1 auto",
        resize: "none",
        boxSizing: "border-box",
        padding: "8px",
        border: "1px solid rgba(255,210,70,0.35)",
        borderRadius: "4px",
        background: "rgba(60,45,0,0.18)",
        color: "inherit",
        fontFamily: "monospace",
        fontSize: "12px",
        lineHeight: "1.35",
    });
    const footer = document.createElement("div");
    Object.assign(footer.style, {
        display: "flex",
        flex: "0 0 auto",
        justifyContent: "space-between",
        gap: "8px",
        padding: "0 2px",
        fontSize: "10px",
    });
    const status = document.createElement("span");
    const count = document.createElement("span");
    count.style.marginLeft = "auto";
    footer.append(status, count);
    root.append(textarea, footer);

    const domWidget = node.addDOMWidget(
        "runtime_candidate_editor",
        "prompt-random-choice-runtime-editor",
        root,
        {
            serialize: false,
            hideOnZoom: false,
            getMinHeight: () => 96,
            getHeight: () => "100%",
            afterResize: () => {
                root.style.height = "100%";
                textarea.style.height = "100%";
            },
            getValue: () => textarea.value,
            setValue: (value) =>
                setLocalText(node, value, { sync: true, dirty: true }),
        },
    );
    node.__promptRandomChoiceRuntimeUI = { root, textarea, status, count, domWidget };
    node.__promptRandomChoiceRuntimeSync = {
        clientId: randomId("client"),
        nextSequence: 0,
        desiredText:
            typeof optionsWidget.value === "string" ? optionsWidget.value : "",
        acknowledgedText: null,
        revision: null,
        composing: false,
        inFlight: false,
        timer: null,
        editVersion: 0,
    };

    const absorb = (event) => event.stopPropagation();
    for (const eventName of [
        "pointerdown",
        "mousedown",
        "mouseup",
        "click",
        "dblclick",
        "keyup",
    ]) {
        textarea.addEventListener(eventName, absorb);
    }
    textarea.addEventListener("keydown", (event) => {
        const save =
            (event.ctrlKey || event.metaKey) &&
            !event.altKey &&
            event.key.toLowerCase() === "s";
        if (!save) {
            event.stopPropagation();
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        scheduleSync(node, textarea.value, true);
        const commandId = event.shiftKey
            ? "Comfy.SaveWorkflowAs"
            : "Comfy.SaveWorkflow";
        app.extensionManager?.command?.execute?.(commandId, {
            errorHandler: (error) =>
                console.error(`[PromptRandomChoice] ${commandId} failed`, error),
        });
    });
    textarea.addEventListener("compositionstart", () => {
        node.__promptRandomChoiceRuntimeSync.composing = true;
        setStatus(node, "EDITING");
    });
    textarea.addEventListener("compositionend", () => {
        const sync = node.__promptRandomChoiceRuntimeSync;
        sync.composing = false;
        sync.editVersion += 1;
        const value = setLocalText(node, textarea.value, { dirty: true });
        scheduleSync(node, value, true);
    });
    textarea.addEventListener("input", () => {
        const sync = node.__promptRandomChoiceRuntimeSync;
        sync.editVersion += 1;
        const value = setLocalText(node, textarea.value, { dirty: true });
        if (sync.composing) sync.desiredText = value;
        else scheduleSync(node, value);
    });
    textarea.addEventListener("blur", () => {
        if (!node.__promptRandomChoiceRuntimeSync.composing) {
            scheduleSync(node, textarea.value, true);
        }
    });
    setLocalText(node, optionsWidget.value);
    setStatus(node, "SYNCING", "checking server state");
}

async function initialiseFromServer(node) {
    buildUI(node);
    if (!node.__promptRandomChoiceRuntimeUI) return;
    if (node.__promptRandomChoiceRuntimeInitialising) {
        return node.__promptRandomChoiceRuntimeInitialising;
    }
    const operation = (async () => {
        const key = ensureUniqueStateKey(node);
        const sync = node.__promptRandomChoiceRuntimeSync;
        const editVersion = sync.editVersion;
        const response = await api.fetchApi(`${LIVE_ROUTE}/${encodeURIComponent(key)}`);
        if (response.status === 404) {
            sync.desiredText = setLocalText(
                node,
                widgetByName(node, "options_text")?.value ?? "",
            );
            sync.acknowledgedText = null;
            await flushSync(node);
            return;
        }
        if (!response.ok) throw new Error(await responseError(response));
        const payload = await response.json();
        const state = payload?.state;
        if (typeof state?.input_text !== "string") {
            throw new Error("Server returned an invalid Runtime candidate state");
        }
        sync.revision = state.revision ?? null;
        sync.acknowledgedText = state.input_text;
        if (sync.editVersion !== editVersion) {
            await flushSync(node);
            return;
        }
        sync.desiredText = state.input_text;
        setLocalText(node, state.input_text, { dirty: true });
        setStateStatus(node, state);
    })()
        .catch((error) => {
            console.error("[PromptRandomChoice] Runtime initialisation failed", error);
            setStatus(node, "SYNC ERROR", String(error?.message ?? error));
        })
        .finally(() => {
            node.__promptRandomChoiceRuntimeInitialising = null;
        });
    node.__promptRandomChoiceRuntimeInitialising = operation;
    return operation;
}

app.registerExtension({
    name: "ruminar.PromptRandomChoice.Runtime",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!TARGETS.has(nodeData.name)) return;
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);
            setTimeout(() => void initialiseFromServer(this), 0);
            return result;
        };
        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = originalOnConfigure?.apply(this, arguments);
            setTimeout(() => void initialiseFromServer(this), 0);
            return result;
        };
        const originalOnDrawBackground = nodeType.prototype.onDrawBackground;
        nodeType.prototype.onDrawBackground = function (ctx) {
            const result = originalOnDrawBackground?.apply(this, arguments);
            if (!this.flags?.collapsed) {
                ctx.save();
                ctx.fillStyle = LIVE_BACKGROUND_TINT;
                ctx.fillRect(
                    1,
                    0,
                    Math.max(0, Number(this.size?.[0] ?? 0) - 2),
                    Math.max(0, Number(this.size?.[1] ?? 0)),
                );
                ctx.restore();
            }
            return result;
        };
    },
});
