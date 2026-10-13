"""properties.py — G-PBT falsification battery for django__django-16502 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
case is a COMPLETE ``Solution.lean`` variant built by region surgery, so it
shares the FROZEN spec byte-for-byte: only text strictly inside an
``-- impl-start`` / ``-- impl-end`` region — and, where a correct reshape must
legitimately re-prove, inside a ``-- proof-start`` / ``-- proof-end`` region —
is replaced. ``markers.same_spec`` therefore holds by construction and every
``theorem correct_<name>`` STATEMENT stays byte-identical, so a rejection is
attributable to the postcondition rather than to a tampered contract. No case
introduces an axiom, a helper lemma, a new theorem, or ``sorry``/``admit``/
``native_decide``.

``expect:"verify"`` passes iff the variant is in scope AND the file elaborates
with every obligation closed. ``expect:"reject"`` passes iff the variant is in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

------------------------------------------------------------------------------
DEFENDED SURFACE — two independent behaviors, each a full input→output relation
over a small record of observable booleans:

  headerPolicy (c : HeaderCtx) -> HeaderResult
    (i)  result.contentLengthPresent = (c.contentLengthSet && !c.isHead)
    (ii) result.connectionDisconnect =
           ((!c.isHead && !c.contentLengthSet) || !c.isThreading || c.appDisconnect)

  bodyEmission (c : BodyCtx) -> BodyResult
    (iii) result.bodyEmitted = !c.isHead
    (iv)  result.headersSent  = true

Clause (i) is the load-bearing one for the body-length header: it pins the
header's presence to the CONJUNCTION of "the base step left one" and "the
request wants an entity body", so it is violated both by keeping the header for
a metadata-only request AND by dropping it for an ordinary one. Clause (ii) is
the discriminator for the connection-persistence signal: the signal is asserted
for an ordinary response of unknown length, a single-request server, or an
application that already asked for non-reuse — and, crucially, NOT merely
because a metadata-only response carries no length. Clause (iii) is the headline
behavior (no entity body for a metadata-only request, the full body otherwise);
clause (iv) pins the second observable of the same computation, which the
metadata-only branch must establish itself rather than inherit from its input.

Both clauses of each obligation are grounded entirely in the inputs — each is an
equality against a boolean term built only from the argument record, fully
unfolded by ``decide``. The bundle declares no ``opaque`` and no ``axiom``, so
there is no answer key an implementation could ECHO instead of computing, and no
term on which a witness would have to condition: every refutation below is
stated at concrete literals. In place of an echo rival the battery carries
honest cheapest-implementation positive controls.

------------------------------------------------------------------------------
CLASS-BY-CLASS ADVERSARIAL READ (what the nagini sibling probes, re-expressed
against this carrier):

  * VALUE / PARTIAL-DOMAIN — APPLIES, and is the whole reject lane here. Each
    rival is correct on part of the input cube and diverges on a sub-domain: the
    pre-fix policy, the two one-sided errors on the length-header clause
    (never drop / always drop), the over-assertion of the non-reuse signal, the
    two UNDER-assertions of that same signal (one per remaining disjunct), and
    three rivals on the body-emission pair. Clause (ii) is a three-way
    disjunction, so it is probed in BOTH directions: a rival that asserts the
    signal where the clause forbids it, and — for each of the other two
    disjuncts — a rival that withholds it where the clause demands it.

  * CONTROL-FLOW-EFFECT — APPLIES to bodyEmission clause (iv). The metadata-only
    branch's second observable is not a value it returns but an effect it must
    ENSURE (the response metadata reaches the stream even though no body will),
    and its entry value is an INPUT. A rival that computes the body decision
    correctly and simply leaves that observable at whatever it came in as is
    wrong exactly on the sub-domain where the metadata had not yet been written.

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory probe
    on this instance writes to an input held at half permission. Lean is
    referentially transparent: no input carries a heap permission, there is no
    read-only fraction to overwrite and no aliasing to exploit, so the class has
    no expressible instance and NO substitute is fabricated for it.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend. Each
    ``implementation_*`` is a total Lean ``def`` over a finite record; a
    diverging implementation cannot be written at all, so there is nothing for a
    rival to exploit and no spec hole to record. (This is NOT the velvet
    disposition, where a partial-termination setting lets a non-terminating
    implementation satisfy every clause vacuously; see
    the corpus-wide termination-semantics finding.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS, per the grounding argument above.

  * AXIOM LANE — EMPTY. meta.json records axioms == [] and
    deep_model_references == []; both behaviors are total computations over
    their own argument records. The nagini sibling's AXIOM_TESTS were empty for
    the same reason, and that lane belongs to G-AX regardless.

------------------------------------------------------------------------------
WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection on its own attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input; each was checked to hold of its rival and to FAIL on the
frozen solution, so it discriminates rather than asserting a tautology. Every
witness binds nothing (no conditioning is needed on a fully computable carrier),
so no witness can be refuted-by-inconsistent-hypothesis.

The nine refutation points are spread across the input cube rather than fixed
at one convenient cell, so the battery says something about the spec's
dependence on EVERY input:

  headerPolicy (isHead, contentLengthSet, isThreading, appDisconnect)
    weak-header-prefix                (T, T, T, F)   the metadata-only F2P cell
    weak-header-length-kept           (T, T, F, T)   single-request server AND an
                                                     application-requested
                                                     non-reuse, so neither of
                                                     those inputs is pinned
    weak-header-length-always-dropped (F, T, T, F)   the ordinary-method F2P cell
    weak-header-signal-on-any-missing (T, F, T, F)   no length left by the base
                                                     step
    weak-header-signal-drops-single   (T, T, F, F)   single-request server, the
                                                     ONLY disjunct that can fire
                                                     at this cell
    weak-header-signal-drops-app      (F, T, T, T)   application-requested
                                                     non-reuse, likewise the only
                                                     disjunct that can fire here
  bodyEmission (isHead, headersAlreadySent)
    weak-body-always-emits            (T, T)
    weak-body-never-emits             (F, T)
    weak-body-metadata-not-ensured    (T, F)

Each of the four ``headerPolicy`` inputs and both ``bodyEmission`` inputs is
therefore observed at BOTH settings across the reject witnesses. Rivals that
diverge on overlapping cells are still refuted at DIFFERENT points and against
different clauses, so no rival's rationale claims a sub-domain the manifest
never demonstrates; the two rivals that both touch the metadata-only /
length-present cell are separated there by clause: ``weak-header-prefix`` is
refuted through clause (i) while ``weak-header-signal-on-any-missing`` satisfies
clause (i) everywhere and is refuted through clause (ii), at a cell where the
base step left no length at all.

DIRECTIONALITY OF CLAUSE (ii). The clause is an EQUALITY to a three-way
disjunction, so a battery that only ever refutes it by OVER-assertion leaves
half of it undemonstrated: nothing would show the spec compels the signal where
a disjunct is live. ``weak-header-signal-drops-single`` and
``weak-header-signal-drops-app`` supply the missing direction, one per remaining
disjunct, each refuted at a cell where its own disjunct is the ONLY true one —
so each attributes the failure to that disjunct alone rather than to the
disjunction as a whole. Together with ``weak-header-signal-on-any-missing``
(over-assertion, the method gate) all three disjuncts of clause (ii) are
independently demonstrated to be load-bearing, in the direction each can fail.
"""
from pathlib import Path

