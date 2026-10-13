"""properties.py — G-PBT falsification battery for django__django-11815 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct referenceEnumMember`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  referenceEnumMember (module className memberName : List Char)
      (payloadText : List Char) (payloadImports : List (List Char))
      return (out : (List Char) × (List (List Char)))
    require ∀ c ∈ memberName, isIdentChar c
    ensures out.1 = memberReference module className memberName
    ensures out.2 = referenceImports module
    ensures out = (memberReference module className memberName,
                   referenceImports module)

``memberReference`` and ``referenceImports`` are total, fully-unfolded pure
functions in the ``pure`` region (the ``axioms`` region declares nothing).
The two load-bearing ``ensures`` clauses pin the result to:

  (P0) out.1 = memberReference module className memberName
       = module ++ '.' ++ className ++ '[' ++ ('\\'' ++ memberName ++ '\\'')
         ++ ']'    — the reference text in SUBSCRIPT form keyed on the stable
       symbolic name; the subscription delimiters and the quoted name are all
       pinned, and it is built from module/className/memberName ALONE.
  (P1) out.2 = referenceImports module = ["import " ++ module] — exactly the one
       import the reference needs, a function of module ALONE.

``payloadText`` and ``payloadImports`` are read-only inputs the result MUST NOT
depend on: they describe the member's stored payload as rendered on its own, and
neither postcondition mentions them. The load-bearing subtlety is that the
reference is keyed on the STABLE symbolic name (``memberName``) and never on the
mutable payload (``payloadText``) — the two are allowed to disagree, and the
post-image must hold for every value the payload inputs take.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated. (See footer.)
  * NONTERMINATION — the spec REJECTS a diverging rival, but the class is not
    shippable as an ``expect="reject"`` case for a TOOLING reason, re-measured
    here rather than argued. This bundle runs under
    ``loom.semantics.termination "total"``, so a diverging impl does NOT verify:
    an impl whose loop carries no decreasing measure is refused with
    ``error: Decreasing annotations are required in total correctness
    semantics`` (exit 1, measured, both with the gold body after the loop and
    with a deliberately wrong return after it). So the spec is NOT weak here and
    the earlier ``partial``-semantics reading of this class no longer describes
    this carrier.
    What blocks the case is the WITNESS half, not the spec: that same
    termination error fires while elaborating the ``method`` body, which is
    upstream of everything a witness file contains and is NOT removed by the
    obligation-stripping the witness build performs. Measured — against the
    diverging rival, a witness file carrying only ``example : 1 + 1 = 2 := by
    decide`` fails with the identical termination error (exit 1), as does one
    that merely derives the tester. So no witness can ELABORATE against this
    rival, which is the half a reject case must pass, and the gate would record
    ``witness-unproven`` for a rival the spec genuinely refuses. A
    ``witness_reference`` does not help: it replaces the GOLD-side subject,
    while the failure here is on the rival side. Recorded as a tooling
    limitation on the witness path, not as a spec hole and not as a vacuous
    class. (See footer.)
  * PAYLOAD-KEYED / WRONG-SOURCE — APPLIES, and is the headline SPEC-TOO-WEAK
    probe: build the reference from the mutable payload instead of the stable
    symbolic name. Attacked on TWO axes, because a single rival that changes both
    the key and the delimiters cannot attribute its refutation to either:
    ``weak-payload-keyed-callform`` (payload key AND call-form delimiters — the
    pre-fix shape, refuted at every input) and ``weak-payload-keyed-subscript``
    (the delimiters and quoting gold-correct, ONLY the key wrong — refuted
    exactly where the payload differs from the name, and agreeing with the frozen
    impl where they coincide).
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the reference but
    diverging on a sub-domain (the wrong subscription delimiters; a tampered
    import line; the payload's own imports unioned into the import set).
  * QUALIFIER ORDER — APPLIES, and was UNATTACKED before this audit. Every rival
    above keys, delimits, or imports wrongly while leaving the two qualifier
    binders in their given order, so nothing tested that ``module`` and
    ``className`` enter the reference in THAT order rather than the other.
    ``weak-qualifier-swapped`` closes it: both binders are read, both are
    present, only their order is exchanged.
  * UNGROUNDED-ORACLE ECHO — N/A. ``memberReference``/``referenceImports`` are
    concrete ``def``s spelled out as closed-form concatenations of the inputs
    (no opaque answer key to echo); the cheapest correct impl simply evaluates
    them, which the ``pos-oracle-direct`` positive covers honestly.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
six witnesses sit at six DISTINCT input points and vary every binder the
spec predicates read (``module``, ``className``, ``memberName``), plus the
read-only payload inputs. THREE of them are AXIS-ISOLATING: their rivals agree
with the frozen impl off one sub-domain, so the witness point is what carries the
claim (``weak-payload-keyed-subscript`` for "the reference never depends on the
payload text", ``weak-import-union-payload`` for "the import set never depends on
the payload's imports", ``weak-qualifier-swapped`` for "the two qualifiers enter
in their given order"). Every witness's gold-side failure is a plain evaluation
(``decide`` reduces the tester and reports the claim false), so no case rests on
a stuck reduction, a type error, or a missing identifier.
"""
from pathlib import Path

INSTANCE = "django__django-11815"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap) --------
_GOLD_IMPL = (
    "    let refString : List Char :=\n"
    "      module ++ ['.'] ++ className ++ ['['] ++ (['\\''] ++ memberName ++ ['\\'']) ++ [']']\n"
    "    let imports : List (List Char) := [\"import \".toList ++ module]\n"
    "    return (refString, imports)"
)

