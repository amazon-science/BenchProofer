# refinement.md — django__django-12304

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_template_usable_grouping` impl region, using the
`base_class_creation`, `flag_name_taken_by_choice`, `finalize_grouping` and
`resolved_in_template` axioms) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The metaclass site — `ChoicesMeta.__new__` (`django/db/models/enums.py:11`)

Gold hunk (one added line, between `cls.label = property(...)` at line 33 and
`return enum.unique(cls)` at line 34):
```
  cls.label = property(lambda self: cls._value2label_map_.get(self.value))
+ cls.do_not_call_in_templates = True
  return enum.unique(cls)
```

| # | model.py impl op (`build_template_usable_grouping`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `grouping = base_class_creation(identity)` | the base construction step `cls = super().__new__(metacls, classname, bases, classdict)` (`enums.py:28`) together with the derived tables the same step records, `cls._value2label_map_ = …` (line 29) and `cls.label = property(…)` (line 33) — i.e. `enums.py:28-33` | A-consumed | `base_class_creation` is the weakest contract on the unchanged base construction step the proof needs. It produces a callable class object with the requested identity, ISSUES the provenance token `built_from_declaration` for that object, CONSUMES the single-use declaration resource `declaration_available(identity)` (the real `classdict`, which `super().__new__` exhausts — a second call on it raises `KeyError` on the first member name; mapping.md §2b), and deliberately leaves the initial preserve-when-callable flag UNCONSTRAINED — the real callee yields `getattr(cls, 'do_not_call_in_templates', False) == False` only for a class with no flagged ancestor, but `True` (inherited) for a class built under an already-flagged base (`IntegerChoices`/`TextChoices`/user subclasses once the patched metaclass has flagged `Choices`). It is TOTAL: `Exsures(BaseStepRefused, base_step_refuses(identity))` carries the refusals this step itself makes (a declared kind that cannot carry the values → `TypeError: type 'bool' is not an acceptable base type` at line 28; a choice named after a table this step binds → `AttributeError('Cannot reassign members.')` at line 29/33), and `Ensures(not base_step_refuses(identity))` makes delivery two-sided, so a body can neither invent a refusal the step does not make nor deliver for one it does. It does NOT include the value-distinctness step (that is A4). (mapping.md §3.1; G-AX exercises BOTH initial flag states and both refusal families.) |
| A2 | `if flag_name_taken_by_choice(identity): raise PreserveFlagNameTaken()` | the GUARD on the added line: `cls.do_not_call_in_templates = True` (`enums.py:34`) is an attribute binding on an `enum.EnumMeta` instance, so it passes through `EnumMeta.__setattr__`, which raises `AttributeError('Cannot reassign members.')` iff `'do_not_call_in_templates' in cls.__dict__['_member_map_']` | A-consumed + I | the real added line is a GUARDED binding, not a bare field write. The model separates the guard's decision (the opaque declaration predicate `flag_name_taken_by_choice`, mapping.md §3.3) from the binding itself (A3). Where the guard refuses, the real construction delivers no class object at all and the declaring `class` statement sees the `AttributeError`; the model reports `PreserveFlagNameTaken`. This is one leg of the complete case split, and it is confined to declarations A1 accepted (`not base_step_refuses` conjunct), because the base step's refusal comes first. |
| A3 | `grouping.preserve_when_callable = True` | `cls.do_not_call_in_templates = True` (`enums.py:34`) | I | identical concrete operation: a boolean attribute on the just-created class object is assigned the literal `True`. `preserve_when_callable` ↔ `do_not_call_in_templates` (R: the model keeps only this one touched attribute; mapping.md §1, §2). This is THE line the patch adds. Placed AFTER A2 and BEFORE A4, exactly as line 34 sits between the guard it trips and line 35. |
| A4 | `delivered = finalize_grouping(grouping, identity)` | `enum.unique(cls)` (`enums.py:35`; line 34 @ base_commit) | A-consumed | `finalize_grouping` is the weakest contract on the unchanged value-distinctness step. It is TOTAL: it hands back THE SAME object (`enum.unique` ends `return enumeration`, hence `Ensures(Result() is grouping)`) with both modelled facts untouched — so it cannot launder a flag that was never recorded — passing the provenance token along; or it REFUSES with `RepeatedChoiceValue` (`ValueError('duplicate values found in …')`) for exactly the declarations `repeats_choice_value` holds of. It is a SEPARATE axiom from A1 precisely because it runs AFTER A3: a declaration that both takes the flag's name and repeats a value is refused at line 34, not 35, and the `not flag_name_taken_by_choice` conjunct in `Exsures(RepeatedChoiceValue, …)` pins that. (mapping.md §3.4; G-AX drives the real `enum.unique` over a 600-iteration value-multiset fuzz.) |
| A5 | `return delivered` | `return enum.unique(cls)` — the same expression, whose value the metaclass returns to the declaring `class` statement | I | the model returns exactly what A4 handed back; by A4's `Result() is grouping` that is the object A1 produced, carrying the token, so `Ensures(built_from_declaration(Result(), identity))` and `Ensures(Result().identity == identity)` are about THAT object rather than any object reporting the requested identity. |

The behavioural postcondition `resolved_in_template(Result()) == identity` is
discharged from A3+A4+A5: after A3, `grouping.preserve_when_callable == True`;
A4 hands back the SAME object with that fact untouched
(`Result().preserve_when_callable == Old(grouping.preserve_when_callable)`); and
the `resolved_in_template` axiom (A-consumed, the unchanged template
variable-resolution rule for a callable whose no-arg call fails) then yields
`grouping.identity`. The proof CONSUMES this axiom's `Ensures` — it is the link
from "the flag is set" to the tested behaviour "the grouping resolves to itself
in a template, so its members are accessible."

The three REFUSAL postconditions are discharged the same way, each from the axiom
of the step that makes it: `Ensures(not base_step_refuses)` /
`Exsures(BaseStepRefused, …)` from A1, `Ensures(not flag_name_taken_by_choice)` /
`Exsures(PreserveFlagNameTaken, …)` from A2's guard, and `Ensures(not
repeats_choice_value)` / `Exsures(RepeatedChoiceValue, …)` from A4. Because each
predicate is opaque, the ONLY way a body can establish the negative is to have
RUN the step and had it deliver; and because each `Exsures` leg is guarded by the
negations of the earlier predicates, the ORDER A1 → A2 → A3 → A4 is itself part
of what must be refined. A body that reorders A4 before A2/A3 satisfies every
unordered clause and still diverges from the repository on a declaration that
both takes the flag's name and repeats a value.

## B. The variable-resolution site — `Variable._resolve_lookup` (`django/template/base.py:851`)

This site is **UNCHANGED** by the patch; it already branches on
`do_not_call_in_templates`. It is the unchanged callee the behaviour flows
through, modeled by the `resolved_in_template` axiom (A-consumed).

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `resolved_in_template(grouping)` axiom: `Result() == identity` iff `preserve_when_callable`, else `INVALID_VALUE` | no diff line (the `if getattr(current, 'do_not_call_in_templates', False): pass` branch already present at `base.py:852-853`); the patch's added flag merely makes the branch taken | A-consumed | `resolved_in_template` is the weakest contract on the unchanged resolution rule the spec needs, specialised to a callable whose no-argument invocation fails (a class object needing a constructor `value` arg). The proof consumes its `Ensures` to derive the behavioural postcondition. The flag the patch sets selects the `pass` branch (preserve), so resolution yields the grouping itself; without the flag the no-arg call fails → `string_if_invalid` (the invalid sentinel). (mapping.md §3.2; G-AX confirms it against the REAL `Template`/`Context` and the REAL patched `Choices`.) |

Why this carries the F2P test: the F2P template `{{ Suit.DIAMOND.label }}`
first resolves the variable `Suit` (the grouping, a callable class). With the
flag (gold) the grouping resolves to itself, so `.DIAMOND` (a member) and then
`.label` resolve, rendering `Diamond`. Without the flag (pre-patch) the engine
invokes `Suit()`, which fails (a `value` argument is required), yielding
`string_if_invalid`; the subsequent `.DIAMOND` lookup then fails and the
template renders nothing. The model's `model_prepatch.py` reproduces exactly the
pre-patch state — its spec region is byte-identical to `model.py`'s and its impl
region omits A2, A3 and A4's flag dependence, i.e. exactly the three lines the
patch's one added line and its guard bring:
```python
grouping = base_class_creation(identity)  # type: EnumGrouping
delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
return delivered
```
It **fails** first on `Ensures(not flag_name_taken_by_choice(identity))` — with
the guard gone there is nothing left to establish that the flag's name was free —
and independently on `Ensures(Result().preserve_when_callable == True)` and
`Ensures(resolved_in_template(Result()) == identity)`, neither of which the
verifier can establish from an unconstrained flag. That is the spec sensing the
change (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
adding the boolean attribute assignment `cls.do_not_call_in_templates = True` —
is modeled **identically** (step A3, tag I: a boolean field assignment). It is
NOT hidden behind an axiom. The consumed axioms cover **unchanged** callees
the new/surrounding code invokes — the base construction step
(`base_class_creation`, §3.1), the guard the added binding passes through
(`flag_name_taken_by_choice`, §3.3), the value-distinctness step the construction
returns (`finalize_grouping`, §3.4) and the template variable-resolution rule
(`resolved_in_template`, §3.2) — never the operation under change. There is no
A-reference deep model here (no changed operation needed deep modeling: the
change is a single boolean assignment).

## C2. Obligations beyond the mapped operations (totality, multiplicity, provenance, the complete ordered case split)

The operation table above enumerates only WHICH operations the impl performs.
Further obligations are needed for `verify ⇒ resolved`, because an impl can
perform the right operations and still not be the gold metaclass. All are
recorded in mapping.md §2b with their repo grounding.

| # | obligation | why the mapped operations alone do not give it |
|---|---|---|
| D1 | `Requires(MustTerminate(2))` — the construction must actually DELIVER a grouping | Nagini proves PARTIAL correctness by default: a body that never reaches its return discharges every `Ensures` vacuously. `return build_template_usable_grouping(identity)` is trivially "the same operations" (it is a self-call) and satisfies every leg of §A, yet its faithful patch (`return metacls.__new__(metacls, classname, bases, classdict)`) hangs class creation with `RecursionError` so the F2P module cannot even import. Real class creation always returns the class object to the `class` statement. Measure 2 permits the measure-1 callees (`base_class_creation`, `finalize_grouping`, `EnumGrouping.__init__`) and forbids re-entry of this construction. |
| D2 | `Requires(declaration_available(identity))`, consumed by A1 — one declaration yields one grouping | `identity` is a caller-chosen free int that `base_class_creation` merely echoes, so the delivery clauses alone permit TWO base constructions to both "return `identity`". Under §2's bijection `identity ↔ id(cls)` that is unrealizable (two distinct class objects cannot share an `id()`), and in the repo the second `super().__new__` on an already-consumed `classdict` raises `KeyError` on the first member name. The single-use resource ties the delivered grouping to THE object A1 produced instead of to the caller's int. It is an opaque `@Predicate` with no body and no `Ensures`, so it adds multiplicity only — no new behavioural claim and no new G-AX surface. |
| D3 | `Requires(built_from_declaration(Result(), identity))` — the grouping DELIVERED is the one A1 built | `identity` is a caller-chosen free int, so a body may run the whole gold construction and then return a different, freshly built grouping carrying the same identity value; every clause about the flag and the identity still holds of the substitute. The provenance token can only be obtained from A1 (which issues it) or A4 (which passes it along), and it is body-less so it cannot be `Fold`ed. In the repository the substitution is impossible because `enum.unique(cls) is cls`: the declaring `class` statement receives the object line 28 produced. Rejected as `weak-wrong-identity-obj` and `weak-echo-fabricate`. |
| D4 | NO precondition on WHICH declarations are specified; a complete, ORDERED four-way case split instead | THE RECORDED HOLE. The earlier spec carried `Requires(base_step_can_bind_choices(identity))`, so every declaration that repeats a choice value, names a choice after the flag's name, or declares an unusable kind fell OUTSIDE the specified domain and an impl could do as it liked there. `atk_2.py` verified against that spec — its refusal branch was unreachable in the proof — and its patch broke PASS_TO_PASS `test_invalid_definition`, which asserts `ValueError: duplicate values found in <enum 'Fruit'>: PINEAPPLE -> APPLE`. The repair removes the precondition and makes each refusal OBSERVABLE instead: three opaque declaration predicates, propagated through A1's and A4's `Exsures`, and one `Exsures` leg per refusal guarded by the negations of the earlier predicates so the ORDER A1 → A2 → A3 → A4 is pinned too. Rejected as `weak-wrong-report-on-repeat`, `weak-skip-distinctness`, `weak-swap-reports`, `weak-finalize-before-flag`, `weak-invent-base-refusal`, `weak-always-refuse`, `weak-inverted-refuse`, `partial-fixed-identity`. |

No obligation narrows the domain: `identity > 0` is unchanged and D4 strictly
WIDENS the specified domain by deleting the earlier exclusion, so the repair is a
strengthening in both directions (more declarations specified, more pinned about
each). None pins an incidental detail of the gold implementation: the gold impl
and both structurally-different positive controls (`pos-flag-after-distinctness`,
which records the flag on the object the distinctness step returns;
`pos-local-flag`, which binds the grouping to a typed local first) satisfy them,
as G-PBT's soundness lane records, and `admiss-f2p-diamond` re-confirms the F2P
shape is admissible.

## D. verify(model) ⇒ resolved

`build_template_usable_grouping` verifies only if it sets
`preserve_when_callable == True` (A3) AND the behavioural consequence holds:
`resolved_in_template(Result()) == identity ≠ INVALID_VALUE` (B1). By R
(EnumGrouping ↔ the enum class object; `preserve_when_callable` ↔
`do_not_call_in_templates`; `INVALID_VALUE` ↔ `string_if_invalid`) and I (the
boolean assignment) the verified function equals the gold metaclass on the
tested grouping: it builds the class via the unchanged base step (A1, A-consumed),
passes the flag's name through the same guard the real binding passes through
(A2), sets `do_not_call_in_templates = True` (A3), and returns what the unchanged
value-distinctness step hands back (A4, A5). By G-AX the unchanged base
construction meets `base_class_creation`, the unchanged `enum.unique` meets
`finalize_grouping`, the unchanged `EnumMeta.__setattr__` guard meets
`flag_name_taken_by_choice` (and the three declaration predicates are shown
mutually independent and their consultation ORDER observable), and the unchanged
template resolution rule meets `resolved_in_template` — all confirmed against the
REAL callees, the REAL `Template`/`Context` and the REAL `Choices` rendering the
F2P template. It further verifies only if it TERMINATES (D1), runs the base
construction step exactly once (D2), delivers THAT object (D3), and makes the
right one of the four outcomes for EVERY declaration, in the right order (D4) —
so it cannot be a diverging body, a double-constructing body, a body that
substitutes a fabricated grouping, or a body that treats the refused declarations
as a region of its own. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and audited callees —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
