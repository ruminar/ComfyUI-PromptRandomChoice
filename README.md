# ComfyUI-PromptRandomChoice

実行のたびに「プロンプトガチャ」を爆速で回す、超軽量なランダム選択ノードじゃ！

「背景や天気を適当に変えて、一晩中回しておきたいのう……」<br/>
そんなおぬしの願いを、実行時間 0.010s（注：作者環境で速いとき）という瞬速の魔法で叶えて進ぜよう！

背景・時間帯・天気などを別々にランダム化したい時に便利じゃ。<br/>
フロー内に複数個置いても、それぞれ独立して動くぞ。


## v0.6.0

候補を実行中に編集できるRuntime版と、候補リストを操作しやすくする制御記号を追加したのじゃ。

- `Runtime Prompt Random Choice`
- `Runtime Prompt Random Choice Ex`
- `#` で始まる候補を一時的にコメントアウト
- Runtime版では `!` で始まる候補を次回再選択時に強制選択
- Ex版の直積構文を展開前に検出して停止
- Runtime編集中の波括弧不一致は、最後に受理した正常な候補を使って待機

互換性に関する注意:

- 従来版でも先頭 `#` はコメントとして扱われます
- `scene{day|night}{clear|rain}` のような隣接子グループは使用できなくなりました
  - 今回のバージョンより、Ex版での直積を禁止しています
  - 直積を実現したい場合は、それぞれ別のExノードへ分け、String Joinで結合してください

## v0.5.0

`Safe Random Seed` を追加したのじゃ。

- `Safe Random Seed`
  - KSampler向けに、0以上のランダムseedだけを出力する小型ノード
  - Python側で `secrets` を使って発番します
  - 実行後、ノードタイトルを `Seed: 4897362896` のように書き換えます

## v0.4.0

`Prompt Random Choice Ex` を追加したのじゃ。

- `Prompt Random Choice`
  - フラットな候補リストから1つ選ぶノード
- `Prompt Random Choice Ex`
  - フラット候補に加えて、`{}` による入れ子の候補展開に対応したノード
  - 先にすべての葉候補へ展開し、最後に1回だけランダム選択します
  - 展開済み候補リストは `options_text` が変わるまでキャッシュします

どちらもノードとしての出力は同じじゃ。

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
  - 実行時にノードタイトルが `Ch: coffee shop` のように更新されるぞ。
  - KSamplerのプレビューと見比べやすいのじゃ。

- **KSampler向けの安全なランダムseed生成**
  - `Safe Random Seed` は、0以上のINTだけを出力するぞ。
  - 実行後、ノードタイトルが `Seed: 4897362896` のように更新されるのじゃ。

- **複数設置に対応**
  - 背景用、時間帯用、天気用など、複数ノードを置いてそれぞれ別々に使えるぞ。

- **ファイル名向けの返り値**
  - ファイル名向けに安全化した文字列 `selected_text_safe` を出力するのじゃ。

- **明示的な空候補 `()` に対応**
  - `()` が選ばれた場合、プロンプト向け出力は空文字に、ファイル名向け出力は `empty` になるのじゃ。

- **候補のコメントアウト**
  - trim後の先頭が `#` の候補は選択対象から除外されます。
  - Ex版では各階層で利用できます。

- **Runtime編集**
  - Runtime版では、Queue投入後でもサーバーが受理した最新候補集合を参照できます。
  - `!` はRuntime版だけで強制選択記号として働き、従来版では通常文字です。

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

これは、概念上は次の葉候補を持つのじゃ。

```text
town
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

この5候補から1つが選ばれるのじゃ。<br/>
最終葉候補がすべて等しい確率になるよう、各枝の葉数を使って1経路だけを選ぶため、完成文字列を事前に全列挙はしません。
<br/>

## 導入方法

ComfyUIの `custom_nodes` ディレクトリで、以下のコマンドを打ち込むのじゃ！

```bash
git clone https://github.com/ruminar/ComfyUI-PromptRandomChoice.git
```

## 使い方

ノード追加メニューの `Prompt Random Choice` カテゴリに、通常版・Runtime版・Safe Random Seedがまとまっています。

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
- trim後の先頭が `#` の候補はコメントとして除外
- `!` は従来版では通常文字として扱う
- `change_every` が 1 なら毎回選び直す
- `change_every` が 2 以上なら、その回数ぶん同じ候補を維持する
- 実行時にタイトルへ `Ch: lake` や `Ch: (empty) (2/3)` のように表示する
- `Safe Random Seed` は実行時にタイトルへ `Seed: 4897362896` のように表示する

