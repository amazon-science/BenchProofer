# properties.py — G-PBT falsification battery for django__django-14122 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   getGroupBy (metaOrdering : Bool) (gb : GroupBy)
#              (select orderBy : List (Bool × List Col)) (having : List Col)
#     -> List Col
#   The accumulated grouping columns, fully pinned to the inputs by the single
#   postcondition clause `result = groupByExpressions metaOrdering gb select orderBy
#   having`. That oracle is a total, transparent fold over the inputs (no opaque
#   callee, no answer-key), so `decide` computes it at any literal input — witnesses
#   need no conditioning on the carrier.
#
# Although the postcondition is a single equality, groupByExpressions pins several
# INDEPENDENT sub-behaviours, each attackable one at a time:
#   (C0) empty-source short-circuit: an empty grouping source yields [] regardless
#        of the other phases;
#   (C1) explicit seed: an explicit caller-supplied grouping set contributes its
#        columns first;
#   (C2) selected-expression filter: a selected entry already covered by a reference
#        contributes NOTHING, otherwise its columns, in order;
#   (C3) DISCRIMINATING ordering gate: the ordering columns are added ONLY when the
#        ordering is an explicit request (metaOrdering = false) — an implicit default
#        (metaOrdering = true) must contribute nothing. This is the load-bearing
#        clause the F2P demands;
#   (C4) ordering-entry filter: within the ordering phase, an entry that merely
#        references the selected columns contributes nothing, otherwise its columns;
#   (C5) filter columns: the post-aggregation filter columns come last.
#
# Two further sub-behaviours the accumulation pins, added after audit because no rival
# above could observe them (each existing witness makes ONE phase non-empty with
# pairwise-distinct column identities, which is blind to both):
#   (C6) PHASE ORDER: the phases are concatenated in a fixed sequence, so a rival that
#        emits the right multiset in the wrong order must still be rejected;
#   (C7) MULTIPLICITY: the modeled value is the accumulated list BEFORE the separate
#        de-duplication pass, so repeats are preserved and an eager de-dup is wrong.
#   (C8) INTRA-PHASE ORDER: within a single phase the columns are emitted in the
#        order the entries are given, so a rival that permutes the entries INSIDE a
#        phase must still be rejected. Added by a later audit: C6 pins the order of
#        the phases relative to one another, but every witness above makes each
#        phase either empty, a single entry, or repeats of ONE identity, so none of
#        them can observe an ordering error within a phase (measured: all four
#        select-bearing witnesses fail to refute a reverse-select impl).
#   (C9) POSITIONAL PINNING OF *EVERY* PHASE AND EVERY LIST. Added by a later audit
#        that measured C6/C8 as covering only the two phases their witnesses make
#        non-empty. Each witness above is minimal by design — it makes ONE phase
#        (or two, for C6) non-empty with pairwise-distinct identities — and that
#        minimality is precisely what leaves the OTHER phases' positions and the
#        internal order of the other three lists unpinned. Measured over the whole
#        shipped battery: SIX distinct wrong impls are refuted by NONE of the 12
#        witnesses — the explicit seed emitted last, the ordering phase moved after
#        the filter phase, and the reverse of the seed list, of the ordering list,
#        of the filter list, and of a select entry's own column list. All six are
#        REJECTED by the frozen spec (so none is a spec hole); they were simply
#        untested. riv-permute-all-phases below closes all six at once with a
#        single input that makes every phase non-empty with length >= 2.
#
# CARRIER NOTE: the nagini sibling abstracted only the ordering contribution behind
# fractional read permission (four half-permission `List[int]` inputs, an
# order_contrib fold, and the requested/default guard). This backend models the WHOLE
# accumulation directly over the transparent `List (Bool × List Col)` carrier, so
# nagini's ordering rivals (uncond-fold / inverted-guard / drop-skip / invert-skip)
# map onto clauses C3 + C4 here, and the extra transparent structure
# (C0/C1/C2/C5/C6/C7) is additionally attackable — which is what the broader carrier
# lets this lane defend. All four of nagini's ordering rivals are carried over: the
# fourth (invert-skip) is riv-invert-order-skip below, and it is NOT redundant with
# drop-skip — drop-skip is only ever too permissive, so no witness of it can catch an
# impl that also drops a required column.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's mandatory `_FRAME_MUT`: the four list inputs were held
#     at Acc(list_pred(.),1/2) read-only, and the rival wrote back into one). Lean is
#     referentially transparent — no aliasing, no fractional permission — so a "store
#     into a read-only input" rival is not expressible and the lane is VACUOUS here.
#     See 'assessment'.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. The whole
#     accumulation is modeled DEEPLY (groupByExpressions), so there is no consumed
#     axiom anyway.
#
# ADMISSIBILITY, on a total carrier (nagini's `_ADMISS`: read-asserts on the four
# half-permission inputs proving the Requires non-vacuous). An earlier revision of
# this file dropped the lane with the reason "the lean obligation has no
# precondition hypothesis, so nothing could be PRECOND-TOO-STRONG". That reason is
# WRONG, and a later audit replaced it: the analogue of PRECOND-TOO-STRONG on a
# total carrier is not a rejected precondition but the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input — a spec that pins `result` to an
# oracle no implementation can meet there would still discharge `∀ …` vacuously in
# no useful sense, and nothing else in this battery evaluates the spec predicate at
# the F2P point at all. The positives all reason about ALL inputs symbolically and
# the rivals only ever exhibit inputs where the spec is VIOLATED, so an input where
# the modeled behaviour is positively SATISFIED, and specifically the one the F2P
# demands, was untested. admiss-f2p-shaped below discharges the spec predicate by
# evaluation at that concrete input as a `have`, then closes the frozen obligation
# verbatim.
from pathlib import Path

