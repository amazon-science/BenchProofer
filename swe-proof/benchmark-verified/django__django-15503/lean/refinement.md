# refinement.md — django__django-15503

Maps every op in `implementation_keyLookupPath` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses callee axiom ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let intermediate := keys.dropLast` | `*rhs_key_transforms, final_key = rhs_key_transforms` (the `*rhs_key_transforms` binding) | R | Python starred-unpack of all-but-last ↔ `List.dropLast`; `list[str]` ↔ `List String` |
| 2 | `let finalKey := keys.getLastD ""` | `*rhs_key_transforms, final_key = rhs_key_transforms` (the `final_key` binding) | R | last element; total `getLastD` with default (precondition `keys ≠ []` matches Python's guaranteed ≥1 element, so the default is never taken) |
| 3 | `let mut rhsJsonPath := pathOfKeys intermediate` | `rhs_json_path = compile_json_path(rhs_key_transforms, include_root=False)` | R | `compile_json_path` over the intermediate keys ↔ `pathOfKeys` = `String.join ∘ map renderSegment`; each `renderSegment` = one loop step (`[num]` for `int(k)` success, `"." + json.dumps(k)` otherwise). `numericKey` models Python `int(k)` faithfully: trims ASCII whitespace, accepts an optional leading `+`/`-`, and a digit run with single underscore separators (no leading/trailing/doubled underscore) — so `"-1"→[-1]`, `"+2"→[2]`, `" 3 "→[3]`, `"1_0"→[10]`, while `"1_"`, `"_1"`, `"1__0"`, `"12a"` stay named. G-CONF fuzzes exactly these edges against the real callee. |
| 4 | `rhsJsonPath := rhsJsonPath ++ finalSegment finalKey` | `rhs_json_path += self.compile_json_path_final_key(final_key)` where `compile_json_path_final_key` returns `".%s" % json.dumps(key)` | R | **the fixed line**: the final key is appended as a NAMED member (`"." ++ encodeKey k`), NOT via `compile_json_path` (which would emit `[num]` for a digit-run key) |
| 5 | `return lhsJsonPath ++ rhsJsonPath` | `rhs_params.append(lhs_json_path + rhs_json_path)` | I | prefix concatenation; one element of `rhs_params` |

Every op is R or I. `encodeKey` (↔ `json.dumps`) is an **opaque signature** the
impl carries, applied identically on named-member steps in ops #3 and #4 and on
BOTH sides of the fix — it is not A-consumed (the proof uses no property of it)
and not A-reference (its output is not observed by the spec; the fix is about
WHICH renderer is applied, not the escaping). So `axioms` region holds only the
`opaque encodeKey` decl; no `_prop` axiom, no G-AX obligation.

Because the impl region is entirely R/I (no A-tagged content), `conf_skip =
false`: G-CONF mechanically differential-tests this impl against the patched
RHS-path assembly, with `encodeKey` bound to `json.dumps` on both legs (it
cancels), isolating the positional-vs-named final-key routing.

## Prepatch (the real bug)

`Solution_prepatch.lean` replaces ops #1–#4 with the single pre-patch line
`let rhsJsonPath := pathOfKeys keys` — i.e. the ENTIRE key list, including the
final key, is routed through `compile_json_path` (`pathOfKeys`). This is exactly
the base_commit code:
```python
rhs_params.append("%s%s" % (lhs_json_path,
    compile_json_path(rhs_key_transforms, include_root=False)))
```
For a final key that is a digit run (e.g. `"1111"`, `"123"`, `"000"`),
`renderSegment` emits `[num]` (an array-index step) rather than the required
`"." ++ encodeKey k` (a named-member step). The discriminating clause is the
whole `problem_spec` equality: the spec requires the result to end in
`finalSegment (keys.getLastD "")` = `"." ++ encodeKey finalKey`, but the
prepatch produces `renderSegment finalKey` = `"[" ++ toString n ++ "]"` whenever
the final key is numeric — a different string (starts with `[`, not `.`). Hence
`correct_keyLookupPath` is unprovable for the prepatch impl (G-DIFF), matching
the issue: `has_key='1111'` found 0 rows because the query addressed array index
1111 instead of the object member named "1111".
