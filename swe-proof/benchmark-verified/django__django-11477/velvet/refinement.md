# refinement.md — django__django-11477

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`bindCaptures` `do` block, plus the `keepOne`/`keepPresent` pure model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none in this bundle), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); this narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The binding site — `RegexPattern.match()` (`django/urls/resolvers.py:153-158`)

Gold hunk:
```
- kwargs = match.groupdict()
+ kwargs = {k: v for k, v in match.groupdict().items() if v is not None}
  args = () if kwargs else match.groups()
  return path[match.end():], args, kwargs
```

| # | Solution.lean impl op (`bindCaptures`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `namedGroups : List Named` | `match.groupdict()` — the `dict[str, Optional[str]]` of named captures | R | dict (insertion order) ↔ key-distinct assoc list; `None` value ↔ `(name, none)`, present value ↔ `(name, some v)` (mapping.md §2). The regex result is an **input**, not a callee. |
| A2 | parameter `positionalGroups : List String` | `match.groups()` — the tuple of positional captures | R | tuple ↔ list (mapping.md §2). Also an input. |
| A3 | `out.named = keepPresent namedGroups`, computed by the backward `while` fold (each step prepends `keepOne p`) | `{k: v for k, v in match.groupdict().items() if v is not None}` | I | the dict comprehension's `if v is not None` filter IS `keepOne` (`some ↦ keep`, `none ↦ drop`); the comprehension over `.items()` in order IS the front-recursive concat `keepPresent`. Concrete, transliterated by G-CONF. **Discriminating op** — see below. |
| A4 | `out.positional = if out.named = [] then positionalGroups else []` | `args = () if kwargs else match.groups()` | I | truthiness of the new `kwargs` dict ↔ `out.named = []` (an empty assoc list is the empty dict, which is falsy); `()` ↔ `[]`; `match.groups()` ↔ `positionalGroups`. Unchanged source line, but its observable value is re-driven by the new `kwargs` (A3), so it is modeled. |
| A5 | (omitted) `path[match.end():]` remainder | the returned triple's first element | — | identical pre/post-patch, untouched by the diff; out of scope of the modeled change (mapping.md §2, §3). Not a behavioural difference any F2P test can attribute to this patch. |

Discriminating content of the change: an absent optional named group
(`v is None`) must be **dropped** from `kwargs`. In the model that is
`keepOne (name, none) = []` feeding `keepPresent`, so
`out.named = keepPresent namedGroups` omits every `none`-valued pair. The
pre-patch `kwargs = match.groupdict()` kept every group verbatim;
`Solution_prepatch.lean` reproduces that (`result := p :: result`, no filter)
and **fails** `out.named = keepPresent namedGroups` (G-DIFF) on exactly the
`ensures_2` clause whenever a group bound `none`.

This single change has TWO observable consequences, both pinned by the spec:
1. **kwargs** no longer carries `name: None` entries (A3) — the
   `test_re_path_with_optional_parameter` / `test_translate_url_utility` F2P
   assertions on `match.kwargs`.
2. **args** flips when ALL named groups are absent: pre-patch `kwargs` was a
   non-empty dict (`{arg2: None}`) so `args` was `()`; post-patch `kwargs`
   becomes empty, so `args = match.groups()` (A4) — the
   `named_optional_terminated … /optional/1/ … [1], {}` F2P reverse case.
   `out.positional`'s `if out.named = []` guard captures this flip exactly.

## B. No kind-A steps

Every step is R or I. The operation that changed — the keyword-binding filter —
is modeled **directly** (`keepOne`/`keepPresent`, the spelled-out fold, A3, an
**I** step), not behind an axiom. There are no unchanged callees whose contract
the proof consumes: `match.groupdict()` / `match.groups()` are evaluated inputs
(R, A1/A2), and the only other op the real `match` performs (`path[match.end():]`)
is unchanged and unmodeled (A5).

## C. No kind-3 (inexpressible-changed-op) steps

The changed op is a finite per-element filter and an emptiness test — both
expressible. Nothing is hidden.

## D. verify(Solution) ⇒ resolved

`bindCaptures` verifies only if (A3) its keyword bindings equal the
present-only filter `keepPresent namedGroups` and (A4) its positional bindings
appear exactly when there are no keyword bindings. By R (`dict ↔ assoc list`,
`tuple ↔ list`, mapping.md §2) the verified `(out.named, out.positional)` equals
the gold `(kwargs, args)` of the patched `match` on the tested inputs; by G-CONF
the R/I transliteration agrees with the **real** patched `RegexPattern.match`
over ≥10⁵ fuzzed `groupdict`/`groups` inputs. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there are no axioms (so G-AX is a skip).
