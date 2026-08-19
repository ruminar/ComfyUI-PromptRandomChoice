# PromptRandomChoice specification index

このディレクトリは、実装より先に守るべき仕様と退行条件を記録する。

- [candidate-language.md](candidate-language.md): 共通候補記法、`#`、`!`、Ex文法
- [runtime-behavior.md](runtime-behavior.md): Runtime同期、revision、`change_every`、エラー分類
- [regression-matrix.md](regression-matrix.md): 仕様と自動テストの対応表

## 変更時の原則

1. 挙動を変更する前に該当仕様を更新する。
2. 仕様変更には対応する回帰テストを追加する。
3. `python -m unittest discover -s tests` を成功させる。
4. JavaScript変更時は `node --check web/prompt_random_choice.js` と
   `node --check web/runtime_prompt_random_choice.js` を成功させる。
5. 互換性に影響する変更はREADMEとRELEASE_NOTESにも記載する。

現在の対象バージョンは `0.6.0`。
