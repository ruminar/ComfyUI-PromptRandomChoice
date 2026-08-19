from __future__ import annotations

from dataclasses import dataclass
import re
import secrets


MAX_NESTING_DEPTH = 64
MAX_LEAF_OPTIONS = 4096


class CandidateSyntaxError(ValueError):
    """Base class for candidate-language errors."""


class IncompleteCandidateSyntaxError(CandidateSyntaxError):
    """The text may become valid when the user finishes editing it."""


class UnsupportedCandidateSyntaxError(CandidateSyntaxError):
    """The text is structurally complete but uses unsupported syntax."""


def normalize_prompt_fragment(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"[\t\r\n]+", " ", value)
    value = re.sub(r"\s*,\s*", ",", value)

    parts = []
    for part in value.split(","):
        item = part.strip()
        if item and item != "()":
            parts.append(item)
    return ", ".join(parts)


def split_candidate_parts(
    options_text: str,
    *,
    validate_braces: bool = True,
) -> list[str]:
    """Split top-level candidates while preserving nested child groups."""
    text = str(options_text or "").replace("\r\n", "\n").replace("\r", "\n")
    parts: list[str] = []
    current: list[str] = []
    depth = 0

    for char in text:
        if char == "{":
            depth += 1
            current.append(char)
            continue
        if char == "}":
            if depth == 0 and not validate_braces:
                current.append(char)
                continue
            depth -= 1
            if depth < 0:
                raise IncompleteCandidateSyntaxError(
                    "Unmatched closing brace '}' in candidate text."
                )
            current.append(char)
            continue
        if depth == 0 and char in ("|", "\n"):
            parts.append("".join(current))
            current = []
            continue
        current.append(char)

    if depth and validate_braces:
        raise IncompleteCandidateSyntaxError(
            "Unmatched opening brace '{' in candidate text."
        )
    parts.append("".join(current))
    return [part.strip(" \t\r\n,") for part in parts if part.strip(" \t\r\n,")]


def _decode_leaf(value: str, *, forced: bool) -> str:
    item = value[1:].strip() if forced else value
    if forced and not item:
        raise UnsupportedCandidateSyntaxError(
            "A forced candidate must not be empty. Use '!()' to force an empty string."
        )
    if item == "()":
        return ""
    return item


@dataclass(frozen=True)
class FlatCandidatePool:
    options: tuple[str, ...]
    forced: bool = False

    @property
    def leaf_count(self) -> int:
        return len(self.options)

    def choose(self) -> str:
        if not self.options:
            return ""
        return secrets.choice(self.options)


def build_flat_pool(options_text: str, *, allow_force: bool) -> FlatCandidatePool:
    parts = split_candidate_parts(options_text, validate_braces=False)
    active: list[str] = []
    first_forced: str | None = None

    for part in parts:
        if part.startswith("#"):
            continue
        is_forced = allow_force and part.startswith("!")
        value = _decode_leaf(part, forced=is_forced)
        if is_forced:
            if first_forced is None:
                first_forced = value
            continue
        active.append(value)

    if first_forced is not None:
        return FlatCandidatePool((first_forced,), forced=True)
    return FlatCandidatePool(tuple(active))


def _format_multiple_group_error(candidate: str, position: int) -> str:
    pointer = " " * position + "^"
    return (
        "Unsupported syntax: A candidate may contain only one direct child group.\n\n"
        f"{candidate}\n{pointer}\n\n"
        "Multiple direct child groups are not supported because they create "
        "a Cartesian product during candidate expansion. Use separate Prompt "
        "Random Choice Ex nodes and combine their outputs with String Join."
    )


def _find_direct_group(candidate: str) -> tuple[int, int] | None:
    depth = 0
    start = -1
    first_group: tuple[int, int] | None = None

    for index, char in enumerate(candidate):
        if char == "{":
            if depth == 0:
                if first_group is not None:
                    raise UnsupportedCandidateSyntaxError(
                        _format_multiple_group_error(candidate, index)
                    )
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise IncompleteCandidateSyntaxError(
                    "Unmatched closing brace '}' in candidate text."
                )
            if depth == 0:
                first_group = (start, index)

    if depth:
        raise IncompleteCandidateSyntaxError(
            "Unmatched opening brace '{' in candidate text."
        )
    return first_group


