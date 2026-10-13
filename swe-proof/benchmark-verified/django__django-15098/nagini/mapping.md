# mapping.md — django__django-15098

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2c7846d992ca512d36a73f518205015c88ed088c`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
compiled matcher the deep model is validated against by G-AX / axiom_check.py).

Repo file under change: `django/utils/translation/trans_real.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `language_prefix_len(path)` | the locale-prefix extraction performed by `language_code_prefix_re.match(path)` then `regex_match[1]` inside `get_language_from_path` — `django/utils/translation/trans_real.py:46` (the module-level `language_code_prefix_re`), consumed at `:508` (`regex_match = language_code_prefix_re.match(path)`) / `:511` (`lang_code = regex_match[1]`) | the modeled changed operation: given a request path, return the length of the extracted locale-code candidate (group 1), or `-1` when the matcher does not match |
| `prefix_len_spec(path, maxsep)` *(deep model — A-reference)* | the compiled regex `language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+){0,2})(/\|$)')` — `trans_real.py:46` (post-patch) | pure spec: the structural parse the regex performs; the deep model of the changed matcher, validated `prefix_len_spec(.,2) == real matcher` by axiom_check.py (G-AX), NOT a consumed axiom |
| `run_len`, `nsep`, `no_adjacent_sep`, `well_formed_tag`, `spec_unfold` | sub-structure of the same regex (`\w+`, the `([@-]\w+)` repeat group, the `{0,2}` bound, the trailing `(/\|$)`) | pure helpers spelling out the matcher's decision |
| `is_word(c)` *(consumed axiom — checked by G-AX)* | the `\w` character class as the matcher evaluates it, i.e. with **full Unicode** semantics | membership of ONE code point in the "word" class. `@ContractOnly`: its contract pins the class exactly **below** code point 128 (the ASCII word set) and leaves it **open** at/above 128, which is what the real Unicode class satisfies |
| `is_sep(c)` | the `[@-]` character class | a sub-tag separator `-` (45) or `@` (64) |

The pre-patch repo symbol the change edits (for the refinement audit): the same
module-level regex with the **old** body `r'^/(\w+([@-]\w+)?)(/|$)'` — i.e. the
`([@-]\w+)` group repeated `{0,1}` (the `?`) instead of `{0,2}`.

## 2. Unchanged downstream callee (handled by composition, not modeled here)

`get_language_from_path` (`trans_real.py:501`) is, post-patch:

```python
regex_match = language_code_prefix_re.match(path)
if not regex_match:
    return None
lang_code = regex_match[1]
try:
    return get_supported_language_variant(lang_code, strict=strict)
except LookupError:
    return None
```

`get_supported_language_variant` (`trans_real.py:464`) is **UNCHANGED** by the
patch. The only edit is the regex, which changes *which* candidate codes are
extracted and forwarded. The modeled operation is therefore the extraction
(`language_prefix_len`); the resolver is a downstream, unchanged callee applied
to the extracted code. The composition is behaviour-preserving in the sense the
fix relies on: for any path, `get_language_from_path(path)` =
`None` when no code is extracted, else `resolve(extracted_code)` — and `resolve`
is identical pre/post-patch. Hence pinning the extraction (the changed op) pins
the only behavioural delta. This is documented further in refinement.md (the
resolver is an **I** step — identical concrete callee — over the extracted code).
It is NOT referenced from the consumer spec view (no axiom, no symbol), so it
cannot leak and cannot be an over-claimed contract.

## 3. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` request path | `List[int]` of Unicode code points | `path[k]` ↔ `ord(path_str[k])`; `len` ↔ `len`; `"/" ↔ 47`, `"-" ↔ 45`, `"@" ↔ 64` |
| `str` value inside the specification | `PSeq[int]` (pure Viper sequence) via `ToSeq` | `PSeq` `take`/`drop`/`len`/`[i]` mirror `str` slice/`len`/index |
| `re.match(path)` truthiness + `match[1]` | `prefix_len_spec(path, 2) != -1` (matched) and the captured length `prefix_len_spec(path, 2)` | the captured group 1 is exactly the maximal candidate run after the leading `/`; its length is what the model returns. The captured *content* is `path[1 : 1+len]`, which the unchanged resolver consumes — see §2. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

### 3.1 The `\w` character class: consumed as an axiom, not approximated

