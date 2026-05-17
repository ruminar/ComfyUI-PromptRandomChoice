# ComfyUI-PromptRandomChoice

実行のたびに「プロンプトガチャ」を爆速で回す、超軽量なランダム選択ノードじゃ！

「背景や天気を適当に変えて、一晩中回しておきたいのう……」<br/>
そんなおぬしの願いを、実行時間 0.010s（注：作者環境で速いとき）という瞬速の魔法で叶えて進ぜよう！

背景・時間帯・天気などを別々にランダム化したい時に便利じゃ。<br/>
フロー内に複数個置いても、それぞれ独立して動くぞ。


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
※ 設定後は折りたたんで使うのもおすすめです

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

## 仕様

- `|` または実際の改行で分割
- `\n` という文字列は区切りとして扱わない
- 各候補の前後の空白と `,` を trim
- 空候補は無視
- `()` は明示的な空候補として扱う
- `change_every` が 1 なら毎回選び直す
- `change_every` が 2 以上なら、その回数ぶん同じ候補を維持する
- 実行時にタイトルへ `Choice: lake` や `Choice: (empty) (2/3)` のように表示する

## 出力

- `selected_text`  
  trim後の選択文字列です。  
  `()` が選ばれた場合は空文字 `""` になります。

- `selected_text_safe`  
  ファイル名向けに安全化した出力です。  
  `selected_text` が空なら `empty` を返します。

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


## 付録

背景候補

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

時刻
```text
day|day|day|morning|sunset|night
```

天候
```text
()|(clear sky:0.9)|(clear sky:0.9)|(clear sky:0.9)|(cloudy sky:0.9)|rain|snow
```

光
```text
()|soft lighting|warm lighting|natural lighting|(backlighting:0.8)|(dramatic lighting:0.8)|(cinematic lighting:0.8)
```

姿勢、視線、動作
```text
()|standing|sitting|walking|looking at viewer|waving|hands on hips|jumping|running|skipping|looking up
```

表情
```text
()|smiling|gentle smile|serious expression|surprised expression|slightly surprised|shy expression|happy expression|smiling, open mouth|slightly open mouth|closed-mouth smile
```

構図
```text
()|(face close-up:0.9)|upper body|upper body|full body|full body|full body|full body|full body|wide shot|(from side:0.8)|(from above:0.8)|(low angle:0.8)|(from behind, looking back:0.8)
```
