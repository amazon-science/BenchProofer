# mapping.md — django__django-15503

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 859a87d873ce7152af73ab851653b4e1c3ffea4c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each A-reference deep model.

Repo file under change: `django/db/models/fields/json.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `compileRhsPath (lhsPath) (keys)` | the per-key right-hand-side path construction inside `HasKeyLookup.as_sql` — `django/db/models/fields/json.py:191-202` (the `for key in rhs:` body that appends to `rhs_params`) | the modeled changed behavior: build the path string locating a queried key |
| `compilePrefix` / `keySeg` / `arraySeg` / `canonicalDigits` / `isNumericKey` *(deep model — A-reference)* | `compile_json_path(key_transforms, include_root=False)` — `django/db/models/fields/json.py:129` | UNCHANGED callee: compiles a sequence of interior keys to a rootless path; numeric keys become array segments `[n]`, others object members `."k"` |
| `memberSeg (k)` *(deep model — A-reference)* | `".%s" % json.dumps(key_transform)` — body of the new `HasKeyLookup.compile_json_path_final_key` (`django/db/models/fields/json.py:175-177` post-patch) | UNCHANGED primitive (`json.dumps` + string format): locate the queried (final) key by name, regardless of spelling |
| `isSimpleKey` / `isSimpleChar` | (spec-domain predicate, no repo symbol) | the `require` domain: keys are non-empty ASCII-alphanumeric runs — the bijection's validity bound (mapping.md §2) |

The pre-patch repo symbol the change *displaces* (refinement audit only, not in
the consumer spec view): the unconditional
`"%s%s" % (lhs_json_path, compile_json_path(rhs_key_transforms, include_root=False))`
(`json.py:196-202` pre-patch), which compiled the *whole* key list — including
the final key — by the general (array-aware) rule.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a single JSON key `key_transform` (a `str`) | `List Char` | `k` (Python str) ↔ `k.toList`-shaped `List Char`; `len(k)` ↔ `k.length`; concat ↔ `++`; empty ↔ `[]` |
| the key list `rhs_key_transforms` (a `list[str]`) | `List (List Char)` | element-wise the row above; `*rhs, final = ks` ↔ `(ks.dropLast, ks.getLast!)` |
| the compiled path string (a `str`) | `List Char` | per-character as above; the function returns one path string |
| `lhs_json_path` (already-compiled enclosing-document path) | `List Char` (the `lhsPath` parameter) | opaque prefix; identity on `List Char`; never mutated (read-only, directive 5) |
| a single character | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the ASCII range this is total and exact |

**Domain bound (`require keys.all isSimpleKey`).** The F2P / repo lookups carry
keys that are non-empty ASCII-alphanumeric runs (`"123"`, `"nested"`, `"456"`,
`"789"`, `"777"`, `"ipsum"`, `"array"`, `"000"`, `"lorem"`, `"999"`). On exactly
this domain the two deep models are faithful to the real callees (verified by
G-AX, §3): (a) `int(k)` succeeds iff `k` is all-digit, so `compile_json_path`'s
`try: int(...)` branch is `isNumericKey`; (b) `json.dumps(k)` of an ASCII
alphanumeric string is `'"' + k + '"'` with no escaping, so `memberSeg`'s quoting
is exact. Keys with non-alphanumeric characters (escapes, unicode, embedded
quotes) are outside the modeled domain and not claimed.

Lean `String`/`List Char` indexing is total and sound (no Nagini `List[int]`
workaround needed); the carrier is `List Char` because the operation is
per-character path assembly.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

`Solution.lean` consumes NO axioms (the `axioms` region is empty). Both kind-A
liabilities are **A-reference deep models**: the changed behavior is spelled out
in the `pure` region and validated `== real callee` by G-AX, not hidden behind a
consumed axiom about the function under change.

### 3.1 `compilePrefix` deep model ↔ `compile_json_path` (A-reference)
**Callee:** `django.db.models.fields.json.compile_json_path(ks, include_root=False)`
(`json.py:129`) — UNCHANGED by the gold patch. For each interior key it tries
`int(key_transform)`; on success it appends `"[%s]" % num` (so a digit run is
integer-normalised — leading zeros dropped, `compile_json_path(["007"]) == "[7]"`,
`["000"] == "[0]"`), on `ValueError` it appends `"." + json.dumps(key)`. On the
simple-key domain this is exactly `keySeg`: numeric → `arraySeg`
(`'[' :: canonicalDigits k ++ ']'`), else `memberSeg`. `compilePrefix` is the
front-recursive concatenation over the interior keys (`keys.dropLast`).

### 3.2 `memberSeg` deep model ↔ `'.%s' % json.dumps(key)` (A-reference)
**Callee:** the body of the patch's new `compile_json_path_final_key` on the base
`HasKeyLookup` — `".%s" % json.dumps(key_transform)`. `json.dumps` of an ASCII
alphanumeric string wraps it in double quotes with no escaping, so the result is
`'."' + k + '"'`, which is `memberSeg k`. This is the heart of the fix: the
final (queried) key is located **by name** — as an object member — even when its
spelling is all digits, instead of being mis-compiled to an array index.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `compile_json_path`
and the REAL `json.dumps` on boundary keys (numeric, leading-zero `007`/`000`,
large `10^21`, alphabetic, mixed `1a`/`a1`) and key-lists (the F2P shapes), plus
20 000 randomized fuzz rounds over the simple-key alphabet, asserting (a)
`compilePrefix == compile_json_path` (A-reference 1) and (b)
`memberSeg == '.%s' % json.dumps` (A-reference 2). Imports only stdlib `json`
and the in-tree `compile_json_path`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15503`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `compileRhsPath`'s impl (`compilePrefix` over `keys.dropLast`,
`memberSeg` of `keys.getLast!`, `++` with `lhsPath`) to Python; the oracle is the
patched right-hand-side path built from the REAL patched callees
`compile_json_path` + `HasKeyLookup.compile_json_path_final_key`. Both are run
in-container with the gold patch applied; they must agree on every
Requires-satisfying input.
