# mapping.md — pytest-dev__pytest-5840

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 73c5b7f4b11a81e971f7d1bb18072e06a87060f4`, states the type
abstraction, and gives the provenance of the callees the contracts are validated
against.

Repo files under change: `src/_pytest/config/__init__.py`,
`src/_pytest/pathlib.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `conftest_dedup_key(loc)` | the dedup-key computation in `PytestPluginManager._importconftest` — `src/_pytest/config/__init__.py:434` (the key line `conftestpath = unique_path(conftestpath)` at `:438`, used as `self._conftestpath2mod[...]` key at `:440,:457`) | the modeled changed function: it computes the key under which a conftest module is cached/looked-up |
| `make_key(loc, recognised_convention)` *(A-consumed)* | the key constructor the cache key is built by — `Path(str(conftestpath)).resolve()` (`config/__init__.py:432` post-patch, the recognised convention) vs `unique_path(conftestpath)` (`config/__init__.py:438` pre-change, the unrecognised convention) | callee contract: returns a key carrying the canonical location string under EITHER convention; grants `lookup_recognised` only under the recognised one |
| `lookup_recognised(canon)` *(capability token)* | the membership-recognition property of `_conftestpath2mod` — whether `Path(str(p)).resolve() in _conftestpath2mod` for a stored key (`config/__init__.py:440`) | abstract `@ContractOnly @Predicate`: the unforgeable capability that the cache's membership test recognises the key as equal to an independently-recomputed key for the same location |
| `canonical(loc)` *(A-consumed)* | the value-level canonicalisation of the location string — `str(Path(str(conftestpath)).resolve())` (post) / `os.path.realpath(str(conftestpath))` (pre); same string on the F2P inputs | pure callee: the structural symlink/abs resolution both conventions share; never the operation under change |

The pre-change repo symbol the change removes (for the refinement audit, not
referenced from the consumer spec view): the helper `unique_path` —
`src/_pytest/pathlib.py:340-346`,
`return type(path)(normcase(str(path.realpath())))`. It is called as the cache
key in `_importconftest` (`config/__init__.py:438`), in `_getconftestmodules`
(`:409`) and in `_set_initial_conftests` (`:370`). It returns a `py.path.local`
object; the post-change code keys the cache by a `pathlib.Path`. The two key
kinds compare `==` true and (on POSIX) carry the IDENTICAL location string, but
they are NOT membership-compatible: a `pathlib.Path` is not `in` a dict keyed by
`py.path.local` (distinct `__hash__`), so the recomputed-key lookup MISSES the
pre-change stored key and the subsequent re-import derives a dotted module name
the import machinery rejects.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` filesystem location (the argument `conftestpath` rendered via `str(...)`, and the resulting key's location string) | `List[int]` of Unicode code points | `s[k]` ↔ `loc[k] == ord(s[k])`; `len(s)` ↔ `len(loc)`; an empty `str` ↔ `[]` |
| `str` location inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `pathlib.Path` vs `py.path.local` key OBJECT (`config/__init__.py:432`/`:438`), distinguished by dict-membership recognition (`__hash__`/identity class), NOT by string value | the key as a `List[int]` location string + the abstract recognition token `lookup_recognised` | the cache is keyed by an object whose membership-recognition (whether a recomputed key is `in` the cache) is the F2P discriminator. The location STRING is identical across key kinds (carried by `canonical`); the changed, observable dimension is the recognition capability (carried by `lookup_recognised`, granted only by the recognised convention `Path(...).resolve()`). |
| `Path(str(conftestpath)).resolve()` symlink/abs canonicalisation | `canonical(loc)` — unchanged structural canonicalisation | both pre- and post-change canonicalise the location to the SAME string (`realpath` / `resolve`); the F2P inputs are already-absolute, symlink-free paths, so the canonical string is the location itself. The ONLY changed, observable dimension is the key kind's membership-recognition. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `make_key` / `lookup_recognised` ↔ the cache-key constructor + membership (A-consumed)
**Callee:** the cache-key constructor. Recognised convention (gold):
`Path(str(conftestpath)).resolve()` — a `pathlib.Path`. Unrecognised convention
(pre-change): `unique_path(conftestpath)` = `type(local)(normcase(realpath(...)))`
— a `py.path.local`. The cache's membership test is
`recomputed_key in _conftestpath2mod` where the lookup recomputes
`Path(str(p)).resolve()` independently (exactly the FAIL_TO_PASS test:
`key = Path(str(subconftest)).resolve(); assert key in
conftest._conftestpath2mod`).

The behaviour the gold patch establishes (`config/__init__.py`):
```python
# Use a resolved Path object as key to avoid loading the same conftest twice
# ...
# it resolves to the correct path/drive in case-insensitive file systems (#5792)
key = Path(str(conftestpath)).resolve()
...
return self._conftestpath2mod[key]
...
self._conftestpath2mod[key] = mod
```
A key built by the recognised convention is RECOGNISED by the membership test as
equal to an independently-recomputed key for the same location (membership HITS),
so the constructor's contract grants `lookup_recognised`. A key built by the
unrecognised convention carries the same location string but is NOT recognised
(membership MISSES), so no token is granted. The result postcondition REQUIRES
the token, so a verifying construction must route through the recognised
convention.

**Soundness check (G-AX):** `axiom_check.py` creates real conftest files (the
FAIL_TO_PASS subdir names `test`/`tests` — all lowercase, proving casing is NOT
the discriminator on POSIX — plus the issue scenarios and 2000 randomized fuzz
names). For each it builds both keys and asserts: (i) both carry the IDENTICAL
canonical location string (validating `canonical` and that string-equality is
not the discriminator); (ii) a recomputed `Path(...).resolve()` lookup is FOUND
in a dict keyed by the recognised key (`lookup_recognised` is sound — a real
membership HIT); (iii) the same recomputed lookup is NOT found in a dict keyed by
the unrecognised key (no token — a real membership MISS), despite the identical
location string. It imports only `pathlib`, `os`, `py` (the modules the patch
and the test use). Exit 0 iff sound. Docs:
https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve.

### 3.2 `canonical` ↔ `str(Path(str(p)).resolve())` / `realpath(str(p))` (A-consumed)
**Callee:** the value-level canonicalisation of the location string. Post-change
`Path(str(conftestpath)).resolve()` and pre-change
`os.path.realpath(str(conftestpath))` (inside `unique_path`) both resolve
symlinks and make the path absolute, producing the SAME string on the F2P inputs
(already-absolute, symlink-free). `canonical` is the deterministic pure model of
that unchanged structural resolution; it is NOT the operation under change (the
change is the key kind / membership recognition, §3.1). G-AX asserts both real
conventions agree on the canonical location string on every checked file.