## Safe Random Seed

KSampler向けに、0以上のランダムseedを1つ生成します。
汎用の整数Primitiveを `randomize` すると負数が出る場合がありますが、このノードは負数を出しません。
SDE系サンプラーで `expected non-negative integer` が出る事故を避けるための小さな保険じゃ。

- 入力はありません
- 出力は `seed` だけです
- 乱数はComfyUIサーバー側、Pythonの `secrets` で生成します
- 発番はノード実行時です
- 出力値の範囲は `0` から `2^53 - 1` です
- 同じノードの出力を複数箇所へ接続した場合、同じseed値を配ります
- 別々のseedが欲しい場合は、`Safe Random Seed` ノードを複数置いてください
- 前回出力されたseed値は、次回の乱数生成には影響しません
- 実行後、ノードタイトルを `Seed: 4897362896` のように書き換えます

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

この入力は、概念上は次の最終葉候補を持ちます。

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
- 各階層で `#` コメント候補を除外
- 展開結果は親要素へ `, ` で接続
- 最終葉候補が均等確率になるよう、葉数を重みとして1経路だけ選択
- 完成した全候補文字列は事前に列挙しない
- 入れ子の深さと葉候補数には安全上限があります
- 1候補が持てる直接の子グループは1個まで
- `A{B|C}{D|E}` のような直積構文は展開前にエラー
- リテラルの `{` / `}` をプロンプト文字として使う用途は非対応

### 直積構文について

縦方向の入れ子と、子を持つ親候補を同じ階層へ複数並べることはできます。

```text
black hair{straight long hair|short cut}
blonde hair{long hair|wavy long hair}
```

一方、同じ候補へ子グループを横に複数並べる構文は使用できません。

```text
A{B|C}{D|E}
```

この構文は直積を作るため、候補展開前にエラーになります。独立した軸は別の `Prompt Random Choice Ex` ノードへ分け、String Joinで結合してください。

## Runtime Prompt Random Choice

<img width="699" height="420" alt="image" src="https://github.com/user-attachments/assets/fea5989f-6348-404f-87c5-aa5506113b71" />

`Runtime Prompt Random Choice` と `Runtime Prompt Random Choice Ex` は、実行時点でComfyUIサーバーが受理済みの最新候補テキストを参照します。候補入力欄には同期状態が表示されます。

- `EDITING`: 編集中または送信待ち
- `SYNCING`: サーバーへ送信中
- `LIVE`: 最新入力をサーバーが受理済み
- `EDITING / SYNTAX INCOMPLETE`: Exの波括弧が編集中で不一致。最後の正常revisionを使用
- `HARD ERROR`: サポートしない完成済み構文。修正されるまで次回実行を停止
- `SYNC ERROR`: 通信または同期エラー

### `!` 強制選択

`!` はRuntime版だけで有効です。同じ階層に複数ある場合は、上から最初の候補を使用します。先頭の `!` は出力されません。

```text
black hair
!blonde hair
!silver hair
```

この場合は `blonde hair` を使用します。`!()` は空文字を強制選択します。従来版の `Prompt Random Choice` / `Prompt Random Choice Ex` では `!` は通常文字です。

Runtime Exでは各階層で最初の `!` を適用します。`!` はその階層の枝だけを絞り込み、選択された枝の子階層は引き続き評価されます。

### Runtimeと`change_every`

Runtimeでリアルタイム更新されるのは候補集合であり、現在選択中の完成文字列ではありません。`change_every = 3` なら、途中で候補を編集・削除・コメントアウトしたり `!` を追加しても、現在の結果を3回出力するまで維持します。

```text
実行1: Aを選択
実行2: A
実行3: A
実行4: 最新revisionの候補集合から再選択
```

`!` は次回の再選択時に通常のランダム選択を上書きし、保持期間へ割り込みません。候補編集を次のジョブへ反映したい場合は `change_every = 1` を使用してください。`change_every` 自体はRuntime同期されず、Queue投入時の値を使います。

