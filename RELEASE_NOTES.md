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

## 備考

通常の `Prompt Random Choice` は、フラットな候補選択用としてそのまま残しています。  
階層候補が必要な場合だけ `Prompt Random Choice Ex` を使ってください。
