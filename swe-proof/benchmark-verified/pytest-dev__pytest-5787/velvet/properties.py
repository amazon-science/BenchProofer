"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5787 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE — three cooperating contracted methods over a report value:

  serializeReport   (r : TraceReport) return (s : Serialized)
    ensures s = encode r          -- (S) the serialized form is exactly encode r
  deserializeReport (s : Serialized) return (r : TraceReport)
    ensures r = decode s          -- (D) the rebuilt report is exactly decode s
  roundTripReport   (r : TraceReport) return (out : TraceReport)
    ensures out = r               -- (R) serialize then reconstruct is identity

``TraceReport`` is either ``simple`` (a single exception: text/summary tokens +
attached blocks) or ``chained`` (an ORDERED list of ``Link``s + attached
blocks). ``encode`` of a chained report stores the WHOLE ordered link list
(``chain := some ls``) while echoing the final link's tokens at top level;
``decode`` rebuilds the full chain from the stored list. The single behaviour
under test is that the ENTIRE chain — its length, its order, and each link's
content — survives the round trip and is not collapsed to a single exception.

The load-bearing sub-structure of clause (S) is the ``chain`` field of the
serialized form on the ``chained`` arm: it must be ``some ls`` with ``ls`` the
full list in original order. A wrong serializer can (a) drop the list entirely
(``chain := none`` — the collapse), (b) keep it but reversed, (c) drop a link,
or (d) keep the right length but wrong per-link content. Clause (D) mirrors this
on the reconstruction site; clause (R) is the composite that the failing test
actually exercises end to end.

