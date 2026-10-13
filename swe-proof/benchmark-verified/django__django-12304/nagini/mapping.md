# mapping.md — django__django-12304

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4c1b401e8250f9f520b3c7dc369554477ce8b15a`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/models/enums.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_template_usable_grouping(identity)` | `ChoicesMeta.__new__(metacls, classname, bases, classdict)` — `django/db/models/enums.py:11` (the assignment site at body line 34, between `cls.label = property(...)` at line 33 and `return enum.unique(cls)` at line 34 @ base_commit; the patch makes the assignment line 34 and pushes `return enum.unique(cls)` to line 35) | the modeled changed function: the metaclass that builds the enumeration grouping class object and flags it so it is preserved (not invoked) during template variable resolution |
| `base_class_creation(identity)` *(axiom — A-consumed)* | the base construction step: `super().__new__(metacls, classname, bases, classdict)` — `enum.EnumMeta.__new__`, invoked at `django/db/models/enums.py:28` — together with the derived per-choice tables the same step records, `cls._value2label_map_` (line 29) and the `label` property (line 33); i.e. `enums.py:28-33`, everything the modeled function does BEFORE recording the flag | unchanged base callee that creates the enumeration class object, binds the declared choices under their own names and records the derived tables. TOTAL: it either delivers the object (issuing the provenance token) or REFUSES the declaration and reports `BaseStepRefused`, and it refuses exactly the declarations `base_step_refuses` holds of. The axiom pins the identity and leaves the initial preserve-when-callable flag UNCONSTRAINED (a class with no flagged ancestor carries none — falsy; a class built under an already-flagged base INHERITS it — truthy). It does NOT include the value-distinctness step: that is a separate axiom, reached AFTER the flag is recorded |
| `finalize_grouping(grouping, identity)` *(axiom — A-consumed)* | the value-distinctness step `enum.unique(cls)` — `django/db/models/enums.py:35` (line 34 @ base_commit), the step whose result the modeled function returns | unchanged callee the construction hands the already-flagged grouping to at the very END. TOTAL: it hands back THE SAME object with both modeled facts untouched (`enum.unique(cls) is cls`), passing the provenance token along, or REFUSES with `RepeatedChoiceValue` (`ValueError('duplicate values found in …')`) for exactly the declarations `repeats_choice_value` holds of |
| `base_step_refuses(identity)` *(axiom — @Pure @ContractOnly, opaque)* | the refusals `enums.py:28-33` itself makes: `enum.EnumMeta.__new__` refusing a declared kind that cannot carry the declared choice values (`TypeError: type 'bool' is not an acceptable base type`, `enums.py:28`), and the assignments at lines 29/33 refusing a choice declared under the name of a table this step must itself bind (`label`, `_value2label_map_` → `AttributeError('Cannot reassign members.')` from `enum.EnumMeta.__setattr__`) | decidable property of the DECLARATION (its declared kind and its choice names), settled before the construction starts. Opaque in the model: both outcomes are realizable and neither is assumed, so the only way a body can learn the step did not refuse is to have RUN it |
| `flag_name_taken_by_choice(identity)` *(axiom — @Pure @ContractOnly, opaque)* | the table the guard on `enums.py:34` consults: `enum.EnumMeta.__setattr__` refuses `cls.do_not_call_in_templates = True` with `AttributeError('Cannot reassign members.')` iff `'do_not_call_in_templates' in cls.__dict__['_member_map_']` — i.e. iff one of the grouping's own declared choices occupies that name (CPython `Lib/enum.py`, `EnumMeta.__setattr__`) | decidable property of the DECLARATION (its choice names). Recording the flag is a GUARDED binding, not a bare field write; this is what makes the second outcome of the case split real rather than hypothetical |
| `repeats_choice_value(identity)` *(axiom — @Pure @ContractOnly, opaque)* | the table `enum.unique(cls)` consults at `enums.py:35`: it raises `ValueError('duplicate values found in <enum 'X'>: B -> A')` iff two declared choices share a value (CPython `Lib/enum.py`, `unique`) | decidable property of the DECLARATION (its choice values). Independent of the two predicates above — all four combinations are realizable (measured; §3.3) — so no clause of the spec may be discharged by assuming one settles another |
| `resolved_in_template(grouping)` *(axiom — A-consumed)* | `django.template.base.Variable._resolve_lookup` — `django/template/base.py:816`, specifically the callable-handling step `if callable(current): if getattr(current, 'do_not_call_in_templates', False): pass …` at `django/template/base.py:851-866` | unchanged template variable-resolution rule; specialised to a callable object whose no-argument invocation cannot succeed |
| `EnumGrouping` | the enumeration class object produced by `ChoicesMeta.__new__` (a `Choices`/`IntegerChoices`/`TextChoices` subclass) | minimal carrier of the two touched facts (object identity; the preserve-when-callable flag) |
| `INVALID_VALUE` (`== 0`) | `context.template.engine.string_if_invalid` (the substitute a template emits when a variable lookup fails) — `django/template/base.py:855,864` | the invalid-value sentinel; modeled as `0`, distinct from every (positive) grouping identity |
| `EnumGrouping.preserve_when_callable` | the `do_not_call_in_templates` attribute on the class object (`django/db/models/enums.py:34` after the change; absent / falsy before) | boolean flag read by `_resolve_lookup` at `django/template/base.py:852` |
| `declaration_available(identity)` *(axiom — opaque single-use `@Predicate`, no `Ensures`)* | the `classdict` (`enum._EnumDict`) the metaclass is called with — the declared-members record `ChoicesMeta.__new__` reads `classdict._member_names` off and hands to `super().__new__` (`django/db/models/enums.py:11,28`) | multiplicity carrier only: enum's classdict is SINGLE-USE (`super().__new__` consumes the member names; a second `super().__new__(metacls, classname, bases, classdict)` on the same classdict raises `KeyError` on the first member name). Consumed by `base_class_creation` and never returned, so the base construction step runs at most once per declaration |
| `built_from_declaration(grouping, identity)` *(axiom — opaque `@Predicate`, no body, no `Ensures`)* | the object identity of the class `super().__new__` returned at `django/db/models/enums.py:28` and that `enum.unique(cls)` hands back unchanged at line 35 (`enum.unique(cls) is cls`) | provenance carrier only: the token is ISSUED by `base_class_creation` for the object it produced and PASSED ALONG by `finalize_grouping` for the object it hands back. Body-less, so it cannot be `Fold`ed into existence — the only way to hold one is to have obtained it from one of those two steps. This is what makes "the grouping THIS construction produced" observable instead of collapsing to "any object that reports the requested identity" |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the enumeration class object (a `type`) produced by the metaclass | `EnumGrouping` instance | the model keeps only the two facts the behaviour reads: a distinguishing object identity and the preserve-when-callable boolean. The class object's identity (its `id()` / "is this the same object") ↔ `EnumGrouping.identity` (a positive int). |
| `cls.do_not_call_in_templates = True` (attribute set to the boolean literal `True`) | `grouping.preserve_when_callable = True` | identical boolean assignment; `getattr(cls, 'do_not_call_in_templates', False)` ↔ `grouping.preserve_when_callable` |
| `getattr(cls, 'do_not_call_in_templates', False)` right after `super().__new__` — `False` for a class with no flagged ancestor, but `True` (inherited) for a class built under an already-flagged base (e.g. `IntegerChoices`/`TextChoices`/user subclasses once the patched `ChoicesMeta` has flagged `Choices`) | `EnumGrouping.preserve_when_callable` UNCONSTRAINED (havoced) as built by `base_class_creation` | the real initial value varies with the ancestry, so the axiom does not pin it; a correct implementation must establish the flag unconditionally, exactly as the gold patch's unconditional `cls.do_not_call_in_templates = True` does |
| `string_if_invalid` (an empty string by default; the value a failed lookup yields, after which the chained `.DIAMOND.label` lookup also fails and the template renders nothing) | `INVALID_VALUE == 0` | "the resolution did not yield the object itself, so subsequent member access cannot proceed" ↔ `Result() == INVALID_VALUE`; a positive identity ↔ "the object itself is preserved and members resolve" |

