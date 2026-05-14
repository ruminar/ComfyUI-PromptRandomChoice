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


def _split_options(options_text: str):
    text = str(options_text or "")
    parts = re.split(r"\||\r?\n", text)

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


def _safe_text(value: str):
    text = str(value or "")

    if not text:
        return "empty"

    text = text.replace("\\", "/").replace("/", "_")
    text = re.sub(r'[<>:"|?*\x00-\x1f]', "_", text)
    text = re.sub(r"[\s,]+", "_", text)
    text = text.replace("(", "_").replace(")", "_")
    text = re.sub(r"_+", "_", text)
    text = text.strip().strip("._-")

    return text or "empty"


class PromptRandomChoice:
    def __init__(self):
        self._current_choice = None
        self._repeat_index = 0
        self._last_options_key = None
        self._last_change_every = None

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

    def pick(self, options_text, change_every):
        options = _split_options(options_text)
        change_every = max(1, int(change_every))
        options_key = tuple(options)

        if not options:
            self._reset_state()
            return {
                "ui": {
                    "selected_text_title": ["(empty)"],
                    "repeat_index": [0],
                    "change_every": [change_every],
                },
                "result": ("", "empty"),
            }

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

        return {
            "ui": {
                "selected_text_title": [selected_text_title],
                "repeat_index": [self._repeat_index],
                "change_every": [change_every],
            },
            "result": (selected_text, selected_text_safe),
        }


NODE_CLASS_MAPPINGS = {
    "PromptRandomChoice": PromptRandomChoice,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptRandomChoice": "Prompt Random Choice",
}
