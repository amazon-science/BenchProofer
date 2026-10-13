# refinement.md — django__django-13346

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildMembershipClause` `do` block, plus the `slotToken`/`clauseTokens` deep
model in the `pure` region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; bijection in mapping.md §2), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (a deep model validated == the real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
narrative is audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The membership-clause RHS site — `KeyTransformIn.process_rhs` (`django/db/models/fields/json.py`, gold hunk)

Gold hunk (new lookup class, the load-bearing body):
```python
class KeyTransformIn(lookups.In):
    def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        if not connection.features.has_native_json_field:
            func = ()
            if connection.vendor == 'oracle':
                func = []
                for value in rhs_params:
                    value = json.loads(value)
                    function = 'JSON_QUERY' if isinstance(value, (list, dict)) else 'JSON_VALUE'
                    func.append("%s('%s', '$.value')" % (function, json.dumps({'value': value})))
                func = tuple(func)
                rhs_params = ()
            elif connection.vendor == 'mysql' and connection.mysql_is_mariadb:
                func = ("JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))",) * len(rhs_params)
            elif connection.vendor in {'sqlite', 'mysql'}:
                func = ("JSON_EXTRACT(%s, '$')",) * len(rhs_params)
            rhs = rhs % func
        return rhs, rhs_params
