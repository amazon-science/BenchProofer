# refinement.md — pytest-dev__pytest-5840

Maps every operation in `implementation_cacheKey` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `cacheKey` (the key derivation in `PytestPluginManager._importconftest`)

Post-patch repo code (`patch.diff`, `src/_pytest/config/__init__.py`):
```python
def _importconftest(self, conftestpath):
    # Use a resolved Path object as key to avoid loading the same conftest twice
    # ... Using Path().resolve() is better than py.path.realpath because
    # it resolves to the correct path/drive in case-insensitive file systems (#5792)
    key = Path(str(conftestpath)).resolve()      # changed: was unique_path(conftestpath)
    try:
        return self._conftestpath2mod[key]
    except KeyError:
        ...
        self._conftestpath2mod[key] = mod
        ...
```

Lean impl (`implementation_cacheKey`):
```lean
def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
  let key := resolved
  return key
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `resolved : List Char` (input carrier) | the canonical resolved absolute path string of the conftest file — `str(Path(str(conftestpath)).resolve())` post-fix, `str(conftestpath.realpath())` pre-fix | **R** | the path canonicalization (resolve symlinks / absolutize) is UNCHANGED by the patch (both legs perform it), so it is factored out as the already-resolved input; `str` per-code-point ↔ `List Char` (SPEC_GUIDE §2). See mapping.md. |
| 2 | `let key := resolved` | `key = Path(str(conftestpath)).resolve()` used verbatim as the dictionary key | **I** (deep model of the changed op) | **the fixed operation.** Post-fix the resolved path is used as the cache key with its letter case PRESERVED — no normalization is applied (`Path.resolve()` canonicalizes without folding case, and `normcase`/`unique_path` are deleted). Modeled as the identity on the already-resolved `resolved`. This is the heart of the fix. |
| 3 | `return key` | `self._conftestpath2mod[key]` (store/lookup under that key) | **R** | the derived key is what indexes the module cache; the modeled output is that key string. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched key derivation.

## Callee provenance (no consumed axiom)

- `Path.resolve()` / `py.path.local.realpath()` — the path canonicalization
  (resolve symlinks, make absolute). UNCHANGED by the patch (both pre- and
  post-fix canonicalize); factored out as the already-resolved input `resolved`,
  so it is not part of the modeled value. Not axiomatized: its omission
  constrains no output component the spec leaves free (the spec pins the full
  key as a function of `resolved`).
- `os.path.normcase` — the case fold the bug applies (lower-cases on
  case-insensitive file systems). The patch REMOVES it. It is the changed op's
  PRE-fix behavior, modeled deeply by `Char.toLower` in the prepatch leg only;
  never axiomatized (SPEC_GUIDE §3: never axiomatize the operation the patch
  changes).
- `str(...)`, dictionary indexing (`self._conftestpath2mod[key]`) — identical
  concrete container/string ops; the key string is what the model produces.

## Soundness check (verify ⟹ correct)

- `problem_spec_cacheKey` pins the result EXACTLY: `result = resolved` (full
  equality to the input path) — directive 5 (frame): the key is determined
  entirely by the resolved input path, with no component left free. No ungrounded
  oracle (directive 8) — the postcondition is dischargeable only by reproducing
  the resolved path character-for-character, including its letter case.
- The prepatch impl reproduces the PRE-FIX behavior: `resolved.map Char.toLower`,
  modeling `normcase` lower-casing the path on a case-insensitive file system. It
  violates the spec on the discriminating clause — any `resolved` containing an
  upper-case character has `resolved.map Char.toLower ≠ resolved`, so the carried
  gold proof (`rfl`) cannot close (verified: G-DIFF, exit 1). For an all-lowercase
  path the two legs coincide, but the spec demands equality for ALL inputs, so the
  prepatch is unprovable in general.
- This discriminating case is precisely what the FAIL_TO_PASS tests assert:
  `test_setinitial_conftest_subdirs[test]` / `[tests]` store a conftest whose
  resolved path key is `Path(str(subconftest)).resolve()` (case preserved) and
  assert that key — not the case-folded `unique_path(subconftest)` — is present in
  `_conftestpath2mod`. The new `test_conftest_uppercase` exercises an upper-case
  package segment (`Foo/`), reproducing the issue's `imageProcessing` casing.
- G-CONF confirms the R/I shadow (identity) == an in-process replica of the
  patched key derivation over hand-picked edge cases (upper-case package
  segments, mixed-case drive letters) plus ≥1e5 fuzzed path strings drawn from an
  alphabet that includes upper-case letters (so the discriminator bites).
