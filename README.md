# ComfyUI-PromptRandomChoice

実行のたびに「プロンプトガチャ」を爆速で回す、超軽量なランダム選択ノードじゃ！

「背景や天気を適当に変えて、一晩中回しておきたいのう……」<br/>
そんなおぬしの願いを、実行時間 0.010s（注：作者環境で速いとき）という瞬速の魔法で叶えて進ぜよう！

背景・時間帯・天気などを別々にランダム化したい時に便利じゃ。<br/>
フロー内に複数個置いても、それぞれ独立して動くぞ。


## v0.4.0

`Prompt Random Choice Ex` を追加したのじゃ。

- `Prompt Random Choice`
  - フラットな候補リストから1つ選ぶノード
- `Prompt Random Choice Ex`
  - フラット候補に加えて、`{}` による入れ子の候補展開に対応したノード
  - 先にすべての葉候補へ展開し、最後に1回だけランダム選択します
  - 展開済み候補リストは `options_text` が変わるまでキャッシュします

どちらもノードしての出力は同じじゃ。

- `selected_text`
- `selected_text_safe`

## 特徴

- **実行ごとにランダム選択**
  - キューを雑に100件積んでも、毎回候補を選び直すぞ。

- **区切りは `|` または実際の改行**
  - `|` と改行の両方を区切りとして扱うので、混在していても動くぞ。
  - 区切り文字が連続して出現した場合は、候補から取り除かれることに注意じゃ。
    - 明示的に空白文字列を候補として返却させたい場合は、明示的に `()` と指定するのじゃ。

- **候補の前後の `,` と空白を自動で整理**
  - `town,`
  - `coffee shop,`
  - `castle, fortress,`
  のような書き方でも大丈夫じゃ。

- **現在の選択結果をタイトル表示**
  - 実行時にノードタイトルが `Choice: coffee shop` のように更新されるぞ。
  - KSamplerのプレビューと見比べやすいのじゃ。

- **複数設置に対応**
  - 背景用、時間帯用、天気用など、複数ノードを置いてそれぞれ別々に使えるぞ。

- **ファイル名向けの返り値**
  - ファイル名向けに安全化した文字列 `selected_text_safe` を出力するのじゃ。

- **明示的な空候補 `()` に対応**
  - `()` が選ばれた場合、プロンプト向け出力は空文字に、ファイル名向け出力は `empty` になるのじゃ。

## Prompt Random Choice Ex の追加要素

- **フラット候補に加えて、`{}` による入れ子の候補展開に対応**
  - しかも、ComfyUIの標準記法と異なり、`{}` 内を入れ子にできるのじゃ。
    - `{}` 内の要素は内側から解釈され、選択項目がカンマで前後に接続される。
  - `|` と改行の両方を区切りとして扱うので、混在していても動くぞ。
  - 区切り文字が連続して出現した場合は、候補から取り除かれることに注意じゃ。
    - 明示的に空白文字列を候補として返却させたい場合は、明示的に `()` と指定するのじゃ。
    
ここは実例を見てもらった方が話が早そうじゃ。
```text
town|zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
```

これは、内部的には次の候補へ展開され、キャッシュされるのじゃ。

