# mapping.md — pytest-dev__pytest-5840

## Symbol binding (file:line @ base_commit 73c5b7f4b11a81e971f7d1bb18072e06a87060f4)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_cacheKey` / `problem_spec_cacheKey` | the cache-key derivation inside `PytestPluginManager._importconftest` (the `key = …` step that indexes `self._conftestpath2mod`) | `src/_pytest/config/__init__.py:431-439` (post-patch); base_commit lines `434-440` |
| `resolved : List Char` (input) | the canonical resolved absolute path string of the conftest file — `str(Path(str(conftestpath)).resolve())` post-fix; `str(conftestpath.realpath())` is the resolution the pre-fix `unique_path` performs before the case-fold | `__init__.py:438` (`Path(str(conftestpath)).resolve()`) |
| `result : List Char` (output) | the dictionary key actually used to store/look up the loaded module in `self._conftestpath2mod` | `__init__.py:436` and `:456` (`self._conftestpath2mod[key]`) |

The modeled function is the cache-key derivation in `_importconftest`. This is
the F2P-observable site: the FAIL_TO_PASS tests
(`test_setinitial_conftest_subdirs[test]`, `[tests]`) assert that the key under
which a loaded conftest is stored equals `Path(str(subconftest)).resolve()` —
i.e. the resolved path with its letter case preserved — rather than the
case-folded `unique_path(subconftest)`.

### What the code does (base_commit)

```python
def _importconftest(self, conftestpath):
    # Use realpath to avoid loading the same conftest twice ...
    conftestpath = unique_path(conftestpath)          # <-- key derivation
    try:
        return self._conftestpath2mod[conftestpath]
    except KeyError:
        ...
        self._conftestpath2mod[conftestpath] = mod    # stored under the same key
        ...
```

with, in `src/_pytest/pathlib.py`:

```python
def unique_path(path):
    """Returns a unique path in case-insensitive (but case-preserving) file
    systems such as Windows. ..."""
    return type(path)(normcase(str(path.realpath())))
```

`path.realpath()` canonicalizes the path (resolves symlinks, makes absolute).
`os.path.normcase` then, on case-insensitive file systems (Windows), folds the
result to **lower case**. That folded string becomes the cache key. On a
case-preserving file system the on-disk path retains its original case, so the
folded key no longer matches the path's true casing; the module's qualified name
is later derived from this corrupted path, producing
`ModuleNotFoundError: No module named '<lowercased-package>'`.

### What the patch changes

The post-patch code derives the key as `Path(str(conftestpath)).resolve()`:
`pathlib.Path.resolve()` canonicalizes the path (resolves symlinks, makes
absolute) **without folding case** — it returns the path with its true on-disk
casing preserved (the `unique_path` helper, and its only consumer's reliance on
`normcase`, are deleted). The observable change is therefore: the canonical
resolved path is used as the key **verbatim**, with letter case preserved, rather
than lower-cased.

### Lean modeling

- The path canonicalization (resolve symlinks / absolutize) is UNCHANGED across
  the patch — both `realpath()` (pre) and `Path.resolve()` (post) perform it. It
  is therefore factored out as the already-canonicalized **input** `resolved :
  List Char` (a path string as a sequence of characters; `str` per-code-point ↔
  `List Char`, SPEC_GUIDE §2). This keeps the model focused on the ONE behavior
  the patch changes.
- The modeled value is the key-derivation step applied to `resolved`:
  - **post-fix (Solution.lean):** the identity — `result = resolved` (case
    preserved).
  - **pre-fix (Solution_prepatch.lean):** the ASCII lower-case fold —
    `resolved.map Char.toLower` (modeling `os.path.normcase` on a
    case-insensitive file system, which is the configuration the bug manifests on
    and the F2P tests pin).

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| the canonical resolved path string (`str(path.realpath())` / `str(Path(...).resolve())`) | `resolved : List Char` | each Unicode code point of the string ↔ one `Char`, in order. |
| the cache key string stored in `self._conftestpath2mod` | `result : List Char` | same code-point ↔ `Char` correspondence. |
| `os.path.normcase(s)` on a case-insensitive (Windows) file system | `s.map Char.toLower` (pre-fix leg only) | per-character ASCII lower-casing (the case fold the bug performs). |
| post-fix key derivation (`Path(str(p)).resolve()` used verbatim as key) | the identity on `resolved` | the resolved path is the key, character-for-character. |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — how the cache
  key is derived from the resolved path — is modeled DEEPLY (SPEC_GUIDE §3: a
  deeply-modeled changed op is never axiomatized): post-fix it is the identity on
  the input path; pre-fix it is the lower-case fold. No property of an external
  callee is consumed by the proof, so the `axioms` region is empty and **G-AX
  skips**.
- `path.realpath()` / `Path.resolve()` — the path canonicalization. UNCHANGED by
  the patch (both legs canonicalize); factored out as the already-resolved input
  `resolved`, so its behavior is not part of the modeled value. Modeling only the
  touched behavior (SPEC_GUIDE §3); its omission constrains no output component
  the spec leaves free — the spec pins the full key.
- `os.path.normcase` (`src/_pytest/pathlib.py`, imported from `os.path`) — the
  case fold the bug applies; on a case-insensitive file system it lower-cases.
  The patch removes it; it is modeled deeply by `Char.toLower` in the PRE-FIX leg
  only (it is the discriminator), never axiomatized.
- **Flag/platform dependency:** `os.path.normcase` is the identity on
  case-sensitive (POSIX) file systems and a lower-case fold on case-insensitive
  (Windows) ones. The bug, the issue, and the new F2P tests
  (`test_setinitial_conftest_subdirs`) all concern the case-insensitive
  configuration — and the new `test_conftest_uppercase` is explicitly skipped on
  case-sensitive file systems. The pre-fix leg therefore models `normcase` in its
  case-folding (Windows) configuration, which is the configuration under which
  the behavior differs. Recorded here so G-CONF fuzzes paths containing
  upper-case characters (where the two legs disagree).

## G-CONF fuzz seed

Pinned LCG seed: **5840** (see `conformance_check.py` `SEED`). Corpus: random path
strings built from path separators and segment characters drawn from a small
alphabet that INCLUDES upper-case ASCII letters (so the case fold actually
bites), plus hand-picked edge cases (empty path, all-lower path, path with
upper-case package segments mirroring the issue's `imageProcessing`, mixed-case
drive letters). The R/I shadow of `implementation_cacheKey` (the identity) is
diffed against an in-process replica of the POST-PATCH key derivation
(`Path(str(p)).resolve()` used verbatim, modeled as the identity on the
already-resolved path), over ≥1e5 fuzzed inputs. The discriminating clause —
paths whose case fold differs from the original — is pinned by the upper-case
edge cases, where the pre-fix leg (`normcase`) would disagree.
