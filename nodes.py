import random
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

    # Split by "|" or actual newlines only.
    # Do not treat literal "\\n" text as a delimiter.
    parts = re.split(r"\||\r?\n", text)

    options = []
    for part in parts:
        item = str(part).strip(" \t\r\n,")
        if item:
            options.append(item)

    return options


class PromptRandomChoice:
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
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_text",)
    FUNCTION = "pick"
    CATEGORY = "utils/prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force execution for every queued run so the random choice changes.
        return time.time_ns()

    def pick(self, options_text):
        options = _split_options(options_text)

        if not options:
            return {
                "ui": {
                    "selected_text": [""],
                },
                "result": ("",),
            }

        # Do not use random.choice here.
        # Some ComfyUI workflows/extensions may reset Python's global random state
        # from the generation seed, which can make random.choice repeat the same
        # index every queued run. secrets.choice uses OS entropy instead.
        selected = secrets.choice(options)
        prompt_text = f",{selected},"

        return {
            "ui": {
                "selected_text": [selected],
            },
            "result": (prompt_text,),
        }


NODE_CLASS_MAPPINGS = {
    "PromptRandomChoice": PromptRandomChoice,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptRandomChoice": "Prompt Random Choice",
}
