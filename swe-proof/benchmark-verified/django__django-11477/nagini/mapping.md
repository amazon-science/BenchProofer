# mapping.md — django__django-11477

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e28671187903e6aca2428374fdd504fca3032aee`, states the type
abstraction, and gives the provenance of the single deep-model reference (there
are no consumed axioms).

Repo file under change: `django/urls/resolvers.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_captures(keys, vals, positional)` | `RegexPattern.match(self, path)` — `django/urls/resolvers.py:150` (changed body line 156) | the modeled changed function: how a matched pattern reports captured named groups (kwargs) and positional captures (args) |
| `kept_keys(keys, vals)` *(deep model — A-reference)* | the retained keys of `{k: v for k, v in match.groupdict().items() if v is not None}` — `resolvers.py:156` (post-patch) | pure spec: the named-group names whose captured value is not `None` |
| `kept_vals(keys, vals)` *(deep model — A-reference)* | the retained values of that same dict comprehension | pure spec: the parallel retained captured values |
| `absent()` | Python `None` as a `re.Match.groupdict()` value for a named group that did not participate in the match | pure spec: the reserved absence sentinel |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view): `kwargs = match.groupdict()`
(`resolvers.py:156` @ base_commit) — the UNFILTERED named-group mapping, which
includes optional groups that did not participate, carrying their `None` value.

`RoutePattern.match` (`resolvers.py:248`, body line 252) also reads
`match.groupdict()` but is **not** changed by the gold patch (its named groups,
produced by `_route_to_regex`, are never optional), so it is out of scope.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `match.groupdict()` — `Dict[str, Optional[str]]` from named-group name to its captured string or `None` | two parallel `List[int]` — `keys` (group-name tokens, distinct) and `vals` (parallel captured-value tokens) | a dict entry `name -> value` ↔ `keys[i] == token(name)`, `vals[i] == token(value)`; `value is None` ↔ `vals[i] == absent()` (`-1`); `len(keys) == len(vals)` (one value per group). Only key/value identity and which groups participated are observed (the F2P tests compare `match.kwargs` for equality and `match.args`), so integer tokens are the faithful carrier. |
| a captured string value | a non-`absent()` `int` token | identity; the F2P tests observe value equality, not string content |
| `match.groups()` — the positional-capture tuple | `positional: List[int]` | a tuple element ↔ a list element (same order); a `tuple` ↔ a `List` (the F2P tests compare `match.args` for tuple equality) |
| `kwargs = {k: v for k, v in match.groupdict().items() if v is not None}` (post-patch) | `(Result()[0], Result()[1])` = `(kept_keys, kept_vals)` | the filtered dict, carried as parallel retained key/value sequences (order preserved) |
| `args = () if kwargs else match.groups()` (post-patch) | `Result()[2]` | `()` ↔ empty list when the retained mapping is non-empty; the positional list otherwise |
| `return path[match.end():], args, kwargs` | the path tail `path[match.end():]` is an unchanged carry-through, independent of the change; omitted from the model | the change touches only `args`/`kwargs`; the path tail is identical pre/post-patch |

`str` indexing/iteration is banned in Nagini, so captured values and group names
are carried as `int` tokens; the dict is carried as two parallel `List[int]` so
the retention filter is a sequence fold (front-recursive) the verifier unfolds.

## 3. Reference provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `kept_keys`/`kept_vals` deep model ↔ real `RegexPattern.match` (A-reference)
**Reference operation:** `RegexPattern.match` after the gold patch — the dict
comprehension `{k: v for k, v in match.groupdict().items() if v is not None}`
and the choice `args = () if kwargs else match.groups()`
(`django/urls/resolvers.py:156-157`). The changed retention/selection is modelled
**deeply** by the `@Pure` folds `kept_keys`/`kept_vals` (in the `pure` region)
and the verified loop in `select_captures`; there is **no consumed axiom**. The
deep model is validated equal to the real operation out-of-band by
axiom_check.py (G-AX).

Semantics relied on (CPython `re`, the engine `RegexPattern` uses via
`self.regex.search`): `re.Match.groupdict()` returns a dict with an entry for
EVERY named group in the pattern; a named group that did not participate in the
match has value `None` (its default). `re.Match.groups()` returns the tuple of
positional-group captures. Docs:
https://docs.python.org/3/library/re.html#re.Match.groupdict and `.groups`.
Hence the post-patch comprehension keeps exactly the named groups whose value is
not `None`, and `args` is `()` iff that retained mapping is non-empty — which is
what `kept_keys`/`kept_vals` and the `len(Result()[0]) == 0` choice encode.

**Soundness check (G-AX):** `axiom_check.py` runs the real post-patch
`RegexPattern.match` expression over an `re` match for 11 boundary
(pattern, path) pairs — the three F2P patterns (`regex_optional`,
`with-arguments`, `named_optional_terminated`) with both their participating and
non-participating paths, purely-positional patterns, an optional-only-named
pattern, mixed present/absent optional groups, and a group-free pattern — plus
25 000 randomized fuzz patterns with 0–3 optional named groups and a random
subset participating, and asserts the real `(kwargs, args)` equals the deep
model on every match. This gold-expression comparison is the **load-bearing**
soundness check; it runs on any host and exits 0 iff sound.

It ALSO drives the real `django.urls.resolvers.RegexPattern.match` end-to-end,
but **only against the post-patch target version** (`base_commit` Django 3.0 with
the gold patch). The driver is version-guarded by `repo_is_target_postpatch`,
which detects the target behaviourally (on a pattern with a non-participating
optional named group AND a positional group, 3.0 gold selects `args` against the
*filtered* mapping → `args == match.groups()`, whereas later releases such as
4.2 select `args` against the *unfiltered* `groupdict()` → `args == ()`). On a
non-target Django (or pre-patch repo, or absent surface) the end-to-end driver
is skipped so version skew cannot crash the sound checker (per the lead-auditor
verdict D3/D4). It imports only the standard-library `re` module (the engine the
patched code uses) plus, optionally, the repository package the gold patch edits.

**Required invocation:** run in the pinned eval container WITH the gold patch
applied (Django 3.0 @ `base_commit`) for the full check including the end-to-end
driver; the gold-expression check passes regardless of host. Exit 0 iff sound.