ADVERSARIAL READ of the nagini classes on this carrier (full accounting at the
foot of this file):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries this MANDATORY
    (a store into the read-only input held at half permission). This backend is
    referentially transparent: no input is declared ``mut``, there is no heap
    and no aliasing, so there is no read-only input to overwrite and no
    permission system to trip. Not fabricated (porting map: vacuous here).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``match`` / ``let`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal
    (``case «decreasing_1: spin» ... ⊢ False``). Dropping the clause rather
    than faking it is refused even earlier, by the elaborator's own check
    (``Decreasing annotations are required in total correctness semantics``).
    So divergence neither applies to this impl nor discharges the ``ensures``
    clauses vacuously if a rival introduces it.
  * COUNT / ORDER / VALUE (partial-domain) — APPLIES; the core class. A rival
    that collapses the chain, reverses it, drops a link, or duplicates a link's
    content is right on the degenerate single-link sub-domain and diverges on
    every genuine multi-link chain. Refuted by (S)/(D)/(R).
  * UNGROUNDED-ORACLE ECHO — N/A. ``encode`` / ``decode`` are concrete ``def``s
    over the method's own input (empty ``axioms`` region; ``meta.json axioms =
    []``); the cheapest correct impl simply evaluates them, covered honestly by
    the positive controls.

WITNESS MECHANISM. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the post-image through Velvet's own tester machinery:
``<method>Tester <input> = false`` says the extracted program's result violates
the method's postcondition at that concrete input. It is checked in a file whose
``prove_correct`` blocks have been stripped, so no tactic script can mask the
verdict. Every field of ``Link`` / ``Serialized`` / ``TraceReport`` is ``Nat`` /
``Option String`` / a finite sum, all with ``DecidableEq``, so each tester
reduces under ``decide`` and every witness closes by ``decide`` at literal
inputs. No witness binds a hypothesis (the carrier is fully transparent — the
per-link content tokens are concrete ``Nat``), so there is no
joint-satisfiability obligation. No ``sorry``/``admit``/``native_decide``/
``axiom`` appears in any witness.

Every witness below was checked out-of-band with ``scripts/lean_verify.sh``:
each ELABORATES against its rival (the tester ``decide``s to ``false`` — the
rival's output violates the postcondition at the probed input) and FAILS against
the frozen solution (whose tester ``decide``s to ``true`` there), so each
rejection is a genuine spec refutation and not mechanical tactic breakage.

INDEPENDENT AUDIT (re-derived, not inherited). Every reject witness was rebuilt
twice: all ELABORATE against their rival (exit 0) and all FAIL against the frozen
solution (exit 1) with a SEMANTIC refutation — ``decide`` reduces and reports
"``Tactic `decide` proved that the proposition <tester input> = false`` is false",
i.e. gold's tester is genuinely ``true`` at that input. No gold-side failure is a
stuck reduction, unknown identifier, or type error, so every rejection is
attributable to the postcondition. Additional probes, all built for real:
  * SPEC-TOO-WEAK — 7 NEW wrong impls the battery did not contain (top-level
    text/summary echoing the FIRST link instead of the last; ``extras`` dropped
    on serialize / on deserialize / across the composite; the ``.simple`` arm
    emitting ``chain := some []``; the chain DUPLICATED, i.e. too LONG rather
    than too short; the ``none`` arm rebuilding a constant report). All 7 were
    REJECTED, under the frozen proofs and again under an additive relaxed proof
    tail so a tactic gap could not be mistaken for a rejection. No spec hole.
    The two ``extras`` rivals were promoted into the battery above, since that
    field had no probe point at all.
  * SPEC-TOO-STRONG — 4 NEW correct reshapes VERIFY: serialize delegating to
    ``pure (encode r)``, deserialize delegating to ``pure (decode s)``, ``last``
    computed as ``ls.reverse.headD default`` instead of via ``getLast?``, and
    deserialize destructuring the whole ``Serialized`` instead of ``s.chain``. A
    fifth (``roundTripReport`` returning ``r`` directly) verifies once its proof
    body is reduced to a bare ``loom_solve``, which a rival may do; under the
    frozen two-line script it fails with ``No goals to be solved`` — tactic
    brittleness, not a spec that rejects a correct impl. No soundness hole.
  * The admissibility assert is LIVE: flipping its claimed chain to the reversed
    ``some [l1, l0]`` leaves ``error: unsolved goals`` (exit 1), so the case is
    not passing on a vacuous assert.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(mapping.md §3: the serialization calls no unchanged foreign callee; every step
is R or I). Nothing in any proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5787"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies WHOLLY inside one impl region (or one prove_correct body)
# and is unique in Solution.lean, so every swap edits only the elided region and
# preserves same_spec + the byte-identical obligation statement. Asserted below.
# ---------------------------------------------------------------------------

# The full `match` body of serializeReport's impl region.
_SER_BLOCK = (
    "\n    match r with\n"
    "    | .simple t s xs => pure { text := t, summary := s, extras := xs, chain := none }\n"
    "    | .chained ls xs =>\n"
    "        let last := (ls.getLast?).getD default\n"
    "        pure { text := last.text, summary := last.summary, extras := xs, chain := some ls }\n    ")

# The single line inside serializeReport that stores the chain link list — the
# load-bearing sub-structure of clause (S). Every serialize rival edits ONLY
# this line.
_SER_LINE = (
    "        pure { text := last.text, summary := last.summary, extras := xs, chain := some ls }")

# The full `match` body of deserializeReport's impl region.
_DES_BLOCK = (
    "\n    match s.chain with\n"
    "    | some ls => pure (.chained ls s.extras)\n"
    "    | none    => pure (.simple s.text s.summary s.extras)\n    ")

# The `some`-arm line of deserializeReport — where the chain is rebuilt.
_DES_SOME = "    | some ls => pure (.chained ls s.extras)"

# The full impl body of roundTripReport.
_RT_BLOCK = (
    "\n    let s ← serializeReport r\n"
    "    let out ← deserializeReport s\n"
    "    return out\n    ")

# serializeReport's frozen proof body — retuned only by the admissibility case,
# which prepends an in-region `assert` whose goal `decide` closes.
_SER_PROOF = "prove_correct serializeReport by\n  loom_solve <;> simp_all [encode]"

for _a in (_SER_BLOCK, _SER_LINE, _DES_BLOCK, _DES_SOME, _RT_BLOCK, _SER_PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


def _witness(method, body):
    """Velvet tester preamble for `method`, then the `example` refutation.

    `extract_program_for` / `derive_tester_for` are directives inside the witness
    (appended to BOTH the rival and the gold file), so the tester name exists on
    both sides by construction — it is not a variant-only symbol.
    """
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — one structurally-different CORRECT impl per
    # obligation, each keeping the byte-identical `ensures` and re-verifying. If
    # a faithful correct reshape cannot verify, the clause is over-fit to the
    # frozen impl's syntactic form => SPEC-TOO-STRONG. All three verify under the
    # frozen proof unchanged (the reshapes are observationally identical).
    # =====================================================================
    {
        "id": "pos-serialize-armswap",
        "kind": "soundness",
        "expect": "verify",
        # `match` arms reordered (chained arm first, simple arm second). Same
        # value on every input; the frozen `loom_solve <;> simp_all [encode]`
        # closes it unchanged.
        "module": _swap(
            _BASE, _SER_BLOCK,
            "\n    match r with\n"
            "    | .chained ls xs =>\n"
            "        let last := (ls.getLast?).getD default\n"
            "        pure { text := last.text, summary := last.summary, extras := xs, chain := some ls }\n"
            "    | .simple t s xs => pure { text := t, summary := s, extras := xs, chain := none }\n    "),
        "rationale": "CORRECT reshape of serializeReport: the two `match` arms are "
        "reordered (chained first), an observationally identical impl. Clause (S) "
        "`s = encode r` must still discharge — else it is over-fit to the arm "
        "ORDER, SPEC-TOO-STRONG. Defends serializeReport.",
    },
    {
        "id": "pos-deserialize-armswap",
        "kind": "soundness",
        "expect": "verify",
        # deserialize arms reordered (none arm first). Same value on every input.
        "module": _swap(
            _BASE, _DES_BLOCK,
            "\n    match s.chain with\n"
            "    | none    => pure (.simple s.text s.summary s.extras)\n"
            "    | some ls => pure (.chained ls s.extras)\n    "),
        "rationale": "CORRECT reshape of deserializeReport: the `some`/`none` arms "
        "are reordered, observationally identical. Clause (D) `r = decode s` must "
        "still discharge — else it is over-fit to the arm order, SPEC-TOO-STRONG. "
        "Defends deserializeReport.",
    },
    {
        "id": "pos-roundtrip-nested",
        "kind": "soundness",
        "expect": "verify",
        # Inline the intermediate `s` binding: pass `← serializeReport r` directly
        # into deserializeReport. Same data flow, no intermediate local.
        "module": _swap(
            _BASE, _RT_BLOCK,
            "\n    let out ← deserializeReport (← serializeReport r)\n"
            "    return out\n    "),
        "rationale": "CORRECT reshape of roundTripReport: the intermediate binding "
        "is inlined (`← serializeReport r` passed straight into deserializeReport). "
        "Same composite data flow. Clause (R) `out = r` must still discharge — else "
        "it is over-fit to the `let`-binding FORM, SPEC-TOO-STRONG. Defends "
        "roundTripReport.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling builds an F2P-shaped multi-stage chain and
    # asserts the precondition admits it. There is NO `require` clause on any
    # method here, so that probe is vacuous. Re-aimed at the residual total-domain
    # risk: that the post-image is DEGENERATE at the interesting point. An
    # in-region `assert` pins, on an F2P-shaped TWO-LINK chain (distinct links, a
    # connecting description on the first), that (a) `encode`'s stored `chain` is
    # the FULL ordered two-element list (not `none`, not truncated) and (b)
    # `decode ∘ encode` rebuilds that exact two-link chain. So the modeled
    # behaviour is non-degenerate exactly where the fix matters. The assert is
    # live (a false claim leaves an unsolved goal — checked during authoring); the
    # serialize impl follows verbatim so clause (S)'s own obligation still
    # discharges. Only serializeReport's proof is retuned (to also close the
    # decidable assert goal); the other two proofs are untouched.
    # =====================================================================
    {
        "id": "admiss-multilink-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _SER_BLOCK,
                "\n"
                "    assert (with_name_prefix `admiss\n"
                "      ((encode (.chained [⟨1,2,some \"c\"⟩, ⟨3,4,none⟩] [])).chain\n"
                "         = some [⟨1,2,some \"c\"⟩, ⟨3,4,none⟩]\n"
                "       ∧ decode (encode (.chained [⟨1,2,some \"c\"⟩, ⟨3,4,none⟩] []))\n"
                "         = .chained [⟨1,2,some \"c\"⟩, ⟨3,4,none⟩] []))\n"
                "    match r with\n"
                "    | .simple t s xs => pure { text := t, summary := s, extras := xs, chain := none }\n"
                "    | .chained ls xs =>\n"
                "        let last := (ls.getLast?).getD default\n"
                "        pure { text := last.text, summary := last.summary, extras := xs, chain := some ls }\n    "),
            _SER_PROOF,
            "prove_correct serializeReport by\n"
            "  loom_solve <;> first | decide | simp_all [encode]"),
        "rationale": "the modeled behaviour is non-degenerate at the F2P-shaped "
        "two-link chain: `encode`'s stored `chain` is the FULL ordered list "
        "`some [l0, l1]` (neither `none` nor truncated) and `decode ∘ encode` "
        "rebuilds that exact two-link chain — so the round trip preserves length, "
        "order, and per-link content where the fix matters. The in-region assert "
        "must discharge (else the obligation is degenerate at the interesting "
        "point); the serialize impl is kept verbatim so clause (S) still "
        "discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each edits ONE impl line (proof left frozen: it fails on
    # the reshaped/wrong impl regardless, and the rejection is attributed to the
    # postcondition by the machine-checked witness, not to tactic breakage). Each
    # witness probes a DISTINCT input point.
    # =====================================================================

    # ---- serialize clause (S): drop the link list entirely (the collapse) ----
    {
        "id": "serialize-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SER_LINE,
            "        pure { text := last.text, summary := last.summary, extras := xs, chain := none }"),
        "refinement": "this IS the pre-patch serializer: a chained report stored "
        "only its outermost exception's top-level tokens and DROPPED the ordered "
        "link list (chain := none). The failing test builds a two-link chained "
        "failure and asserts the reconstructed chain still has length >= 2 with "
        "per-link content; with the list dropped, deserialization rebuilds a single "
        "exception and the chain collapses to one stage — it does NOT resolve (the "
        "very bug the patch fixes).",
        "rationale": "REJECT from clause (S) `s = encode r`: on the chained arm "
        "`encode` stores `chain := some ls`, but the rival stores `none`, so the "
        "serialized form differs from `encode r` for every chained report. "
        "Verifying would be SPEC-TOO-WEAK on the load-bearing chain field. Refuted "
        "at a distinct two-link chain.",
        "witness": _witness(
            "serializeReport",
            'example : serializeReportTester (.chained [⟨1,2,some "c"⟩, ⟨3,4,none⟩] []) = false := by\n'
            "  decide\n"),
    },

    # ---- serialize clause (S): keep the list but REVERSED (order) ----
    {
        "id": "serialize-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SER_LINE,
            "        pure { text := last.text, summary := last.summary, extras := xs, chain := some ls.reverse }"),
        "refinement": "a faithful patch serializing the links newest-first "
        "(reversed) would present the outermost failure as the originating cause on "
        "reconstruction. The failing test asserts per-index link content matches the "
        "original at each position, so reversed order fails per index — it would NOT "
        "resolve. Length is preserved, so ONLY the order structure of clause (S) "
        "catches it.",
        "rationale": "REJECT from clause (S): `some ls.reverse != some ls` "
        "(= `(encode r).chain`) for every chain that is not palindromic. Length is "
        "right; the rival is caught ONLY by the ORDER embedded in `encode`. Refuted "
        "at a distinct non-palindromic two-link chain.",
        "witness": _witness(
            "serializeReport",
            'example : serializeReportTester (.chained [⟨5,6,some "d"⟩, ⟨7,8,none⟩] []) = false := by\n'
            "  decide\n"),
    },

    # ---- serialize clause (S): DROP the first link (length + shift) ----
    {
        "id": "serialize-dropfirst",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SER_LINE,
            "        pure { text := last.text, summary := last.summary, extras := xs, chain := some ls.tail }"),
        "refinement": "a faithful patch serializing the chain from its second link "
        "onward would drop the originating exception (the root cause) from the "
        "transport form. The failing test builds a multi-link chain and checks the "
        "full length and every link; the dropped root cause fails the length and "
        "per-link assertions — it would NOT resolve.",
        "rationale": "REJECT from clause (S): `some ls.tail != some ls` "
        "(= `(encode r).chain`) whenever the chain is non-empty — the stored list "
        "is one link short and shifted. Refuted at a distinct THREE-link chain (the "
        "only witness that varies chain length to 3).",
        "witness": _witness(
            "serializeReport",
            "example : serializeReportTester "
            "(.chained [⟨1,2,none⟩, ⟨3,4,none⟩, ⟨5,6,none⟩] []) = false := by\n"
            "  decide\n"),
    },

    # ---- serialize clause (S): right length, WRONG per-link content ----
    {
        "id": "serialize-const-firstlink",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SER_LINE,
            "        pure { text := last.text, summary := last.summary, extras := xs, "
            "chain := some (ls.map (fun _ => ls.headD default)) }"),
        "refinement": "a faithful patch that copied the first link's content into "
        "every serialized slot would duplicate the originating cause across all "
        "stages. The failing test asserts each reconstructed link matches the "
        "original at that index; the duplicated content fails for every later stage "
        "— it would NOT resolve. Length is preserved, so ONLY the per-link-content "
        "structure of clause (S) catches it.",
        "rationale": "REJECT from clause (S): `some (ls.map (fun _ => ls.headD "
        "default)) != some ls` (= `(encode r).chain`) whenever any link differs "
        "from the first. Length is right; caught ONLY by the per-link content. "
        "Refuted at a distinct two-link chain whose links differ.",
        "witness": _witness(
            "serializeReport",
            "example : serializeReportTester "
            "(.chained [⟨2,3,none⟩, ⟨4,5,none⟩] []) = false := by\n"
            "  decide\n"),
    },

    # ---- serialize clause (S): drop the ATTACHED BLOCKS (the `extras` field) ----
    # Added by the audit. Every other reject case probes the `chain` field and
    # passes `[]` for `extras`, so no witness in the battery varied that field at
    # all: a serializer that transported the chain perfectly but dropped the
    # attached blocks was unattacked. Witness probes at a NON-EMPTY `extras`.
    {
        "id": "serialize-drop-extras",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SER_LINE,
            "        pure { text := last.text, summary := last.summary, extras := [], chain := some ls }"),
        "refinement": "a faithful patch that serialized the chain correctly but "
        "dropped the report's attached supplementary text blocks would lose the "
        "captured-output/log sections that travel with a failure. Those blocks are "
        "restored on reconstruction and rendered with the report, so a round trip "
        "that returns none of them does not reproduce the original report — it "
        "would NOT resolve. The chain is fully preserved here, so ONLY the "
        "attached-block component of clause (S) catches it.",
        "rationale": "REJECT from clause (S) `s = encode r`: `encode` stores "
        "`extras := xs`, but the rival stores `[]`, so the serialized form differs "
        "from `encode r` for every chained report carrying at least one attached "
        "block. Refuted at the battery's only probe point with a NON-EMPTY "
        "`extras`, a field no other witness varies.",
        "witness": _witness(
            "serializeReport",
            "example : serializeReportTester "
            '(.chained [⟨6,7,none⟩, ⟨8,9,some "e"⟩] [("cap","out","=")]) = false := by\n'
            "  decide\n"),
    },

    # ---- deserialize clause (D): drop the ATTACHED BLOCKS on rebuild ----
    # Added by the audit; the `extras` mirror of the above on the second site.
    {
        "id": "deserialize-drop-extras",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DES_SOME,
            "    | some ls => pure (.chained ls [])"),
        "refinement": "a faithful reconstruction that rebuilt the full chain but "
        "restored no attached supplementary blocks would drop the captured "
        "output/log sections from the reconstructed report, which is then rendered "
        "without them. The blocks are part of what must survive the round trip — "
        "it would NOT resolve. The chain is fully preserved, so ONLY the "
        "attached-block component of clause (D) catches it.",
        "rationale": "REJECT from clause (D) `r = decode s`: when `s.chain = some "
        "ls`, `decode` rebuilds `.chained ls s.extras`, but the rival rebuilds "
        "`.chained ls []`, differing for every serialized form carrying at least "
        "one attached block. Refuted at a distinct serialized form with a "
        "NON-EMPTY `extras`.",
        "witness": _witness(
            "deserializeReport",
            "example : deserializeReportTester "
            '⟨3,4,[("sec","body","-")],some [⟨1,2,some "c"⟩, ⟨3,4,none⟩]⟩ = false := by\n'
            "  decide\n"),
    },

    # ---- deserialize clause (D): collapse a stored chain to a simple report ----
    {
        "id": "deserialize-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DES_SOME,
            "    | some ls => pure (.simple s.text s.summary s.extras)"),
        "refinement": "this IS the pre-patch reconstruction: even given a full "
        "serialized link list, it always rebuilt a SINGLE exception from the "
        "top-level tokens, discarding the stored chain. The failing test reads the "
        "reconstructed chain back and asserts length >= 2 — with the list discarded "
        "the chain collapses to one stage — it would NOT resolve. Pins the SECOND "
        "cooperating site, not just serialize.",
        "rationale": "REJECT from clause (D) `r = decode s`: when `s.chain = some "
        "ls`, `decode` rebuilds `.chained ls s.extras`, but the rival rebuilds a "
        "`.simple`, differing for every stored chain. Verifying would be "
        "SPEC-TOO-WEAK on the reconstruction site. Refuted at a distinct serialized "
        "form carrying a two-link list.",
        "witness": _witness(
            "deserializeReport",
            'example : deserializeReportTester ⟨9,9,[],some [⟨1,2,some "c"⟩, ⟨3,4,none⟩]⟩ = false := by\n'
            "  decide\n"),
    },

    # ---- deserialize clause (D): rebuild the chain REVERSED (order) ----
    {
        "id": "deserialize-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DES_SOME,
            "    | some ls => pure (.chained ls.reverse s.extras)"),
        "refinement": "a faithful reconstruction that rebuilt the chain from the "
        "stored list in reverse would present the links newest-first, so the "
        "originating cause appears as the outermost failure. The failing test "
        "asserts per-index link content on the reconstructed chain — reversed order "
        "fails per index — it would NOT resolve. Mirrors the serialize order attack "
        "on the reconstruction site.",
        "rationale": "REJECT from clause (D): `.chained ls.reverse != .chained ls` "
        "(= `decode s` when `s.chain = some ls`) for every non-palindromic list. "
        "Length preserved; caught ONLY by order. Refuted at a distinct serialized "
        "form carrying a non-palindromic two-link list.",
        "witness": _witness(
            "deserializeReport",
            "example : deserializeReportTester ⟨0,0,[],some [⟨5,6,none⟩, ⟨7,8,none⟩]⟩ = false := by\n"
            "  decide\n"),
    },

    # ---- roundtrip clause (R): serialize, then collapse on rebuild ----
    {
        "id": "roundtrip-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RT_BLOCK,
            "\n    let s ← serializeReport r\n"
            "    return (.simple s.text s.summary s.extras)\n    "),
        "refinement": "the composite pre-patch behaviour: serialize correctly, then "
        "reconstruct a single exception from the top-level tokens, collapsing the "
        "chain. The failing test exercises exactly this deserialize ∘ serialize "
        "lifecycle and asserts the reconstructed chain has length >= 2 — the "
        "collapsed composite fails — it would NOT resolve.",
        "rationale": "REJECT from clause (R) `out = r`: for a chained input the "
        "composite returns a `.simple` built from the serialized top-level tokens, "
        "which is not equal to the original chained report. Verifying would be "
        "SPEC-TOO-WEAK on the composite lifecycle the F2P exercises. Refuted at a "
        "distinct two-link chain.",
        "witness": _witness(
            "roundTripReport",
            'example : roundTripReportTester (.chained [⟨1,2,some "c"⟩, ⟨3,4,none⟩] []) = false := by\n'
            "  decide\n"),
    },

    # ---- roundtrip clause (R): ignore the input entirely (constant output) ----
    {
        "id": "roundtrip-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RT_BLOCK,
            "\n    return (.simple 0 0 [])\n    "),
        "refinement": "a degenerate composite that discards the report and returns a "
        "fixed empty simple report round-trips nothing; the reconstructed longrepr "
        "would carry none of the original chain, so the failing test's length and "
        "per-link assertions all fail — it would NOT resolve.",
        "rationale": "REJECT from clause (R) `out = r`: the constant `.simple 0 0 "
        "[]` equals `r` on no admissible chained report (and on essentially no "
        "input). Verifying would be SPEC-TOO-WEAK — the clause would not force the "
        "output to depend on the input. Refuted at a distinct single-link chain "
        "(the only witness at chain length 1).",
        "witness": _witness(
            "roundTripReport",
            "example : roundTripReportTester (.chained [⟨9,9,none⟩] []) = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The sibling battery has 9 SPEC cases (1 soundness positive, 1 admissibility,
# 7 uniqueness rivals: 2 frame-mutation + 5 chain-collapse) plus a 1-case AXIOM
# lane. That bundle modeled a permission-bearing List[int] carrier for TWO
# functions (serialize_chain / deserialize_chain) with copy_link as the per-link
# identity. THIS bundle models the SAME whole-chain-survival behaviour over a
# richer, referentially-transparent carrier — an inductive TraceReport
# (simple | chained) with a structured Serialized form — and contracts THREE
# obligations: serializeReport, deserializeReport, and the composite
# roundTripReport that the F2P test actually exercises. The value/order/content
# surface carries across; the permission surface does not exist here.
#
#   sibling case                    -> here                             disposition
#   ---------------------------------------------------------------------------
#   pos-control-localreshape        -> pos-serialize-armswap            PORTED
#   (composite not modeled there)   -> pos-deserialize-armswap          ADDED (obl)
#   (composite not modeled there)   -> pos-roundtrip-nested             ADDED (obl)
#   admiss-multistage               -> admiss-multilink-nondegenerate   RE-AIMED
#   frame-serialize-write           -> (none)                          VACUOUS
#   frame-deserialize-write         -> (none)                          VACUOUS
#   outermost-only-serialize        -> serialize-collapse               PORTED
#   reverse-order-serialize         -> serialize-reverse                PORTED
#   drop-first-link-serialize       -> serialize-dropfirst              PORTED
#   const-first-link-serialize      -> serialize-const-firstlink        PORTED
#   deserialize-collapse            -> deserialize-collapse             PORTED
#   (mirror of reverse on site 2)   -> deserialize-reverse              ADDED (obl)
#   (composite lifecycle)           -> roundtrip-collapse               ADDED (obl)
#   (composite lifecycle)           -> roundtrip-constant               ADDED (obl)
#   (no sibling case: `extras`)     -> serialize-drop-extras            ADDED (audit)
#   (no sibling case: `extras`)     -> deserialize-drop-extras          ADDED (audit)
#   AXIOM_TESTS (1)                 -> (none)                          DROPPED (G-AX)
#
# 6 ported, 1 re-aimed, 5 added to cover obligations the sibling did not model,
# 2 added by the audit to attack a field no case probed, 2 vacuous, 1 dropped
# = 14 SPEC cases (3 soundness, 1 admissibility, 10 uniqueness). The 5 "added
# (obl)" cases are NOT parity padding: deserializeReport
# and roundTripReport are genuinely-modeled obligations here (the sibling modeled
# only serialize/deserialize as a permission pair, not the composite), and the
# porting rule is to defend AND attack every obligation this bundle models. Each
# added rival is a real distinct failure mode with a machine-checked witness.
#
# VACUOUS (frame-serialize-write / frame-deserialize-write). The sibling carries
#   these MANDATORY because each input is held at half permission and an in-place
#   write is rejected for insufficient permission. This backend is referentially
#   transparent and declares NO `mut` binder over any input — `r` and `s` are
#   immutable values with no heap footprint — so there is no read-only input to
#   overwrite and no permission system to trip. Not fabricated (porting map:
#   vacuous here).
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``match`` / ``let`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal
#   (``case «decreasing_1: spin» ... ⊢ False``). Dropping the clause rather
#   than faking it is refused even earlier, by the elaborator's own check
#   (``Decreasing annotations are required in total correctness semantics``).
#   So divergence neither applies to this impl nor discharges the ``ensures``
#   clauses vacuously if a rival introduces it.
# DROPPED (AXIOM_TESTS). The sibling's axiom lane validates its A-reference deep
#   model against the real callee. This bundle declares no axioms and no
#   deep-model references (mapping.md §3: empty `axioms` region), so there is
#   nothing to probe — and this gate ignores AXIOM_TESTS regardless.
#
# OBLIGATION / CLAUSE COVERAGE. Three obligations, each with ONE input binder and
#   ONE top-level equality clause. Every obligation is DEFENDED and ATTACKED:
#   * serializeReport  (S) `s = encode r`  — defended by pos-serialize-armswap
#     (and admiss-multilink-nondegenerate); attacked by serialize-collapse
#     (drop list), serialize-reverse (order), serialize-dropfirst (length),
#     serialize-const-firstlink (per-link content) — the four independent ways
#     the load-bearing `chain` sub-structure can be wrong — plus
#     serialize-drop-extras (the attached-block field, added by the audit).
#   * deserializeReport (D) `r = decode s` — defended by pos-deserialize-armswap;
#     attacked by deserialize-collapse (drop chain), deserialize-reverse
#     (order), and deserialize-drop-extras (attached blocks, added by the audit).
#   * roundTripReport  (R) `out = r`       — defended by pos-roundtrip-nested;
#     attacked by roundtrip-collapse (realistic composite prepatch) and
#     roundtrip-constant (input-independent output).
# BINDER / PROBE-POINT COVERAGE. The single input binder of each obligation is
#   varied across that obligation's reject witnesses, all at DISTINCT input
#   points (pts, per obligation):
#     serializeReport `r`   (pts=5): [l(1,2,c),l(3,4)]; [l(5,6,d),l(7,8)];
#                                    [l(1,2),l(3,4),l(5,6)] (len 3);
#                                    [l(2,3),l(4,5)];
#                                    [l(6,7),l(8,9,e)] w/ extras [("cap","out","=")]
#     deserializeReport `s` (pts=3): ⟨9,9,[],some [l(1,2,c),l(3,4)]⟩;
#                                    ⟨0,0,[],some [l(5,6),l(7,8)]⟩;
#                                    ⟨3,4,[("sec","body","-")],some [l(1,2,c),l(3,4)]⟩
#     roundTripReport `r`   (pts=2): [l(1,2,c),l(3,4)]; [l(9,9)] (len 1)
#   Chain LENGTH is varied (1, 2, 3), link ORDER is varied (non-palindromic
#   inputs so reverse is observable), per-link CONTENT is varied (distinct link
#   tokens so a content swap is observable), the connecting-description field
#   `desc` is varied (some/none), and `extras` is varied EMPTY vs NON-EMPTY (the
#   audit's two added cases; before them every witness passed `[]`, leaving that
#   field's contribution to (S)/(D) unprobed). No two rivals of the same
#   obligation share an input point.
# WITNESS DISCRIMINATION (verified during authoring with two real builds per
#   reject case via scripts/lean_verify.sh): each witness ELABORATES against its
#   rival (the extracted tester `decide`s to false — the rival's output violates
#   the postcondition at the probed input) and FAILS against the frozen solution
#   (whose tester `decide`s to true there). No witness binds a hypothesis (the
#   carrier is fully transparent), so there is no joint-satisfiability
#   obligation. No `sorry`/`admit`/`native_decide`/`axiom` in any witness.
AXIOM_TESTS = []
