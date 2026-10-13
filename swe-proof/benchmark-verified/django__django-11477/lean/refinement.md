# refinement.md — django__django-11477

Maps every operation in `implementation_capture` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op). Every step is R, A, or I.

## Modeled function: `capture` (`RegexPattern.match`)

Post-patch repo code (`patch.diff`):
```python
def match(self, path):
    match = self.regex.search(path)
    if match:
        kwargs = {k: v for k, v in match.groupdict().items() if v is not None}  # changed
        args = () if kwargs else match.groups()
        return path[match.end():], args, kwargs
    return None
```

Lean impl (`implementation_capture`):
```lean
def implementation_capture {V : Type}
    (path : List Char) (outcome : Option (ScanOutcome V)) :
    Option (List Char × List (Option V) × List (Nat × Option V)) := Id.run do
  let some sc := outcome | return none
  let mut named : List (Nat × Option V) := []
  for entry in sc.namedCaptures do
    if carriesValue entry then
      named := named ++ [entry]
  let positional := if named.isEmpty then sc.positionalCaptures else []
  return some (path.drop sc.consumed, positional, named)
```
where `carriesValue (name, v) = v.isSome`.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let some sc := outcome \| return none` | `match = self.regex.search(path)` then `if match: … return …` else `return None` | **R** | the regex-search result ↔ `Option (ScanOutcome V)`; `none` ↔ `match is None` (falls to `return None`); `some sc` ↔ a successful match carrying `end()`/`groupdict()`/`groups()`. Unchanged by the patch. |
| 2 | `for entry in sc.namedCaptures do if carriesValue entry then named := named ++ [entry]` | `kwargs = {k: v for k, v in match.groupdict().items() if v is not None}` | **I** (deep model of the changed op) | **the fixed operation.** The comprehension keeps exactly the named groups whose value is not `None`; `carriesValue entry = entry.2.isSome` reproduces `v is not None`, and the accumulator `for` builds the kept association list in declaration order — exactly the post-fix `groupdict()` filtering. |
| 3 | `let positional := if named.isEmpty then sc.positionalCaptures else []` | `args = () if kwargs else match.groups()` | **I** | the positional fallback: report `match.groups()` iff `kwargs` is empty, else the empty tuple. `named.isEmpty` ↔ `not kwargs` (an empty dict is falsy). This consumes the FILTERED `named` (post-fix `kwargs`), so when every named group was absent (`None`-valued) and thus dropped, `named` is empty and positional captures are now reported — a behavior the prepatch (unfiltered `kwargs`) suppresses. Unchanged code, but its observable output shifts because its input (`kwargs`) is now filtered. |
| 4 | `return some (path.drop sc.consumed, positional, named)` | `return path[match.end():], args, kwargs` | **R** | the 3-tuple ↔ `(leftover, positional, named)`; `path[match.end():]` ↔ `path.drop sc.consumed`; `args`/`kwargs` ↔ `positional`/`named`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `RegexPattern.match` reshaping behavior.

## Soundness check (verify ⟹ correct)

- `problem_spec_capture path outcome result` pins the result EXACTLY by
  case-splitting on `outcome`:
  * `none` ⇒ `result = none` (no stray success invented);
  * `some sc` ⇒ `result = some (path.drop sc.consumed,
    if named.isEmpty then sc.positionalCaptures else [], named)` where
    `named = sc.namedCaptures.filter carriesValue`.
  Every output component is grounded in the input (directive 5/8): the leftover
  path is `path.drop consumed`; the named mapping is the input named captures
  filtered to those carrying a value, in input order; the positional list is
  pinned to either the input positional captures or `[]` per the `named.isEmpty`
  decision. Nothing is left unconstrained; no ungrounded oracle.
- The prepatch impl reproduces the PRE-FIX behavior: `kwargs = match.groupdict()`
  unfiltered (`named := named ++ [entry]` for EVERY entry, including
  `none`-valued ones). It violates the spec on the discriminating clause
  `outcome = some sc` where `sc.namedCaptures` contains an absent named capture
  (`(name, none)`): the spec drops it (and, if that empties `named`, reports the
  positional captures), but the prepatch keeps it (and forces `positional = []`).
  Its carried gold proof cannot close (G-DIFF/G-PANEL); the failing case is a
  `some` outcome with at least one `(_, none)` named capture.
- This discriminating case is precisely what the FAIL_TO_PASS tests exercise:
  `test_re_path_with_optional_parameter` resolves `/regex_optional/1/` against
  `^regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?` and asserts
  `match.kwargs == {'arg1': '1'}` (NOT `{'arg1':'1','arg2':None}`);
  `test_translate_url_utility` round-trips a URL with an absent optional group and
  asserts the rebuilt URL has no literal `None`. With every named group present
  pre- and post-fix agree; the asymmetry only appears for absent optional groups.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  `RegexPattern.match` over hand-picked edge cases (all-present, some-absent,
  all-absent-named-with-positional, no-match) plus ≥1e5 fuzzed scan outcomes.