INSTANCE = "django__django-14122"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# Each lies ENTIRELY inside impl-start/impl-end (except _PROOF) and is unique in _BASE.

# The full impl body (used by the direct-grounded-oracle positive, which drops the loop
# and reproves the identical theorem statement).
_FULL_IMPL = (
    "def implementation_getGroupBy\n"
    "    (metaOrdering : Bool) (gb : GroupBy)\n"
    "    (select orderBy : List (Bool × List Col)) (having : List Col) :\n"
    "    List Col := Id.run do\n"
    "  let mut expressions : List Col := []\n"
    "  match gb with\n"
    "  | GroupBy.isNone => return []\n"
    "  | GroupBy.allFields => pure ()\n"
    "  | GroupBy.explicit cols =>\n"
    "      for c in cols do\n"
    "        expressions := expressions ++ [c]\n"
    "  for entry in select do\n"
    "    if entry.1 then\n"
    "      continue\n"
    "    for col in entry.2 do\n"
    "      expressions := expressions ++ [col]\n"
    "  if !metaOrdering then\n"
    "    for entry in orderBy do\n"
    "      if !entry.1 then\n"
    "        for col in entry.2 do\n"
    "          expressions := expressions ++ [col]\n"
    "  for col in having do\n"
    "    expressions := expressions ++ [col]\n"
    "  return expressions"
)
assert _BASE.count(_FULL_IMPL) == 1, "full impl anchor drifted"

# The three `match gb` arms (attacked by the isNone-short-circuit rival and reordered
# by the match-reorder positive).
_MATCH = (
    "  match gb with\n"
    "  | GroupBy.isNone => return []\n"
    "  | GroupBy.allFields => pure ()\n"
    "  | GroupBy.explicit cols =>\n"
)

# The explicit-seed arm body (attacked by the drop-explicit rival).
_EXPLICIT_ARM = (
    "  | GroupBy.explicit cols =>\n"
    "      for c in cols do\n"
    "        expressions := expressions ++ [c]\n"
)

# The selected-expression phase, with its reference skip (attacked by drop-select-skip).
_SELECT_PHASE = (
    "  for entry in select do\n"
    "    if entry.1 then\n"
    "      continue\n"
    "    for col in entry.2 do\n"
    "      expressions := expressions ++ [col]\n"
)

# The ordering gate + phase (attacked by uncond-fold / inverted-guard).
_ORDER_GATE = (
    "  if !metaOrdering then\n"
    "    for entry in orderBy do\n"
    "      if !entry.1 then\n"
    "        for col in entry.2 do\n"
    "          expressions := expressions ++ [col]\n"
)

# The per-ordering-entry reference skip inside the gated phase (attacked by
# drop-order-skip / invert-order-skip).
_ORDER_SKIP = (
    "      if !entry.1 then\n"
    "        for col in entry.2 do\n"
    "          expressions := expressions ++ [col]\n"
)

# The trailing filter phase (attacked by drop-having).
_HAVING_PHASE = (
    "  for col in having do\n"
    "    expressions := expressions ++ [col]\n"
    "  return expressions"
)

# The frozen proof body (everything inside proof-start/proof-end). Swapped only by the
# direct-grounded-oracle positive, whose different impl needs a shorter honest reproof
# of the byte-identical theorem statement.
_PROOF = _BASE[
    _BASE.index("-- proof-start\n") + len("-- proof-start\n"):
    _BASE.index("\n-- proof-end")
]
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-match-reorder: structurally-different but CORRECT impl. The `match gb` arms are
# reordered (allFields, then isNone, then explicit); the accumulation is otherwise
# byte-identical, so the output equals the frozen impl's on every input. The frozen
# `theorem correct_getGroupBy` statement is byte-identical AND the frozen proof body
# still closes (the case-split is on gb regardless of arm order) — a faithful
# restructure with no reproof and no new axiom/lemma/sorry. If it FAILS =>
# SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape).
#
# AUDIT NOTE (strength of this control, measured): reordering `match` arms is a
# DEFINITIONAL no-op on this carrier — a probe declaring the reordered body as a
# second constant and asserting `implementation_getGroupBy m gb s o hv =
# <reordered> m gb s o hv` closes by `cases gb <;> rfl` (exit 0), i.e. the two
# impls are per-constructor definitionally equal. `rfl` alone does NOT close it
# (the whnf of the un-split `match` differs), so this case does exercise the
# proof's ability to see through a re-elaborated `match`, but it can NOT detect a
# postcondition over-fit to the frozen impl's COMPUTATIONAL shape. The two
# reshapes below carry that load instead: pos-gate-hoisted changes the elaborated
# term genuinely (the gate moves off the loop body and onto the iterated list) and
# needs an honest reproof, and pos-select-via-flatMap replaces a whole loop phase
# with the oracle's own combinator form.
_POS_REORDER = _swap(
    _BASE, _MATCH,
    "  match gb with\n"
    "  | GroupBy.allFields => pure ()\n"
    "  | GroupBy.isNone => return []\n"
    "  | GroupBy.explicit cols =>\n",
)