```text
town
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

この5候補から1つが選ばれるのじゃ。<br/>
入れ子になった各要素が、すべて等しい確率で出現するように工夫しておるのじゃ。
<br/>

## 導入方法

ComfyUIの `custom_nodes` ディレクトリで、以下のコマンドを打ち込むのじゃ！

```bash
git clone https://github.com/ruminar/ComfyUI-PromptRandomChoice.git
```

## 使い方

1. `Prompt Random Choice` ノードを置く
2. `options_text` に候補を入れる (入力例を参照)
3. 必要に応じて `change_every` を選ぶ
4. `selected_text` を `Join String Multi` などの文字列結合ノードへ繋ぎ、ポジティブプロンプトへ足す
5. キューを好きなだけ積む

<br/>
<img width="544" height="526" alt="image" src="https://github.com/user-attachments/assets/d230659e-f008-4232-955d-1fa6fdf299fa" /><br/><br/>

<img width="594" height="555" alt="image" src="https://github.com/user-attachments/assets/7966c50e-15c7-41cf-b167-06a54054acec" /><br/>
※ 設定後は折りたたんで使うのもおすすめなのじゃ。

## 入力例

### 改行区切り (改行前の`,`は任意です)

```text
town,
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
coffee shop,
```

### `|` 区切り

```text
town|
girl's room|
park|
lake|
flower garden|
castle, fortress|
forest|
grasslands|
sea|
snowy landscape|
mountain|
flower field|
starry sky|
coffee shop|
```
### 何も追加しない候補

`()` は明示的な空候補として扱われます。

```text
()|(full body:0.9)
```

この例では、何も追加しない場合と、`(full body:0.9)` を追加する場合をランダムに切り替えられます。

### 選ばれやすさを調整したい場合

同じ候補を複数回書けば、そのぶん選ばれやすくなります。

```text
day|day|day|sunset|night
```

昼を多めに出したい、たまに夕方や夜も混ぜたい、という時に便利じゃ。

<br/>

## 仕様

- `|` または実際の改行で分割
- `\n` という文字列は区切りとして扱わない
- 各候補の前後の空白と `,` を trim
- 空候補は無視
- `()` は明示的な空候補として扱う
- `change_every` が 1 なら毎回選び直す
- `change_every` が 2 以上なら、その回数ぶん同じ候補を維持する
- 実行時にタイトルへ `Choice: lake` や `Choice: (empty) (2/3)` のように表示する

## Prompt Random Choice

候補リストから1つ選びます。

```text
town|park|lake|coffee shop
```

`()` は明示的な空候補です。

```text
()|(full body:0.9)
```

## Prompt Random Choice Ex

`Prompt Random Choice` と同じフラットな候補リストをそのまま使えます。

```text
town|park|lake|coffee shop
```

さらに、候補の中に `{}` を書くことで、選ばれた候補にだけ追加候補をぶら下げられます。

```text
town|zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
```

この入力は、内部的には次の候補へ展開されます。

```text
town
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

この5候補から1つが選ばれます。

### 複数行の Ex 例

```text
zoo{
  animals{
    birds
    penguins
  }
  aquarium{
    fish
    jellyfish
  }
}
```

出力例:

