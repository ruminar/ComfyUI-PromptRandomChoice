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

- **候補の前後の `,` と空白を自動で整理**
  - `town,`
  - `coffee shop,`
  - `castle, fortress,`
  のような書き方でも大丈夫じゃ。

- **プロンプト結合向けの返り値**
  - 選ばれた候補の前後に `,` を付けて返すぞ。
  - 例: `coffee shop` → `,coffee shop,`

- **現在の選択結果をタイトル表示**
  - 実行時にノードタイトルが `Choice: coffee shop` のように更新されるぞ。
  - KSamplerのプレビューと見比べやすいのじゃ。

- **複数設置に対応**
  - 背景用、時間帯用、天気用など、複数ノードを置いてそれぞれ別々に使えるぞ。

## 導入方法

ComfyUIの `custom_nodes` ディレクトリで、以下のコマンドを打ち込むのじゃ！

```bash
git clone https://github.com/ruminar/ComfyUI-PromptRandomChoice.git
```

## 使い方

1. `Prompt Random Choice` ノードを置く
2. `options_text` に候補を入れる (入力例を参照)
3. 必要に応じて `change_every` を選ぶ (NEW)
4. `prompt_text` を文字列結合ノードなどでポジティブプロンプトへ足す
5. キューを好きなだけ積む

<br/>
<img width="415" height="642" alt="image" src="https://github.com/user-attachments/assets/b498aee3-07c3-4b00-94a6-d0c67af79de2" /><br/><br/>

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
- 有効な候補が1件も無い場合は空文字 `""` を返す
- 候補があれば `,selected,` を返す

## 出力

- `prompt_text`
  - 例: `,coffee shop,` (結合しやすいように、前後をtrimしてから`,`を付与します)

## ライセンス

GPL-3.0（ComfyUI本体の掟に従っておるぞ！）

## 宣伝画像

<img width="1024" height="1536" alt="PromptRandomChoice説明画像v0 2 0" src="https://github.com/user-attachments/assets/84bd447c-5b17-409b-aa3e-cfe4bf369bed" />
※ 区切り文字は 改行 または `|` です。カンマは候補の前後に付いた場合だけ自動で取り除きます。 <br/><br/>

(最初の版)
<img width="1024" height="1536" alt="PromptRandomChoice説明画像" src="https://github.com/user-attachments/assets/e5308bd1-82cb-4f9b-bd89-0dbddb7a009e" />