# pos-gate-hoisted: a CORRECT reshape that is NOT definitionally the frozen impl.
# The ordering gate moves off the loop BODY and onto the iterated LIST: instead of
# `if !metaOrdering then for entry in orderBy do …`, iterate
# `for entry in (if metaOrdering then [] else orderBy) do …`. Same output at every
# input (iterating the empty list contributes nothing, which is exactly what the
# skipped phase contributed), but a genuinely different elaborated term: the frozen
# proof body does NOT close it, so the theorem statements are kept byte-identical
# and the tactic bodies are extended with (a) an `hord'` framing lemma for the
# residual `entry.1 = false` branch shape the reshape produces and (b) a trailing
# `simp` for the `filter []` residue. This is the reshape that actually tests
# SPEC-TOO-STRONG: if a faithful correct impl of this shape could not be proven,
# the spec would be over-fit to the frozen loop nesting.
_POS_HOISTED = _swap(
    _swap(
        _BASE, _ORDER_GATE,
        "  for entry in (if metaOrdering then [] else orderBy) do\n"
        "    if !entry.1 then\n"
        "      for col in entry.2 do\n"
        "        expressions := expressions ++ [col]\n",
    ),
    # Extend the tactic bodies only; every `theorem correct_*` STATEMENT stays
    # byte-identical to the frozen file (audited by diffing the headers).
    "  cases gb with\n"
    "  | isNone => exact absurd rfl h\n",
    "  have hord' : ∀ (es : List (Bool × List Col)) (acc : List Col),\n"
    "      forIn (m := Id) es acc (fun entry r =>\n"
    "          if entry.1 = false then ForInStep.yield (r ++ entry.2)\n"
    "          else ForInStep.yield r)\n"
    "        = acc ++ (es.filter (fun e => !e.1)).flatMap (fun e => e.2) := by\n"
    "    intro es; induction es with\n"
    "    | nil => intro acc; simp; rfl\n"
    "    | cons e rest ih =>\n"
    "        intro acc\n"
    "        rw [List.forIn_cons]\n"
    "        cases he : e.1\n"
    "        · simp only [he, if_true]\n"
    "          show forIn (m := Id) rest (acc ++ e.2) _ = _\n"
    "          rw [ih]; simp [List.filter, he, List.append_assoc]\n"
    "        · simp only [he, Bool.true_eq_false, if_false]\n"
    "          show forIn (m := Id) rest acc _ = _\n"
    "          rw [ih]; simp [List.filter, he]\n"
    "  cases gb with\n"
    "  | isNone => exact absurd rfl h\n",
)
_POS_HOISTED = _POS_HOISTED.replace(
    "          Bool.false_eq_true, hsel, hord, hs, List.nil_append, List.append_assoc]",
    "          Bool.false_eq_true, hsel, hord, hord', hs, List.nil_append,\n"
    "          List.append_assoc] <;>\n"
    "        simp",
)

# pos-select-via-flatMap: a second CORRECT reshape with a different mechanism — the
# whole selected-expression LOOP phase is replaced by the oracle's own combinator
# form (`(select.filter (fun e => !e.1)).flatMap (fun e => e.2)`), appended in one
# step. Correct by construction and, notably, the frozen proof body still closes
# (the `hsel` framing lemma states exactly this equality), so this is a no-reproof
# reshape that nevertheless removes a loop the frozen proof was written around.
_POS_FLATMAP = _swap(
    _BASE, _SELECT_PHASE,
    "  expressions := expressions ++ "
    "(select.filter (fun e => !e.1)).flatMap (fun e => e.2)\n",
)

# pos-direct-grounded-oracle: the cheapest HONEST impl. The postcondition oracle
# groupByExpressions is GROUNDED in the arguments (a total transparent fold), so
# directly returning it is a fully-grounded correct implementation, not an ungrounded
# echo — a wrong constant/echo fails the postcondition (see the reject cases). The
# proof collapses to `rfl` after unfolding (the impl is now definitionally
# groupByExpressions). MUST verify (the postcondition is literally result =
# groupByExpressions …); else SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(
        _BASE, _FULL_IMPL,
        "def implementation_getGroupBy\n"
        "    (metaOrdering : Bool) (gb : GroupBy)\n"
        "    (select orderBy : List (Bool × List Col)) (having : List Col) :\n"
        "    List Col :=\n"
        "  groupByExpressions metaOrdering gb select orderBy having",
    ),
    _PROOF,
    # Reprove ALL THREE frozen `correct_*` obligations (their statements are kept
    # byte-identical; only the tactic bodies change). Against the direct impl each
    # collapses to unfold + rfl. The two forIn framing lemmas the frozen proof used
    # are no longer needed (the impl has no loops) and are dropped — removing a
    # non-obligation helper is admissible; only ADDING a theorem/lemma is banned.
    "theorem correct_getGroupBy_isNone (metaOrdering : Bool)\n"
    "    (select orderBy : List (Bool × List Col)) (having : List Col) :\n"
    "    implementation_getGroupBy metaOrdering GroupBy.isNone select orderBy having\n"
    "      = groupByExpressions metaOrdering GroupBy.isNone select orderBy having := by\n"
    "  rfl\n"
    "\n"
    "theorem correct_getGroupBy_nonNone (metaOrdering : Bool) (gb : GroupBy)\n"
    "    (select orderBy : List (Bool × List Col)) (having : List Col)\n"
    "    (h : gb ≠ GroupBy.isNone) :\n"
    "    implementation_getGroupBy metaOrdering gb select orderBy having\n"
    "      = explicitCols gb ++ selectCols select\n"
    "        ++ (if metaOrdering then [] else orderByCols orderBy) ++ having := by\n"
    "  unfold implementation_getGroupBy groupByExpressions\n"
    "  cases gb with\n"
    "  | isNone => exact absurd rfl h\n"
    "  | allFields => rfl\n"
    "  | explicit cols => rfl\n"
    "\n"
    "theorem correct_getGroupBy :\n"
    "    ∀ (metaOrdering : Bool) (gb : GroupBy)\n"
    "      (select orderBy : List (Bool × List Col)) (having : List Col),\n"
    "      problem_spec_getGroupBy metaOrdering gb select orderBy having\n"
    "        (implementation_getGroupBy metaOrdering gb select orderBy having) := by\n"
    "  intro metaOrdering gb select orderBy having\n"
    "  unfold problem_spec_getGroupBy implementation_getGroupBy\n"
    "  rfl",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the WITNESS — checked in
# a file with the obligation removed — not the rival's own build).
# ===========================================================================