```text
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

### Ex のルール

- 選択候補の区切り文字は、実際の改行 または `|`
- 空候補は無視
- `()` は明示的な空候補
- `{}` の内部も、実際の改行 または `|` で候補分割
- `{}` は最内側からすべての葉候補へ展開
- 展開結果は親要素へ `, ` で接続
- 最終候補リストから最後に1回だけランダム選択
- 展開済み候補リストは `options_text` が変わるまでキャッシュ
- 展開候補数と展開回数には安全上限があります
- リテラルの `{` / `}` をプロンプト文字として使う用途は非対応

## 出力

- `selected_text`  
  trim後の選択文字列です。  
  `()` が選ばれた場合は空文字 `""` になります。

- `selected_text_safe`  
  ファイル名向けに安全化した出力です。  
  `selected_text` が空なら `empty` を返します。

## 推奨構成

`selected_text` を kjnodes の `Join String Multi` などへ接続し、区切り文字は結合ノード側で管理するのがおすすめじゃ。

複数の `Prompt Random Choice` / `Prompt Random Choice Ex` を並べることで、背景・時間帯・天気・構図などを別々にランダム化するのじゃ。

ただし、Ex はすべての要素を1つにまとめるためのノードではなく、`zoo` の時だけ動物候補を追加するような、親子関係のある候補を扱うためのノードとして使うのがおすすめじゃ。

<br/>

## 標準選択記法 `{day|night|morning}` との違いについて

- ComfyUI標準にも、プロンプト候補をランダムに切り替える構文として `{a|b|c}` 記法があります。<br/>
この記法は、`CLIP Text Encode` でプロンプトが処理される段階で解決されます。

- 一方、`PromptRandomChoice` はその前段で候補を1つに確定し、選ばれた文字列だけを通常の `STRING` として出力します。<br/>
そのため、選ばれなかった候補は下流へ流れません。

  - この性質により、選択候補の中にLoRAのトリガーワードをより安全に含めることもできます。<br/>
選ばれた候補だけが後続ノードへ渡されるため、標準の `{a|b|c}` 記法よりも、候補の確定状態をワークフロー上で明示しやすくなります。
    - ※ ただし、LoRA自体のロードON/OFFを切り替えるものではありません。  
ここでいう安全性は、選ばれなかったトリガーワード文字列が下流へ流れない、という意味です。

- 区切り文字は、標準の `{a|b|c}` 記法と同じ `|` を使えます。  
そのため、標準記法から `{}` の中身を抜き出して `PromptRandomChoice` に持ってきたり、逆に `PromptRandomChoice` の中身を `{}` で括ってプロンプト文字列へ戻したりできます。<br/>
出入り自由です。

- また、画像生成の比較では、1回ごとにプロンプト候補が変わると、差分を判断しづらい場合があります。<br/>
`PromptRandomChoice` では `change_every` を使うことで、同じ候補を数回維持してから次の候補へ切り替えることができます。

- さらに、`PromptRandomChoice` の段階で確定した候補はノードタイトルに表示されます。
  - KSamplerのプレビューと見比べながら、現在どの候補が使われているかを確認できます。
  - `change_every` 指定時には、`Choice: lake (2/3)` のように進捗も表示されます。

<br/>

## ライセンス

GPL-3.0（ComfyUI本体の掟に従っておるぞ！）

## 宣伝画像

<img width="1055" height="1491" alt="PromptRandomChoice説明画像" src="https://github.com/user-attachments/assets/7a4f1b5f-c77b-4e47-90af-cbd0330c85fe" />

EX版
<img width="1122" height="1402" alt="PromptRandomChoiceEx説明画像" src="https://github.com/user-attachments/assets/f45a44b7-5692-4d98-854a-7736677e1f5a" />

## コピペ用おすすめ候補リスト

### 背景

```text
Indoor,
girl's room,
coffee shop,
library,
classroom,
office,
laboratory,
art gallery,
museum,
bookstore,
bakery,
restaurant,
concert hall,
theater,
school hallway,
greenhouse,
observatory,
Outdoor,
City,
town,
park,
rooftop,
train station,
shopping street,
courtyard,
bridge,
riverside,
harbor,
marketplace,
alley,
village,
Nature,
lake,
flower garden,
forest,
grasslands,
sea,
mountain,
flower field,
beach,
island,
cave,
botanical garden,
Traditional,
Fantasy-ish,
Japanese garden,
shrine,
temple,
castle,
fortress,
palace,
ruins,
```

### 背景 Ex 版

```text
indoor{
  girl's room
  coffee shop
  library
  classroom
  office
  laboratory
  art gallery
  museum
  bookstore
  bakery
  restaurant
  concert hall
  theater
  school hallway
  greenhouse
  observatory
}
city{
  town
  park
  rooftop
  train station
  shopping street
  courtyard
  bridge
  riverside
  harbor
  marketplace
  alley
  village
}
nature{
  lake
  flower garden
  forest
  grasslands
  sea
  mountain
  flower field
  beach
  island
  cave
  botanical garden
}
traditional{
  japanese garden
  shrine
  temple
}
fantasy-ish{
  castle
  fortress
  palace
  ruins
}
```

### 時刻
```text
day|day|day|morning|sunset|night
```

### 天候
```text
()|(clear sky:0.9)|(clear sky:0.9)|(clear sky:0.9)|(cloudy sky:0.9)|rain|snow
```

### 光
```text
()|soft lighting|warm lighting|natural lighting|(backlighting:0.8)|(dramatic lighting:0.8)|(cinematic lighting:0.8)
```

### 姿勢、視線、動作
```text
()|standing|sitting|walking|looking at viewer|waving|hands on hips|jumping|running|skipping|looking up
```

### 表情
```text
()|smiling|gentle smile|serious expression|surprised expression|slightly surprised|shy expression|happy expression|smiling, open mouth|slightly open mouth|closed-mouth smile
```

### 構図
```text
()|(face close-up:0.9)|upper body|upper body|full body|full body|full body|full body|full body|wide shot|(from side:0.8)|(from above:0.8)|(low angle:0.8)|(from behind, looking back:0.8)
```
