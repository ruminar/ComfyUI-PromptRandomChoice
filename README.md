# ComfyUI-PromptRandomChoice

English | [日本語](README.ja.md)

A lightweight random-choice node that quickly draws a new "prompt gacha" result as your workflow runs.

Want to vary backgrounds and weather while leaving a workflow running overnight?<br/>
This node is designed for that job, with an execution time as low as 0.010 seconds in the author's environment.

It is especially useful when you want to randomize backgrounds, time of day, weather, and other prompt parts independently.<br/>
You can place multiple instances in one workflow; each instance keeps its own selection state.


## v0.6.0

v0.6.0 adds Runtime nodes for editing candidates while queued jobs are running, plus control prefixes for managing candidate lists.

- `Runtime Prompt Random Choice`
- `Runtime Prompt Random Choice Ex`
- Temporarily disable candidates whose trimmed text starts with `#`
- In Runtime nodes, force a candidate starting with `!` at the next reselection point
- Detect Cartesian-product syntax in Ex nodes before expansion and stop with an error
- While editing Runtime Ex input, unmatched braces keep using the last accepted valid candidate set

Compatibility notes:

- A leading `#` is now treated as a comment in the non-Runtime nodes too
- Adjacent child groups such as `scene{day|night}{clear|rain}` are no longer supported
  - Cartesian products are prohibited in Ex nodes as of this version
  - Use separate Ex nodes and combine their outputs with String Join when you need independent axes

## v0.5.0

Added `Safe Random Seed`.

- `Safe Random Seed`
  - A small KSampler-oriented node that only outputs non-negative random seeds
  - Generates values server-side with Python's `secrets` module
  - Updates its title after execution, for example `Seed: 4897362896`

## v0.4.0

Added `Prompt Random Choice Ex`.

- `Prompt Random Choice`
  - Selects one item from a flat candidate list
- `Prompt Random Choice Ex`
  - Supports both flat candidates and nested candidate branches written with `{}`
  - Counts leaves and selects one path so every final leaf has equal probability
  - Avoids materializing every completed string in advance

Both nodes provide the same outputs.

- `selected_text`
- `selected_text_safe`

## Features

- **Random selection on execution**
  - Queue as many jobs as you like; the node reselects according to `change_every`.

- **Use `|` or real line breaks as separators**
  - Both forms can be mixed in the same input.
  - Empty items created by repeated separators are ignored.
    - Write `()` when you explicitly want an empty-string candidate.

- **Automatic cleanup of surrounding commas and whitespace**
  - `town,`
  - `coffee shop,`
  - `castle, fortress,`
  These styles are all accepted.

- **Current result shown in the node title**
  - The title updates after execution, for example `Ch: coffee shop`.
  - This makes it easy to compare the selected prompt with the KSampler preview.

- **Safe random seeds for KSampler**
  - `Safe Random Seed` outputs non-negative integers only.
  - Its title updates after execution, for example `Seed: 4897362896`.

- **Multiple independent instances**
  - Use separate nodes for backgrounds, time of day, weather, and other independent prompt axes.

- **Filename-friendly output**
  - `selected_text_safe` returns a sanitized form suitable for filenames.

- **Explicit empty candidate `()`**
  - When selected, the prompt output is an empty string and the filename output is `empty`.

- **Candidate comments**
  - A candidate whose trimmed text starts with `#` is excluded from selection.
  - Comments work at every level in Ex nodes.

- **Runtime editing**
  - Runtime nodes use the latest candidate set accepted by the server, even after jobs have been queued.
  - `!` forces a candidate only in Runtime nodes; non-Runtime nodes treat it as ordinary text.

## Additional Prompt Random Choice Ex features

- **Nested candidate branches with `{}` in addition to flat candidates**
  - Unlike ComfyUI's standard selection notation, groups can be nested.
    - Inner selections are evaluated as child branches and joined to their parent with commas.
  - Both `|` and real line breaks separate candidates and may be mixed.
  - Empty items created by repeated separators are ignored.
    - Write `()` to explicitly return an empty string.
    
An example is the easiest way to see how this works.
```text
town|zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
```

Conceptually, this expression has the following leaf candidates.