The behaviour observed by the F2P test (`{{ Suit.DIAMOND.label }}` renders
`Diamond`) requires that resolving `Suit` (the grouping, a callable class) in a
template yields the grouping itself rather than `string_if_invalid`: only then
does the `.DIAMOND` member lookup, and in turn `.label`, succeed. That is
exactly `resolved_in_template(grouping) == grouping.identity` (≠ the invalid
sentinel).

## 2b. Total correctness, multiplicity, provenance, and the complete ORDERED case split (spec obligations added after the P2 / G-EQ audits)

Obligations on the modeled function that the earlier spec text lacked. Each is a
property of the REAL operation, and each is what separates the gold metaclass
from a same-spec wrong implementation the earlier spec admitted.

| obligation | model.py form | repo reality | what it rejects |
|---|---|---|---|
| **total correctness** | `Requires(MustTerminate(2))` on `build_template_usable_grouping`; measure 1 on `base_class_creation` and on `EnumGrouping.__init__` | `ChoicesMeta.__new__` (`django/db/models/enums.py:11`) is a bounded loop over `classdict._member_names` followed by straight-line work, and class creation must RETURN the class object to the `class` statement that triggered it. It never diverges. | a body that re-enters the construction (`return build_template_usable_grouping(identity)`) or loops forever. Nagini proves only PARTIAL correctness without this, so such a body discharges every `Ensures` from the self-call's own contract while no run reaches a return. Faithful patch: `return metacls.__new__(metacls, classname, bases, classdict)` → `RecursionError` on `class Suit(int, Choices)`, the enumeration cannot be declared, F2P cannot import. Measure 2 admits the measure-1 callees but forbids re-entering this construction, so Nagini reports `Obligation leak check failed`. |
| **one declaration ⇒ one grouping** | opaque `@ContractOnly @Predicate declaration_available(identity)` with NO body and NO `Ensures`; required by `build_template_usable_grouping` and CONSUMED (not returned) by `base_class_creation` | enum's `classdict` is single-use. `super().__new__` consumes `_member_names`; running it a second time on the same `classdict` raises `KeyError` on the first member name (reproduced: `KeyError: 'DIAMOND'`). And under §2's bijection `identity ↔ id(cls)` two distinct class objects cannot share an `id()`, so "two base constructions both returning `identity`" is unrealizable. | a body that runs the base step twice for one declaration, discards the first and returns the second. `Ensures` E1–E5 alone do NOT reject it (the second object reports the requested identity and carries the flag), because `identity` is a caller-chosen free int the axiom merely echoes. The single-use resource is what makes "the grouping THIS construction produced" observable in the spec. Faithful patch duplicates the `super().__new__` call → `KeyError 'DIAMOND'`, class creation fails outright. |
| **the grouping delivered is the one that was built** | opaque `@ContractOnly @Predicate built_from_declaration(grouping, identity)` with NO body and NO `Ensures`; ISSUED by `base_class_creation` for what it produced, required-and-re-issued by `finalize_grouping`, and required of `Result()` by the modeled function | `enum.unique(cls) is cls` (`enums.py:35`): the object the declaring `class` statement receives IS the object `super().__new__` produced at line 28, flag and all. Nothing in the real construction substitutes a different object. | a body that performs the entire gold construction and then returns a DIFFERENT, freshly-built grouping. Identity alone cannot reject it, because `identity` is a caller-chosen free int and a fabricated object can be given any identity value; the token can only be obtained from the two steps that issue it, and it is body-less so it cannot be `Fold`ed. Rejected as `weak-wrong-identity-obj` / `weak-echo-fabricate` (G-PBT). |
| **the case split is COMPLETE — no declaration is excluded** | NO precondition beyond `identity > 0` + the declaration resource; four mutually exclusive, exhaustive outcomes: `Ensures(not base_step_refuses ∧ not flag_name_taken_by_choice ∧ not repeats_choice_value ∧ …)` for delivery, plus three `Exsures` legs, each guarded by the conjunction of the *earlier* predicates' negations | every declaration reaches the real `ChoicesMeta.__new__`; each of the three steps refuses some of them and the construction reports the refusal of the earliest one. A repeated choice value in particular is refused only at `enums.py:35`, by a step the construction reaches NORMALLY, after the flag has already been recorded at line 34 — so it is squarely inside the behaviour, not outside it. | THE RECORDED HOLE. The earlier spec carried `Requires(base_step_can_bind_choices(identity))`, which excluded the duplicate-choice-value domain. `atk_2.py` verified against it (its negative branch was unreachable in the proof) yet its patch broke PASS_TO_PASS `test_invalid_definition`, which asserts `ValueError: duplicate values found in <enum 'Fruit'>: PINEAPPLE -> APPLE`. Making the three refusals OBSERVABLE (three opaque declaration predicates, propagated through the two step axioms' `Exsures`) rather than excluding them by precondition is what closes it. Rejected as `weak-wrong-report-on-repeat`, `weak-skip-distinctness`, `weak-swap-reports`, `partial-fixed-identity`, `weak-invent-base-refusal`, `weak-always-refuse`, `weak-inverted-refuse` (G-PBT). |
| **the refusals are ORDERED** | the `not flag_name_taken_by_choice(identity)` conjunct inside `Exsures(RepeatedChoiceValue, …)` (and the `not base_step_refuses(identity)` conjunct inside both later legs) | measured on the patched worktree: a declaration that BOTH names a choice `do_not_call_in_templates` AND repeats a choice value raises at `enums.py:34` (`AttributeError('Cannot reassign members.')`), not at line 35 — because the flag is recorded before the distinctness step runs; a declaration that both declares a bad kind and repeats a value raises at line 28. G-CONF classifies every oracle refusal by the `enums.py` line it escaped from, located in the patched file at run time, and the order `34 < 35` is asserted. | a body that runs the distinctness step BEFORE recording the flag. It performs exactly the same operations and satisfies every unordered clause, but on a both-conditions declaration it reports `RepeatedChoiceValue` where the real construction reports the taken-name refusal. Rejected as `weak-finalize-before-flag` (G-PBT) and caught as `distinctness-before-flag` (G-CONF). |

