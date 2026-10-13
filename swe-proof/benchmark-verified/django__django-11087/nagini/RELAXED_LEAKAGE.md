# Relaxed-leakage disposition — django__django-11087

This bundle takes the **relaxed-leakage** disposition. The policy lives in the
binding spec-construction rules, `prompts/nagini/spec_guide.md` directive 6
("**Exception — relaxed-leakage**"); the gate that honors it is
`src/swebench_unified/gates/leak.py`. (There is no `docs/RELAXED_LEAKAGE.md` in
this repo — an earlier revision of this file cited one, and that citation was
wrong.) The spec view names the gold's tested discriminator
— that the cascade SELECT fetches only the columns the deletion **consults**
UNLESS the related rows will be **exposed to observers** (a pre-/post-removal
observer is attached to that model), or the pending query already **requires the
whole row** — because this instance is a genuine `problem_statement` ↔ gold
MISMATCH and a *faithful* spec cannot avoid naming the gated exception.

## Identifier inventory of the spec view (the mechanical screen's surface)

`leakage.screen(model.py, nagini, patch.diff, problem_statement, test_patch)`
records **`passed=True`, 0 hard failures, 0 warnings**. Token scan of the
185-line spec view:

| token | count | note |
|---|---|---|
| `select_related` | **0** | see "the rename" below |
| `_has_signal_listeners`, `can_fast_delete`, `only(`, `defer`, `deferred`, `base_manager`, `queryset` | 0 | no repo identifier from the changed hunks |
| `signal`, `listener`, `pre_delete`, `post_delete`, `m2m_changed` | 0 | neutral "observer" / "exposed" vocabulary throughout |
| `fixed`, `copy`, `patch`, `bug` | 0 | G-LEAK's edit-narration vocabulary is absent |
| `collect` | 3 | all three are English: "the deletion **collect**or walks a relation", and twice "**sub-collection** of consulted columns". Not the repo symbol. |

The model's parameters are `all_fields`, `already_selected`, `referenced`, `pk`,
`whole_row_required`, `pre`, `post` — none of which is a verbatim identifier from
the gold diff.

### The rename, and why the strand could not simply be deleted

An earlier revision of this spec named the parameter `select_related`, which is a
**verbatim identifier from the gold diff line**
`if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):`
and does not occur in the `problem_statement` at all (token count 0). That is a
genuine leak of the discriminator's shape and it is now gone: the parameter is
`whole_row_required`, described functionally as the pending query already asking
for a whole row plus further relations, so no narrowing of it is attempted.

Dropping the strand rather than renaming it would **destroy faithfulness**:
with it dropped the abstraction becomes NON-FUNCTIONAL. Measured against the
real patched callee:

```
plain  R.objects.all()              6-coord input: all=[big,id,origin_id,uf]
select_related('origin')            6-coord input: all=[big,id,origin_id,uf]
   already_selected=[big,id,origin_id,uf]  referenced=[id]  pk=id  pre=F  post=F
   -- IDENTICAL on all six remaining coordinates --
REAL output, plain           : ['id']
REAL output, select_related  : ['big','id','origin_id','uf']
```

Two inputs equal on every remaining coordinate have different real outputs, so
**no** postcondition over the remaining inputs can predict the real callee: the
spec would necessarily be either unfaithful or vacuous on that class. Under the
repair rules that is a forbidden trade (weakening a postcondition until the
divergence is unobservable). The strand is load-bearing for faithfulness and can
only be renamed — which is what was done. This measurement is reproducible
from the instance image alone: apply `patch.diff` at `base_commit`, subclass
`Collector` overriding `related_objects` to return `super().related_objects(...)`
with and without `.select_related('origin')`, call `collect([origin])` under
`CaptureQueriesContext`, and read the cascade SELECT's column list. On a
4-column related model (`id`, `origin_id`, `unique_field`, `large_field`) with
`unique_field` the only consulted column, the plain pending query yields
`['id','unique_field']` and the `select_related` one yields all four columns,
with every other model coordinate held equal.

## Why faithful + non-leaking is impossible here (adversarial analysis)

Directive 6 judges leakage against the **solver-visible `problem_statement`
ONLY**, never `hints_text`, the gold internals, or the hidden `test_patch`.

