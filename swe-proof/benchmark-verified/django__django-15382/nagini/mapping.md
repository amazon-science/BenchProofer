# mapping.md — django__django-15382

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 770d3e6a4ce8e0a91a9e27156036c1985e74d4a3`, states the type
abstraction, and gives the provenance of the one consumed axiom (callee source +
the exact behaviour the axiom encodes).

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_exists(satisfiable, negated)` | `Exists.as_sql(self, compiler, connection, template=None, **extra_context)` — `django/db/models/expressions.py:1212` (class `Exists`, line 1199) | the modeled changed function (renders a negatable EXISTS predicate to SQL) |
| `render_inner(satisfiable)` *(axiom — A-consumed)* | `Subquery.as_sql` — `django/db/models/expressions.py:1178`, invoked from `Exists.as_sql` as `super().as_sql(compiler, connection, template=template, query=query, **extra_context)` (lines 1214–1220) | the UNCHANGED super-class sub-selection renderer the predicate renderer calls |
| `inner_fragment(satisfiable)` *(axiom — A-consumed, `@Pure`)* | the CONTENT (`str` value) of the SQL fragment returned by that same `Subquery.as_sql` super-call on a satisfiable inner selection | `@Pure` companion of `render_inner`; names the renderer's satisfiable output as a pure function of the input so the predicate renderer's satisfiable postcondition can pin `Result()` to it (directive 8 grounding). Not the function under change. |
| `EmptyResultSet` (model exception class) | `django.core.exceptions.EmptyResultSet` — imported at `expressions.py:8`; raised during compilation of an unsatisfiable inner query | the "matches-nothing" signal |
| `not_prefix()` | the literal `'NOT '` in `sql = 'NOT {}'.format(sql)` (`expressions.py:1222`) | pure spec: the negation marker as code points |
| `satisfiable` (parameter, {0,1}) | whether `self.query.exists(using=...).as_sql(...)` compiles to SQL (1) or raises `EmptyResultSet` (0). An empty queryset (`.none()`) attaches a `NothingNode` whose `as_sql` raises `EmptyResultSet` (`django/db/models/sql/where.py:228-233`) | abstract input: inner-selection satisfiability |
| `negated` (parameter, {0,1}) | `self.negated` — set in `Exists.__init__` (line 1204) and flipped by `__invert__` (line 1209) | abstract input: the predicate's negation flag |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): `Exists.as_sql` called
`super().as_sql(...)` **without** guarding `EmptyResultSet`, so an unsatisfiable
inner selection propagated the signal unconditionally — including the negated
case, where the predicate is universally true and the signal then erased the
surrounding WHERE condition (the issue's `EmptyResultSet` print).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the returned SQL text fragment (a `str`) | `List[int]` of code points; specification over `PSeq[int]` via `ToSeq` | `s[k]` ↔ `sql[k] == ord(s[k])`; `len`/`+`/slice/`take` mirror `str` `len`/`+`/slice/prefix; the empty `str` `''` ↔ `[]` (`len == 0`) |
| the `(sql, params)` 2-tuple `Exists.as_sql` returns | only the `sql` component is modeled (`List[int]`); `params` is unobserved by the F2P behaviour | the F2P test observes the result rows (WHERE semantics), which depend on the SQL-fragment SHAPE: empty fragment ⇒ "matches everything"; non-empty ⇒ a real predicate. The discriminating observable is empty-vs-non-empty + the `NOT` prefix, all carried by `sql`. |
| `self.negated` (a `bool`) | `negated: int` ∈ {0,1} | `True` ↔ 1, `False` ↔ 0 |
| inner-query satisfiability (a runtime property: does compilation raise `EmptyResultSet`?) | `satisfiable: int` ∈ {0,1} | unsatisfiable (raises) ↔ 0; satisfiable (returns SQL) ↔ 1 |
| `'NOT {}'.format(sql)` (str prefixing) | `[78,79,84,32] + sql` (list prepend of `'NOT '` code points) | `'NOT ' + sql` ↔ `not_prefix() ++ ToSeq(sql)` |
| `EmptyResultSet` (builtin/Django exception) | user-defined `EmptyResultSet(Exception)` | observationally the same raise; a builtin/library exception in an `Exsures` crashes the Nagini translator, so a user-defined stand-in is used (SPEC_GUIDE §2) |

`str` indexing/iteration is banned in Nagini, so the SQL carrier is `List[int]`;
the spec's prefix relation is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `render_inner` ↔ `Subquery.as_sql` (A-consumed)
**Callee:** `Subquery.as_sql(self, compiler, connection, template=None, query=None, **extra_context)`
(`django/db/models/expressions.py:1178`). `Exists.as_sql` invokes it as
`super().as_sql(..., query=self.query.exists(using=connection.alias), ...)`.
Internally it calls `query.as_sql(compiler, connection)` (line 1182). For an
**unsatisfiable** inner query — e.g. one built from `QuerySet.none()`, which
attaches a `NothingNode` (`django/db/models/sql/where.py:228-233`) whose
`as_sql` does `raise EmptyResultSet` — that compilation raises `EmptyResultSet`,
which `Subquery.as_sql` propagates. For a **satisfiable** inner query it returns
a non-empty `EXISTS(...)`-template SQL fragment.

The axiom encodes only the obligations the predicate renderer relies on (the
**weakest** sufficient contract):

  * `satisfiable == 1` ⇒ returns (full ownership) the fragment whose CONTENT is
    `inner_fragment(satisfiable)` — a non-empty fragment that does not itself
    begin with the negation marker;
  * `satisfiable == 0` ⇒ raises `EmptyResultSet`.

`inner_fragment(satisfiable) -> PSeq[int]` (the `@Pure` companion) names that
satisfiable content as a pure function of the input. Its only encoded properties
are the weakest the proof needs: non-empty, and not itself NOT-prefixed. It is
the SAME real callee output viewed as a value (not a separate callee, not an
answer-key oracle — its value is opaque, with no hardcoded table). Its purpose is
directive-8 grounding: the predicate renderer's satisfiable postcondition pins
`ToSeq(Result()) == inner_fragment(...)` (and `not_prefix() + inner_fragment(...)`
when negated), so the only way to discharge it is to actually return
`render_inner`'s output — a fabricated fragment cannot satisfy it.

This is an UNCHANGED callee (the patch touches only `Exists.as_sql`, never
`Subquery.as_sql` nor the `EmptyResultSet`-raising path). It is the function the
changed code CALLS, so it is correctly axiomatized rather than re-implemented.

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory Django and
runs the REAL `Subquery.as_sql` exactly as `Exists.as_sql` invokes it, on a
satisfiable inner selection (`User.objects.all()`) and an unsatisfiable one
(`User.objects.none()`), asserting: satisfiable ⇒ no raise + non-empty SQL;
unsatisfiable ⇒ raises `EmptyResultSet` (which also validates `inner_fragment`'s
non-empty + not-NOT-prefixed properties on the satisfiable path). It additionally
drives the post-patch `Exists.as_sql` itself over all four `(satisfiable,
negated)` combinations and asserts the model's case table, crucially that
`sat=0, neg=1` RETURNS NORMALLY (does not propagate the signal) AND yields the
EMPTY fragment (`sql == ''`) — matching the spec clause
`Ensures(Implies(satisfiable == 0 and negated == 1, len(Result()) == 0))`. The
empty fragment is the discriminating, grounded behaviour: it contributes no
restriction, so `~Exists(empty)` matches every row and the F2P result-set equality
holds; a non-empty fragment there (always-false or junk) would change the observed
rows and NOT resolve. `patch.diff == gold` returns `''`, so the assertion is exact.
Verified against the real 4.1 source (gold-patched): all assertions pass; against
the un-patched source the `sat=0, neg=1` case raises `EmptyResultSet` (the bug). It
imports only Django (the very package under change) + stdlib; exit 0 iff sound. Run
in-container at the instance's pinned version (4.1), with the gold patch applied
for the post-patch case checks.