`declaration_available` and `built_from_declaration` are unforgeable tokens, not
behavioural claims: each has no body (so nothing can `Fold` one into existence)
and no `Ensures` (so neither asserts anything about a callee's result and neither
adds a G-AX soundness surface — there is no observable they could disagree with
the real callee about). The first constrains only HOW MANY TIMES the base
construction step may run, which is exactly what enum's single-use classdict
enforces at runtime; the second constrains only WHICH object may be delivered,
which is exactly what `enum.unique(cls) is cls` gives.

**None of these obligations narrows the input domain — the repair strictly WIDENS
it.** `identity > 0` is unchanged, the earlier
`Requires(base_step_can_bind_choices(identity))` has been REMOVED (so the
duplicate-value, taken-flag-name and bad-kind declarations that were previously
excluded are now specified), and every grouping shape admissible before is
admissible now. The added obligations are all `Ensures`/`Exsures` strength or
resource discipline, never precondition strength; G-PBT's `admiss-f2p-diamond`
lane re-confirms admissibility of the F2P shape, and G-CONF now exercises 100000
declarations of which the previously-excluded refusal shapes are a measured part.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `base_class_creation` ↔ the base construction step, `enums.py:28-33` (A-consumed)
**Callee:** `enum.EnumMeta.__new__` (CPython stdlib `Lib/enum.py`), invoked via
`super().__new__(metacls, classname, bases, classdict)` at
`django/db/models/enums.py:28`, TOGETHER WITH the derived per-choice tables the
same step records — `cls._value2label_map_ = dict(zip(cls._value2member_map_,
labels))` (line 29) and `cls.label = property(...)` (line 33). That is exactly
`enums.py:28-33`: everything the modeled function does BEFORE recording the flag.
The value-distinctness step at the end (`enum.unique(cls)`, line 35) is
deliberately **NOT** folded in here — it is a separate axiom (§3.4), because it
runs AFTER the flag is recorded and the difference is observable (§2b, the ORDER
row). This step is UNCHANGED by the patch. It creates the enumeration class
object. The axiom pins ONLY the identity of the produced
grouping and deliberately leaves the initial `preserve_when_callable` value
**unconstrained**: right after `super().__new__`, `getattr(cls,
'do_not_call_in_templates', False)` is `False` for a class with no flagged
ancestor (e.g. the abstract `Choices` base itself, or a plain `enum.Enum`),
but `True` (inherited through the MRO) for any class constructed under an
already-flagged base — which is exactly what happens for `IntegerChoices`,
`TextChoices`, and every user subclass once the patched `ChoicesMeta` has
flagged the `Choices` root. Because both initial states are realized by the
real callee, no sound contract may pin the initial flag; leaving it havoced
also forces a verifying implementation to establish the flag unconditionally
(the gold patch's unconditional assignment) rather than rely on — or invert —
its incoming value.

The axiom is **TOTAL** over declarations, exactly as the real step is: it either
delivers the object (issuing the provenance token) or reports `BaseStepRefused`,
and `Exsures(BaseStepRefused, base_step_refuses(identity))` + `Ensures(not
base_step_refuses(identity))` make those two legs two-sided, so a body cannot
invent a refusal for a declaration the step accepts nor deliver a grouping for
one it rejects. The refusals the real step makes, measured against the patched
worktree (`enums.py`):

* a declared kind that cannot carry the declared choice values —
  `class Suit(bool, enum.Enum)` → `TypeError: type 'bool' is not an acceptable
  base type`, raised inside `super().__new__` at **line 28**;
* a choice declared under the name of a table this step must itself bind
  (`label`, `_value2label_map_`) → `AttributeError('Cannot reassign members.')`
  from `enum.EnumMeta.__setattr__` at **line 29 / 33**;
* and it ACCEPTS a declaration that repeats a choice value — that one is refused
  only later, by §3.4's step. Measured: 272 accepted / 328 refused over the
  axiom_check shape table.

The axiom does not model the CONTENT of the member maps or labels (none are
observed by the modeled behaviour) and, deliberately, not value-distinctness.
Docs: https://docs.python.org/3/library/enum.html.

### 3.2 `resolved_in_template` ↔ `Variable._resolve_lookup` callable step (A-consumed)
**Callee:** `django.template.base.Variable._resolve_lookup`
(`django/template/base.py:816`), specifically the per-lookup callable-handling
step (`django/template/base.py:851-866`). This step is UNCHANGED by the patch
(it already branches on `do_not_call_in_templates`). Source at base_commit:

```python
if callable(current):
    if getattr(current, 'do_not_call_in_templates', False):
        pass
    elif getattr(current, 'alters_data', False):
        current = context.template.engine.string_if_invalid
    else:
        try:  # method call (assuming no args required)
            current = current()
        except TypeError:
            signature = inspect.signature(current)
            try:
                signature.bind()
            except TypeError:  # arguments *were* required
                current = context.template.engine.string_if_invalid
            else:
                raise
```

The axiom is **specialised to the grouping scenario**: `current` is a class
object (always `callable`), it does **not** set `alters_data`, and invoking it
with no arguments cannot succeed — constructing an enum member requires a
`value` argument, so `current()` raises `TypeError` and `signature.bind()` also
raises `TypeError` (arguments *were* required), driving the result to
`string_if_invalid`. Under that specialisation the rule reduces to:

  • if `do_not_call_in_templates` is truthy → the object is left as-is (the
    `pass` branch): resolution yields the object itself; ⇔
    `Result() == grouping.identity`.
  • otherwise → the no-argument call fails and the result is
    `string_if_invalid`; ⇔ `Result() == INVALID_VALUE`.

This is the weakest contract the proof needs; it does not model the
non-callable, `alters_data`, or callable-with-no-required-args cases (the
grouping is none of those). **Flag/scenario dependency recorded for G-AX:** the
axiom is sound for a *callable whose no-argument invocation raises a
required-argument `TypeError`* (which the enumeration grouping is); G-AX must
exercise that scenario (a class needing a constructor argument), both with and
without `do_not_call_in_templates`. Docs:
https://docs.djangoproject.com/en/stable/ref/templates/api/#variables-and-lookups
(Django calls callables with no arguments unless `do_not_call_in_templates` is
set).

**Soundness check (G-AX):** `axiom_check.py` (a) drives the REAL
`django.template.Template` / `Context` end-to-end on a callable class that
requires a constructor argument, with `do_not_call_in_templates = True` (the
object is preserved → member access resolves) and `False`/absent (the call
fails → `string_if_invalid`), and (b) drives the REAL Django `Choices` /
`IntegerChoices` produced by the patched metaclass through the exact F2P
template `{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}`, asserting the
rendered output, and confirms a grouping built WITHOUT the flag renders empty.
It also confirms both realizable initial states of the flag right after
`super().__new__` (`base_class_creation`): ABSENT/falsy for a class with no
flagged ancestor, and inherited-truthy for a subclass of an already-flagged
base — establishing that the axiom's unconstrained initial flag is the only
sound contract. Exit 0 iff every observation matches the axioms' `Ensures`.
Note that G-AX runs at **base_commit** for this bundle (`ax_apply_gold` is not
set), so `axiom_check.py` is written to be tree-independent: every axiom it
grounds is about an UNCHANGED callee, and the one F2P observation it makes
reports the flag it actually measured rather than assuming the patched value.

### 3.3 the three declaration predicates (A-consumed, `@Pure @ContractOnly`, opaque)
`base_step_refuses`, `flag_name_taken_by_choice` and `repeats_choice_value` are
opaque decidable properties of the DECLARATION — its declared kind, its choice
names, its choice values — all settled before the construction starts. They are
what makes the three refusals OBSERVABLE in the spec instead of excluded from it
(§2b). Their repository grounding, each an UNCHANGED callee:

* `base_step_refuses` ↔ the refusals `enums.py:28-33` makes (§3.1).
* `flag_name_taken_by_choice` ↔ the guard on the flag-recording line. Recording
  the flag is `cls.do_not_call_in_templates = True` at `enums.py:34`, and `cls`
  is an `enum.EnumMeta` instance, so the assignment goes through CPython's
  ```python
  def __setattr__(cls, name, value):
      """Block attempts to reassign Enum members. …"""
      member_map = cls.__dict__.get('_member_map_', {})
      if name in member_map:
          raise AttributeError('Cannot reassign members.')
      super().__setattr__(name, value)
  ```
  So the flag's recording is REFUSED precisely when one of the grouping's own
  declared choices is named `do_not_call_in_templates`. This is a guarded binding,
  not a bare field write, which is why the model spends a whole leg of its case
  split on it.
* `repeats_choice_value` ↔ the table `enum.unique(cls)` consults (§3.4).

**Independence and ORDER.** The model treats the three as logically independent
and pins the order in which they are consulted. Both facts are measured, not
assumed: `axiom_check.check_refusal_independence` realizes six declaration shapes
covering all four combinations of the two later predicates plus base refusal
(observed `[(False,False,False), (False,False,True), (False,True,False),
(False,True,True), (True,None,None)]`), and
`axiom_check.check_refusal_order` composes the real callees in both orders and
shows the observable difference: flag-recording first → `AttributeError`,
distinctness first → `ValueError`, and the two types differ. That difference is
exactly what the `not flag_name_taken_by_choice(identity)` conjunct in
`Exsures(RepeatedChoiceValue, …)` pins.

**Soundness check (G-AX):** `axiom_check.check_flag_name_guard` drives the REAL
`enum.EnumMeta.__setattr__` over a 400-iteration fuzz of member names,
non-member names and the flag's own name, asserting refusal happens iff the name
is one of the class's own declared members (measured 133 refusals / 267 free
bindings); `check_base_step_refusal` grounds `base_step_refuses` on the real
step (272 accepted / 328 refused), including that a repeated choice value is NOT
refused there; `check_finalize_grouping` grounds `repeats_choice_value` on the
real `enum.unique` (§3.4).

