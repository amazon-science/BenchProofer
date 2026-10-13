# mapping.md — django__django-15098

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2c7846d992ca512d36a73f518205015c88ed088c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one axiom.

Repo file under change: `django/utils/translation/trans_real.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolvePathLanguage (path : List Char) (strict : Bool)` | `get_language_from_path(path, strict=False)` — `django/utils/translation/trans_real.py:501` (body lines 508-515) | the modeled changed function: resolve a URL path to the language code to activate |
| `leadingLocaleTag` / `lstep` / `ldecode` / `LS` *(deep model — A-reference)* | the leading-prefix matcher `language_code_prefix_re` (`trans_real.py:46`) applied at `trans_real.py:508` (`.match(path)`), and the extracted `regex_match[1]` (`trans_real.py:510`) | pure spec: the leading locale tag a path carries; deep model of the (changed) prefix matcher, validated `== language_code_prefix_re.match(path)[1]` by conformance_check.py (G-CONF) |
| `listedLanguage` *(axiom — A-consumed)* | `get_supported_language_variant(lang_code, strict)` — `trans_real.py:464`, called at `trans_real.py:513`; its `LookupError` (caught at `trans_real.py:514`) is folded into `none` | unchanged downstream callee: resolve a candidate tag to a configured language, or fail |

