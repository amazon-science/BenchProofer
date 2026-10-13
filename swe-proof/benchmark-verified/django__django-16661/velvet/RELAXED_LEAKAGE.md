# RELAXED_LEAKAGE — django__django-16661

Disposition: **KEEP with relaxed leakage** (per `RELAXED_LEAKAGE.md`).
`meta.json gates.G-LEAK.status = "relaxed"`.

This file is the second-round recovery disposition. Round 1 attempted plain
de-narration (option (a): re-express the spec in `problem_statement`-public
vocabulary). It failed the blind re-audit because the gold's load-bearing
discriminator is **PS-inexpressible**: the spec STRUCTURE that any *faithful*
spec must carry still discloses behavior absent from the public issue. The
correct disposition is therefore option (b): a documented, unavoidable leak.

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). Velvet precedents with the
same disposition: django__django-10999, django__django-11141,
django__django-11265, django__django-13023, matplotlib__matplotlib-26208,
scikit-learn__scikit-learn-14983, sphinx-doc__sphinx-8265.

## The modeled slice

`ModelAdmin.lookup_allowed` walks the `LOOKUP_SEP`-split lookup path and, per
segment, decides whether to `relation_parts.append(part)` (record it as a real
relational descent). The bundle models this per-segment keep decision as
`keptSegments : List Hop → List Bool`, pinning the output to `keepMask hops`,
where `keepSegment` is the post-gold append guard transliterated over the
per-segment introspection facts. The gold patch changes ONLY this guard:

```python
# pre  (base_commit):
if not prev_field or (prev_field.is_relation
        and field not in prev_field.path_infos[-1].target_fields):
# gold (post-patch):
if not prev_field or (prev_field.is_relation
        and field not in model._meta.parents.values()
        and field is not model._meta.auto_field
        and (model._meta.auto_field is None
             or part not in getattr(prev_field, "to_fields", []))):
    relation_parts.append(part)
```

## The problem_statement ↔ gold mismatch

The public `problem_statement` reports ONE symptom and offers ONE diagnosis:
`lookup_allowed('restaurant__place__country')` wrongly raises
`DisallowedModelAdminLookup` "with foreign key as primary key", because the admin
"think[s] that having a foreign key field as a primary key is the same as concrete
inheritance" and so "shortcuts it to restaurant__country". Its sole assertion is
`self.assertIs(ma.lookup_allowed('restaurant__place__country', 'test_value'), True)`.
`hints_text` is a single bisect commit hash — no mechanism at all.

The public diagnosis maps cleanly to exactly ONE of the gold guard's clauses —
the concrete-inheritance-parent-link clause `field not in
model._meta.parents.values()` (`Hop.concreteParentLink`). PS tokens: `concrete`×2,
`inheritance`×1, `foreign key`×2, `primary key`×2, `shortcut`×1. That clause does
not leak.

The gold guard adds TWO further, coupled discriminators that the public text never
mentions:

| gold clause | Lean flag | role |
|---|---|---|
| `field is not model._meta.auto_field` | `redundantLocalValue` | drop the auto-generated PK segment ("found from local model anyway") |
| `(model._meta.auto_field is None or part not in getattr(prev_field, "to_fields", []))` | `hasRedundantLocalValue` / `priorAlreadyCovers` | per-record auto-PK gate × prior-relation `to_fields` membership |

### Token scan (verified against `instance.json`)

Every discriminating token of the two extra clauses is **absent from BOTH
`problem_statement` AND `hints_text`** (counts are literal substring counts over
the lowercased fields):

| token | `problem_statement` | `hints_text` |
|---|---|---|
| `auto_field`, `auto-generated`, `automatic`, `identity` | **0** | **0** |
| `to_fields`, `target_fields`, `referenced` | **0** | **0** |
| `redundant`, `redundancy`, `found from`, `local model`, `found already`, `anyway` | **0** | **0** |
| `__id`, `id__exact`, `exact` | **0** | **0** |
| `parents.values`, `_meta`, `prev_field`, `is_relation` | **0** | **0** |

The "value would be found from the local model anyway" redundancy rationale
appears ONLY in the gold-**removed** code comment (deleted by the patch — see the
`-` lines), not in the public issue.