Python's `re` evaluates `\w` on a `str` pattern with **full Unicode**
semantics, so the real class admits Unicode letters and digits (é, ñ, 中, ß,
٠, …) in addition to `[A-Za-z0-9_]`. The model therefore does **not** transcribe
the class as an ASCII enumeration; it consumes the per-code-point membership
test as the `@ContractOnly` axiom `is_word(c)` whose contract states only what
the real class actually guarantees:

* **below code point 128** the contract PINS the value: exactly the decimal
  digits, the two cased Latin runs, and the low line — and nothing else below
  128. (Verified exhaustively over cp 0..127 by G-AX: the real `\w` agrees on
  all 128.)
* **at and above 128** the contract says NOTHING. The real class is Unicode, so
  which further letters and digits it admits is the callee's business. The axiom
  is deliberately OPEN there.

The consequence is the point of the design: because the axiom is open above 128,
an implementation may not decide that region for itself. It must route every
code point through `is_word` and be correct for EVERY class the contract
permits — so the extraction rule is claimed over the whole `List[int]` input
domain, with **no domain restriction and no out-of-domain region**. There is no
`Requires` bounding `path[k]`, and none is needed: the postcondition is now true
of the real matcher on non-ASCII paths as well as ASCII ones.

An implementation that hardcodes either reading — "cp 233 is a word character"
or "no cp >= 128 is a word character" — is REJECTED by the verifier, because
neither is entailed by the axiom. G-AX checks both halves of the contract (the
pinned half exhaustively, the open half by exhibiting real members AND
non-members above 128, each of which the contract must permit) and then checks
the deep parse against the real matcher with `is_word` instantiated at the real
class, over a corpus that spans both sides of the boundary.

## 4. Deep-model reference provenance (A-reference — checked by G-AX)

**Real callee:** the compiled regex `language_code_prefix_re`
(`trans_real.py:46`, post-patch body `r'^/(\w+([@-]\w+){0,2})(/|$)'`). The
changed matcher is modeled **deeply** by `prefix_len_spec` (with `run_len`,
`nsep`, `no_adjacent_sep`, `well_formed_tag`, `spec_unfold`) over ONE consumed
`@ContractOnly` axiom — `is_word(c)`, the per-code-point word-class membership
test (§3.1), which is an **unchanged** callee the patch does not touch. Reading
the regex structurally:

* `^/` — the path must begin with `/` (code point 47). ⇒ `path[0] == 47`.
* `\w` — the word class, consumed as the axiom `is_word` (§3.1) rather than
  enumerated, so the structural reading below holds for the real Unicode class
  and not merely for its ASCII part.
* `(\w+([@-]\w+){0,2})` — group 1: a `\w+` run, then **0, 1 or 2** occurrences
  of (`[@-]` then `\w+`). Because `\w` and `[@-]` are disjoint classes and the
  quantifiers are greedy, group 1 is the maximal leading run of word/separator
  characters (`run_len`), it must be a well-formed `word+(sep word+)*`
  (non-empty, starts/ends with a word char, no two adjacent separators —
  `well_formed_tag`), and it may contain **at most 2 separators**
  (`nsep(tag) <= 2`).
* `(/|$)` — the character immediately after group 1 must be `/` (47) or a
  position where `$` matches. Python's `re` gives `$` (without `re.MULTILINE`)
  the semantics "end of string, OR immediately before a newline that is the
  LAST character of the string". ⇒ `run end == len(body)`, or `body[run] == 47`,
  or (`body[run] == 10` and `run == len(body) - 1`). E.g. the real matcher
  matches `"/en\n"` with group 1 `"en"`; the model returns 2 there too.

Group 1's length is therefore `run_len(body)` when accepted, else there is no
match (`-1`). The pre-patch body differs only in the repeat bound: `?` =
`{0,1}` ⇒ at most **1** separator (`nsep(tag) <= 1`). This single-bound change
is the entire behavioural delta, captured by the `maxsep` parameter (2 in the
spec, 1 in `model_prepatch.py`).