# riv-uncond-fold-default-ordering (C3): drop the `if !metaOrdering` gate and run the
# ordering phase UNCONDITIONALLY. This is the verbatim PRE-PATCH shape. Correct when
# the ordering is explicit; WRONG when it is the model's implicit default
# (metaOrdering = true), where the ordering columns must contribute nothing.
_RIV_UNCOND = _swap(
    _BASE, _ORDER_GATE,
    "  for entry in orderBy do\n"
    "    if !entry.1 then\n"
    "      for col in entry.2 do\n"
    "        expressions := expressions ++ [col]\n",
)

# riv-inverted-guard (C3): invert the gate — `if !metaOrdering` -> `if metaOrdering`.
# Folds the ordering columns exactly on the wrong branch: added on an implicit default
# (must be dropped) and dropped on an explicit request (must be kept).
_RIV_INVGUARD = _swap(
    _BASE, "  if !metaOrdering then\n", "  if metaOrdering then\n",
)

# riv-drop-order-skip (C4): within the (correctly gated) ordering phase, append every
# ordering entry's columns regardless of its reference flag. Wrong as soon as an
# ordering entry references the selected columns (entry.1 = true) — those columns are
# already grouped and must contribute nothing.
_RIV_DROPORDSKIP = _swap(
    _BASE, _ORDER_SKIP,
    "      for col in entry.2 do\n"
    "        expressions := expressions ++ [col]\n",
)

# riv-drop-select-skip (C2): remove the selected-expression reference skip, appending
# every selected entry's columns even when the entry is already covered by a reference
# (entry.1 = true) — those must contribute nothing.
_RIV_DROPSELSKIP = _swap(
    _BASE, _SELECT_PHASE,
    "  for entry in select do\n"
    "    for col in entry.2 do\n"
    "      expressions := expressions ++ [col]\n",
)

# riv-drop-explicit-seed (C1): drop the explicit caller-supplied grouping seed (its
# columns must lead the result), accumulating only the later phases.
_RIV_DROPEXPLICIT = _swap(
    _BASE, _EXPLICIT_ARM,
    "  | GroupBy.explicit cols =>\n"
    "      pure ()\n",
)

# riv-drop-having (C5): drop the trailing filter phase, so the post-aggregation filter
# columns never reach the result.
_RIV_DROPHAVING = _swap(
    _BASE, _HAVING_PHASE,
    "  return expressions",
)

# riv-isnone-not-empty (C0): treat the empty grouping source like "group by all fields"
# — fall through and accumulate the other phases instead of short-circuiting to [].
_RIV_ISNONE = _swap(
    _BASE, "  | GroupBy.isNone => return []\n",
    "  | GroupBy.isNone => pure ()\n",
)

# riv-invert-order-skip (C4, the other polarity): this is nagini's `invert-backref-skip`,
# which the port dropped. It IS expressible here and it is a DISTINCT wrong impl from
# riv-drop-order-skip: flipping `if !entry.1` to `if entry.1` keeps exactly the ordering
# entries the spec says to drop and drops exactly the ones it says to keep, so it is
# wrong in BOTH directions at once. drop-order-skip is only ever too permissive (a
# superset of the correct columns), so no witness of that rival can catch an impl that
# also DROPS a required column. The witness below puts both polarities in one ordering
# list — a non-referencing entry that must be kept and a referencing one that must be
# dropped — so it discriminates a wrong impl that swaps them.
_RIV_INVORDSKIP = _swap(
    _BASE, "      if !entry.1 then\n", "      if entry.1 then\n",
)

# riv-having-before-select (phase ORDER, previously unattacked): keep every phase and
# every filter, but emit the trailing filter columns BEFORE the selected-expression
# columns. The result is a PERMUTATION of the correct list — same multiset, wrong order.
# Nothing in the existing battery pinned the ORDER of the phases: every prior rival
# either adds or removes columns, so each is caught by a witness whose input makes one
# phase non-empty and the rest empty, and such an input cannot see a reordering at all.
_RIV_HAVINGFIRST = _swap(
    _swap(
        _BASE, _SELECT_PHASE,
        "  for col in having do\n"
        "    expressions := expressions ++ [col]\n"
        + _SELECT_PHASE,
    ),
    _HAVING_PHASE, "  return expressions",
)

# riv-eager-dedup (MULTIPLICITY, previously unattacked): accumulate exactly the right
# columns in exactly the right order, then de-duplicate. The spec's value is the
# accumulated list BEFORE the de-duplication phase (that pass is explicitly not modeled
# here), so collapsing repeats is wrong — and it is wrong in a way no other rival can
# expose: the difference is visible only at an input where one column is contributed
# TWICE. Every existing witness uses pairwise-distinct column identities, so all of them
# hold of this rival's impl too. Guards the modeling boundary itself.
_RIV_DEDUP = _swap(
    _BASE, "  return expressions", "  return expressions.eraseDups",
)

# riv-reverse-select-order (C8, INTRA-PHASE order): keep every phase, every filter and
# every phase's position, but iterate the selected entries in REVERSE. The result is a
# permutation of the correct list that permutes WITHIN one phase, so riv-having-before-
# select (which permutes phases relative to each other) does not subsume it and neither
# does any witness above: each of those makes every phase empty, a single entry, or
# repeats of ONE column identity, and reversal is invisible at all three. Measured
# during audit: the four select-bearing witnesses (drop-select-skip, having-before-
# select, eager-dedup, isnone-not-empty) all FAIL to refute this impl (exit 1 each),
# so this clause was genuinely unattacked. The witness below therefore gives the
# selected phase TWO entries with DISTINCT column identities, which is the smallest
# input at which an intra-phase permutation is observable.
_RIV_REVSELECT = _swap(
    _BASE, "  for entry in select do\n", "  for entry in select.reverse do\n",
)

