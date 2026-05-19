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
amusement park{ferris wheel|carousel|balloons}
(){
  white day
  wedding ceremony
  birthday party
}"""

MAX_EXPAND_STEPS = 64
MAX_EXPANDED_OPTIONS = 4096


def _split_options(options_text: str):
    """
    Split candidates by "|" or actual newline only at brace depth 0.

    Empty candidates are ignored.
    "()" is treated as an explicit empty candidate and becomes "".

    This function is shared by PromptRandomChoice and PromptRandomChoiceEx.
    For Ex, nested blocks such as zoo{animals|birds} stay together when
    splitting the top-level candidate list.
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

        # Empty parts caused by repeated delimiters are ignored.
        if not item:
            continue

        # Explicit empty choice.
        # Example: ()|(full body:0.9)
        if item == "()":
            options.append("")
            continue

        options.append(item)

    return options


def _normalize_prompt_fragment(text: str):
    """
    Normalize comma-connected prompt fragments after nested expansion.

    Standalone "()" fragments are removed here, which enables:
      (){white day|wedding ceremony}
    to become:
      white day
      wedding ceremony

    This also keeps the syntax forgiving:
      zoo{aquarium,{fish|jellyfish}}
    becomes:
      zoo, aquarium, fish
    """
    value = str(text or "")

    # Normalize line breaks/tabs to spaces.
    value = re.sub(r"[\t\r\n]+", " ", value)

    # Normalize spaces around commas.
    value = re.sub(r"\s*,\s*", ",", value)

    # Split comma-connected fragments, remove empty fragments and explicit
    # empty marker fragments, then join them in a prompt-friendly form.
    parts = []
    for part in value.split(","):
        item = part.strip()
        if not item:
            continue
        if item == "()":
            continue
        parts.append(item)

    return ", ".join(parts)


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


def _find_first_block(text: str):
    """
    Return (start, end) for the first balanced {...} block.

    If braces are unmatched, return None and leave the text as literal.
    """
    value = str(text or "")
    start = value.find("{")
    if start < 0:
        return None

    depth = 0
    for index in range(start, len(value)):
        char = value[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, index

    return None


def _expand_all_nested_choices(option_text: str):
    """
    Expand one top-level candidate into all final leaf candidates.

    Ex uses leaf-uniform probability:
      1. expand all nested {...} branches first
      2. choose one item from the expanded leaf list

    Example:
      town|zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}

    becomes:
      town
      zoo, animals, birds
      zoo, animals, penguins
      zoo, aquarium, fish
      zoo, aquarium, jellyfish

    Empty parent groups are supported:
      (){white day|wedding ceremony}

    becomes:
      white day
      wedding ceremony
    """

    def expand_recursive(value: str, depth: int):
        if depth > MAX_EXPAND_STEPS:
            raise ValueError(
                "PromptRandomChoiceEx expansion exceeded the maximum expansion steps. "
                "Please check nested braces."
            )

        block = _find_first_block(value)
        if block is None:
            return [_normalize_prompt_fragment(value)]

        start, end = block
        prefix = value[:start]
        body = value[start + 1:end]
        suffix = value[end + 1:]

        inner_options = _split_options(body)
        if not inner_options:
            inner_options = [""]

        results = []
        for inner in inner_options:
            inner_expanded_options = expand_recursive(inner, depth + 1)

            for inner_expanded in inner_expanded_options:
                replacement = f", {inner_expanded}" if inner_expanded else ""
                candidate = prefix + replacement + suffix
                expanded_candidates = expand_recursive(candidate, depth + 1)

                for expanded in expanded_candidates:
                    results.append(expanded)
                    if len(results) > MAX_EXPANDED_OPTIONS:
                        raise ValueError(
                            "PromptRandomChoiceEx expanded too many options "
                            f"({len(results)} > {MAX_EXPANDED_OPTIONS})."
                        )

        return results

    initial = str(option_text or "").strip(" \t\r\n,")
    return expand_recursive(initial, 0)


def _build_expanded_options(options_text: str):
    top_options = _split_options(options_text)
    expanded_options = []

    for option in top_options:
        for expanded in _expand_all_nested_choices(option):
            # Keep empty results because they can come from explicit ().
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

    def _reset_state(self):
        super()._reset_state()
        # Keep the expansion cache; it depends only on options_text.
        # Selection state and expansion cache have different lifecycles.

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