```text
town
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

One of these five candidates is selected.<br/>
The selector uses each branch's leaf count to choose one path with equal probability for every final leaf. It does not materialize all completed strings in advance.
<br/>

## Installation

Run the following command in ComfyUI's `custom_nodes` directory.

```bash
git clone https://github.com/ruminar/ComfyUI-PromptRandomChoice.git
```

## Usage

The `Prompt Random Choice` category in the Add Node menu contains the standard nodes, Runtime nodes, and Safe Random Seed.

First, choose the node that matches your use case.

| What you want to do | Node |
| --- | --- |
| Select one item from a simple list | `Prompt Random Choice` |
| Write parent-child candidates with `{}` | `Prompt Random Choice Ex` |
| Edit a simple candidate list while queued jobs are running | `Runtime Prompt Random Choice` |
| Edit a candidate list containing `{}` while queued jobs are running | `Runtime Prompt Random Choice Ex` |

1. Add the appropriate node from the table above
2. Enter candidates in `options_text` (see [Input examples](#input-examples))
3. Set `change_every` as needed
4. Connect `selected_text` to a String Join-style node and add it to the positive prompt
5. Queue as many jobs as you like

With `change_every = 1`, the node reselects for every job. With `change_every = 3`, it uses the same candidate for three jobs. Leave it at `1` if you are unsure.

<br/>
<img width="544" height="526" alt="image" src="https://github.com/user-attachments/assets/d230659e-f008-4232-955d-1fa6fdf299fa" /><br/><br/>

<img width="594" height="555" alt="image" src="https://github.com/user-attachments/assets/7966c50e-15c7-41cf-b167-06a54054acec" /><br/>
Once configured, you may want to collapse the node to save canvas space.

### Tune candidates while generation continues with a Runtime node

With ordinary random selection, you do not know when the candidate you want to tune will appear again. Runtime nodes let you temporarily force a candidate by adding an ASCII `!` to the start of it. In the non-Runtime `Prompt Random Choice` and `Prompt Random Choice Ex` nodes, `!` is ordinary text and does not force a selection.

This gives you a practical edit-and-preview loop without stopping the queue.

```text
Choose a random candidate you want to tune
  ↓
Add ! to its beginning to force it temporarily
  ↓
Edit the candidate while reviewing generated images
  ↓
Remove ! when satisfied and return it to the random pool
```

For interactive tuning, set `change_every = 1` before adding jobs to the queue. After the input status becomes `LIVE`, the latest accepted candidates are evaluated by the next job. Edits do not alter a job that is already running.

#### 1. Start with a normal candidate list

Use line breaks or `|` to separate candidates.

```text
black hair, straight long hair,
dark brown hair, short cut,
blonde hair, long hair,
```

#### 2. Force the candidate you want to tune with `!`

To review only the blonde-hair candidate, add `!` to the beginning of its trimmed text. The `!` itself is removed from the output.

```text
black hair, straight long hair,
dark brown hair, short cut,
!blonde hair, long hair,
```

If more than one candidate at the same level starts with `!`, a Runtime node uses the first one from the top.

#### 3. Tune it while the queue keeps running

Wait until the input shows `LIVE`, then edit the forced candidate while reviewing the generated images.

```text
black hair, straight long hair,
dark brown hair, short cut,
!gold yellow hair, very long hair, blue eyes, small ahoge, side braid, black ribbon,
```

With `change_every = 1`, the latest content accepted by the server is used at the next job's selection point. You do not need to clear and rebuild the queue.

#### 4. Remove `!` when tuning is complete

When you are satisfied, remove `!`. The tuned text returns to the normal random candidate pool.

```text
black hair, straight long hair,
dark brown hair, short cut,
gold yellow hair, very long hair, blue eyes, small ahoge, side braid, black ribbon,
```

#### When `change_every` is 2 or greater

`change_every` controls how many times the current selected result is reused. With `change_every = 3`, editing candidates or adding `!` does not interrupt the current holding period.

```text
Run 1: Select A
       ↓ Add !B in the Runtime input
Run 2: A
Run 3: A
Run 4: Evaluate the latest candidates and select B
```

This is useful when comparing three images per candidate. Use `change_every = 1` when you want to review each edit on the next job.

#### Forcing a path in Runtime Ex

In Runtime Ex, `!` only forces the level where it appears. To force one complete path from parent to child, add `!` separately at every level on that path.

```text
black hair{
  straight long hair
  short cut
}
!blonde hair{
  !long hair
  wavy long hair
}
```

This example forces `blonde hair` at the top level and `long hair` in its child group, producing `blonde hair, long hair`.

## Input examples

### Line-break separated (a comma before the line break is optional)

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

### `|` separated

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
### A candidate that adds nothing

`()` is an explicit empty candidate.

```text
()|(full body:0.9)
```

This example randomly switches between adding nothing and adding `(full body:0.9)`.

### Adjusting selection probability

Repeat a candidate to make it more likely to be selected.

```text
day|day|day|sunset|night
```

This is useful when you want mostly daytime images with occasional sunset or night scenes.

<br/>

## Core rules

- Split candidates on `|` or real line breaks
- The two-character string `\n` is not a separator
- Trim surrounding whitespace and commas from each candidate
- Ignore empty candidates
- Treat `()` as an explicit empty candidate
- Exclude a candidate as a comment when its trimmed text starts with `#`
- Treat `!` as ordinary text in non-Runtime nodes
- Reselect every run when `change_every` is 1
- Keep the same result for the specified number of runs when `change_every` is 2 or greater
- Show values such as `Ch: lake` or `Ch: (empty) (2/3)` in the title after execution
- Show a value such as `Seed: 4897362896` in the Safe Random Seed title after execution