def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- proof-body anchor. The `prove_correct` TACTIC BODY is the second region
# ---- the consumer spec view elides, so replacing it keeps `markers.same_spec`
# ---- and leaves the `prove_correct referenceEnumMember` obligation (its header,
# ---- hence its statement) byte-identical — only the script that discharges it
# ---- changes. Used solely to EXTEND the frozen tail for a case that adds an
# ---- in-region `assert`: the frozen script does not know about a goal the frozen
# ---- impl never raises. Nothing here weakens an obligation; `variant_scope`
# ---- independently rejects a dropped obligation, a new axiom, or a `sorry`.
_GOLD_PROOF = (
    "prove_correct referenceEnumMember by\n"
    "  loom_solve\n"
    "  all_goals simp_all [memberReference, quotedName, referenceImports]\n"
)

def _proof(src, body):
    """Replace the `prove_correct` tactic body of an already-built variant."""
    return _swap(src, _GOLD_PROOF, body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `referenceEnumMemberTester module className memberName payloadText
# ---- payloadImports = false` says the extracted program's result violates the
# ---- method's postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can mask the
# ---- verdict; every witness closes by `decide` over concrete literals.
def _tester(body):
    m = "referenceEnumMember"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the contract is point-wise equality over the pure
    # region, so the reproof stays a `loom_solve` away from the frozen script.
    # =====================================================================
    {
        "id": "pos-oracle-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest correct reshape: evaluate the pure spec functions directly
        # (they are closed-form concatenations of the inputs, NOT an opaque
        # answer key), so the result is exactly the post-image by definition.
        "module": _impl(
            "    let refString : List Char := memberReference module className memberName\n"
            "    let imports : List (List Char) := referenceImports module\n"
            "    return (refString, imports)"),
        "rationale": "the reference/import text spelled by evaluating the pure "
                     "`memberReference`/`referenceImports` (each a fully-unfolded "
                     "concatenation of the inputs) is `memberReference ...` / "
                     "`referenceImports ...` by definition, so P0/P1 discharge "
                     "under the frozen `loom_solve`; if a correct impl cannot "
                     "verify the post-image is SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reshaped-single-expression",
        "kind": "soundness",
        "expect": "verify",
        # The sibling's soundness positive: build the fragment in ONE whole-list
        # concatenation via a named quoted-name local, stage the import first,
        # and name the returned tuple. Observationally identical on every input;
        # each part is a whole-list `++` matching how the pure functions unfold,
        # so no induction lemma is needed.
        "module": _impl(
            "    let imports : List (List Char) := [\"import \".toList ++ module]\n"
            "    let quoted : List Char := ['\\''] ++ memberName ++ ['\\'']\n"
            "    let refString : List Char :=\n"
            "      module ++ ['.'] ++ className ++ ['['] ++ quoted ++ [']']\n"
            "    let out : (List Char) × (List (List Char)) := (refString, imports)\n"
            "    return out"),
        "rationale": "a reshaped-but-observationally-identical construction (named "
                     "quoted-name local, single whole-list concatenation, import "
                     "staged first, named tuple) computes the identical `out` on "
                     "every input and adds no proof obligation, so P0/P1 still "
                     "discharge under the frozen `loom_solve`; else "
                     "SPEC-TOO-STRONG on the impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — this surface HAS a precondition
    # (`∀ c ∈ memberName, isIdentChar c`), so the PRECOND-TOO-STRONG direction is
    # live and is tested directly rather than argued away: the case discharges,
    # BY EVALUATION at concrete F2P-shaped member names, that the precondition is
    # actually satisfiable there, AND that the post-image at those points is
    # non-degenerate. Both halves matter and both are separately falsifiable:
    #
    #   (a) `∀ c ∈ "GOOD"/"A"/"D0_x", isIdentChar c` — the require ADMITS the
    #       member names the operation is reached with (all-caps, single-letter,
    #       and a mixed letter/digit/underscore name). A require that excluded any
    #       of them would be PRECOND-TOO-STRONG: the spec would say nothing about
    #       the very inputs it exists to constrain, and every impl would pass
    #       vacuously there.
    #   (b) the post-image's VALUE at those points, plus one `≠` pinning that the
    #       demanded value is NOT the payload-keyed call form — so a post-image
    #       that had degenerated into something every impl meets cannot pass.
    #
    # The impl is kept verbatim so the method's own obligation still discharges.
    # Liveness of every conjunct family was measured, not assumed: perturbing the
    # precondition conjunct (an out-of-alphabet name), the reference value, the
    # import value, or the `≠` each leaves an unsolved goal and fails the build.
    # The proof tail adds `first | decide | simp_all [isIdentChar]`, which only
    # discharges the added assert (the frozen tail alone leaves the `isIdentChar`
    # goals open); the `prove_correct` header and every spec clause are untouched.
    # =====================================================================
    {
        "id": "admiss-reference-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof(_impl(
            "    assert (with_name_prefix `assert\n"
            "      ((∀ c ∈ \"GOOD\".toList, isIdentChar c) ∧\n"
            "       (∀ c ∈ \"A\".toList, isIdentChar c) ∧\n"
            "       (∀ c ∈ \"D0_x\".toList, isIdentChar c) ∧\n"
            "       memberReference \"m\".toList \"C\".toList \"A\".toList\n"
            "         = \"m.C['A']\".toList ∧\n"
            "       memberReference \"m\".toList \"Status\".toList \"GOOD\".toList\n"
            "         = \"m.Status['GOOD']\".toList ∧\n"
            "       referenceImports \"m\".toList = [\"import m\".toList] ∧\n"
            "       memberReference \"m\".toList \"Status\".toList \"GOOD\".toList\n"
            "         ≠ \"m.Status('Good')\".toList))\n"
            + _GOLD_IMPL),
            _GOLD_PROOF.rstrip("\n")
            + "\n  all_goals first | decide | simp_all [isIdentChar]\n"),
        "rationale": "PRECOND-TOO-STRONG probe, discharged by evaluation at "
                     "concrete inputs: the require `∀ c ∈ memberName, isIdentChar "
                     "c` ADMITS the F2P-shaped member names (`GOOD`, `A`, `D0_x` "
                     "— all-caps, single-letter, and mixed letter/digit/"
                     "underscore), so the spec is not vacuous at exactly the "
                     "inputs it constrains. It further pins that the post-image "
                     "at those points is non-degenerate: the reference is the "
                     "name-keyed subscript form (`m.Status['GOOD']`), the import "
                     "is the singleton (`import m`), and the demanded value is "
                     "NOT the payload-keyed call form. Every conjunct family is "
                     "live — perturbing the admitted name, the reference value, "
                     "the import value, or the `≠` each fails the build.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-payload-keyed-callform",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug. Build the reference from the mutable payload text in
        # CALL form `module.Class(payload)` instead of the stable symbolic name
        # in SUBSCRIPT form. Keyed on the wrong input entirely.
        "module": _impl(
            "    let refString : List Char :=\n"
            "      module ++ ['.'] ++ className ++ ['('] ++ payloadText ++ [')']\n"
            "    let imports : List (List Char) := [\"import \".toList ++ module]\n"
            "    return (refString, imports)"),
        "refinement": "the faithful real counterpart keys the reference on the "
                      "member's serialized VALUE in call form rather than its "
                      "stable NAME in subscript form — exactly the reported "
                      "regression. The failing tests assert the reference is the "
                      "name-keyed subscript form (e.g. the enum member is emitted "
                      "under its symbolic name, not its stored value); the "
                      "value-keyed call form still fails them, and additionally a "
                      "value that renders differently over time (a translated "
                      "string) makes the emitted reference unloadable. It would "
                      "NOT resolve.",
        "rationale": "REJECT from P0 `out.1 = memberReference module className "
                     "memberName`: the impl emits `module ++ '.' ++ className ++ "
                     "'(' ++ payloadText ++ ')'`, which differs from the required "
                     "name-keyed subscript form on TWO counts at once — the key "
                     "(`payloadText` rather than `memberName`) and the delimiters "
                     "(`(`/`)` rather than `[`/`]`, with the quotes dropped). "
                     "Refuted at `memberName=\"A\"`, `payloadText=\"v\"`. NOTE the "
                     "attribution limit, measured rather than assumed: because the "
                     "delimiters are wrong too, this rival is refuted at EVERY "
                     "input including one where `payloadText = memberName`, so its "
                     "rejection alone does NOT attest that the post-image is "
                     "independent of the payload. That claim is carried by "
                     "`weak-payload-keyed-subscript`, whose only defect is the "
                     "key.",
        "witness": _tester(
            "example : referenceEnumMemberTester \"a\".toList \"C\".toList "
            "\"A\".toList \"v\".toList [] = false := by\n  decide\n"),
    },
    {
        "id": "weak-payload-keyed-subscript",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Isolates the KEYING axis, which no shipped rival did:
        # the qualified type, the subscript brackets and the quoting are all
        # gold-correct, and the ONLY defect is that the quoted token is the
        # mutable payload instead of the stable symbolic name. Refuted exactly
        # where the two differ, and it AGREES with the frozen impl where they
        # coincide (measured: the refutation at `payloadText = memberName =
        # "GOOD"` does NOT hold) — so this rejection, unlike the call-form one,
        # attributes precisely to the post-image's independence from the payload.
        "module": _impl(
            "    let refString : List Char :=\n"
            "      module ++ ['.'] ++ className ++ ['['] ++ (['\\''] ++ payloadText ++ ['\\'']) ++ [']']\n"
            "    let imports : List (List Char) := [\"import \".toList ++ module]\n"
            "    return (refString, imports)"),
        "refinement": "the faithful real counterpart renders the subscript form "
                      "correctly but keys it on the member's serialized VALUE "
                      "rather than its stable NAME. The failing tests assert the "
                      "reference is keyed on the symbolic name, and a value-keyed "
                      "subscript is a different string whenever the two disagree "
                      "(the reported case: a name in one case and a display value "
                      "in another), so it still fails them. Worse, it reintroduces "
                      "the reported defect in full — the emitted reference is "
                      "pinned to a value that may be rendered differently later, "
                      "so an already-written reference stops resolving. It would "
                      "NOT resolve.",
        "rationale": "REJECT from P0 `out.1 = memberReference module className "
                     "memberName`: the emitted text is `module ++ '.' ++ className "
                     "++ '[' ++ '\\'' ++ payloadText ++ '\\'' ++ ']'`, which is the "
                     "required form with `payloadText` substituted for "
                     "`memberName` — every delimiter and both quotes are correct, "
                     "so the ONLY discrepancy is the key. It therefore differs "
                     "from the post-image exactly on the sub-domain `payloadText ≠ "
                     "memberName` and agrees on `payloadText = memberName`, which "
                     "is what makes this case (and not the call-form one) the "
                     "machine-checked evidence that the post-image is a function "
                     "of the symbolic name ALONE and never of the payload. "
                     "Refuted at `memberName=\"GOOD\"`, `payloadText=\"Good\"` — a "
                     "name/value pair that differs only in case, so the refutation "
                     "cannot be read off the length or shape of the two strings.",
        "witness": _tester(
            "example : referenceEnumMemberTester \"s\".toList \"G\".toList "
            "\"GOOD\".toList \"Good\".toList [] = false := by\n  decide\n"),
    },
    {
        "id": "weak-import-union-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The import-set rival the sibling's refinement argument
        # actually describes: the module import UNION the payload's own imports.
        # `weak-import-tamper` models this with a corrupted module path, which
        # never reads `payloadImports` at all — so before this case the battery
        # had no rival that touched that binder, and the "the payload's imports
        # must not reach the output" half of the frame claim was untested.
        # Refuted only where `payloadImports` is NONEMPTY (measured: at
        # `payloadImports = []` this rival agrees with the frozen impl and the
        # refutation does not hold), which is what makes the binder meaningful
        # rather than merely varied.
        "module": _impl(
            "    let refString : List Char :=\n"
            "      module ++ ['.'] ++ className ++ ['['] ++ (['\\''] ++ memberName ++ ['\\'']) ++ [']']\n"
            "    let imports : List (List Char) := [\"import \".toList ++ module] ++ payloadImports\n"
            "    return (refString, imports)"),
        "refinement": "this IS the faithful pre-fix import shape: the module "
                      "import together with the imports the payload's own "
                      "rendering would need. The failing tests compare the import "
                      "set exactly against the singleton module import, so any "
                      "input whose payload contributes an import fails them. It "
                      "would NOT resolve.",
        "rationale": "REJECT from P1 `out.2 = referenceImports module`: the impl "
                     "emits `[\"import \" ++ module] ++ payloadImports` where the "
                     "post-image demands the singleton `[\"import \" ++ module]`, "
                     "so it violates P1 on exactly the sub-domain `payloadImports "
                     "≠ []`. The reference text (out.1) is gold-correct, isolating "
                     "the failure to the import clause AND to the payload-imports "
                     "binder specifically — the residual goal the verifier leaves "
                     "is literally `payloadImports = []`. Refuted at "
                     "`module=\"d\"`, `className=\"F\"`, `memberName=\"D0\"` with "
                     "`payloadImports=[\"import t\"]` — a fourth distinct point, "
                     "and the only witness in the battery at which that binder is "
                     "load-bearing.",
        "witness": _tester(
            "example : referenceEnumMemberTester \"d\".toList \"F\".toList "
            "\"D0\".toList \"u\".toList [\"import t\".toList] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-wrong-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        # Correctly keyed on the symbolic name BUT emits the subscription with
        # PARENTHESES instead of BRACKETS: module.Class('NAME') in call form.
        # A near-miss that agrees with the name-keyed form on the identifier
        # substring but diverges at the delimiter positions for every input.
        "module": _impl(
            "    let refString : List Char :=\n"
            "      module ++ ['.'] ++ className ++ ['('] ++ (['\\''] ++ memberName ++ ['\\'']) ++ [')']\n"
            "    let imports : List (List Char) := [\"import \".toList ++ module]\n"
            "    return (refString, imports)"),
        "refinement": "a counterpart that keys on the symbolic name but wraps it "
                      "in call-form parentheses instead of subscript brackets "
                      "renders `module.Class('NAME')` — still not the "
                      "`module.Class['NAME']` subscript form the failing tests "
                      "assert verbatim, and after loading it re-invokes the enum "
                      "by a string that is not one of its values. The tests "
                      "compare the rendered reference exactly, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from P0: the impl emits `(`/`)` where "
                     "`memberReference` requires the subscript `[`/`]`, so "
                     "`out.1 ≠ memberReference ...` for EVERY input (P0 pins the "
                     "WHOLE sequence including the delimiters, not just the "
                     "identifier substring). Refuted at `module=\"m\"`, "
                     "`className=\"D\"`, `memberName=\"B\"` — a distinct point "
                     "varying all three name binders.",
        "witness": _tester(
            "example : referenceEnumMemberTester \"m\".toList \"D\".toList "
            "\"B\".toList \"w\".toList [\"p\".toList] = false := by\n  decide\n"),
    },
    {
        "id": "weak-qualifier-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY THIS AUDIT. Isolates the QUALIFIER-ORDER axis, which no shipped
        # rival touched: the key is gold-correct (the symbolic name), the subscript
        # brackets and both quotes are gold-correct, the import line is
        # gold-correct, and BOTH qualifier binders are present — only their ORDER
        # in the reference is exchanged. Before this case every rival left the two
        # qualifiers in their given order, so nothing attested that P0 pins WHICH
        # of the two leads the dotted prefix; a spec that had only pinned "the
        # reference contains both qualifiers, a dot, and the quoted name" would
        # have accepted this rival. AXIS-ISOLATING: it agrees with the frozen impl
        # on the whole sub-domain `module = className` and is refutable only where
        # the two differ (measured: at `module = className = "Q"` the refutation
        # does NOT hold, exit 1).
        "module": _impl(
            "    let refString : List Char :=\n"
            "      className ++ ['.'] ++ module ++ ['['] ++ (['\\''] ++ memberName ++ ['\\'']) ++ [']']\n"
            "    let imports : List (List Char) := [\"import \".toList ++ module]\n"
            "    return (refString, imports)"),
        "refinement": "the faithful real counterpart renders the qualified type with "
                      "its two components transposed — the type's own name where the "
                      "defining module belongs and vice versa. The failing tests "
                      "compare the rendered reference exactly, and a transposed "
                      "qualifier is a different string for every type whose module "
                      "and name differ (which is every realistic one), so it fails "
                      "them. The emitted reference also does not resolve after "
                      "loading, since the dotted prefix no longer names a real "
                      "module path. It would NOT resolve.",
        "rationale": "REJECT from P0 `out.1 = memberReference module className "
                     "memberName`: the post-image pins the qualified type as "
                     "`module ++ '.' ++ className` — the defining module FIRST, "
                     "then the type name — and the impl emits `className ++ '.' ++ "
                     "module`. Every other component (the name key, both quotes, "
                     "the subscript brackets, the import line) is gold-correct, so "
                     "the ONLY discrepancy is the order of the two qualifier "
                     "binders. It therefore differs from the post-image exactly on "
                     "the sub-domain `module ≠ className` and agrees on "
                     "`module = className`, which is what makes this case the "
                     "machine-checked evidence that P0 pins the qualifier ORDER and "
                     "not merely the presence of both parts. Refuted at "
                     "`module=\"p\"`, `className=\"Q\"`, `memberName=\"E1\"` — a "
                     "sixth distinct point, and the only witness at which the "
                     "relative order of the two qualifier binders is load-bearing.",
        "witness": _tester(
            "example : referenceEnumMemberTester \"p\".toList \"Q\".toList "
            "\"E1\".toList \"r\".toList [\"import s\".toList] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-import-tamper",
        "kind": "uniqueness",
        "expect": "reject",
        # The reference text is gold-correct; only the import line is wrong: a
        # stray trailing code point on the module path, so the emitted import is
        # not the singleton `import module`. Isolates the failure to P1.
        "module": _impl(
            "    let refString : List Char :=\n"
            "      module ++ ['.'] ++ className ++ ['['] ++ (['\\''] ++ memberName ++ ['\\'']) ++ [']']\n"
            "    let imports : List (List Char) := [\"import \".toList ++ module ++ ['x']]\n"
            "    return (refString, imports)"),
        "refinement": "a counterpart that emits a module import which is not the "
                      "enumeration's own defining module — a corrupted or "
                      "mis-derived module path — emits an import that does not "
                      "make the reference loadable. The failing tests compare the "
                      "import set exactly against the singleton module import, so "
                      "it does NOT resolve. (The DIFFERENT pre-fix defect of "
                      "unioning the payload's own imports into the set is not this "
                      "case — it is `weak-import-union-payload`, which models it "
                      "directly rather than by analogy.)",
        "rationale": "REJECT from P1 `out.2 = referenceImports module`: the impl "
                     "emits `[\"import \" ++ module ++ \"x\"]` where the "
                     "post-image demands `[\"import \" ++ module]`, so it violates "
                     "P1 for EVERY input (the corruption is unconditional, unlike "
                     "the payload-union rival's `payloadImports ≠ []` sub-domain). "
                     "The reference text (out.1) is gold-correct, isolating the "
                     "failure to the import clause. Refuted at `module=\"z\"`, "
                     "`className=\"E\"`, `memberName=\"C\"` — a third distinct "
                     "point.",
        "witness": _tester(
            "example : referenceEnumMemberTester \"z\".toList \"E\".toList "
            "\"C\".toList \"q\".toList [] = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals). This bundle models only the
# purely-functional core — a single method `referenceEnumMember` — where the
# sibling contracts one function over a permission-bearing, total-correctness
# surface. The value surface carries across intact; the permission and
# termination surfaces do not exist here. Every sibling case is accounted for.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-single-expression         -> pos-reshaped-single-expression PORTED
#                                            (+ pos-oracle-direct ADDED)
#   admissibility-four-readonly-inputs     -> admiss-reference-nondegenerate RE-AIMED
#   frame-mutation-write-payload           -> (none)                    VACUOUS
#   payload-keyed-prepatch-bug             -> weak-payload-keyed-callform PORTED
#                                            + weak-payload-keyed-subscript ADDED
#   partial-domain-wrong-delimiter         -> weak-wrong-delimiter       PORTED
#   nontermination-diverge-before-return   -> (none)   NOT PORTABLE (witness-path
#                                            tooling limit; the spec REJECTS it)
#   import-tamper-extra-codepoint          -> weak-import-tamper         PORTED
#                                            + weak-import-union-payload ADDED
#   (no sibling analogue)                  -> weak-qualifier-swapped     ADDED
#
# 3 ported, 1 re-aimed, 1 vacuous, 1 not-portable-for-tooling; 1 positive control
# and 3 uniqueness rivals added (all four by the adversarial audits — see AUDIT).
#
# VACUOUS (frame-mutation-write-payload): the sibling's mandatory frame-mutation
#   rival writes to a read-only input held at a fractional heap permission, and
#   is rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, this bundle declares no
#   `mut` binder, there is no heap and no aliasing. There is no read-only input
#   to overwrite and no permission system to trip, so the class is vacuous. No
#   substitute is fabricated (per the porting map, this class is legitimately
#   dropped rather than replaced). DEMONSTRATED, not asserted: an in-region
#   variant that rebinds `payloadText`/`payloadImports` to modified values ahead
#   of the (verbatim) gold construction VERIFIES — there is no frame obligation
#   for such a write to violate, because the rebinding is a new immutable local
#   and cannot be observed by the caller. The "payload must not leak" obligation
#   the sibling attaches to the permission surface is instead defended on the
#   VALUE surface here, and on both of its axes: weak-payload-keyed-subscript
#   (the payload reaching the reference TEXT) and weak-import-union-payload (the
#   payload's imports reaching the IMPORT SET).
# NOT PORTABLE — witness-path tooling limit, NOT a spec hole and NOT vacuous
#   (nontermination-diverge-before-return): the sibling regresses a
#   total-correctness (`MustTerminate`) obligation. This bundle runs under
#   `loom.semantics.termination "total"`, so the analogous obligation IS
#   discharged here and the spec genuinely REJECTS a diverging rival — measured,
#   not argued: an impl that prefixes gold's body with `while true do i := i + 1`
#   fails with `error: Decreasing annotations are required in total correctness
#   semantics` (exit 1), and so does the sharper variant that diverges and then
#   returns the unambiguously wrong `([], [])`. So the earlier
#   `partial`-semantics note (a diverging impl verifies vacuously, escalated
#   corpus-wide) does NOT describe this carrier: this bundle is `total`, as all
#   500 velvet bundles are, and it rejects the probe.
#
#   The class is still not shippable as `expect="reject"`, but for a TOOLING
#   reason on the WITNESS path rather than for anything about the spec. A reject
#   case must carry a witness that ELABORATES against the rival; the termination
#   error fires while elaborating the `method` body itself, which is upstream of
#   the witness and is not removed by the obligation-stripping the witness build
#   performs. Measured against the diverging rival: a witness file whose only
#   claim is `example : 1 + 1 = 2 := by decide` fails with that same termination
#   error (exit 1), as does one that merely derives the tester and claims nothing.
#   So the rival-side half is unreachable for EVERY claim, and the gate would
#   record `witness-unproven` — an inconclusive outcome — for a rival the spec
#   actually refuses. A `witness_reference` cannot repair it either: that
#   substitutes the GOLD-side subject, whereas the blocked build here is the
#   rival's. Recorded as a bug on the witness path with the error text above,
#   per the audit protocol's "a rival the port could not land for a TOOLING
#   reason is a bug to report".
# RE-AIMED (admissibility): the sibling's case Asserts the four half-permission
#   inputs are readable and reaches a normal return. There is no permission
#   surface here, so that exact reading is vacuous — but this surface DOES carry a
#   precondition (`∀ c ∈ memberName, isIdentChar c`), so the PRECOND-TOO-STRONG
#   direction is live and is tested rather than argued away. The case now
#   discharges, by evaluation at concrete F2P-shaped member names, both that the
#   require ADMITS them (the analogue of "the four inputs are usable": the spec is
#   not vacuous at the inputs it exists to constrain) and that the post-image
#   there is non-degenerate. Every conjunct family is separately falsifiable —
#   measured, see AUDIT.
# ADDED (1): pos-oracle-direct — a second, structurally-different correct impl
#   (evaluate the pure spec functions directly), so the soundness surface is
#   defended by two distinct reshapes. This is the sibling's honest
#   "echo-grounded-oracle" positive control re-expressed: the pure functions are
#   closed-form concatenations of the inputs, not an opaque answer key, so
#   evaluating them IS the correct computation.
#
# BINDER / CLAUSE COVERAGE. The two load-bearing clauses are attacked by six
#   rivals at six DISTINCT input points:
#     P0 (reference text) : weak-payload-keyed-callform (wrong key AND wrong
#                             delimiters — the pre-fix shape, wrong everywhere),
#                           weak-payload-keyed-subscript (ONLY the key wrong),
#                           weak-wrong-delimiter (ONLY the delimiters wrong),
#                           weak-qualifier-swapped (ONLY the qualifier ORDER
#                             wrong, wrong iff `module ≠ className`);
#     P1 (import set)     : weak-import-tamper (module path corrupted, wrong
#                             everywhere),
#                           weak-import-union-payload (ONLY the payload's imports
#                             added, wrong iff `payloadImports ≠ []`).
#   The three binders the spec predicates read are varied across the witnesses:
#   `module` over "a"/"s"/"d"/"m"/"p"/"z", `className` over "C"/"G"/"F"/"D"/"Q"/"E",
#   `memberName` over "A"/"GOOD"/"D0"/"B"/"E1"/"C"; and the read-only payload
#   inputs `payloadText` ("v"/"Good"/"u"/"w"/"r"/"q") and `payloadImports`
#   ([]/[]/["import t"]/["p"]/["import s"]/[]) too.
#
#   The variation is MEANINGFUL, not two spellings of one point — each of the
#   THREE axis-isolating rivals agrees with the frozen impl off its sub-domain, so
#   its witness point is the thing carrying the claim:
#     * weak-payload-keyed-subscript is refuted at `memberName="GOOD"`,
#       `payloadText="Good"` and NOT at `payloadText = memberName` — so it, alone,
#       attests that the post-image is a function of the symbolic name and not of
#       the payload.
#     * weak-import-union-payload is refuted at `payloadImports=["import t"]` and
#       NOT at `payloadImports=[]` — so it, alone, makes that binder load-bearing.
#     * weak-qualifier-swapped is refuted at `module="p"`, `className="Q"` and NOT
#       at `module = className` — so it, alone, attests that P0 pins the ORDER of
#       the two qualifier binders and not merely that both appear.
#   All three non-refutations were measured, not assumed (exit 1 at the agreement
#   point in each case).
#
# WITNESS DISTINCTNESS. The four P0 rivals diverge for four different reasons,
#   and the split matters for attribution: the call-form rival is wrong on the key
#   AND the delimiters, so it is refuted even where payload and name coincide and
#   its rejection cannot be read as evidence about the key (measured: it is refuted
#   at `payloadText = memberName = "GOOD"`, exit 0). The three isolating rivals
#   each pin exactly one axis — the key, the delimiters, the qualifier order.
#   Likewise on P1: one rival is unconditionally wrong, the other wrong only on the
#   payload-imports sub-domain.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   axiom and no A-reference deep model (the reference construction is modeled
#   deeply in the pure region), and this gate ignores AXIOM_TESTS regardless.
#
# ---------------------------------------------------------------------------
# AUDIT (independent adversarial re-derivation of a recorded SOUND). Every claim
# below is an exit code from a real `lean_verify.sh` build, not an argument.
#
# CONFIRMED EARNED
#   * Statement integrity: every case's variant differs from the frozen file ONLY
#     inside the impl region (and, for the admissibility case, the `prove_correct`
#     tactic body). No `ensures`, no `require`, no `pure` def, and no obligation
#     header is reformatted anywhere.
#   * All three original witnesses rebuilt by hand: each ELABORATES against its
#     rival (exit 0) and FAILS against the frozen solution (exit 1), and gold's
#     error is in every case the plain evaluation "Tactic `decide` proved that the
#     proposition ... = false is false".
#   * FORGERY TEST (mandatory two-line experiment) on all five reject cases:
#     flipping the claim from `= false` to `= true` SWAPS both exit codes — the
#     forged claim verifies against gold (0) and fails against the rival (1). So
#     gold's exit code tracks the claim rather than erroring around it; none of
#     these rejections is hollow.
#   * SPEC-TOO-WEAK probe (8 NEW wrong impls the battery did not contain): the
#     payload-imports union, an unquoted name, a name quoted with `"` instead of
#     `'`, module/class qualifier swapped, importing the class rather than the
#     module, a sub-domain rival wrong only at the empty name, and both rivals
#     added above. ALL rejected, each leaving a concrete semantic residual goal
#     (e.g. `payloadImports = []`, `memberName = [] → payloadText = ...`). No spec
#     hole found on the value surface.
#   * SPEC-TOO-STRONG probe (4 NEW correct reshapes): a right-associated `++`
#     chain, a two-halves split through the pure `quotedName`, construction routed
#     through the `String` carrier and back via `.toList`, and the import built
#     with `List.cons` over an explicit char list. ALL verify. The spec does not
#     over-constrain the impl's shape.
#   * The declared domain is honest, not a dodge: an impl that returns `[]` for a
#     name outside the identifier alphabet still verifies, which is exactly what
#     the `require` says it may do. That is the scoping recorded in mapping.md,
#     not an unclaimed hole.
#
# REPAIRED (four defects found, all in the manifest — the frozen spec is intact)
#   1. The admissibility case was aimed only at post-image non-degeneracy and
#      never at the precondition, even though this surface HAS one. It now
#      discharges precondition satisfiability at concrete F2P-shaped names as
#      well, so the PRECOND-TOO-STRONG direction is actually tested. (The frozen
#      proof tail leaves those `isIdentChar` goals open; the case extends the
#      tactic body, which the spec view elides, and every conjunct family was
#      checked to be independently falsifiable.)
#   2. `weak-payload-keyed-callform`'s rationale claimed its rejection made the
#      post-image's independence from the payload observable. It does not: the
#      rival's delimiters are wrong too, and it is refuted even at
#      `payloadText = memberName` (measured). The claim is corrected in place and
#      the property is now carried by the added `weak-payload-keyed-subscript`,
#      which is wrong ONLY in the key.
#   3. `weak-import-tamper`'s refinement described the payload-imports union while
#      the impl models a corrupted module path — a claim the case never
#      demonstrated, and no rival read `payloadImports` at all. The refinement is
#      corrected and `weak-import-union-payload` now models the union directly.
#   4. The nontermination omission was recorded as "vacuous / inexpressible" on
#      the ground that a diverging impl does not violate the spec, and a later
#      revision re-labelled it a `partial`-semantics hole on the ground that such
#      an impl VERIFIES. Both are withdrawn: this bundle is `total` and the
#      diverging rival is REJECTED (see the entry above), so the class is closed
#      by the semantics and unshippable only on the witness path.
#
# The frame-mutation omission was re-derived rather than accepted on argument: an
# in-region variant that rebinds both read-only payload inputs VERIFIES, so there
# is genuinely no frame obligation on this carrier for such a write to violate.
# Verdict stands as VACUOUS, now demonstrated.
#
# ---------------------------------------------------------------------------
# AUDIT 2 (second independent adversarial pass, wave d1). 46 real builds; every
# claim below is an exit code observed, not an argument.
#
# CONFIRMED EARNED (re-derived from scratch, not taken from AUDIT 1)
#   * Statement integrity re-checked by diffing all 8 generated variants against
#     the frozen file: every hunk lies inside the impl region, plus the
#     admissibility case's one added `prove_correct` tail line. No `ensures`, no
#     `require`, no `pure` def, no obligation header touched.
#   * All FIVE original witnesses rebuilt: each elaborates against its rival
#     (exit 0) and fails against the frozen solution (exit 1). Every gold-side
#     error is the plain evaluation `Tactic `decide` proved that the proposition
#     ... = false is false` — no stuck reduction, no missing `Decidable`, no
#     unification failure, so none matches the gate's stuck screens.
#   * FORGERY TEST re-run on all five (10 further builds): flipping `= false` to
#     `= true` swaps BOTH exit codes in every case (gold 0, rival 1). Gold's exit
#     code therefore carries information about the claim; no case is hollow.
#   * AGREEMENT-POINT probes (attack C, is the rival wrong or just different):
#     all three axis-isolating rivals verified as genuinely sub-domain rivals —
#     `weak-payload-keyed-subscript` at `payloadText = memberName = "GOOD"` and
#     `weak-import-union-payload` at `payloadImports = []` both fail to refute
#     (exit 1), while `weak-payload-keyed-callform` DOES refute at
#     `payloadText = memberName` (exit 0), confirming its documented attribution
#     limit. No rival is observably identical to gold; no case is vacuous.
#   * ADMISSIBILITY conjunct liveness re-measured (5 builds): the case as shipped
#     verifies (exit 0), and four separate perturbations each FAIL (exit 1) — an
#     out-of-alphabet name in the precondition conjunct, a corrupted reference
#     value, a corrupted import value, and flipping the `≠` to `=`. Every
#     conjunct family is load-bearing; the positive is not passing vacuously.
#   * SPEC-TOO-WEAK probe, 16 NEW wrong impls beyond AUDIT 1's set, aimed at the
#     two UNCONSTRAINED binders (`module`/`className` carry no `require`) since
#     coverage showed them least probed: qualifier order swapped, name quoted with
#     `"`, name unquoted, attribute form `module.Class.NAME`, a trailing space,
#     importing the class as well, importing without the `import ` prefix, an
#     empty import list, a duplicated import, and six SUB-DOMAIN rivals that are
#     gold everywhere except at `memberName = []`, `payloadText = []`,
#     `module = []`, `className = []`, `module` containing a dot, and
#     `memberName.length > 8`. ALL 16 REJECTED, each leaving a concrete semantic
#     residual goal (`¬memberName = []`, `¬payloadText = [] → payloadText =
#     memberName`, `False`, and the two transposed concatenations printed in
#     full). No spec hole on the value surface, including on the unconstrained
#     binders.
#   * SPEC-TOO-STRONG probe, 6 NEW correct reshapes: a fully right-associated `++`
#     chain, `List.flatten` over the eight fragments, routing through the pure
#     `quotedName`, the import via `List.cons`, a `String`-carrier round trip via
#     `.toList`, and a head/tail two-`let` split. ALL 6 VERIFY (exit 0). The spec
#     does not over-constrain the impl's shape.
#   * The declared-domain scoping is honest AND its boundary was probed: an impl
#     that returns `[]` for a name outside the identifier alphabet verifies (exit
#     0) — exactly what the `require` permits. A sharper reshape that branches on
#     `memberName.contains '\''` does NOT close under the frozen tail (residual
#     goal `'\'' ∉ memberName`), but that is a TACTIC gap, not a spec hole: the
#     goal follows from the `require`, and extending the tail with
#     `intro hc; have := require_1 _ hc; simp [isIdentChar] at this` closes it
#     (exit 0, measured two ways). Not reported as SPEC-TOO-STRONG for that
#     reason.
#
# REPAIRED BY THIS PASS (two defects, both in the manifest — frozen spec intact)
#   5. STALE SEMANTICS CLAIM, the load-bearing one. The frozen solution carries
#      `set_option loom.semantics.termination "total"`, but the header and footer
#      both argued the nontermination class from `"partial"` and recorded it as an
#      already-escalated corpus-wide hole. Under `total` the opposite disposition
#      holds and was measured: the diverging rival is REJECTED, with `error:
#      Decreasing annotations are required in total correctness semantics` (exit
#      1), both with gold's body after the loop and with a wrong `([], [])` return
#      after it. So the spec is not weak here and the prose was describing a
#      carrier this bundle no longer uses.
#      Per attack F′ that would make the class UNDERPORTED and shippable — so it
#      was attempted rather than re-labelled from theory. It is NOT landable, for
#      a witness-path tooling reason, measured with two further builds: the
#      termination error fires while elaborating the `method` body, upstream of
#      the witness and not removed by the obligation-stripping, so against the
#      diverging rival even a witness file whose only claim is `1 + 1 = 2` fails
#      with that same error (exit 1). The rival-side half of the witness contract
#      is unreachable for every claim, and a `witness_reference` cannot help
#      because it substitutes the GOLD-side subject. Re-recorded as a tooling
#      limitation with the error text, not as a spec hole and not as a vacuous
#      class.
#   6. QUALIFIER-ORDER AXIS UNATTACKED. Coverage plus a read of all five rivals
#      showed that every one of them left `module` and `className` in their given
#      order, so nothing in the battery attested that P0 pins WHICH qualifier
#      leads the dotted prefix — a spec pinning only "both qualifiers, a dot and
#      the quoted name are present" would have passed the whole battery. Landed
#      `weak-qualifier-swapped` (exchange the two, everything else gold-correct)
#      with the full evidence set: witness elaborates on the rival (exit 0), fails
#      on gold (exit 1) with a plain-evaluation signature, forgery swaps both exit
#      codes (gold 0 / rival 1), and the agreement point `module = className = "Q"`
#      does NOT refute (exit 1), so the case is genuinely axis-isolating.
AXIOM_TESTS = []