### 3.4 `finalize_grouping` ↔ `enum.unique(cls)` (A-consumed)
**Callee:** `enum.unique` (CPython stdlib `Lib/enum.py`), invoked at
`django/db/models/enums.py:35` (line 34 @ base_commit) as the modeled function's
`return enum.unique(cls)`. UNCHANGED by the patch. Source:

```python
def unique(enumeration):
    """Class decorator for enumerations ensuring unique member values."""
    duplicates = []
    for name, member in enumeration.__members__.items():
        if name != member.name:
            duplicates.append((name, member.name))
    if duplicates:
        alias_details = ', '.join(
            ["%s -> %s" % (alias, name) for (alias, name) in duplicates])
        raise ValueError('duplicate values found in %r: %s' %
                         (enumeration, alias_details))
    return enumeration
```

The axiom is **TOTAL** over declarations, exactly as the callee is: it either
hands back **the same object** (`return enumeration`, hence
`Ensures(Result() is grouping)`) with both modelled facts untouched — so it
cannot be used to launder a flag that was never recorded — or it REFUSES with
`ValueError('duplicate values found in …')`, hence
`Exsures(RepeatedChoiceValue, repeats_choice_value(identity))`. The pairing with
`Ensures(not repeats_choice_value(identity))` makes the two legs two-sided.

