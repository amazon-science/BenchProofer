# mapping.md — django__django-11477

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e28671187903e6aca2428374fdd504fca3032aee`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and the pinned G-CONF fuzz seed.

Repo file under change: `django/urls/resolvers.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `bindCaptures (namedGroups, positionalGroups)` | the post-search binding block of `RegexPattern.match(self, path)` — `django/urls/resolvers.py:150` (changed body lines 153-158) | the modeled changed function: turns the regex capture into the `(kwargs, args)` a route exposes |
| `keepPresent (xs : List Named)` | the `{k: v for k, v in match.groupdict().items() if v is not None}` dict comprehension introduced by the patch (`resolvers.py:156` post-patch) | pure spec: the keyword bindings, keeping only groups that bound a value |
| `keepOne (p : Named)` | the per-item `if v is not None` test of that comprehension | pure spec: one group's contribution to the keyword bindings |
| `Bindings.positional` selection (`if out.named = [] then …`) | `args = () if kwargs else match.groups()` (`resolvers.py:157`, UNCHANGED by the patch but observably re-driven by the new `kwargs`) | pure spec: positional bindings are surfaced only when there are no keyword bindings |

There is **no axiom and no deep-model reference** in this bundle: the operation
the patch changes is a pure post-processing of values the regex engine already
produced (`match.groupdict()`, `match.groups()`). Those values are the **inputs**
to the modeled function (`namedGroups`, `positionalGroups`), not callees whose
contract the proof must assume. The regex engine itself is unchanged and is not
modeled — it only supplies the inputs (mapping.md §2, §3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `match.groupdict()` — an insertion-ordered `dict[str, Optional[str]]` of named-group captures | `List Named = List (String × Option String)` | the dict's `.items()` in insertion order ↔ the list in order; a present capture `name: "v"` ↔ `(name, some "v")`; an absent optional capture `name: None` ↔ `(name, none)`. Python `dict` over distinct keys ↔ a key-distinct association list; `len` ↔ `.length`. |
| `match.groups()` — the tuple of all non-named positional captures | `List String` (`positionalGroups`) | tuple in order ↔ list in order. (Repo `None` entries are immaterial here: a route either has named groups, in which case `args` is `()`, or it has none; the F2P inputs use named groups only.) |
| the comprehension result `kwargs` (a `dict`) | `out.named : List Named` | same dict↔assoc-list bijection; key order preserved (CPython dict comprehension preserves source order). |
| `args` (a tuple) | `out.positional : List String` | tuple↔list; the empty tuple `()` ↔ `[]`. |
| the returned triple `(path[match.end():], args, kwargs)` | `(out.named, out.positional)` modeled; the unchanged `path[match.end():]` slice omitted | the leading remainder-of-path element is computed identically pre/post-patch (untouched by the diff) and is not part of the modeled change; mapping.md §3. |

A Python `str` group value is carried opaquely as a Lean `String` — the modeled
operation never inspects a value's contents, only whether it is present
(`is not None` ↔ `Option.isSome`). So the `String` payload is a transparent
token; only its `some`/`none` status is behaviourally load-bearing.

## 3. Callee provenance

**No kind-A callees.** `match.groupdict()` and `match.groups()` are evaluations
of the (unchanged) compiled regex against `path`; their results are the *inputs*
the modeled function consumes. The patch does not change them, nor any routine
they call, so there is nothing to axiomatize or deep-model. The only unchanged
op the real `match` performs that is omitted from the model is the
`path[match.end():]` remainder slice (identical pre/post-patch, observationally
out of scope of the diff). Hence:

- `axiom_check.py` (G-AX) has no axioms to validate — it is a `status=skip`
  stub (no `axioms` content), consistent with `meta.json axioms = []`.
- `conformance_check.py` (G-CONF) carries the whole behavioural burden: it
  drives the **real** patched `RegexPattern.match` and compares its
  `(args, kwargs)` against the R/I transliteration of `bindCaptures`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11477`** so the
consumer-side verdict is reproducible. Its R/I shadow transliterates
`keepOne`/`keepPresent` and the `args` fallback (all R/I-tagged ops) to Python;
there are no A-tagged callees to leave as real (§3).
