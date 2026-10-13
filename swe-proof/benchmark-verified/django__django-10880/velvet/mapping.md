# mapping.md — django__django-10880

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 838e432e3e5519c5383d12018e6c78f8ec7833c1`, states the type
abstraction (the Lean↔Python bijection G-CONF and G-AX use to bridge values),
and gives the provenance of the deep-model reference.

Repo file under change: `django/db/models/aggregates.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `aggregateAsSql (function distinct expressions)` | `Aggregate.as_sql` — `django/db/models/aggregates.py:70` | the modeled changed method (renders an aggregate SQL call) |
| `distinctQualifier (distinct : Bool)` | `extra_context['distinct'] = … if self.distinct else ''` — `django/db/models/aggregates.py:71` | pure spec: the leading qualifier text placed before the argument list |
| `renderCall (function distinct expressions)` *(deep model — A-reference)* | `Func.as_sql`'s template substitution `template % data` with `template = '%(function)s(%(distinct)s%(expressions)s)'` — `django/db/models/expressions.py` (`Func.as_sql`), template at `aggregates.py:17` | pure spec: the rendered call string; deep model of the unchanged generic renderer, validated `renderCall == real renderer` by axiom_check.py (G-AX) |

The modeled method's argument carriers correspond to the three template
placeholders the renderer consumes for the no-filter path:
- `function` ↔ `data['function']` (the class attribute `function`, e.g. `'COUNT'`),
- `distinct` ↔ the truth of `self.distinct` (whether the aggregate deduplicates),
- `expressions` ↔ `data['expressions']` (the rendered, comma-joined argument SQL).

## 2. Scope of the model (why `as_sql` reduces to `renderCall`)

`Aggregate.as_sql` sets `extra_context['distinct']` and then, for an aggregate
with **no `filter`** (`self.filter` falsy), delegates to `super().as_sql(...)`
(`Func.as_sql`), which performs `template % data` with the class template
`'%(function)s(%(distinct)s%(expressions)s)'`. The F2P input
(`Count(Case(When(...)), distinct=True)`) has `filter=None`, so this is exactly
the path under test. The two `filter`-branch sub-paths
(`supports_aggregate_filter_clause` true/false) only wrap/transform the
expressions and then call the SAME renderer; they do not alter the distinct
qualifier's content. The modeled behavior — the qualifier text and its placement
in the template — is therefore the full content of the change for every path.
(`check_expression_support`, `compiler.compile` of arguments, and `mark_safe`
have no effect on the distinct-qualifier behavior the F2P test observes; see §3.)

## 3. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement relies on).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the rendered SQL fragment (`str`: `function`, `expressions`, and the `as_sql` result string) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single SQL character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `self.distinct` truthiness | Lean `Bool` | a Python truthy `self.distinct` ↔ `true`; falsy ↔ `false`. The aggregate sets `self.distinct` to the `bool` `distinct` ctor arg (`aggregates.py:27`). |
| string interpolation `template % {'function':f,'distinct':q,'expressions':e}` over template `'%(function)s(%(distinct)s%(expressions)s)'` | `renderCall f distinct e = f ++ ['('] ++ distinctQualifier distinct ++ e ++ [')']` | placeholder-by-placeholder: `%(function)s ↔ f`, literal `(` ↔ `['(']`, `%(distinct)s ↔ distinctQualifier distinct`, `%(expressions)s ↔ e`, literal `)` ↔ `[')']` |

`String`/`List Char` indexing in Lean is total and sound; the carrier is
`List Char` because the operation is a per-character string concatenation.

## 3.1 `renderCall` deep model ↔ the generic renderer (A-reference)

**Callee:** `Func.as_sql`'s final line `return template % data, params`, with the
`Aggregate.template = '%(function)s(%(distinct)s%(expressions)s)'`. This generic
renderer is **unchanged** by the patch; only the *value* placed in
`data['distinct']` changes. The renderer is modeled **deeply** by `renderCall`
(no consumed `renderCall` axiom): substituting the three named placeholders into
the fixed template is exactly the ordered concatenation
`function ++ "(" ++ distinct-qualifier ++ expressions ++ ")"`. G-AX
(`axiom_check.py`) drives the real `Aggregate`/`Func` renderer on boundary +
fuzzed `(function, distinct, expressions)` triples and asserts the real rendered
string equals `renderCall` under the §3 bijection. Exit 0 iff sound.

The **changed** operation — the qualifier text `distinctQualifier` — is NOT
axiomatized: it is the spelled-out `if distinct then "DISTINCT " else ""`
(`distinctQualifier`), the I/R-tagged content G-CONF transliterates and
differential-tests against the patched `as_sql`. The discriminator is the
trailing separator after `DISTINCT`: `distinct=True ⇒ "DISTINCT "` (with the
separator) vs the pre-patch `"DISTINCT"` (no separator), which glued the keyword
onto the argument text (`DISTINCTCASE …`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10880`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `distinctQualifier`/`renderCall` (R/I-tagged ops) to Python and
compares against the real patched `Aggregate.as_sql` (the oracle, driven with a
stub compiler/connection over the no-filter path of §2).
