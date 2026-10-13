# refinement.md — django__django-12965

Maps every operation in `implementation_isSingleTableDelete` to its `patch.diff`
counterpart in `SQLDeleteCompiler.single_alias`
(django/db/models/sql/compiler.py:1408-1411). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** op left as the real repo
callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch `single_alias`)
```python
class SQLDeleteCompiler(SQLCompiler):
    @cached_property
    def single_alias(self):
        # Ensure base table is in aliases.
        self.query.get_initial_alias()
        return sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1
```

The added line `self.query.get_initial_alias()` mutates the query so its primary
table is recorded among the referenced tables BEFORE the count. Everything else
is the pre-existing count-active-tables-and-compare-to-one expression.

## Modeling decision
The observable behavior of `single_alias` is a single boolean. Its only inputs are
the query's table references and their reference counts; the table *names* are
irrelevant to the boolean (they serve only as dict keys), so the query is modeled
as `refs : List Nat` — the reference counts in `alias_map` insertion order
(insertion order matters solely because `get_initial_alias`'s non-empty branch
increments the FIRST-recorded reference).

`get_initial_alias` is an UNCHANGED callee that the fix newly invokes. Rather than
axiomatize it, it is modeled DEEPLY by `includePrimary`, capturing exactly its
effect on the reference-count multiset (empty ⇒ add a fresh count-1 reference;
non-empty ⇒ bump the first reference). This deep model is validated == the real
callee by G-CONF (A-reference), so it is NOT a consumed axiom.

## Operation correspondence
| # | Lean op (`implementation_isSingleTableDelete`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let refs := includePrimary refs` | `self.query.get_initial_alias()` (the added line) | A-reference | deep model of the unchanged `get_initial_alias` callee, restricted to its effect on the reference-count multiset (empty ⇒ `[1]`; `c::rest` ⇒ `(c+1)::rest`). Left abstract-as-modeled and bound to the REAL `get_initial_alias` in G-CONF; no property consumed ⇒ NOT an `axiom` (not A-consumed) and NOT axiomatized. |
| 2 | `let mut active := 0; for c in refs do if c > 0 then active := active + 1` | `sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map)` | R | counting references with positive reference count. `int ≥ 0 ↔ Nat`; the generator-sum over the dict ↔ the `for`-accumulator over `refs : List Nat`; `alias_refcount[t] > 0 ↔ c > 0`. |
| 3 | `return active == 1` | `... == 1` | I | compare the active count to one; `bool ↔ Bool`. |

## R/I + A-reference legs ⇒ G-CONF
Op 1 (the A-reference `includePrimary`) is bound to the REAL `get_initial_alias`
in G-CONF; ops 2,3 (R count + I compare) are the R/I content. `conf_skip = false`:
the impl region has genuine R/I content (counting + comparison), so
`conformance_check.py` differential-tests the shadow (`includePrimary` then
count-active==1) against the REAL patched `SQLDeleteCompiler.single_alias` over
≥10^5 fuzzed reference-count configurations (including the empty / full-table case,
which is the discriminating one).

## No A-consumed row
The proof consumes no property of an opaque callee (`includePrimary` is a concrete
`def`, unfolded by the proof). So `meta.json axioms = []`; op 1 is recorded as an
A-reference solely to document the G-CONF binding to the real `get_initial_alias`.
There is no `opaque`/`axiom` declaration in `Solution.lean`, and `axiom_check.py`
is a skip stub.

## F2P alignment
`test_fast_delete_all` runs `User.objects.all().delete()` and asserts exactly one
query whose SQL contains no `SELECT` subquery. For a full-table delete the query
has recorded no table references (`alias_map` empty), so pre-patch the active count
is `0`, `single_alias` is `False`, and `as_sql` emits the
`DELETE … WHERE pk IN (SELECT …)` subquery — failing the test. The discriminating
clause `problem_spec_isSingleTableDelete` pins (`refs = []` ⇒ after `includePrimary`
the active count is `1` ⇒ `true`); the prepatch impl (folds over `refs` directly,
omitting `includePrimary`) gives `false` on `refs = []` and so cannot satisfy the
spec — its carried gold proof fails to typecheck (G-DIFF). `patch.diff` (gold
verbatim) makes the harness resolve.