Why it is a SEPARATE axiom rather than part of §3.1: it runs at line 35, i.e.
**after** the flag is recorded at line 34. Folding it into the base construction
step would make the model refuse a repeated choice value BEFORE the flag was
recorded, which is observationally wrong on a declaration that also takes the
flag's name (§2b, the ORDER row) — and it is how the earlier spec came to treat
duplicate values as an excluded domain in the first place.

**Soundness check (G-AX):** `axiom_check.check_finalize_grouping` asserts every
clause against the real callee: (i) same object back on a distinct-value
declaration; (ii) the `do_not_call_in_templates` attribute is exactly as it was
found, checked with the flag ABSENT, `False` and `True`; (iii) over a
600-iteration seeded fuzz of value multisets it refuses with
`ValueError('duplicate values found in …')` iff the multiset has a duplicate.

## G-CONF (differential conformance: shadow of the impl region ↔ real patched repo function)

`conformance_check.py` refutes the R/I refinement leg by executing both sides on
the same inputs. It is **not** covered by G-VERIFY (impl ⊨ spec) or G-PBT (no
wrong impl ⊨ spec), neither of which looks at the repository at all.

* **Shadow (provenance `direct`)** — the `# impl-start` / `# impl-end` region of
  `model.py`, copied **verbatim**:
  ```python
  grouping = base_class_creation(identity)  # type: EnumGrouping
  if flag_name_taken_by_choice(identity):
      raise PreserveFlagNameTaken()
  grouping.preserve_when_callable = True
  delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
  return delivered
  ```
  The region contains no contract calls, so nothing had to be stripped; the `pure`
  region is empty, so there is no `@Pure` helper to copy; no `PSeq`/`ToSeq`
  carrier occurs in this model, so no sequence shim is needed.
