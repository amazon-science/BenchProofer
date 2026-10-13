# mapping.md — django__django-15930

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 63884829acd207404f2a5c3cc1d6b4cd0a822b70`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assembleConditionalBranch (cond res : Compiled)` | `When.as_sql(self, compiler, connection, ...)` — `django/db/models/expressions.py:1297` (body 1299–1308) | the modeled changed function: assemble one branch of a conditional selection from its compiled condition + consequent |
| `Compiled` (`sql : List Char`, `params : List Int`) | the `(sql, params)` pair returned by `compiler.compile(node)` (`expressions.py:1301`, `:1305`) | a compiled SQL fragment: text + ordered bound params |
| `truePredicate` *(deep model — A-reference)* | `compiler.compile(Value(True))` (`expressions.py:1304`, gold post-patch) | the always-true predicate the empty-condition branch falls back to; its compiled form `("%s", [True])` is modeled as `{ sql := "%s".toList, params := [1] }`, validated == the real callee by axiom_check.py (G-AX) |
| `branchClause cond res` | the template splice `template % template_params` with `template = "WHEN %(condition)s THEN %(result)s"` (`expressions.py:1246`, `:1307`) plus the parameter concatenation (`sql_params.extend(condition_params)` then `... result_params`, `:1303`,`:1306`) | pure spec: the assembled branch text + params for a given condition/consequent |

The branch's `condition_sql` comes from `compiler.compile(self.condition)`
(`expressions.py:1301`). For the issue's `~Q(pk__in=[])` it is the **empty
string** `""`: `WhereNode.as_sql` returns `"", []` for a node that matches
everything (`django/db/models/sql/where.py:81-135`, the `full_needed == 0`
branch under a negated empty `pk__in=[]`). The pre-patch code splices that empty
string straight into the template, yielding `WHEN  THEN ...` — the
`syntax error at or near "THEN"` of the problem statement.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a compiled fragment text `sql : str` | `List Char` (`Compiled.sql`) | `s` (Python str) ↔ `s.toList`-shaped `List Char`; empty `str` `""` ↔ `[]`; `str` concat ↔ `List` `++` |
| the parameter list `params : list` | `List Int` (`Compiled.params`) | each bound parameter carried by an integer identity; ordered list ↔ `List Int`; `list.extend` ↔ `++`. The actual Python values are opaque to the assembly step (it only forwards them in order), so an integer identity per slot is a faithful order-preserving abstraction. |
| the literal `True` bound by `Value(True)` | the integer identity `1` | `Value(True).as_sql` returns `("%s", [True])`; `True` is carried by the single identity `1` in `truePredicate.params` |
| `compiler.compile(Value(True))` | `truePredicate = { sql := "%s".toList, params := [1] }` | the always-true placeholder fragment; **A-reference**, validated by G-AX |
| the template `"WHEN %(condition)s THEN %(result)s"` | the splice in `branchClause` | fixed string with two `%`-slots ↔ `"WHEN " ++ cond.sql ++ " THEN " ++ res.sql`. The two literal slots `condition`/`result` are filled in order; `extra_context`/`self.template` overrides are not exercised by the modeled call path (mapping.md §3). |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the predicate "the condition text is empty" is a per-byte
emptiness test (`cond.sql = []`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `truePredicate` deep model ↔ `compiler.compile(Value(True))` (A-reference)
**Callee:** `SQLCompiler.compile(Value(True))`, i.e. `Value.as_sql`
(`django/db/models/expressions.py:992-1008`). With the default boolean
`output_field` (`Value._resolve_output_field` returns `BooleanField()` for a
`bool` value, `expressions.py:1024-1025`) and no `get_placeholder`, `Value.as_sql`
falls through to `return "%s", [val]` where `val` is the adapted `True`. So
`compiler.compile(Value(True))` is the fragment text `"%s"` binding one
literal-true parameter — exactly `truePredicate = { sql := "%s".toList,
params := [1] }` (the literal carried by the integer identity `1`, §2). The
fragment is **non-empty**, which is the whole point of the fix: it gives the
branch a valid always-true predicate where the empty condition had none.

This is the changed operation, modeled **deeply** as concrete data (no
`axiom` the proof consumes); G-AX validates the data == the real callee.

### 3.2 The empty-condition trigger (context for G-AX, no consumed contract)
The condition that drives the new branch — a match-everything filter compiling
to `""` — is the real `WhereNode.as_sql` returning `"", []`
(`django/db/models/sql/where.py:126-135`). G-AX exercises this end-to-end by
compiling a real `When(~Q(pk__in=[]), then=...)` and asserting its condition
SQL is empty, and that the patched `When.as_sql` then emits the non-empty
always-true predicate (so the assembled branch is `WHEN %s THEN %s`, not the
broken `WHEN  THEN %s`). No contract on `WhereNode`/`Q` is consumed by the
proof; this leg only confirms the modeled trigger is real.

### 3.3 Flag / config dependencies
`When.as_sql` is called with the default `template=None` (so `self.template =
"WHEN %(condition)s THEN %(result)s"` is used) and `extra_context={}` on the
modeled path (`Case.as_sql` compiles each `When` via `compiler.compile`). The
two `%`-slots are filled positionally; no custom template or extra context is in
play for the F2P scenario. Recorded so G-AX/G-CONF fuzz the default configuration.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15930`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `branchClause` and the empty-condition substitution
(`if cond.sql = [] then truePredicate else cond`) to Python over the real
`(sql, params)` carrier, and compares against the gold-patched assembly line of
`When.as_sql` run on stand-in compiled fragments (the patched source line
transliterated; see conformance_check.py for the oracle choice rationale).