INSTANCE = "django__django-16502"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of one impl region or the FULL tactic
# body of one proof region, and each occurs exactly once in Solution.lean (both
# invariants asserted by _swap at load, so drift in the frozen solution breaks
# this manifest loudly instead of silently retargeting a replacement).
# ---------------------------------------------------------------------------

_I_HEADER = (
    "  let mut clPresent := c.contentLengthSet\n"
    "  -- A metadata-only response must not advertise a body length.\n"
    "  if c.isHead && clPresent then\n"
    "    clPresent := false\n"
    "  let mut disconnect := c.appDisconnect\n"
    "  if !c.isHead && !clPresent then\n"
    "    disconnect := true\n"
    "  else if !c.isThreading then\n"
    "    disconnect := true\n"
    "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n"
)

_P_HEADER = (
    "  intro c\n"
    "  obtain ⟨isHead, contentLengthSet, isThreading, appDisconnect⟩ := c\n"
    "  cases isHead <;> cases contentLengthSet <;> cases isThreading <;> "
    "cases appDisconnect <;>\n"
    "    exact ⟨rfl, rfl⟩\n"
)

_I_BODY = (
    "  if c.isHead then\n"
    "    -- Drain the application's output without writing any body bytes, then\n"
    "    -- ensure the headers have been written.\n"
    "    let mut sent := c.headersAlreadySent\n"
    "    if !sent then\n"
    "      sent := true\n"
    "    return { bodyEmitted := false, headersSent := sent }\n"
    "  else\n"
    "    -- Defer to the standard writer: it emits the headers then the body.\n"
    "    return { bodyEmitted := true, headersSent := true }\n"
)


# ---------------------------------------------------------------------------
# Witness helpers (plain string building; nothing Lean-semantic lives here).
# ---------------------------------------------------------------------------

def _hctx(is_head, cl_set, threading, app_disc):
    return ("{ isHead := %s, contentLengthSet := %s, isThreading := %s, "
            "appDisconnect := %s }" % (is_head, cl_set, threading, app_disc))


def _bctx(is_head, already_sent):
    return "{ isHead := %s, headersAlreadySent := %s }" % (is_head, already_sent)


