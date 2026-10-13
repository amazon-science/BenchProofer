"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5787 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligations closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models two symmetric loops over an abstract ``List[int]`` chain (``serialize_chain``
and ``deserialize_chain``) each under fractional-permission contracts. This Lean
bundle models the same two cooperating operations DEEPLY over the observable
data: a failure representation is a ``Longrepr`` (a single exception, or a chain
carrying an ordered list of links) and its builtin-data form is a
``SerializedLongrepr`` (outermost crash/traceback + sections + an optional list
of links). Two total functions are contracted — ``implementation_serialize`` and
``implementation_deserialize`` — each with a GROUNDED equality obligation
(``result = serializeLongrepr lr`` / ``result = deserializeLongrepr s``): the
result is pinned to a term built only from the input, so presence, order and
per-link content of the chain are all fixed. Each nagini case maps to an attack
on one of these two obligations, or is principled-omitted; the mapping is in the
module ``assessment``.

DEFENDED SURFACE (two modeled operations, one round-trip behavior).
  * serialize: a single exception records NO link list; a chain records the FULL
    ordered list of its links (``chain := some (chain.map packLink)``) and
    exposes its outermost link's traceback/crash. Independent clauses of the
    obligation: the single arm; the chained arm's outermost crash/traceback; the
    chained arm's recorded link list (presence + order + per-link content).
  * deserialize: a present non-empty link list rebuilds the WHOLE chain
    (``.chained`` with every link, in order); otherwise a single exception is
    rebuilt. Independent clauses: the chain-present arm (constructor + links);
    the no-chain arm.

