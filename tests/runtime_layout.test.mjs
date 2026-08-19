import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(
    new URL("../web/runtime_prompt_random_choice.js", import.meta.url),
    "utf8",
);

test("Runtime editor uses resizable DOM widget layout options", () => {
    assert.doesNotMatch(source, /domWidget\.computeSize\s*=/);
    assert.match(source, /getMinHeight:\s*\(\)\s*=>\s*96/);
    assert.match(source, /getHeight:\s*\(\)\s*=>\s*"100%"/);
    assert.match(source, /afterResize:/);
    assert.match(source, /flex:\s*"1 1 auto"/);
});
