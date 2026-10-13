# mapping.md — sympy__sympy-16886

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c50643a49811e9fe2f4851adff4313ad46f7325e`, states the type
abstraction, and gives the provenance of the deep model (the changed data
table) checked by axiom_check.py / G-AX. There is **no consumed axiom**.

Repo file under change: `sympy/crypto/crypto.py`.

## 1. Symbol ↔ repo binding

The modelled unit is the **per-word encoding step** of `encode_morse` — the
inner loop that turns one word into its Morse rendering:

```python
1574    for word in words:
1575        morseword = []
1576        for letter in word:
1577            morseletter = mapping[letter]
1578            morseword.append(morseletter)
1579
1580        word = sep.join(morseword)
```

That is the step the changed table feeds, and the only step whose behaviour the
gold patch alters. On the modelled domain (§2) the surrounding pass is the
identity, so the model function also equals the whole real `encode_morse` there;
that is what conformance_check.py compares against (G-CONF).

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `encode_morse(msg, sep)` | the per-word encoding step of `encode_morse(msg, sep='|', mapping=None)` — `sympy/crypto/crypto.py:1574-1580` (function defined at `:1539`), i.e. `word ↦ sep.join(mapping[letter] for letter in word)` | the modeled changed behaviour (the step that consumes the table) |
| `morse_list(c)` | one dictionary lookup `mapping[letter]` (`crypto.py:1577`), where `mapping == char_morse` (`crypto.py:1536`, via `mapping = mapping or char_morse` at `:1559`) | the per-symbol table lookup, modeled as an executable `List[int]` builder |
| `morse_of(c)` *(deep model — A-reference)* | the per-symbol Morse representation table: `char_morse = {v: k for k, v in morse_char.items()}` (`crypto.py:1536`), inverted from `morse_char` (`crypto.py:1509-1535`) | pure spec: Morse signal sequence for one symbol; the deep model of the changed data table, validated `morse_of == char_morse` **on all 52 keys** by axiom_check.py (G-AX), NOT consumed as an axiom |
| `encoded_seq(s, sep)` | the join of the per-symbol codes by the separator: `word = sep.join(morseword)` (`crypto.py:1580`) | pure spec: encoding of a whole word as the per-symbol codes joined by a single separator signal |
| `dot()` / `dash()` | the literal Morse signal characters `'.'` (ord 46) and `'-'` (ord 45) used in the `morse_char` keys (`crypto.py:1509-1535`) | pure spec: the two Morse signals as code points |
| `represented(c)` | membership in the table's key set, `set(mapping.keys())` (`ok`, `crypto.py:1569`) minus the `' '` key added at `:1562` — equivalently `c in char_morse` for the table as written at `:1536` | pure spec: the predicate that says the table gives `c` a representation; the 52 code points `'A'`..`'Z'`, `'0'`..`'9'`, `! $ ' ( ) + , - . / : ; = ? @ _` |
| `no_signals()` | the empty Morse rendering: what a character the table does not represent contributes, because it is deleted by `translate(msg, None, ''.join(chars - ok))` (`crypto.py:1570`) before the per-word step runs | pure spec: the empty signal sequence |
| `sep_accepted(c)` | the guard `assert sep not in mapping` at the top of `encode_morse` (`crypto.py:1560`), with `mapping == char_morse` plus the `' '` key added by `mapping[" "] = word_sep` (`crypto.py:1562`) | pure spec: the separator-acceptance predicate — True iff the real encoder returns normally rather than raising `AssertionError` on that separator (see §2, separator row) |

The single changed line of the gold patch is in `morse_char` (`crypto.py:1523`):
`"-----": "0", "----": "1",` → `"-----": "0", ".----": "1",`. Because
`char_morse` inverts `morse_char`, the change is observed as
`char_morse['1']`: pre-patch `'----'` (four dashes), post-patch `'.----'`
(dot + four dashes). The per-word step maps each character of a word to
`mapping[letter]`, so `encode_morse('1...')` emits the corrected code.

## 2. Type abstraction and modelled domain (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| one `word` of the split plaintext, a `str` (`crypto.py:1574`) | `List[int]` of Unicode code points | `msg[k]` ↔ `ord(word[k])`; `len` and indexing mirror `str`. |
| a Morse code `str` (e.g. `'.----'`) | `PSeq[int]` / `List[int]` over `{46, 45}` | `'.'` ↔ `dot()` = 46, `'-'` ↔ `dash()` = 45; `str` concatenation ↔ `PSeq`/list `+`. |
| the separator `sep` (default `'|'`, a single character) | a single `int` code point `sep`, required **accepted** (`sep_accepted(sep)`) | `sep.join(...)` ↔ inserting `PSeq(sep)` between adjacent symbol codes. |
| `translate(msg, None, ''.join(chars - ok))` (`crypto.py:1570`), whitespace normalisation (`:1566`), word splitting (`:1573`), the word join and trailing-whitespace suffix (`:1583`) | outside the modelled unit | unchanged plumbing, orthogonal to the bug; §2.1 records what each of these guarantees about the per-word step's input, which is what licenses the modelled domain. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification join is phrased over `PSeq[int]` via `ToSeq`.

