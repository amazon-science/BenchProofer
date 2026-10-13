# mapping.md — sphinx-doc__sphinx-8459

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 68aa4fb29e7dfe521749e1e14f750d7afabb3481`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the modeled callees.

Repo file under change: `sphinx/ext/autodoc/typehints.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recordParamTypes (params, retAnnot, aliases, renderType)` | `record_typehints(app, objtype, name, obj, options, args, retann)` — `sphinx/ext/autodoc/typehints.py:23` (body lines 28-35) | the modeled changed function: records each parameter's display type string, plus the return type, into an ordered mapping |
| `params : List Param` | `sig.parameters.values()` where `sig = inspect.signature(obj, …)` — `typehints.py:30-31` | the callable's ordered parameter list; each carries a name and an optional annotation |
| `retAnnot : Option SourceType` | `sig.return_annotation` (vs `sig.empty`) — `typehints.py:34` | the return annotation, present iff it is not `Parameter.empty` |
| `aliases : Aliases` | `app.config.autodoc_type_aliases` — the configured alias map; **the value the gold patch newly passes through** | the configured alias map (an ordered name→target association) |
| `renderType : Aliases → SourceType → TypeStr` *(free input)* | the composite renderer `inspect.signature(obj, type_aliases=·)` + `typing.stringify(·)` — `sphinx/util/inspect.py:471` + `sphinx/util/typing.py:278` | UNCHANGED callees. Given an alias map and a source annotation, produces its display string. Modeled as a free (universally-quantified) input, NOT an axiom or deep model — see §3. |
| `paramEntry`, `recordedTypes`, `returnEntry` (pure region) | the body loop of `record_typehints` (`typehints.py:32-35`): skip unannotated params, record `name → stringify(annotation)`, record `'return' → stringify(return_annotation)` last | pure spec of the recorded mapping as an ordered assoc list |

The pre-patch behavior the change removes (refinement audit only, not in the
consumer spec view): `inspect.signature(obj)` was called with the **default
empty** `type_aliases={}` (`sphinx/util/inspect.py:472`), so configured aliases
were never consulted when `autodoc_typehints == 'description'`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a Python `str` (a name, a source annotation string, a rendered display string) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; empty ↔ `[]`; on the BMP `Char.ofNat (ord ch)` ↔ `ch` is total and exact |
| `sig.parameters.values()` (ordered) | `List Param` | order-preserving; `p.name` ↔ `Param.name`; `p.annotation` (vs `param.empty`) ↔ `Param.annot : Option SourceType` (`empty` ↔ `none`) |
| `sig.return_annotation` (vs `sig.empty`) | `Option SourceType` | present ↔ `some`, `empty` ↔ `none` |
| `app.config.autodoc_type_aliases` (a `dict[str,str]`) | `Aliases = List (List Char × List Char)` | ordered association; opaque to the spec — consulted only by `renderType` |
| the `OrderedDict` `annotation` populated by `record_typehints` | `List (List Char × TypeStr)` | order-preserving; `OrderedDict.items()` ↔ the assoc list; the fixed key `'return'` ↔ `"return".toList` |
| `inspect.signature(obj, type_aliases=A)` ∘ `typing.stringify` | `renderType A : SourceType → TypeStr` | the renderer applied to alias map `A`; a function value, passed in (free input) |

Lean `List Char` indexing is total and sound. The carrier for strings is
`List Char` because names/annotations/display strings are character sequences;
the recorded mapping is an ordered assoc list because the repo uses an
`OrderedDict` keyed by parameter name with `'return'` appended last.

## 3. Callee provenance — the renderer is a FREE INPUT (no axiom, no deep model)

**Callees:** `sphinx.util.inspect.signature` (`sphinx/util/inspect.py:471`,
post-patch invoked as `inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)`)
and `sphinx.util.typing.stringify` (`sphinx/util/typing.py:278`). Neither is
changed by the patch. `inspect.signature` forwards `type_aliases` into
`typing.get_type_hints(subject, None, type_aliases)` (`inspect.py:508`), which
resolves annotation names through the alias namespace; `typing.stringify` then
formats each resolved annotation into its display string.

These two unchanged callees are modeled together as the **free input**
`renderType : Aliases → SourceType → TypeStr`. The spec is **universally
quantified** over `renderType`, so it makes NO behavioural claim about it and
holds for EVERY renderer. Consequences:

- There is **no `axiom`** about the renderer and **no deep model** of it, so
  there is **nothing for G-AX to validate** (no `axiom_check.py` is shipped —
  `gates.gate_ax` returns `skip`). This is the safest possible treatment of an
  unchanged callee: weaker than an axiom, it cannot over-claim.
- The single behavioural fact the bundle pins is the one the patch changes:
  every recorded string is `renderType **aliases** …`, i.e. the renderer is
  applied to the **configured** alias map — not `renderType []`. The prepatch
  applies `renderType []` (the default empty map, `inspect.signature(obj)`) and
  consequently **fails** `out = recordedTypes (renderType aliases) … ` (G-DIFF),
  because for a configured alias `renderType aliases ≠ renderType []`.

Docs: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_type_aliases

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1)

`conformance_check.py` seeds its `random.Random` with **`8459`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the impl region's structural ops — iterate parameters in order, skip
unannotated, record `name → renderType aliases annot`, append the `'return'`
entry last — to Python, leaving the renderer as the **real** unchanged callees
`inspect.signature(obj, type_aliases=aliases)` + `typing.stringify` (the
free-input `renderType` applied to the configured `aliases`). The oracle is the
**patched** `record_typehints` run directly. They must agree on the recorded
ordered mapping for every fuzzed `(callable, alias map)` pair.
