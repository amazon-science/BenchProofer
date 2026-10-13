# mapping.md — sphinx-doc__sphinx-7985

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f30284ef926ebaf04b176f21b421e2dffc679792`, states the type
abstraction, and gives the provenance of each modelled callee.

Repo file under change: `sphinx/builders/linkcheck.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check(target, file_exists, ignore_match, remote)` | the nested `check()` of `CheckExternalLinksBuilder.check_thread` — `sphinx/builders/linkcheck.py:211` (body 213-225 pre-patch) | the modeled changed function: per-target status classification without contacting the network |
| `classify(s, file_exists, ignore_match, remote)` | the post-patch decision cascade of `check()` (`linkcheck.py:213-225` post-patch) | pure spec: the full classification as a function of target + environment facts |
| `starts_with(target, lit)` | `str.startswith(prefix)` (`uri.startswith((...))` at `linkcheck.py:213,215`) | deep model (A-reference) of the anchored literal prefix test |
| `prefix_eq(s, lit)` | the literal prefix relation underlying `str.startswith` | pure spec: literal prefix match |
| `scheme_present(target)` | `uri_re.match(uri)` where `uri_re = re.compile('[a-z]+://')` (`linkcheck.py:38` module level, used at the post-patch `check()` `if uri_re.match(uri)`) | deep model (A-reference) of the introduced scheme-shape regex match |
| `has_uri_scheme(s)` / `lower_run(s)` | the anchored match of `re.compile('[a-z]+://')` | pure spec: a `[a-z]+://` scheme prefix is present |
| `UNCHECKED/WORKING/MISSING/IGNORED` | the status strings `'unchecked' / 'working' / 'broken' / 'ignored'` returned by `check()` | pure spec: the four local-classification outcomes as integer codes. The model symbol for `'broken'` is named `MISSING` — a behaviour-faithful synonym describing the modelled meaning (the referenced local target is absent); the `MISSING ↔ 'broken'` binding is recorded here and in refinement.md A11. |
| `remote` parameter | the value returned by the unchanged web branch (cache hits in `self.good/self.broken/self.redirected`, the top-level `to_ignore` loop, and `check_uri()`'s network probe) | opaque outcome of the unchanged remote-handling branch |
| `file_exists` parameter | `path.exists(path.join(self.srcdir, uri))` (post-patch `check()`) | environment fact: the local file is present on disk |
| `ignore_match` parameter | `any(rex.match(uri) for rex in self.to_ignore)` (the inner ignore loop the patch adds) | environment fact: some configured ignore pattern matches the target |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): the non-web branch returned the
unclassified status `'local'` for every target (`linkcheck.py:215-216`
pre-patch: `elif not uri.startswith(('http:', 'https:')): return 'local', '', 0`),
and the first guard included `'ftp:'` in the unchecked tuple
(`linkcheck.py:213` pre-patch: `uri.startswith(('#', 'mailto:', 'ftp:'))`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `uri: str` (the target) | `target: List[int]` of Unicode code points | `uri[k]` ↔ `target[k] == ord(uri[k])`; `len(uri)` ↔ `len(target)`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` slice/`len`/index |
| `uri.startswith(prefix)` | `prefix_eq(ToSeq(target), lit)` / `starts_with(target, lit)` | anchored literal prefix; `lit` is the prefix as a code-point sequence (e.g. `'http:'` ↔ `PSeq(104,116,116,112,58)`) |
| `uri.startswith((p1, p2))` (tuple) | `prefix_eq(.., p1) or prefix_eq(.., p2)` | `str.startswith` with a tuple is the disjunction of the per-prefix tests |
| `uri_re.match(uri)` truthiness (`uri_re = re.compile('[a-z]+://')`) | `has_uri_scheme(ToSeq(target))` (bool) | `re.match` is anchored at the start; the pattern matches iff a maximal leading `[a-z]+` run (length ≥ 1) is immediately followed by `://` (§3.2) |
| status strings `'unchecked'/'working'/'broken'/'ignored'` | int codes `0/1/2/3` | the four returned statuses; the F2P tests observe these via the rendered output (`[broken] path/to/notfound`) and the JSON `status` field |
| `path.exists(path.join(self.srcdir, uri))` | boolean input `file_exists` | a genuinely environment-dependent fact (filesystem); not a callee with a checkable value contract — supplied as an input, exactly as the real `check()` consumes the boolean |
| the inner `for rex in self.to_ignore: if rex.match(uri)` loop | boolean input `ignore_match` | "some configured ignore pattern matches the target"; the per-pattern regex is user configuration, modelled as the resulting boolean |
| the unchanged web branch outcome | opaque int input `remote` | the cache/network classification is unchanged by the patch; modelled as an opaque value so the model neither over- nor under-constrains it |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**: the two changed string
decisions are modelled deeply, so the corresponding real callees are
**A-references** validated == the deep model out-of-band by axiom_check.py
(G-AX), never consumed by the proof.

### 3.1 `starts_with` / `prefix_eq` deep model ↔ `str.startswith` (A-reference)
**Callee:** CPython `str.startswith(prefix)`. The anchored literal prefix test
is modelled deeply by `prefix_eq` (front-recursive over `PSeq[int]`) and the
verified loop in `starts_with`. `str.startswith(prefix)` returns True iff the
first `len(prefix)` characters of the string equal `prefix` exactly; for a
prefix longer than the string it is False. `str.startswith((p1, p2))` (the
tuple form used at `linkcheck.py:213,215`) is `startswith(p1) or
startswith(p2)`. G-AX asserts `prefix_eq(s, lit) == s.startswith(lit)` for each
literal `#`, `mailto:`, `http:`, `https:`, `ftp:` on boundary + 80 000 fuzz
inputs. Docs: https://docs.python.org/3/library/stdtypes.html#str.startswith.

### 3.2 `scheme_present` / `has_uri_scheme` deep model ↔ `re.match('[a-z]+://')` (A-reference)
**Callee:** `re.compile('[a-z]+://').match(uri)` — the regex the gold patch
introduces at module level (`uri_re`, `linkcheck.py:38` post-patch), used as
`if uri_re.match(uri):` in the local branch. `re.Pattern.match` is **anchored at
the start** of the string. The pattern `[a-z]+://` requires one or more ASCII
lowercase letters, then the three literals `:`,`/`,`/`. Because `:` is not in
`[a-z]`, the `[a-z]+` token consumes the *maximal* leading lowercase run, then
demands `://` immediately after it; so the match succeeds iff

  `k := len(maximal leading [a-z] run) ≥ 1`  and  `uri[k:k+3] == '://'`.

This is exactly `has_uri_scheme` (`lower_run` computes `k`; the model checks
`s[k]==':'` (58), `s[k+1]=='/'` (47), `s[k+2]=='/'` (47)). **Flag dependency:**
the pattern is the default (no `re.IGNORECASE`), so the run is ASCII lowercase
only — an uppercase or digit lead does not start a scheme (e.g. `Scheme://` and
`1://` do NOT match), which G-AX fuzzes explicitly. G-AX asserts
`has_uri_scheme(s) == (uri_re.match(s) is not None)` on boundary + 80 000 fuzz
inputs. Docs: https://docs.python.org/3/library/re.html#re.Pattern.match.

### 3.3 `classify` deep model ↔ the real post-patch `check()` (A-reference)
**Callee:** the gold-patched nested `check()` body. axiom_check.py transcribes
that body verbatim (statuses as the integer codes; `path.exists(...)` →
`file_exists`; the inner ignore loop → `ignore_match`; the unchanged web branch
→ `remote`) and asserts `classify(s, fe, im, rem) == real_check(...)` over all
boundary + fuzz inputs. It also transcribes the **pre-patch** `check()` and
confirms the four F2P targets (`conf.py`→working, `path/to/notfound`→broken,
the same ignored, a non-tuple `gopher://` scheme→unchecked) discriminate the
fixed model from the buggy `'local'`-returning pre-patch — i.e. the deep model
tracks the FIXED behaviour, not the bug.

**Soundness check (G-AX):** `axiom_check.py` imports only the standard-library
`re` module (the very module the patch uses) and passes the filesystem/ignore
facts as booleans (no real I/O). Exit 0 iff every obligation holds.
