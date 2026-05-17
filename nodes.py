import re
import secrets
import time


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
amusement park{ferris wheel|carousel|balloons}"""

INNER_BLOCK_PATTERN = re.compile(r"\{([^{}]*)\}", re.DOTALL)
MAX_EXPAND_STEPS = 64
MAX_EXPANDED_OPTIONS = 4096


def _split_options(options_text: str):
    """
    Split candidates by "|" or actual newline only at brace depth 0.

    Empty candidates are ignored.
    "()" is treated as an explicit empty candidate and becomes "".
    """
    text = str(options_text or "").replace("\r\n", "\n").replace("\r", "\n")

    parts = []
    current = []
    depth = 0

    for char in text:
        if char == "{":
            depth += 1
            current.append(char)
            continue

        if char == "}":
            depth = max(0, depth - 1)
            current.append(char)
            continue

        if depth == 0 and char in ("|", "\n"):
            parts.append("".join(current))
            current = []
            continue

        current.append(char)

    parts.append("".join(current))

    options = []
    for part in parts:
        item = str(part).strip(" \t\r\n,")

        if not item:
            continue

        if item == "()":
            options.append("")
            continue

        options.append(item)

    return options


def _normalize_prompt_fragment(text: str):
    value = str(text or "")
    value = re.sub(r"[\t\r\n]+", " ", value)
    value = re.sub(r"\s*,\s*", ", ", value)
    value = re.sub(r"(,\s*){2,}", ", ", value)
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" \t\r\n,")
    return value


def _safe_text(value: str):
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

    return text or "empty"


def _find_first_brace_block(text: str):
    """Return (open_index, close_index) for the first balanced {...} block."""
    open_index = text.find("{")
    if open_index < 0:
        return None

    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return open_index, index

    # Unmatched "{". Treat it as normal text rather than looping forever.
    return None


def _expand_one_expression(text: str, depth: int = 0):
    """
    Expand one candidate into all final leaf candidates.

    This expands the first outermost {...} block, chooses every top-level
    branch in that block, and then recursively expands only the selected
    branch. This avoids duplicating unrelated branches.
    """
    if depth > MAX_EXPAND_STEPS:
        raise ValueError(
            "PromptRandomChoiceEx expansion exceeded the maximum expansion steps. "
            "Please check nested braces."
        )

    value = str(text or "").strip(" \t\r\n,")
    block = _find_first_brace_block(value)

    if block is None:
        return [_normalize_prompt_fragment(value)]

    open_index, close_index = block
    prefix = value[:open_index]
    body = value[open_index + 1:close_index]
    suffix = value[close_index + 1:]

    branch_options = _split_options(body)
    if not branch_options:
        branch_options = [""]

    expanded = []
    for branch in branch_options:
        if branch:
            candidate = f"{prefix}, {branch}{suffix}"
        else:
            candidate = f"{prefix}{suffix}"

        for item in _expand_one_expression(candidate, depth + 1):
            normalized = _normalize_prompt_fragment(item)
            expanded.append(normalized)

            if len(expanded) > MAX_EXPANDED_OPTIONS:
                raise ValueError(
                    "PromptRandomChoiceEx expanded too many options "
                    f"({len(expanded)} > {MAX_EXPANDED_OPTIONS})."
                )

    return expanded


def _build_expanded_options(options_text: str):
    top_options = _split_options(options_text)
    expanded_options = []

    for option in top_options:
        for expanded in _expand_one_expression(option):
            # Keep "" when it came from explicit (). It allows Ex to return an
            # intentional empty selection just like PromptRandomChoice.
            expanded_options.append(expanded)

            if len(expanded_options) > MAX_EXPANDED_OPTIONS:
                raise ValueError(
                    "PromptRandomChoiceEx expanded too many options "
                    f"({len(expanded_options)} > {MAX_EXPANDED_OPTIONS})."
                )

    return tuple(expanded_options)



class _RandomChoiceStateMixin:
    def __init__(self):
        self._current_choice = None
        self._repeat_index = 0
        self._last_options_key = None
        self._last_change_every = None

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return time.time_ns()

    def _reset_state(self):
        self._current_choice = None
        self._repeat_index = 0
        self._last_options_key = None
        self._last_change_every = None

    def _select_new_choice(self, options):
        self._current_choice = secrets.choice(options)
        self._repeat_index = 1

    def _run_choice(self, options, change_every):
        change_every = max(1, int(change_every))
        options = tuple(options)
        options_key = options

        if not options:
            self._reset_state()
            return "", "empty", "(empty)", 0, change_every

        state_changed = (
            self._last_options_key != options_key
            or self._last_change_every != change_every
            or self._current_choice not in options
        )

        if state_changed or self._current_choice is None:
            self._select_new_choice(options)
        elif self._repeat_index < change_every:
            self._repeat_index += 1
        else:
            self._select_new_choice(options)

        self._last_options_key = options_key
        self._last_change_every = change_every

        selected_text = str(self._current_choice or "")
        selected_text_safe = _safe_text(selected_text)
        selected_text_title = selected_text if selected_text else "(empty)"

        return (
            selected_text,
            selected_text_safe,
            selected_text_title,
            self._repeat_index,
            change_every,
        )


class PromptRandomChoice(_RandomChoiceStateMixin):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "options_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": DEFAULT_OPTIONS_TEXT,
                    },
                ),
                "change_every": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 999999,
                        "step": 1,
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("selected_text", "selected_text_safe")
    FUNCTION = "pick"
    CATEGORY = "utils/prompt"

    def pick(self, options_text, change_every):
        options = _split_options(options_text)
        selected_text, selected_text_safe, selected_text_title, repeat_index, change_every = self._run_choice(
            options,
            change_every,
        )

        return {
            "ui": {
                "selected_text_title": [selected_text_title],
                "repeat_index": [repeat_index],
                "change_every": [change_every],
            },
            "result": (selected_text, selected_text_safe),
        }


class PromptRandomChoiceEx(_RandomChoiceStateMixin):
    def __init__(self):
        super().__init__()
        self._expanded_options_cache_key = None
        self._expanded_options_cache = tuple()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "options_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": DEFAULT_OPTIONS_TEXT_EX,
                    },
                ),
                "change_every": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 999999,
                        "step": 1,
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("selected_text", "selected_text_safe")
    FUNCTION = "pick"
    CATEGORY = "utils/prompt"

    def _get_expanded_options_cached(self, options_text):
        cache_key = str(options_text or "")

        if self._expanded_options_cache_key == cache_key:
            return self._expanded_options_cache

        expanded_options = _build_expanded_options(cache_key)
        self._expanded_options_cache_key = cache_key
        self._expanded_options_cache = expanded_options

        return expanded_options

    def pick(self, options_text, change_every):
        options = self._get_expanded_options_cached(options_text)
        selected_text, selected_text_safe, selected_text_title, repeat_index, change_every = self._run_choice(
            options,
            change_every,
        )

        return {
            "ui": {
                "selected_text_title": [selected_text_title],
                "repeat_index": [repeat_index],
                "change_every": [change_every],
            },
            "result": (selected_text, selected_text_safe),
        }


NODE_CLASS_MAPPINGS = {
    "PromptRandomChoice": PromptRandomChoice,
    "PromptRandomChoiceEx": PromptRandomChoiceEx,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptRandomChoice": "Prompt Random Choice",
    "PromptRandomChoiceEx": "Prompt Random Choice Ex",
}
