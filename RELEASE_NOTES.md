## v0.4.0

`Prompt Random Choice Ex` を追加しました。

## 追加

- `Prompt Random Choice Ex`
  - `Prompt Random Choice` と同じフラット候補リストに対応
  - `{}` による入れ子の候補展開に対応
  - 最内側の `{}` からランダムに展開
  - 展開結果を親要素へ `, ` で接続
  - `selected_text` / `selected_text_safe` を出力

## 例

```text
town|zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
```

出力例:

```text
town
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

## 備考

通常の `Prompt Random Choice` は、フラットな候補選択用としてそのまま残しています。  
階層候補が必要な場合だけ `Prompt Random Choice Ex` を使ってください。
