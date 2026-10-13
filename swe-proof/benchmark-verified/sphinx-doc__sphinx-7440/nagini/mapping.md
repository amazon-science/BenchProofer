# mapping.md — sphinx-doc__sphinx-7440

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9bb204dcabe6ba0fc422bf4a45ad0c79c680d90b`, states the type
abstraction, and gives the provenance of the single kind-A reference (the deep
model `casefold` validated against the real lower-casing).

Repo file under change: `sphinx/domains/std.py` (with a consistency hunk in
`sphinx/domains/std.py` line 568 referencing `sphinx/roles.py:XRefRole`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `register_term_name(termtext)` | the term-registration argument of `make_glossary_term` — `std.note_object('term', termtext, node_id, ...)` at `sphinx/domains/std.py:308` (post-patch); pre-patch `note_object('term', termtext.lower(), ...)` | the modeled changed behaviour: the cross-reference key registered for a glossary term |
| `fold_cp(c)` | the per-character effect of CPython `str.lower()` on one ASCII code point (the pre-patch `.lower()` call) | pure spec: ASCII case fold of one code point |
| `casefold(s)` *(deep model — A-reference)* | CPython `str.lower()` on the (ASCII) term text — the operation the pre-patch applied and the fix removed | pure spec: the whole-string ASCII case fold; the CONTRAST operation the registration must NOT perform; validated `casefold == ascii str.lower` by axiom_check.py (G-AX), NOT consumed as an axiom |

`make_glossary_term` computes `termtext = term.astext()` (the rendered text of
the term node, `sphinx/domains/std.py:284`) and passes a key derived from it to
`StandardDomain.note_object` (`sphinx/domains/std.py:649`), which stores
`self.objects[objtype, name] = (docname, labelid)` and later re-emits `name`
verbatim from `get_objects` (`sphinx/domains/std.py:974-975`,
`yield (name, name, type, ...)`). The F2P test reads that key back through
`get_objects()` and asserts `("TERM2", "TERM2", "term", "index", "term-TERM2",
-1)` — i.e. the stored `name` is the term text with its original case.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the term text `termtext`, and the registered key) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `termtext.lower()` (pre-patch, `std.py:308`) | `casefold(ToSeq(termtext))` | CPython `str.lower()` on the ASCII term-text domain is the per-character ASCII fold A-Z→a-z (`fold_cp`); see §3 |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`. The
modeled function returns the registered key (a `List[int]`); the post-patch
behaviour is the identity copy of `termtext`, the pre-patch behaviour is
`casefold(termtext)`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `casefold` deep model ↔ `str.lower()` (A-reference)
**Callee:** CPython `str.lower()` (the pre-patch `termtext.lower()` call). The
operation the change concerns — folding the term text to lower case — is
modelled **deeply** by the `@Pure` fold `casefold` (with `fold_cp`) in the
`pure` region. There is **no consumed axiom**; `casefold` is validated equal to
the real callee out-of-band by axiom_check.py (G-AX).

On the **ASCII domain** — which is the domain glossary terms in this benchmark
inhabit (`term1`, `TERM2`, `mysql`, `MySQL`, identifiers, option names) — Python's
`str.lower()` is exactly the per-character map

  upper-case Latin 'A'..'Z' (code points 65..90) → its lower-case form (+32),
  every other code point → itself,

which is what `fold_cp` / `casefold` encode. axiom_check.py asserts this two
ways: (1) exhaustively over all 128 ASCII code points `fold_cp(c) ==
ord(chr(c).lower())`; (2) `casefold(s) == [ord(c) for c in s.lower()]` over
boundary + 20 000 fuzz ASCII strings. (Full-Unicode `str.lower()` performs
additional case mappings; the deep model is deliberately the **ASCII** fold and
is validated only on the ASCII domain the change exercises — recorded here so
G-AX fuzzes the right domain.) Docs:
https://docs.python.org/3/library/stdtypes.html#str.lower.

The post-patch registration applies **no** fold — the key is the term text
verbatim (model.py `register_term_name` postcondition `ToSeq(Result()) ==
ToSeq(termtext)`). `casefold` is present only to (a) drive the pre-patch
skeleton (`model_prepatch.py`) and (b) serve as the A-reference whose
divergence from the identity on any upper-case input is the discriminating
witness of the fix (axiom_check.py check (3)).

### 3.2 The second gold hunk — `XRefRole(lowercase=True)` → `XRefRole()`
The gold patch also drops `lowercase=True` from the `'term'` role registration
(`sphinx/domains/std.py:568`, the `roles` dict; `XRefRole` is defined at
`sphinx/roles.py:52`, and `lowercase` lower-cases the cross-reference *lookup
target* at `sphinx/roles.py:146-147`). This is the read-side counterpart of the
write-side fix: once term keys are stored with original case, a `:term:`
reference must look them up with original case too. The F2P test `test_glossary`
exercises only the **write** side (registration + index + `get_objects`); it
contains no `:term:` cross-reference, so the tested discriminator is entirely
hunk 1 (the `termtext.lower()` → `termtext` change), which the model captures.
Hunk 2 is a consistency change with no independently-tested observable in the
F2P set and is documented here (refinement.md tags it R/consistency, no separate
`model_prepatch_<k>`). No callee is axiomatized for it.

**Soundness check (G-AX):** `axiom_check.py` runs the real `str.lower()` over the
full ASCII domain and over boundary + 20 000 fuzz ASCII term-text strings,
asserting `casefold` equals it and that the case-preserving identity differs
from `casefold` exactly on upper-case input. It imports only the standard
library. Exit 0 iff sound.