The BEHAVIOURAL DISCRIMINATOR (the fix): the whole multi-stage failure (count +
order + per-link content) must survive the round trip rather than collapsing to
its outermost exception. Pre-fix, serialization recorded no link list and
deserialization always rebuilt a single exception, so a chain collapsed to one
stage. The uniqueness rivals below ARE those two regressions and their
partial-domain / value-level neighbours.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini battery carries two
    frame-mutation rivals (an in-place write into the read-only ``chain`` /
    ``transport`` held at half permission). Lean is referentially transparent: an
    input carries no heap permission, there is no half-permission to overwrite
    and no aliasing to exploit, so those rivals have no expressible instance
    here. No substitute is fabricated. (nagini cases ``frame-serialize-write``,
    ``frame-deserialize-write``.)

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not vacuous. (Corrected by the
    second audit, which MEASURED this rather than reasoning about it; the earlier
    text claimed the class was vacuous because "a diverging implementation cannot
    be written at all", and that is false.) The frozen file sets no
    ``loom.semantics.termination`` option, and while ``implementation_*`` is
    declared as a total ``def``, an impl-region edit may make it ``partial def``:
    ``partial def implementation_serialize ... | .chained chain secs => return
    implementation_serialize (.chained chain secs)`` is EXPRESSIBLE here and
    passes ``variant_scope`` (no new axiom/sorry/theorem, both theorem statements
    byte-identical), and it is indeed REJECTED (exit 1).

    But that rejection is NOT attributable to divergence, so the case is not
    shippable, and the audit demonstrated this with two controls rather than
    asserting it. ``partial`` makes the definition OPAQUE (it is compiled via an
    ``Inhabited`` witness and carries no equational unfolding), so:
      - a ``partial def`` whose body is the FROZEN one verbatim still VERIFIES
        (exit 0) — so ``partial`` alone is not what is being rejected; but
      - a ``partial`` RECURSIVE and CORRECT reshape (a tail-recursive
        ``implSerAux`` accumulating the same list) is rejected IDENTICALLY
        (exit 1, ``Tactic 'rfl' failed``) to the diverging one, and
      - the projection witness that discriminates every other rival here fails
        (exit 1, ``unsolved goals``) against the diverging rival, the correct
        recursive ``partial`` rival, AND the frozen solution alike — three
        builds, one error. The opaque term never reduces, so no witness can
        separate a diverging impl from a correct one.
    Per the brief's F′ rule this is therefore recorded as a KNOWN HOLE in the
    spec (a non-reducing impl is not refutable on this carrier), NOT as a vacuous
    class, and no case is fabricated for it. (The nagini sibling carries no
    ``diverge-*`` case either, so nothing is being dropped from the port.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Both obligations are GROUNDED: ``result``
    is pinned equal to a term (``serializeLongrepr``/``deserializeLongrepr``)
    built only from the input. There is no opaque answer key an implementation
    could echo. (``packLink``/``unpackLink`` are the modeled per-link identity
    copy — the unchanged entry-payload pass-through — NOT an oracle for the
    chain-structure decision; the impl still has to record/rebuild the list.) In
    its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS that must verify.

  * COLLAPSE / PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on the
    degenerate single-exception domain but diverging on every multi-stage chain:
    dropping the link list entirely (serialize) or ignoring it (deserialize);
    dropping the originating link; reversing the order; duplicating one link's
    content across every slot.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen tactic script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete multi-stage input and refuting it. Each was
built two ways and SEEN to discriminate: it ELABORATES against its rival and
FAILS against the frozen solution.

A subtlety of this carrier drives the witness tactics. ``Longrepr`` and
``SerializedLongrepr`` do NOT derive ``DecidableEq`` (their ``Link`` field is a
tuple of structures), so the refutations are not stated by a single ``decide``.
Instead they PROJECT the discriminating field and let ``simp`` reduce the
resulting DECIDABLE equality to ``False``: the recorded link list via
``congrArg SerializedLongrepr.chain`` (an ``Option (List Link)``), the outermost
crash via ``congrArg SerializedLongrepr.crash`` (a ``FileLoc``), the carried
sections via ``congrArg SerializedLongrepr.sections``, and — on the deserialize
site, where the result is a ``Longrepr`` rather than a structure — the rebuilt
link list via a ``congrArg`` over an explicit ``match`` that projects a
``.chained``'s links and sends a ``.single`` to ``[]``. No witness binds a
hypothesis (all inputs are concrete literals), so no carrier conditioning and no
consistency obligation arises.

AUDIT NOTE (independent re-derivation). Every reject witness was rebuilt BOTH
ways by the audit and its exit codes recorded: each elaborates against its rival
(exit 0) and fails against the frozen solution (exit 1). The gold-side failure
was additionally READ, because an exit code alone does not distinguish a semantic
refutation from a syntactic accident. ALL of them now fail on gold with
``hc : True ⊢ False`` — the projection reduces, agrees on gold, and leaves the
unprovable ``False`` — which is a genuine refutation of the concrete claim. The
``deserialize-collapse`` witness did NOT: it closed with
``exact Longrepr.noConfusion h``, and on gold the ``Id.run``/``forIn`` term never
reduced to a constructor application, so the failure was ``error: Type mismatch``
— ill-typed rather than false. It discriminated by exit code, so the gate
accepted it, but the rejection was attributable to an unfolding failure and not
to the spec. It has been REPAIRED to the projection shape used everywhere else
and re-confirmed (rival 0 / gold 1, ``hc : True ⊢ False``). Independently, gold
was shown to SATISFY the spec at all witness points (``... := by rfl``, exit 0),
so no witness is merely vacuously false of it.

The audit also closed two coverage gaps it found by adding two reject cases below.
Every pre-existing serialize rival edited only the ``.chained`` arm and kept ``let
outer := outerOf chain`` verbatim, so two independent clauses were never probed:
WHICH link is the outermost one (``outermost-from-head-serialize``) and the
``.single`` arm's "records no link list" (``single-arm-empty-chain-serialize``,
which also moves the ``lr`` binder to its other constructor for the first time in
the battery).

SECOND-AUDIT NOTE (independent re-derivation, all nine reject witnesses rebuilt).
A second, independent audit re-derived every claim above with its own builds and
made three changes:

  * It re-ran the FORGERY test (flip the claim / reveal the hypothesis type) on
    all nine reject witnesses, because ``hc : True ⊢ False`` is not a plain
    evaluation and "it looks semantic" is not evidence in either direction. Both
    halves came back decisive. FLIP: restating each witness as the POSITIVE claim
    (drop the ``¬``, close ``by rfl``) builds against gold at exit 0 and against
    the rival at exit 1 — the exact inverse of the witness itself, so gold's exit
    code demonstrably TRACKS the claim rather than being constant. REVEAL:
    appending ``exact (hc : Nat)`` after the witness's own ``simp ... at hc``
    prints ``hc has type True`` on gold (simp PROVED the projected equation there)
    and ``No goals to be solved`` on the rival (simp closed the goal outright).
    That pair is a genuine refutation, not a tactic mismatch, for all nine.

  * It CORRECTED the divergence-lane disposition from "vacuous" to "known hole"
    (see the class list above) — a ``partial def`` rival is expressible and in
    scope here, so "cannot be written at all" was false; it is unrefutable, which
    is a different and weaker statement.

  * It CORRECTED the ``single-arm-empty-chain-serialize`` refinement, which
    claimed a P2P consequence the manifest never demonstrates, and DISPROVED that
    claim by build (the ``some []`` vs ``none`` difference is invisible after a
    full round trip). The case is kept with its true, narrower scope.

  * It closed the one remaining coverage gap by adding ``drop-sections-
    deserialize``: no shipped reject case attacked the SECTIONS carry-through on
    either site, though the F2P asserts the reconstructed sections in the same
    block as the chain.

  Its SPEC-TOO-WEAK / SPEC-TOO-STRONG sweep found no hole in either direction:
  nine further NEW wrong impls (crash-from-head-only, blanked descriptions,
  duplicated last link, single-arm dropped sections, deserialize drop-last,
  ``.chained`` at the ``some []`` boundary, sections dropped on three more
  arm/site combinations, truncate-to-2) were ALL rejected, and six NEW correct
  reshapes (serialize by ``map``; inline ``getLast?``; build-reversed-then-
  ``.reverse``; deserialize branching on ``isEmpty``; deserialize by ``foldr``;
  and BOTH sites reshaped at once) were ALL provable.

BINDER / POINT SPREAD. The frozen obligations carry NO precondition hypothesis
(both modeled functions are total, so ``∀`` is unguarded); the input binders are
the ``Longrepr`` argument of serialize and the ``SerializedLongrepr`` argument of
deserialize. The NINE reject witnesses probe NINE DISTINCT inputs — a 2-link
chain, a 3-link chain, three further 2-link chains with different link contents,
a SINGLE-exception representation, and three serialized forms carrying 2-link
lists — varying chain length, per-link traceback/crash/description, the presence
of a link ``description`` and ``extraline``, and the ``sections`` list (empty,
one-entry and two-entry). No two rivals share a refutation point, and the ``lr``
binder is moved across BOTH of its constructors. Every independent clause of both
obligations is attacked: on serialize, the link-list presence
(outermost-only), order (reverse), count (drop-first), per-link content
(const-link), WHICH link is outermost (outermost-from-head), and the ``.single``
arm's no-link-list rule (single-arm-empty-chain); on deserialize, the
chain-present arm's whole-chain rebuild (collapse), the rebuilt-chain order
(deserialize-reverse) and the sections carry-through (drop-sections) — so the
``s`` binder is moved to three points and its constructor choice, its per-index
content and its carried sections are all exercised.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
constraining ``opaque`` callee (``packLink``/``unpackLink`` are transparent
identities; the entry payload is modeled as data carried through). The nagini
``AXIOM_TESTS`` (an A-reference round-trip probe, G-AX's job) are dropped.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5787"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside an impl region (or, for the admissibility
# positive, the serialize proof region) so same_spec stays byte-identical and
# each theorem STATEMENT is untouched.

# The chained arm of the serialize impl (records the ordered link list).
_I_SER_CHAINED = (
    "  | .chained chain secs =>\n"
    "      let outer := outerOf chain\n"
    "      let mut serChain : List Link := []\n"
    "      for link in chain do\n"
    "        serChain := serChain ++ [packLink link]\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := some serChain }"
)

# The whole deserialize impl body (chain-present arm + no-chain arm).
_I_DES_BODY = (
    "  match s.chain with\n"
    "  | some (l :: ls) =>\n"
    "      let mut deChain : List Link := []\n"
    "      for link in (l :: ls) do\n"
    "        deChain := deChain ++ [unpackLink link]\n"
    "      return .chained deChain s.sections\n"
    "  | _ =>\n"
    "      return .single s.traceback s.crash s.sections"
)

# The head of the frozen serialize proof (its `intro`/`cases` opening), used as
# the insertion point for the admissibility ground instance.
_P_SER_HEAD = "  intro lr\n  cases lr with"


# Concrete multi-stage link lists used by the witnesses. Each is a genuine chain
# (>= 2 links) with distinct per-link traceback/crash so order and content are
# observable. Chosen so no two witnesses probe the same input.
_L_OUTER = (
    '[({ entries := ["r1"], extraline := none, style := "long" }, '
    '{ path := "f1", lineno := 11, message := "ValueError: 11" }, none), '
    '({ entries := ["r2"], extraline := some "x", style := "long" }, '
    '{ path := "f2", lineno := 12, message := "ValueError: 12" }, '
    'some "The above exception was the direct cause")]'
)
_L_DROP = (
    '[({ entries := ["a1"], extraline := none, style := "long" }, '
    '{ path := "g1", lineno := 21, message := "ValueError: 21" }, none), '
    '({ entries := ["a2"], extraline := none, style := "long" }, '
    '{ path := "g2", lineno := 22, message := "ValueError: 22" }, some "d"), '
    '({ entries := ["a3"], extraline := none, style := "long" }, '
    '{ path := "g3", lineno := 23, message := "ValueError: 23" }, some "d2")]'
)
_L_REV = (
    '[({ entries := ["p"], extraline := none, style := "s" }, '
    '{ path := "u", lineno := 1, message := "m1" }, none), '
    '({ entries := ["q"], extraline := none, style := "s" }, '
    '{ path := "v", lineno := 2, message := "m2" }, some "c")]'
)
_L_CONST = (
    '[({ entries := ["c1"], extraline := none, style := "s" }, '
    '{ path := "w", lineno := 5, message := "n1" }, none), '
    '({ entries := ["c2"], extraline := some "y", style := "s" }, '
    '{ path := "z", lineno := 6, message := "n2" }, some "cc")]'
)
_L_COL = (
    '[({ entries := ["d1"], extraline := none, style := "s" }, '
    '{ path := "k1", lineno := 7, message := "o1" }, none), '
    '({ entries := ["d2"], extraline := none, style := "s" }, '
    '{ path := "k2", lineno := 8, message := "o2" }, some "cd")]'
)
_L_DESREV = (
    '[({ entries := ["e1"], extraline := none, style := "s" }, '
    '{ path := "q1", lineno := 3, message := "p1" }, none), '
    '({ entries := ["e2"], extraline := none, style := "s" }, '
    '{ path := "q2", lineno := 4, message := "p2" }, some "cr")]'
)


def _ser_witness(links, secs):
    """A serialize refutation: the rival's recorded `.chain` differs from the
    spec's, so projecting that field and reducing the resulting decidable
    `Option (List Link)` equality yields `False`."""
    lr = f"(.chained {links} {secs})"
    return (
        "-- Refuted at a concrete multi-stage chain. Longrepr/SerializedLongrepr\n"
        "-- carry no DecidableEq, so the witness PROJECTS the recorded link list\n"
        "-- (SerializedLongrepr.chain) — a decidable Option (List Link) — on which\n"
        "-- the rival and the spec disagree, and simp reduces it to False. No\n"
        "-- hypothesis is bound, so there is nothing to be inconsistent.\n"
        f"example : ¬ problem_spec_serialize\n"
        f"    {lr}\n"
        f"    (implementation_serialize {lr}) := by\n"
        "  intro h\n"
        "  have hc := congrArg SerializedLongrepr.chain h\n"
        "  simp [implementation_serialize, serializeLongrepr, outerOf, packLink] at hc\n"
    )


# === POSITIVE CONTROLS (soundness) =========================================
# Structurally-different but CORRECT implementations that MUST verify. If a
# faithful correct impl cannot satisfy the frozen obligation the spec is
# SPEC-TOO-STRONG. Each keeps every theorem statement byte-identical and closes
# the proof honestly (no new lemma, no axiom, no sorry). Ports nagini's
# `pos-control-localreshape` — a local-variable reshape of the append loop — onto
# BOTH cooperating sites (one positive per modeled function).

_POS_SER = _swap(
    _BASE, _I_SER_CHAINED,
    "  | .chained chain secs =>\n"
    "      let outer := outerOf chain\n"
    "      let mut serChain : List Link := []\n"
    "      for link in chain do\n"
    "        let l := packLink link\n"
    "        serChain := serChain ++ [l]\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := some serChain }",
)

_POS_DES = _swap(
    _BASE, _I_DES_BODY,
    "  match s.chain with\n"
    "  | some (l :: ls) =>\n"
    "      let mut deChain : List Link := []\n"
    "      for link in (l :: ls) do\n"
    "        let u := unpackLink link\n"
    "        deChain := deChain ++ [u]\n"
    "      return .chained deChain s.sections\n"
    "  | _ =>\n"
    "      return .single s.traceback s.crash s.sections",
)

# AUDIT ADDITION — two STRONGER positives. The two positives above bind the
# per-link copy to a local inside the same loop, which zeta-reduces: their impls
# are near-definitionally the frozen ones, so they confirm little beyond that the
# frozen tactic survives a rename. The audit therefore added a genuinely
# different SHAPE at each site — the imperative accumulate-into-a-mutable-list
# loop is REMOVED entirely — and confirmed both verify (exit 0), so the frozen
# obligations are not merely satisfied by their own syntactic form.

# Serialize by a single `foldl` over the chain; no `for`, no mutable accumulator.
# Verifies under the frozen tactic script unchanged.
_POS_SER_FOLD = _swap(
    _BASE, _I_SER_CHAINED,
    "  | .chained chain secs =>\n"
    "      let outer := outerOf chain\n"
    "      let serChain := chain.foldl (fun acc link => acc ++ [packLink link]) []\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := some serChain }",
)

# Deserialize by a direct `List.map`; no loop and no accumulator, so the frozen
# proof's `key` flatten-lemma becomes unnecessary and the reproof drops it. This
# is the one positive that legitimately re-proves (a `proof` region edit), which
# `variant_scope` permits while holding every theorem STATEMENT byte-identical.
_POS_DES_MAP = _swap(
    _swap(
        _BASE, _I_DES_BODY,
        "  match s.chain with\n"
        "  | some (l :: ls) =>\n"
        "      return .chained ((l :: ls).map unpackLink) s.sections\n"
        "  | _ =>\n"
        "      return .single s.traceback s.crash s.sections",
    ),
    "  have key : ∀ (l : List Link), (List.map (fun x => [unpackLink x]) l).flatten = List.map unpackLink l := by\n"
    "    intro l; induction l with\n"
    "    | nil => simp\n"
    "    | cons a t ih => simp [ih]\n"
    "  unfold problem_spec_deserialize implementation_deserialize deserializeLongrepr\n"
    "  split <;> simp [key]",
    "  unfold problem_spec_deserialize implementation_deserialize deserializeLongrepr\n"
    "  split <;> simp",
)


# === ADMISSIBILITY =========================================================
# A positive control confirming the serialize obligation is SATISFIABLE
# (non-vacuous) at the normal, F2P-shaped multi-stage input. The frozen theorem
# carries no precondition hypothesis, so the nagini precondition-admission probe
# (`admiss-multistage`) has no binder to attack; the honest analogue discharges
# the spec predicate by `rfl` at a ground 2-link chain (an F2P scenario:
# ValueError(11) → ValueError(12) chained by "The above exception …") as a
# `have`, then closes the frozen obligation verbatim. Nothing is assumed: no new
# declaration, the statement is byte-identical, the ground instance is a `have`
# inside the existing tactic body.
_ADM_GROUND = (
    "  have _ground : problem_spec_serialize\n"
    f"      (.chained {_L_OUTER} [])\n"
    f"      (implementation_serialize (.chained {_L_OUTER} [])) := by\n"
    "    rfl\n"
    + _P_SER_HEAD
)
_ADMISS = _swap(_BASE, _P_SER_HEAD, _ADM_GROUND)


# === UNIQUENESS / SPEC-TOO-WEAK rivals =====================================
# Wrong implementations sharing the frozen spec that MUST be rejected. Each
# carries (a) the refinement argument that its faithful real patch would NOT
# resolve the F2P, and (b) a refutation witness pinning the violation at one
# concrete multi-stage input.

# (a) outermost-only serialize: emit `chain := none` for a chain (the pre-patch
# shape — the whole link list is dropped).
_OUTER_ONLY = _swap(
    _BASE, _I_SER_CHAINED,
    "  | .chained chain secs =>\n"
    "      let outer := outerOf chain\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := none }",
)

# (b) drop-first serialize: skip the originating (first) link.
_DROP_FIRST = _swap(
    _BASE, _I_SER_CHAINED,
    "  | .chained chain secs =>\n"
    "      let outer := outerOf chain\n"
    "      let mut serChain : List Link := []\n"
    "      for link in chain.drop 1 do\n"
    "        serChain := serChain ++ [packLink link]\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := some serChain }",
)

# (c) reversed serialize: record every link but newest-first.
_REVERSE = _swap(
    _BASE, _I_SER_CHAINED,
    "  | .chained chain secs =>\n"
    "      let outer := outerOf chain\n"
    "      let mut serChain : List Link := []\n"
    "      for link in chain do\n"
    "        serChain := packLink link :: serChain\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := some serChain }",
)

# (d) const-link serialize: record the CORRECT length but every slot carries the
# first link's content.
_CONST_LINK = _swap(
    _BASE, _I_SER_CHAINED,
    "  | .chained chain secs =>\n"
    "      let outer := outerOf chain\n"
    "      let mut serChain : List Link := []\n"
    "      for _link in chain do\n"
    "        serChain := serChain ++ [packLink (chain.headD default)]\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := some serChain }",
)

# (e) deserialize collapse: ignore the recorded link list, always rebuild a
# single exception (the pre-fix deserialization shape).
_DES_COLLAPSE = _swap(
    _BASE, _I_DES_BODY,
    "  match s.chain with\n"
    "  | _ =>\n"
    "      return .single s.traceback s.crash s.sections",
)

# (f) deserialize reversed: rebuild the whole chain but newest-first (order
# attack on the deserialize site — length preserved, order wrong).
_DES_REVERSE = _swap(
    _BASE, _I_DES_BODY,
    "  match s.chain with\n"
    "  | some (l :: ls) =>\n"
    "      let mut deChain : List Link := []\n"
    "      for link in (l :: ls) do\n"
    "        deChain := unpackLink link :: deChain\n"
    "      return .chained deChain s.sections\n"
    "  | _ =>\n"
    "      return .single s.traceback s.crash s.sections",
)

# (g) AUDIT ADDITION — outermost-from-head serialize. The audit found the
# `outerOf` clause (which of a chain's links is the OUTERMOST one, exposed as the
# serialized crash/traceback) entirely unattacked: every pre-existing serialize
# rival keeps `let outer := outerOf chain` verbatim, so the recorded
# crash/traceback pair was never moved off its correct value. This rival records
# the full link list correctly but takes the outermost crash/traceback from the
# chain's FIRST link instead of its LAST. Built and confirmed rejected (exit 1),
# with a witness confirmed to discriminate (rival exit 0 / gold exit 1).
_OUTER_HEAD = _swap(
    _BASE, _I_SER_CHAINED,
    "  | .chained chain secs =>\n"
    "      let outer := match chain.head? with\n"
    "        | some (tb, cr, _) => (tb, cr)\n"
    "        | none => ((default : Traceback), (default : FileLoc))\n"
    "      let mut serChain : List Link := []\n"
    "      for link in chain do\n"
    "        serChain := serChain ++ [packLink link]\n"
    "      return { crash := outer.2, traceback := outer.1, sections := secs,\n"
    "               chain := some serChain }",
)

# (h) AUDIT ADDITION — single-arm chain forgery. The audit found the serialize
# `.single` arm entirely unattacked: every pre-existing rival edits only the
# `.chained` arm, so the clause "a single exception records NO link list" was
# never probed. This rival keeps the chained arm verbatim and makes the single
# arm record `chain := some []` instead of `none` — a present-but-empty link
# list, which on the deserialize side is exactly the value that decides whether a
# representation rebuilds as a chain or as a single exception. Built and confirmed
# rejected (exit 1), witness confirmed to discriminate.
_SINGLE_EMPTY_CHAIN = _swap(
    _BASE,
    "  | .single tb cr secs =>\n"
    "      return { crash := cr, traceback := tb, sections := secs, chain := none }",
    "  | .single tb cr secs =>\n"
    "      return { crash := cr, traceback := tb, sections := secs, chain := some [] }",
)

# (i) SECOND-AUDIT ADDITION — deserialize drops the carried sections. The second
# audit found the SECTIONS carry-through clause unattacked by every shipped reject
# case: both obligations carry `sections` through unchanged, and while the frozen
# equality pins it, no rival had ever moved it off its correct value, so the clause
# was never probed on either site. (The first audit built two sections rivals as
# throwaway D-probes and promoted neither, leaving the gap open in the shipped
# battery.) This rival rebuilds the chain CORRECTLY — right count, right order,
# right per-link content — and drops only the titled sections. That is the finest
# surviving clause on the deserialize site, and it is F2P-relevant: the test asserts
# `longrepr.sections == [("title", "contents", "=")]` on the reconstructed
# representation, alongside the chain assertions. Built and confirmed rejected
# (exit 1); witness confirmed to discriminate (rival exit 0 / gold exit 1, gold's
# `hc` revealed as `True`).
_DES_DROP_SECTIONS = _swap(
    _BASE, _I_DES_BODY,
    "  match s.chain with\n"
    "  | some (l :: ls) =>\n"
    "      let mut deChain : List Link := []\n"
    "      for link in (l :: ls) do\n"
    "        deChain := deChain ++ [unpackLink link]\n"
    "      return .chained deChain []\n"
    "  | _ =>\n"
    "      return .single s.traceback s.crash s.sections",
)

# The sections rival's witness point: a fresh 2-link chain (`t`-prefixed, linenos
# 51/52) carrying a TWO-entry sections list — the longest sections list in the
# battery, and the only witness point where sections carry more than one entry.
_L_SECS = (
    '[({ entries := ["t1"], extraline := none, style := "s" }, '
    '{ path := "tp1", lineno := 51, message := "T: 51" }, none), '
    '({ entries := ["t2"], extraline := some "te", style := "s" }, '
    '{ path := "tp2", lineno := 52, message := "T: 52" }, some "td")]'
)
_SECS_TWO = '[("title", "contents", "="), ("second", "more", "-")]'

# Concrete inputs for the two audit-added rivals' witnesses. Both are fresh
# points: a 2-link chain with `h`-prefixed contents (distinct from every
# pre-existing witness), and the first `.single` input in the battery.
_L_HEAD = (
    '[({ entries := ["h1"], extraline := none, style := "s" }, '
    '{ path := "hp1", lineno := 41, message := "H: 41" }, none), '
    '({ entries := ["h2"], extraline := none, style := "s" }, '
    '{ path := "hp2", lineno := 42, message := "H: 42" }, some "hd")]'
)
_SINGLE_IN = (
    '(.single { entries := ["s1"], extraline := none, style := "long" } '
    '{ path := "sf", lineno := 9, message := "E: 9" } [("sec", "body", "sp")])'
)


SPEC_TESTS = [
    # ---------------------------------------------------------------- positives
    {
        "id": "pos-serialize-link-bound-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SER,
        "rationale": "structurally-different CORRECT serialize: the appended link "
        "is bound to a local `l` inside the loop before being recorded, instead of "
        "inlining `packLink link`. The recorded list is identical on every input, "
        "so `result = serializeLongrepr lr` still holds. Must verify, else the "
        "chain-recording clause is SPEC-TOO-STRONG. Proof: the frozen `induction "
        "chain` tactic closes for the reshaped loop (the local zeta-reduces). "
        "Ports nagini's local-reshape positive to the serialize site.",
    },
    {
        "id": "pos-deserialize-link-bound-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DES,
        "rationale": "structurally-different CORRECT deserialize: the rebuilt link "
        "is bound to a local `u` inside the loop before being appended, instead of "
        "inlining `unpackLink link`. The rebuilt chain is identical on every input, "
        "so `result = deserializeLongrepr s` still holds. Must verify, else the "
        "chain-rebuild clause is SPEC-TOO-STRONG. Proof: the frozen `split <;> simp "
        "[key]` closes for the reshaped loop. Defends the SECOND cooperating site "
        "with a correct reshape on a different region than the serialize positive.",
    },
    {
        "id": "pos-serialize-foldl",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SER_FOLD,
        "rationale": "structurally-different CORRECT serialize with the imperative "
        "loop REMOVED: the recorded link list is built by a single `foldl` over the "
        "chain — no `for`, no mutable accumulator — instead of appending into a "
        "`let mut`. Extensionally identical on every input, so `result = "
        "serializeLongrepr lr` still holds, and the frozen tactic script closes it "
        "unchanged. Added by the audit because the two local-binding positives "
        "zeta-reduce to the frozen impl and so confirm little; this one changes the "
        "shape of the recursion itself. Must verify, else the chain-recording clause "
        "is SPEC-TOO-STRONG in its accidental syntactic form.",
    },
    {
        "id": "pos-deserialize-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DES_MAP,
        "rationale": "structurally-different CORRECT deserialize with the imperative "
        "loop REMOVED: the chain is rebuilt by a direct `List.map` over the recorded "
        "links. Extensionally identical on every input, so `result = "
        "deserializeLongrepr s` still holds. The only case in the battery that "
        "legitimately RE-PROVES: with no accumulator loop the frozen proof's `key` "
        "flatten-lemma is unnecessary, so the reproof drops it and closes with "
        "`split <;> simp`. Every theorem STATEMENT stays byte-identical (the edit is "
        "confined to the impl and proof regions, which `variant_scope` permits), and "
        "no new declaration, lemma, axiom or `sorry` is introduced. Must verify, "
        "else the chain-rebuild clause is SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-ground-multistage",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the serialize obligation is discharged at a ground F2P-shaped "
        "2-link chain (ValueError(11) → ValueError(12), chained by the direct-cause "
        "connective) by `rfl` as a `have`, then the frozen obligation is closed "
        "verbatim. Verifies (else the modeled behavior is unsatisfiable at exactly "
        "the multi-stage shape the F2P exercises — the analogue of PRECOND-TOO-"
        "STRONG). Nothing is assumed: no new declaration, the theorem statement is "
        "byte-identical, the ground instance is a `have` inside the existing tactic "
        "body. Ports nagini's `admiss-multistage` probe.",
    },
    # ---------------------------------------------------------------- rejects
    {
        "id": "outermost-only-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _OUTER_ONLY,
        "refinement": "this IS the pre-patch bug: serialization recorded only the "
        "outermost traceback/crash and NO link list, so a chained failure collapses "
        "to a single stage after a round trip. The F2P asserts the reconstructed "
        "chain has length >= 2 with per-link content, so the faithful real patch "
        "would NOT resolve (it is the very bug the patch fixes).",
        "rationale": "REJECT from the serialize chain-recording clause: on a "
        "multi-stage chain the spec records `chain := some (links...)` while the "
        "rival records `chain := none`, so the recorded link list — hence `result` "
        "— differs. Binder: a 2-link chain, sections empty.",
        "witness": _ser_witness(_L_OUTER, "[]"),
    },
    {
        "id": "deserialize-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DES_COLLAPSE,
        "refinement": "this IS the pre-patch deserialize, which always rebuilt a "
        "single exception and ignored any recorded link list; even given a full "
        "transport form the chain collapses to length 1. The F2P reads the "
        "reconstructed chain back and asserts length >= 2, so the faithful real "
        "patch would NOT resolve. Pins the SECOND cooperating site.",
        "rationale": "REJECT from the deserialize chain-present arm: with a present "
        "non-empty link list the spec returns `.chained (both links, in order)` and "
        "the rival returns `.single (...)`, so the rebuilt chain is LOST entirely. "
        "The witness projects the rebuilt link list out of the returned `Longrepr` "
        "(a decidable `List Link`, with the rival's `.single` projecting to `[]`) "
        "and reduces the disagreement to False. Binder: a SerializedLongrepr "
        "carrying a 2-link list and a non-empty sections list — the presence/count "
        "attack on the deserialize site, complementing the order attack below.",
        # AUDIT REPAIR. The original witness closed with
        # `exact Longrepr.noConfusion h` after a `simp only [...] at h`. It
        # discriminated by EXIT CODE (rival 0 / gold 1) so the gate accepted it,
        # but the gold-side failure was `error: Type mismatch —
        # Longrepr.noConfusion h has type Longrepr.noConfusionType ?m (do let r ←
        # forIn ...)`, i.e. the `Id.run`/`forIn` term never reduced to a
        # constructor application, so `noConfusion` was ILL-TYPED against gold
        # rather than semantically false of it. A witness that fails on gold for a
        # typing/unfolding reason is not a discriminator (the gate cannot tell the
        # two apart). Replaced with the same PROJECTION shape the order rival on
        # this site uses — project the rebuilt link list out of the returned
        # `Longrepr` and let `simp` reduce the resulting decidable `List Link`
        # equality. Rebuilt both ways: elaborates against the rival (exit 0) and
        # fails on the frozen solution with `hc : True ⊢ False` (exit 1) — a
        # SEMANTIC refutation of the concrete claim. Independently confirmed that
        # gold SATISFIES the spec at this very input (`... := by rfl`, exit 0), so
        # the witness is substantively false of gold.
        "witness": (
            "-- Refuted at a serialized form carrying a 2-link list. The spec\n"
            "-- rebuilds the WHOLE chain (both links, in order); the rival collapses\n"
            "-- to a single exception, so the rebuilt link list is empty where the\n"
            "-- spec's has two entries. Longrepr carries no DecidableEq, so the\n"
            "-- witness PROJECTS the rebuilt link list (a decidable List Link) via a\n"
            "-- match — the collapsing rival's `.single` projects to `[]` — and simp\n"
            "-- reduces the disagreement to False. No hypothesis is bound, so there\n"
            "-- is nothing to be inconsistent.\n"
            "example : ¬ problem_spec_deserialize\n"
            "    { crash := { path := \"k2\", lineno := 8, message := \"o2\" },\n"
            "      traceback := { entries := [\"d2\"], extraline := none, style := \"s\" },\n"
            "      sections := [(\"z\", \"zc\", \"zs\")],\n"
            f"      chain := some {_L_COL} }}\n"
            "    (implementation_deserialize\n"
            "      { crash := { path := \"k2\", lineno := 8, message := \"o2\" },\n"
            "        traceback := { entries := [\"d2\"], extraline := none, style := \"s\" },\n"
            "        sections := [(\"z\", \"zc\", \"zs\")],\n"
            f"        chain := some {_L_COL} }}) := by\n"
            "  intro h\n"
            "  have hc := congrArg (fun r => match r with\n"
            "    | Longrepr.chained c _ => c\n"
            "    | Longrepr.single _ _ _ => ([] : List Link)) h\n"
            "  simp [implementation_deserialize, deserializeLongrepr, unpackLink] at hc\n"
        ),
    },
    {
        "id": "drop-first-link-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_FIRST,
        "refinement": "a faithful patch serializing the chain with its first link "
        "dropped would omit the originating exception (root cause) from the "
        "transport form; the F2P builds a chain and checks EVERY link, so the "
        "dropped root cause fails the length and per-link-content assertions — it "
        "would NOT resolve.",
        "rationale": "REJECT from the serialize count/content clause: the spec "
        "records all N links, the rival records N-1 (missing the first), so the "
        "recorded list differs in length and per-index content. Binder DISTINCT "
        "from every other rival: a 3-LINK chain with a non-empty sections list, so "
        "chain length and the sections binder are both moved.",
        "witness": _ser_witness(_L_DROP, '[("s1", "b1", "sep1")]'),
    },
    {
        "id": "reverse-order-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REVERSE,
        "refinement": "a faithful patch recording the links newest-first would "
        "present the outermost failure as the root cause after a round trip; the "
        "F2P asserts per-index equality of the reconstructed chain, so reversed "
        "order fails per index — it would NOT resolve. Length is preserved, so ONLY "
        "the order clause catches it.",
        "rationale": "REJECT from the serialize ORDER clause: the recorded list has "
        "the correct length but reversed order, so it differs from `chain.map "
        "packLink` per index. Binder: a 2-link chain with link contents distinct "
        "from every other witness (traceback `p`/`q`), sections empty.",
        "witness": _ser_witness(_L_REV, "[]"),
    },
    {
        "id": "const-first-link-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _CONST_LINK,
        "refinement": "a faithful patch that copied the first link's content into "
        "every recorded slot would duplicate the originating cause across all "
        "stages; the F2P asserts each reconstructed link matches the original at "
        "its index, so the duplicated content fails for the later stage(s) — it "
        "would NOT resolve. Length is preserved, so ONLY the per-link-content "
        "clause catches it (value-level).",
        "rationale": "REJECT from the serialize per-link CONTENT clause: the "
        "recorded list has the correct length but every slot carries the first "
        "link, so positions >= 1 differ from `chain.map packLink`. Binder DISTINCT: "
        "a 2-link chain with contents `c1`/`c2` (second link carries an extraline) "
        "and a non-empty sections list.",
        "witness": _ser_witness(_L_CONST, '[("n", "c", "x")]'),
    },
    {
        "id": "reverse-order-deserialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DES_REVERSE,
        "refinement": "a faithful patch rebuilding the chain newest-first would "
        "invert the stage order on reconstruction, presenting the outermost failure "
        "as the root cause; the F2P asserts per-index equality of the reconstructed "
        "chain, so reversed order fails per index — it would NOT resolve. Length is "
        "preserved, so ONLY the order clause catches it, and it does so on the "
        "DESERIALIZE site (the round-trip's second half).",
        "rationale": "REJECT from the deserialize chain-rebuild ORDER clause: the "
        "rebuilt `.chained` list has the correct length but reversed order, so it "
        "differs from `(l :: ls).map unpackLink` per index. Witness projects the "
        "rebuilt link list (a decidable `List Link`) and reduces it to False. Binder "
        "DISTINCT from the collapse rival: a SerializedLongrepr carrying a 2-link "
        "list with contents `e1`/`e2`, sections empty — so the deserialize input "
        "binder `s` is moved to a second point and the second cooperating site now "
        "has its order clause attacked (not only its constructor).",
        "witness": (
            "-- Refuted at a serialized form carrying a 2-link list. The rebuilt\n"
            "-- chain must preserve order; the rival reverses it. Longrepr has no\n"
            "-- DecidableEq, so the witness PROJECTS the rebuilt link list (a\n"
            "-- decidable List Link) via a match and simp reduces it to False. No\n"
            "-- hypothesis is bound.\n"
            "example : ¬ problem_spec_deserialize\n"
            "    { crash := { path := \"q2\", lineno := 4, message := \"p2\" },\n"
            "      traceback := { entries := [\"e2\"], extraline := none, style := \"s\" },\n"
            "      sections := [],\n"
            f"      chain := some {_L_DESREV} }}\n"
            "    (implementation_deserialize\n"
            "      { crash := { path := \"q2\", lineno := 4, message := \"p2\" },\n"
            "        traceback := { entries := [\"e2\"], extraline := none, style := \"s\" },\n"
            "        sections := [],\n"
            f"        chain := some {_L_DESREV} }}) := by\n"
            "  intro h\n"
            "  have hc := congrArg (fun r => match r with\n"
            "    | Longrepr.chained c _ => c\n"
            "    | Longrepr.single _ _ _ => ([] : List Link)) h\n"
            "  simp [implementation_deserialize, deserializeLongrepr, unpackLink] at hc\n"
        ),
    },
    # ------------------------------------------------ rejects added by the audit
    {
        "id": "outermost-from-head-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _OUTER_HEAD,
        "refinement": "a faithful patch that read the outermost traceback/crash off "
        "the chain's FIRST link would advertise the originating (root-cause) "
        "exception as the failure's headline crash, while the link list itself "
        "stayed correct. The F2P compares the reconstructed representation's "
        "outermost crash/traceback against the original's — which are the LAST "
        "link's — so a chain whose first and last links differ fails that "
        "comparison; it would NOT resolve. The link list is fully preserved, so "
        "ONLY the outermost-selection clause catches it.",
        "rationale": "REJECT from the serialize OUTERMOST clause, which the rest of "
        "the battery leaves unattacked: every other serialize rival keeps `let "
        "outer := outerOf chain` verbatim and attacks the recorded list instead, so "
        "the recorded crash/traceback was never moved off its correct value. The "
        "spec pins them to the chain's LAST link; this rival takes them from the "
        "FIRST. The witness projects `SerializedLongrepr.crash` — a decidable "
        "FileLoc equality — at a 2-link chain whose two crash locations differ. "
        "Binder DISTINCT from every other witness: `h`-prefixed contents, linenos "
        "41/42, sections empty.",
        "witness": (
            "-- Refuted at a concrete 2-link chain whose first and last links carry\n"
            "-- DIFFERENT crash locations. The spec exposes the LAST link's crash as\n"
            "-- the outermost one; the rival exposes the first link's. The witness\n"
            "-- projects SerializedLongrepr.crash (a decidable FileLoc) and simp\n"
            "-- reduces the disagreement to False. No hypothesis is bound.\n"
            "example : ¬ problem_spec_serialize\n"
            f"    (.chained {_L_HEAD} [])\n"
            f"    (implementation_serialize (.chained {_L_HEAD} [])) := by\n"
            "  intro h\n"
            "  have hc := congrArg SerializedLongrepr.crash h\n"
            "  simp [implementation_serialize, serializeLongrepr, outerOf] at hc\n"
        ),
    },
    {
        "id": "single-arm-empty-chain-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SINGLE_EMPTY_CHAIN,
        "refinement": "a faithful patch whose single-exception branch emitted an "
        "empty link list instead of none would put a chain key into the builtin "
        "data for a failure that has no chain — a WIRE-FORMAT divergence from the "
        "modeled behavior, which the frozen equality pins exactly. "
        "SCOPE OF THE CLAIM, corrected by the second audit (the earlier text "
        "claimed this rival would break a P2P because 'the two halves of the round "
        "trip would disagree about whether the representation is chained', and that "
        "is FALSE — the audit disproved it by building the round trip): "
        "deserialization sends a present-but-EMPTY link list and an ABSENT one to "
        "the same `.single`, so `deserializeLongrepr { serializeLongrepr single "
        "with chain := some [] } = deserializeLongrepr (serializeLongrepr single)` "
        "is PROVABLE (`by simp [serializeLongrepr, deserializeLongrepr]`, exit 0). "
        "The reconstructed representation is therefore IDENTICAL and no test that "
        "only reads it back can see the difference. This case is kept, honestly "
        "scoped: it is a REJECT because the frozen serialize obligation is an exact "
        "equality on the builtin-data form, so the wire value is observable AT THE "
        "SERIALIZE SITE even where the end-to-end round trip masks it — and that is "
        "the only clause it attests to. It is NOT claimed to be F2P- or P2P-"
        "breaking. Contrast the chained-arm rivals, whose divergence the audit "
        "confirmed IS end-to-end visible (the same probe proves `... with chain := "
        "none` `≠` the spec's round trip, exit 0).",
        "rationale": "REJECT from the serialize SINGLE arm — the arm no other case "
        "in this battery touches (every other rival edits only the `.chained` arm, "
        "so the clause `a single exception records NO link list` was never probed). "
        "The spec requires `chain := none` for a single exception; this rival emits "
        "`some []`. The witness projects `SerializedLongrepr.chain` — a decidable "
        "`Option (List Link)` — at the battery's only `.single` input, which is also "
        "a binder point no other witness visits (the `lr` binder's OTHER "
        "constructor, with a non-empty sections list).",
        "witness": (
            "-- Refuted at a concrete SINGLE-exception input (the other constructor\n"
            "-- of the serialize binder). The spec records NO link list for a single\n"
            "-- exception (`chain := none`); the rival records a present-but-empty\n"
            "-- one (`some []`). The witness projects SerializedLongrepr.chain — a\n"
            "-- decidable Option (List Link) — and simp reduces `none = some []` to\n"
            "-- False. No hypothesis is bound.\n"
            "example : ¬ problem_spec_serialize\n"
            f"    {_SINGLE_IN}\n"
            f"    (implementation_serialize {_SINGLE_IN}) := by\n"
            "  intro h\n"
            "  have hc := congrArg SerializedLongrepr.chain h\n"
            "  simp [implementation_serialize, serializeLongrepr] at hc\n"
        ),
    },
    # ----------------------------------------- reject added by the SECOND audit
    {
        "id": "drop-sections-deserialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DES_DROP_SECTIONS,
        "refinement": "a faithful patch that rebuilt the chain correctly but dropped "
        "the titled sections would lose the captured output/report sections attached "
        "to a failure, while the chain itself looked perfect. The F2P checks the "
        "reconstructed representation's sections against the original's — one titled "
        "section, added before the round trip — in the SAME assertion block as the "
        "chain length and per-link content, so a patch that dropped them fails the "
        "F2P even with the chain fully preserved; it would NOT resolve. The chain is "
        "untouched, so ONLY the sections carry-through clause catches it.",
        "rationale": "REJECT from the deserialize SECTIONS carry-through clause, "
        "which every other case in the battery leaves unattacked: both obligations "
        "carry `sections` through unchanged, and while the frozen equality pins the "
        "field, no other rival moves it off its correct value — so the clause was "
        "never probed on either site. The spec rebuilds `.chained (links) s.sections`; "
        "this rival rebuilds `.chained (links) []` with the links still right. The "
        "witness projects the rebuilt SECTIONS out of the returned `Longrepr` — a "
        "decidable `List (String × String × String)`, projected via a match so both "
        "constructors are total — and simp reduces the disagreement to False. Binder "
        "DISTINCT from every other witness: `t`-prefixed links at linenos 51/52 and "
        "the battery's only TWO-entry sections list, so the sections binder is moved "
        "off both `[]` and the single-entry points the other cases use.",
        "witness": (
            "-- Refuted at a serialized form carrying BOTH a 2-link list and a\n"
            "-- non-empty sections list. The spec carries the sections through\n"
            "-- unchanged onto the rebuilt `.chained`; the rival drops them. Longrepr\n"
            "-- carries no DecidableEq, so the witness PROJECTS the rebuilt SECTIONS\n"
            "-- (a decidable List (String × String × String)) via a match — total on\n"
            "-- both constructors — and simp reduces the disagreement to False. No\n"
            "-- hypothesis is bound, so there is nothing to be inconsistent.\n"
            "example : ¬ problem_spec_deserialize\n"
            "    { crash := { path := \"tp2\", lineno := 52, message := \"T: 52\" },\n"
            "      traceback := { entries := [\"t2\"], extraline := some \"te\", style := \"s\" },\n"
            f"      sections := {_SECS_TWO},\n"
            f"      chain := some {_L_SECS} }}\n"
            "    (implementation_deserialize\n"
            "      { crash := { path := \"tp2\", lineno := 52, message := \"T: 52\" },\n"
            "        traceback := { entries := [\"t2\"], extraline := some \"te\", style := \"s\" },\n"
            f"        sections := {_SECS_TWO},\n"
            f"        chain := some {_L_SECS} }}) := by\n"
            "  intro h\n"
            "  have hc := congrArg (fun r => match r with\n"
            "    | Longrepr.chained _ secs => secs\n"
            "    | Longrepr.single _ _ secs => secs) h\n"
            "  simp [implementation_deserialize, deserializeLongrepr, unpackLink] at hc\n"
        ),
    },
]


# === AXIOM LANE ============================================================
# EMPTY. The bundle consumes no `axiom` and declares no constraining `opaque`
# callee: the (de)serialize logic including the per-link entry-payload copy is
# modeled deeply (`packLink`/`unpackLink` = identity). The nagini AXIOM_TESTS (an
# A-reference round-trip probe) belong to the G-AX lane, which this gate ignores;
# dropped.
AXIOM_TESTS = []
