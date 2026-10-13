# mapping.md — django__django-12143

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5573a54d409bb98b5c5acdb308310bed02d392c2`, states the type
abstraction, and gives the provenance of the deep-model reference (the changed
operation's real callee, validated by axiom_check.py / G-AX — there are NO
consumed axioms).

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `is_edited_pk_key(prefix, pkname, key)` | the per-key acceptance test inside `ModelAdmin._get_edited_object_pks` — `pk_pattern.match(key)` (`django/contrib/admin/options.py:1632-1635`, the `match` at line 1635 over the pattern built at line 1634) | the modeled changed behaviour: does one submitted POST key carry an edited row's primary key under the (fixed) pattern |
| `recognises(prefix, pkname, key)` *(deep model — A-reference)* | the compiled pattern `re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), self.model._meta.pk.name))` applied via `.match(key)` (`options.py:1634-1635`, post-fix) | pure spec: the literal structural decomposition the fixed pattern recognises; validated `recognises == real fixed match` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `prefix_eq(s, lit)` | the literal sub-pattern produced by `re.escape(prefix)` (the leading group label) and the trailing literal `self.model._meta.pk.name` | pure spec: literal code-point-for-code-point match of `lit` against the head of `s` |
| `all_digits(s)` / `is_digit(c)` | the `\d+` sub-pattern, over the realistic ASCII-digit domain (see §3) | pure spec: every code point a decimal digit |
| `match_literal(key, off, lit)` / `run_is_digits(key, lo, hi)` | proof scaffolding (verified helpers) that compute `prefix_eq` / `all_digits` over the list carrier; no repo counterpart | proof-only decomposition of the recognition loop |

The single changed expression (gold hunk):

```
- pk_pattern = re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name))
+ pk_pattern = re.compile(
+     r'{}-\d+-{}$'.format(re.escape(prefix), self.model._meta.pk.name)
+ )
```

The list comprehension `[value for key, value in request.POST.items() if
pk_pattern.match(key)]` (`options.py:1635`, UNCHANGED) is a filter that applies
the per-key test to every POST item; modelling the per-key decision
`is_edited_pk_key` is sufficient (see refinement.md R3).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`prefix`, the pk field name `self.model._meta.pk.name`, and each POST `key`) | `List[int]` of Unicode code points | `s[k]` ↔ `xs[k] == ord(s[k])`; `len(s)` ↔ `len(xs)`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the hyphen `'-'` | code point `45` | `ord('-') == 45` |
| a decimal digit `'0'..'9'` | code points `48..57` | `ord('0')==48 … ord('9')==57` |
| the regex anchor `'$'` (the metacharacter the pre-patch mishandles) | code point `36` | `ord('$') == 36` (used only in `model_prepatch.py`'s buggy skeleton) |
| `re.compile(...).match(key) is not None` | `recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))` | structural decomposition; see §3 for the equivalence and its domain |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference provenance (kind A-reference — checked by G-AX)

**Reference callee:** the CPython `re` module — `re.compile(pattern).match(key)`
with the FIXED pattern `r'{}-\d+-{}$'.format(re.escape(prefix), pkname)`. The
changed recognition is modelled **deeply** by the `@Pure` predicate
`recognises` (with `prefix_eq`, `all_digits`); there is **no consumed axiom**.
The deep model is validated equal to the real callee out-of-band by
axiom_check.py (G-AX).

`re.escape(prefix)` turns every code point of `prefix` into a literal matcher
(e.g. `re.escape('form$') == r'form\$'`, `re.escape('a.b+c*') == r'a\.b\+c\*'`),
so the leading region of `key` must equal `prefix` **character for character**.
The full fixed pattern is therefore the anchored decomposition

  `prefix` (literal) · `-` · `\d+` · `-` · `pkname` (literal) · `$`

and `.match` anchors at the start; the trailing `$` anchors the end. That is
exactly `recognises`.

**Domain scoping (the flag-style dependency G-AX must respect, analogous to
html.escape's `quote=True`).** The equivalence `recognises == fixed match` is
asserted over the keys Django actually constructs/receives for `list_editable`
formsets:

  * **ASCII digit run.** A bare `\d` in a unicode `str` pattern also accepts
    non-ASCII Unicode decimal digits (e.g. U+0660); the formset row index is
    rendered from a Python `int`, so a real key's digit run is always ASCII
    `0-9`. `all_digits` models the ASCII class. This wider `\d` acceptance is
    UNCHANGED by the fix.
  * **No trailing newline.** A `$` anchor in a unicode pattern also matches just
    before a single trailing `'\n'`, so the real callee would accept
    `'form-0-uuid\n'`; an HTTP form-field NAME cannot contain a raw newline.
    `recognises` requires the key to end exactly at `pkname`. This
    trailing-newline tolerance is UNCHANGED by the fix.

Both scopings are properties shared by the pre- and post-fix code and by every
real submitted key. The gold fix changes ONLY how `prefix` is interpreted
(literal vs. regex), which is precisely what the deep model pins; the two
scoped behaviours are orthogonal to the change.

**Soundness check (G-AX, `axiom_check.py`):** runs the REAL `re` callee on
21×3 boundary prefix/pkname combinations (each with literally-matching keys and
structural near-misses, prefixes covering every regex metacharacter) plus
60 000 randomized fuzz inputs, and asserts `recognises == fixed_match` over the
scoped domain (0 mismatch). It additionally asserts the change is real: 30 000+
inputs (including the exact F2P case `prefix='form$'`, `key='form$-0-uuid'`)
DISCRIMINATE the fixed match from the pre-fix raw-prefix match (which either
returns the wrong answer or raises `re.error`). stdlib-only (`re`); exit 0 iff
sound.
