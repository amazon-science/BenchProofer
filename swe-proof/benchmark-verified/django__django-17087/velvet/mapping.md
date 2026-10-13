# mapping.md — django__django-17087

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 4a72da71001f154ea60906a2f74898d32b7322a7`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms and no A-references** in this bundle —
see §3.

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildReference (module clsChain memberName)` | the bound-class-member branch of `FunctionTypeSerializer.serialize` — `django/db/migrations/serializer.py:166-173` (the `if getattr(self.value, "__self__", …) and isinstance(self.value.__self__, type):` body) | the modeled changed computation |
| `referencePath (module clsChain memberName)` | the post-patch dotted reference `"%s.%s.%s" % (module, klass.__qualname__, self.value.__name__)` — `django/db/migrations/serializer.py:171` post-patch | pure spec: the dotted reference string, as a list of components |
| `module` (the `module : String` parameter) | `klass.__module__` where `klass = self.value.__self__` — `serializer.py:169-170` | the defining module's dotted path |
| `clsChain` (the `clsChain : List String` parameter) | the components of `klass.__qualname__` (post-patch) — the ordered chain of enclosing qualifier names of `klass`, outermost first; `serializer.py:171` post-patch | the enclosing-qualifier chain of the bound member's owning class |
| `memberName` (the `memberName : String` parameter) | `self.value.__name__` — the bound member's own name — `serializer.py:171` | the final reference component |

The modeled function is `FunctionTypeSerializer.serialize`; the ONLY behavior the
gold patch changes is how the owning class is named in this one branch (which
class-name attribute supplies the middle component of the `"%s.%s.%s"`
reference). The surrounding dispatch (`serializer_factory`, the `__self__`/`type`
guard, the returned `{"import %s" % module}` set) is unchanged and surrounds the
modeled expression. The spec isolates the changed reference assembly. G-CONF (§4)
drives the WHOLE real `serializer_factory(...).serialize()` end-to-end on a real
bound class method of a nested class, so the modeled assembly is exercised inside
its true caller.

The pre-patch repo code the change replaces (refinement audit only): the middle
component was taken from the owning class's bare innermost name
(`klass.__name__`) instead of its full enclosing-qualifier chain
(`klass.__qualname__`) — `serializer.py:171` pre-patch.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the module path `klass.__module__` (a `str`) | `String` (`module`) | identity on strings |
| the owning class's enclosing-qualifier chain — `klass.__qualname__` split on `.` (a non-empty list of `str`) | `List String` (`clsChain`, `require clsChain ≠ []`) | a dotted qualname `"A.B.C"` ↔ the component list `["A","B","C"]`; a non-nested class has a single-element chain. `__qualname__` of a class reachable as `Field.default` contains no `<locals>`, so the split is a clean component list. |
| the bound member's own name `self.value.__name__` (a `str`) | `String` (`memberName`) | identity on strings |
| the produced dotted reference `"%s.%s.%s" % (...)` (a `str`) | `List String` (`out`) | the component list ↔ the `.`-joined dotted string: `out` joined on `.` is the emitted reference (G-CONF bridges via `".".join(out)`). |

Modeling the reference as a `List String` of components (rather than a single
fused `String`) is faithful and *stronger*: it lets the postconditions assert the
full enclosing chain `clsChain` appears in order between `module` and
`memberName` (length `clsChain.length + 2`), which is exactly the property the
fix establishes — the `.`-join is an order-preserving injection on these
dotted-identifier components, so equality of component lists ⇔ equality of the
emitted dotted strings (no component itself contains a `.`).

## 3. Callees / axioms / references — none

- **No consumed axioms.** The changed branch calls no repo/stdlib function whose
  contract the proof must assume. `klass.__module__`, `klass.__qualname__` and
  `self.value.__name__` are attribute *reads* off the value being serialized —
  plain data already in hand, modeled as the free inputs `module`, `clsChain`,
  `memberName`. The spec assumes only `clsChain ≠ []` (a class always has at
  least its own name in its qualname), so the contract holds for every owning
  class — no over-claim (SPEC_GUIDE §0.7/§0.8).
- **No A-references.** The changed assembly is modeled deeply by
  `referencePath`; there is no deep model standing in for a separate unchanged
  callee. Its fidelity to the real patched behavior is checked by **G-CONF**
  end-to-end against `FunctionTypeSerializer.serialize`, not by G-AX.
- Consequently this bundle ships **no `axiom_check.py`**; G-AX is `skip`
  (gates.py `gate_ax`: "no axiom_check.py" → skip).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`17087`** so the
consumer-side verdict is reproducible. It builds a REAL bound class method whose
owning class is nested an arbitrary, controlled number of levels deep inside a
synthetic module (the innermost class's `__qualname__` is the full chain, its
`__name__` the innermost name), feeds it to the real
`serializer_factory(...).serialize()` (gold applied by the harness), and compares
the emitted dotted reference string against the R/I shadow of `buildReference`
(`".".join([module] + clsChain + [memberName])`). Nesting depth is fuzzed over
`1..5` so both the single-qualifier case (where the pre-patch already agreed) and
the genuinely-nested cases (the bug) are exercised. Boundary cases (the gold F2P
shape `migrations.test_writer.WriterTests.NestedChoices.method`, the depth-1
`appname.models.Capability.default` from the report, and member/class-name
collisions) are checked first.