@dataclass(frozen=True)
class ExCandidate:
    prefix: str
    suffix: str
    children: "ExCandidatePool | None" = None

    @property
    def leaf_count(self) -> int:
        return self.children.leaf_count if self.children is not None else 1

    def select_by_index(self, index: int) -> str:
        if self.children is None:
            return normalize_prompt_fragment(self.prefix + self.suffix)
        child = self.children.select_by_index(index)
        replacement = f", {child}" if child else ""
        return normalize_prompt_fragment(self.prefix + replacement + self.suffix)


@dataclass(frozen=True)
class ExCandidatePool:
    candidates: tuple[ExCandidate, ...]
    forced: bool = False

    @property
    def leaf_count(self) -> int:
        return sum(candidate.leaf_count for candidate in self.candidates)

    def select_by_index(self, index: int) -> str:
        if index < 0 or index >= self.leaf_count:
            raise IndexError("leaf candidate index is out of range")
        remaining = index
        for candidate in self.candidates:
            if remaining < candidate.leaf_count:
                return candidate.select_by_index(remaining)
            remaining -= candidate.leaf_count
        raise IndexError("leaf candidate index is out of range")

    def choose(self) -> str:
        count = self.leaf_count
        if count == 0:
            return ""
        return self.select_by_index(secrets.randbelow(count))


def _parse_ex_candidate(
    raw_candidate: str,
    *,
    allow_force: bool,
    depth: int,
) -> ExCandidate:
    if depth > MAX_NESTING_DEPTH:
        raise UnsupportedCandidateSyntaxError(
            f"PromptRandomChoiceEx nesting exceeds {MAX_NESTING_DEPTH} levels."
        )

    forced = allow_force and raw_candidate.startswith("!")
    candidate = raw_candidate[1:].strip() if forced else raw_candidate
    if forced and not candidate:
        raise UnsupportedCandidateSyntaxError(
            "A forced candidate must not be empty. Use '!()' to force an empty string."
        )

    group = _find_direct_group(candidate)
    if group is None:
        leaf = _decode_leaf(candidate, forced=False)
        return ExCandidate(prefix=leaf, suffix="")

    start, end = group
    prefix = candidate[:start]
    suffix = candidate[end + 1 :]
    child_text = candidate[start + 1 : end]
    children = _parse_ex_pool(child_text, allow_force=allow_force, depth=depth + 1)
    if not children.candidates:
        children = ExCandidatePool((ExCandidate(prefix="", suffix=""),))
    return ExCandidate(prefix=prefix, suffix=suffix, children=children)


def _parse_ex_pool(
    options_text: str,
    *,
    allow_force: bool,
    depth: int,
) -> ExCandidatePool:
    parts = split_candidate_parts(options_text)
    active_candidates: list[ExCandidate] = []
    first_forced_candidate: ExCandidate | None = None

    for part in parts:
        if part.startswith("#"):
            continue
        is_forced = allow_force and part.startswith("!")
        candidate = _parse_ex_candidate(
            part,
            allow_force=allow_force,
            depth=depth,
        )
        if is_forced:
            if first_forced_candidate is None:
                first_forced_candidate = candidate
        else:
            active_candidates.append(candidate)

    candidates = (
        (first_forced_candidate,)
        if first_forced_candidate is not None
        else tuple(active_candidates)
    )
    pool = ExCandidatePool(candidates, forced=first_forced_candidate is not None)
    if pool.leaf_count > MAX_LEAF_OPTIONS:
        raise UnsupportedCandidateSyntaxError(
            "PromptRandomChoiceEx contains too many leaf candidates "
            f"({pool.leaf_count} > {MAX_LEAF_OPTIONS})."
        )
    return pool


def build_ex_pool(options_text: str, *, allow_force: bool) -> ExCandidatePool:
    return _parse_ex_pool(options_text, allow_force=allow_force, depth=0)


def classify_runtime_text(options_text: str, *, is_ex: bool) -> tuple[str, str]:
    try:
        if is_ex:
            build_ex_pool(options_text, allow_force=True)
        else:
            build_flat_pool(options_text, allow_force=True)
    except IncompleteCandidateSyntaxError as exc:
        return "incomplete", str(exc)
    except UnsupportedCandidateSyntaxError as exc:
        return "hard_error", str(exc)
    return "valid", ""
