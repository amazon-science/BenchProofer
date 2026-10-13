"""PBT manifest for sympy__sympy-23824 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (region-surgery: only
the text strictly inside the single `# impl-start` / `# impl-end` region is
edited) and swap the implementation; they are checked by Nagini verify +
markers.same_spec. There are NO axiom cases for this instance (see assessment).

Defended surface (read from model.py / refinement.md / mapping.md / instance):

  ONE modeled function over the gamma-matrix leading-run restore site
  (sympy.physics.hep.gamma_matrices.kahane_simplify, the patched line 697-698):

    * restore_leading(leading: List[int], tail: List[int]) -> List[int]
        leading  = free_pos[0:first_dum_pos]  — the leading uncontracted gamma
                   factors, in original left-to-right order.
        tail     = ri                         — one core-result term.
        Pre : Acc(list_pred(leading), 1/2)    <- leading is READ-ONLY
              Acc(list_pred(tail), 1/2)       <- tail    is READ-ONLY
        Post: Acc(list_pred(leading), 1/2)    (returns the read perm)
              Acc(list_pred(tail), 1/2)       (returns the read perm)
              Acc(list_pred(Result()))        (full perm on a FRESH result)
              ToSeq(Result()) == ToSeq(leading) + ToSeq(tail)
        LOAD-BEARING clause: the last Ensures — the result is the leading run in
        its ORIGINAL order followed by tail, i.e. order-preserving concatenation
        `leading ++ tail`. The pre-patch bug prepended each leading factor at the
        front in turn (insert(0,...)) -> reverse(leading) ++ tail.

  Read-only inputs: BOTH leading and tail are Acc(list_pred(.), 1/2).
  => the FRAME-MUTATION probe is MANDATORY (a rival that WRITES leading or tail
  to satisfy the postcondition by side effect must be REJECTED for insufficient
  permission).

  GROUNDED oracle: the postcondition is `ToSeq(Result()) == ToSeq(leading) +
  ToSeq(tail)` — a fully-unfolded function of the two inputs (PSeq concatenation
  via ToSeq), NOT an opaque @Pure answer-key. There is nothing to echo without
  doing the work, so the directive-2 ungrounded-oracle-echo attack does not apply
  (an honest cheapest-/structurally-different correct positive control replaces
  it; see assessment).

Axiom lane: NONE. meta.axioms == [], deep_model_references == [], no
@ContractOnly, no axiom_check.py. The changed operation is pure order-preserving
list/sequence concatenation modeled DEEPLY in the impl; G-AX is vacuous. So
AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23824"
FLOAT_ENCODING = None  # meta.json float_encoding is null (int gamma-index labels)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchor: the WHOLE impl body (gold), strictly inside # impl-start /
# # impl-end. Every variant is produced by _swap on exactly this block, so the
# frozen spec (axioms/pure/pre/post/invariant markers) is never touched and
# same_spec holds by construction.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(leading):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
    "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(leading))\n"
    "        Invariant(ToSeq(result) == ToSeq(leading).take(i))\n"
    "        Invariant(MustTerminate(len(leading) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(leading[i])\n"
    "        i = i + 1\n"
    "    j = 0\n"
    "    while j < len(tail):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
    "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= j and j <= len(tail))\n"
    "        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(j))\n"
    "        Invariant(MustTerminate(len(tail) - j + 1))\n"
    "        # invariants-end\n"
    "        result.append(tail[j])\n"
    "        j = j + 1\n"
    "    return result"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): local-variable reshape -----------------
    # Structurally different from the gold (loop counters renamed k/p; the cached
    # bounds n=len(leading), m=len(tail) introduced as locals; the permission and
    # bound invariants reordered) but behaviourally and PROOF-identical: it is
    # still the forward two-phase append with the SAME take-prefix invariants the
    # gold proof relies on (ToSeq(result)==ToSeq(leading).take(k); then
    # ToSeq(result)==ToSeq(leading)+ToSeq(tail).take(p)). Forward append against a
    # forward (take-prefix) spec helper auto-discharges — no front-recursive fold,
    # no f(a+b)=f(a)+f(b) lemma needed (pilot bugs #2/#3 avoided: every gold
    # invariant it still needs is KEPT, only the executable shape / names change).
    # MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    result = []  # type: List[int]\n"
            "    n = len(leading)\n"
            "    k = 0\n"
            "    while k < n:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= k and k <= n)\n"
            "        Invariant(n == len(leading))\n"
            "        Invariant(ToSeq(result) == ToSeq(leading).take(k))\n"
            "        Invariant(MustTerminate(n - k + 1))\n"
            "        # invariants-end\n"
            "        result.append(leading[k])\n"
            "        k = k + 1\n"
            "    m = len(tail)\n"
            "    p = 0\n"
            "    while p < m:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= p and p <= m)\n"
            "        Invariant(m == len(tail))\n"
            "        Invariant(ToSeq(result) == ToSeq(leading) + ToSeq(tail).take(p))\n"
            "        Invariant(MustTerminate(m - p + 1))\n"
            "        # invariants-end\n"
            "        result.append(tail[p])\n"
            "        p = p + 1\n"
            "    return result"),
        "rationale": "a behaviourally- and proof-identical reshape (renamed "
                     "counters, cached bounds, reordered invariant lines) keeps the "
                     "forward take-prefix invariants the gold proof discharges, so it "
                     "must verify against the frozen postcondition (else "
                     "SPEC-TOO-STRONG). Forward append vs forward take-prefix spec "
                     "helper => no induction-lemma proof gap.",
    },

    # -- ADMISSIBILITY: the precondition admits a normal F2P-shaped input -----
    # A non-trivial Assert of the two read-only Requires at function entry (a
    # no-op for a verifying spec), then the gold impl verbatim. The F2P witness
    # G(rho)*G(sigma)*G(mu)*G(-mu) has leading run [rho,sigma] (len 2) and a
    # core term; the precondition Acc(list_pred(leading),1/2) & Acc(list_pred(
    # tail),1/2) is exactly what a caller threading two half-permissions supplies.
    # If the Requires could not be established for such an input the Assert would
    # fail => PRECOND-TOO-STRONG. It verifies, so the precondition is satisfiable.
    {
        "id": "admiss-precond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    Assert(Acc(list_pred(leading), 1 / 2))\n"
            "    Assert(Acc(list_pred(tail), 1 / 2))\n"
            + _GOLD_IMPL),
        "rationale": "the modeled function's own Requires "
                     "(Acc(list_pred(leading),1/2) & Acc(list_pred(tail),1/2)) is "
                     "established at entry; the two Asserts confirm both half-"
                     "permissions are in hand for a normal F2P-shaped input "
                     "([rho,sigma] leading run + a core term) and the body still "
                     "verifies (else PRECOND-TOO-STRONG).",
    },

    # -- FRAME-MUTATION (uniqueness): write the read-only `leading` -----------
    # MANDATORY: leading is Acc(list_pred(leading),1/2) — READ-ONLY. This rival
    # appends to `leading` (only 1/2 permission held) before the gold build. It
    # MUST be REJECTED for INSUFFICIENT PERMISSION (list.append needs the full
    # list_pred). The gold build is otherwise verbatim, so the rejection is
    # attributable to the write, not a proof gap.
    {
        "id": "frame-mutate-leading-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    leading.append(0)\n"
            + _GOLD_IMPL),
        "refinement": "the gold patch builds a FRESH list per term "
                      "(free_pos[0:first_dum_pos] + ri) and never mutates free_pos. "
                      "A faithful real patch that appended to free_pos would corrupt "
                      "the shared leading slice for EVERY subsequent term ri in the "
                      "`for ri in resulting_indices` comprehension, producing wrong "
                      "factor lists for all later terms; test_kahane_simplify1 "
                      "(multi-term results) would then return the wrong gamma product, "
                      "so such a patch would NOT resolve the F2P.",
        "rationale": "rejected by the permission system: `leading` is held at "
                     "Acc(list_pred(leading),1/2); `list.append` requires the FULL "
                     "predicate, so the write is INSUFFICIENT-PERMISSION. If it "
                     "verified, the read-only frame on `leading` is unguarded "
                     "(SPEC-TOO-WEAK).",
    },

    # -- FRAME-MUTATION (uniqueness): in-place index write to `tail` ----------
    # A different write shape on the OTHER read-only input. tail[0] = ... needs
    # the full list_pred. Guarded so it only runs when tail is non-empty (keeps
    # the gold value otherwise); the write itself is the rejected action.
    {
        "id": "frame-mutate-tail-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if len(tail) > 0:\n"
            "        tail[0] = 0\n"
            + _GOLD_IMPL),
        "refinement": "the core term `ri` is read and concatenated, never rewritten, "
                      "by the gold patch. A patch that overwrote ri[0] in place would "
                      "change the simplified gamma factors of that term — the F2P "
                      "expects 4*G(rho)*G(sigma); corrupting a term's factor labels "
                      "yields a different tensor expression and fails the assertion, "
                      "so it would NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: an in-place store to "
                     "`tail` needs the full list_pred but only 1/2 is held. Frame "
                     "integrity of the read-only core-term input.",
    },

    # -- PARTIAL-DOMAIN (uniqueness): reverse(leading) ++ tail = THE BUG -------
    # The actual pre-patch behaviour: prepend each leading factor at the front in
    # turn (insert(0,...)), which REVERSES the leading run. Here the leading run
    # is appended in DESCENDING index order (i = len-1 .. 0), producing
    # reverse(leading) ++ tail. NOTE: Nagini PSeq exposes only take/drop/update
    # (no `.reversed()`), so this impl carries ONLY the permission + bound
    # invariants (no value-tracking invariant for the wrong run). It translates
    # cleanly; the verifier cannot establish the load-bearing postcondition
    # ToSeq(Result())==ToSeq(leading)+ToSeq(tail) from those invariants (and in
    # fact the impl computes the reversed value), so it is REJECTED at exactly
    # that clause — not for a translation error. Correct only when the leading
    # run has 0/1 element (or all-equal factors); WRONG with >=2 distinct factors
    # — exactly model_prepatch.py's failure.
    {
        "id": "partial-reverse-leading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    result = []  # type: List[int]\n"
            "    i = len(leading) - 1\n"
            "    while i >= 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(-1 <= i and i < len(leading))\n"
            "        Invariant(MustTerminate(i + 1))\n"
            "        # invariants-end\n"
            "        result.append(leading[i])\n"
            "        i = i - 1\n"
            "    j = 0\n"
            "    while j < len(tail):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= j and j <= len(tail))\n"
            "        Invariant(MustTerminate(len(tail) - j + 1))\n"
            "        # invariants-end\n"
            "        result.append(tail[j])\n"
            "        j = j + 1\n"
            "    return result"),
        "refinement": "this IS the pre-patch behaviour (the insert(0, free_pos[i]) "
                      "loop for i=0..first_dum_pos-1, which leaves the leading run "
                      "REVERSED in front of each term). On the F2P witness "
                      "kahane_simplify(G(rho)*G(sigma)*G(mu)*G(-mu)) the leading run "
                      "[rho,sigma] is restored as [sigma,rho], so the result is "
                      "4*G(sigma)*G(rho) instead of the expected 4*G(rho)*G(sigma) — "
                      "test_kahane_simplify1 fails. model_prepatch.py reproduces "
                      "exactly this; it does NOT resolve.",
        "rationale": "rejected by the load-bearing Ensures ToSeq(Result()) == "
                     "ToSeq(leading)+ToSeq(tail): this impl builds the leading run in "
                     "reverse, so the result is reverse(leading)++tail, which differs "
                     "from leading++tail whenever the leading run has two distinct "
                     "factors; the postcondition is unprovable. If it verified the "
                     "order constraint is unpinned (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): drop the FIRST leading factor -----------
    # Correct on all of tail and on leading[1:], but skips leading[0] (loop starts
    # at i=1). Wrong on every input whose leading run is non-empty (the first-
    # element subdomain). Carries only permission + bound invariants (no value-
    # tracking) so it translates cleanly; the verifier cannot prove the load-
    # bearing postcondition because the result omits leading[0], so it is rejected
    # at that clause.
    {
        "id": "partial-skip-first-leading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    result = []  # type: List[int]\n"
            "    i = 1\n"
            "    while i < len(leading):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(1 <= i and i <= len(leading))\n"
            "        Invariant(MustTerminate(len(leading) - i + 1))\n"
            "        # invariants-end\n"
            "        result.append(leading[i])\n"
            "        i = i + 1\n"
            "    j = 0\n"
            "    while j < len(tail):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= j and j <= len(tail))\n"
            "        Invariant(MustTerminate(len(tail) - j + 1))\n"
            "        # invariants-end\n"
            "        result.append(tail[j])\n"
            "        j = j + 1\n"
            "    return result"),
        "refinement": "dropping the first leading factor (e.g. free_pos[1:"
                      "first_dum_pos] + ri) loses one gamma matrix from the front of "
                      "every term; on the F2P G(rho)*G(sigma)*G(mu)*G(-mu) it would "
                      "drop G(rho), yielding 4*G(sigma) instead of 4*G(rho)*G(sigma) "
                      "— a different (shorter) tensor product — so test_kahane_"
                      "simplify1 fails and the patch does NOT resolve.",
        "rationale": "rejected by ToSeq(Result()) == ToSeq(leading)+ToSeq(tail): this "
                     "impl computes ToSeq(leading).drop(1)+ToSeq(tail), which omits "
                     "leading[0] and so differs whenever leading is non-empty. "
                     "Partial-domain (first-element) divergence; if it verified the "
                     "leading-run completeness is unpinned (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): reverse the TAIL ------------------------
    # leading is restored correctly in order (gold first loop, with its value
    # invariant kept); only the core term is appended in DESCENDING index order,
    # producing leading ++ reverse(tail). Correct when tail has 0/1 element (or
    # all-equal factors); wrong whenever the core term has >=2 distinct factors.
    # The second loop carries only permission + bound invariants (no `.reversed()`
    # — not a PSeq op), so it translates cleanly and the rejection lands on the
    # load-bearing postcondition.
    {
        "id": "partial-reverse-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(leading):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(leading))\n"
            "        Invariant(ToSeq(result) == ToSeq(leading).take(i))\n"
            "        Invariant(MustTerminate(len(leading) - i + 1))\n"
            "        # invariants-end\n"
            "        result.append(leading[i])\n"
            "        i = i + 1\n"
            "    j = len(tail) - 1\n"
            "    while j >= 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(leading), 1 / 2))\n"
            "        Invariant(Acc(list_pred(tail), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(-1 <= j and j < len(tail))\n"
            "        Invariant(MustTerminate(j + 1))\n"
            "        # invariants-end\n"
            "        result.append(tail[j])\n"
            "        j = j - 1\n"
            "    return result"),
        "refinement": "reversing the core term (free_pos[0:first_dum_pos] + "
                      "list(reversed(ri))) scrambles the factor order WITHIN each "
                      "simplified term; a kahane_simplify result term carries an "
                      "ordered list of free-index labels, so reordering it produces a "
                      "different tensor expression than the F2P's expected "
                      "4*G(rho)*G(sigma) (e.g. for a multi-factor core term) and the "
                      "P2P test_kahane_algorithm ordering expectations break — does "
                      "NOT resolve.",
        "rationale": "rejected by ToSeq(Result()) == ToSeq(leading)+ToSeq(tail): this "
                     "impl builds leading++reverse(tail), differing whenever the core "
                     "term has two distinct factors, so the postcondition is "
                     "unprovable. Partial-domain (tail-order) divergence; if it "
                     "verified the tail order is unpinned (SPEC-TOO-WEAK).",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# NONE. meta.axioms == [], deep_model_references == [], no @ContractOnly, no
# axiom_check.py: the changed operation is pure order-preserving list/sequence
# concatenation modeled deeply in the impl. G-AX is vacuous (meta records it
# "vacuous"). There is no real-callee obligation to probe.
AXIOM_TESTS = []