```
(plus `KeyTransform.register_lookup(KeyTransformIn)` — registration, not behavior.)

| # | Solution.lean impl op (`buildMembershipClause`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `vals : List Int` | `rhs, rhs_params = super().process_rhs(...)` — `rhs_params` is the list of listed values, `rhs` the comma-joined `%s` template (one `%s` per value) | R | `list` ↔ `List Int` (mapping.md §2); the super-class call is UNCHANGED and supplies one bare `%s` slot per listed value, modeled as the input shape (`vals.length` slots), not assumed of a callee. |
| A2 | parameter `bareTok : List Char` | one `%s` placeholder of the super-class template (`In.process_rhs`, `lookups.py:384`) | R | `str` ↔ `List Char`; the operand token used unchanged on a native backend. |
| A3 | parameter `wrapOf : Int → List Char`, with `require ∀ v ∈ vals, wrapOf v ≠ bareTok` | the gold hunk's construction of `func[i]` FROM `rhs_params[i]` — constant in the value on sqlite/mysql/mariadb, value-dependent on Oracle (`JSON_QUERY` vs `JSON_VALUE` by the value's kind, with the value's own JSON embedded) — substituted into slot `i` by `rhs % func` | R | `str` ↔ `List Char`, and the per-value construction ↔ a total function PARAMETER (not an axiom: no `ensures` is attached to it, so the proof assumes nothing about its values beyond the `require`). The spec abstracts over WHICH construction a vendor uses (mapping.md §2) while keeping the dependence on the value, pinning the load-bearing property: each listed value's token genuinely transforms the placeholder (`wrapOf v ≠ bareTok`). Each vendor's concrete construction is compared byte for byte against the gold code by G-CONF. |
| A4 | the per-slot `if native then bareTok else wrapOf v`, evaluated at each slot's own value | `if not connection.features.has_native_json_field: ... rhs = rhs % func` (the substitution runs iff non-native; otherwise `rhs` is left as the bare template) | I + R | the capability test `native` ↔ `connection.features.has_native_json_field` (mapping.md §2: the gold `if not ...` makes `native = false` the substituting branch); the `if`/choice control flow is **I**. The choice is made PER SLOT, at that slot's own value, because the gold hunk builds `func[i]` from `rhs_params[i]`: no per-slot uniformity is claimed, and on the Oracle branch two slots of one clause really do differ (mapping.md §2). |
| A5 | the `while` loop prepending `slotToken … vals[i-1]!` per slot ⇒ `result = clauseTokens native bareTok wrapOf vals` | `rhs = rhs % func` substituting `func[i]` into the `i`-th of the `vals.length` `%s` slots, in order | I + R | the per-slot substitution over the whole template ↔ the front-recursive fold `clauseTokens` (one `slotToken`, applied to that slot's own value, per slot, in order); string/list ops are **I**, the `str`↔`List Char` carrier is **R**. |
| A6 | parameter `wrapHoldsValue : Bool`, with NO relation to `wrapOf` asserted in the `require` | which non-native ARM the vendor dispatch selects: the arm that builds each operand expression around the value itself (Oracle, `json.py:386-396`) vs the arms that leave an inner `%s` open (MariaDB `json.py:398`, `{sqlite, mysql}` `json.py:400`) | R | `connection.vendor == 'oracle'` (on the non-native path) ↔ `wrapHoldsValue = true`; a `bool` ↔ `Bool` carrier. It is a separate INPUT rather than a predicate over `wrapOf` because the real distinction is a branch, not a property of the expression's bytes: an Oracle expression built from a value whose own text contains `%s` holds its value AND contains the mark, so any `require` tying the two would exclude a real input (mapping.md §3.1). The bijection image is `wrap_holds_value(vendor)` in conformance_check.py. |
| A7 | the second returned component `if native then vals else (if wrapHoldsValue then [] else vals)` ⇒ `out.2 = clauseSuppliedValues native wrapHoldsValue vals` | the second element of the returned pair, `rhs_params` (`json.py:402`): the incoming list forwarded unchanged on the native short-circuit and on the MariaDB / `{sqlite, mysql}` arms, and `()` on the Oracle arm, which assigns `rhs_params = ()` at `json.py:396` | I + R | `process_rhs` returns a PAIR and both halves are load-bearing. The real decision is WHOLE-CLAUSE and per-ARM: `json.py:396` is the hunk's only assignment to `rhs_params`, it sits inside the Oracle arm and AFTER that arm's per-value loop, and it inspects no token — so the outcome is "all of them" or "none of them", never a subset. The model's two-way branch on `(native, wrapHoldsValue)` is that control flow (**I**), over the `list` ↔ `List Int` carrier (**R**). NOTE the shape this step deliberately does NOT take: deriving the component by testing each emitted token for the mark. That rule agrees on every listed value whose text has no `%` and diverges as soon as one does — for `'100%sale'` the Oracle expression `JSON_VALUE('{"value": "100%sale"}', '$.value')` contains `%s` yet the real callee returns `rhs_params == []` (measured on the patched callee). G-CONF compares this component exactly and now fuzzes mark-bearing values so the two rules cannot be confused again (mapping.md §2.1). |

Discriminating content of the change — on a **non-native** backend each slot must
receive its own value's extraction expression, not the bare placeholder — lives
in
`native = false ⇒ out.1 = clauseTokens false bareTok wrapOf vals`, i.e. slot `i`'s
emitted token is that value's `wrapOf vals[i] ≠ bareTok` (model) ⇔ the inserted
`if not ...: rhs = rhs % func` with `func[i]` built from `rhs_params[i]` (real). The pre-patch code (no `KeyTransformIn` registered) emits the
bare placeholder per slot regardless of `native`; `Solution_prepatch.lean`
reproduces that (every slot `bareTok`, never consulting `native`, never consulting
the per-value map, and forwarding every value whatever the arm) and **fails**
exactly that clause (G-DIFF): for `native = false` and any non-empty `vals` it
yields a `bareTok` where the spec demands `wrapOf v`, and
`require ∀ v ∈ vals, wrapOf v ≠ bareTok` makes the two provably distinct at every
listed value. It fails the A7 clause as well, since on the value-holding arm it
hands over every value where the spec demands none — so the twin is refuted by
each of the two obligations independently, not only by their conjunction.

## B. No consumed axioms, no A-reference

The bundle declares no `axiom` and no A-reference deep model of an outside callee
(mapping.md §3.1). The changed operation (the per-slot template substitution and
the accompanying-values decision) is modeled DEEPLY via
`slotToken`/`clauseTokens`/`clauseSuppliedValues`. The three things it ranges over
are **input data** (the bare placeholder from the unchanged super-class template,
the vendor's per-value operand-expression map, and which arm's expression form was
taken), carried as parameters — not contracts the proof consumes. `wrapOf` is a
total function parameter with no `ensures` attached, universally quantified in the
contract, so it is data and not an axiomatized callee; `wrapHoldsValue` is a plain
`Bool` input, likewise unconstrained (mapping.md §3.1). The function under change
is not axiomatized. G-AX is therefore `skip` (no `axiom_check.py`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I (A6/A7 included: the arm-level fact is an ordinary `Bool`
input and the second return component is modeled concretely as a branch on it, not
axiomatized). The one operation that genuinely *changed* — replacing each
membership-list operand placeholder with the backend's stored-value extraction
expression for that slot's own listed value, on non-native backends — is modeled
**deeply** (the
per-slot `if native then bareTok else wrapOf v` choice, evaluated at each slot's
own value, plus the spelled-out fold `clauseTokens`), not hidden behind an axiom
about the function under change.

## D. verify(Solution) ⇒ resolved

`buildMembershipClause` verifies only if (i) on a native backend each slot is the
bare placeholder, (ii) on a **non-native** backend each slot is the
extraction expression `wrapOf v` for that slot's OWN listed value (distinct from
the bare placeholder at every listed value), and (iii) the values travelling
alongside the clause are BALANCED against the arm the clause was built on — every
listed value on the native short-circuit and on an arm whose expressions leave a
place open, and none at all on an arm whose expressions hold their own value.
(i)+(ii) are the tokens the gold hunk builds; (iii) is the `rhs_params` half of its
return pair, which is why a token-identical implementation that withholds or
over-supplies the values does not verify — and, equally, why one that decides by
inspecting the expression it just emitted does not either: at a listed value whose
own text carries the mark the two rules give different answers and only the
per-arm one matches the real callee. By R (`str`↔`List Char`, `list`↔`List Int`,
`has_native_json_field`↔`native`, the per-value construction↔`wrapOf`, the arm's
expression form↔`wrapHoldsValue`;
mapping.md §2) the verified pair equals the gold
`KeyTransformIn.process_rhs` return on the same inputs, for
every enumerated vendor branch — G-CONF differential-tests all of
oracle/mariadb/sqlite-mysql/native over ≥10⁵ fuzzed inputs by EXACT per-slot
token equality AND exact equality of the accompanying values, with no per-vendor
downgrade, over a pool that includes mark-bearing listed values, and asserts the
unenumerated-vendor configuration out of scope (mapping.md §2.1). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE: the F2P
`test_key_in` now compares extracted scalar values, returning the expected rows
on sqlite instead of the empty queryset). The single trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness obligation.
