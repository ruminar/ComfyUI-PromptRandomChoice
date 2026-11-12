import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const runtimeSource = readFileSync(
    new URL("../web/runtime_prompt_random_choice.js", import.meta.url),
    "utf8",
);
const titleSource = readFileSync(
    new URL("../web/prompt_random_choice.js", import.meta.url),
    "utf8",
);

function loadTitleExtension() {
    let extension;
    const app = {
        graph: { setDirtyCanvas() {} },
        registerExtension(value) {
            extension = value;
        },
    };
    const executableSource = titleSource.replace(/^import .*;\r?\n/m, "");
    Function("app", executableSource)(app);
    return extension;
}

test("Runtime editor uses resizable DOM widget layout options", () => {
    assert.doesNotMatch(runtimeSource, /domWidget\.computeSize\s*=/);
    assert.match(runtimeSource, /getMinHeight:\s*\(\)\s*=>\s*96/);
    assert.match(runtimeSource, /getHeight:\s*\(\)\s*=>\s*"100%"/);
    assert.match(runtimeSource, /afterResize:/);
    assert.match(runtimeSource, /flex:\s*"1 1 auto"/);
});

test("Runtime editor uses the supported DOM widget compatibility path", () => {
    assert.match(runtimeSource, /node\.widgets\?\.find/);
    assert.match(runtimeSource, /node\.addDOMWidget\(/);
    assert.match(runtimeSource, /"runtime_candidate_editor"/);
    assert.match(runtimeSource, /serialize:\s*false/);
    assert.match(runtimeSource, /widget\.type\s*=\s*"hidden"/);
    assert.match(runtimeSource, /widget\.hidden\s*=\s*true/);
    assert.doesNotMatch(runtimeSource, /useWidgetValueStore/);
});

test("Execution titles are updated through the node onExecuted callback", () => {
    assert.match(
        titleSource,
        /const originalOnExecuted = nodeType\.prototype\.onExecuted/,
    );
    assert.match(
        titleSource,
        /nodeType\.prototype\.onExecuted = function \(message\)/,
    );
    assert.match(titleSource, /originalOnExecuted\?\.apply\(this, arguments\)/);
    assert.match(titleSource, /this\.title\s*=/);
    assert.doesNotMatch(titleSource, /api\.addEventListener\(\s*["']executed/);
    assert.doesNotMatch(titleSource, /Number\(\s*nodeId\s*\)/);
});

test("Execution title callback preserves existing handlers and node names", () => {
    const cases = [
        ["PromptRandomChoice", "Ch: blonde hair (2/3)"],
        ["PromptRandomChoiceEx", "Ex: blonde hair (2/3)"],
        ["RuntimePromptRandomChoice", "Rt: blonde hair (2/3)"],
        ["RuntimePromptRandomChoiceEx", "RtEx: blonde hair (2/3)"],
        ["SafeRandomSeed", "Seed: 123"],
    ];

    for (const [nodeName, expectedTitle] of cases) {
        const extension = loadTitleExtension();
        let originalCalls = 0;
        class NodeType {}
        NodeType.prototype.onExecuted = function () {
            originalCalls += 1;
        };
        extension.beforeRegisterNodeDef(NodeType, { name: nodeName });
        const node = new NodeType();
        node.onExecuted({
            selected_text_title: ["blonde hair"],
            repeat_index: [2],
            change_every: [3],
            seed_title: ["Seed: 123"],
        });

        assert.equal(originalCalls, 1);
        assert.equal(node.title, expectedTitle);
    }
});
