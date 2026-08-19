# Regression matrix

## 自動実行

```powershell
$py = "C:\path\to\python.exe"
& $py -B -m unittest discover -s tests
node --check web/prompt_random_choice.js
node --check web/runtime_prompt_random_choice.js
node --test tests/runtime_layout.test.mjs
```

GitHub Actionsでは `.github/workflows/regression-tests.yml` が同じ検証を行う。

## 仕様とテストの対応

| 保護対象 | 主なテスト |
|---|---|
| 従来版の `!` は通常文字 | `test_flat_comments_and_non_runtime_bang_are_literal`, `test_non_runtime_ex_keeps_bang_as_text` |
| Runtimeの最初の `!` | `test_runtime_flat_uses_first_forced_candidate`, `test_ex_comments_and_first_force_apply_recursively` |
| `!()` / 単独`!` / `!!` | `test_runtime_forced_empty_and_bare_bang`, `test_double_bang_removes_only_control_marker`, `test_runtime_ex_forced_empty_is_a_leaf` |
| `#`コメントと全件コメント | `test_all_commented_candidates_produce_empty_pool`, `test_ex_comments_and_first_force_apply_recursively` |
| Exの葉均等候補集合 | `test_ex_filters_each_level_and_keeps_leaf_uniform_paths` |
| 複数親と縦入れ子 | `test_ex_multiple_parents_and_vertical_nesting` |
| 直積の展開前拒否 | `test_adjacent_direct_groups_are_rejected_before_selection` |
| 強制で隠れた枝もHard Error検査 | `test_hard_error_is_detected_even_in_branch_overridden_by_force` |
| Soft/Hard分類 | `test_incomplete_braces_are_distinguished`, `test_adjacent_groups_classify_as_hard_error` |
| Runtime編集が保持周期へ割り込まない | `test_edit_does_not_interrupt_change_every` |
| Soft incompleteは最後の正常revision | `test_incomplete_uses_last_valid_revision` |
| Hard Errorは黙ってフォールバックしない | `test_hard_error_never_falls_back` |
| Hard Error修正後の復帰 | `test_hard_error_clears_after_valid_text_is_accepted` |
| revisionは正常変更だけで進む | `test_revisions_advance_only_for_valid_text` |
| 受理済み空文字と状態なしの区別 | `test_accepted_empty_text_overrides_queued_fallback` |
| 古いクライアント更新の拒否 | `test_stale_runtime_update_is_rejected` |
| ノード登録名とRuntime入力 | `test_node_mappings_and_runtime_inputs_are_stable` |
| 全ノードが単一トップ階層へ表示 | `test_all_nodes_share_one_top_level_menu_category` |
| 通常版は候補変更で再選択 | `test_regular_node_resets_when_candidates_change` |
| ファイル名安全化 | `test_safe_text_handles_device_names_and_length` |
| Runtime textareaがノード高へ追従 | `runtime_layout.test.mjs` |

## 手動確認項目

- ComfyUI再起動後にRuntimeノード2種がメニューへ表示される。
- textareaで日本語IME変換中に同期されない。
- `EDITING → SYNCING → LIVE`が視認できる。
- 括弧不一致で`SYNTAX INCOMPLETE`となり生成を継続する。
- 直積入力で`HARD ERROR`となり、次回実行が停止する。
- Hard Error修正後に`LIVE`へ復帰する。
- Workflow保存・再読込で候補テキストとstate keyが維持される。
- ノード複製時にstate keyが重複しない。
- `change_every=3`の途中編集でも現在の完成文字列が3回維持される。
