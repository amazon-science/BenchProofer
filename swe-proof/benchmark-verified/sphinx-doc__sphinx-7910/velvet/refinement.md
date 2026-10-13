# refinement.md — sphinx-doc__sphinx-7910

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `inclusionDecisionM` `do` block and the deep `inclusionDecision` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — **A-consumed** / **A-reference**), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The owner-lookup site — `_skip_member` (`sphinx/ext/napoleon/__init__.py:441`)

Gold hunk:
```
- cls = obj.__globals__[cls_path]
+ cls = inspect.unwrap(obj).__globals__[cls_path]
```

| # | Solution.lean impl op (`inclusionDecisionM`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `ctx : Context`, `name : List Char`, flags | `what`, `name`, `inc_*` args of `_skip_member` | R | `what:str ↔ Context`, `name:str ↔ List Char`, flags ↔ `Bool` (mapping.md §2). |
| A2 | `(name != "__weakref__".toList) && target.hasDoc && isConsidered ctx` | `name != '__weakref__' and has_doc and is_member` (`:421-422`) | I + R | guard transliterated; `has_doc ↔ DocTarget.hasDoc`, `is_member ↔ isConsidered`. |
| A3 | `match ctx … => ownerIn target target.resolvedScope` | `if what=='class'/'exception': … cls = inspect.unwrap(obj).__globals__[cls_path]; cls_is_owner = (cls and hasattr… and name in cls.__dict__)` (`:428-446`, post-patch) | I + R | the ownership computation. The CHANGED operation — the namespace consulted — is the choice of `resolvedScope` (the unwrapped object's globals) over `directScope`; modeled deeply via `ownerIn`/`scopeOwns` reading `resolvedScope`. mapping.md §3. The dotted-path branch (`isMultiSegment ⇒ ownerViaPathWalk`) is unchanged. |
| A4 | `containerPath` / `isMultiSegment` / `scopeOwns` | `qualname.rpartition('.')[0]`, `'.' in cls_path`, the `__globals__[cls_path]` lookup folded to a scope membership (`KeyError ⇒ except ⇒ False`) | I + R | string/dict ops transliterated; `str ↔ List Char`, dict lookup ↔ scope membership boolean (mapping.md §2). |
| A5 | `if (ctx == wholeUnit) ∨ owner then …` | `if what=='module' or cls_is_owner:` (`:450`) | I + R | the ownership gate. |
| A6 | `categoryEnabled name … ⇒ forceInclude else noOverride` | the init/special/private classification and `return False`, else fall through to `return None` (`:451-463`) | I + R | leaf classification transliterated; `False ↔ forceInclude`, `None ↔ noOverride`. |

Discriminating content of the change — ownership for a wrapped target is decided
in the namespace of the object it stands for (`resolvedScope`), not the wrapper's
own namespace (`directScope`) — lives in step A3: the spec's `ownerIn target
target.resolvedScope`. The pre-patch code read `obj.__globals__` (the wrapper's
namespace, which lacks the owning class), so ownership wrongly failed for a
decorated member; `Solution_prepatch.lean` reproduces that (impl reads
`directScope`) and **fails** `out = inclusionDecision …` (G-DIFF), exactly on the
ownership clause.

## B. No axioms, no A-reference

There is no consumed axiom and no A-reference deep model of an external callee.
`inspect.unwrap`'s decorator-chain unwrapping is *unchanged* machinery: it is not
the operation under change (the patch swaps WHICH object's `__globals__` is
read), and its effect is folded into the `directScope` vs `resolvedScope`
distinction the model carries explicitly. Hence G-AX is a documented skip
(axiom_check.py); the branch's structural correctness — including that the patched
flow reads the resolved scope — is refuted by G-CONF over 117 920 cases.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the namespace
the owner-class lookup consults — is modeled **deeply and concretely** (the
`directScope`/`resolvedScope` fields and `ownerIn`/`scopeOwns`), not hidden behind
an axiom about the function under change. There is no consumed axiom at all.

## D. verify(Solution) ⇒ resolved

`inclusionDecisionM` verifies only if its verdict equals `inclusionDecision`,
which decides ownership against the **resolved** (unwrapped) scope (A3) and forces
inclusion exactly when an enabled category matches (A6). By R (`what ↔ Context`,
`str ↔ List Char`, `False/None ↔ forceInclude/noOverride`, dict-lookup ↔ scope
membership) the verified decision equals the patched `_skip_member` on the tested
inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on
≥10⁵ inputs (seed=7910). The F2P case `test_class_decorated_doc` — a
`functools.wraps`-decorated `__special_doc__`-style member that must be included —
is the wrapped-target case where `resolvedScope` owns but `directScope` does not;
the spec demands `forceInclude` there, and only the post-patch (`resolvedScope`)
impl satisfies it. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement, and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point (G-AX vacuous).
