## v0.4.0

`Prompt Random Choice Ex` を追加しました。

## 追加

- `Prompt Random Choice Ex`
  - `Prompt Random Choice` と同じフラット候補リストに対応
  - `{}` による入れ子の候補展開に対応
  - すべての葉候補へ展開してから、最後に1回だけランダム選択
  - 展開結果を親要素へ `, ` で接続
  - 展開済み候補リストを `options_text` 単位でキャッシュ
  - `selected_text` / `selected_text_safe` を出力
  - `(){...}` のような空親グループに対応
    - 親要素 `()` は出力されません
    - 子要素だけが候補になります

## 例

```text
town|zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
```
これは、内部的には次の候補へ展開されます。

```text
town
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```
この5候補から1つが選ばれます。
<br/>


親要素 `()` の例
```text
(){
  white day
  wedding ceremony
  birthday party
}
```

内部的には次の候補へ展開されます。

```text
white day
wedding ceremony
birthday party

## 備考

- `Prompt Random Choice Ex` は、すべての葉候補へ展開してから最後に1回だけランダム選択します
- 展開済み候補リストは `options_text` 単位でキャッシュします
- 通常の `Prompt Random Choice` は、フラットな候補選択用としてそのまま残しています
