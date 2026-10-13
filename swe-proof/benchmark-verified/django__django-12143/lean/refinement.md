# refinement.md — django__django-12143

Maps every op in `implementation_rowKeySelection` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses callee
axiom · **A-reference** deep model validated == real callee (G-AX/G-CONF) ·
**I** identical op.

The modeled function is the per-row primary-key selection in
`ModelAdmin._get_edited_object_pks`:

```python
pk_pattern = re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkName))
return [value for key, value in request.POST.items() if pk_pattern.match(key)]
```

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `for kv in items do … acc := acc ++ [kv.2]` | `[value for key, value in request.POST.items() if pk_pattern.match(key)]` | R | list-comprehension ↔ accumulator `for` loop; `request.POST.items()` ordered `(key,value)` pairs ↔ `items : List (List Char × α)`; both preserve order + multiplicity |
| 2 | `if matchesRowKey mark pkName kv.1 then …` | `if pk_pattern.match(key)` | A-reference | the truthiness of `re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkName)).match(key)` is modeled DEEPLY by `matchesRowKey`; validated == real by G-CONF |
| 3 | `stripPrefix? mark key` (literal prefix consume) | `re.escape(prefix)` matched at the start (`.match` is start-anchored) | A-reference | **the fixed op**: escaped prefix ⇒ the marker is matched as a LITERAL string, i.e. `mark.isPrefixOf key`. Pre-patch: raw `prefix` spliced into the pattern (metachars active) |
| 4 | `'-' :: r2` then `r2.takeWhile isDecimalDigit` (non-empty) | the `-\d+` middle segment | A-reference | a hyphen followed by a non-empty run of **Unicode decimal digits** (category Nd): `isDecimalDigit` tests the 54 Nd code-point runs of the engine's Unicode data (mapping.md digit-class note) — matching `\d` on a py3 `str` pattern exactly |
| 5 | `'-' :: r3` then `stripPrefix? pkName r3` then `atEnd tail` | the trailing `-<pkName>$` | A-reference | hyphen, then the pk field name matched literally (`pkName` is a Python identifier ⇒ regex-literal), then the end anchor: `atEnd` accepts the true end of the key OR exactly one trailing `'\n'`, matching `$`'s tolerance (mapping.md end-anchor note) |
| 6 | `kv.2` (the returned value) | `value` | I / R | the POST value passes through untouched; opaque payload ↔ arbitrary `α` (frame) |

Every op is R, I, or A-reference. **No A-consumed rows** — the matcher is
modeled deeply (`matchesRowKey`, built from the pure helpers `stripPrefix?`,
`isDecimalDigit`/`digitRanges`, `atEnd`, and a `takeWhile`/`dropWhile` digit
split), so its constituent regex operations are spelled out, not axiomatized.
There is no `opaque`/`axiom` declaration; the regex engine + `re.escape` are
A-reference callees whose composite effect (`matchesRowKey`) is checked == the
real `re`-engine behavior by `conformance_check.py`.

Because the impl region contains R/I content (the selection loop) as well as the
deeply-modeled A-reference matcher, `conf_skip = false`: G-CONF mechanically
differential-tests `shadow_select` (the op-for-op transliteration of
`implementation_rowKeySelection`, matcher inlined) against the real escaped-prefix
`re` pattern over ≥1.2e5 fuzzed inputs, including non-Latin decimal digits,
digit-like non-digits, and trailing-newline keys.

## Prepatch (the real bug)

`Solution_prepatch.lean` is byte-identical outside the `impl`+`proof` regions
(same `problem_spec`, same `matchesRowKey`, same pure helpers). Its impl
substitutes `matchesRowKey` with `matchesRowKeyUnescaped`, which models the
pre-patch pattern construction (marker spliced in WITHOUT `re.escape`): on a
marker containing the end-of-input metacharacter `$`, the raw pattern's `$`
forces end-of-input mid-key, so no longer key can ever match — the matcher
wrongly rejects everything. This is exactly the data-loss regression in the
issue.

The discriminating input is the F2P case: marker `form$`, pk `uuid`, key
`form$-0-uuid`. The spec (literal matcher `matchesRowKey`) says this key
qualifies (its value is selected); the prepatch impl (`matchesRowKeyUnescaped`,
`$` in marker ⇒ reject) drops it. Thus
`problem_spec_rowKeySelection mark pkName items (implementation_rowKeySelection …)`
is FALSE for the prepatch impl on that input, so `correct_rowKeySelection` is
unprovable against it (G-DIFF), while the post-patch (literal) impl satisfies the
spec.
