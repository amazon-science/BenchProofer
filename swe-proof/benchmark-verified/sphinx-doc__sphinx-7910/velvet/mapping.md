# mapping.md — sphinx-doc__sphinx-7910

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 27ac10de04697e2372d31db5548e56a7c6d9265d`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the (here: empty) axiom set.

Repo file under change: `sphinx/ext/napoleon/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `inclusionDecisionM (ctx, name, target, incInit, incSpecial, incPrivate)` | `_skip_member(app, what, name, obj, skip, options)` — `sphinx/ext/napoleon/__init__.py:381` (decision body 421-462) | the modeled changed function (member-inclusion decision) |
| `Context` | the `what` string argument (`"class"`/`"exception"`/`"module"`/other) and the `is_member` test (`__init__.py:422`) | the context a target appears in |
| `Decision.forceInclude` / `Decision.noOverride` | `_skip_member`'s return values `False` / `None` (`__init__.py:462,463`) | force inclusion vs leave the default |
| `DocTarget.hasDoc` | `getattr(obj, '__doc__', False)` (`__init__.py:421`) | target carries documentation text |
| `DocTarget.qualifiedName` | `getattr(obj, '__qualname__', '')` (`__init__.py:429`) | the target's fully-qualified name |
| `DocTarget.ownerViaPathWalk` | the multi-segment branch result: `functools.reduce(getattr, cls_path.split('.'), mod)` then `hasattr(cls, name) and name in cls.__dict__` (`__init__.py:433-439,445-446`) | for a dotted container path, whether the attribute-chain walk yields an owner |
| `DocTarget.resolvedScope` | `inspect.unwrap(obj).__globals__` (post-patch `__init__.py:441`) | the namespace of the object the target stands for, once any wrapper is seen through — the scope the FIX consults |
| `DocTarget.directScope` | `obj.__globals__` (pre-patch `__init__.py:441`) | the target's OWN namespace — the scope the BUG consults (prepatch only) |
| `containerPath` | `qualname.rpartition('.')[0]` (`__init__.py:430`) | container path = before the last '.' |
| `isMultiSegment` | `'.' in cls_path` (`__init__.py:433`) | dotted (multi-segment) container path |
| `scopeOwns scope key` | `scope[key]` lookup + `cls and hasattr(cls, name) and name in cls.__dict__` (`__init__.py:441,445-446`); `KeyError` ⇒ `except` ⇒ `False` | whether looking the container up in a scope yields an owner of the leaf |
| `categoryEnabled` | the init/special/private classification gated by `inc_init`/`inc_special`/`inc_private` (`__init__.py:451-462`) | enabled inclusion category for the leaf |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `obj.__globals__[cls_path]` (`__init__.py:441` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `what : str` ∈ {"class","exception","module", …} | `Context` (`classBody`/`exceptionBody`/`wholeUnit`/`freestanding`) | `"class"↔classBody`, `"exception"↔exceptionBody`, `"module"↔wholeUnit`, anything else ↔ `freestanding`; `is_member ↔ isConsidered ctx` |
| `name : str` (leaf member name) | `List Char` | `s ↔ s.toList`; `startswith/endswith` ↔ `isPrefixOf/isSuffixOf` on `List Char`; `== "__init__"` ↔ `== "__init__".toList` |
| `_skip_member` return (`False`/`None`) | `Decision` | `False ↔ forceInclude`, `None ↔ noOverride`. (`_skip_member` never returns `True` on this path.) |
| `getattr(obj,'__doc__',False)` truthiness | `Bool` (`hasDoc`) | a target with non-empty `__doc__` ↔ `hasDoc = true` |
| `obj.__qualname__` | `List Char` (`qualifiedName`) | `qn ↔ qn.toList`; `rpartition('.')[0]` ↔ `containerPath` |
| `obj.__globals__[cls_path]` resolving to an owning class | `Bool` entry in a scope `List (List Char × Bool)` | a successful lookup that satisfies `cls and hasattr(cls,name) and name in cls.__dict__` ↔ `(cls_path, true)` present in the scope; `KeyError`/non-owner ↔ absent or `(cls_path, false)`. Each scope is the namespace folded to the one boolean the branch reads. |
| `inspect.unwrap(obj)` then its `__globals__` | `resolvedScope` | unwrapping the decorator chain (`functools.wraps` sets `__wrapped__`) so the lookup hits the namespace where the leaf is genuinely defined. For an UNwrapped target, `inspect.unwrap(obj) is obj`, so `resolvedScope == directScope`. |
| multi-segment walk `functools.reduce(getattr, …)` + ownership | `Bool` (`ownerViaPathWalk`) | the change does NOT touch the dotted-path branch; its owner result is recorded as one boolean. |

`name`/`qualifiedName` are per-character so the carrier is `List Char`; Lean
`List Char` indexing/prefix tests are total and sound.

## 3. Callee provenance — none consumed (kind-A is empty)

There is **no axiom** and **no A-reference deep model of an external callee** in
this bundle (`axioms`/`deep_model_references` empty in meta.json). The operation
the gold patch changes is the *namespace consulted* by the owner-class lookup:

```
- cls = obj.__globals__[cls_path]
+ cls = inspect.unwrap(obj).__globals__[cls_path]
```

`inspect.unwrap(obj)` (a thin wrapper over `functools`/`inspect`’s
`__wrapped__`-chain follower; sphinx’s `sphinx.util.inspect.unwrap` just calls
`inspect.unwrap` and returns `obj` on a `ValueError`) walks a decorated object
back to the object it wraps. With `functools.wraps`, the wrapper copies
`__doc__`/`__qualname__` but its `__globals__` is the *decorator module's*
globals — which does NOT contain the owning class — so the pre-patch lookup
`KeyError`s and ownership wrongly fails. The fix consults the *unwrapped*
object's globals, where the class lives.

This is modeled **deeply and structurally**: the wrapper-vs-underlying
distinction is the `directScope` vs `resolvedScope` fields, and the lookup is
`scopeOwns`/`ownerIn`. There is nothing to validate against a real callee
(unwrapping is unchanged machinery folded into the recorded scopes), so G-AX is a
documented **skip** (axiom_check.py). The structural correctness of the branch —
including that the post-patch flow reads `resolvedScope` — is refuted by G-CONF
(`conformance_check.py`), whose ORACLE transliterates the patched
`_skip_member` ownership flow verbatim. mapping.md §2.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7910`** so the
consumer-side verdict (§11.3) is reproducible. The SHADOW transliterates
`inclusionDecision` and its helpers (all R/I-tagged ops); the ORACLE
transliterates the patched `_skip_member` ownership branch, reducing each target
to the recorded structural fields the branch inspects and reading ownership from
the resolved (unwrapped) scope (the patched behavior). No A-tagged callee is run,
because there is none.