## Safe Random Seed

Generates one non-negative random seed for KSampler.
A generic integer Primitive may produce negative values when randomized; this node never does.
It is a small safeguard against `expected non-negative integer` errors from SDE-family samplers.

- No inputs
- One output: `seed`
- Uses Python's `secrets` module on the ComfyUI server
- Generates a new value when the node executes
- Output range: `0` through `2^53 - 1`
- Connecting one node to multiple destinations sends the same seed to all of them
- Add multiple `Safe Random Seed` nodes when you need independent values
- The previous output does not affect the next generated seed
- Updates the node title after execution, for example `Seed: 4897362896`

## Prompt Random Choice

Selects one item from a candidate list.

```text
town|park|lake|coffee shop
```

`()` is an explicit empty candidate.

```text
()|(full body:0.9)
```

## Prompt Random Choice Ex

You can use the same flat candidate lists accepted by `Prompt Random Choice`.

```text
town|park|lake|coffee shop
```

You can also add a child group with `{}` so that extra candidates are evaluated only under the selected parent.

```text
town|zoo{animals{birds|penguins}|aquarium,{fish|jellyfish}}
```

Conceptually, this input has the following final leaf candidates.

```text
town
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

One of these five candidates is selected.

### Multiline Ex example

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

Possible outputs:

```text
zoo, animals, birds
zoo, animals, penguins
zoo, aquarium, fish
zoo, aquarium, jellyfish
```

### Ex rules

- Separate candidates with real line breaks or `|`
- Ignore empty candidates
- Treat `()` as an explicit empty candidate
- Separate candidates inside `{}` with real line breaks or `|` as well
- Exclude `#` comment candidates at every level
- Join selected child text to its parent with `, `
- Weight each path by its leaf count so all final leaves have equal probability
- Do not materialize every completed candidate string in advance
- Enforce safety limits on nesting depth and leaf count
- Allow at most one direct child group per candidate
- Reject Cartesian-product syntax such as `A{B|C}{D|E}` before expansion
- Literal `{` and `}` characters in prompt text are not supported

### Cartesian-product syntax

Vertical nesting is allowed, and multiple parent candidates with their own child groups may appear at the same level.

```text
black hair{straight long hair|short cut}
blonde hair{long hair|wavy long hair}
```

However, one candidate cannot contain multiple adjacent child groups.

```text
A{B|C}{D|E}
```

This syntax creates a Cartesian product and therefore raises an error before candidate expansion. Put independent axes in separate `Prompt Random Choice Ex` nodes and combine their outputs with String Join.

## Runtime Prompt Random Choice

<img width="699" height="420" alt="image" src="https://github.com/user-attachments/assets/fea5989f-6348-404f-87c5-aa5506113b71" />

`Runtime Prompt Random Choice` and `Runtime Prompt Random Choice Ex` use the latest candidate text accepted by the ComfyUI server at execution time. The candidate input displays its synchronization state.

- `EDITING`: Input is being edited or waiting to be sent
- `SYNCING`: Input is being sent to the server
- `LIVE`: The server has accepted the latest input
- `EDITING / SYNTAX INCOMPLETE`: Ex braces are temporarily unmatched; the last valid revision remains active
- `HARD ERROR`: Structurally complete but unsupported syntax; executions stop until it is corrected
- `SYNC ERROR`: Communication or synchronization error

### Forced selection with `!`

`!` is active only in Runtime nodes. If multiple candidates at the same level start with `!`, the first one from the top is used. The leading `!` is not included in the output.

```text
black hair
!blonde hair
!silver hair
```

This example uses `blonde hair`. `!()` forces an empty string. The non-Runtime `Prompt Random Choice` and `Prompt Random Choice Ex` nodes treat `!` as ordinary text.

Runtime Ex applies the first `!` independently at each level. It restricts only that level's branch; child levels under the selected branch are still evaluated.

### Runtime and `change_every`

Runtime editing updates the candidate set, not the completed string currently being held. With `change_every = 3`, the current result is kept for all three runs even if you edit, remove, comment out, or force candidates during that period.

```text
Run 1: Select A
Run 2: A
Run 3: A
Run 4: Reselect from the latest candidate revision
```

`!` overrides normal random selection at the next reselection point; it does not interrupt the current holding period. Use `change_every = 1` when edits should affect the next job. `change_every` itself is not synchronized at Runtime—the value submitted with the queued workflow is used.

### Runtime Ex syntax errors