### Runtime Exの構文エラー

- 波括弧不一致は編集中の一時状態として扱い、新しいrevisionにはしません。最後に受理した正常な候補集合で生成を継続します。
- 隣接子グループによる直積はHard Errorです。古い候補へ黙ってフォールバックせず、次回実行でエラーにします。

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
  - `change_every` 指定時には、`Ch: lake (2/3)` のように進捗も表示されます。

<br/>

## 開発仕様と回帰テスト

実装時に守る仕様は [`.spec/README.md`](.spec/README.md) を起点にまとめています。

標準ライブラリだけで回帰テストを実行できます。

```bash
python -B -m unittest discover -s tests -v
```

pushとPull RequestではGitHub ActionsがPython回帰テストとJavaScript構文検査を自動実行します。

## ライセンス

GPL-3.0（ComfyUI本体の掟に従っておるぞ！）

## 宣伝画像

<img width="1055" height="1491" alt="PromptRandomChoice説明画像" src="https://github.com/user-attachments/assets/7a4f1b5f-c77b-4e47-90af-cbd0330c85fe" />

EX版
<img width="1122" height="1402" alt="PromptRandomChoiceEx説明画像" src="https://github.com/user-attachments/assets/f45a44b7-5692-4d98-854a-7736677e1f5a" />

Runtime版
<img width="1055" height="1491" alt="image" src="https://github.com/user-attachments/assets/b766c03e-9d95-4e88-9bd2-1b448f4e21c7" />


## コピペ用おすすめ候補リスト

### 背景

```text
Indoor,
girl's room,
bedroom,
living room,
kitchen,
dining room,
bathroom,
attic,
basement,
coffee shop,
cafe terrace,
library,
private library,
classroom,
music room,
science room,
computer room,
school infirmary,
gymnasium,
office,
meeting room,
conference room,
laboratory,
medical room,
art studio,
art gallery,
museum,
aquarium,
planetarium,
observatory interior,
bookstore,
bakery,
flower shop,
convenience store,
supermarket,
restaurant,
bar,
diner,
karaoke room,
arcade,
game center,
cinema,
concert hall,
theater,
dance studio,
school hallway,
locker room,
stairwell,
elevator hall,
greenhouse,
train interior,
subway interior,
airport terminal,
shopping mall,
hotel room,
lobby,
chapel interior,

Outdoor,
city,
town,
downtown,
residential area,
park,
playground,
plaza,
rooftop,
balcony,
terrace,
train station,
bus stop,
airport runway,
shopping street,
courtyard,
bridge,
crosswalk,
intersection,
riverside,
canal,
harbor,
port,
boardwalk,
marketplace,
festival street,
food stall area,
alley,
back alley,
village,
suburban street,
schoolyard,
campus,
parking lot,
construction site,
amusement park,
theme park,
zoo,
stadium exterior,
cemetery,
clock tower,
lighthouse,
windmill,
waterfront,

Nature,
lake,
pond,
waterfall,
river,
stream,
flower garden,
rose garden,
forest,
bamboo forest,
pine forest,
rainforest,
grasslands,
meadow,
savanna,
sea,
ocean,
coral reef,
mountain,
mountain path,
hilltop,
valley,
cliff,
flower field,
sunflower field,
lavender field,
beach,
shore,
island,
tropical island,
cave,
crystal cave,
botanical garden,
jungle,
swamp,
marsh,
desert,
oasis,
snowfield,
glacier,
ice cave,
volcanic area,
hot spring,
starry sky,
night sky,
aurora,

Traditional,
Japanese garden,
shrine,
temple,
tea house,
tatami room,
engawa,
onsen,
ryokan,
festival grounds,
torii gate,
bamboo grove path,
castle,
fortress,
palace,
ruins,
old town,
stone pavement,
pagoda,
dojo,
samurai residence,
courtyard garden,
```

### 時刻
```text
()|day|day|day|morning|sunset|night
```

### 天候
```text
()|Strong sunshine|(clear sky:0.9)|(clear sky:0.9)|(clear sky:0.9)|(cloudy sky:0.9)|rain|snow|Rainbow after Rain|storm, thunder
```

