"""properties.py — G-PBT falsification battery for django__django-16136 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct notAllowedResponse`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method producing a delivered response over two
read-only inputs — an execution-mode flag and a permitted-method list):

  notAllowedResponse (asynchronous : Bool) (allowed : List String)
      return (out : Delivery)
    ensures out = deliverNotAllowed asynchronous allowed
    ensures out.isAwaitable = asynchronous
    ensures out.response = { allowed := allowed }
    ensures asynchronous = true  → out = Delivery.awaitable { allowed := allowed }
    ensures asynchronous = false → out = Delivery.immediate { allowed := allowed }

with ``deliverNotAllowed`` a fully-unfolded ``def`` in the ``pure`` region:

  deliverNotAllowed async allowed =
    (if async then Delivery.awaitable {allowed} else Delivery.immediate {allowed})

The two INPUT BINDERS are ``asynchronous : Bool`` and ``allowed : List String``.
The clauses pin TWO independent behaviours a well-shaped candidate can still get
wrong:

  * (WRAPPER) the delivered object is an awaitable wrapper EXACTLY when the view
    runs asynchronously, otherwise the plain response object — pinned by
    ``out.isAwaitable = asynchronous`` and the two mode-conditioned clauses. This
    is the discriminating bug-fix behaviour: the pre-change routine always handed
    back the plain response, which an asynchronous caller then cannot await.
  * (RESPONSE) the delivered object carries the SAME 405 response listing the
    given permitted methods, in BOTH modes — pinned by
    ``out.response = { allowed := allowed }``. Deciding the delivery wrapper must
    not change WHICH response is delivered.

``deliverNotAllowed`` is GROUNDED in the inputs (a total dispatch on the flag
wrapping the given list), not an opaque answer key, so there is no wrong echo to
build and the ungrounded-oracle probe is replaced by honest positive controls.

THE CARRIER IS FULLY TRANSPARENT. ``Delivery`` is a two-constructor inductive
with ``DecidableEq``, ``deliverNotAllowed`` / ``isAwaitable`` / ``response`` all
compute on ``Bool`` and ``List String`` literals, and the impl is a straight-line
closed form (no loop) whose extracted program reduces under ``simp``/``decide``.
So a witness reaches the impl through Velvet's extractor
(``extract_program_for notAllowedResponse`` gives ``notAllowedResponseExec async
allowed = NonDetT.run (notAllowedResponse async allowed)``, reducing to
``DivM.res out``) and states ``notAllowedResponseExec async allowed ≠
DivM.res (deliverNotAllowed async allowed)`` at a concrete input — with ``decide``
closing the residual literal (no opaque leaf, no carrier conditioning needed, so
no witness binds a hypothesis and there is no joint-satisfiability obligation).
Both gold and every rival are loop-free here, so the discrimination is NOT the
loop-vs-closed-form asymmetry other bundles rely on: it is that the wrong impl
provably contradicts the postcondition at the probed input while gold satisfies
it. Both halves were checked out-of-band with ``scripts/lean_verify.sh`` (rival
elaborates exit 0, gold fails nonzero) for every reject case.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame rival (``allowed_methods.append(999)`` through a reference held at
    ``Acc(list_pred(allowed_methods), 1/2)``) because a write needs full
    permission. Lean and Velvet are referentially transparent: ``allowed`` is an
    immutable value, this bundle declares NO ``mut`` binder over any input, and
    there is no heap and no aliasing — so there is no read-only input to overwrite
    and no substitute probe to build. Not fabricated (per the porting map: this
    class is vacuous on Lean/Velvet).
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. The three nagini
    wrapper rivals (always-sync, always-async, inverted) and the fresh-reply
    identity rival re-express directly onto the WRAPPER and RESPONSE clauses.
  * UNGROUNDED-ORACLE ECHO — N/A. ``deliverNotAllowed`` is a total ``def`` over
    the method's own inputs; there is no answer key to echo. Replaced by the
    honest positive controls.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the conditional
delivery is modeled DEEPLY by ``deliverNotAllowed`` and validated == the real
async-def-wrap mechanism by axiom_check.py — that is G-AX's job, and this gate
ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "django__django-16136"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end) and is unique in Solution.lean; both facts
# are asserted at load by _swap. Editing only these keeps markers.same_spec True
# and the prove_correct notAllowedResponse statement byte-identical.
#
# The gold executable body: build the 405 response, then choose the delivery
# wrapper by the execution-mode flag. Every variant replaces exactly this block.
# ---------------------------------------------------------------------------

_GOLD_IMPL = (
    "    let resp : NotAllowed := { allowed := allowed }\n"
    "    let out := if asynchronous then Delivery.awaitable resp"
    " else Delivery.immediate resp\n"
    "    return out"
)


def _variant(block: str) -> str:
    return _swap(_BASE, _GOLD_IMPL, block)


# The frozen proof body. An admissibility case prepends an in-region `assert` to
# the gold impl, which raises one EXTRA goal the frozen script does not discharge;
# retuning the tactic body is in scope (the spec view elides it), so the method's
# own obligation still discharges by the frozen script and only the assert goal
# gets the added alternative.
_GOLD_PROOF = (
    "prove_correct notAllowedResponse by\n"
    "  loom_solve <;>\n"
    "    cases asynchronous <;>\n"
    "    simp_all [deliverNotAllowed, Delivery.isAwaitable, Delivery.response]"
)


def _assert_variant(assert_block: str) -> str:
    """Gold impl with `assert_block` prepended, plus a proof tail for its goal."""
    src = _swap(_BASE, _GOLD_IMPL, assert_block + _GOLD_IMPL)
    return _swap(
        src, _GOLD_PROOF,
        _GOLD_PROOF + "\n  all_goals first\n    | decide\n"
        "    | simp_all [deliverNotAllowed, Delivery.isAwaitable,"
        " Delivery.response]")


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `notAllowedResponseExec async allowed` is `NonDetT.run (notAllowedResponse
# ---- async allowed)`, reducing to `DivM.res out`; `≠ DivM.res (deliverNotAllowed
# ---- async allowed)` says the impl's output contradicts the postcondition at
# ---- that concrete input. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can mask the verdict. Both rival and gold are
# ---- loop-free closed forms; the residual equality reduces under decide, so the
# ---- witness ELABORATES against the wrong rival and FAILS against gold (which
# ---- satisfies the postcondition at every input).
_EXTRACT = "extract_program_for notAllowedResponse\n\n"


def _witness(inp: str) -> str:
    return _EXTRACT + (
        "example : notAllowedResponseExec " + inp + " ≠ "
        "DivM.res (deliverNotAllowed " + inp + ") := by\n"
        "  unfold notAllowedResponseExec notAllowedResponse\n"
        "  simp [NonDetT.run, pure]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. The impl is loop-free, so each keeps
    # the frozen `prove_correct` tactic body BYTE-IDENTICAL (the `cases
    # asynchronous <;> simp_all [...]` script closes any behaviourally-equivalent
    # closed form).
    # =====================================================================

    # Ports nagini pos-branch-reorder: test the SYNC case first (guard negated),
    # ASYNC in the else — identical values, mirrored control flow.
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(
            "    let resp : NotAllowed := { allowed := allowed }\n"
            "    let out := if !asynchronous then Delivery.immediate resp"
            " else Delivery.awaitable resp\n"
            "    return out"),
        "rationale": "branch-REORDER positive control: the SYNC case (guard "
                     "negated) is chosen first, the ASYNC case in the else. "
                     "Identical values, mirrored control flow; the routine is "
                     "loop-free so no fold/induction lemma is involved. Keeps every "
                     "postcondition clause (WRAPPER `out.isAwaitable = asynchronous` "
                     "and the mode-conditioned pair; RESPONSE `out.response = "
                     "{allowed}`). A faithful reshape MUST verify — else the spec is "
                     "over-fit to the branch FORM => SPEC-TOO-STRONG.",
    },

    # Ports nagini pos-direct-bool: reshape the branch into a `match` on the flag.
    {
        "id": "pos-match-on-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(
            "    let resp : NotAllowed := { allowed := allowed }\n"
            "    let out := match asynchronous with\n"
            "      | true => Delivery.awaitable resp\n"
            "      | false => Delivery.immediate resp\n"
            "    return out"),
        "rationale": "control-flow reshape: the `if/then/else` dispatch on the "
                     "execution-mode flag is rewritten as an equivalent `match` on "
                     "the flag, building the delivery once per branch. "
                     "Behaviourally identical to gold; a different executable shape "
                     "that must still satisfy WRAPPER + RESPONSE. Must verify.",
    },

    # Ports nagini pos-collapsed-direct: no intermediate branch at all — return the
    # grounded post-image directly. `deliverNotAllowed` is GROUNDED in the inputs
    # (a total dispatch), so this is the honest cheapest-correct impl and doubles
    # as proof the spec is not echo-vulnerable.
    {
        "id": "pos-collapsed-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant("    return (deliverNotAllowed asynchronous allowed)"),
        "rationale": "fully collapsed positive control: `return "
                     "(deliverNotAllowed asynchronous allowed)` with no `resp`/`out` "
                     "local and no explicit branch. `deliverNotAllowed` is GROUNDED "
                     "in the inputs (a total flag-dispatch wrapping the given list), "
                     "so this is the honest cheapest CORRECT impl — not an "
                     "ungrounded-oracle echo — and must satisfy WRAPPER + RESPONSE. "
                     "Must verify; else the spec over-constrains the impl SHAPE "
                     "rather than the observable behaviour => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — ports the sibling's admiss-f2p-shaped-input. This bundle has
    # NO `require` clause, so the sibling's literal obligation ("the precondition
    # admits a normal input") is indeed vacuous — but the RESIDUAL admissibility
    # risk on a total domain is not: a post-image that is DEGENERATE at the
    # interesting point (constant in the flag, or collapsing the method list)
    # reads exactly like a spec every impl meets. This case discharges an
    # in-region `assert`, at a concrete F2P-shaped MULTI-method list, that the
    # post-image is non-degenerate: both flag values are realised, the delivered
    # response carries the full given list, and the two modes are DISTINCT
    # deliveries at the same input. The impl is kept verbatim so the method's own
    # obligation still discharges by the frozen script. The assert is LIVE, not
    # decoration: negating one conjunct at the same point leaves an unsolved goal
    # (checked out-of-band — `simp_all made no progress`, exit 1).
    # =====================================================================
    {
        "id": "admiss-delivery-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _assert_variant(
            "    assert (with_name_prefix `admiss\n"
            "      ((deliverNotAllowed true [\"GET\", \"POST\", \"HEAD\"]).isAwaitable"
            " = true\n"
            "        ∧ (deliverNotAllowed false [\"GET\", \"POST\","
            " \"HEAD\"]).isAwaitable = false\n"
            "        ∧ (deliverNotAllowed true [\"GET\", \"POST\", \"HEAD\"]).response\n"
            "            = { allowed := [\"GET\", \"POST\", \"HEAD\"] }\n"
            "        ∧ deliverNotAllowed true [\"GET\"] ≠"
            " deliverNotAllowed false [\"GET\"]))\n"),
        "rationale": "admissibility on a precondition-free total domain: the "
                     "post-image is SATISFIABLE and NON-DEGENERATE at a concrete "
                     "F2P-shaped 3-method list. The assert pins that the WRAPPER "
                     "clause is realised at BOTH flag values (awaitable at true, "
                     "immediate at false — so the spec is not constant in the "
                     "flag), that the RESPONSE clause carries the FULL given list "
                     "(not a collapsed/empty one), and that the two modes deliver "
                     "DISTINCT objects at the same input (so the flag genuinely "
                     "discriminates). Without this, a spec no impl could meet — or "
                     "one whose clauses were jointly trivial — would be "
                     "indistinguishable from a strong one. Must verify.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- WRAPPER clause: always the plain response (the pre-change behaviour) ----
    {
        "id": "weak-always-immediate-prechange",
        "kind": "uniqueness",
        "expect": "reject",
        # Hand back the plain response object unconditionally — correct on the sync
        # sub-domain, wrong on the async sub-domain. This is the pre-change bug.
        "module": _variant(
            "    let resp : NotAllowed := { allowed := allowed }\n"
            "    return (Delivery.immediate resp)"),
        "refinement": "this IS the pre-change behaviour: always hand back the plain "
                      "response, never an awaitable wrapper. Its faithful real "
                      "counterpart returns the bare 405 response even for an "
                      "asynchronous view, which the caller then tries to await — "
                      "raising the exact reported failure ('object ... can't be used "
                      "in await expression'). The failing test asserts the returned "
                      "object IS a coroutine for the async view and would FAIL, so a "
                      "verifying rival here is a true verify-but-not-resolve break.",
        "rationale": "REJECT from the WRAPPER clause `out.isAwaitable = "
                     "asynchronous` (and `asynchronous = true → out = awaitable`): "
                     "this rival pins the wrapper to `immediate` unconditionally, so "
                     "on the async sub-domain `isAwaitable = false ≠ true`. Refuted "
                     "at `true [\"GET\"]` (async view): the rival returns "
                     "`immediate`, the spec demands `awaitable`. Rejection comes "
                     "from the discriminating bug-fix clause, not from shape (a "
                     "well-formed Delivery is still produced). Varies `asynchronous` "
                     "to true.",
        "witness": _witness('true ["GET"]'),
    },

    # ---- WRAPPER clause: always the awaitable wrapper (the dual) ----
    {
        "id": "weak-always-awaitable",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrap in an awaitable unconditionally — correct on the async sub-domain,
        # wrong on the SYNC sub-domain (the common path).
        "module": _variant(
            "    let resp : NotAllowed := { allowed := allowed }\n"
            "    return (Delivery.awaitable resp)"),
        "refinement": "the dual partial-domain rival: always wrap in an awaitable, "
                      "even for a SYNC view. Its faithful counterpart hands back an "
                      "un-awaited coroutine on the synchronous path, which the "
                      "synchronous caller never resolves — a regression on the "
                      "common case. The failing test asserts the returned object is "
                      "NOT a coroutine for the sync view and would FAIL. "
                      "verify-but-not-resolve.",
        "rationale": "REJECT from the WRAPPER clause `out.isAwaitable = "
                     "asynchronous` (and `asynchronous = false → out = immediate`): "
                     "the wrapper is pinned to `awaitable` unconditionally, so on "
                     "the sync sub-domain `isAwaitable = true ≠ false`. Refuted at "
                     "`false [\"POST\"]` (sync view): the rival returns `awaitable`, "
                     "the spec demands `immediate`. The RESPONSE clause is untouched "
                     "— the rejection is squarely the wrapper mapping. Varies "
                     "`asynchronous` to false and `allowed` to a distinct list.",
        "witness": _witness('false ["POST"]'),
    },

    # ---- WRAPPER clause: invert the whole mapping (awaitable iff SYNC) ----
    {
        "id": "weak-inverted-mapping",
        "kind": "uniqueness",
        "expect": "reject",
        # Flip the flag: awaitable iff SYNC. Wrong on BOTH normal sub-domains.
        "module": _variant(
            "    let resp : NotAllowed := { allowed := allowed }\n"
            "    let out := if asynchronous then Delivery.immediate resp"
            " else Delivery.awaitable resp\n"
            "    return out"),
        "refinement": "inverts the entire mapping: awaitable iff SYNC. A faithful "
                      "counterpart with the execution-mode guard negated hands back "
                      "a coroutine for sync views and a bare response for async "
                      "views — wrong on BOTH failing-test rows (the sync row expects "
                      "not-a-coroutine, the async row expects a coroutine), so both "
                      "subtests FAIL. verify-but-not-resolve.",
        "rationale": "REJECT from the WRAPPER clause on the ENTIRE domain: "
                     "`out.isAwaitable = (not asynchronous)` contradicts "
                     "`out.isAwaitable = asynchronous` for every flag value. Refuted "
                     "at `false [\"HEAD\"]` — the sync sub-domain, where the rival "
                     "returns `awaitable` and the spec demands `immediate` (a "
                     "DISTINCT input point from the always-awaitable rival's, which "
                     "attacks the same clause with a different `allowed`). Varies "
                     "`asynchronous` to false and `allowed` to a third list.",
        "witness": _witness('false ["HEAD"]'),
    },

    # ---- RESPONSE clause: deliver a fresh (empty) response, right wrapper ----
    {
        "id": "weak-fresh-response",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the WRAPPER mapping CORRECT but deliver a response built from a fresh
        # EMPTY method list rather than the given `allowed`. Rejected only by the
        # RESPONSE clause `out.response = { allowed := allowed }`.
        "module": _variant(
            "    let resp : NotAllowed := { allowed := ([] : List String) }\n"
            "    let out := if asynchronous then Delivery.awaitable resp"
            " else Delivery.immediate resp\n"
            "    return out"),
        "refinement": "keeps the async→awaitable WRAPPER mapping CORRECT but "
                      "delivers a 405 response built from a brand-new EMPTY "
                      "permitted-method list rather than the given `allowed`. Its "
                      "faithful counterpart builds the not-allowed response over the "
                      "wrong (empty) method set, so the delivered response no longer "
                      "lists the methods the resource permits — a malformed 405 "
                      "whose permitted-method content the failing test's downstream "
                      "checks require. verify-but-not-resolve (a wrapper-only "
                      "abstraction would miss this; the RESPONSE clause catches it).",
        "rationale": "REJECT from the RESPONSE clause `out.response = "
                     "{ allowed := allowed }`: the rival's response carries the "
                     "fresh empty list, never `allowed`, so the equality fails "
                     "whenever `allowed` is non-empty. Refuted at `true [\"GET\"]`: "
                     "the rival's `out.response.allowed = []` while the spec demands "
                     "`[\"GET\"]`. Rejection comes from the response-preservation "
                     "clause, not from the WRAPPER (which this rival deliberately "
                     "satisfies — it is the one rival that ABUSES the `allowed` "
                     "binder, so the battery would miss a mishandling of `allowed` "
                     "without it).",
        "witness": _witness('true ["GET"]'),
    },

    # ---- RESPONSE clause: truncate the method list (multi-element domain) ----
    # Added by the audit. Every pre-existing witness probes a SINGLETON list, and
    # a singleton is a fixed point of truncation-to-one AND of reordering — so a
    # rival that mangles the method list only when it has 2+ elements was
    # invisible to the battery as shipped. Measured: this rival's refutation FAILS
    # to elaborate at `true ["GET"]` (`decide` proves the negation false, exit 1 —
    # the rival is correct there) and elaborates only at a multi-element point.
    {
        "id": "weak-truncate-allowed",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct WRAPPER mapping and correct on every singleton list; drops every
        # permitted method after the first once the list has 2+ elements.
        "module": _variant(
            "    let resp : NotAllowed := { allowed := allowed.take 1 }\n"
            "    let out := if asynchronous then Delivery.awaitable resp"
            " else Delivery.immediate resp\n"
            "    return out"),
        "refinement": "keeps the WRAPPER mapping CORRECT and agrees with gold on "
                      "every one-element method list, but truncates a longer list "
                      "to its first method. Its faithful counterpart builds the 405 "
                      "over a TRUNCATED permitted-method set, so a resource "
                      "permitting several methods advertises only one — the "
                      "delivered response no longer reports the methods the "
                      "resource permits, which is the whole content of a 405. The "
                      "real handler is reached with multi-method lists (a view "
                      "defining several handlers), so this is a live divergence, "
                      "not a boundary curiosity. verify-but-not-resolve.",
        "rationale": "REJECT from the RESPONSE clause `out.response = "
                     "{ allowed := allowed }` on the MULTI-ELEMENT sub-domain only. "
                     "Refuted at `false [\"GET\", \"POST\", \"HEAD\"]`: the rival "
                     "delivers `{allowed := [\"GET\"]}` while the spec demands the "
                     "full three-method list. This rival is what makes the "
                     "`allowed` binder's coverage MEANINGFUL rather than three "
                     "spellings of one point: weak-fresh-response abuses `allowed` "
                     "only by emptying it, which a singleton already exposes, so "
                     "before this case no witness distinguished list ORDER or "
                     "LENGTH from list PRESENCE. Varies `allowed` to a "
                     "multi-element list and `asynchronous` to false.",
        "witness": _witness('false ["GET", "POST", "HEAD"]'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (3 soundness
# positives, 1 admissibility, 4 uniqueness rivals, 1 frame-mutation rival) plus a
# 1-case AXIOM lane. This bundle models the SAME purely-functional core — how the
# 405 "method not allowed" response is delivered (awaitable wrapper iff the view
# is async, over the same permitted-method list) — over the same finite carrier
# (a `Bool` flag and a `List String`), so the three positive controls and the
# four wrapper/response rivals port near 1:1; the frame and admissibility cases
# are genuinely vacuous on this carrier.
#
#   sibling case                     -> here                            disposition
#   ---------------------------------------------------------------------------
#   pos-branch-reorder               -> pos-branch-reorder              PORTED
#   pos-direct-bool                  -> pos-match-on-flag               PORTED (reshaped)
#   pos-collapsed-direct             -> pos-collapsed-direct            PORTED
#   admiss-f2p-shaped-input          -> admiss-delivery-nondegenerate   PORTED (re-aimed, by audit)
#   weak-always-sync-prepatch        -> weak-always-immediate-prechange PORTED
#   weak-always-async                -> weak-always-awaitable           PORTED
#   weak-inverted-mapping            -> weak-inverted-mapping           PORTED
#   weak-fresh-reply-identity        -> weak-fresh-response             PORTED (re-aimed)
#   frame-mutate-allowed-methods     -> (none)                          VACUOUS
#   AXIOM_TESTS (1)                  -> (none)                          DROPPED (G-AX)
#   (no sibling)                     -> weak-truncate-allowed           ADDED (by audit)
#
# 8 ported + 1 added, 1 vacuous, 1 dropped = 9 SPEC cases (3 soundness,
# 1 admissibility, 5 uniqueness).
#
# AUDIT AMENDMENTS (independent adversarial audit of the port; the port recorded
#   SOUND on 7 cases and the three defects below were found under that SOUND):
#   (1) admiss-f2p-shaped-input had been dropped as VACUOUS. Its literal
#       obligation (a `require` admits a normal input) IS vacuous here, but the
#       residual non-degeneracy obligation is EXPRESSIBLE on this carrier and is
#       now carried by admiss-delivery-nondegenerate. Recording it as
#       inexpressible was an omission, not a carrier fact.
#   (2) every shipped witness probed a SINGLETON `allowed` list, and a singleton
#       is a fixed point of both truncation-to-one and reordering. So the
#       "`allowed` binder is ABUSED / its dependence is demonstrated" claim held
#       only for PRESENCE (empty vs non-empty), never for LENGTH or ORDER, and a
#       list-mangling rival on the multi-element sub-domain was invisible. Closed
#       by weak-truncate-allowed. (An order-only rival — `allowed.reverse` — is
#       also correctly REJECTED by the spec, measured exit 1, so this was a
#       battery coverage gap and NOT a spec hole.)
#   (3) the DIVERGENCE paragraph claimed the class was "genuinely VACUOUS here
#       (NOT a spec hole)". The disposition (nothing to ship in this lane) was
#       right and the reason was wrong, but a LATER revision then got it wrong the
#       other way, saying that under `partial` semantics a diverging impl VERIFIES
#       and citing an internal findings doc. That is the PARTIAL rule against a
#       TOTAL file: line 4 reads `"total"`, as it does in all 500 velvet bundles,
#       and the `set_option` elaborator itself runs `openScope `TotalCorrectness`
#       (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the option and the
#       `open` cannot disagree. Under `total` a postcondition is claimed of ALL
#       runs and every loop owes a strictly decreasing measure, so a diverging
#       rival is REJECTED. The correct reason for shipping nothing is the WITNESS
#       contract: the rejection fires at the `method`, so no witness can elaborate
#       against such a rival.
#
# PORTED (3 positive controls): the sibling's branch-reorder ports directly (guard
#   negated, branches mirrored). The sibling's local-variable/direct-bool control
#   (`flag = async_mode; Delivered(flag, ...)`) is reshaped here as a `match` on
#   the flag — the Velvet-idiomatic equivalent of hoisting the decision — since
#   the carrier has no separate boolean payload field to thread. The
#   collapsed-direct control ports 1:1 as `return (deliverNotAllowed asynchronous
#   allowed)`. All three keep the frozen `prove_correct` tactic body byte-identical
#   and were verified to build (exit 0).
# PORTED (4 rivals): always-sync/always-async/inverted re-express directly onto the
#   WRAPPER clause (`out.isAwaitable = asynchronous`); the fresh-reply rival is
#   RE-AIMED onto the RESPONSE clause. The sibling's `is` IDENTITY pin
#   (`reply.methods is allowed_methods`) has no counterpart on a referentially
#   transparent carrier — there is no object identity to distinguish from
#   structural equality — so the rival is re-aimed at the VALUE the identity pin
#   protected: `out.response = { allowed := allowed }`. Delivering a response over
#   a FRESH EMPTY list violates that equality, which is the same defect the
#   identity pin caught (a response that is not the given method set). Each
#   refinement argument carries over: pre-change delivery breaks the async row,
#   always-await breaks the sync row, inversion breaks both, and a wrong method set
#   yields a malformed 405 — none would resolve the failing tests.
# PORTED (admiss-delivery-nondegenerate) — RE-AIMED, added by the audit. The
#   sibling self-runs an F2P-shaped input through the construction chain to prove
#   the precondition `Acc(list_pred(...), 1/2)` admits it. This bundle declares NO
#   `require` clause, so that literal obligation is vacuous. But "the post-image
#   is total, therefore satisfiable, therefore there is no residual risk" does NOT
#   follow: totality says a value EXISTS at every input, not that the value is
#   non-degenerate, and a post-image constant in the flag or collapsing the method
#   list would satisfy every clause while pinning nothing. That residual IS
#   expressible here — an in-region `assert` at a concrete F2P-shaped 3-method
#   list, discharged by `decide` — so the case is carried rather than dropped. It
#   was checked LIVE: negating one conjunct at the same point fails to build
#   (`simp_all made no progress`, exit 1).
# VACUOUS (frame-mutate-allowed-methods): the sibling carries this MANDATORY
#   because `allowed_methods` is held at Acc(list_pred(allowed_methods), 1/2) and a
#   rival can illegally `.append` to it. This backend is referentially transparent
#   and declares no `mut` binder — `allowed` is an immutable value with no heap
#   footprint — so there is no read-only input to overwrite and no substitute
#   probe. Not fabricated (per the porting map: this class is vacuous on
#   Lean/Velvet).
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference conditional delivery == the real async-def-wrap mechanism);
#   this bundle consumes no axiom `ensures`, and the gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has two input binders — `asynchronous :
#   Bool` and `allowed : List String` — and two independent top-level behaviours
#   (WRAPPER: `out.isAwaitable = asynchronous` + the two mode-conditioned clauses;
#   RESPONSE: `out.response = { allowed := allowed }`). The `asynchronous` binder
#   is varied across BOTH values by the reject witnesses (true for
#   always-immediate and fresh-response; false for always-awaitable, inverted and
#   truncate), so a rival that mishandled only one flag value cannot hide. The
#   `allowed` binder is abused along TWO independent axes, which the audit found
#   the shipped battery did not separate: PRESENCE (weak-fresh-response empties
#   the list) and LENGTH/ORDER (weak-truncate-allowed drops methods past the
#   first). That second axis needs a MULTI-ELEMENT witness point, because a
#   singleton list is a fixed point of truncation-to-one and of reordering alike —
#   so the four original witnesses, all at singleton lists, could not have caught
#   a rival that mangles only longer lists. The wrapper rivals hold `allowed` at
#   representative non-empty singletons (["GET"], ["POST"], ["HEAD"]), which is
#   correct for them, since the WRAPPER behaviour is independent of `allowed` by
#   design. The five reject witnesses probe four DISTINCT input points — `true
#   ["GET"]`, `false ["POST"]`, `false ["HEAD"]`, `true ["GET"]` (fresh-response
#   shares the flag/list of always-immediate but attacks a DIFFERENT clause), and
#   `false ["GET","POST","HEAD"]` (the multi-element point) — so both flag values
#   are covered, both clauses attacked, and the `allowed` binder's variation is
#   MEANINGFUL (list length changes the spec's verdict) rather than three
#   spellings of one point. The three positive controls plus the admissibility
#   assert defend the whole obligation.
# WITNESS DISCRIMINATION (verified with two real builds per reject case, and
#   INDEPENDENTLY RE-DERIVED by the audit — for all four original witnesses the
#   rival build exited 0 with empty output and the gold build exited 1 with
#   `Tactic decide proved that the proposition ¬<rival literal> = deliverNotAllowed
#   <input> is false`, i.e. a SEMANTIC refutation of the concrete claim, not a
#   stuck `decide`, unknown identifier, unfolding failure or timeout; the same two
#   builds were run for the added weak-truncate-allowed): each witness ELABORATES
#   against its loop-free rival (the
#   extracted program reduces to a Delivery literal that provably differs from
#   `deliverNotAllowed` at the probed input) and FAILS against the frozen solution
#   (whose extracted program reduces to the correct literal, so `decide` proves
#   the negated goal FALSE). No witness binds a hypothesis (the carrier is fully
#   transparent, `decide` closes every residual), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
AXIOM_TESTS = []
