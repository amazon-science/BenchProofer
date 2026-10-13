# mapping.md — sphinx-doc__sphinx-7910

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 27ac10de04697e2372d31db5548e56a7c6d9265d`, states the type
abstraction, and gives the provenance of the one consumed axiom.

Repo file under change: `sphinx/ext/napoleon/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `skip_decision(obj, is_special, is_init, is_private, inc_special, inc_init, inc_private)` | `_skip_member(app, what, name, obj, skip, options)` — `sphinx/ext/napoleon/__init__.py:381` (changed body line 441; class-owner branch lines 426-462) | the modeled changed function (autodoc `autodoc-skip-member` hook) for the documented class/exception member with a single-component class path |
| `canonical(obj)` *(axiom — A-consumed)* | `sphinx.util.inspect.unwrap` — `sphinx/util/inspect.py:121` (newly called at `__init__.py:441` post-patch), itself a thin wrapper over CPython stdlib `inspect.unwrap` (`Lib/inspect.py`) | the unchanged library primitive the patch switches the `__globals__` source to: recovers the ORIGINAL function from a decorator wrapper |
| `MemberObj.has_doc` | `getattr(obj, '__doc__', False)` (`__init__.py:424`) truthiness | whether the member is documented |
| `MemberObj.cls_name` | the single-component `cls_path` from `obj.__qualname__.rpartition('.')` (`__init__.py:429-430`) | the owning class-name token (qualified-name class component) |
| `MemberObj.ns` | the member object's `__globals__` mapping consulted at `__init__.py:441` (`cls = <chosen>.__globals__[cls_path]` then `name in cls.__dict__`) | the namespace through which the owning class is resolved; for `MemberObj.ns[cls_name]` see §2 (the `cls_is_owner` collapse) |
| `MemberObj.is_class_member` | ground truth of `cls and hasattr(cls, name) and name in cls.__dict__` (`__init__.py:445-446`) for the canonical (unwrapped) object | whether the member is genuinely its class's own member |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view): `cls = obj.__globals__[cls_path]`
(`__init__.py:441`), where `obj` is the possibly-wrapped member object.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the member object `obj` (a function / bound method, possibly decorator-wrapped) | `MemberObj` (a minimal class with only the touched fields) | `obj.__doc__` truthiness ↔ `has_doc`; the qualname class component ↔ `cls_name` (opaque `int` token); `obj.__globals__` ownership resolution ↔ `ns`; ground-truth membership ↔ `is_class_member` |
| the class object resolved by `cls = <ns>[cls_path]` and the subsequent `name in cls.__dict__` test | collapsed into one `bool` recorded at `ns[cls_name]` | the repository evaluates `cls_is_owner = (cls_path in <globals>) and hasattr(cls, name) and (name in cls.__dict__)`. The two sub-conditions (class resolvable in the namespace; member among the class's own attributes) are observed only through their conjunction `cls_is_owner`, so the model records, at the class-name key, the single boolean "the class resolved here owns this member". `cls_name in ns` ↔ `cls_path in <globals>` (class name resolvable); `ns[cls_name]` ↔ `name in cls.__dict__` (member owned). Absent key ↔ `KeyError` → `cls_is_owner=False`. |
| the class-name tokens / member identity | opaque `int` | only WHICH class is resolved and whether the lookup succeeds is observed; integer identity is faithful (no string indexing, banned by Nagini) |
| `what == 'class' or 'exception'`, `name != '__weakref__'`, and the dotted-`cls_path` `importlib` branch | the modeled single-component, documented class/exception member | the F2P/P2P tests exercise only single-component class paths (`SampleClass.__decorated_func__`, `SampleClass.__special_doc__`, …) where the changed line `cls = <chosen>.__globals__[cls_path]` is reached; the dotted branch (`functools.reduce(getattr, …)`) is unchanged by the patch and not on the tested path |
| `app.config.napoleon_include_{special,init,private}_with_doc` | `inc_special` / `inc_init` / `inc_private` booleans | direct |
| the kind classification `is_init` / `is_special` / `is_private` (`__init__.py:451-455`) | `is_init` / `is_special` / `is_private` booleans, mutually exclusive (precondition) | `is_init = name=='__init__'`; `is_special` and `is_private` are defined `not is_init and …`, so the three are mutually exclusive — encoded as a precondition |

The modeled `Result()` carrier is `Optional[bool]` over `{False, None}` —
exactly the repository return values on this branch (`return False` to include;
fall through to `return None` to abstain). The repository never returns `True`
on the documented-member branch, so `True` is outside the modeled codomain.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `canonical` ↔ `sphinx.util.inspect.unwrap` (A-consumed)
**Callee:** `sphinx.util.inspect.unwrap(obj)` (`sphinx/util/inspect.py:121`):

```python
def unwrap(obj):
    """Get an original object from wrapped object (wrapped functions)."""
    try:
        return inspect.unwrap(obj)
    except ValueError:
        # might be a mock object
        return obj
```

It delegates to CPython stdlib `inspect.unwrap(func)`, which follows the
`__wrapped__` chain (the attribute `functools.wraps` sets on a wrapper) to the
end and returns the innermost original object; on an object with no
`__wrapped__` it returns the object unchanged. The only divergence of the
repo wrapper from the stdlib function is catching `ValueError` (raised by
`inspect.unwrap` only on a `__wrapped__` cycle, e.g. a mock) and returning
`obj` — still the identity, consistent with the axiom's identity-on-unwrapped
clause. Docs: https://docs.python.org/3/library/inspect.html#inspect.unwrap.

The axiom `canonical` encodes only the obligations the changed line relies on:

  * `canonical(obj)` is non-None and preserves the inclusion-relevant identity
    of `obj` — `has_doc`, `cls_name`, `is_class_member` — because
    `functools.wraps` copies `__doc__`, `__qualname__` (hence the `cls_path`
    class component), `__module__` and `__name__` onto the wrapper, so
    unwrapping changes none of them;
  * the recovered object's namespace (`Result().ns`) records the GROUND-TRUTH
    ownership: `obj.cls_name in Result().ns and Result().ns[obj.cls_name]`
    holds exactly when `obj.is_class_member`. This is the substantive clause:
    the ORIGINAL function's `__globals__` is the module in which the function —
    and therefore its owning class — is genuinely defined, so resolving the
    class there and testing `name in cls.__dict__` reproduces true ownership.
    A decorator-wrapped object's OWN `__globals__` is the decorator module's
    and need not contain the class — which is precisely the defect the patch
    repairs by switching the `__globals__` source to `unwrap(obj)`.

This is the **weakest** contract the proof consumes (it says nothing about the
full unwrap algorithm, partials, classmethods, or the `ValueError` path).

**Soundness check (G-AX):** `axiom_check.py` builds, in a real Python
interpreter, the test's scenario — a method decorated by `functools.wraps`
whose decorator lives in a DIFFERENT module than the owning class (so the
wrapper's `__globals__` lacks the class) — for documented special / init /
private members, on classes and `Exception` subclasses, plus undecorated
controls and a multi-decorator chain. For each it runs the real
`inspect.unwrap` and asserts: (a) qualname/doc are preserved across unwrap;
(b) the wrapper's `__globals__` does NOT contain the class while the unwrapped
original's `__globals__` DOES (the discriminator); (c) the recovered
`cls_path in globals and name in cls.__dict__` equals true ownership. It also
asserts the full `_skip_member` ground truth — that the patched namespace
choice returns `False` (include) where the pre-patch returns `None` (skip) on
the decorated documented member. Imports only the standard library
(`functools`, `inspect`, `types`). Exit 0 iff every obligation holds.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg: the impl region of
`model.py` vs the REAL patched repo function. Recorded here for reproducibility.

* **Shadow** — `MemberObj` + the `# impl-start`/`# impl-end` region copied
  VERBATIM, with only the contract calls (`Requires`/`Ensures`/`Assert`)
  deleted; nothing restructured or renamed. The `# pure-start` region is empty,
  so there is no `@Pure` helper to copy, and the model carries no sequences, so
  no `PSeq`/`ToSeq` shim is needed. Provenance `direct`.
* **`canonical` (the one `@ContractOnly` callee)** — not re-implemented: the
  shadow calls the REAL callee it axiomatizes, `sphinx.util.inspect.unwrap`
  (§1 / §3.1), on the real member object behind the abstract `MemberObj`, and
  re-abstracts the result through the same bridge. The axiom's own obligations
  (non-None; `has_doc`/`cls_name` preserved; `Result().ns` records ground-truth
  ownership) are asserted on every input, so a violation fails the gate rather
  than being assumed.
* **Oracle** — the real patched `sphinx.ext.napoleon._skip_member`
  (`sphinx/ext/napoleon/__init__.py:381`, changed body line 441), **called**,
  not transliterated. The gate applies `patch.diff` to /testbed first and
  `PYTHONPATH=/testbed` makes the patched module importable. The modeled branch
  reads only `app.config.napoleon_include_{init,special,private}_with_doc` and
  never touches `skip`/`options`, so a two-attribute config stub plus a real
  function object drives it — no Sphinx application is required (this is why the
  velvet sibling's transliteration argument does not apply here).
* **Type bridge (§2, inverted)** — inputs are generated as REAL member objects
  (a function with controlled `__qualname__`/`__doc__` defined in a controlled
  module-globals dict, optionally wrapped by cross-module `functools.wraps`
  decorators) and abstracted to the carrier: `has_doc <- bool(getattr(obj,
  '__doc__', False))`; `cls_name <- ` interned int token of
  `obj.__qualname__.rpartition('.')`; `ns <- {token(k): bool(v and hasattr(v,
  name) and name in v.__dict__)}` over `obj.__globals__` (absent key == the
  repo's `KeyError` -> `cls_is_owner=False`); `is_class_member <- ` the same
  expression on the CANONICAL (unwrapped) object's globals, per §1. The
  `is_special`/`is_init`/`is_private` flags come from the repository's own
  classification (§2 row 6), which makes the mutual-exclusion `Requires` hold by
  construction. Result bridge: model `False` <-> real `False` (include), model
  `None` <-> real `None` (abstain), compared identity-sensitively. A binding on
  which the repo's ownership expression would RAISE has no `Dict[int, bool]`
  preimage; such an input is reported (`bridge-undefined`), never dropped.
* **Input domain** — the permission conjuncts are vacuous at runtime; the only
  real `Requires` is the kind mutual exclusion, satisfied by the bridge.
  Generation stays inside §2's declared modeled scope: `what in {'class',
  'exception'}`, `name != '__weakref__'`, single-component (dotless)
  `cls_path` — the restrictions §2 already declares, not a domain narrowed to
  route around a disagreement. Inside that scope everything is generated:
  undocumented members, unresolvable classes, inherited-not-owned members,
  intrinsic `__dict__` names, a falsy class (the repo's `cls and` conjunct), a
  non-class binding, and a same-name shadowing class.
* **Inputs / seed** — 32256-case exhaustive boundary catalogue (2 class names x
  16 member names x 3 doc values x 3 decoration depths x 7 ownership shapes x 2
  `what` values x 8 config settings) then seeded fuzz to **100000** total
  comparisons. **Pinned seed: `SEED = 79100`.**
* **Anti-vacuity** — the run counts inputs on which the pre-patch namespace
  choice (`obj.ns`) would disagree with the patched result and FAILS if that
  count is zero, so a generator that drifted off the branch the gold patch
  changed cannot report a green vacuous pass. Recorded run: 2583 of 100000
  inputs discriminate.
* **Negative controls (capability to fail, checked out-of-band under /tmp)** —
  (a) shadow vs a PRE-patch oracle (`cls = obj.__globals__[cls_path]`): exits 1
  on the F2P shape (decorated documented `__init__`, `inc_init=True`), shadow
  `False` vs oracle `None`; (b) shadow mutated to read `obj.ns` instead of
  `canon.ns` vs the patched oracle: exits 1 on the same input in the opposite
  direction. Recorded gate verdict on the unmutated pair: `G-CONF=pass`.