**Soundness check (G-AX):** `axiom_check.py` discharges TWO obligations.
(1) *Axiom soundness* — the real `\w` class must satisfy `is_word`'s contract:
the pinned half is checked EXHAUSTIVELY over cp 0..127, and the open half is
checked by exhibiting real code points at/above 128 on BOTH sides of the class
(letters/digits that are members, punctuation/symbols/spaces that are not),
each of which the contract must permit — plus a non-vacuity guard that both
sides are actually populated. (2) *Deep-model soundness* — with `is_word`
instantiated at the REAL class (`re.compile(r'\w').fullmatch`, not an
enumeration), it compiles BOTH the real pre-patch matcher
`r'^/(\w+([@-]\w+)?)(/|$)'` and the real post-patch matcher
`r'^/(\w+([@-]\w+){0,2})(/|$)'` and asserts on every probed path — ASCII AND
non-ASCII — that `prefix_len_spec(codepoints, 1)` equals the old matcher's
`len(group(1))` (or `-1`) and `prefix_len_spec(codepoints, 2)` equals the new
matcher's. The corpus includes non-ASCII letters, a non-ASCII digit, and
non-ASCII NON-word characters, an exhaustive sweep to length 4 over a
class-complete alphabet that straddles cp 128 (`a1_-@/.\n` + `é中×`), 150 000
fuzz paths over a wide pool, and a systematic per-code-point sweep of the class
boundary itself (~1 280 code points across six Unicode blocks, each placed in
seven locale-shaped templates). **Any** disagreement is a FAILURE: there is no
out-of-domain region to report. Measured: 175 156 paths, 0 failures. It imports
only the standard library (`re`, `random`, `sys`, `unicodedata`); nothing
repo-specific.

*Falsifiability (checked out-of-band):* reverting the transcribed `is_word` to
the ASCII enumeration fails with 21 636 divergences, and claiming the axiom
closes the region above 128 fails on the real `is_word(233) == True`.

## G-CONF (differential conformance — `conformance_check.py`)

**Shadow (provenance `direct`).** The `# impl-start`/`# impl-end` region of
`model.py` (`language_prefix_len`) copied **verbatim** into
`conformance_check.py`, with only the contract calls (`Requires`, `Ensures`,
`Invariant`, `Assert`) and the `# invariants-start|end` markers deleted — 60
lines, byte-identical to the stripped region (no restructuring, no renaming).
The `@Pure` helpers it calls (`is_sep`, `is_tagchar`) copy over the
same way, as does the whole `pure` region (`run_len`, `nsep`,
`no_adjacent_sep`, `well_formed_tag`, `spec_unfold`, `prefix_len_spec`) on top
of a small immutable `PSeq` shim (`len`/`[i]`/`take`/`drop`/`+`/`==`, plus
`ToSeq`). The one `@ContractOnly` callee, the word-class membership axiom
`is_word` (§3.1), is **not** transcribed as an enumeration — it is instantiated
at its REAL counterpart, `re.compile(r'\w').fullmatch`, i.e. the same Unicode
class the oracle matcher itself uses. So the axiom is EXERCISED here rather than
assumed, and a shadow that re-decided the class as ASCII would be caught (it is:
see Falsifiability below).

**Oracle — CALLED, not transliterated.** The real patched repo object of §1:
`django.utils.translation.trans_real.language_code_prefix_re`
(`trans_real.py:46`), consumed exactly as `trans_real.py:508/:511` does —
`mo = language_code_prefix_re.match(path)`, then `len(mo[1])`, or `-1` when
there is no match. The gate applies `patch.diff` to /testbed and sets
`PYTHONPATH`, so the imported object is the *patched* compiled matcher; no
pattern text is hard-coded in the script. An anti-vacuity guard runs first: the
imported matcher must accept `/en-latn-us/` with `group(1) == "en-latn-us"`
(which the pre-patch `?` bound cannot), and its `.pattern` must differ from the
pre-patch source recovered via `git show HEAD:…/trans_real.py`. A failed
patch-apply therefore FAILS the check instead of silently passing against
unpatched code. The unchanged downstream resolver (§2, refinement.md A7) is out
of scope by design — the extraction is the changed operation.

**Type bridge (§3, inverted).** Generation happens over the concrete `str`
path and is lowered per call to the model carrier by
`path = [ord(ch) for ch in s]` (`"/" ↔ 47`, `"-" ↔ 45`, `"@" ↔ 64`,
`"\n" ↔ 10`, `"é" ↔ 233`, `"中" ↔ 20013`); the specification side goes through
`ToSeq(path)` → `PSeq[int]`. The bridge is total over Unicode: a non-ASCII path
lowers to a `Requires`-satisfying `List[int]` like any other.
The result bridge is `re.match` truthiness + `len(group(1))` ↔ the returned
length / `-1`. Every `str` lowers to a `Requires`-satisfying input, since the
precondition is only `Acc(list_pred(path), 1/2)`. Three things are diffed per
input: (a) shadow length vs real `len(group(1))`/`-1`; (b) the §3 *content*
claim `group(1) == s[1:1+len]`; (c) the model's own postcondition executed —
impl region `== prefix_len_spec(ToSeq(path), 2)` — so a model-internal
divergence is caught too, not assumed.