# riv-gate-on-wrong-binder (C3, third angle): keep a gate on the ordering phase but read
# the WRONG input for it — gate on the selected list being empty instead of on whether
# the ordering was explicitly requested. This is the "right shape, wrong observable"
# error: the impl still has a conditional ordering phase, so it is not caught by
# reasoning about the presence of a gate, only about WHICH binder decides it. Both
# existing C3 rivals (uncond-fold, inverted-guard) attack the gate's polarity or its
# presence; neither shows the spec pins the gate to `metaOrdering` specifically.
_RIV_WRONGGATE = _swap(
    _BASE, "  if !metaOrdering then\n", "  if select.isEmpty then\n",
)

# riv-permute-all-phases (C9): the accumulation emits exactly the correct MULTISET of
# columns — every phase present, every reference filter honoured, the ordering gate
# read off the right binder — but the explicit seed is emitted LAST instead of first.
# Added by a later audit that measured the existing order-pinning cases as covering
# only the phases their own witnesses make non-empty. riv-having-before-select pins
# select-vs-having and riv-reverse-select-order pins the interior of the select phase;
# NEITHER pins where the explicit seed sits, because every witness in the battery
# either leaves the seed empty (11 of 12) or makes it the ONLY non-empty phase
# (riv-drop-explicit-seed, gb=explicit [5] with all else empty), and the seed's
# position is unobservable at both. Measured: this impl is refuted by NONE of the 12
# shipped witnesses.
#
# The witness below is deliberately NOT minimal, and that is the point of the case.
# It makes EVERY phase non-empty with length >= 2 and pairwise-distinct identities, so
# one input simultaneously pins the position of all four phases AND the internal order
# of all four lists. That closes, in one case, five further wrong impls this battery
# also failed to refute (each verified during the audit as rejected by the frozen spec,
# so none is a spec hole): the ordering phase moved after the filter phase, and the
# reverse of the seed list, of the ordering list, of the filter list, and of an
# individual select entry's own column list.
_RIV_PERMUTE = _swap(
    _swap(
        _BASE, _EXPLICIT_ARM,
        "  | GroupBy.explicit cols =>\n"
        "      pure ()\n",
    ),
    _HAVING_PHASE,
    "  for col in having do\n"
    "    expressions := expressions ++ [col]\n"
    "  match gb with\n"
    "  | GroupBy.explicit cols =>\n"
    "      for c in cols do\n"
    "        expressions := expressions ++ [c]\n"
    "  | _ => pure ()\n"
    "  return expressions",
)

# admiss-f2p-shaped: the ADMISSIBILITY positive. Not a reshape — the impl and the
# frozen proof are byte-identical; two `have`s are prepended to the frozen obligation's
# own tactic body, which then closes verbatim. They discharge the spec predicate BY
# EVALUATION at a concrete F2P-shaped input and pin the value the modeled behaviour
# takes there. The input is the F2P shape: an aggregate whose ordering is the model's
# own implicit default (metaOrdering = true) naming a column that is not otherwise
# grouped, alongside a genuinely selected column. The obligation must be SATISFIABLE
# at that point, and satisfiable with the ordering column ABSENT — the demanded
# behaviour. If this failed, the modeled behaviour would be unmeetable at exactly a
# normal F2P input, the total-carrier analogue of PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    "  intro metaOrdering gb select orderBy having\n",
    "  have _ground : problem_spec_getGroupBy true GroupBy.allFields\n"
    "      [(false, [1])] [(false, [2])] []\n"
    "      (implementation_getGroupBy true GroupBy.allFields\n"
    "        [(false, [1])] [(false, [2])] []) := by\n"
    "    unfold problem_spec_getGroupBy implementation_getGroupBy\n"
    "    decide\n"
    "  have _witnessed : implementation_getGroupBy true GroupBy.allFields\n"
    "      [(false, [1])] [(false, [2])] [] = [1] := by decide\n"
    "  intro metaOrdering gb select orderBy having\n",
)


