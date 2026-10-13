# mapping.md — astropy__astropy-14309

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = cdb66059a2feb44ee49021874605ba90801f9986`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `astropy/io/fits/connect.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `classifyFitsOrigin (stream, path, extra)` | `is_fits(origin, filepath, fileobj, *args, **kwargs)` — `astropy/io/fits/connect.py:48` (body lines 62-72) | the modeled changed function (origin classifier) |
| `stream : Option Bool` | the `fileobj` parameter and its signature comparison `sig == FITS_SIGNATURE` (`connect.py:62-66`) | readable-stream branch, collapsed to its boolean verdict |
| `path : Option (List Char)` | the `filepath` parameter (`connect.py:67`) | path branch input |
| `extra : List Bool` | the trailing `*args` sequence, each entry collapsed to its `isinstance(arg, (HDUList, TableHDU, BinTableHDU, GroupsHDU))` verdict (`connect.py:72`) | object-class branch |
| `hasKnownExt (path)` *(deep model — A-reference)* | `filepath.lower().endswith((".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz"))` (`connect.py:67-69` post-patch) | pure spec: case-insensitive known-extension test; deep model of the UNCHANGED case-folding suffix test, validated `hasKnownExt == real .lower().endswith((...))` by axiom_check.py (G-AX), NOT a consumed axiom |
| `Crash.indexOOB` | the `IndexError` raised by `args[0]` when `args` is empty (`connect.py:72`) | the absent-observation failure the public problem statement reports |

The behaviour the change touches is purely CONTROL FLOW: pre-patch the path
branch only short-circuits to `True` on a match and otherwise falls THROUGH to
`args[0]`; post-patch the path branch returns the extension test's boolean
outright. No callee is added, removed, or redefined.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `fileobj` (a readable stream, or `None`) | `Option Bool` | `None` ↔ `none`; a present stream ↔ `some (sig == FITS_SIGNATURE)` — the branch's only observation is that boolean, so the stream is collapsed to it (the stream's bytes are never compared by the change) |
| `filepath` (`str` path, or `None`) | `Option (List Char)` | `None` ↔ `none`; a `str` ↔ `some s.toList`; `len(s)` ↔ `l.length`; empty `str` ↔ `some []` |
| a single path character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `*args` (trailing positional tuple) | `List Bool` | the tuple `(a0, a1, …)` ↔ `[b0, b1, …]` where `bi = isinstance(ai, (HDUList, TableHDU, BinTableHDU, GroupsHDU))`; empty tuple ↔ `[]`; `args[0]` ↔ head of the list, an IndexError on empty ↔ `Crash.indexOOB` |
| `str.lower()` (`connect.py:67`) | `List.map Char.toLower` | per-code-point case fold; on the BMP ASCII-and-Latin extension targets these agree (the recognised suffixes are pure ASCII, so any case variant of them is decided identically) |
| `str.endswith(tuple)` (`connect.py:67`) | `knownExts.any (·.isSuffixOf ·)` | Python `endswith` over a tuple is True iff the string ends in ANY member; `List.isSuffixOf` over the known-extension list, OR-folded by `List.any`, encodes exactly that |
| `IndexError` raised by `args[0]` | `Except.error Crash.indexOOB` | the only escaping failure of the function; a returned `bool` ↔ `Except.ok b` |

The carrier for `filepath` is `List Char` because the operation is
per-code-point (lowercasing + suffix match). Lean `List`/`String` indexing is
total and sound.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `hasKnownExt` deep model ↔ `str.lower().endswith((...))` (A-reference)
**Callee:** Python `str.lower()` then `str.endswith(tuple)` (`connect.py:67-69`),
both UNCHANGED by the patch (the patch only removes the `if …: return True` /
fall-through wrapper around this expression). The extension test is modeled
**deeply** by `hasKnownExt` (with `knownExts`) in the `pure` region; there is
**no consumed axiom** about it. The six recognised lowercase suffixes are
`.fits`, `.fits.gz`, `.fit`, `.fit.gz`, `.fts`, `.fts.gz`.

Because `str.endswith(tuple)` returns True iff the (lowercased) string ends in
any tuple member, and the suffixes are pure ASCII, the chained
`.lower().endswith((...))` is exactly: lowercase every code point, then test
membership of any known suffix — which is what `hasKnownExt`/`knownExts`
encode (note `.fits.gz` and `.fit.gz` are multi-dot suffixes, handled by the
plain `isSuffixOf` over the whole tail, no tokenisation).

**Soundness check (G-AX):** `axiom_check.py` evaluates the real
`s.lower().endswith((...))` on boundary inputs (each suffix alone, upper/mixed
case variants, multi-dot tails, empty string, names with the extension in the
middle but not the end) plus 20 000 randomized fuzz strings, asserting the Lean
`hasKnownExt` transliteration agrees with the real expression on every input. It
also calls the REAL `connect.is_fits` directly to confirm the boundary facts the
control-flow model relies on: a present `filepath` (matching or not) never reads
`args` (so never raises), and a path-absent call with empty `*args` raises
`IndexError` on the real function. Imports only the astropy under test. Exit 0
iff sound.

There is **no A-consumed axiom**: the proof discharges by `simp_all [originSpec]`
over the concrete branch structure; `hasKnownExt` is a concrete `def`, not an
axiomatized contract. `Crash.indexOOB` is a modeled OUTCOME (an inductive
constructor), not a callee contract.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14309`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the branch control flow (the I ops) to Python and leaves the extension test as
the real `str.lower().endswith((...))` (the A-reference callee → real code, not
the model). The oracle is the gold-patched real `connect.is_fits`, classified
into the `Except Crash Bool` outcome domain (catch `IndexError` → `error`, a
returned bool → `ok`).