- Unmatched braces are treated as a temporary editing state and are not accepted as a new revision. Generation continues with the last accepted valid candidate set.
- A Cartesian product caused by adjacent child groups is a Hard Error. It never silently falls back to old candidates; the next execution raises an error.

## Outputs

- `selected_text`  
  The selected string after trimming.<br/>
  Returns the empty string `""` when `()` is selected.

- `selected_text_safe`  
  A filename-safe version of the selected string.<br/>
  Returns `empty` when `selected_text` is empty.

## Recommended workflow structure

Connect `selected_text` to a string-combination node such as kjnodes' `Join String Multi`, and manage delimiters on the joining side.

Place multiple `Prompt Random Choice` or `Prompt Random Choice Ex` nodes side by side to randomize backgrounds, time of day, weather, composition, and other independent axes separately.

Ex is not intended to put every independent dimension into one node. Use it for real parent-child relationships—for example, adding animal candidates only when `zoo` is selected.

<br/>

## Difference from standard `{day|night|morning}` selection syntax

- ComfyUI also supports `{a|b|c}` for random prompt choices.<br/>
  That syntax is resolved when the prompt is processed by `CLIP Text Encode`.

- `PromptRandomChoice`, by contrast, resolves one candidate earlier and outputs only the selected text as a normal `STRING`.<br/>
  Unselected candidates never travel downstream.

  - This can make LoRA trigger words safer to use inside candidate lists because only the selected trigger text reaches later nodes.<br/>
    It also makes the resolved state more explicit in the workflow than standard `{a|b|c}` syntax.
    - This does **not** load or unload the LoRA itself.<br/>
      "Safer" here only means that unselected trigger-word text is not passed downstream.

- Candidate lists can use the same `|` separator as standard `{a|b|c}` syntax.<br/>
  This makes it easy to move the contents of a standard group into `PromptRandomChoice`, or wrap a flat list in `{}` and move it back into prompt text.

- When comparing generated images, changing prompt candidates every run can make differences difficult to judge.<br/>
  `change_every` lets `PromptRandomChoice` keep one candidate for several runs before selecting another.

- The candidate resolved by `PromptRandomChoice` is also displayed in the node title.
  - You can compare it directly with the KSampler preview.
  - When `change_every` is greater than 1, the title also shows progress such as `Ch: lake (2/3)`.

<br/>

## Development specifications and regression tests

Internal implementation requirements are documented in Japanese starting from [`.spec/README.md`](.spec/README.md).

The regression suite runs with the Python standard library only.

```bash
python -B -m unittest discover -s tests -v
```

GitHub Actions automatically runs the Python regression suite and JavaScript syntax checks on pushes and pull requests.

## License

GPL-3.0, following ComfyUI's license requirements.

## Promotional images (Japanese)

<img width="1055" height="1491" alt="PromptRandomChoice overview" src="https://github.com/user-attachments/assets/7a4f1b5f-c77b-4e47-90af-cbd0330c85fe" />

Ex version
<img width="1122" height="1402" alt="PromptRandomChoiceEx overview" src="https://github.com/user-attachments/assets/f45a44b7-5692-4d98-854a-7736677e1f5a" />

Runtime version
<img width="1055" height="1491" alt="Runtime PromptRandomChoice overview" src="https://github.com/user-attachments/assets/b766c03e-9d95-4e88-9bd2-1b448f4e21c7" />


## Copy-ready recommended candidate lists

### Background

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

### Time of day
```text
()|day|day|day|morning|sunset|night
```

### Weather
```text
()|Strong sunshine|(clear sky:0.9)|(clear sky:0.9)|(clear sky:0.9)|(cloudy sky:0.9)|rain|snow|Rainbow after Rain|storm, thunder
```

### Lighting
```text
()|soft lighting|warm lighting|natural lighting|(backlighting:0.8)|(dramatic lighting:0.8)|(cinematic lighting:0.8)
```

### Pose, gaze, and action
```text
()|standing|sitting|walking|looking at viewer|waving|hands on hips|jumping high|running|skipping|looking up
```

### Expression
```text
()|smiling|gentle smile|serious expression|surprised expression|slightly surprised|shy expression|happy expression|smiling, open mouth|slightly open mouth|closed-mouth smile
```

### Composition
```text
()|(face close-up:0.9)|upper body|upper body|full body|full body|full body|full body|full body|wide shot|(from side:0.8)|(from above:0.8)|(low angle:0.8)|(from behind, looking back:0.8)
```

### Background — Ex version

The background candidates are grouped by theme. You can combine them into one background node,<br/>
or put each group in a separate node and mix them independently.<br/>
Repeat items to increase their probability, remove anything you do not need, and customize the lists to suit your workflow.

#### Standard backgrounds for Ex
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

#### Extra-rich fantasy backgrounds for Ex
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

#### Seasonal and event backgrounds for Ex
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