* **ALL FOUR `@ContractOnly` callees are bridged to the REAL repo / stdlib code
  they axiomatize** (§3), so the axioms are exercised rather than assumed:
  * `base_class_creation` ↔ the unchanged base construction step
    (`super().__new__(...)` at `django/db/models/enums.py:28` together with the
    derived tables at lines 29 and 33; §3.1). Since every step of the modeled
    function except the one added line is unchanged, the bridge runs the REAL
    `ChoicesMeta.__new__` **as it exists at base_commit**, obtained in-container
    with `git show HEAD:django/db/models/enums.py` and exec'd as module
    `enums_base_commit` — never retyped in the script — with the
    value-distinctness step **alone** removed (the module's `enum` name is
    swapped for a proxy whose `unique` is the identity function) so that step is
    reached through its own bridge instead of twice. The script asserts the
    base_commit text differs from the patched working tree by **exactly one added
    line** (`+        cls.do_not_call_in_templates = True`) and exits non-zero
    otherwise, so the bridge provably carries the whole unchanged remainder and
    none of the modeled edit. The bridge is TOTAL exactly as the axiom is: it
    returns the produced object, re-checking the axiom's
    `Ensures(Result().identity == identity)` against the real callee, or reports
    `BaseStepRefused` carrying the real callee's own exception. Both realizable
    initial flag states the axiom leaves **havoced** are exercised (absent 64662 /
    inherited-truthy 35338).
  * `finalize_grouping` ↔ the unchanged value-distinctness step `enum.unique(cls)`
    at `django/db/models/enums.py:35` (§3.4). The bridge returns the object the
    real callee hands back, asserting the axiom's `Result() is grouping`,
    identity- and flag-preservation clauses against it, or reports
    `RepeatedChoiceValue` carrying the real `ValueError`.
  * `flag_name_taken_by_choice` ↔ the table the REAL unchanged
    `enum.EnumMeta.__setattr__` guard consults, `name in cls.__dict__['_member_map_']`
    (§3.3). When it reports True the bridge additionally attempts the real binding
    and asserts it really is refused with `AttributeError`; when it reports False
    the shadow's own subsequent assignment goes through the real guard. So the
    predicate is checked on both sides rather than modelled by the script.
  * `resolved_in_template` ↔ the unchanged rule
    `django.template.base.Variable._resolve_lookup` (callable step,
    `django/template/base.py:851-866`), driven as the REAL
    `Variable('x').resolve(ctx)` inside a **template-bound** `Context` (so the
    failed-invoke branch reaches `context.template.engine.string_if_invalid`)
    with a deliberately NON-EMPTY `string_if_invalid`, so "the object itself"
    and "the invalid value" are never confusable with each other or with `''`.
