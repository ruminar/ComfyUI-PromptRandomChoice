import math
import unittest
from unittest.mock import patch

from candidate_parser import (
    IncompleteCandidateSyntaxError,
    UnsupportedCandidateSyntaxError,
    build_ex_pool,
    build_flat_pool,
    classify_runtime_text,
)
from nodes import (
    NODE_CLASS_MAPPINGS,
    PromptRandomChoice,
    PromptRandomChoiceEx,
    RuntimePromptRandomChoice,
    RuntimePromptRandomChoiceEx,
    _safe_text,
)
from runtime_state import (
    RUNTIME_CANDIDATE_STATE_STORE,
    RuntimeCandidateStateStore,
    StaleRuntimeCandidateUpdate,
)


def update_runtime_state(
    *, key, text, kind="flat", sequence=1, client="test-client"
):
    status, error = classify_runtime_text(text, is_ex=kind == "ex")
    return RUNTIME_CANDIDATE_STATE_STORE.update(
        state_key=key,
        node_kind=kind,
        text=text,
        input_status=status,
        error=error,
        client_id=client,
        client_sequence=sequence,
    )


class CandidateParserTests(unittest.TestCase):
    def test_flat_comments_and_non_runtime_bang_are_literal(self):
        pool = build_flat_pool("# disabled\n!literal\nnormal", allow_force=False)
        self.assertEqual(pool.options, ("!literal", "normal"))

    def test_runtime_flat_uses_first_forced_candidate(self):
        pool = build_flat_pool("!first\nnormal\n!second", allow_force=True)
        self.assertEqual(pool.options, ("first",))
        self.assertTrue(pool.forced)

    def test_runtime_forced_empty_and_bare_bang(self):
        self.assertEqual(build_flat_pool("normal\n!()", allow_force=True).options, ("",))
        with self.assertRaisesRegex(UnsupportedCandidateSyntaxError, "forced candidate"):
            build_flat_pool("normal\n!", allow_force=True)

    def test_double_bang_removes_only_control_marker(self):
        self.assertEqual(
            build_flat_pool("!!candidate", allow_force=True).options,
            ("!candidate",),
        )

    def test_all_commented_candidates_produce_empty_pool(self):
        self.assertEqual(build_flat_pool("# first\n# second", allow_force=False).leaf_count, 0)
        self.assertEqual(build_ex_pool("# first\n# second", allow_force=False).leaf_count, 0)

    def test_ex_filters_each_level_and_keeps_leaf_uniform_paths(self):
        pool = build_ex_pool("A{x|y|z}\nB{!p|q}", allow_force=True)
        self.assertEqual(pool.leaf_count, 4)
        self.assertEqual(
            [pool.select_by_index(index) for index in range(4)],
            ["A, x", "A, y", "A, z", "B, p"],
        )

    def test_ex_comments_and_first_force_apply_recursively(self):
        pool = build_ex_pool(
            "!A{#x|!y|!z}\n!B{p}",
            allow_force=True,
        )
        self.assertEqual(pool.leaf_count, 1)
        self.assertEqual(pool.select_by_index(0), "A, y")

    def test_runtime_ex_forced_empty_is_a_leaf(self):
        pool = build_ex_pool("A{x|!()|y}", allow_force=True)
        self.assertEqual(pool.leaf_count, 1)
        self.assertEqual(pool.select_by_index(0), "A")

    def test_ex_multiple_parents_and_vertical_nesting(self):
        pool = build_ex_pool(
            "black hair{straight long hair|short cut}\n"
            "blonde hair{long hair{side braid|black ribbon}|wavy long hair}",
            allow_force=False,
        )
        self.assertEqual(
            [pool.select_by_index(index) for index in range(pool.leaf_count)],
            [
                "black hair, straight long hair",
                "black hair, short cut",
                "blonde hair, long hair, side braid",
                "blonde hair, long hair, black ribbon",
                "blonde hair, wavy long hair",
            ],
        )

    def test_non_runtime_ex_keeps_bang_as_text(self):
        pool = build_ex_pool("!A{x|y}", allow_force=False)
        self.assertEqual(
            [pool.select_by_index(index) for index in range(2)],
            ["!A, x", "!A, y"],
        )

    def test_adjacent_direct_groups_are_rejected_before_selection(self):
        with self.assertRaises(UnsupportedCandidateSyntaxError) as context:
            build_ex_pool("scene{day|night}{clear|rain}", allow_force=False)
        message = str(context.exception)
        self.assertIn("only one direct child group", message)
        self.assertIn("Cartesian product", message)
        self.assertIn("^", message)
        self.assertIn("String Join", message)

    def test_incomplete_braces_are_distinguished(self):
        for text in ("A{x|y", "A{x|y}}"):
            with self.subTest(text=text):
                with self.assertRaises(IncompleteCandidateSyntaxError):
                    build_ex_pool(text, allow_force=False)
                self.assertEqual(classify_runtime_text(text, is_ex=True)[0], "incomplete")

    def test_adjacent_groups_classify_as_hard_error(self):
        status, error = classify_runtime_text("scene{day|night}{clear|rain}", is_ex=True)
        self.assertEqual(status, "hard_error")
        self.assertIn("Cartesian product", error)

    def test_hard_error_is_detected_even_in_branch_overridden_by_force(self):
        status, error = classify_runtime_text(
            "!A{x}\nB{day|night}{clear|rain}",
            is_ex=True,
        )
        self.assertEqual(status, "hard_error")
        self.assertIn("Cartesian product", error)