def _refute_header(comment, is_head, cl_set, threading, app_disc):
    ctx = _hctx(is_head, cl_set, threading, app_disc)
    return (comment
            + "example : ¬ problem_spec_headerPolicy\n"
            + f"    {ctx}\n"
            + f"    (implementation_headerPolicy\n      {ctx}) := by\n"
            + "  unfold problem_spec_headerPolicy implementation_headerPolicy\n"
            + "  decide\n")


def _refute_body(comment, is_head, already_sent):
    ctx = _bctx(is_head, already_sent)
    return (comment
            + "example : ¬ problem_spec_bodyEmission\n"
            + f"    {ctx}\n"
            + f"    (implementation_bodyEmission\n      {ctx}) := by\n"
            + "  unfold problem_spec_bodyEmission implementation_bodyEmission\n"
            + "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # of the modeled behavior cannot satisfy the frozen obligation, the
    # postcondition is over-fit to the frozen statement shape =>
    # SPEC-TOO-STRONG. Each keeps the `theorem correct_<name>` statement
    # byte-identical; where the frozen tactic body no longer applies to the
    # new shape the obligation is RE-PROVED with core tactics only (no helper
    # lemma, no axiom, no assumption token).
    # =====================================================================
    {
        "id": "pos-header-decision-as-local",
        "kind": "soundness",
        "expect": "verify",
        # Stage the non-reuse decision into an explicit local boolean computed
        # in ONE expression from the post-drop state, then return both
        # components from locals. A different control-flow source (a single
        # boolean formula instead of the frozen if/else-if chain) with the same
        # value on the whole 2^4 input cube.
        "module": _swap(
            _BASE, _I_HEADER,
            "  -- A metadata-only response must not advertise a body length; decide\n"
            "  -- the non-reuse signal from the post-drop state in one expression.\n"
            "  let clPresent := c.contentLengthSet && !c.isHead\n"
            "  let disconnect :=\n"
            "    (!c.isHead && !clPresent) || !c.isThreading || c.appDisconnect\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "rationale": "the cheapest honest implementation of the header policy: "
                     "both observables computed as single boolean formulas over "
                     "the argument record, replacing the frozen mutable-local "
                     "if/else-if chain. Identical on every one of the 16 inputs, "
                     "so clauses (i) and (ii) must both still hold; if this "
                     "cannot verify, the postcondition is pinned to the frozen "
                     "control shape rather than to the behavior => "
                     "SPEC-TOO-STRONG. It is also the grounding control: the "
                     "decision is COMPUTED from the inputs, not echoed from any "
                     "oracle. Proof: the frozen tactic body is retained — the "
                     "exhaustive case split still reduces both sides to literals.",
    },
    {
        "id": "pos-header-guards-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder: test the single-request-server guard FIRST and the
        # ordinary-response-of-unknown-length guard second — the opposite
        # evaluation order to the frozen chain. Both arms assert the same
        # signal, so the reachable result set is unchanged.
        "module": _swap(
            _BASE, _I_HEADER,
            "  let mut clPresent := c.contentLengthSet\n"
            "  -- A metadata-only response must not advertise a body length.\n"
            "  if c.isHead && clPresent then\n"
            "    clPresent := false\n"
            "  let mut disconnect := c.appDisconnect\n"
            "  -- Reordered guards: the single-request-server case is examined\n"
            "  -- first, the unknown-length ordinary response second.\n"
            "  if !c.isThreading then\n"
            "    disconnect := true\n"
            "  else if !c.isHead && !clPresent then\n"
            "    disconnect := true\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "rationale": "swapping the two guards that assert the non-reuse signal "
                     "cannot change the result — both arms set the same value, "
                     "so the union they cover is order-independent — hence "
                     "clause (ii) still holds pointwise and clause (i) is "
                     "untouched. Must verify; if it does not, the spec is "
                     "over-fit to the frozen guard ORDER => SPEC-TOO-STRONG. "
                     "Proof: frozen tactic body retained.",
    },
    {
        "id": "pos-body-branchless",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the two-arm branch into the pair of values it computes: the
        # body decision is the negation of the metadata-only flag and the
        # metadata observable is established unconditionally. Same result on
        # both inputs, including the ensure-step the frozen metadata-only arm
        # spells out with a mutable local.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Whether the entity body reaches the stream is exactly the\n"
            "  -- negation of the metadata-only flag; the response metadata is\n"
            "  -- ensured written either way.\n"
            "  return { bodyEmitted := !c.isHead, headersSent := true }\n",
        ),
        "rationale": "a correct branchless reshape of the body-emission pair: "
                     "clause (iii) is the definition of the returned first "
                     "component and clause (iv) of the second, so both hold on "
                     "both inputs. Must verify; if it does not, the spec is "
                     "pinned to the frozen branch-and-mutable-local shape => "
                     "SPEC-TOO-STRONG. Note this is the strongest positive on "
                     "the metadata observable: the frozen implementation reaches "
                     "`true` through its input, this one ignores the input "
                     "entirely, and the spec must accept both because clause "
                     "(iv) constrains only the exit state. Proof: frozen tactic "
                     "body retained.",
    },
    {
        "id": "pos-body-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Control-flow reorder: handle the ordinary method in the guard and let
        # the metadata-only path fall through, keeping the explicit ensure-step
        # (now written as a match on the entry state rather than a mutable
        # local). Same values on both inputs.
        "module": _swap(
            _BASE, _I_BODY,
            "  if !c.isHead then\n"
            "    -- Defer to the standard writer: it emits the headers then the body.\n"
            "    return { bodyEmitted := true, headersSent := true }\n"
            "  -- Drain the application's output without writing any body bytes,\n"
            "  -- then ensure the headers have been written.\n"
            "  match c.headersAlreadySent with\n"
            "  | true  => return { bodyEmitted := false, headersSent := true }\n"
            "  | false => return { bodyEmitted := false, headersSent := true }\n",
        ),
        "rationale": "reordering the two exits behind a negated guard and "
                     "spelling the ensure-step as an explicit split on the entry "
                     "state preserves both components on both inputs, so clauses "
                     "(iii) and (iv) still hold. Must verify (else "
                     "SPEC-TOO-STRONG on the body-emission obligation). Proof: "
                     "frozen tactic body retained — the exhaustive split over "
                     "both inputs still reduces each side to a literal.",
    },

    # =====================================================================
    # ADMISSIBILITY — the frozen obligations carry NO precondition hypothesis
    # (every modeled behavior is total, so each `∀` is unguarded), so the
    # nagini sibling's precondition-satisfiability probe has no binder to
    # attack here. The honest analogue is to show the obligation is
    # SATISFIABLE at the concrete, F2P-shaped inputs rather than only provable
    # in the abstract: both legs the F2P exercises are discharged by evaluation
    # as `have`s inside the existing tactic body, alongside the frozen
    # obligation. If a ground instance at the normal input could not be
    # discharged, the modeled behavior would be unsatisfiable at exactly the
    # point the test observes (the analogue of PRECOND-TOO-STRONG).
    # =====================================================================
    {
        "id": "admiss-header-f2p-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_HEADER,
            "  -- The two ground instances the test observes: a multi-request\n"
            "  -- server, no application-requested non-reuse, and a body length\n"
            "  -- left by the base step — once for an ordinary method, once for a\n"
            "  -- metadata-only one.\n"
            "  have _ordinary : problem_spec_headerPolicy\n"
            f"      {_hctx('false', 'true', 'true', 'false')}\n"
            "      (implementation_headerPolicy\n"
            f"        {_hctx('false', 'true', 'true', 'false')}) := by\n"
            "    unfold problem_spec_headerPolicy implementation_headerPolicy\n"
            "    decide\n"
            "  have _metadata_only : problem_spec_headerPolicy\n"
            f"      {_hctx('true', 'true', 'true', 'false')}\n"
            "      (implementation_headerPolicy\n"
            f"        {_hctx('true', 'true', 'true', 'false')}) := by\n"
            "    unfold problem_spec_headerPolicy implementation_headerPolicy\n"
            "    decide\n"
            + _P_HEADER,
        ),
        "rationale": "the headerPolicy obligation is discharged by `decide` at "
                     "the two ground inputs the F2P exercises — a multi-request "
                     "server with a base-supplied body length and no "
                     "application-requested non-reuse, once for an ordinary "
                     "method and once for a metadata-only one — and the frozen "
                     "obligation is then closed verbatim. Verifies iff the spec "
                     "is jointly satisfiable at the normal input, i.e. clauses "
                     "(i) and (ii) do not contradict each other there. Nothing "
                     "is assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instances are `have`s "
                     "inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival is a genuine verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, checked to hold of the rival and to FAIL on gold.
    # =====================================================================

    # ---- headerPolicy, clauses (i) and (ii) ----
    {
        "id": "weak-header-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-FIX policy for this behavior: the metadata-only method is not
        # distinguished at all — the body-length header is left exactly as the
        # base step produced it, and the non-reuse signal is asserted on any
        # response lacking a length, whatever the method.
        "module": _swap(
            _BASE, _I_HEADER,
            "  -- Does not distinguish the metadata-only method: the body-length\n"
            "  -- header is left as found and the non-reuse signal is asserted on\n"
            "  -- any response of unknown length.\n"
            "  let clPresent := c.contentLengthSet\n"
            "  let mut disconnect := c.appDisconnect\n"
            "  if !clPresent then\n"
            "    disconnect := true\n"
            "  else if !c.isThreading then\n"
            "    disconnect := true\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "refinement": "this is the pre-existing header policy, method-blind on "
                      "both counts. Its faithful real patch is the UNCHANGED "
                      "code, under which a metadata-only response still "
                      "advertises the body length the base step computed and, "
                      "when no length is known, also carries the non-reuse "
                      "signal. The F2P test asserts of the metadata-only "
                      "response that NO body-length header line appears at all "
                      "and that the non-reuse signal is absent, so it would NOT "
                      "resolve — it is the very defect the change removes.",
        "rationale": "REJECT from clause (i) `result.contentLengthPresent = "
                     "(c.contentLengthSet && !c.isHead)`: at the metadata-only F2P "
                     "cell (isHead, contentLengthSet, isThreading, "
                     "appDisconnect) = (T, T, T, F) the spec requires `false` and "
                     "the rival returns the base step's `true`. If it verified => "
                     "SPEC-TOO-WEAK (the spec admits the pre-fix policy). "
                     "Refuted at contentLengthSet = T, which is where clause (i) "
                     "can separate them; the rival is ALSO wrong on clause (ii) "
                     "at contentLengthSet = F, and that neighbouring cell is "
                     "where `weak-header-signal-on-any-missing` — which satisfies "
                     "clause (i) everywhere — is refuted instead, so the two "
                     "rivals are demonstrated at different points and through "
                     "different clauses.",
        "witness": _refute_header(
            "-- The metadata-only cell the test observes: a multi-request server,\n"
            "-- no application-requested non-reuse, and a body length left by the\n"
            "-- base step. The length must not survive onto a response that will\n"
            "-- carry no entity body.\n",
            "true", "true", "true", "false"),
    },
    {
        "id": "weak-header-length-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # One-sided error isolated to clause (i): the non-reuse decision is
        # computed exactly as the frozen policy does, but the body-length header
        # is never dropped for a metadata-only response. (Because the frozen
        # non-reuse guard is itself gated on the method, omitting the drop leaves
        # clause (ii) untouched on the whole cube — the defect is confined to
        # clause (i).)
        "module": _swap(
            _BASE, _I_HEADER,
            "  -- Defect: the body-length header is never dropped, so it survives\n"
            "  -- onto a response that will carry no entity body.\n"
            "  let clPresent := c.contentLengthSet\n"
            "  let mut disconnect := c.appDisconnect\n"
            "  if !c.isHead && !clPresent then\n"
            "    disconnect := true\n"
            "  else if !c.isThreading then\n"
            "    disconnect := true\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "refinement": "keeps the whole non-reuse decision correct and omits only "
                      "the removal of the body-length header for a metadata-only "
                      "response. Its faithful real patch is the change with that "
                      "one hunk left out: a metadata-only response would still "
                      "advertise the length the base step computed for a body it "
                      "is not going to send. The F2P test asserts that NO "
                      "body-length header line appears on the metadata-only "
                      "response, so it would NOT resolve.",
        "rationale": "REJECT from clause (i) `result.contentLengthPresent = "
                     "(c.contentLengthSet && !c.isHead)`: at (T, T, F, T) the spec "
                     "requires `false` and the rival returns `true`. Refuted at "
                     "a SINGLE-REQUEST server with an application-requested "
                     "non-reuse — a cell where clause (ii) demands the signal be "
                     "asserted and the rival correctly asserts it — so the "
                     "refutation isolates clause (i), and neither isThreading nor "
                     "appDisconnect is held at the value the other witnesses use. "
                     "If it verified => SPEC-TOO-WEAK (the metadata-only length "
                     "removal unenforced).",
        "witness": _refute_header(
            "-- A single-request server whose application already asked for\n"
            "-- non-reuse: clause (ii) is satisfied here by this rival, so the\n"
            "-- refutation is attributable to the length-header clause alone.\n",
            "true", "true", "false", "true"),
    },
    {
        "id": "weak-header-length-always-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # The OTHER one-sided error on clause (i): the length header is dropped
        # unconditionally, for every method rather than only for the
        # metadata-only one. Agrees with the frozen policy on the whole
        # metadata-only half of the cube and diverges on the ordinary half.
        "module": _swap(
            _BASE, _I_HEADER,
            "  -- Defect: the body-length header is dropped for EVERY method, not\n"
            "  -- only for a response that will carry no entity body.\n"
            "  let clPresent := false\n"
            "  let mut disconnect := c.appDisconnect\n"
            "  if !c.isHead && !c.contentLengthSet then\n"
            "    disconnect := true\n"
            "  else if !c.isThreading then\n"
            "    disconnect := true\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "refinement": "drops the body-length header for every method instead of "
                      "only where no entity body will follow — i.e. the real "
                      "patch with the method condition on that removal omitted. "
                      "The F2P test asserts of the ORDINARY response that the "
                      "body-length header line IS present with the body's exact "
                      "length, so it would NOT resolve. (Its non-reuse decision "
                      "is deliberately kept faithful — read off the base step's "
                      "own length state rather than the clobbered local — so the "
                      "case attacks clause (i) and nothing else.)",
        "rationale": "REJECT from clause (i) `result.contentLengthPresent = "
                     "(c.contentLengthSet && !c.isHead)`: at the ORDINARY-method F2P "
                     "cell (F, T, T, F) the spec requires `true` and the rival "
                     "returns `false`. This is the mirror image of "
                     "`weak-header-length-kept` — that rival is wrong on the "
                     "metadata-only half and right on the ordinary half, this one "
                     "the reverse — which is why clause (i) has to be a "
                     "CONJUNCTION rather than a one-way implication, and why the "
                     "two rivals are refuted in opposite halves of the isHead "
                     "domain. If it verified => SPEC-TOO-WEAK (the clause would "
                     "not pin the header's SURVIVAL for a body-bearing response).",
        "witness": _refute_header(
            "-- The ordinary-method cell the test observes: the body-length the\n"
            "-- base step computed must survive onto a response that will carry\n"
            "-- the entity body.\n",
            "false", "true", "true", "false"),
    },
    {
        "id": "weak-header-signal-on-any-missing",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on clause (ii): the length-header removal is performed
        # correctly (so clause (i) holds on the WHOLE cube), but the non-reuse
        # signal is asserted whenever no length is present, without regard to
        # the method — the narrowest form of the pre-fix defect, confined to the
        # metadata-only sub-domain of clause (ii).
        "module": _swap(
            _BASE, _I_HEADER,
            "  let mut clPresent := c.contentLengthSet\n"
            "  -- A metadata-only response must not advertise a body length.\n"
            "  if c.isHead && clPresent then\n"
            "    clPresent := false\n"
            "  let mut disconnect := c.appDisconnect\n"
            "  -- Defect: the non-reuse signal is asserted on any response of\n"
            "  -- unknown length, including one that will carry no entity body.\n"
            "  if !clPresent then\n"
            "    disconnect := true\n"
            "  else if !c.isThreading then\n"
            "    disconnect := true\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "refinement": "keeps the body-length removal but leaves the "
                      "non-reuse guard un-gated on the method: a metadata-only "
                      "response, whose length header has just been removed and "
                      "whose length is therefore unknown, is told not to reuse "
                      "the connection. Its faithful real patch is the change "
                      "with only the method condition on the persistence guard "
                      "omitted. The F2P test asserts the non-reuse signal is "
                      "absent from the metadata-only response, so it would NOT "
                      "resolve. Worse than the pre-fix code on this leg, since "
                      "removing the length header is exactly what makes the "
                      "un-gated guard fire.",
        "rationale": "REJECT from clause (ii) `result.connectionDisconnect = "
                     "((!c.isHead && !c.contentLengthSet) || !c.isThreading || "
                     "c.appDisconnect)`: at "
                     "(T, F, T, F) the spec requires `false` — a metadata-only "
                     "response on a multi-request server with no "
                     "application-requested non-reuse must not carry the signal, "
                     "whatever its length state — and the rival returns `true`. "
                     "This is a genuine NEAR-MISS of `weak-header-prefix`: it "
                     "satisfies clause (i) at EVERY input (that is what makes it "
                     "narrower), so it cannot be refuted where that rival is, and "
                     "it is refuted here instead at contentLengthSet = F, the one "
                     "value no other headerPolicy witness uses. If it verified => "
                     "SPEC-TOO-WEAK (the method gate on the persistence signal "
                     "unenforced — the discriminating half of the change).",
        "witness": _refute_header(
            "-- A metadata-only response for which the base step left no body\n"
            "-- length at all, on a multi-request server, with no\n"
            "-- application-requested non-reuse: the non-reuse signal must not be\n"
            "-- asserted merely because the length is unknown.\n",
            "true", "false", "true", "false"),
    },
    {
        "id": "weak-header-signal-drops-single",
        "kind": "uniqueness",
        "expect": "reject",
        # The OPPOSITE direction on clause (ii): every rival above asserts the
        # signal too OFTEN. This one withholds it — the single-request-server
        # disjunct is dropped entirely, so a response that cannot be followed by
        # another on the same connection is still advertised as reusable. Clause
        # (i) is performed correctly, so the defect is confined to clause (ii).
        "module": _swap(
            _BASE, _I_HEADER,
            "  let mut clPresent := c.contentLengthSet\n"
            "  -- A metadata-only response must not advertise a body length.\n"
            "  if c.isHead && clPresent then\n"
            "    clPresent := false\n"
            "  let mut disconnect := c.appDisconnect\n"
            "  -- Defect: the single-request-server case never asserts the\n"
            "  -- non-reuse signal, so a connection that will not carry another\n"
            "  -- request is still advertised as reusable.\n"
            "  if !c.isHead && !c.contentLengthSet then\n"
            "    disconnect := true\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "refinement": "keeps the body-length removal and the unknown-length "
                      "guard, and drops only the arm that asserts non-reuse for "
                      "a server handling a single request. Its faithful real "
                      "patch is the change with the server-capability arm of the "
                      "persistence decision deleted: a client would be invited "
                      "to reuse a connection the server is about to stop serving, "
                      "which is the pre-existing persistent-connection guarantee "
                      "the change must PRESERVE, not alter. The surrounding suite "
                      "covers the single-request server (the default for this "
                      "server), so it would NOT resolve.",
        "rationale": "REJECT from clause (ii) `result.connectionDisconnect = "
                     "((!c.isHead && !c.contentLengthSet) || !c.isThreading || "
                     "c.appDisconnect)`: at (T, T, F, F) the spec requires `true` "
                     "and the rival returns `false`. This is the UNDER-assertion "
                     "direction, which no rival above probes — every other clause "
                     "(ii) rival asserts the signal too often, so without this "
                     "case the clause's second disjunct is never shown to be "
                     "load-bearing and a spec that simply omitted it would pass. "
                     "Refuted at a cell where `!isThreading` is the ONLY true "
                     "disjunct (the method is metadata-only so the first is "
                     "false, and the application asked for nothing), so the "
                     "failure is attributable to that disjunct alone. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _refute_header(
            "-- A metadata-only response on a SINGLE-REQUEST server, with a body\n"
            "-- length left by the base step and no application-requested\n"
            "-- non-reuse: the signal must be asserted, because the server will\n"
            "-- not serve another request on this connection.\n",
            "true", "true", "false", "false"),
    },
    {
        "id": "weak-header-signal-drops-app",
        "kind": "uniqueness",
        "expect": "reject",
        # The remaining disjunct of clause (ii), also in the UNDER-assertion
        # direction: the application's own non-reuse request is discarded rather
        # than carried into the response (the decision starts from `false`
        # instead of from the incoming state). Clause (i) is untouched.
        "module": _swap(
            _BASE, _I_HEADER,
            "  let mut clPresent := c.contentLengthSet\n"
            "  -- A metadata-only response must not advertise a body length.\n"
            "  if c.isHead && clPresent then\n"
            "    clPresent := false\n"
            "  -- Defect: an application that already asked the client not to\n"
            "  -- reuse the connection is ignored — the decision starts from\n"
            "  -- `false` rather than from the incoming request.\n"
            "  let mut disconnect := false\n"
            "  if !c.isHead && !clPresent then\n"
            "    disconnect := true\n"
            "  else if !c.isThreading then\n"
            "    disconnect := true\n"
            "  return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }\n",
        ),
        "refinement": "computes both header decisions from scratch but discards "
                      "the state the application had already established, so a "
                      "response whose application explicitly asked for non-reuse "
                      "goes out advertising the connection as reusable. Its "
                      "faithful real patch is the change rewritten to seed the "
                      "persistence decision from `false` instead of from what "
                      "was already present — silently overriding the "
                      "application's own instruction, a behavior the change is "
                      "not permitted to touch. It would NOT resolve.",
        "rationale": "REJECT from clause (ii) `result.connectionDisconnect = "
                     "((!c.isHead && !c.contentLengthSet) || !c.isThreading || "
                     "c.appDisconnect)`: at (F, T, T, T) the spec requires `true` "
                     "and the rival returns `false`. The third disjunct is the "
                     "one input to clause (ii) that no other rival makes "
                     "load-bearing: every other case either leaves the "
                     "`appDisconnect` seed intact or is refuted at a cell where "
                     "another disjunct is already true, so a spec that dropped "
                     "`|| c.appDisconnect` would survive the rest of the "
                     "battery. Refuted at a cell where `appDisconnect` is the "
                     "ONLY true disjunct — an ordinary response of KNOWN length "
                     "on a multi-request server — so the failure isolates it. If "
                     "it verified => SPEC-TOO-WEAK.",
        "witness": _refute_header(
            "-- An ordinary response of known length on a multi-request server\n"
            "-- whose application already asked the client not to reuse the\n"
            "-- connection: that request must survive into the response, since\n"
            "-- neither of the other two grounds for the signal holds here.\n",
            "false", "true", "true", "true"),
    },

    # ---- bodyEmission, clauses (iii) and (iv) ----
    {
        "id": "weak-body-always-emits",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-FIX body emission: no metadata-only special case at all —
        # every response defers to the standard writer, which emits the headers
        # and then the body.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Does not distinguish the metadata-only method: every response\n"
            "  -- defers to the standard writer, which emits the headers then the\n"
            "  -- body.\n"
            "  return { bodyEmitted := true, headersSent := true }\n",
        ),
        "refinement": "this is the pre-existing emission path verbatim: with no "
                      "metadata-only case, the standard writer sends the entity "
                      "body for every method. Its faithful real patch is the "
                      "UNCHANGED code, which is precisely the reported defect — "
                      "the F2P test asserts the metadata-only response's body is "
                      "empty. It would NOT resolve.",
        "rationale": "REJECT from clause (iii) `result.bodyEmitted = !c.isHead`: at "
                     "(isHead, headersAlreadySent) = (T, T) the spec requires "
                     "`false` and the rival returns `true`. Refuted with the "
                     "metadata already written, so this rival's point is distinct "
                     "from `weak-body-metadata-not-ensured`'s (which needs the "
                     "not-yet-written state to diverge at all) even though both "
                     "concern a metadata-only request. If it verified => "
                     "SPEC-TOO-WEAK (the spec admits the headline defect).",
        "witness": _refute_body(
            "-- A metadata-only request whose response metadata has already been\n"
            "-- written: no entity body may reach the stream.\n",
            "true", "true"),
    },
    {
        "id": "weak-body-never-emits",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror error on clause (iii): the entity body is withheld from
        # EVERY method, not only from the metadata-only one. Agrees with the
        # frozen behavior on the whole metadata-only half and diverges on the
        # ordinary half.
        "module": _swap(
            _BASE, _I_BODY,
            "  -- Defect: the application's output is drained without writing any\n"
            "  -- body bytes for EVERY method, not only where no entity body is\n"
            "  -- wanted.\n"
            "  let mut sent := c.headersAlreadySent\n"
            "  if !sent then\n"
            "    sent := true\n"
            "  return { bodyEmitted := false, headersSent := sent }\n",
        ),
        "refinement": "withholds the entity body from every method — i.e. the "
                      "added emission path with its method condition omitted, so "
                      "the drain-without-writing branch is taken "
                      "unconditionally. The F2P test asserts the ORDINARY "
                      "response's body equals the application's data exactly, so "
                      "it would NOT resolve; an empty body for every response "
                      "would also break every pre-existing response the "
                      "surrounding suite reads back.",
        "rationale": "REJECT from clause (iii) `result.bodyEmitted = !c.isHead`: at (F, T) "
                     "the spec requires `true` and the rival returns `false`. "
                     "This is the mirror of `weak-body-always-emits`, which is "
                     "why clause (iii) must be an EQUALITY to `!isHead` and not "
                     "merely `isHead → ¬bodyEmitted`: a one-way clause would "
                     "admit this rival. Refuted in the ordinary half of the "
                     "isHead domain, so the two body rivals move that input "
                     "rather than probing one method three times. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _refute_body(
            "-- An ordinary request whose metadata has already been written: the\n"
            "-- entity body must still reach the stream.\n",
            "false", "true"),
    },
    {
        "id": "weak-body-metadata-not-ensured",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW-EFFECT rival on clause (iv): the body decision is exactly
        # right, but the metadata-only path never ensures the response metadata
        # reaches the stream — it simply reports whatever state it was handed.
        # Correct wherever the metadata had already been written; wrong on the
        # sub-domain where it had not.
        "module": _swap(
            _BASE, _I_BODY,
            "  if c.isHead then\n"
            "    -- Defect: the application's output is drained without writing any\n"
            "    -- body bytes, but the response metadata is never ensured written —\n"
            "    -- whatever state it arrived in is what is reported.\n"
            "    return { bodyEmitted := false, headersSent := c.headersAlreadySent }\n"
            "  else\n"
            "    -- Defer to the standard writer: it emits the headers then the body.\n"
            "    return { bodyEmitted := true, headersSent := true }\n",
        ),
        "refinement": "gets the body decision exactly right and omits only the "
                      "step that guarantees the response metadata is written on "
                      "the no-entity-body path. Its faithful real patch is the "
                      "added emission path with that hunk dropped: a "
                      "metadata-only request whose metadata had not yet been "
                      "written produces a response with NO metadata on the "
                      "stream at all. The F2P test reads the metadata-only "
                      "response's lines back and asserts both on the last line "
                      "and on the header lines present, all of which requires "
                      "the metadata to have been emitted; it would NOT resolve. "
                      "The path is not hypothetical — it is the ordinary one for "
                      "this behavior, since nothing before it writes the "
                      "metadata when no entity body is going to follow.",
        "rationale": "REJECT from clause (iv) `result.headersSent = true`: at (T, F) the "
                     "spec requires `true` unconditionally and the rival returns "
                     "the entry value `false`. This is the only rival that "
                     "attacks clause (iv), and it is the case that makes the "
                     "`headersAlreadySent` INPUT load-bearing: the clause pins "
                     "the exit state regardless of the entry state, so a "
                     "computation that merely passes the input through must be "
                     "rejected — the analogue of an output component left to "
                     "track its input instead of the decision. Refuted at "
                     "headersAlreadySent = F, the one value at which it diverges "
                     "and the value no other witness uses; at T it AGREES with "
                     "the frozen behavior, which is exactly why its own point is "
                     "needed rather than a shared one. If it verified => "
                     "SPEC-TOO-WEAK (clause (iv) would not force the metadata to "
                     "be written).",
        "witness": _refute_body(
            "-- A metadata-only request whose response metadata has NOT yet been\n"
            "-- written: this computation must ensure it is, so the exit state is\n"
            "-- pinned independently of the entry state.\n",
            "true", "false"),
    },
]
