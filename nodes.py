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


def _choose_from_options_text(options_text: str):
    options = _split_options(options_text)
    if not options:
        return ""
    return secrets.choice(options)


def _normalize_prompt_fragment(text: str):
    """
    Normalize comma-connected prompt fragments after nested expansion.

    This keeps the syntax forgiving:
      zoo{aquarium,{fish|jellyfish}}
    can safely become:
      zoo, aquarium, fish
    even if intermediate expansion produced duplicate commas.
    """
    value = str(text or "")

    # Normalize line breaks/tabs to spaces.
    value = re.sub(r"[\t\r\n]+", " ", value)

    # Normalize spaces around commas.
    value = re.sub(r"\s*,\s*", ", ", value)

    # Collapse duplicate commas.
    value = re.sub(r"(,\s*){2,}", ", ", value)

    # Collapse spaces.
    value = re.sub(r"\s+", " ", value)

    # Trim awkward edges.
    value = value.strip(" \t\r\n,")
    return value


def _expand_nested_choice(text: str):
    """
    Expand nested {...} blocks from the innermost blocks outward.

    Rule:
      - {...} chooses one candidate from inside.
      - Inside candidates are split by top-level "|" or actual newline.
      - The selected nested result is comma-connected to the parent text.
      - "()" is an explicit empty candidate.
      - Unmatched braces are left as-is after the expansion limit is reached.

    Example:
      zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
        -> zoo, animals, birds
        -> zoo, aquarium, jellyfish
    """
    value = str(text or "").strip(" \t\r\n,")

    for _ in range(MAX_EXPAND_STEPS):
        match = INNER_BLOCK_PATTERN.search(value)
        if not match:
            break

        chosen = _choose_from_options_text(match.group(1))
        replacement = f", {chosen}" if chosen else ""
        value = value[:match.start()] + replacement + value[match.end():]

    return _normalize_prompt_fragment(value)


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

    def _pick_candidate(self, options):
        return secrets.choice(options)

    def _select_new_choice(self, options):
        self._current_choice = self._pick_candidate(options)
        self._repeat_index = 1

    def _run_choice(self, options, change_every):
        change_every = max(1, int(change_every))
        options_key = tuple(options)

        if not options:
            self._reset_state()
            return "", "empty", "(empty)", 0, change_every

        state_changed = (
            self._last_options_key != options_key
            or self._last_change_every != change_every
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

    def _pick_candidate(self, options):
        raw_choice = secrets.choice(options)
        return _expand_nested_choice(raw_choice)

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


NODE_CLASS_MAPPINGS = {
    "PromptRandomChoice": PromptRandomChoice,
    "PromptRandomChoiceEx": PromptRandomChoiceEx,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptRandomChoice": "Prompt Random Choice",
    "PromptRandomChoiceEx": "Prompt Random Choice Ex",
}