### 2.1 Every domain restriction points at a real guard

The precondition of the model's `encode_morse` is exactly three facts about the
word and one about the separator. Each is enforced by a specific statement of
the real function, so the modelled domain is the per-word step's **actual**
input set, not a convenience:

1. **Every symbol of the word is `represented`.**
   `chars = set(''.join(msg.split()))`, `ok = set(mapping.keys())`,
   `msg = translate(msg, None, ''.join(chars - ok))` (`crypto.py:1568-1570`)
   DELETES every non-whitespace character the table does not represent before
   any word is formed. So `mapping[letter]` at `:1577` is only ever handed a key
   of the table. axiom_check.py proves this mechanically rather than by reading:
   it passes a recording `dict` subclass as `mapping=` and asserts that every
   key the real encoder looks up is a represented, non-whitespace single
   character, over a 17-message corpus that includes unrepresented characters,
   lower case, and runs of assorted whitespace (G-AX, A-reference 4).
2. **No symbol of the word is whitespace.**
   `words = msg.split()` (`crypto.py:1573`) — `str.split()` with no argument
   never yields a piece containing whitespace. (The `' '` key that
   `mapping[" "] = word_sep` adds at `:1562` therefore never reaches the lookup
   either.) This is why the modelled domain may exclude code point 32 and the
   other whitespace code points without leaving an exploitable branch: a guard
   keyed on whitespace inside a word cannot fire in the repository.
3. **The word may be empty.** `str.split()` never yields an empty piece, so the
   empty word is a *widening* of the real input set: the model pins a behaviour
   (`encoded_seq` of the empty word is `no_signals()`) that the repository never
   exercises. A widening only ever adds obligations, and this one removes the
   `Requires(len(msg) >= 1)` dead branch that a coarser binding of the model to
   the whole encoder could exploit (a rival that special-cases the empty input).
4. **The separator is accepted.** `assert sep not in mapping`
   (`crypto.py:1560`) RAISES `AssertionError` when the separator is itself a
   represented character; and because `mapping[" "] = word_sep` (`:1562`)
   mutates the module-level `char_morse`, `' '` is a mapping key from the second
   call on. `sep_accepted` spells out exactly that reject set
   (`not (c == 32 or represented(c))`), and `Requires(sep_accepted(sep))` keeps
   rejected separators OUTSIDE the modelled domain: the model only claims a
   normal return where the real function returns normally (e.g.
   `encode_morse('1', sep='0')` raises in the repo and is not in the domain).
   G-AX checks both the set identity and the observable `AssertionError`.
   An accepted separator is in particular distinct from the two signal code
   points 46/45 (both are represented punctuation), so the join is unambiguous;
   `'|'` is code point 124, accepted, and is the default the F2P tests use.

Because a precondition always leaves branches the verifier does not constrain,
refinement.md §E states the **refinement rule** that goes with this binding: a
branch in `morse_list`'s impl region refines to an entry of the table
(`:1536`/`:1577`) — a region with no excluded input, since `morse_of` is total —
and a branch in `encode_morse`'s impl region refines to a statement **inside the
per-word loop body** (`:1575-1580`), never to a guard at the top of the
repository function (`:1539`), whose parameter is the whole plaintext and not
this model's `msg`. §E.2 tabulates every input the domain excludes against the
guard above that makes it unreachable there.

**Residual narrowing (declared).** The model's `sep` is a single code point,
while the real parameter is an arbitrary `str` — the F2P test also calls
`encode_morse(' ', sep='``')` with a two-character separator. No `int`-valued
branch of a model implementation can observe or exploit that difference, so the
abstraction closes no attack surface; and every F2P call with a multi-character
or whitespace-only message has an **empty word list**, so the per-word step this
model binds never runs for it (refinement.md §D).

**Total-correctness obligation.** The real per-word step is one bounded pass
over the word that always returns its rendering; Nagini is a
partial-correctness verifier by default, so without an explicit obligation a
diverging implementation (endless loop, bare self-recursion) would satisfy
every `Ensures` vacuously while never delivering the encoding. The spec
therefore carries `Requires(MustTerminate(3))` on `encode_morse` (consumed by
the encoding loop with the strictly decreasing, bounded-below measure
`i + 2`) and `Requires(MustTerminate(2))` on `morse_list` (a straight-line
table lookup callable from the encoder's body without leaking the
obligation).