def _wit(meta, gb, select, orderBy, having, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal input, closed by `decide`. Elaborates against a rival that diverges from
    groupByExpressions there, and fails on gold (which satisfies the spec at every
    input). All arguments are Lean literals; the oracle is a transparent fold so
    `decide` computes both sides."""
    call = f"{meta} {gb} {select} {orderBy} {having}"
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_getGroupBy {call}\n"
        f"    (implementation_getGroupBy {call}) := by\n"
        f"  unfold problem_spec_getGroupBy implementation_getGroupBy\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-match-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the grouping-source case arms are "
            "reordered while the accumulation stays byte-identical, so the output equals "
            "the frozen impl's on every input. The frozen `theorem correct_getGroupBy` "
            "statement is byte-identical and the frozen proof body still closes (the "
            "case split is on the source regardless of arm order) — a faithful "
            "restructure with no reproof, no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-direct-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition oracle groupByExpressions is GROUNDED in the arguments (a "
            "total transparent fold), so returning it directly is the honest cheapest "
            "CORRECT impl, not an ungrounded echo; the proof collapses to `rfl` after "
            "unfolding. Must verify (the postcondition is literally result = "
            "groupByExpressions …); else SPEC-TOO-STRONG. Also shows the spec is not "
            "echo-vulnerable: every WRONG shape below fails the same postcondition."
        ),
    },
    {
        "id": "pos-gate-hoisted",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HOISTED,
        "rationale": (
            "CORRECT reshape that is NOT definitionally the frozen impl: the ordering "
            "gate moves off the loop BODY and onto the iterated LIST (`for entry in (if "
            "metaOrdering then [] else orderBy)`), which contributes nothing exactly when "
            "the skipped phase did. The frozen proof body does not close this shape, so "
            "the three `theorem correct_*` STATEMENTS are kept byte-identical and only "
            "the tactic bodies are extended — with an `hord'` framing lemma for the "
            "residual branch shape the reshape produces and a trailing `simp` for the "
            "`filter []` residue. This is the control that actually probes SPEC-TOO-"
            "STRONG: unlike an arm reorder (definitionally a no-op, see pos-match-"
            "reorder), it changes the elaborated term, so if the spec were over-fit to "
            "the frozen loop nesting this case would FAIL."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADMISSIBILITY on a total carrier: the obligation is SATISFIABLE at a "
            "concrete F2P-shaped input, discharged by evaluation as a `have` before "
            "the frozen obligation is closed verbatim. The input is the shape the F2P "
            "demands — an aggregate whose ordering is the model's own implicit default "
            "(metaOrdering = true) naming a column not otherwise grouped, alongside a "
            "genuinely selected column — and the second `have` pins the value there to "
            "the selected column ALONE, i.e. the ordering column is absent. Nothing is "
            "assumed: the impl and the frozen proof body are byte-identical, the three "
            "`theorem correct_*` statements are byte-identical, and no new "
            "axiom/lemma/theorem/sorry is introduced. This is the lane that detects "
            "PRECOND-TOO-STRONG; the total-carrier analogue is the modeled behaviour "
            "being unmeetable at exactly a normal F2P input, which every other case in "
            "this battery leaves untested — the positives reason symbolically over ALL "
            "inputs and the rivals only ever exhibit inputs where the spec is "
            "VIOLATED, so no other case evaluates the spec predicate at a point where "
            "it is meant to HOLD. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "pos-select-via-flatMap",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLATMAP,
        "rationale": (
            "second CORRECT reshape, different mechanism: the whole selected-expression "
            "LOOP phase is replaced by the combinator form `(select.filter (fun e => "
            "!e.1)).flatMap (fun e => e.2)` appended in one step. Removes a loop the "
            "frozen proof was written around while the frozen proof body still closes "
            "(its `hsel` framing lemma states exactly this equality) — a no-reproof "
            "reshape at the level of a whole phase. If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "riv-uncond-fold-default-ordering",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNCOND,
        "refinement": (
            "running the ordering phase unconditionally is literally the PRE-PATCH "
            "shape: an implicit default ordering still widens the grouping. On the F2P "
            "case — an aggregate over a model whose implicit default ordering names a "
            "column not otherwise grouped — that column leaks into the grouping and "
            "splits the aggregation into spurious groups, so the aggregate counts are "
            "wrong and the F2P assertion fails. A faithful patch of this shape does NOT "
            "resolve; a verifying rival is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the discriminating "
            "ordering-gate clause (C3): when metaOrdering = true the ordering columns "
            "must contribute nothing. Witness holds metaOrdering = true with a non-ref "
            "ordering entry — varies the metaOrdering binder against the inverted-guard "
            "rival (which is witnessed at metaOrdering = false). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # meta=true, orderBy=[(false,[7])]: gold drops it ([]); rival keeps it ([7]).
        "witness": _wit("true", "GroupBy.allFields", "[]", "[(false, [7])]", "[]",
                        "implicit default ordering: gold contributes nothing, rival leaks the column"),
    },
    {
        "id": "riv-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INVGUARD,
        "refinement": (
            "inverting the gate folds the ordering columns on exactly the wrong branch: "
            "an implicit default still leaks (fails the F2P) and an explicit ordering is "
            "wrongly dropped, breaking the explicit-ordering aggregation PASS_TO_PASS "
            "cases. Resolves nothing."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the ordering-gate clause "
            "(C3) from the other side: with metaOrdering = false (explicit request) the "
            "ordering columns must be KEPT, but the rival drops them. Witness holds "
            "metaOrdering = false with a non-ref ordering entry — a distinct input point "
            "from the uncond-fold rival's metaOrdering = true. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # meta=false, orderBy=[(false,[7])]: gold keeps it ([7]); rival drops it ([]).
        "witness": _wit("false", "GroupBy.allFields", "[]", "[(false, [7])]", "[]",
                        "explicit ordering: gold keeps the column, rival drops it"),
    },
    {
        "id": "riv-drop-order-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPORDSKIP,
        "refinement": (
            "keeping the gate but dropping the per-entry reference skip appends the "
            "columns of an ordering entry that merely references the SELECT clause — "
            "columns already in the grouping — yielding a duplicated/extra grouping "
            "column. The ordering-with-references PASS_TO_PASS cases and the F2P do not "
            "resolve."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the ordering-entry "
            "reference filter (C4): a referencing ordering entry (entry.1 = true) must "
            "contribute nothing. Witness sets metaOrdering = false with a REFERENCING "
            "ordering entry — varies the ordering entry's reference-flag binder (.1). If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # meta=false, orderBy=[(true,[7])]: gold drops the ref entry ([]); rival keeps it ([7]).
        "witness": _wit("false", "GroupBy.allFields", "[]", "[(true, [7])]", "[]",
                        "referencing ordering entry: gold contributes nothing, rival re-adds the column"),
    },
    {
        "id": "riv-drop-select-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPSELSKIP,
        "refinement": (
            "removing the selected-expression reference skip appends the columns of a "
            "selected entry already covered by a reference — a duplicated grouping "
            "column for every reference-covered SELECT expression, so aggregate queries "
            "over reference-covered columns group wrongly. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the selected-expression "
            "reference filter (C2): a reference-covered selected entry (entry.1 = true) "
            "must contribute nothing. Witness sets a REFERENCING select entry — varies "
            "the select entry's reference-flag binder (.1). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # select=[(true,[7])]: gold drops the ref entry ([]); rival keeps it ([7]).
        "witness": _wit("false", "GroupBy.allFields", "[(true, [7])]", "[]", "[]",
                        "reference-covered select entry: gold contributes nothing, rival re-adds the column"),
    },
    {
        "id": "riv-drop-explicit-seed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPEXPLICIT,
        "refinement": (
            "dropping the explicit caller-supplied grouping seed omits the columns the "
            "caller explicitly grouped by — the leading columns of the grouping vanish, "
            "so an explicitly-grouped aggregate groups by the wrong (missing) columns. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the explicit-seed clause "
            "(C1): an explicit caller-supplied grouping set must lead the result. "
            "Witness sets the grouping source to an explicit list — varies the grouping-"
            "source binder (gb) to the explicit constructor. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # gb=explicit [5]: gold=[5]; rival drops the seed ([]).
        "witness": _wit("false", "(GroupBy.explicit [5])", "[]", "[]", "[]",
                        "explicit grouping seed: gold emits the seed column, rival drops it"),
    },
    {
        "id": "riv-drop-having",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPHAVING,
        "refinement": (
            "dropping the trailing filter phase omits the post-aggregation filter "
            "columns from the grouping, so an aggregate whose filter references a column "
            "not otherwise grouped produces an invalid/incorrect GROUP BY. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the filter-columns "
            "clause (C5): the post-aggregation filter columns come last. Witness sets a "
            "non-empty filter-column list — varies the having binder. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # having=[9]: gold=[9]; rival drops it ([]).
        "witness": _wit("false", "GroupBy.allFields", "[]", "[]", "[9]",
                        "filter columns: gold appends them, rival drops them"),
    },
    {
        "id": "riv-isnone-not-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ISNONE,
        "refinement": (
            "treating the empty grouping source as 'group by all fields' accumulates the "
            "other phases instead of short-circuiting to the empty grouping. Its "
            "faithful counterpart would emit a GROUP BY for a query that must have none "
            "(a non-aggregate query), changing the result set. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the empty-source "
            "short-circuit clause (C0): an empty grouping source yields [] regardless of "
            "the other phases. Witness sets gb = the empty source WITH a non-empty "
            "selected phase — varies the grouping-source binder (gb) to the empty "
            "constructor while the select binder is non-trivial. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # gb=isNone, select=[(false,[3])]: gold=[]; rival accumulates ([3]).
        "witness": _wit("false", "GroupBy.isNone", "[(false, [3])]", "[]", "[]",
                        "empty grouping source: gold yields [], rival accumulates the select column"),
    },
    {
        "id": "riv-invert-order-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INVORDSKIP,
        "refinement": (
            "inverting the per-entry reference skip inside the gated ordering phase keeps "
            "exactly the ordering columns that are already grouped and drops exactly the "
            "ones that still need grouping — wrong in both directions on every ordering "
            "case. The explicit-ordering aggregation PASS_TO_PASS cases break (their "
            "genuine ordering columns vanish from the grouping) and the F2P does not "
            "resolve. Resolves nothing."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the ordering-entry "
            "reference filter (C4) at the OPPOSITE polarity from riv-drop-order-skip, "
            "which is only ever too permissive (its output is a superset of the correct "
            "columns) and so cannot expose an impl that also DROPS a required column. The "
            "witness puts both polarities in one ordering list — a non-referencing entry "
            "that must be kept and a referencing one that must be dropped — so it "
            "discriminates precisely the swap. This is nagini's `invert-backref-skip`, "
            "expressible here. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # meta=false, orderBy=[(false,[7]),(true,[8])]: gold=[7]; rival swaps them ([8]).
        "witness": _wit("false", "GroupBy.allFields", "[]", "[(false, [7]), (true, [8])]", "[]",
                        "swapped ordering skip: gold keeps only the non-referencing column, "
                        "rival keeps only the referencing one"),
    },
    {
        "id": "riv-having-before-select",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_HAVINGFIRST,
        "refinement": (
            "emitting the post-aggregation filter columns ahead of the selected-expression "
            "columns produces the right SET of grouping columns in the wrong SEQUENCE. The "
            "grouping list is positional downstream (it is consumed in order, and the "
            "selected expressions' own positions are what the aggregate is keyed on), so a "
            "permuted list is a different GROUP BY. Resolves nothing."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the order of the phases "
            "relative to ONE ANOTHER, which no other rival probes: every other rival adds "
            "or removes columns, so each is caught by a witness that makes ONE phase "
            "non-empty and the rest empty — and such an input cannot see a reordering at "
            "all. This witness therefore makes TWO phases non-empty simultaneously (a "
            "selected entry and a filter column) so the ordering of the concatenation is "
            "observable. It does NOT pin the order WITHIN a phase (its selected phase has "
            "a single entry): that is riv-reverse-select-order's clause (C8). If it "
            "VERIFIES => SPEC-TOO-WEAK (the postcondition would only pin the multiset)."
        ),
        # select=[(false,[1])], having=[9]: gold=[1,9]; rival emits [9,1].
        "witness": _wit("false", "GroupBy.allFields", "[(false, [1])]", "[]", "[9]",
                        "phase order: gold emits the selected column before the filter column, "
                        "rival emits them the other way round"),
    },
    {
        "id": "riv-eager-dedup",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DEDUP,
        "refinement": (
            "de-duplicating inside this function collapses repeats that the modeled value "
            "is defined to still carry — the de-duplication is a LATER, separate pass over "
            "the accumulated list, and folding it in here changes the value handed to that "
            "pass. A faithful impl of this shape moves work across the modeled boundary "
            "and does not reproduce the accumulated list the rest of the pipeline consumes."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks MULTIPLICITY, which no "
            "other rival probes: this impl accumulates exactly the right columns in exactly "
            "the right order and differs from gold ONLY at an input where one column is "
            "contributed twice. Every other witness in this battery uses pairwise-distinct "
            "column identities, so all of them hold of this impl too. The witness therefore "
            "repeats a column identity across two selected entries. Guards the modeling "
            "boundary (the accumulated list BEFORE the de-duplication phase). If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # select=[(false,[1]),(false,[1])]: gold=[1,1]; rival collapses to [1].
        "witness": _wit("false", "GroupBy.allFields", "[(false, [1]), (false, [1])]", "[]", "[]",
                        "repeated column identity: gold keeps both occurrences, rival collapses them"),
    },
    {
        "id": "riv-reverse-select-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVSELECT,
        "refinement": (
            "emitting the selected-expression columns in reverse order produces the "
            "right SET of grouping columns, in the right phase, in the wrong SEQUENCE "
            "within that phase. The grouping list is consumed positionally downstream, "
            "so a permuted list is a different GROUP BY even when the permutation stays "
            "inside one phase. Resolves nothing."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks INTRA-PHASE ORDER (C8), "
            "which no other rival probes. riv-having-before-select pins the order of the "
            "phases relative to one another, but not the order WITHIN a phase, and the "
            "distinction is real: every other witness in this battery makes each phase "
            "empty, a single entry, or repeats of ONE column identity, and a reversal is "
            "invisible at all three. Measured during audit: all four select-bearing "
            "witnesses fail to refute this impl. The witness therefore gives the selected "
            "phase TWO entries with DISTINCT identities — the smallest input at which an "
            "intra-phase permutation is observable. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # select=[(false,[1]),(false,[2])]: gold=[1,2]; rival reverses to [2,1].
        "witness": _wit("false", "GroupBy.allFields", "[(false, [1]), (false, [2])]",
                        "[]", "[]",
                        "intra-phase column order: gold emits the selected columns in "
                        "list order, rival emits them reversed"),
    },
    {
        "id": "riv-gate-on-wrong-binder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONGGATE,
        "refinement": (
            "gating the ordering phase on whether the selected list is empty, rather than "
            "on whether the ordering was explicitly requested, gets the F2P case wrong "
            "exactly as the unguarded shape does — an aggregate that selects nothing "
            "still widens its grouping with an implicitly-defaulted ordering column, "
            "splitting the aggregation. Resolves nothing."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks the discriminating ordering "
            "gate (C3) from a third angle: the impl still HAS a conditional ordering phase, "
            "but it reads the wrong observable to decide it. The two existing C3 rivals "
            "attack the gate's polarity (riv-inverted-guard) or its presence "
            "(riv-uncond-fold-default-ordering); neither shows the spec pins the decision "
            "to the ordering-request binder SPECIFICALLY rather than to any input that "
            "happens to be discriminating. Witness holds metaOrdering = true (the ordering "
            "must contribute nothing) with an empty selected list, so the rival's gate "
            "opens where the spec's is closed. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # meta=true, select=[], orderBy=[(false,[7])]: gold=[]; rival's gate opens ([7]).
        "witness": _wit("true", "GroupBy.allFields", "[]", "[(false, [7])]", "[]",
                        "gate keyed on the wrong input: gold contributes nothing for an implicit "
                        "default ordering, rival opens its gate and leaks the column"),
    },
    {
        "id": "riv-permute-all-phases",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PERMUTE,
        "refinement": (
            "emitting the explicit caller-supplied grouping seed LAST rather than first "
            "produces the right SET of grouping columns in the wrong SEQUENCE, with the "
            "caller's own explicitly-grouped columns displaced to the end. The grouping "
            "list is consumed positionally downstream, so a permuted list is a different "
            "GROUP BY: the caller asked to group by those columns first and the emitted "
            "grouping keys on them last. Resolves nothing — it does not even address the "
            "ordering behaviour the F2P turns on, while additionally corrupting the "
            "explicitly-grouped cases that currently pass."
        ),
        "rationale": (
            "REJECTED by result = groupByExpressions …. Attacks C9 — the positional "
            "pinning of the phases and lists that the two existing order cases leave "
            "open. riv-having-before-select pins select-vs-having and "
            "riv-reverse-select-order pins the interior of the select phase, but NEITHER "
            "pins where the explicit seed sits: 11 of the 12 other witnesses leave the "
            "seed empty and the twelfth (riv-drop-explicit-seed) makes it the only "
            "non-empty phase, and the seed's position is unobservable at both. Measured "
            "during audit: this impl is refuted by NONE of the 12 other shipped "
            "witnesses. The witness is deliberately NON-minimal — every phase non-empty, "
            "each list of length >= 2, all identities pairwise distinct — so one input "
            "pins the position of all four phases AND the internal order of all four "
            "lists at once, which also closes five further wrong impls the battery could "
            "not refute (ordering phase moved after the filter phase; the reverse of the "
            "seed, ordering, and filter lists; the reverse of a select entry's own column "
            "list — each separately confirmed during audit to be rejected by the frozen "
            "spec, so none is a spec hole). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # gb=explicit [5,6], select=[(false,[1,2]),(true,[60])],
        # orderBy=[(false,[7]),(true,[8]),(false,[3])], having=[9,4]:
        # gold=[5,6,1,2,7,3,9,4]; rival displaces the seed to the end ([1,2,7,3,9,4,5,6]).
        "witness": _wit("false", "(GroupBy.explicit [5, 6])",
                        "[(false, [1, 2]), (true, [60])]",
                        "[(false, [7]), (true, [8]), (false, [3])]", "[9, 4]",
                        "every phase non-empty: gold leads with the explicit seed, rival "
                        "displaces it to the end — same multiset, wrong sequence"),
    },
]


# No @ContractOnly axioms and no opaque callees: the whole accumulation (empty-source
# short-circuit, explicit seed, the selected/ordering reference filters, the
# discriminating ordering gate, and the trailing filter columns) is modeled DEEPLY over
# the transparent List (Bool × List Col) / GroupBy carrier, so the axiom lane is vacuous
# here and belongs to G-AX regardless.
AXIOM_TESTS = []
