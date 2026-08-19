from __future__ import annotations

try:
    from aiohttp import web
    from server import PromptServer
except ImportError:
    web = None
    PromptServer = None

try:
    from .candidate_parser import classify_runtime_text
    from .runtime_state import (
        RUNTIME_CANDIDATE_STATE_STORE,
        StaleRuntimeCandidateUpdate,
    )
except ImportError:
    from candidate_parser import classify_runtime_text
    from runtime_state import (
        RUNTIME_CANDIDATE_STATE_STORE,
        StaleRuntimeCandidateUpdate,
    )


if PromptServer is not None and web is not None:

    @PromptServer.instance.routes.post(
        "/prompt_random_choice/runtime_candidate_state"
    )
    async def update_runtime_candidate_state(request):
        try:
            data = await request.json()
            if not isinstance(data, dict):
                raise TypeError("request body must be a JSON object")
            node_kind = data.get("node_kind", "")
            text = data.get("text")
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            status, error = classify_runtime_text(text, is_ex=node_kind == "ex")
            state = RUNTIME_CANDIDATE_STATE_STORE.update(
                state_key=data.get("state_key", ""),
                node_kind=node_kind,
                text=text,
                input_status=status,
                error=error,
                client_id=data.get("client_id", ""),
                client_sequence=data.get("client_sequence"),
            )
            return web.json_response({"ok": True, "state": state.to_dict()})
        except StaleRuntimeCandidateUpdate as exc:
            return web.json_response({"ok": False, "error": str(exc)}, status=409)
        except (TypeError, ValueError) as exc:
            return web.json_response({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:
            return web.json_response(
                {"ok": False, "error": f"Unexpected Runtime state error: {exc}"},
                status=500,
            )

    @PromptServer.instance.routes.get(
        "/prompt_random_choice/runtime_candidate_state/{state_key}"
    )
    async def read_runtime_candidate_state(request):
        state_key = request.match_info.get("state_key", "")
        state = RUNTIME_CANDIDATE_STATE_STORE.get(state_key)
        if state is None:
            return web.json_response(
                {"ok": False, "error": "Runtime candidate state not found"},
                status=404,
            )
        return web.json_response({"ok": True, "state": state.to_dict()})