* **Oracle** — the REAL patched repo function is **called**, not transliterated:
  `django.db.models.enums.ChoicesMeta.__new__` (`django/db/models/enums.py:11`;
  the gold patch adds the assignment at body line 34), invoked through the normal
  class-creation path `ChoicesMeta(classname, bases, classdict)` from the patched
  module imported off `/testbed`. The script asserts via `inspect.getsource`
  that the ambient `__new__` carries `cls.do_not_call_in_templates = True` and
  exits non-zero otherwise, so it can never silently diff the shadow against
  base_commit code.
* **Outcome tags — the spec's case split, made executable.** The modeled function
  has FOUR outcomes and the differential compares **which one** each leg
  produces, not merely whether both raised: `delivered`, `base-refused`,
  `flag-name-taken`, `repeats-value`. On the SHADOW leg the tag is which model
  exception escaped (i.e. the `Exsures` the spec demands). On the ORACLE leg the
  tag is read off the REAL traceback — the line of `django/db/models/enums.py`
  the exception escaped from: the flag-recording line (measured at 34), the
  `return enum.unique(cls)` line (measured at 35), or any earlier line of the
  function. Both line numbers are **located in the patched source at run time**
  (never hard-coded) and their order `34 < 35` is asserted, so the classification
  is the repository's own structure rather than the script's opinion. For
  `base-refused` and `repeats-value` the two legs' exception **type and message**
  are compared as well, so a bridge that reported the right tag with the wrong
  report would still be caught; for `flag-name-taken` the oracle's exception is
  asserted to be `AttributeError('Cannot reassign members.')`.