### 光
```text
()|soft lighting|warm lighting|natural lighting|(backlighting:0.8)|(dramatic lighting:0.8)|(cinematic lighting:0.8)
```

### 姿勢、視線、動作
```text
()|standing|sitting|walking|looking at viewer|waving|hands on hips|jumping high|running|skipping|looking up
```

### 表情
```text
()|smiling|gentle smile|serious expression|surprised expression|slightly surprised|shy expression|happy expression|smiling, open mouth|slightly open mouth|closed-mouth smile
```

### 構図
```text
()|(face close-up:0.9)|upper body|upper body|full body|full body|full body|full body|full body|wide shot|(from side:0.8)|(from above:0.8)|(low angle:0.8)|(from behind, looking back:0.8)
```

### 背景 Ex 版

背景は、項目ごとにまとめてあるから、全部くっつけて1つの背景ノードにするのも、<br/>
それぞれ別ノードにして組み合わせるのも、おぬしの好きな方を選べるようにしたぞ！<br/>
同じ項目を繰り返したり、不要な項目を削除したりして、おぬし好みのプロンプトに育てておくれなのじゃ。

#### Ex 標準背景
```text
indoor{
  girl's room,
  bedroom,
  living room,
  kitchen,
  dining room,
  bathroom,
  attic,
  basement,
  coffee shop,
  cafe terrace,
  library,
  private library,
  classroom,
  music room,
  science room,
  computer room,
  school infirmary,
  gymnasium,
  office,
  meeting room,
  conference room,
  laboratory,
  medical room,
  art studio,
  art gallery,
  museum,
  aquarium,
  planetarium,
  observatory interior,
  bookstore,
  bakery,
  flower shop,
  convenience store,
  supermarket,
  restaurant,
  bar,
  diner,
  karaoke room,
  arcade,
  game center,
  cinema,
  concert hall,
  theater,
  dance studio,
  school hallway,
  locker room,
  stairwell,
  elevator hall,
  greenhouse,
  train interior,
  subway interior,
  airport terminal,
  shopping mall,
  hotel room,
  lobby,
  chapel interior,
}
Outdoor{
  city,
  town,
  downtown,
  residential area,
  park,
  playground,
  plaza,
  rooftop,
  balcony,
  terrace,
  train station,
  bus stop,
  airport runway,
  shopping street,
  courtyard,
  bridge,
  crosswalk,
  intersection,
  riverside,
  canal,
  harbor,
  port,
  boardwalk,
  marketplace,
  festival street,
  food stall area,
  alley,
  back alley,
  village,
  suburban street,
  schoolyard,
  campus,
  parking lot,
  construction site,
  amusement park,
  theme park,
  zoo,
  stadium exterior,
  cemetery,
  clock tower,
  lighthouse,
  windmill,
  waterfront,
}
Nature{
  lake,
  pond,
  waterfall,
  river,
  stream,
  flower garden,
  rose garden,
  forest,
  bamboo forest,
  pine forest,
  rainforest,
  grasslands,
  meadow,
  savanna,
  sea,
  ocean,
  coral reef,
  mountain,
  mountain path,
  hilltop,
  valley,
  cliff,
  flower field,
  sunflower field,
  lavender field,
  beach,
  shore,
  island,
  tropical island,
  cave,
  crystal cave,
  botanical garden,
  jungle,
  swamp,
  marsh,
  desert,
  oasis,
  snowfield,
  glacier,
  ice cave,
  volcanic area,
  hot spring,
  starry sky,
  night sky,
  aurora,
}
traditional{
  Japanese garden,
  shrine,
  temple,
  tea house,
  tatami room,
  engawa,
  onsen,
  ryokan,
  festival grounds,
  torii gate,
  bamboo grove path,
  castle,
  fortress,
  palace,
  ruins,
  old town,
  stone pavement,
  pagoda,
  dojo,
  samurai residence,
  courtyard garden,
}
```

