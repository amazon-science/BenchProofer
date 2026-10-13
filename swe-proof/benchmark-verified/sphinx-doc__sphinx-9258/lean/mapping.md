# mapping.md — sphinx-doc__sphinx-9258

## Symbol binding (@ base_commit `06107f838c28ab6ca6bfc2cc208e15997fcb2146`)

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_splitTypeSpec` / `problem_spec_splitTypeSpec` / `correct_splitTypeSpec` | `PyXrefMixin.make_xrefs` (the split + per-piece classify loop) | `sphinx/domains/python.py:304-321` |
| `reSplit true` / `reSplit false` | `re.split(delims, target)` with `delims` = the NEW / OLD pattern | `sphinx/domains/python.py:307-309` |
| `delimLen true` / `delimLen false` | `delims_re.match(sub_target)` (truthiness) with NEW / OLD pattern | `sphinx/domains/python.py:308,318` |
| `Seg.sep piece` | `contnode or innernode(sub_target, sub_target)` (a separator node kept verbatim) | `sphinx/domains/python.py:319` |
| `Seg.name piece` | `self.make_xref(rolename, domain, sub_target, …)` (a cross-referenced type name) | `sphinx/domains/python.py:320-321` |

The changed line is exactly `delims` (307): the regex gains a `\s*\|\s*`
alternative between `\s+or\s+` and `\.\.\.`.

## The regex alternation being modeled

NEW pattern (post-patch):
`(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)`
OLD pattern (pre-patch): same minus the `|\s*\|\s*` alternative.

`re.split` with a **capturing** group returns interleaved text/separator pieces
(the captured separators sit at odd indices). `filter(None, …)` drops empty
pieces. Each survivor is then classified with `delims_re.match(sub_target)`
(match anchored at the start): truthy ⇒ separator piece, falsy ⇒ type name. Two
facts verified by fuzz (see `conformance_check.py`):
1. `delims_re.match(piece)` is truthy **iff** the piece was captured as a
   separator by `re.split` — so `classifySeg` can decide the tag by re-matching
   the separator alternation as a prefix.
2. The Lean `delimLen`/`reSplit`/`tokenize` model reproduces
   `re.split` + `filter` + classify byte-for-byte over ≥1e5 fuzzed inputs
   (both NEW and OLD pattern), so the R/I legs carry no unmodeled behaviour.

### Lean ↔ Python type bijection

| Lean | Python | bijection |
|---|---|---|
| `List Char` | `str` (the `target`) | per-code-point; `str ↔ list of chars` |
| `List Seg` | `List[Node]` (the `results`) | one segment per node, in order; `Seg.sep t` ↔ a verbatim separator/`contnode` node carrying text `t`, `Seg.name t` ↔ a `make_xref(...)` node cross-referencing `t` |
| `reSplit` piece list (incl. empties) | `re.split(delims, target)` list | equal element-by-element as `str`/`List Char` |
| `delimLen true piece |>.isSome` | `bool(delims_re.match(piece))` | equal Bool |
| whitespace: `isSp c` | Python `\s` (Unicode, the `re` default for `str` patterns) | exact: `isSp` enumerates precisely the code points `re.compile(r'\s')` matches — U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000 (verified by enumerating all of Unicode) |

The downstream node construction (`contnode or innernode(...)` vs
`self.make_xref(...)`) is UNCHANGED by the patch and is a structural
one-to-one map from the classification decision; it is represented directly by
the `Seg` carrier (`sep` vs `name`) rather than modeled as separate node objects.
No unchanged callee is *consumed*: there is no `opaque`/`axiom` in the bundle.

## Callee provenance / flag dependency

- `re.split`, `re.compile`, `delims_re.match` are Python stdlib; their behaviour
  under the specific `delims` alternation is modeled deeply (not axiomatized),
  because the alternation itself is what the patch changes (§3: never axiomatize
  the changed op).
- `self.make_xref` / `innernode` / `contnode` are unchanged and their internal
  node structure is irrelevant to the fix (the fix only changes WHICH substrings
  reach `make_xref` vs are kept as separators). Represented by the `Seg` carrier;
  not axiomatized, not fuzzed.
- No flag-dependent callee.

## G-CONF fuzz seed

`conf_seed = 9258` (pinned). Alphabet for fuzzed `target`:
`"abc |[](),.or\t\n\f\v\xa0\x85 　\x1c"` (covers type-name chars, all
separator triggers, and whitespace including the non-ASCII / non-obvious code
points Python `\s` matches — `\f`, `\v`, NBSP, NEL, EM SPACE, IDEOGRAPHIC
SPACE, FS control), lengths 0–16, ≥1e5 samples. The check compares the Lean-model
shadow (re-implemented in Python identically to the Lean defs) against the real
post-patch `re.split`+classify over the NEW pattern, AND cross-checks that the
Lean-model shadow equals the direct `re.split` for BOTH patterns.
