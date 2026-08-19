from __future__ import annotations

import re
import secrets
import time

try:
    from .candidate_parser import (
        UnsupportedCandidateSyntaxError,
        build_ex_pool,
        build_flat_pool,
    )
    from .runtime_state import RUNTIME_CANDIDATE_STATE_STORE
except ImportError:
    from candidate_parser import (
        UnsupportedCandidateSyntaxError,
        build_ex_pool,
        build_flat_pool,
    )
    from runtime_state import RUNTIME_CANDIDATE_STATE_STORE


DEFAULT_OPTIONS_TEXT = """town,
girl's room,
park,
lake,
flower garden,
castle, fortress,
forest,
grasslands,
sea,
snowy landscape,
mountain,
flower field,
starry sky,
coffee shop,"""

DEFAULT_OPTIONS_TEXT_EX = """town
zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
coffee shop{cake|coffee cup}
amusement park{ferris wheel|carousel|balloons}
(){
  white day
  wedding ceremony
  birthday party
}"""

MAX_SAFE_SEED = 2**53 - 1
CATEGORY = "Prompt Random Choice"
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def _safe_text(value: str) -> str:
    text = str(value or "")
    if not text:
        return "empty"
    text = text.replace("\\", "/").replace("/", "_")
    text = re.sub(r'[<>:"|?*\x00-\x1f]', "_", text)
    text = re.sub(r"[\s,]+", "_", text)
    text = text.replace("(", "_").replace(")", "_")
    text = text.replace("{", "_").replace("}", "_")
    text = re.sub(r"_+", "_", text)
    text = text.strip().strip("._-")
    if not text:
        return "empty"
    if text.upper() in WINDOWS_RESERVED_NAMES:
        text = f"_{text}"
    return text[:200].rstrip(" .") or "empty"


def _options_input(default: str) -> tuple[str, dict]:
    return (
        "STRING",
        {"multiline": True, "default": default, "dynamicPrompts": False},
    )


def _change_every_input() -> tuple[str, dict]:
    return (
        "INT",
        {"default": 1, "min": 1, "max": 999999, "step": 1},
    )


def _state_key_input() -> tuple[str, dict]:
    return (
        "STRING",
        {"default": "", "multiline": False, "dynamicPrompts": False},
    )


class _RandomChoiceStateMixin:
    def __init__(self):
        self._current_choice: str | None = None
        self._repeat_index = 0
        self._last_source_key: str | None = None
        self._last_change_every: int | None = None
        self._selected_revision = 0

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return time.time_ns()

    def _reset_selection(self):
        self._current_choice = None
        self._repeat_index = 0
        self._selected_revision = 0

    def _select_new_choice(self, pool, selected_revision: int):
        self._current_choice = pool.choose()
        self._repeat_index = 1
        self._selected_revision = selected_revision

    def _run_choice(
        self,
        pool,
        change_every,
        *,
        source_key: str,
        reset_on_source_change: bool,
        latest_revision: int = 0,
    ):
        change_every = max(1, int(change_every))
        source_changed = self._last_source_key != source_key
        interval_changed = (
            self._last_change_every is not None
            and self._last_change_every != change_every
        )
        needs_selection = self._current_choice is None or interval_changed
        if reset_on_source_change and source_changed:
            needs_selection = True

        if not needs_selection:
            if self._repeat_index < change_every:
                self._repeat_index += 1
            else:
                needs_selection = True

        self._last_source_key = source_key
        self._last_change_every = change_every
        if needs_selection:
            if pool.leaf_count == 0:
                self._reset_selection()
                return "", "empty", "(empty)", 0, change_every, 0
            self._select_new_choice(pool, latest_revision)

        selected_text = str(self._current_choice or "")
        return (
            selected_text,
            _safe_text(selected_text),
            selected_text if selected_text else "(empty)",
            self._repeat_index,
            change_every,
            self._selected_revision,
        )

    @staticmethod
    def _format_result(choice_result, *, latest_revision=0, runtime_status=""):
        (
            selected_text,
            selected_text_safe,
            selected_text_title,
            repeat_index,
            change_every,
            selected_revision,
        ) = choice_result
        return {
            "ui": {
                "selected_text_title": [selected_text_title],
                "repeat_index": [repeat_index],
                "change_every": [change_every],
                "latest_revision": [latest_revision],
                "selected_revision": [selected_revision],
                "runtime_status": [runtime_status],
            },
            "result": (selected_text, selected_text_safe),
        }