## Why a faithful + PS-only spec is provably impossible

A faithful spec must (i) reject the prepatch (G-DIFF) and (ii) reproduce the gold
per-segment keep decision on every shape the F2P test exercises. I drove the real
post-gold `lookup_allowed` in-container (eval image
`sweb.eval.x86_64.django_1776_django-16661`, both `patch.diff` + hidden
`test_patch` applied; the F2P passes `OK`) and recorded the per-segment facts and
keep flags for all three F2P assertions:

```
lookup restaurant__place__country               keep: restaurant=1 place=1 country=1            -> True
lookup restaurant__place__country__id__exact     keep: restaurant=1 place=1 country=1 id=0       -> True
lookup restaurant__place__country__name          keep: restaurant=1 place=1 country=1 name=1     -> True
```

Two facts make the leak unavoidable:

1. **The publicly-described fix (keep `place`) IS PS-expressible.** The sole
   gold-vs-prepatch divergence on the public lookup is at the `place` segment
   (a `OneToOneField(primary_key=True)` — a FK that is the record's own PK,
   reached through a relation): prepatch drops it (`field in
   prev_field.path_infos[-1].target_fields` ⇒ `targetOfPrior=1`), gold keeps it.
   That FK-as-PK-vs-concrete-inheritance distinction is literally the PS text.

2. **The auto-field drop (drop `id`) is REQUIRED by the F2P yet PS-inexpressible.**
   In the second F2P assertion, `restaurant__place__country__id__exact`, the gold
   guard **drops** the `id` segment because `id` IS Country's auto PK
   (`field is model._meta.auto_field` ⇒ `redundantLocalValue=1`). With `id`
   dropped, `relation_parts = ['restaurant','place','country']`, whose
   `LOOKUP_SEP.join` is `restaurant__place__country` ∈ `list_filter` ⇒
   `lookup_allowed` returns **True** (test passes). A spec that knows only the
   PS-public concepts (first segment / prior-is-relation / concrete-parent link)
   has no way to drop `id` — `id` is reached via a relation and is not a
   concrete-parent link — so it **keeps** `id`, giving
   `relation_parts = ['restaurant','place','country','id']` whose join is NOT in
   `list_filter` ⇒ `lookup_allowed` returns **False** ⇒ **the F2P fails**.
   (Verified by direct simulation of the downstream
   `len(relation_parts) <= 1` / `LOOKUP_SEP.join(...)` membership logic on both
   masks.)

