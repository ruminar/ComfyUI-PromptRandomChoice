# Nodes 2.0 compatibility

## Scope

This repository supports both the Legacy Nodes renderer and Nodes 2.0 without
migrating the Python nodes to the V3 API.

The compatibility boundary is intentionally limited to the existing node
contracts and frontend extension behavior. Node identifiers, input and output
names, widget serialization, and Python execution behavior must remain stable.

## Official implementation checked

The current ComfyUI frontend main branch (package version 1.61.0) was checked
on 2026-11-12:

- Nodes 2.0 uses a Vue-based renderer while the Legacy renderer remains
  selectable.
- Execution results are resolved to the target LiteGraph node and delivered by
  calling `node.onExecuted(output)`.
- Widgets created with `node.addDOMWidget(...)` are registered in the widget
  store used by Nodes 2.0.
- `node.widgets` may be undefined, so reads must remain guarded.
- Legacy `hidden` and `type = "hidden"` widget visibility writes are bridged to
  the current visibility state.

References:

- https://docs.comfy.org/interface/nodes-2
- https://github.com/Comfy-Org/ComfyUI_frontend/blob/main/src/scripts/app.ts
- https://github.com/Comfy-Org/ComfyUI_frontend/blob/main/docs/extensions/widgets-migration.md
- https://github.com/Comfy-Org/ComfyUI_frontend/blob/main/src/scripts/domWidget.ts
- https://github.com/Comfy-Org/ComfyUI_frontend/blob/main/src/lib/litegraph/src/widgets/BaseWidget.ts

## Compatibility decisions

| Concern | Existing implementation | Decision |
| --- | --- | --- |
| Execution title | Wraps each node type's `onExecuted` and assigns `node.title` | Keep unchanged; this is the shared Legacy/Nodes 2.0 path |
| Runtime editor | Uses a uniquely named `addDOMWidget` with `getValue` and `setValue` | Keep unchanged; it participates in the Nodes 2.0 widget store |
| Saved Runtime inputs | Keeps `options_text` and `state_key` serialized while hiding their built-in widgets | Keep unchanged to preserve workflow data and backend inputs |
| Widget lookup | Uses `node.widgets?.find(...)` | Keep unchanged; the undefined case is guarded |
| Runtime background tint | Uses `onDrawBackground` | Retain as a Legacy-only cosmetic decoration; do not write Vue internals or persistent node colors |
| Python node API | Uses `NODE_CLASS_MAPPINGS` and the existing class API | Keep V1 API; no V3 migration |

The Runtime editor, synchronization, selection behavior, inputs, and outputs do
not depend on the Legacy-only background tint.

## Stable workflow contracts

The following node identifiers remain unchanged:

- `PromptRandomChoice`
- `PromptRandomChoiceEx`
- `RuntimePromptRandomChoice`
- `RuntimePromptRandomChoiceEx`
- `SafeRandomSeed`

The existing Python regression tests lock the Runtime input names and all node
mapping identifiers. The frontend regression tests lock the shared
`onExecuted` title path and the supported DOM widget registration path.

## Verification boundary

Automated checks cover Python behavior, mapping and input contracts, JavaScript
syntax, Runtime DOM widget layout options, and the frontend compatibility paths
listed above.

The following require manual verification in a real ComfyUI installation:

- Existing workflow load and execution with Legacy Nodes
- Existing workflow load and execution with Nodes 2.0
- Title updates after execution in both renderers
- Runtime editor display, editing, resize, save/reload, and server sync in both
  renderers
- Switching the same workflow between Legacy Nodes and Nodes 2.0
- Runtime state behavior during queued execution
