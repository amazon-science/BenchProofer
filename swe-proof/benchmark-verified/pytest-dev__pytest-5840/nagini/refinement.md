# refinement.md — pytest-dev__pytest-5840

The operation-by-operation correspondence between `model.py`'s implementation
(the `conftest_dedup_key` impl region and the callee contracts it uses) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (a callee — **A-consumed** where the proof uses an axiom's `Ensures`,
**A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The modeled change — the conftest cache key in `_importconftest`

Gold hunk (`src/_pytest/config/__init__.py`):
```
-        # Use realpath to avoid loading the same conftest twice
+        # Use a resolved Path object as key to avoid loading the same conftest twice
         # with build systems that create build directories containing
         # symlinks to actual files.
-        conftestpath = unique_path(conftestpath)
+        # Using Path().resolve() is better than py.path.realpath because
+        # it resolves to the correct path/drive in case-insensitive file systems (#5792)
+        key = Path(str(conftestpath)).resolve()
         try:
-            return self._conftestpath2mod[conftestpath]
+            return self._conftestpath2mod[key]
         ...
-            self._conftestpath2mod[conftestpath] = mod
+            self._conftestpath2mod[key] = mod
```
(The gold patch also deletes the now-unused helper and its `normcase` import in
`src/_pytest/pathlib.py`, and drops the helper's calls in `_getconftestmodules`
/ `_set_initial_conftests`, replacing the former's `directory.parts()` with
`directory.realpath().parts()`. These are the same single change — stop building
the cache key under the unrecognised key convention — applied at the
helper-definition and the two other call sites; the modeled function
`conftest_dedup_key` captures the load-bearing key computation the FAIL_TO_PASS
tests observe via `_conftestpath2mod` membership.)

### The real discriminator the FAIL_TO_PASS tests observe

The graded F2P tests (`test_setinitial_conftest_subdirs[test]` / `[tests]`)
store a conftest under a constructor-produced key, then assert membership with
an INDEPENDENTLY-recomputed key:
```python
key = Path(str(subconftest)).resolve()
assert key in conftest._conftestpath2mod   # post-patch test
```
On the POSIX evaluation harness the subdir names (`test`, `tests`) are
all-lowercase and `os.path.normcase` is the identity, so the two key conventions
produce the **identical location string**. The discriminator is therefore NOT
letter casing; it is whether the cache's membership test RECOGNISES the stored
key as equal to the recomputed key:

  * the gold convention stores `Path(str(conftestpath)).resolve()` (a
    `pathlib.Path`); the recomputed `Path(...).resolve()` lookup is recognised
    (membership HITS);
  * the pre-change convention stored `unique_path(conftestpath)` (a
    `py.path.local`); the recomputed `pathlib.Path` lookup is NOT recognised
    (membership MISSES) — even though the two keys' location strings are equal
    and `py.path.local(s) == pathlib.Path(s)` compares true, they are not
    membership-compatible (distinct key kinds).

This is a CONTROL-FLOW / construction effect with no value-level discriminator
(the location strings are identical). It is modelled with an UNFORGEABLE
capability token (`lookup_recognised`) granted only by the recognised
construction — exactly per SPEC_GUIDE directive 8.

| # | model.py impl op (`conftest_dedup_key`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `loc: List[int]` | `str(conftestpath)` — the location string of the conftest | R | `str` ↔ `List[int]` code points (mapping.md §2). `str(conftestpath)` renders the path object to its string form, which the key constructor then canonicalises. |
| A2 | `make_key(loc, True)` — the key constructor invoked under the recognised convention; its `Ensures` give the canonical location string AND grant `lookup_recognised(...)` | `key = Path(str(conftestpath)).resolve()` | A-consumed | the key constructor is an UNCHANGED callee (CPython `pathlib.Path(...).resolve()` for the recognised convention; `unique_path`/`py.path.local` for the unrecognised one). Its contract is consumed by the proof: the recognised convention's `Ensures(Implies(recognised_convention, lookup_recognised(...)))` discharges the result's token clause. The contract is validated == the real cache-membership semantics by G-AX (axiom_check.py): a recomputed key HITS a dict keyed by the recognised key and MISSES one keyed by the unrecognised key, with identical location strings. (mapping.md §3.1.) |
| A3 | `canonical(Old(ToSeq(loc)))` — the value-level canonical location both conventions carry, used in the result's value postcondition | the canonical location string `str(Path(str(conftestpath)).resolve())` (and the removed `realpath(str(...))`) | A-consumed | the unchanged value-level canonicalisation (structural symlink/abs resolution) is the same string for both conventions on the F2P inputs (already-absolute, symlink-free). Axiomatized as the deterministic pure callee `canonical`; never the operation under change. Validated == the real resolution by G-AX. (mapping.md §3.2.) |
| A4 | `result` returned (a `List[int]` holding the token) | `key` used as `self._conftestpath2mod[key]` (store) and `self._conftestpath2mod[key]` (lookup) | R + I | the key is a location string under refinement R; using it identically as the dict key on both store (`config/__init__.py:457→:455`) and lookup (`:440→:436`) is the identical control/data flow. The dict-membership observable the F2P test pins (`Path(str(subconftest)).resolve() in _conftestpath2mod`) succeeds iff the stored key holds the recognition capability — exactly the `lookup_recognised` token the result postcondition requires. |

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the cache-key construction convention — is modelled by the `make_key` callee
contract whose distinguishing EFFECT (granting the unforgeable
`lookup_recognised` token only under the recognised convention) is the
load-bearing change. The token is an abstract `@ContractOnly @Predicate`: it has
no body, so a verifying impl cannot fabricate it via `Fold`, and Nagini does not
carry a predicate instance across value-equal copies — so an impl cannot launder
it from a value-equal unrecognised key. The result postcondition REQUIRES the
token, so the result can only be a key the recognised construction produced. No
callee under change is axiomatized as the function under change; `make_key` and
`canonical` are UNCHANGED callees whose contracts are validated == their real
behaviour by G-AX (axiom_check.py).

## C. verify(model) ⇒ resolved

`conftest_dedup_key` verifies only if its result (a) carries the canonical
location string of the input (`ToSeq(Result()) == canonical(...)`, A3) and (b)
holds the `lookup_recognised` token (A2). Clause (b) is dischargeable ONLY by
routing the result through `make_key(loc, True)`, the recognised convention — a
result built under the unrecognised convention carries the same location string
but lacks the token and FAILS the postcondition (`model_prepatch.py` is exactly
that and fails on the `lookup_recognised` clause; the echo-cheat that returns
`make_key(loc, False)` likewise fails). By R (`str` ↔ `List[int]`) the verified
key equals the canonical location string, and by A2/G-AX the recognised
convention is `Path(str(conftestpath)).resolve()`, whose key a recomputed
`Path(...).resolve()` lookup recognises (HIT). The gold patch stores/looks-up
`_conftestpath2mod` under exactly that recognised key, so a model satisfying this
spec, refined by the map above, IS the gold patch up to type refinement and the
audited callees — and the gold patch resolves (G-RESOLVE). The FAIL_TO_PASS
tests observe `Path(str(subconftest)).resolve() in conftest._conftestpath2mod`:
post-patch the stored key is recognised and the lookup HITS; the pre-patch
`unique_path` key (same string, unrecognised kind) MISSES — exactly the
discrimination the spec encodes via `lookup_recognised`. The trust points of
PLAN §1.1 active here are the two consumed-callee contracts (`make_key`,
`canonical`), both validated by G-AX (axiom_check.py); refinement fidelity is
this document (G-EQ).