**Read-only input.** `Requires(Acc(list_pred(msg), 1/2))` and the matching
`Ensures` abstract the fact that the per-word step READS the word (a Python
`str`, immutable) and builds the codes in a fresh carrier `morseword`
(`crypto.py:1575-1578`); it never writes to its input. The half permission is
what rejects an implementation that mutates `msg` to satisfy the postcondition
(properties.py, `rival-frame-mutate-msg`).

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `morse_of` deep model ↔ the `char_morse` table (A-reference)
**Source:** `sympy/crypto/crypto.py`. The Morse representation table is the
module-level dict `morse_char` (`crypto.py:1509-1535`), mapping each Morse code
string to a character; the encoder uses its inverse
`char_morse = {v: k for k, v in morse_char.items()}` (`crypto.py:1536`). The
changed operation is this **data table**, so it is modeled DEEPLY by the
`@Pure` function `morse_of` (with `dot`/`dash`) in the `pure` region; there is
**no `@ContractOnly` axiom** the proof consumes. The deep model is validated
equal to the real table out-of-band by axiom_check.py (G-AX).

`morse_of` is **total on `int`**: it spells out all 52 represented code points
and returns `no_signals()` for every other one. Totality is what leaves an
implementation no unconstrained branch — the postcondition
`ToSeq(Result()) == morse_of(c)` of `morse_list` carries no `Requires` on `c`
and therefore pins the lookup on the whole code space. The 52 entries, as
`morse_of` encodes them and as the gold `char_morse` holds them:

```
A  '.-'       B  '-...'     C  '-.-.'     D  '-..'      E  '.'
F  '..-.'     G  '--.'      H  '....'     I  '..'       J  '.---'
K  '-.-'      L  '.-..'     M  '--'       N  '-.'       O  '---'
P  '.--.'     Q  '--.-'     R  '.-.'      S  '...'      T  '-'
U  '..-'      V  '...-'     W  '.--'      X  '-..-'     Y  '-.--'
Z  '--..'
0  '-----'    1  '.----'    2  '..---'    3  '...--'    4  '....-'
5  '.....'    6  '-....'    7  '--...'    8  '---..'    9  '----.'
.  '.-.-.-'   ,  '--..--'   :  '---...'   ;  '-.-.-.'   ?  '..--..'
-  '-....-'   _  '..--.-'   (  '-.--.'    )  '-.--.-'   '  '.----.'
=  '-...-'    +  '.-.-.'    /  '-..-.'    @  '.--.-.'   $  '...-..-'
!  '-.-.--'
```

The discriminating digit is `'1'`: the gold table maps it to `'.----'`
(dot + four dashes, five signals), whereas the pre-patch table mapped it to
`'----'` (four dashes only). `morse_of(49)` (model.py, `'1'` = code point 49)
returns `PSeq(dot(), dash(), dash(), dash(), dash())` = `'.----'`, matching the
gold table. Reference: International Morse Code, https://en.wikipedia.org/wiki/Morse_code
(the `[1]` reference in the function docstring).

**Soundness check (G-AX):** `axiom_check.py` imports the real repository module
(the post-patch source) and asserts

* **A-reference 1** — for **every one of the 52 keys** `ch` of the real
  `char_morse`, `morse_of(ord(ch)) == [ord(sig) for sig in char_morse[ch]]`,
  and that the real code is a string over `{'.', '-'}`;
* **A-reference 2** — `{c : represented(c)}` over the whole Unicode code space
  equals `{ord(k) for k in char_morse}`, and `morse_of(c) == []` for every one
  of the other 1 114 060 code points; plus the observational form of the same
  claim, that encoding a message equals encoding it with its unrepresented
  characters removed (the deletion at `crypto.py:1570`);
* **A-reference 3** — `sep_accepted` equals the real separator guard's accept
  set on every ASCII code point, and the rejection is observable
  (`AssertionError` for each of `'0' 'A' '5' '.' '-' '!' '$' ' '`, and a normal
  return for the default `'|'`);
* **A-reference 4** — the recorded-`mapping` proof of §2.1(1): every character
  reaching `mapping[letter]` is represented and non-whitespace, and the
  recorded lookups are exactly the surviving characters of the message in
  order;
* every digit code is exactly five signals (the property the pre-patch
  `'1' -> '----'` violated), `char_morse['1'] == '.----'`, and the real
  `encode_morse` reproduces the F2P strings for `'12345'`, `'67890'`, `'ABC'`,
  `'SMS'`, `'!@#$%^&*()_+'` and `''`.

Exit 0 iff sound. It imports only the repository module under test; nothing
external. (Measured: it fails on the pre-patch table with
`morse_of deep model unsound on '1'`, and on a table whose `'A'` entry is
corrupted with `... unsound on 'A'`.)
