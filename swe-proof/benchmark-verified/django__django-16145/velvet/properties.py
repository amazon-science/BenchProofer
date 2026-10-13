"""properties.py — G-PBT falsification battery for django__django-16145 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method deriving the display form of a network
host shown in a startup banner, over a per-character carrier ``List Char``):

  formatHost (bracketed : Bool) (host : List Char) return (out : List Char)
    ensures out = displayAddress bracketed host
    ensures bracketed = true → out = ['['] ++ host ++ [']']
    ensures (bracketed = false ∧ host = "0".toList) → out = "0.0.0.0".toList
    ensures (bracketed = false ∧ host ≠ "0".toList) → out = host

``displayAddress`` is a TRANSPARENT ``def`` spelled out over the two inputs
(directive 8) — a three-way ladder decided in order: a bracketed host is wrapped
in a pair of delimiters; otherwise the unspecified-host shorthand is expanded to
its canonical dotted form; any other host is passed through unchanged. It is NOT
an opaque answer-key: every arm reduces to a concatenation of the inputs and
concrete literals, so ``decide`` computes it and no rival can "echo an oracle" —
the only way to satisfy the clause is to build the exact string.

WHAT THE SPEC DEFENDS. The content of interest is the middle arm: the bare
one-character shorthand must be normalised to its dotted-quad form for display,
while every other (non-bracketed) host is returned verbatim and every bracketed
host is wrapped. The prior behaviour returned the shorthand unchanged, so the
printed address was one a browser could not follow. The reject rivals attack, in
order: the wildcard expansion (drop it — the prior behaviour; or emit the wrong
literal), the delimiter wrapping (drop the trailing delimiter; misplace the
pair), and the identity pass-through (gut it to empty).

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on BOTH inputs — ``bracketed`` and ``host``:

  * ``bracketed`` selects the wrapping vs the ladder. The wrapping rivals differ
    from the frozen solution ONLY when ``bracketed = true`` and are refuted
    there; the wildcard/identity rivals differ ONLY when ``bracketed = false``
    and are refuted there. So the load-bearing flag is varied across BOTH arms
    by the witness set, not pinned at one value.
  * ``host`` is the surrounding / decided text. The wildcard rivals are refuted
    at the shorthand ``"0"``; the identity rival at an ordinary host ``"7"``; the
    wrapping rivals at ``"1"``. So ``host`` is varied over three distinct values
    and both the shorthand and the non-shorthand sub-domains are probed.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its list input is held at a fractional heap permission (``Acc(.,1/2)``) an
    impl can illegally overwrite. Lean/Velvet are referentially transparent:
    both inputs here are immutable values, there is no ``mut`` binder, no heap
    and no aliasing — so there is no read-only field to mutate and no substitute
    probe to build. Reported vacuous, not fabricated (porting map).
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent ``def`` over
    the method inputs, not an axiomatized oracle; the ``axioms`` region is empty.
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals right on part of the domain but
    diverging on a sub-domain (the wildcard shorthand; a truncated wildcard
    literal; a dropped/misplaced delimiter; a gutted identity arm). Each is
    refuted at a concrete point that varies the two binders.
  * AXIOM lane (nagini's single real-evaluation equivalence probe) — DROPPED.
    The axiom lane is G-AX's job; this gate ignores ``AXIOM_TESTS``. This bundle
    declares no ``axiom`` regardless (the derivation is primitive string ops).

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``formatHostTester bracketed host = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped (so no tactic script can mask the
verdict) and there are no ``require`` clauses, so every input reaches the
postcondition. ``List Char`` literals via ``"…".toList`` and ``Bool`` literals
are fully concrete, so ``decide`` settles the whole equality — no opaque term, no
conditioning, no head binders (hence no consistency obligation).
"""
from pathlib import Path