#### Ex ファンタジー特盛背景
```text
Fantasy{
  (),
  magic library,
  alchemy workshop,
  wizard tower,
  enchanted forest,
  fairy garden,
  floating island,
  sky castle,
  crystal palace,
  ancient ruins,
  mystic cave,
  dragon's lair,
  underground city,
  sacred spring,
  giant tree,
  mirror lake,
  celestial garden,
  forgotten temple,
  phantom town,
  clockwork city,
  throne room,
  dungeon,
  cathedral,
  portal site,
  magic academy,
  sorcerer's tower,
  witch's cottage,
  fairy village,
  elven forest,
  dwarf mine,
  crystal cave,
  ancient altar,
  holy sanctuary,
  forbidden library,
  sky temple,
  floating garden,
  moonlit lake,
  starlight forest,
  enchanted castle,
  royal palace,
  hidden village,
  ancient labyrinth,
  monster arena,
  summoning chamber,
}
Japanese-style Fantasy{
  (),
  moonlit shrine,
  mystic shrine,
  ancient shrine,
  forgotten shrine,
  mountain shrine,
  forest shrine,
  torii gate,
  spirit forest,
  youkai village,
  oni castle,
  kitsune shrine,
  tanuki forest,
  sacred mountain,
  hidden onsen,
  samurai castle,
  ninja village,
  abandoned temple,
  bamboo spirit path,
  misty bamboo forest,
  sakura spirit realm,
  red torii path,
  shrine festival night,
  haunted Japanese mansion,
  old samurai residence,
  floating lantern river,
  dragon god shrine,
  celestial fox shrine,
  underworld gate,
}
Chinese-style Fantasy{
  (),
  ancient Chinese palace,
  imperial palace,
  jade palace,
  celestial palace,
  xianxia sect,
  martial arts sect,
  mountain cultivation temple,
  immortal mountain,
  cloud sea,
  bamboo mountain path,
  lotus pond,
  moon gate garden,
  Chinese courtyard,
  ancient Chinese city,
  lantern street,
  water town,
  stone bridge town,
  dragon palace,
  phoenix palace,
  taoist temple,
  misty peak,
  sword cultivation arena,
  heavenly staircase,
  jade pavilion,
  floating pagoda,
  immortal cave,
  spirit spring,
  celestial river,
}
Fantasy-ish{
  (),
  gothic castle,
  vampire mansion,
  haunted mansion,
  dark cathedral,
  graveyard,
  crypt,
  necromancer's lair,
  witch market,
  night carnival,
  dream world,
  mirror world,
  toy kingdom,
  candy kingdom,
  steampunk city,
  airship dock,
  mechanical tower,
  clock tower interior,
  abandoned laboratory,
  magical observatory,
  starship temple,
  ancient machine room,
  lost civilization,
  desert ruins,
  sunken city,
  underwater palace,
  ice palace,
  volcanic fortress,
  shadow realm,
  celestial battlefield,
}
```

#### Ex 季節/イベント背景
```text
Spring{
  (),
  cherry blossoms,
  sakura avenue,
  hanami,
  spring festival,
  graduation ceremony,
  entrance ceremony,
  easter,
  flower viewing picnic,
  rainy season,
  hydrangea garden,
  children's day,
  doll festival,
  easter egg hunt,
}
Summer{
  (),
  summer festival,
  festival night,
  food stalls,
  lantern festival,
  bon festival,
  fireworks,
  fireworks festival,
  poolside,
  water park,
  beach party,
  tropical vacation,
  campground,
  tanabata,
  tanabata festival,
  star festival,
}
Autumn{
  (),
  autumn leaves,
  maple forest,
  harvest festival,
  moon viewing,
  halloween,
  halloween party,
  halloween street,
  pumpkin patch,
  haunted house,
  masquerade party,
  autumn festival,
  thanksgiving,
}
Winter{
  (),
  snowy town,
  snow festival,
  ice skating rink,
  christmas,
  christmas market,
  christmas tree,
  christmas party,
  illuminations,
  winter holiday,
  new year,
  new year's shrine visit,
  first sunrise,
  snowy shrine,
  winter illuminations,
  new year's festival,
  new year's eve party,
  winter market,
  christmas dinner,
  holiday shopping street,
  valentine's day,
}
(){
  white day,
  wedding ceremony,
  birthday party,
  anniversary,
  school festival,
  cultural festival,
  sports festival,
  idol concert,
  live event,
  tea party,
  garden party,
  picnic,
  parade,
  carnival,
  temple fair,
}
```
