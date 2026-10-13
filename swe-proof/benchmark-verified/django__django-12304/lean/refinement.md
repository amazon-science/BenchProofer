# refinement.md — django__django-12304

Maps every operation in `implementation_buildChoicesClass` to its `patch.diff`
counterpart in `ChoicesMeta.__new__` (`django/db/models/enums.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (gold, post-patch tail of `__new__`)
```python
        cls.label = property(lambda self: cls._value2label_map_.get(self.value))
+       cls.do_not_call_in_templates = True
        return enum.unique(cls)
```
The patch adds a single statement: the constructed class is marked with
`do_not_call_in_templates = True`. The value→label association
(`cls._value2label_map_`, built earlier in `__new__` from the members) is
untouched.

The modeled value is the constructed class restricted to its two touched
observables (mapping.md): the value→label association it exposes, and whether it
carries the "do not invoke in templates" flag.

## Operation correspondence
| # | Lean op (`implementation_buildChoicesClass`) | patch.diff / base op | tag | note |
|---|---|---|---|---|
| 1 | `let mut cls := { value2label := memberValues, doNotCallInTemplates := false }` | the class object under construction (`cls = super().__new__(...)`), before the flag is set | I | accumulator starts at the constructed class with the flag absent (`getattr(..., False)` default). |
| 2 | `cls := { cls with value2label := memberValues }` | `cls._value2label_map_ = dict(zip(cls._value2member_map_, labels))` (`enums.py:29`, pre-existing) | R/I | the value→label association is the members' `(value, label)` entries carried through. `dict(zip(...))` (value→label map, member-definition order) ↔ `List (Int × String)`; this op is UNCHANGED by the patch and is the frame-pinned component. |
| 3 | `cls := { cls with doNotCallInTemplates := true }` | `cls.do_not_call_in_templates = True` (`enums.py:34` post, the ADDED line) | I | set the "do not invoke" flag to the literal `True`. This is the fix. |
| 4 | `return cls` | `return enum.unique(cls)` | I | return the constructed class (the `enum.unique` wrapper is identity on the modeled observables — it only de-dups aliases, leaving `_value2label_map_` and the new attribute intact). |

`templateWouldCall isCallable doNotCall altersData = isCallable && !doNotCall && !altersData`
is the EXACT engine decision `callable(current) and not
do_not_call_in_templates and not alters_data` from `Variable._resolve_lookup`
(`django/template/base.py:851-856`); it is modeled deeply (a boolean over the
three observables the engine reads), not axiomatized. It appears only in the
spec, fixing the post-condition's meaning; the impl produces the flag the
decision consumes.

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — the members enter as data, the flag is a literal, the
engine decision is modeled deeply). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow (the constructed class's two observables, fed through the engine
decision `templateWouldCall`) against the patched behavior over ≥10^5 fuzzed
inputs. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `__new__` never sets `do_not_call_in_templates`, so the constructed
class lacks the flag (`getattr(cls, 'do_not_call_in_templates', False)` is
`False`). The prepatch impl (`implementation_buildChoicesClass` leaves
`doNotCallInTemplates := false`) is exactly this. The template engine then takes
the `else` arm and invokes the (callable) class with no arguments — which raises,
so the lookup that the template wanted (a member and then its `.label` / `.value`)
fails. The prepatch impl violates the discriminating clause
`templateWouldCall true result.doNotCallInTemplates false = false`: with the flag
`false` it reduces to `true = false`, unprovable — precisely the FAIL_TO_PASS
`test_templates` (`{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}` must render
`Diamond|1`, which requires the engine to NOT call `Suit`). The carried gold
proof body (`simp` on the discriminating clause) fails to typecheck against the
buggy impl (G-DIFF). The value→label frame clause still holds for the prepatch,
so the ONLY failing clause is the flag clause — exactly the modeled fix.

## patch.diff == gold
`patch.diff` is the gold patch verbatim (single added line); applies clean at
`base_commit` and resolves (G-RESOLVE/G-GOLD).
