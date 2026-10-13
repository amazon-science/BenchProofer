# mapping.md — pydata__xarray-4966

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 37522e991a32ee3c0ad1a5ff8afe8e3eb1885550`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one modeled library callee.

Repo file under change: `xarray/coding/variables.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `decodeUnsigned (kind, bits, attr, values)` | `UnsignedIntegerCoder.decode(self, variable, name=None)` — `xarray/coding/variables.py:305` (changed hunk at lines 316–325 post-patch) | the modeled changed function |
| `IntKind` (`signedInt`/`unsignedInt`/`other`) | `data.dtype.kind` ∈ {`"i"`, `"u"`, anything else} — `variables.py:309` | element kind observed by the dispatch |
| `bits` (`Nat`) | `8 * data.dtype.itemsize` — element width in bits; the cast targets `np.dtype("i%s" % data.dtype.itemsize)` / `"u%s"` | element width |
| `attr` (`Option (List Char)`) | `pop_to(attrs, encoding, "_Unsigned")` — the `_Unsigned` attribute string, `none` when `"_Unsigned" not in attrs` (`variables.py:307`) | the signedness attribute |
| `values` (`List Int`) | the integer element values of `data` (the array `unpack_for_decoding` returns) | the stored element values |
| `applyCast` / `castSeq` *(deep model — A-reference)* | `partial(np.asarray, dtype=<target>)` applied elementwise via `lazy_elemwise_func` — `variables.py:313,322` post-patch | pure spec: per-element same-width integer reinterpret; deep model of the unchanged callee `np.asarray`, validated `applyCast == np.asarray(dtype=…)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `chooseMode` | the `if data.dtype.kind == "i": if unsigned == "true"` / `elif data.dtype.kind == "u": if unsigned == "false"` dispatch — `variables.py:309–325` post-patch | pure spec: transform + resulting kind selected from kind+attr |
| `decodeModel` / `Decoded` | the returned `Variable(dims, data, attrs, encoding)` content the F2P tests observe (`decoded.values`, `decoded.dtype`) | pure spec: result values + kind |

The pre-patch repo reality the change extends (refinement audit only, not in the
consumer spec view): the `decode` body had only the `data.dtype.kind == "i"`
branch plus an `else: warnings.warn(...)`; an unsigned (`kind == "u"`) array
fell through to the warning with no reinterpretation.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an integer array `data` (1-D element values) | `List Int` | `np.ndarray` of an integer dtype ↔ `values : List Int` elementwise; `len(data)` ↔ `values.length`; empty array ↔ `[]`. The element values are the **Python ints** `int(x)` for each array element (already reinterpreted into the carrier's signed/unsigned range by its current dtype). |
| `data.dtype.kind` | `IntKind` | `"i"` ↔ `signedInt`; `"u"` ↔ `unsignedInt`; any other kind char ↔ `other` |
| `data.dtype.itemsize` (bytes) | `bits : Nat` | `bits = 8 * itemsize` (itemsize ∈ {1,2,4,8} ↔ bits ∈ {8,16,32,64}); G-AX/G-CONF fuzz all four |
| `_Unsigned` attribute | `Option (List Char)` | absent ↔ `none`; present string `s` ↔ `some s.toList`; the only values the dispatch distinguishes are `"true"` and `"false"` |
| the result `Variable`'s observable content | `Decoded { values, kind }` | `decoded.values` (as Python ints) ↔ `out.values`; `decoded.dtype.kind` ↔ `out.kind` (the F2P test asserts both `decoded.dtype == signed_dtype` and `decoded.values == original_values`) |

The numeric reinterpretation is integer-exact, so `List Int` is the faithful
carrier (no float/precision modeling needed). `np.asarray(x, dtype=target)`
where source and target have the **same itemsize** is a pure two's-complement
reinterpretation of the element bit pattern:
* `i → u` (`toUnsigned bits`): a negative element `x` becomes `x + 2^bits`; a
  non-negative element is unchanged.
* `u → i` (`toSigned bits`): an element `x ≥ 2^(bits-1)` becomes `x - 2^bits`; an
  element below the midpoint is unchanged.
Both verified against real numpy over all four widths in §3 / axiom_check.py.

### Frame discipline (directive 5)
All four parameters (`kind`, `bits`, `attr`, `values`) are read-only inputs;
none is declared `mut`. The routine returns a fresh `Decoded`; no input carrier
is mutated, matching the real `decode`, which builds a new lazy array and
returns a new `Variable` without mutating `data` in place.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `applyCast`/`castSeq` deep model ↔ `np.asarray(dtype=…)` (A-reference)
**Callee:** `numpy.asarray(arr, dtype=signed_or_unsigned_same_width)`, applied
elementwise by `lazy_elemwise_func` with `transform = partial(np.asarray,
dtype=target)`. The changed elementwise reinterpretation is modeled **deeply**
by `applyCast`/`castSeq` in the `pure` region; there is **no consumed axiom**
about it.

Reinterpret semantics (same itemsize, two's complement; NumPy default
`casting='unsafe'` for `np.asarray` with explicit `dtype`):
```
u → i : signed_dtype.type / np.asarray(dtype="i%d")    # x in [0, 2^bits)
          → x        if x <  2^(bits-1)
          → x-2^bits if x >= 2^(bits-1)
i → u : np.asarray(dtype="u%d")                          # x in [-2^(bits-1), 2^(bits-1))
          → x        if x >= 0
          → x+2^bits if x <  0
```
This is the per-element substitution `applyCast (toSigned bits)` /
`applyCast (toUnsigned bits)` encodes. Because the reinterpretation is applied
independently to each element (`np.asarray` is elementwise, order-preserving),
`castSeq m` is faithfully the map of `applyCast m` over the element list.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`np.asarray(arr, dtype=target)` on boundary inputs (0, −1, the max unsigned, the
min/max signed, the midpoint `2^(bits-1)`, ±1 around it) and on randomized fuzz
across all four widths (itemsize 1/2/4/8), asserting `castSeq(model) == real
np.asarray` elementwise. It also exercises the full dispatch `chooseMode` against
a reference re-implementation of the patched `decode` branch logic. Imports only
`numpy`. Exit 0 iff sound.

### 3.2 No A-consumed axioms
The proof consumes **no** `axiom`. The dispatch (`chooseMode`) and the resulting
kind are spelled out in the `pure` region and are pure Lean facts the proof
discharges directly; the elementwise reinterpret is the A-reference deep model of
§3.1. The `_FillValue` re-cast lines of the gold hunk are **not modeled**: the
F2P tests construct variables with no `_FillValue` attribute, so that branch is
behaviorally inert on the tested inputs (recorded in refinement.md §B); modeling
it would add a numpy-scalar-cast liability with no F2P observation behind it.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`4966`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `chooseMode`/`applyCast`/`castSeq` (R/I-tagged ops) to Python and
diffs against the patched repo `UnsignedIntegerCoder.decode` behaviour over the
element values; there is no A-tagged callee left in the impl region's computed
result (the only A content, `np.asarray`, is itself the integer reinterpret the
shadow computes directly and G-AX validates separately).
