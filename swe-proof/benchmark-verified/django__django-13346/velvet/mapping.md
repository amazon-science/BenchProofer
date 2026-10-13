# mapping.md — django__django-13346

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9c92924cd5d164701e2514e1c2d6574126bd7cc2`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
callee provenance + flag dependencies.

Repo file under change: `django/db/models/fields/json.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildMembershipClause (vals native bareTok wrapOf wrapHoldsValue)` | the `process_rhs` of the membership lookup registered on a key-extracted column — added by the gold patch as `KeyTransformIn.process_rhs` (`django/db/models/fields/json.py:381-402` post-patch), refining `In.process_rhs` (`django/db/models/lookups.py:362-390`) | the modeled changed function: build the right-hand side of a membership (`__in`) comparison over a list of listed values, for a key extracted from a stored JSON document — as the PAIR it is returned as: the operand tokens, and the values that still travel alongside them |
| `vals : List Int` | `rhs_params` — the list of listed values the membership clause compares against (`lookups.py:383`, the `sqls_params` of `batch_process_rhs`) | each listed value carried by an integer identity; the count, the order, AND each value's identity all matter to the emitted tokens, since slot `i`'s token is built from `rhs_params[i]` |
| `native : Bool` | `connection.features.has_native_json_field` (`json.py:384` post-patch, used as `if not ...`) | whether the backend stores the document in a native typed JSON column |
| `bareTok : List Char` | one `%s` placeholder of the super-class RHS template (`In.process_rhs` builds `'(' + ', '.join(sqls) + ')'`, each `sqls` element a `%s`; `lookups.py:384`) | the operand token emitted per slot on a native backend (used unchanged) |
| `wrapOf : Int → List Char` | the gold hunk's construction of `func[i]` FROM the listed value at slot `i`: `"JSON_EXTRACT(%s, '$')"` on sqlite/mysql (`json.py:400`) and `"JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))"` on MariaDB (`json.py:398`) (both constant in the value), and on Oracle the value-dependent `"%s('%s', '$.value')" % (function, json.dumps({'value': value}))` where `function` is `JSON_QUERY` for a list/dict and `JSON_VALUE` otherwise (`json.py:386-395`) | the map from ONE listed value to the operand token its slot receives on a non-native backend |
| `wrapHoldsValue : Bool` | whether the branch taken builds its operand expressions AROUND the value — i.e. whether the arm reached is the one that constructs each expression from `json.dumps({'value': value})` and then clears the accompanying values for the whole clause (`rhs_params = ()`, `json.py:396`). `true` on the Oracle arm; `false` on the MariaDB and `{sqlite, mysql}` arms, whose expressions leave an inner `%s` and forward `rhs_params` untouched | the branch-level fact the second output component is a function of. It is a property of the ARM, decided once per clause: `json.py:396` sits inside the arm and after its per-value loop, so the real code consults no emitted token — see §2.1 |
| `slotToken native bareTok wrapOf v` | the per-slot choice `bareTok` (native) vs `wrapOf v` (non-native) — the gold hunk's `rhs = rhs % func` (`json.py:401`) applied to the `%s` slot of the value `v` | pure spec: which token one slot receives, as a function of that slot's own value |
| `clauseTokens native bareTok wrapOf vals` | the whole list of per-slot tokens — `rhs % func` over the full `func` tuple, whose `i`-th entry the gold hunk builds from `rhs_params[i]` (or the bare template under native) | pure spec: the operand tokens for every slot, in order, each from that slot's own value |
| `clauseSuppliedValues native wrapHoldsValue vals` | the SECOND component of `process_rhs`'s return pair, `rhs_params` (`json.py:402`): the incoming values forwarded unchanged on the native short-circuit (the whole `if` at `json.py:384` is skipped) and on the MariaDB and `{sqlite, mysql}` arms, and `()` on the Oracle arm, which sets `rhs_params = ()` for the whole clause at `json.py:396` | pure spec: the values that must still travel alongside the clause — ALL of them or NONE, following the arm taken. It reads `native`, `wrapHoldsValue` and the list, and nothing else: no per-slot decision and no inspection of an emitted token |

The pre-patch behavior: no `KeyTransformIn` is registered, so a `key__in`
lookup falls through to the generic `In` lookup, whose `process_rhs`
(`lookups.py:362-390`) emits the **bare** `%s` placeholder per slot regardless
of `has_native_json_field`. On a non-native backend the bare placeholder binds
the *raw stored* encoding of the key (e.g. a quoted/typed JSON scalar), which
never compares equal to the listed scalar — so the F2P `test_key_in` returns the
empty queryset (the problem statement's "`__in` returns 0 rows"). The fix
replaces each slot's placeholder with the backend's stored-value extraction
expression for that slot's own listed value, so the comparison is
scalar-vs-scalar.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an operand token `str` (one `%s`, possibly wrapped) | `List Char` | `s` (Python str) ↔ `s`-shaped `List Char`; `str` equality ↔ `List Char` equality |
| the RHS-template substitution `rhs % func` over the tuple of per-slot tokens | the list `clauseTokens` of per-slot tokens | each `%s` slot of the comma-joined template maps to one list element, in order; the gold hunk builds `func[i]` from `rhs_params[i]`, so slot `i`'s token is `slotToken` applied to slot `i`'s OWN value. The slots are **not** pinned to one another: on the vendor whose token construction reads the value (Oracle) two slots of one clause carry different tokens, and the model reproduces that pointwise (G-CONF asserts exact per-slot token equality on every branch, with no downgrade) |
| `rhs_params` (the listed values) | `List Int` | order-preserving, one `Int` identity per listed value. The identity is load-bearing, not opaque: it is the argument `wrapOf` is applied at, so the **count**, the **order**, and each element's **identity** all drive the emitted tokens. The same list is the second output component's domain — see the `rhs_params` note in §2.1. |
| the returned `rhs_params`: forwarded whole, or cleared whole | `out.2 : List Int` | `list(rhs_params) ↔ vals` and `() ↔ []`. The real code has exactly these two outcomes and no third: it never drops or reorders a subset, because the only assignment to `rhs_params` inside the hunk is `rhs_params = ()` at `json.py:396` (whole-clause, unconditional within its arm) and every other path returns the incoming list unchanged. So the Lean side is a two-way branch on `(native, wrapHoldsValue)`, not a filter over slots |
| which arm's expression form was taken | `wrapHoldsValue : Bool` | `connection.vendor == 'oracle'` (on the non-native path) `↔ true`; the MariaDB and `{sqlite, mysql}` arms `↔ false`. Read off the arm's STRUCTURE, not off the emitted bytes: `wrap_holds_value(vendor)` in conformance_check.py is the bijection image, and G-CONF fuzzes values whose own text contains `%s` precisely so the two readings are separated (they differ exactly there) |
| `connection.features.has_native_json_field` | `native : Bool` | `True ↔ true`; the gold hunk gates on `if not connection.features.has_native_json_field` (i.e. `native = false` is the wrapping branch) |
| the per-vendor, per-value operand-expression construction | the map `wrapOf : Int → List Char`, with `∀ v ∈ vals, wrapOf v ≠ bareTok` | the spec abstracts over WHICH construction a given non-native vendor uses (sqlite/mysql/mariadb/oracle all differ) by making it a MAP the caller supplies; the load-bearing properties are (i) each listed value's token is a real transformation of the bare placeholder (`wrapOf v ≠ bareTok`), and (ii) slot `i` carries the token of value `i` — so a value-dependent construction is representable and a uniformity claim is NOT made. Each vendor's concrete construction is the bijection image `wrap_of(vendor)` in conformance_check.py, which G-CONF compares byte for byte against the gold code (G-CONF) |

`List Char` (rather than `String`) is the carrier because the discriminating
predicate — "an operand token differs from the bare placeholder" — is a
per-character token equality, and `List Char` equality is total and sound.

### 2.1 What the model does NOT carry, stated rather than implied

* **The returned `rhs_params` is CARRIED, not excluded — and it is a BRANCH
  decision, not a per-slot one.** `process_rhs` returns a pair, and the modeled
  method returns a pair too: the token list AND the values that travel alongside
  it. Two earlier revisions of this bundle got this component wrong in opposite
  directions, and the current shape is what survives both:
  * The first declared it out of scope, reasoning that "forwarded unchanged" was
    behaviourally inert. It is NOT inert: on sqlite/mysql/mariadb — including the
    F2P vendor — the emitted token retains an inner `%s` that a forwarded value
    must fill, so the token list alone under-determines the emitted SQL, and an
    implementation emitting byte-identical tokens while dropping the values
    yields a statement with more placeholders than bindings.
  * The second carried it, but defined it as a FILTER over the slots: the values
    whose slot's emitted token still contains a `%s`. That is not what the real
    code computes. The hunk's only assignment to `rhs_params` is
    `rhs_params = ()` at `json.py:396`, which sits INSIDE the Oracle arm and
    AFTER its per-value loop: it is unconditional within the arm, applies to the
    whole clause, and reads no token. The two rules agree on every listed value
    whose own text contains no `%`, and part company as soon as one does — a
    listed value of `'100%sale'` produces the Oracle expression
    `JSON_VALUE('{"value": "100%sale"}', '$.value')`, which CONTAINS `%s` while
    leaving nothing to fill, so the filter returns that value and the real callee
    returns `()`. Measured on the real patched callee for
    `filter(value__c__in=['100%sale'])`, non-native, one vendor per row: on the
    Oracle arm `rhs = '(JSON_VALUE(\'{"value": "100%sale"}\', \'$.value\'))'`
    with real `rhs_params == []` — the emitted token carries `%s` and no value
    travels, so the byte-derived filter and the real callee disagree exactly
    here; on the `{sqlite, mysql}` arm `rhs = "(JSON_EXTRACT(%s, '$'))"` with
    real `rhs_params == ['"100%sale"']`, where the two rules happen to agree.
    The divergence is therefore on the value-holding arm, and it is that arm the
    modeled `wrapHoldsValue = true` branch predicts.
  The obligation is therefore `out.2 = clauseSuppliedValues native
  wrapHoldsValue vals`, a two-way branch — every value on the native
  short-circuit, none on the value-holding arm, every value on the arms that
  leave a place open — matching the real code's own structure.
  `conformance_check.py` compares this component EXACTLY against the gold
  `oracle_func_and_params` result on every enumerated configuration, with a fuzz
  pool that includes `%`- and `%s`-bearing values (bare, embedded, and nested)
  and a reported count of how many reached the value-holding arm, so the
  comparison cannot silently go blind again.
* **A non-native vendor the gold hunk does not enumerate.** The gold code assigns
  `func` only for `oracle`, mariadb, and `{sqlite, mysql}`; for any other
  non-native vendor `func` stays `()` and `rhs % func` raises `TypeError` on a
  non-empty clause. The modeled method is total, so that configuration is OUT OF
  SCOPE; `conformance_check.py` asserts it raises
  (`test_unenumerated_vendor_raises`) and excludes it from the differential,
  rather than comparing the model against an exception.
* **The empty clause.** `In.process_rhs` discards `None`s and raises
  `EmptyResultSet` when nothing is left (`lookups.py:370-378`), so the gold hunk
  is never reached with an empty `rhs_params` through the lookup path; measured on
  the real callee, `__in=[]` and `__in=[None]` both raise before the hunk runs.
  The modeled method accepts `vals = []` and returns `([], [])` there, which is
  the substitution's own value on an empty template — an input the real path
  cannot deliver rather than a divergence, and noted here rather than left
  implicit.
* **A carrier whose element is an expression, not a value.** If a listed element
  is a query expression (e.g. `F('id')`), `In.batch_process_rhs` compiles it into
  the template instead of emitting a `%s` for it, so the number of slots and the
  length of `rhs_params` come apart: measured on the real callee,
  `value__c__in=[F('id')]` yields `rhs = '("jsonapp_doc"."id")'` with
  `rhs_params == []`. The model's carrier is one value per slot (§2's
  order-preserving bijection), so that shape is OUT OF SCOPE of the bridge, not a
  claim the model makes and gets wrong. The F2P's inputs are plain values.
* **A subquery right-hand side.** If the right-hand side is a queryset rather than
  a list, `In.process_rhs` takes its else-branch (`lookups.py:388-390`) and the
  template handed on is the SUBQUERY's own SQL: every `%s` in it belongs to the
  subquery's parameters, not to an operand slot for a listed value. The hunk
  substitutes into THOSE. Measured on the real patched callee for a filtered
  subquery — template `'(SELECT U0."value" FROM t U0 WHERE U0."id" > %s)'` with
  the subquery's own params — the `{sqlite, mysql}` arm returns
  `'(SELECT U0."value" FROM t U0 WHERE U0."id" > JSON_EXTRACT(%s, \'$\'))'`, i.e.
  the subquery's comparison placeholder has been wrapped, and the Oracle arm
  raises `TypeError: the JSON object must be str, bytes or bytearray, not int` on
  a parameter that is not a JSON string; an unfiltered subquery carries no `%s`
  and passes through unchanged. The model's carrier is one value per slot, so
  there is no slot↔value bijection that maps this shape at all and it is OUT OF
  SCOPE exactly as the `F()` case is. Recorded because it is a latent defect of
  the gold patch itself, present in the real fixed code — upstream of the spec,
  and not a place the spec claims something false.

## 3. Callee provenance + flag dependencies

### 3.1 No consumed axiom, no A-reference deep model of an outside callee
`buildMembershipClause` models the changed operation itself (the per-slot
template substitution plus the accompanying-values decision). The three inputs it
abstracts over — the super-class RHS template's bare `%s` (`bareTok`), the
vendor's per-value operand-expression construction (`wrapOf`), and whether that
construction holds the value it was built for (`wrapHoldsValue`) — are **data
carried in as parameters**, not contracts about an unchanged callee that the proof
consumes. `wrapOf` being a `Int → List Char` parameter does not change that: it is
an ordinary total function supplied by the caller, universally quantified in the
contract, with no `ensures` attached to it — the proof assumes nothing about its
values beyond the stated `require`. `wrapHoldsValue` is likewise a plain `Bool`
input with no relation to `wrapOf` asserted in the `require`: the two are
INDEPENDENT in the contract, which is deliberate. Tying them (e.g. requiring
`wrapHoldsValue = true → ∀ v, bareTok is not a sublist of wrapOf v`) would be
false of the real code, since an Oracle expression built from a value whose text
contains `%s` holds the value AND contains the mark; the model would then exclude
a real input rather than predict it. There is therefore no `axiom` declaration and
no A-reference (so `axiom_check.py` / G-AX has no obligation; see §3.3).

The super-class `In.process_rhs` (`lookups.py:362`) is UNCHANGED by the patch and
supplies the bare-placeholder template; the patch's only edit is post-processing
that template (`rhs = rhs % func`). The spec captures exactly that
post-processing as `slotToken`/`clauseTokens` over the bare token, so no behavior
of `In.process_rhs` beyond "it yields a `%s` per slot" (a `bareTok` per `vals`
element) is relied on — and that is itself modeled as the input shape, not
assumed of a callee.

### 3.2 Flag / config dependencies (recorded for G-CONF)
The rewriting branch is gated on `connection.features.has_native_json_field`
(`native`). The specific per-value token construction depends additionally on
`connection.vendor` (`oracle` / `mysql`+`mysql_is_mariadb` / `{sqlite, mysql}`).
The spec abstracts that construction to the map `wrapOf`; conformance_check.py
exercises **every** enumerated vendor branch of the gold hunk (oracle, mariadb,
sqlite/mysql, and the native short-circuit) and compares the EXACT per-slot token
bytes on each — including the mixed-kind Oracle clauses where two slots differ —
so the abstraction is validated pointwise against each concrete construction with
no per-vendor downgrade. The accompanying-values component depends on the same two
configuration inputs and nothing else — `native`, and which arm the vendor selects
(`wrapHoldsValue`) — and is compared on the same configurations, which is what
pins the Oracle arm's whole-clause `rhs_params = ()` (`json.py:396`) against the
other arms' forwarding. Because that component is the one an earlier revision
derived from the emitted token bytes instead of the arm, conformance_check.py's
fuzz pool deliberately includes listed values whose own text carries `%s` (bare,
embedded, and nested in a list or dict) and REPORTS how many of them reached the
value-holding arm, failing if none did: those are exactly the inputs on which a
byte-derived rule and the real per-arm rule disagree. The unenumerated-vendor
configuration is out of scope and asserted to raise (§2.1).
The F2P test (`test_key_in`) runs on sqlite (the harness DB), i.e. the
`{sqlite, mysql}` branch with `native = false`.

### 3.3 G-AX
No `axiom_check.py` obligation exists: the bundle declares no `axiom` and no
A-reference deep model of an outside callee (meta.json `axioms: []`,
`deep_model_references: []`). G-AX is `skip` (gates.py `gate_ax`: "no
axiom_check.py").

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13346`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`clauseTokens` / `slotToken` (the per-slot `if native then bareTok else wrapOf v`
fold) to Python over the real `(rhs_template_string, rhs_params, native, vendor)`
carrier, with `wrap_of(vendor)` as the bijection image of `wrapOf`, and compares
against the gold-patched `KeyTransformIn.process_rhs` substitution
`rhs = rhs % func` transliterated VERBATIM from
`django/db/models/fields/json.py`, across all enumerated vendor/native
configurations over ≥10⁵ fuzzed inputs. The comparison is EXACT per-slot token
equality (count, order, and bytes) on every branch — no classification proxy and
no per-vendor downgrade — plus EXACT equality of the accompanying values
(`clauseSuppliedValues` vs the gold's returned `rhs_params`) on every branch, plus
a check that the modeled precondition holds at every real input. The fuzz pool
covers the F2P value kinds AND values whose own text carries the substitution
mark, which is the class that separates the modeled per-arm accompanying-values
rule from one read off the emitted token; the run reports how many such inputs
reached the value-holding arm and fails if none did. See conformance_check.py for
the oracle-choice rationale and the scope exclusions.