Therefore the auto-field redundancy discriminator is simultaneously
**load-bearing for the F2P** and **absent from the public text**. No
`problem_statement`-derivable reformulation can both pass the F2P and reject the
prepatch: the only PS-derivable keep rule ("keep unless a concrete-inheritance
parent link") fails the `id__exact` assertion. Faithful + non-leaking is
impossible — not because of a weak spec or a verifier-fragment wall, but because
the public task text and the gold fix discriminate on different things.

### Why round-1 de-narration could not fix it (structural, not lexical, leak)

Round 1 renamed the leaking flags to opaque names
(`redundantLocalValue`/`hasRedundantLocalValue`/`priorAlreadyCovers`) and deleted
the bug→fix narration — removing every *lexical* leak (0 hits for
auto/to_fields/referenced/_meta/parents in the spec view). The re-audit still
found LEAKAGE because the leak is **structural**: to be faithful, `keepSegment`
must spell out the auto-field-drop discriminator (and, to pin gold exactly, the
`to_fields` disjunction) — i.e. a redundancy condition beyond the single
PS-justified `concreteParentLink`. That extra arity and the disjunctive
sub-structure `(!hasRedundantLocalValue || !priorAlreadyCovers)` are
PS-inexpressible regardless of naming. You cannot rename your way out of a
discriminator the public text does not contain. The bundle's error was not the
naming; it was **claiming a clean NO-LEAKAGE pass** for an irreducible leak. This
file + the `relaxed` status correct that.

## Requirements check (RELAXED_LEAKAGE.md)

1. **Core is sound.**
   - **G-VERIFY pass**: `Solution.lean` verifies clean (`lean_verify.sh` exit 0,
     ~2s).
   - **G-DIFF fail**: `Solution_prepatch.lean` (old `targetOfPrior` rule) fails
     verification (exit 1) on exactly the discriminating goal
     `(isFirst || (priorIsRelation && !targetOfPrior)) = keepSegment h`, which is
     unprovable on the FK-as-PK `place` shape (`priorIsRelation=1,
     concreteParentLink=0, redundantLocalValue=0, hasRedundantLocalValue=0,
     priorAlreadyCovers=1, targetOfPrior=1`): prepatch=drop, gold=keep — the bug→fix
     delta the F2P pins. `same_spec(Solution, Solution_prepatch) = True`, so G-DIFF
     is a genuine spec-discrimination test.
   - **G-EQ SOUND + TIGHT**: spec is the exact functional equality
     `out = keepMask hops`; the prepatch bug + ≥6 plausible wrong impls are all
     rejected by the per-segment `keepSegment` obligation; positive control
     (structurally-different correct impl) verifies ⇒ non-vacuous.
   - **directive 8 (no ungrounded oracle)**: `keepSegment`/`keepMask` are concrete
     frozen `def`s over the input `Hop` facts — a total computable function of the
     inputs, no axiomatized answer-key to echo.
   - **G-AX VACUOUS**: `axioms: []`, no `axiom_check.py`; the only changed thing
     (the Boolean combination) is modeled DEEPLY, not axiomatized. Every `Hop`
     field is an UNCHANGED Django introspection fact used read-only (R input).
   - **faithfulness FAITHFUL**: in-container trace confirms the real post-gold
     per-segment keep equals Lean `keepSegment` on every segment of all three F2P
     lookups, including the discriminating `place` (kept) and `id` (dropped); the
     spec pins the full positional mask (≥ the projected `relation_parts`) and
     equals exactly what the gold code produces — not too weak, not too strong.
   - **G-CONF pass**: the R/I shadow (`keepSegment` + backward fold) agrees with the
     independently-transcribed `patch.diff` append guard on all 128 single-`Hop`
     configs + 100131 fuzzed paths (seed 16661), 0 disagreements.
   - **G-RESOLVE**: `patch.diff` == gold verbatim, harness reports `resolved`.
2. **The leak is genuinely unavoidable**, established above by (a) the token scan
   showing the auto-field/`to_fields` discriminators absent from BOTH
   `problem_statement` and `hints_text`, and (b) the in-container F2P trace + the
   downstream-logic simulation proving the auto-field drop is load-bearing for the
   `id__exact` assertion and cannot be produced by any PS-public keep rule. This is
   not lazy de-narration: the behavior itself — dropping a relation-reached segment
   because it is the related record's auto-generated PK — is the leak.
3. **Documented in-bundle** (this file); `meta.json gates.G-LEAK.status =
   "relaxed"` points here. The mechanical lexical G-LEAK screen still passes (the
   spec view names no patched path/symbol and uses only abstract behavioral
   vocabulary — `isFirst`, `priorIsRelation`, `concreteParentLink`,
   `redundantLocalValue`, `hasRedundantLocalValue`, `priorAlreadyCovers`); the leak
   is semantic/structural, as the policy expects. The repo provenance of every flag
   lives in `mapping.md`, not the spec view.

## Scope of what is disclosed

The spec view discloses: a walked lookup path records each segment as a real
descent unless it is locally redundant, where redundancy holds when the segment is
a concrete-inheritance parent link (PS-public) OR one of two further opaque
per-segment/per-record redundancy conditions holds (the relaxed disclosure — the
auto-PK-drop arity and the disjunctive `(!hasRedundantLocalValue ||
!priorAlreadyCovers)` sub-structure). Nothing about the patched file
(`django/contrib/admin/options.py`), the `lookup_allowed` / `relation_parts`
symbols, `model._meta.auto_field`, `getattr(prev_field, "to_fields", [])`,
`model._meta.parents.values()`, or the gold-removed "found from local model"
comment is named in the spec view; those live in `mapping.md` /
`conformance_check.py`.
