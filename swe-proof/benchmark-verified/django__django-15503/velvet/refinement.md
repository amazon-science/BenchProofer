# refinement.md — django__django-15503

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `compileRhsPath` `do` block, plus the deep models `compilePrefix` and
`memberSeg`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs are validated by **G-AX**; the narrative is audited
by **G-EQ**. Claim: any impl verifying against this frozen spec, refined per the
map below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The right-hand-side path site — `HasKeyLookup.as_sql` (`json.py:191-202`)

Gold hunk (the per-key body inside `for key in rhs:`):
```
- rhs_params.append(
-     "%s%s" % (
-         lhs_json_path,
-         compile_json_path(rhs_key_transforms, include_root=False),
-     )
- )
+ *rhs_key_transforms, final_key = rhs_key_transforms
+ rhs_json_path = compile_json_path(rhs_key_transforms, include_root=False)
+ rhs_json_path += self.compile_json_path_final_key(final_key)
+ rhs_params.append(lhs_json_path + rhs_json_path)
```
with `HasKeyLookup.compile_json_path_final_key(self, key) = ".%s" % json.dumps(key)`
(the base, has_key/has_keys/has_any_keys variant — the one the F2P tests exercise
on SQLite/MySQL/Oracle).

| # | Solution.lean impl op (`compileRhsPath`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `lhsPath : List Char` | `lhs_json_path` (str) | R | `str` ↔ `List Char` (mapping.md §2); read-only, not `mut` (directive 5). G-CONF prepends it identically on both legs. |
| A2 | param `keys : List (List Char)`, `require keys ≠ []` | `rhs_key_transforms` (`list[str]`), always non-empty (built from `[key]` or `preprocess_lhs`) | R | `list[str]` ↔ `List (List Char)` (mapping.md §2). The `*rhs, final = ks` unpack requires ≥1 element — captured by `require keys ≠ []`. |
| A3 | `let prefixKeys := keys.dropLast` | `*rhs_key_transforms, final_key = rhs_key_transforms` (the `*rhs` part) | I | `keys.dropLast` ↔ all-but-last; concrete list op, transliterated by G-CONF. |
| A4 | `let finalKey := keys.getLast!` | the `final_key` part of the unpack | I | `keys.getLast!` ↔ last element (total under `require keys ≠ []`); transliterated by G-CONF. |
| A5 | `let prefixPath := compilePrefix prefixKeys` | `compile_json_path(rhs_key_transforms, include_root=False)` | A-reference + I | `compilePrefix` is the **deep model** of the unchanged callee `compile_json_path` on the simple-key domain (mapping.md §3.1). The fold ops (`keySeg`, `arraySeg`, `++`) are **I** (transliterated by G-CONF); equality of the deep model to the real callee is the **A-reference** G-AX validates. |
| A6 | `let finalSeg := memberSeg finalKey` | `self.compile_json_path_final_key(final_key)` = `".%s" % json.dumps(final_key)` | A-reference + I | `memberSeg` is the **deep model** of `'.%s' % json.dumps` on the simple-key domain (mapping.md §3.2). The `'."' ++ k ++ '"'` assembly is **I**; the equality to real `json.dumps` quoting is the **A-reference** G-AX validates. **This is the discriminating clause** — the final key is located by name, not as an array index. |
| A7 | `return lhsPath ++ prefixPath ++ finalSeg` | `rhs_params.append(lhs_json_path + rhs_json_path)` where `rhs_json_path = prefix + final` | I | string concatenation `++` ↔ `+`; the appended element is `lhs + (prefix + final)` = `(lhs + prefix) + final` (associativity). Transliterated by G-CONF. |

Discriminating content of the change — a digit-only **final** key compiled as the
object member `."123"` (`memberSeg`) rather than the array index `[123]`
(`keySeg`/`arraySeg`) — lives in step A6. The pre-patch code compiled the
*entire* list (final key included) with `compile_json_path`, i.e. by the general
array-aware rule; `Solution_prepatch.lean` reproduces that
(`return lhsPath ++ compilePrefix keys`) and **fails** the postcondition
`out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!` exactly
when `keys.getLast!` is numeric (G-DIFF). That divergence is precisely the SQLite
/MySQL/Oracle `has_key='1111'` failure in the problem statement.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — how
the queried final key is compiled — is modeled **deeply** (`memberSeg` vs the
general `keySeg`, step A6, an A-reference + I), not hidden behind an axiom about
the function under change. There are **no consumed axioms** (the `axioms` region
is empty); the two A-reference deep models cover the **unchanged** callees
`compile_json_path` (interior keys) and `json.dumps` (final-key quoting), both
G-AX-validated.

## C. verify(Solution) ⇒ resolved

`compileRhsPath` verifies only if its output equals
`lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!` — i.e. the
interior keys compiled by the general rule and the final key located by name
(A5/A6). By R (`str ↔ List Char`, `list[str] ↔ List (List Char)`, read-only
`lhsPath`) the verified path equals the patched
`lhs_json_path + compile_json_path(rhs, False) + compile_json_path_final_key(final)`
on the tested simple keys; by G-AX the deep models equal the real
`compile_json_path` (A5) and the real `json.dumps` final-key rule (A6); by G-CONF
the R/I transliteration of the whole assembly agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and validated deep models —
and the gold patch resolves (G-RESOLVE). Trust points are exactly the two of
plan §1.1: deep-model soundness (G-AX) and refinement fidelity (this doc,
G-EQ + G-CONF).