class RuntimeNodeTests(unittest.TestCase):
    def tearDown(self):
        for key in (
            "runtime-hold",
            "runtime-incomplete",
            "runtime-hard-error",
            "runtime-hard-recovery",
            "runtime-empty",
        ):
            RUNTIME_CANDIDATE_STATE_STORE.clear(key)

    def test_edit_does_not_interrupt_change_every(self):
        key = "runtime-hold"
        update_runtime_state(key=key, text="black hair\nblonde hair", sequence=1)
        node = RuntimePromptRandomChoice()
        with patch("candidate_parser.secrets.choice", side_effect=lambda values: values[0]):
            first = node.pick("queued", 3, key, "1")
            update_runtime_state(key=key, text="!blonde hair", sequence=2)
            second = node.pick("queued", 3, key, "1")
            third = node.pick("queued", 3, key, "1")
            fourth = node.pick("queued", 3, key, "1")

        self.assertEqual(first["result"][0], "black hair")
        self.assertEqual(
            [result["result"][0] for result in (second, third, fourth)],
            ["black hair", "black hair", "blonde hair"],
        )
        self.assertEqual(second["ui"]["latest_revision"], [2])
        self.assertEqual(second["ui"]["selected_revision"], [1])
        self.assertEqual(fourth["ui"]["selected_revision"], [2])

    def test_incomplete_uses_last_valid_revision(self):
        key = "runtime-incomplete"
        update_runtime_state(key=key, text="A{x|y}", kind="ex", sequence=1)
        state = update_runtime_state(key=key, text="A{x|y", kind="ex", sequence=2)
        self.assertEqual(state.input_status, "incomplete")
        self.assertEqual(state.accepted_text, "A{x|y}")
        self.assertEqual(state.revision, 1)
        result = RuntimePromptRandomChoiceEx().pick("fallback", 1, key, "1")
        self.assertIn(result["result"][0], {"A, x", "A, y"})
        self.assertEqual(result["ui"]["runtime_status"], ["incomplete"])

    def test_hard_error_never_falls_back(self):
        key = "runtime-hard-error"
        update_runtime_state(key=key, text="A{x|y}", kind="ex", sequence=1)
        state = update_runtime_state(key=key, text="A{x|y}{p|q}", kind="ex", sequence=2)
        self.assertEqual(state.input_status, "hard_error")
        self.assertEqual(state.accepted_text, "A{x|y}")
        with self.assertRaisesRegex(UnsupportedCandidateSyntaxError, "Cartesian product"):
            RuntimePromptRandomChoiceEx().pick("fallback", 3, key, "1")

    def test_runtime_nodes_always_invalidate_cache(self):
        self.assertTrue(math.isnan(RuntimePromptRandomChoice.IS_CHANGED()))
        self.assertTrue(math.isnan(RuntimePromptRandomChoiceEx.IS_CHANGED()))

    def test_hard_error_clears_after_valid_text_is_accepted(self):
        key = "runtime-hard-recovery"
        update_runtime_state(key=key, text="A{x}", kind="ex", sequence=1)
        update_runtime_state(key=key, text="A{x}{y}", kind="ex", sequence=2)
        recovered = update_runtime_state(key=key, text="B{z}", kind="ex", sequence=3)
        self.assertEqual(recovered.input_status, "valid")
        self.assertEqual(recovered.revision, 2)
        self.assertEqual(
            RuntimePromptRandomChoiceEx().pick("fallback", 1, key, "1")["result"][0],
            "B, z",
        )

    def test_accepted_empty_text_overrides_queued_fallback(self):
        key = "runtime-empty"
        state = update_runtime_state(key=key, text="", sequence=1)
        self.assertEqual(state.accepted_text, "")
        self.assertEqual(
            RuntimePromptRandomChoice().pick("queued candidate", 1, key, "1")["result"],
            ("", "empty"),
        )


