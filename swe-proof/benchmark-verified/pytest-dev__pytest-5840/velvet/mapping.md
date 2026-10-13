# mapping.md — pytest-dev__pytest-5840

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 73c5b7f4b11a81e971f7d1bb18072e06a87060f4`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of every callee / deep-model reference.

Repo file under change: `src/_pytest/config/__init__.py` (and a helper removed
from `src/_pytest/pathlib.py`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `registerModule (mut registry) (loc) (freshMod)` | `PytestPluginManager._importconftest(self, conftestpath)` — `src/_pytest/config/__init__.py:431` | the modeled changed function (memoizing conftest importer) |
| `registry : List (Key × Module)` | `self._conftestpath2mod : dict` — `src/_pytest/config/__init__.py` (populated at `:453` post-patch) | the module cache mutated by the function |
| `loc : Nat` | the filesystem location denoted by the argument `conftestpath` | abstract identity of the path being imported |
| `freshMod : Module` | the module produced by `conftestpath.pyimport()` — `src/_pytest/config/__init__.py:446` | result of the UNCHANGED import callee on a cache miss (free input, R) |
| `probeKey loc` (`⟨loc, primary⟩`) *(deep model — A-reference)* | `Path(str(conftestpath)).resolve()` — `src/_pytest/config/__init__.py:447` post-patch | the cache key consumers/`_getconftestmodules` probe with (post-patch `_importconftest` keys here too) |
| `⟨loc, secondary⟩` (the prepatch key) *(deep model — A-reference)* | `unique_path(conftestpath) = type(p)(normcase(str(p.realpath())))` — `src/_pytest/pathlib.py:80` (called at `config/__init__.py:434` pre-patch) | the pre-patch cache key — a `py.path.local`-typed object for the same location |
| `regLookup` / `Key`-equality | `dict.__contains__` / `dict[...]` on `_conftestpath2mod` | structural key match = dictionary-key identity |

The pre-patch repo symbols the change removes (refinement audit only, not in the
consumer spec view): `from _pytest.pathlib import unique_path` import and the
`unique_path(...)` calls at `config/__init__.py:369,408,434`; the `unique_path`
helper itself (`pathlib.py:79-86`) and the now-unused `normcase` import
(`pathlib.py:14`). The F2P-load-bearing site is `_importconftest` only (§3.2).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a filesystem location (abstract identity, modulo the case-insensitive FS) | `loc : Nat` | each distinct location ↔ a distinct `Nat`; only equality of locations is observed |
| a *cache-key object* for a location | `Key = ⟨loc, rep⟩` | a key object ↔ `⟨loc, rep⟩` where `rep = primary` iff the object was built by `Path(str(p)).resolve()` (a `pathlib.Path`), `rep = secondary` iff built by `unique_path(p)` (a `py.path.local`). **Two key objects for the same location are equal as `Key` iff their constructing representation matches — mirroring real dict-key identity: same location but different object type ⇒ different hash ⇒ distinct dict key.** (axiom_check.py / G-AX validates this against the real objects.) |
| `self._conftestpath2mod` (`dict[keyobj, module]`) | `registry : List (Key × Module)` | dict ↔ association list; `key in d` ↔ `regLookup reg ⟨loc,rep⟩ ≠ none`; `d[key]` ↔ the matching `regLookup` value; insertion ↔ `++ [(k, m)]` (order-irrelevant; lookup is first-match by full key equality, and a location's key is inserted at most once) |
| a loaded conftest module (`mod`) | `Module := Nat` | only equality of modules is observed (whether two lookups return the same module); a bare identifier suffices |
| `conftestpath.pyimport()` result on a miss | `freshMod : Module` | the UNCHANGED import callee's output, taken as a free input — the spec makes no claim about its value (R; refinement.md §C) |

`regLookup` matches on full structural `Key` equality (location **and**
representation), which is the faithful model of dict-key identity: a `primary`
probe never matches a `secondary`-keyed entry, exactly as a `PosixPath` lookup
never matches a `LocalPath` key (different hash) — see §3.1.

## 3. Callee provenance & the deep-model reference (kind-A — checked by G-AX)

### 3.1 `Key`/`KeyRepr` deep model ↔ real path key objects (A-reference)
The "turn a path into a cache key" operation is modeled **deeply** by
`Key`/`KeyRepr`/`probeKey`; there is **no consumed axiom** about it. The single
behavioural fact the deep model encodes — and that `axiom_check.py` validates
against the REAL objects in the eval container — is:

For one filesystem location, the two key objects
* `primary  = Path(str(p)).resolve()`   (post-patch / consumer probe key), and
* `secondary = unique_path(p)`           (pre-patch cache key),

though they compare **`==` equal** as path values, are **distinct dictionary
keys**: `hash(primary) != hash(secondary)`, so `primary in {secondary: ...}` is
`False`, while `primary in {primary: ...}` is `True`. (Measured in-container:
`secondary` is a `LocalPath`, `primary` a `PosixPath`; `==` True, hashes differ.)
This is exactly `⟨loc, primary⟩ ≠ ⟨loc, secondary⟩` and
`regLookup [(⟨loc,secondary⟩,m)] (probeKey loc) = none` in the model.

`probeKey loc = ⟨loc, primary⟩` is the key consumers compute, so the cache is
correct (a registered location is found again) iff entries are stored under
`primary` — the post-patch behaviour. The pre-patch stored under `secondary`,
hence the F2P lookup miss.

### 3.2 The import callee (`pyimport`) — free input (R, not an axiom)
`conftestpath.pyimport()` is an UNCHANGED callee whose result the cache *decision*
never inspects (the patch touches only the KEY, never the value). It is taken as
the free input `freshMod`; the spec makes no behavioural claim about it and holds
for every value. No axiom, no G-AX obligation. (refinement.md §C.)

**Soundness check (G-AX):** `axiom_check.py` constructs real conftest-style paths
(including mixed-case directory names like `Foo/`, the #5819 scenario) in the
container, builds both key objects with the real `unique_path` (reconstructed
verbatim from `pathlib.py` pre-patch) and `Path(str(p)).resolve()`, and asserts
the distinct-dict-key property above on boundary + fuzz paths. Imports only
stdlib + `py` (the same `py.path.local` the repo uses). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`5840`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the `do` block (lookup-under-primary / append-under-primary) to a Python dict
keyed by the real `Path(str(p)).resolve()` objects, and diffs the post-state
"probe under the consumer key finds the module" predicate against `patch.diff`'s
behaviour (the patched `_importconftest` cache state) over fuzzed sequences of
path imports. `freshMod` (the import callee) is the only A-tagged op and it never
enters the computed key, so the impl region is pure R/I (`conf_skip=false`).