**Inputs — 277 267 `Requires`-satisfying paths, `SEED = 150982026` (pinned as
a module constant `SEED` in `conformance_check.py`).**

| stratum | count | content |
|---|---|---|
| boundary | 111 | the F2P paths (`/pl/`, `/pl`, `/xyz/`, `/en-gb/`, `/en-latn-us/`, `/en-Latn-US/`, `/de-1996/`, `/de-ch-1901/`, `/de-simple-page-test/`, `/i-mingo/`, `/kl-tunumiit/`, `/nan-hani-tw/`); empty path, `/`, `//`, no-leading-slash; the separator-budget edge (2 separators accepted vs 3 rejected — the gold patch's discriminating shape); leading/trailing/adjacent separators; non-candidate terminators; the Python-`re` `$` trailing-final-newline edge (`/en\n`, `/en\n\n`, `/en\nx`, `/en\r\n`, `/\n`) |
| exhaustive | 177 156 | **every** string of length ≤ 5 over the structurally complete alphabet `a 1 _ - @ / . \n é 中 ×` (ASCII word / digit / underscore, both separators, the path separator, an ASCII non-candidate char, the newline, **a non-ASCII letter, a non-ASCII ideograph, and a non-ASCII NON-word symbol**). The impl's decision depends only on these character classes, so this **exhausts the shape space at small length** — and it now straddles code point 128 rather than stopping below it |
| fuzz | 100 000 | seeded (`SEED`), half langtag-shaped (1–5 sub-tags from a real-locale pool that now includes non-ASCII sub-tags × `-`/`@` × 22 tails, dense on the accept/budget boundary), half random over a wide pool spanning both sides of cp 128 (ASCII punctuation and `\n`/`\r`/`\t`, plus non-ASCII letters/digits and non-ASCII punctuation, symbols and spaces) |

**Branch ledger.** A 15-entry coverage ledger, computed from the path text
*independently of the shadow*, requires every impl branch to be taken at least
once: `empty-path`, `no-leading-slash`, `slash-only`, `no-candidate-run`, the
three ill-formed-tag reasons, `budget-exceeded`, all three accepting
terminations (`accept-end-of-path`, `accept-slash-terminator`,
`accept-final-newline`), `reject-terminator`, and `accept-{0,1,2}-sep` — the
last of which is precisely the behaviour the gold patch changed. An unexercised
branch **fails** the check, so a generator that routes around the patched
behaviour cannot report success.

**Domain.** The WHOLE `List[int]` input domain — there is no restriction and no
out-of-domain region (§3.1). The word class is consumed as an axiom that is open
above code point 128 rather than approximated by an ASCII enumeration, so a
non-ASCII path is an ordinary in-domain input and a disagreement on one is a
FAILURE like any other. What the check asserts instead is COVERAGE of that
region: it tracks which non-ASCII code points actually reached the matcher, split
by real word-class membership, and **fails** if either side is empty — otherwise
agreement over an accidentally-ASCII corpus would prove nothing above cp 128.
Measured: 21 distinct non-ASCII word and 11 distinct non-ASCII non-word code
points exercised; both counts appear in the JSON report.

**Falsifiability (verified out-of-band, /tmp scratch only).** The check fails,
with the input and both outputs printed, when: the oracle is swapped for the
pre-patch matcher (provenance guard); the shadow's separator budget is mutated
2→3 (`/de-simple-page-test/`); the final-newline termination is dropped
(`/en\n`); the adjacency check is dropped (`/a--b/`); `is_word` loses the
underscore (`/_x/`); **the shadow re-decides the word class as the ASCII
enumeration instead of consuming the axiom at its real counterpart (`/é/`:
shadow -1 vs oracle 1)**; the generator is crippled so the newline branch is
never reached (ledger); or **the corpus stops reaching non-ASCII code points, so
the word-class boundary above cp 128 is not exercised on both sides (coverage
assertion)**. Unmutated against the patched matcher: exit 0.

**Verdict:** exit 0 iff zero disagreements AND the word-class boundary was
covered on both sides; the last stdout line is a JSON report (`checked`,
`disagreements`, `seed`, per-stratum counts,
`nonascii_word_codepoints_exercised`, `nonascii_nonword_codepoints_exercised`,
`out_of_domain_region: null`,
`shadow: "direct (contract-stripped impl region of model.py)"`,
`oracle: "called: …language_code_prefix_re (patched)"`).
