# Runtime behavior specification

## 目的

Queue投入済みで未実行のジョブが、ノード実行時点でサーバーに受理済みの
最新候補集合を参照できるようにする。実行開始済みのジョブは変更しない。

## Queue時とRuntime時の分離

Queue時に確定するもの:

- グラフと接続
- `change_every`
- サーバー状態がない場合のフォールバック候補テキスト
- 永続化された`state_key`

Runtime同期するもの:

- 候補入力テキスト
- 入力状態
- 受理済み候補revision

`change_every`はRuntime同期しない。

## 選択寿命

Runtimeで更新されるのは候補集合であり、現在選択中の完成文字列ではない。

```text
change_every = 3
実行1: revision 1からAを選択
編集: revision 2を受理
実行2: A
実行3: A
実行4: revision 2から再選択
```

- 候補編集でrepeat countをリセットしない。
- 選択中候補の削除、`#`化、内容変更でも保持期間中は完成文字列を維持する。
- `!`の追加・削除も次回再選択時に反映する。
- `change_every`入力値自体がQueue間で変わった場合は、新周期として選択し直す。
- `selected_revision`は現在の完成文字列を決めたrevisionを表す。

## サーバー状態

状態は少なくとも次を保持する。

```text
state_key
node_kind
input_text
input_status
error
accepted_text
revision
client_id
client_sequence
```

- `accepted_text=None` と受理済み空文字 `accepted_text=""` を区別する。
- revisionは正常な候補テキストが変わった場合だけ増加する。
- incomplete/hard errorだけではrevisionを増加させない。
- クライアントごとの連番で古い更新と連番再利用を拒否する。
- 状態はメモリ内にあり、ComfyUI再起動で消える。
- 状態がなければQueueへ保存された候補テキストを使用する。

## エラー分類

### Soft incomplete

例: 波括弧の閉じ忘れ、余分な閉じ括弧。

- 新しい正常revisionとして受理しない。
- 直前の`accepted_text`とrevisionを維持する。
- Hard Error状態は解除する。
- 実行は最後の正常候補集合で継続する。
- 正常候補が一度もなく、Queueフォールバックも不正なら実行エラー。
- UIは `EDITING / SYNTAX INCOMPLETE` と使用中revisionを表示する。

### Hard error

例: 隣接する複数の直接子グループ、単独の `!`、上限超過。

- サーバーはHard Error状態を保存する。
- 最後の正常候補を黙って使用しない。
- 現在の`change_every`保持期間中でも、次回実行を`ValueError`で停止する。
- 正常な入力が受理されたらHard Errorを解除する。
- UIは `HARD ERROR` と理由を表示する。

## フロントエンド同期

- 120ms debounce。
- 日本語IME変換中は送信しない。
- 1ノード内の送信は順番に処理する。
- UTF-8で512KiBを上限とする。
- Workflow複製で重複した`state_key`は再発行する。
- 入力内容は通常どおりWorkflowへ保存する。
- `EDITING / SYNCING / LIVE / SYNC ERROR`を表示する。
- サーバーに状態があれば、その`input_text`を初期表示へ復元する。
- Runtime textareaはDOMウィジェットの可変領域を使用し、ノードの高さ変更へ追従する。
- textareaは可変領域、同期状態フッターは固定領域として配置する。