* **Type bridge (§2 inverted)** — `GroupingRef` is a two-field view onto a REAL
  enumeration class object: `identity` ↔ `id(cls)` (positive in CPython,
  asserted, so `Requires(identity > 0)` holds and never collides with the
  sentinel `0`); `preserve_when_callable` ↔ `getattr(cls,
  'do_not_call_in_templates', False)` / `setattr(cls, ..., True)`;
  `INVALID_VALUE == 0` ↔ the engine's `string_if_invalid`;
  `resolved_in_template(g)` ↔ `id(cls)` when the real rule yields the class
  object itself, else `0`. Generation runs **concrete → abstract**: the real base
  construction runs first and its object's `id()` is the `identity` handed to
  the shadow, so every input satisfies the `Requires` by construction. For a
  declaration the base step REFUSES there is no produced object, so the identity
  handed to the shadow is the (positive) `id()` of the recorded refusal instead;
  only the refusal report is reachable on that leg.
  `declaration_available(identity)` is inverted as a **consumption counter** on
  the pending record: the bridge asserts the base construction step is entered at
  most ONCE per declaration, which is the executable reading of a resource that
  is consumed and never returned.
* **Observables** — the outcome tag; for a refusal, the real exception type and
  message the report carries; the flag (read the unchanged consumer's way);
  identity preservation (the returned object IS the one the real base
  construction step produced, observed by spying the real
  `enum.EnumMeta.__new__` call on the oracle leg and by object identity against
  the pending record on the shadow leg — the executable reading of
  `Ensures(Result().identity == identity)` plus the provenance token); the
  resolution outcome through the REAL template rule (`self` vs the invalid
  sentinel — the discriminating postcondition); plus the **frame**: members
  (name/value/label), `choices`/`names`/`labels`/`values`,
  `_value2label_map_`, and the produced class's own `__dict__` key set.
* **Inputs** — **100000** (210 boundary + 99790 seeded fuzz) over **10**
  ancestries × member configurations. Ancestries deliberately cover both havoced
  initial flag states on both legs: `raw:*` (bases `(int|str, enum.Enum)` /
  `(enum.Enum,)` — flag ABSENT), `flagged:*` (shared bases pre-carrying the flag —
  INHERITED-TRUTHY, the state where a toggling/conditional impl diverges),
  `own:*` (each leg's own `IntegerChoices`/`TextChoices`/`Choices`), and
  `bad:bool` (a declared kind that cannot carry the declared choice values, which
  the base construction step refuses). Member configurations: empty enum,
  singleton, the exact F2P `Suit` shape (`DIAMOND = 1, 'Diamond'`), auto-derived
  labels, list/tuple label forms, multi-element values, lazy (`gettext_lazy`)
  labels, `__empty__`, negative / zero / empty-string values, **and the three
  refusal shapes**: a choice declared under the flag's own name, two choices
  sharing a value, both at once (which pins the ORDER the two refusals are made
  in), and a choice named after a derived table the base step itself binds. The
  previously-excluded duplicate-value case is now **inside** the compared domain,
  not checked off to the side. The fuzz draws repeated values (p≈0.25) and the
  flag's own name (p≈0.15) so the refusal legs are fuzzed too. All four modeled
  outcomes are asserted to be realized by the boundary domain (measured
  `delivered` 108, `base-refused` 48, `flag-name-taken` 36, `repeats-value` 18);
  if any were missing the script exits non-zero rather than passing vacuously.
* **Pinned seed** — `SEED = 12304` (module constant in `conformance_check.py`).
* **Discrimination self-test** — the differential is re-run with the shadow's body
  MUTATED, once per mutation, and each mutant must be reported as disagreeing
  (boundary shapes caught, of 210):
  `omit-assignment` (the pre-patch impl) 144; `toggle-assignment` (a
  conditional/inverting impl) 36 — exactly the `flagged:*` delivered shapes, where
  the incoming flag is inherited-truthy; `skip-distinctness` 18; 
  `swap-refusal-reports` 36; `distinctness-before-flag` (the ORDER mutation) 18;
  `refuse-everywhere` 126. All six are caught, so a green G-CONF here is not
  vacuous.
* **Verdict** — `G-CONF=pass`: exit 0, 0 disagreements over 100000 inputs.