The pre-patch behaviour the change replaces (refinement audit only, not in the
consumer spec view): the prefix matcher admitted only **one** `[@-]\w+` subtag
after the primary one (`^/(\w+([@-]\w+)?)(/|$)`), so a path whose tag carries
both a script and a region (two additional subtags, e.g. `/en-latn-us/`) failed
to match and resolved to none.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as a
spurious G-CONF / G-AX disagreement (the falsifiability the plan §4 trust
statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `path` (the `str` argument) and the extracted tag / returned code (`str`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]`; str concat ↔ `List` `++` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the ASCII/BMP domain this is total and exact |
| `strict` (the `bool` argument, default `False`) | Lean `Bool` | `True ↔ true`, `False ↔ false`; read-only — not `mut` (directive 5) |
| `None` return / a matched-language `str` return | `Option (List Char)` | `None ↔ none`; a `str` result `s ↔ some s.toList` |
| `regex_match[1]` (`str` or, on no match, the whole `match` is `None`) | `leadingLocaleTag 2 path : Option (List Char)` | the group-1 capture ↔ `some` of its `List Char`; `not regex_match` ↔ `none` |
| `re` word class `\w` (with `re.UNICODE` default) restricted to the langtag domain | `isWordChar c := c.isAlphanum ‖ c == '_'` | on the ASCII langtag domain (RFC 5646 tags + every configured `LANGUAGES` code + the F2P inputs are ASCII), `\w` = `[A-Za-z0-9_]` = `isWordChar`; see §3.1 domain note |
| the two subtag delimiters `[@-]` | `isSubtagSep c := c == '-' ‖ c == '@'` | the regex character class `[@-]` is exactly `{'-','@'}` (a 2-element set, NOT a range — `@`=0x40, `-`=0x2D, so `-` after `@` in `[@-]` is a literal, confirmed empirically) |

Lean `String`/`List Char` indexing is total and sound (no Nagini `List[int]`
workaround); the carrier is `List Char` because the matcher is per-code-point.

## 3. Provenance of the deep model and the axiom

### 3.1 `leadingLocaleTag` deep model ↔ `language_code_prefix_re` (A-reference)
**The changed operation.** The gold patch edits exactly one literal — the prefix
matcher's subtag quantifier:

```
- language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+)?)(/|$)')
+ language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+){0,2})(/|$)')
```

i.e. the number of additional `[@-]\w+` subtags admitted after the primary one
goes from **at most 1** (`?`) to **at most 2** (`{0,2}`). The regex recognises a
path beginning `/`, then a primary word run `\w+`, then up to *k* further
subtags (each a single `-`/`@` separator + a word run `\w+`), terminated by `/`
or end-of-string; group 1 is the locale tag (everything between the leading `/`
and the terminator).

`leadingLocaleTag maxSegs` models this matcher **deeply** as a left-to-right
finite automaton (`lstep` folded over the path, decoded by `ldecode`),
parameterised by `maxSegs` = the additional-subtag bound. `Solution.lean` uses
`leadingLocaleTag 2` (the patched bound); `Solution_prepatch.lean` uses
`leadingLocaleTag 1` (the buggy bound). There is **no consumed `prefixMatch`
axiom** — the changed operation is spelled out, so it is an **A-reference**, not
a consumed axiom (SPEC_GUIDE §3).

**Automaton ↔ regex correspondence.**
- `phase 0` = "expecting the opening `/`" (regex anchor `^/`); a non-`/` first
  char ⇒ no match (`status 2`).
- `phase 1` = "first `\w` of the primary subtag `\w+`"; a non-word char here ⇒
  no match (`\w+` needs ≥1 char).
- `phase 2` = "inside a word run": another `\w` extends it; a separator `[@-]`
  opens a new subtag **iff** fewer than `maxSegs` additional subtags have been
  taken (else no match — the path is longer than the grammar admits and no `/`
  terminator was seen); a `/` terminates and locks the tag in (`status 1`); any
  other char ⇒ no match.
- `phase 3` = "just past a separator, needing the subtag's first `\w`"; a
  non-word char ⇒ no match (a dangling/`--` separator). A word char advances to
  `phase 2` and increments `segs`.
- `phase 2` on a `\n`: tentatively closes the tag (`status 3`). Python's `$` in
  `(/|$)` (no `re.MULTILINE`) matches end-of-string **or** the position just
  before a single trailing `\n` that is the final character of the string. The
  automaton has no lookahead, so it records the tentative close as `status 3`
  and, on any subsequent character, demotes it to `status 2` (reject) — the `\n`
  was not the path's last char, so `$` would not have matched there. A second
  `\n` likewise rejects (`$` matches before only ONE trailing newline).
- `ldecode`: `status 1` (saw a `/` terminator) ⇒ the accumulated tag; `status 2`
  (rejected) ⇒ none; `status 3` (closed by a trailing `\n` that turned out to be
  the path's last char — the `$`-before-final-newline match) ⇒ the accumulated
  tag; otherwise the run reached end-of-path mid-`phase 2`
  (the `$` alternative of `(/|$)`) ⇒ the accumulated tag; `phase 1`/`phase 3` at
  end-of-path (no primary char, or a dangling separator) ⇒ none.

The accumulated `acc` is exactly the group-1 capture: the leading `/` is
consumed by `phase 0` and never appended, and the terminating `/`/`$` is not
part of group 1.

**Domain note (`\w`).** Django compiles the matcher with no `re.ASCII` flag, so
`\w` is Unicode-aware. The modeled `isWordChar` uses `Char.isAlphanum || _ == '_'`.
On the langtag domain this bundle reasons about — RFC 5646 tags, the configured
`LANGUAGES` codes, and every F2P input are ASCII — `\w` = `[A-Za-z0-9_]` =
`isWordChar`, exactly. This domain is **enforced by the method precondition**
`require ∀ c ∈ path, c.toNat < 128` (both twins, byte-identical spec regions):
the spec makes no claim about paths carrying non-ASCII code points, where the
library word class admits characters the modeled ASCII class does not.
conformance_check.py fuzzes over the ASCII word-class + the separators +
delimiters domain (mapping.md §4), where the two agree by construction;
Unicode word chars outside this domain are outside the precondition and out
of scope for the tested behaviour (no configured language code or graded path
contains them).

**Domain note (`$`-before-trailing-newline).** Python's `$` (without
`re.MULTILINE`) matches at end-of-string OR just before a single `\n` that is the
string's final character. The automaton models this faithfully via `status 3`
(see §3.1 correspondence above): an otherwise-valid tag immediately followed by
exactly one trailing `\n` (and nothing after) is recognised, returning the tag —
`leadingLocaleTag 2 "/en\n".toList = some "en".toList`, matching the real patched
`language_code_prefix_re.match("/en\n")[1] == "en"`. Any character after that
`\n`, or a second `\n`, rejects (`$` matches before only one terminal newline).
`\r` is NOT a `$`-terminator and is treated as a non-word reject character, as in
Python. conformance_check.py now includes `\n` in its fuzz alphabet and in its
boundary list, so this class is exercised: 100,040 inputs, 0 disagreements
against the real patched regex (G-CONF, §4).

**Soundness check (G-CONF):** conformance_check.py runs the **real patched**
`language_code_prefix_re` (read straight out of `trans_real` in the patched
container) and asserts `leadingLocaleTag 2 path == regex_match[1]` (or both
none) over the F2P/issue boundary inputs + 10⁵ fuzzed ASCII paths. The R/I leg
is the deep model; the A leg (`listedLanguage`) is held out (§3.2).

### 3.2 `listedLanguage` ↔ `get_supported_language_variant` (A-consumed)
**Callee:** `get_supported_language_variant(lang_code, strict)` (`trans_real.py:464`),
which `get_language_from_path` calls on the extracted tag and whose `LookupError`
it catches and turns into `None` (`trans_real.py:513-515`). This callee is
**unchanged** by the patch.

It is modeled as an **opaque** function `listedLanguage : List Char → Bool →
Option (List Char)` — the **weakest possible contract** (directive 7): the spec
asserts **no** property of its output, only that the resolved language is
*whatever this callee returns* for the extracted tag (its `LookupError` ↦
`none`). The proof never inspects the value; it only carries it through. Hence
there is nothing to over-claim: the only soundness obligation is that modeling
the callee as a deterministic *function* of `(lang_code, strict)` (with a fixed
`LANGUAGES`/`LANGUAGE_CODE` configuration) is faithful — i.e. the real callee is
a pure, deterministic partial function of those two arguments, and its only two
observable outcomes are "return a `str`" (↦ `some`) and "raise `LookupError`"
(↦ `none`), with no third effect the model elides.

**Soundness check (G-AX):** `axiom_check.py` constructs the real callee
in-container and asserts (a) **determinism/functionality**: repeated calls and
freshly-resolved calls with the same `(lang_code, strict)` under a fixed
configuration return equal results; (b) **total dichotomy**: every call either
returns a `str` or raises `LookupError` — never another exception, never `None`,
never a non-`str`; so `Option (List Char)` losslessly captures the outcome. It
exercises the F2P tags, the issue tags, generic-fallback tags, and randomized
ASCII fuzz, under the F2P `LANGUAGES` override and the default configuration,
with both `strict` values. Imports the repo's own `django.utils.translation`
module (in-container) + stdlib. Exit 0 iff every obligation holds.

**Flag dependency.** `strict` is a genuine argument of the callee (it gates the
country-variant fallback at `trans_real.py:492`); it is passed through opaquely
and G-AX fuzzes both `True` and `False`, so no flag is pinned to a single value.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15098`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `leadingLocaleTag 2` (the `lstep`/`ldecode` fold, the R/I-tagged
deep model) to Python and compares against the real patched
`language_code_prefix_re.match(path)[1]`. The A-tagged callee `listedLanguage`
(↔ `get_supported_language_variant`) is held out of G-CONF — it is covered by
G-AX (axiom_check.py, §3.2) — because the change is entirely in the prefix
matcher; isolating the R/I leg keeps the differential test pinned to the edited
operation.
