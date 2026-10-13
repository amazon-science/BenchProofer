# mapping.md — django__django-11099

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d26b2424437dabeeca94d7900b37d2df4410da0c`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/contrib/auth/validators.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `accepts_ascii(value)` | the acceptance decision of `ASCIIUsernameValidator` — the `RegexValidator.__call__` of an instance whose `regex` is the class attribute at `django/contrib/auth/validators.py:9` and `flags = re.ASCII` (`validators.py:14`); `__call__` body `django/core/validators.py:52-60` | modeled changed function (ASCII username acceptance) |
| `accepts_unicode(value)` | the acceptance decision of `UnicodeUsernameValidator` — `regex` at `django/contrib/auth/validators.py:19`, `flags = 0` (`validators.py:24`); `__call__` body `django/core/validators.py:52-60` | modeled changed function (Unicode username acceptance) |
| `permitted_ascii(c)` *(axiom — A-consumed)* | the character class `[\w.@+-]` of the ASCII validator's pattern, evaluated by `re` under `re.ASCII` (`sre`/`re` stdlib; class text in `validators.py:9`) | unchanged community callee: single-code-point membership in the permitted class |
| `permitted_unicode(c)` *(axiom — A-consumed)* | the character class `[\w.@+-]` of the Unicode validator's pattern, evaluated by `re` under `flags=0` (class text in `validators.py:19`) | unchanged community callee: single-code-point membership in the permitted class |
| `all_ascii_permitted(s)` / `all_unicode_permitted(s)` *(deep model — A-reference)* | the WHOLE-string acceptance decision of `regex.search(str(value))` for the respective validator (`django/core/validators.py:57`) | pure spec: every code point admissible; the deep model of the changed end-anchored match, validated `==` the real FIXED regex by axiom_check.py (G-AX) |

The single repo edit (both validators, `validators.py:9` and `validators.py:19`):
the pattern's end anchor changes from `$` to `\Z`. The character class
`[\w.@+-]` and the `flags` are UNCHANGED — that is why class membership is the
(unchanged) axiomatized callee, while the end-anchoring is the deeply-modeled
changed behaviour.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `value` passed to the validator, after `str(value)`) | `List[int]` of Unicode code points | `s[k]` ↔ `value[k] == ord(s[k])`; `len(s)` ↔ `len(value)`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` slice/`len`/index |
| `regex.search(str(value))` truthy (a match exists) | `Result() == True` (value accepted) | `RegexValidator.__call__` raises `ValidationError` iff `not regex_matches` (`inverse_match` is `False` for both username validators); "accepted" ⇔ "no `ValidationError`" ⇔ "a match exists" |
| `re.search` with leading `^` anchor on these patterns | a whole-string predicate | `^` forces the match at position 0; `+` consumes ≥1 char; the end anchor (`$`/`\Z`) constrains the tail. For `^[\w.@+-]+\Z` (fixed) the match exists iff the string is non-empty and every code point is in the class — i.e. `len>=1 and all_permitted` (confirmed by G-AX, axiom_check.py). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `permitted_ascii` / `permitted_unicode` axioms (A-consumed)
**Callee:** single-code-point membership in the regex character class
`[\w.@+-]`, as evaluated by CPython's `re`/`sre` engine. `\w` is flag-sensitive:

* under `re.ASCII` (the ASCII validator's `flags`) `\w` is `[a-zA-Z0-9_]`;
* under `flags=0` (the Unicode validator's `flags`) `\w` is the full Unicode
  word-character set (letters, decimal digits, underscore, plus connector
  punctuation).

In BOTH regimes the class also contains the four literal symbols `. @ + -` and,
crucially, EXCLUDES the line feed U+000A and the space U+0020. The axioms pin
only the points the proof needs (the **weakest** sufficient contract): line feed
and space excluded; `'a'`, `'A'`/`'é'`, `'0'`, `'-'`, `'.'` included. They do
NOT claim anything about the unpinned code points, so they cannot be stronger
than the real class. Docs: https://docs.python.org/3/library/re.html (`\w`,
`re.ASCII`).

### 3.2 `all_ascii_permitted` / `all_unicode_permitted` deep model ↔ the fixed regex (A-reference)
The changed operation is the **end anchor** of the match. It is modeled
**deeply**: acceptance is `len(value) >= 1 and every code point admissible`,
spelled out by the front-recursive folds `all_*_permitted` and the verified
backward loop in `accepts_*`. There is **no axiom about the match itself**; the
deep model is instead validated **== the real FIXED regex** out-of-band by
axiom_check.py (G-AX):

* G-AX compiles the real `^[\w.@+-]+\Z` under each regime's flags and asserts
  `deep_accept(value) == real_fixed.search(value)` on 13 boundary values, 20000
  fuzz values, and a `0x2100` single-code-point sweep — 0 mismatches.
* G-AX also compiles the pre-patch `^[\w.@+-]+$` and asserts every disagreement
  between the deep model (== fixed) and the buggy regex is EXACTLY the
  lone-trailing-line-feed case — confirming the only behavioural delta is the
  one the issue reports.

**Flag dependency (record for G-AX):** `permitted_ascii` and the ASCII deep
model are sound under `re.ASCII`; `permitted_unicode` and the Unicode deep model
are sound under `flags=0`. axiom_check.py fuzzes both regimes with the correct
flags. The username validators never set `re.MULTILINE`, so `$`/`\Z` carry their
single-line meaning (the bug: `$` matches before a final `\n`).