**What the `problem_statement` actually says.** The public issue is titled
"Optimize `.delete()` to use only required fields." Its entire content is an
**unconditional** request: a `.delete()` triggered a `UnicodeDecodeError`
because the cascade SELECT fetched a `text_log_error.line` field "that is not
actually needed for the `.delete()` (it's not a primary key etc), so Django
shouldn't be fetching that field regardless when making the `text_log_error`
SELECT query." The desired behaviour is stated flatly as "use only required
fields" / "fetch only the fields it needs," with no conditioning on signals,
listeners, related-set eager fetching, or any per-model state. Token scan of the
`problem_statement`: `signal` 0, `has_listeners` 0, `pre_delete` 0, `post_delete`
0, `m2m_changed` 0, `listener` 0, `select_related` 0. The only `.only()` mention
is the workaround the reporter used in their own application code — not part of
the desired ORM behaviour and not the gold mechanism.

**What the gold actually does (the tested behaviour).** The gold patch on
`django/db/models/deletion.py` makes the reduction **conditional**. It adds a
helper `Collector._has_signal_listeners(model)` returning
`signals.pre_delete.has_listeners(model) or signals.post_delete.has_listeners(model)`,
and in `Collector.collect` reduces the cascade SELECT to the referenced fields
only when `not (sub_objs.query.select_related or self._has_signal_listeners(related_model))`;
otherwise it leaves the pending queryset alone (because a connected `pre_delete`/
`post_delete` receiver, or an eager `select_related`, will hand the rows to user
code, which may inspect any column). The sole FAIL_TO_PASS test,
`test_only_referenced_fields_selected (delete.tests.DeletionTests)`, pins exactly
this conditional: with no listeners attached the SELECT is reduced to the
referenced columns, but the test framework's own machinery and the P2P
fast-delete / signal tests require that when listeners ARE attached the full
column set is still fetched. An always-defer (unconditionally-reduce) impl —
which is precisely what the `problem_statement` literally asks for — would break
the listener path and the dependent P2P tests.

**Where the discriminator lives.** The gated exception — the
`pre_delete`/`post_delete` `has_listeners` disjunction, the deliberate exclusion
of `m2m_changed` for the single-valued-relation path, and the `select_related`
guard — appears ONLY in `hints_text` (`signal` ×10, `has_listeners` ×3,
`pre_delete` ×1, `post_delete` ×1, `m2m_changed` ×1, `listener` ×3) and the gold
diff / hidden `test_patch`. It is entirely absent from the `problem_statement`.

**The mismatch.** A spec that pins the gold behaviour (so the prepatch
pass-the-pending-queryset-on skeleton fails — G-DIFF — and no wrong impl,
including the always-defer impl the public text literally requests, verifies —
G-EQ) MUST encode the gated exception (`exposed_to_observers = pre or post`,
`m2m_changed` dropped, the whole-row guard). A spec restricted to the
`problem_statement` surface (the unconditional "fetch only required fields")
cannot reject the always-defer impl and therefore cannot be faithful. Hence
**faithful + non-leaking is provably impossible** — the public text (an
unconditional optimization request) and the gold fix (a conditional, gated
optimization) are about different things. This is the
directive-6 relaxation condition, not lazy de-narration: the docstring is
de-narrated to an abstract exposed-to-observers / consulted-columns contract,
and the one verbatim gold identifier that had survived (`select_related`) has
been renamed away; the residual "leak" is the conditional behaviour itself.

**What is NOT disclosed.** Three properties of the query layer that the spec
also pins — that a restricted fetch always retains the row identity, that naming
no column at all is a reset rather than a narrowing, and that with no request
made the pending query's own (possibly narrower) column set stands — are stated
as obligations about the *desired observable behaviour*, in the vocabulary of
column sets. They name no repo symbol, no source line, and no diff text, and
they are the kind of general query-layer fact a solver would have to establish
for themselves in any case. They are also not what distinguishes the fix from
the bug (the prepatch satisfies the third and is silent on the other two); the
discriminator remains the gated narrowing.

## Requirements satisfied (`prompts/nagini/spec_guide.md` directive 6)

1. **Core is sound.** Gate verdicts as recorded by the gate runner (see
   `meta.json` `gates`), not as self-assessed. The prepatch twin is
   spec-byte-identical and fails the postcondition
   `Implies(not whole_row_required and not exposed_to_observers(pre, post)
   and len(referenced) > 0 and Exists(k: referenced[k] == pk),
   ToSeq(Result()) == ToSeq(referenced))`
   of `select_cascade_fields` — the pass-the-pending-queryset-on skeleton returns
   `already_selected`, the spec requires `referenced`. G-EQ: every refinement
   step is R / I / A-reference, no kind-3 — both changed ops are modeled deeply;
   the discriminator is grounded in the input carriers as the structural value
   relations `ToSeq(Result()) == ToSeq(referenced)` vs `== ToSeq(all_fields)` vs
   `== ToSeq(already_selected)`, not an opaque oracle (directive 8). G-AX: zero
   `@ContractOnly` axioms; two A-reference deep models validated by
   `axiom_check.py` against real `django.db.models.signals` has_listeners cycles
   and a mirror of the real deferred-loading semantics that is itself
   cross-validated against the real SQL compiler on all 528 (pending state ×
   requested set) pairs. G-RESOLVE: `patch.diff` == gold verbatim, applies
   cleanly at `base_commit`.
2. **The leak is genuinely unavoidable**, established by the adversarial
   analysis above: the gold's tested discriminator (the gated exception —
   `pre_delete`/`post_delete` `has_listeners`, `m2m_changed` excluded, the
   whole-row guard) is demonstrably absent from `problem_statement` (an
   unconditional "use only required fields" optimization request) and present
   only in `hints_text` / gold / `test_patch`; no PS-derivable reformulation
   models the gold fix (the PS-surface behaviour — unconditional reduction —
   would break the listener path and the dependent P2P tests). The narrower
   question of whether the *whole-row strand specifically* could be dropped was
   tested rather than argued, and answered no: dropping it makes the abstraction
   non-functional (measurement above).
3. **Documented in-bundle and registered.** This file, plus the top-level
   `relaxed_leakage: true` flag in `meta.json` — which is the condition
   `gates/leak.py` and `construct/build_one.py::_leakage_relaxed` actually read,
   and which makes the G-LEAK gate record `status = "relaxed"` rather than a
   misleading "spec view clean" pass. There is no repo-level scope list to
   append to; the registration IS the flag plus this file.