class StateAndCompatibilityTests(unittest.TestCase):
    def test_revisions_advance_only_for_valid_text(self):
        store = RuntimeCandidateStateStore()
        valid = store.update(
            state_key="revision", node_kind="ex", text="A{x|y}",
            input_status="valid", error="", client_id="browser", client_sequence=1,
        )
        incomplete = store.update(
            state_key="revision", node_kind="ex", text="A{x|y",
            input_status="incomplete", error="Unmatched opening brace",
            client_id="browser", client_sequence=2,
        )
        hard = store.update(
            state_key="revision", node_kind="ex", text="A{x}{y}",
            input_status="hard_error", error="Cartesian product",
            client_id="browser", client_sequence=3,
        )
        self.assertEqual((valid.revision, incomplete.revision, hard.revision), (1, 1, 1))
        self.assertEqual(incomplete.accepted_text, "A{x|y}")
        self.assertEqual(hard.accepted_text, "A{x|y}")

    def test_regular_node_resets_when_candidates_change(self):
        node = PromptRandomChoice()
        with patch("candidate_parser.secrets.choice", side_effect=lambda values: values[0]):
            self.assertEqual(node.pick("A\nB", 3)["result"][0], "A")
            self.assertEqual(node.pick("C\nD", 3)["result"][0], "C")

    def test_ex_node_result_shape(self):
        self.assertEqual(
            PromptRandomChoiceEx().pick("A{x}", 1)["result"],
            ("A, x", "A_x"),
        )

    def test_safe_text_handles_device_names_and_length(self):
        self.assertEqual(_safe_text("CON"), "_CON")
        self.assertEqual(len(_safe_text("x" * 300)), 200)

    def test_stale_runtime_update_is_rejected(self):
        store = RuntimeCandidateStateStore()
        common = {
            "state_key": "ordered",
            "node_kind": "flat",
            "input_status": "valid",
            "error": "",
            "client_id": "browser",
        }
        store.update(text="A", client_sequence=2, **common)
        with self.assertRaises(StaleRuntimeCandidateUpdate):
            store.update(text="B", client_sequence=1, **common)

    def test_node_mappings_and_runtime_inputs_are_stable(self):
        self.assertEqual(
            set(NODE_CLASS_MAPPINGS),
            {
                "PromptRandomChoice",
                "PromptRandomChoiceEx",
                "RuntimePromptRandomChoice",
                "RuntimePromptRandomChoiceEx",
                "SafeRandomSeed",
            },
        )
        for node_class in (RuntimePromptRandomChoice, RuntimePromptRandomChoiceEx):
            inputs = node_class.INPUT_TYPES()
            self.assertIn("state_key", inputs["required"])
            self.assertEqual(inputs["hidden"]["unique_id"], "UNIQUE_ID")
            self.assertFalse(inputs["required"]["options_text"][1]["dynamicPrompts"])

    def test_all_nodes_share_one_top_level_menu_category(self):
        self.assertEqual(
            {node_class.CATEGORY for node_class in NODE_CLASS_MAPPINGS.values()},
            {"Prompt Random Choice"},
        )


if __name__ == "__main__":
    unittest.main()