class PromptRandomChoice(_RandomChoiceStateMixin):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "options_text": _options_input(DEFAULT_OPTIONS_TEXT),
                "change_every": _change_every_input(),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("selected_text", "selected_text_safe")
    FUNCTION = "pick"
    CATEGORY = CATEGORY

    def pick(self, options_text, change_every):
        source = str(options_text or "")
        result = self._run_choice(
            build_flat_pool(source, allow_force=False),
            change_every,
            source_key=source,
            reset_on_source_change=True,
        )
        return self._format_result(result)


class PromptRandomChoiceEx(_RandomChoiceStateMixin):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "options_text": _options_input(DEFAULT_OPTIONS_TEXT_EX),
                "change_every": _change_every_input(),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("selected_text", "selected_text_safe")
    FUNCTION = "pick"
    CATEGORY = CATEGORY

    def pick(self, options_text, change_every):
        source = str(options_text or "")
        result = self._run_choice(
            build_ex_pool(source, allow_force=False),
            change_every,
            source_key=source,
            reset_on_source_change=True,
        )
        return self._format_result(result)


class _RuntimeRandomChoiceMixin(_RandomChoiceStateMixin):
    IS_EX = False
    STATE_KEY_PREFIX = "prc-runtime"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        default = DEFAULT_OPTIONS_TEXT_EX if cls.IS_EX else DEFAULT_OPTIONS_TEXT
        return {
            "required": {
                "options_text": _options_input(default),
                "change_every": _change_every_input(),
                "state_key": _state_key_input(),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    def _resolve_state_key(self, state_key, unique_id) -> str:
        key = state_key.strip() if isinstance(state_key, str) else ""
        kind = "ex" if self.IS_EX else "flat"
        return key or f"{self.STATE_KEY_PREFIX}-{kind}-{unique_id}"

    def _runtime_source(self, options_text, state_key, unique_id):
        key = self._resolve_state_key(state_key, unique_id)
        state = RUNTIME_CANDIDATE_STATE_STORE.get(key)
        if state is None:
            return str(options_text or ""), 0, "fallback"
        expected_kind = "ex" if self.IS_EX else "flat"
        if state.node_kind != expected_kind:
            raise ValueError("Runtime state belongs to another node kind.")
        if state.input_status == "hard_error":
            raise UnsupportedCandidateSyntaxError(state.error)
        if state.accepted_text is not None:
            return state.accepted_text, state.revision, state.input_status
        return str(options_text or ""), 0, state.input_status

    def pick(self, options_text, change_every, state_key="", unique_id=None):
        source, latest_revision, runtime_status = self._runtime_source(
            options_text, state_key, unique_id
        )
        pool = (
            build_ex_pool(source, allow_force=True)
            if self.IS_EX
            else build_flat_pool(source, allow_force=True)
        )
        result = self._run_choice(
            pool,
            change_every,
            source_key=source,
            reset_on_source_change=False,
            latest_revision=latest_revision,
        )
        return self._format_result(
            result,
            latest_revision=latest_revision,
            runtime_status=runtime_status,
        )


class RuntimePromptRandomChoice(_RuntimeRandomChoiceMixin):
    IS_EX = False
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("selected_text", "selected_text_safe")
    FUNCTION = "pick"
    CATEGORY = CATEGORY


class RuntimePromptRandomChoiceEx(_RuntimeRandomChoiceMixin):
    IS_EX = True
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("selected_text", "selected_text_safe")
    FUNCTION = "pick"
    CATEGORY = CATEGORY


class SafeRandomSeed:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("seed",)
    FUNCTION = "generate"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return secrets.token_hex(16)

    def generate(self):
        seed = secrets.randbelow(MAX_SAFE_SEED + 1)
        return {
            "ui": {
                "seed_title": [f"Seed: {seed}"],
                "seed_value": [str(seed)],
            },
            "result": (seed,),
        }


NODE_CLASS_MAPPINGS = {
    "PromptRandomChoice": PromptRandomChoice,
    "PromptRandomChoiceEx": PromptRandomChoiceEx,
    "RuntimePromptRandomChoice": RuntimePromptRandomChoice,
    "RuntimePromptRandomChoiceEx": RuntimePromptRandomChoiceEx,
    "SafeRandomSeed": SafeRandomSeed,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptRandomChoice": "Prompt Random Choice",
    "PromptRandomChoiceEx": "Prompt Random Choice Ex",
    "RuntimePromptRandomChoice": "Runtime Prompt Random Choice",
    "RuntimePromptRandomChoiceEx": "Runtime Prompt Random Choice Ex",
    "SafeRandomSeed": "Safe Random Seed",
}