INSTANCE = "django__django-16145"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE impl body; lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap). Anchoring on the whole body keeps every
# ---- surgery inside the elided region — the frozen spec (the `method` header,
# ---- every `ensures`, and the `pure` region that also spells the literals) is
# ---- never touched. ----
_IMPL = (
    "    if bracketed then\n"
    "      return ['['] ++ host ++ [']']\n"
    "    else\n"
    '      if host = "0".toList then\n'
    '        return "0.0.0.0".toList\n'
    "      else\n"
    "        return host"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- admissibility helper: splice an in-region `assert` right after the
# ---- `-- impl-start` marker (still inside the elided impl region), keeping the
# ---- impl body and the frozen proof verbatim. The frozen `loom_solve <;>
# ---- simp_all [displayAddress]` discharges the extra side goal. ----
_IMPL_START = "    -- impl-start\n"


def _with_assert(assert_line: str) -> str:
    return _swap(_BASE, _IMPL_START, _IMPL_START + assert_line)


# ---- witness preamble: reach the contract through Velvet's tester machinery. ----
_TESTER = (
    "extract_program_for formatHost\n"
    "prove_precondition_decidable_for formatHost\n"
    "prove_postcondition_decidable_for formatHost\n"
    "derive_tester_for formatHost\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify against the frozen `prove_correct … by loom_solve <;>
    # simp_all [displayAddress]` script, else SPEC-TOO-STRONG. Both verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-wildcard-split",
        "kind": "soundness",
        "expect": "verify",
        # The dotted-quad expansion literal is built by concatenating two literal
        # fragments ("0.0." ++ "0.0") instead of one flat literal — same value,
        # different construction shape. Ports the nagini wildcard-split positive.
        "module": _with_impl(
            "    if bracketed then\n"
            "      return ['['] ++ host ++ [']']\n"
            "    else\n"
            '      if host = "0".toList then\n'
            '        return "0.0.".toList ++ "0.0".toList\n'
            "      else\n"
            "        return host"),
        "rationale": "structurally-different but semantically identical impl: the "
                     "dotted expansion is built as two concatenated literal "
                     "fragments instead of one flat literal — same value. Must "
                     "verify against `out = displayAddress bracketed host`; else "
                     "the postcondition is over-fit to the literal FORM => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-bracket-reshape",
        "kind": "soundness",
        "expect": "verify",
        # The wrapping is built by first forming the opening fragment
        # (`['['] ++ host`) as a `let`, then appending the closing delimiter —
        # same value, different construction shape. Ports the nagini
        # bracket-reshape positive.
        "module": _with_impl(
            "    if bracketed then\n"
            "      let opened := ['['] ++ host\n"
            "      return opened ++ [']']\n"
            "    else\n"
            '      if host = "0".toList then\n'
            '        return "0.0.0.0".toList\n'
            "      else\n"
            "        return host"),
        "rationale": "structurally-different but semantically identical impl: the "
                     "wrapping is built via an intermediate `let` fragment and a "
                     "trailing append instead of one flat concatenation — same "
                     "value. Must verify; else the postcondition is over-fit to "
                     "the concatenation FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed. This bundle declares NO `require` clause, so the
    # nagini "a normal F2P input satisfies the precondition" reading is vacuous
    # (nothing could exclude the F2P-shaped input). Re-aimed at the residual
    # admissibility risk on a total domain: that the post-image is
    # UNSATISFIABLE / degenerate at the interesting corner. The impl is kept
    # verbatim so the method's own obligation still discharges; an in-region
    # `assert` pins the post-image's decision at the F2P corner (a non-bracketed
    # shorthand host must expand to the dotted form) — the assert is LIVE, not
    # decoration: a false claim about the same point leaves an unsolved goal
    # (verified out-of-band). The frozen proof discharges the extra side goal.
    # =====================================================================
    {
        "id": "admiss-f2p-expands-shorthand",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_assert(
            "    assert (with_name_prefix `assert "
            '(displayAddress false "0".toList = "0.0.0.0".toList))\n'),
        "rationale": "the post-image is satisfiable AND non-degenerate at the F2P "
                     "corner: a non-bracketed host equal to the shorthand must "
                     "expand to the canonical dotted form (not be returned "
                     "verbatim). The in-region assert must discharge (else the "
                     "obligation is unsatisfiable/PRECOND-TOO-STRONG); the impl is "
                     "verbatim so every ensures clause still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (ELABORATES against the rival, FAILS against the frozen
    # solution — both halves confirmed out-of-band with real builds) and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test.
    # =====================================================================
    {
        "id": "weak-prepatch-no-wildcard",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug: the shorthand branch returns the host verbatim instead
        # of the expanded dotted form — exactly the prior behaviour. Correct on
        # every other input, wrong only at the shorthand.
        "module": _with_impl(
            "    if bracketed then\n"
            "      return ['['] ++ host ++ [']']\n"
            "    else\n"
            '      if host = "0".toList then\n'
            "        return host\n"
            "      else\n"
            "        return host"),
        "refinement": "this is exactly the prior behaviour: the shorthand host is "
                      "shown verbatim instead of expanded to its dotted form. A "
                      "faithful patch lacking the expansion renders the banner "
                      "with the un-followable shorthand address, so the failing "
                      "test that pins the announced address for the shorthand "
                      "input still observes the wrong string and still fails — it "
                      "would NOT resolve. This is the precise verify-not-resolve "
                      "case the bundle exists to encode.",
        "rationale": "REJECT from `out = displayAddress bracketed host` and its "
                     "middle clause: at `bracketed = false ∧ host = shorthand` the "
                     "post-image demands the dotted expansion but the impl returns "
                     "the host unchanged. Correct on every other input "
                     "(partial-domain). Refuted at `(false, \"0\")`.",
        "witness": _witness('formatHostTester false "0".toList'),
    },
    {
        "id": "weak-wrong-wildcard-literal",
        "kind": "uniqueness",
        "expect": "reject",
        # The expansion branch FIRES (so this is not the prepatch bug) but emits
        # a truncated literal (three quads, not four). A different failure mode
        # from weak-prepatch: right branch, wrong content — this pins the exact
        # literal, not merely the branch's existence. Refuted at the same
        # shorthand input because, like weak-prepatch, it diverges from the frozen
        # solution ONLY there (identical everywhere else), so no input separates
        # the two while keeping either correct.
        "module": _with_impl(
            "    if bracketed then\n"
            "      return ['['] ++ host ++ [']']\n"
            "    else\n"
            '      if host = "0".toList then\n'
            '        return "0.0.0".toList\n'
            "      else\n"
            "        return host"),
        "refinement": "the expansion is present but truncated (three quads). A "
                      "faithful patch expanding the shorthand to a malformed "
                      "dotted address renders a banner the test still rejects (it "
                      "pins the exact canonical address), so it would NOT resolve.",
        "rationale": "REJECT from the middle clause: at `(false, shorthand)` the "
                     "post-image pins the exact dotted literal, and the truncated "
                     "literal differs from it. A distinct failure mode from "
                     "weak-prepatch (right branch, wrong content) — it pins the "
                     "literal CONTENT, not the branch's existence. Refuted at "
                     "`(false, \"0\")`.",
        "witness": _witness('formatHostTester false "0".toList'),
    },
    {
        "id": "weak-drop-close-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        # The bracketed branch omits the trailing closing delimiter, yielding an
        # open, malformed wrap. Correct on every non-bracketed input, wrong on
        # every bracketed one.
        "module": _with_impl(
            "    if bracketed then\n"
            "      return ['['] ++ host\n"
            "    else\n"
            '      if host = "0".toList then\n'
            '        return "0.0.0.0".toList\n'
            "      else\n"
            "        return host"),
        "refinement": "dropping the trailing delimiter yields an unterminated "
                      "wrap. A faithful patch emitting the opening delimiter with "
                      "no closer renders a malformed host part in the banner, so "
                      "the failing tests that expect the delimited form still fail "
                      "— it would NOT resolve.",
        "rationale": "REJECT from `bracketed = true → out = ['['] ++ host ++ "
                     "[']']`: with `bracketed = true` the post-image carries the "
                     "trailing delimiter the rival never emits, so the strings "
                     "differ. Correct on the `bracketed = false` sub-domain "
                     "(partial-domain). Refuted at `(true, \"1\")` — the witness "
                     "that carries `bracketed = true`.",
        "witness": _witness('formatHostTester true "1".toList'),
    },
    {
        "id": "weak-misplace-delimiters",
        "kind": "uniqueness",
        "expect": "reject",
        # Both delimiters are present but MISPLACED — appended after the host
        # rather than wrapping it. A near-miss of weak-drop-close (both
        # delimiters present, right count), refuted on the same `bracketed = true`
        # arm but demonstrating the PLACEMENT is pinned, not merely the presence
        # of two delimiters.
        "module": _with_impl(
            "    if bracketed then\n"
            "      return host ++ ['['] ++ [']']\n"
            "    else\n"
            '      if host = "0".toList then\n'
            '        return "0.0.0.0".toList\n'
            "      else\n"
            "        return host"),
        "refinement": "the delimiters are present but appended after the host "
                      "instead of wrapping it. A faithful patch placing them "
                      "wrongly renders a malformed host token in the banner, so "
                      "the failing tests that expect the wrapped form still fail — "
                      "it would NOT resolve.",
        "rationale": "REJECT from `bracketed = true → out = ['['] ++ host ++ "
                     "[']']`: the post-image places the opening delimiter BEFORE "
                     "the host; the rival appends both after it, so the strings "
                     "differ whenever the host is non-empty. Near-miss to "
                     "weak-drop-close (both delimiters present) — pins the "
                     "PLACEMENT. Refuted at `(true, \"1\")`.",
        "witness": _witness('formatHostTester true "1".toList'),
    },
    {
        "id": "weak-gut-identity-branch",
        "kind": "uniqueness",
        "expect": "reject",
        # The identity (pass-through) branch is gutted to return the empty
        # sequence. Correct on the bracketed and shorthand inputs, wrong on every
        # ordinary non-shorthand host — this is what VARIES `host` to an ordinary
        # value and probes the non-shorthand sub-domain on the `bracketed = false`
        # arm.
        "module": _with_impl(
            "    if bracketed then\n"
            "      return ['['] ++ host ++ [']']\n"
            "    else\n"
            '      if host = "0".toList then\n'
            '        return "0.0.0.0".toList\n'
            "      else\n"
            "        return []"),
        "refinement": "gutting the pass-through branch returns the empty host for "
                      "every ordinary (non-shorthand, non-bracketed) address. A "
                      "faithful patch returning the empty address renders a banner "
                      "with no host, so the existing tests that pin the announced "
                      "address for an ordinary host still fail — it would NOT "
                      "resolve.",
        "rationale": "REJECT from `(bracketed = false ∧ host ≠ shorthand) → out = "
                     "host`: the branch leaves the empty sequence while the "
                     "post-image demands the host, so they differ whenever the "
                     "host is non-empty. Refuted at `(false, \"7\")` — an ordinary "
                     "host, the witness that VARIES `host` off the shorthand and "
                     "probes the non-shorthand `bracketed = false` sub-domain.",
        "witness": _witness('formatHostTester false "7".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 3 uniqueness rivals) plus a
# 1-case AXIOM lane. This bundle models the SAME functional core (the display
# form of the banner host), so the value/partial-domain classes port directly;
# the permission and precondition classes are vacuous on a referentially-
# transparent carrier.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   pos-control-wildcard-split         -> pos-wildcard-split          PORTED
#   pos-control-bracket-reshape        -> pos-bracket-reshape         PORTED
#   admiss-selfcall-wildcard           -> admiss-f2p-expands-shorthand RE-AIMED
#   frame-mutate-addr                  -> (none)                      VACUOUS
#   weak-prepatch-no-wildcard          -> weak-prepatch-no-wildcard   PORTED
#   weak-drop-close-bracket            -> weak-drop-close-delimiter   PORTED
#   weak-gut-identity-branch           -> weak-gut-identity-branch    PORTED
#   (new — clause coverage)            -> weak-wrong-wildcard-literal ADDED
#   (new — clause coverage)            -> weak-misplace-delimiters    ADDED
#   AXIOM_TESTS (1)                    -> (none)                      DROPPED (G-AX)
#
# RE-AIMED (admissibility): the sibling self-calls on the F2P input (the
#   shorthand host, non-bracketed) and asserts the result property holds. Here no
#   method has a `require` clause, so the "admits a normal input" reading is
#   vacuous; the case is re-aimed at proving the post-image is satisfiable and
#   NON-degenerate at the F2P corner (a non-bracketed shorthand host expands to
#   the dotted form). The in-region assert is discharged symbolically against
#   concrete literals by the frozen proof, and is LIVE — a false claim about the
#   same point leaves an unsolved goal (verified out-of-band).
# VACUOUS (frame-mutation): the sibling's MANDATORY rival WRITES a read-only
#   input held at Acc(.,1/2). This backend is referentially transparent, has no
#   heap and no aliasing, and this bundle declares NO `mut` binder — there is no
#   read-only input to overwrite and no substitute probe to build. Not fabricated
#   (porting map: this class is vacuous here).
# ADDED (weak-wrong-wildcard-literal): a second wildcard rival whose expansion
#   branch FIRES but emits a truncated literal — pins the exact dotted CONTENT,
#   not merely the branch's existence (the sibling's single wildcard rival covers
#   the branch-existence direction only). A real divergence from the post-image
#   with a machine-checked witness.
# ADDED (weak-misplace-delimiters): a second wrapping rival with both delimiters
#   present but MISPLACED — pins the PLACEMENT, not merely the presence of two
#   delimiters (near-miss of weak-drop-close). A real divergence with a
#   machine-checked witness.
#
# BINDER / POINT COVERAGE. The five reject witnesses probe THREE distinct input
#   tuples:
#     (false, "0")   weak-prepatch-no-wildcard, weak-wrong-wildcard-literal
#     (true,  "1")   weak-drop-close-delimiter, weak-misplace-delimiters
#     (false, "7")   weak-gut-identity-branch
#   so `bracketed` is varied over {true, false} (the load-bearing flag is NOT
#   pinned at one value) and `host` over {"0", "1", "7"} (both the shorthand and
#   non-shorthand sub-domains probed). All THREE independent conditional clauses
#   of the postcondition (wrapping / wildcard expansion / identity pass-through)
#   are attacked, and the master equality is attacked by every rival. Two pairs of
#   rivals share an input, and each pair does so legitimately: within a pair both
#   rivals diverge from the frozen solution ONLY at that input (identical
#   everywhere else), so no input separates one from the other while keeping
#   either correct — neither is a near-miss with a wider agreement domain that
#   would demand a more discriminating point. Every rival's witness was confirmed
#   with two real builds to ELABORATE against the rival and FAIL against the
#   frozen solution.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the derivation is primitive string ops on the code-point carrier), and
# this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
