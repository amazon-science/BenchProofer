"""properties.py — G-PBT falsification battery for pydata__xarray-4966 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models one procedure over a half-permission input list with fractional-permission
contracts and a backward accumulator loop; this Lean bundle models the SAME
purely-functional decision as a single total function over the observable inputs
(the array values, the element kind, the byte width, the fill value, the
attribute) returning the touched output components. The nagini rivals therefore
carry over as attacks on the corresponding clause of the one modeled obligation;
the mapping of each nagini case to its Lean counterpart (or its principled
omission) is in the module ``assessment`` in the structured return.

DEFENDED SURFACE (one modeled behavior). The result equals a single grounded
decision over the inputs: when the attribute is absent the input passes through;
when the array's element kind is signed and the attribute is the true-string the
values, kind and fill are read back with the same-width unsigned reinterpretation;
when the element kind is unsigned and the attribute is the false-string they are
read back with the same-width signed (two's-complement) reinterpretation; every
other combination (non-matching attribute value, or the residual element kind)
passes through unchanged, and the byte width is always preserved. The independent
top-level clauses selected by the input:

  * the no-attribute passthrough;
  * the signed-kind + true-string unsigned reinterpretation;
  * the signed-kind + non-true passthrough;
  * the unsigned-kind + false-string signed reinterpretation (the CHANGED clause);
  * the unsigned-kind + non-false passthrough;
  * the residual-kind passthrough.

BEHAVIOURAL DISCRIMINATOR (the fix). An array whose element kind is unsigned,
carrying the false-string attribute, must be read back as the signed integer of
the same byte width (the F2P witness: the unsigned maximum decodes to -1, e.g. an
8-bit 255 -> -1). Before the fix this combination had no branch and fell through
to the residual passthrough arm, so such an array was returned unchanged (still
the unsigned bit pattern). The CHANGED clause pins that signed reinterpretation;
the partial-domain rivals below ARE that pre-fix / boundary-wrong behaviour.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (write
    into the read-only input list) has no expressible instance here; no substitute
    is fabricated. (nagini case 3, frame-mutation-write-data.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs via exact integer
    arithmetic (the reinterpretation is modeled deeply, not axiomatized). There is
    no opaque answer key an implementation could echo, and no ``opaque`` callee to
    condition on — every witness below discharges by ``decide`` on concrete
    literals. In its place the battery carries honest positive controls.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: the pre-fix passthrough collapse; the wrong
    reinterpretation direction; a boundary off-by-one at the sign bit; a leading
    element left unfolded; the fill value left unmapped; the output kind left
    unflipped; the reported byte width narrowed; the existing signed direction
    collapsed; and the load-bearing passthrough clauses (no-attribute,
    non-matching value on BOTH the unsigned-kind and the signed-kind side,
    residual kind).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it by ``decide``. Each was checked to HOLD of its
rival and to FAIL on the frozen solution, so it discriminates rather than
asserting a tautology. The carrier is fully computable (exact ``Int`` arithmetic
on small literals), so no witness needs to condition on an opaque term.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one convenient point: ``kind`` takes signed, unsigned
and other; ``unsignedAttr`` takes none, the true-string, the false-string and a
non-matching value (on both the unsigned-kind and the signed-kind side);
``itemsize`` takes 1 and 2; ``fill`` takes none and some; and ``data`` ranges over
the sign-bit boundary value, the 8- and 16-bit unsigned maxima, a multi-element
list, and small values. No two rivals share a refutation point.

CLAUSE COVERAGE (audit). Each of the six top-level clauses listed above now has at
least one single-fault rival, and each sub-obligation of the CHANGED clause (the
values, the fill value, the element kind, the byte width) has one that is wrong in
that component ALONE — so a rejection localizes to the component named rather than
to the branch as a whole.

AXIOM lane: EMPTY here. The reinterpretation the routine performs is modeled
DEEPLY as exact integer arithmetic, so the bundle consumes no ``axiom`` and
declares no ``opaque`` callee. The nagini ``AXIOM_TESTS`` (also empty there) are
dropped — the axiom lane is G-AX's job.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4966"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. The whole impl def is the impl-region anchor; the whole proof
# body is the proof-region anchor. Both lie ENTIRELY inside their region (and are
# unique in the file, verified at load), so same_spec stays byte-identical and
# the theorem STATEMENT is untouched.
# ---------------------------------------------------------------------------
_IMPL_GOLD = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: implementation_unsignedDecode body not verbatim"

_PROOF_GOLD = """  intro inp
  unfold problem_spec_unsignedDecode implementation_unsignedDecode decodeModel
  simp only [Id.run, bind, pure]
  cases hu : inp.unsignedAttr with
  | none => rfl
  | some u =>
    cases hk : inp.kind with
    | signed => by_cases h : u = "true" <;> simp [h]
    | unsigned => by_cases h : u = "false" <;> simp [h]
    | other => rfl"""

assert _PROOF_GOLD in _BASE, "proof anchor drift: correct_unsignedDecode body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Reorder the two reinterpreting arms: test the unsigned-kind branch FIRST, then
# the signed-kind branch. The two element kinds are mutually exclusive, so the
# reorder is observationally identical on every input; each arm's body is kept
# verbatim. The frozen proof closes unchanged (it splits on the same two kinds).
# If a faithful correct impl could NOT verify => SPEC-TOO-STRONG. Ports nagini
# case 1 (pos-control-branch-reorder).
# ===========================================================================
_IMPL_POS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      else if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""


# ===========================================================================
# (2) ADMISSIBILITY — the obligation is SATISFIABLE at the F2P-shaped input
# (verify). The frozen theorem carries NO precondition hypothesis (the modeled
# behavior is total), so the nagini precondition-admission probe has no binder to
# attack; the honest analogue discharges the spec predicate by `decide` at a
# ground F2P input (unsigned kind, false-string, the unsigned maximum) as a
# `have`, then closes the frozen obligation verbatim. Verifies (else the modeled
# behavior is unsatisfiable at exactly the input the F2P exercises — the analogue
# of PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, the theorem
# statement is byte-identical, the ground instance sits inside the tactic body.
# Ports nagini case 2 (admissibility-readonly-data).
# ===========================================================================
_PROOF_ADMISS = """  have _ground : problem_spec_unsignedDecode
      { data := [255], kind := Kind.unsigned, itemsize := 1, fill := some 255, unsignedAttr := some "false" }
      { data := [-1], kind := Kind.signed, itemsize := 1, fill := some (-1) } := by
    unfold problem_spec_unsignedDecode decodeModel
    decide
  have _ground_impl : implementation_unsignedDecode
      { data := [255], kind := Kind.unsigned, itemsize := 1, fill := some 255, unsignedAttr := some "false" }
      = { data := [-1], kind := Kind.signed, itemsize := 1, fill := some (-1) } := by
    unfold implementation_unsignedDecode
    simp only [Id.run, bind, pure]
    decide
  intro inp
  unfold problem_spec_unsignedDecode implementation_unsignedDecode decodeModel
  simp only [Id.run, bind, pure]
  cases hu : inp.unsignedAttr with
  | none => rfl
  | some u =>
    cases hk : inp.kind with
    | signed => by_cases h : u = "true" <;> simp [h]
    | unsigned => by_cases h : u = "false" <;> simp [h]
    | other => rfl"""


# ---------------------------------------------------------------------------
# Rival impls (each a full impl-region body). Every rival keeps the theorem
# STATEMENT and the frozen proof body verbatim — the proof will not close, so the
# case is scored by its witness, not by build breakage.
# ---------------------------------------------------------------------------

# (3) PRE-FIX PASSTHROUGH COLLAPSE — drop the unsigned-kind branch entirely, so an
# unsigned array with the false-string is returned UNCHANGED (the pre-fix miss).
_IMPL_PREPATCH = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (4) DIRECTION SWAP — in the unsigned-kind branch, read the values back with the
# UNSIGNED reinterpretation (a no-op modulo width) instead of the signed one.
_IMPL_DIRSWAP = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (5) BOUNDARY OFF-BY-ONE — signed reinterpretation with a STRICT `>` sign-bit test
# instead of the gold `≥`, so the exact boundary value (top bit set, remainder ==
# half the modulus) is left unfolded.
_IMPL_BOUNDARY = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (fun x => let m : Int := (2:Int)^bits; let r := x % m; if 2 * r > m then r - m else r)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (6) FIRST-ELEMENT PASSTHROUGH — fold every value except the leading one, which
# is pushed unchanged.
_IMPL_FIRSTELT = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := (match data with | [] => [] | x :: xs => x :: xs.map (reinterpAsSigned bits))
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (7) FILL LEFT UNMAPPED — reinterpret the array values and flip the kind, but
# leave the fill value untouched.
_IMPL_FILLMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (8) OUTPUT KIND NOT FLIPPED — reinterpret the values and fill, but leave the
# reported element kind at its input (unsigned).
_IMPL_KINDMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (9) EXISTING DIRECTION COLLAPSED — the signed-kind + true-string branch flips
# the kind but leaves the values (and fill) unreinterpreted (a passthrough of the
# PASS_TO_PASS direction).
_IMPL_SIGNEDMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          kind := Kind.unsigned
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (10) NO-ATTRIBUTE PASSTHROUGH BROKEN — flip the reported kind when the attribute
# is absent, instead of passing the input through unchanged.
_IMPL_NONEMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := Kind.signed, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (11) NON-MATCHING VALUE GUARD DROPPED — the unsigned-kind branch fires for ANY
# attribute value, not just the false-string, so a non-matching value that should
# pass through is reinterpreted.
_IMPL_GUARDMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        let bits := 8 * inp.itemsize
        data := data.map (reinterpAsSigned bits)
        kind := Kind.signed
        fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""

# (12) RESIDUAL-KIND PASSTHROUGH BROKEN — the reinterpreting branch fires for the
# residual element kind too (guard weakened from unsigned to not-signed), so an
# array whose kind is neither signed nor unsigned is wrongly transformed.
_IMPL_OTHERMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""


# (13) BYTE WIDTH CLOBBERED — the values and the element kind are reinterpreted
# CORRECTLY, but the reported byte width is narrowed to 1 in the reinterpreting
# branch. A single-fault attack on the width-preservation clause, which no other
# rival in this battery touches (added by audit).
_IMPL_WIDTHMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  let mut isize := inp.itemsize
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := isize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        if u = "true" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsUnsigned bits)
          kind := Kind.unsigned
          fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
          isize := 1
      return { data := data, kind := kind, itemsize := isize, fill := fill }"""

# (14) SIGNED-KIND GUARD DROPPED — the signed-kind branch fires for ANY attribute
# value, not just the true-string, so a signed array carrying a non-matching value
# (which must pass through) is reinterpreted and its kind flipped. A single-fault
# attack on the signed-kind + non-true passthrough clause, which no other rival in
# this battery touches (added by audit; its unsigned-kind mirror is case 11).
_IMPL_SIGNEDGUARDMISS = """def implementation_unsignedDecode (inp : DecodeInput) : DecodeResult := Id.run do
  let mut data := inp.data
  let mut kind := inp.kind
  let mut fill := inp.fill
  match inp.unsignedAttr with
  | none =>
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }
  | some u =>
      if kind = Kind.signed then
        let bits := 8 * inp.itemsize
        data := data.map (reinterpAsUnsigned bits)
        kind := Kind.unsigned
        fill := fill.map (reinterpAsUnsigned bits)
      else if kind = Kind.unsigned then
        if u = "false" then
          let bits := 8 * inp.itemsize
          data := data.map (reinterpAsSigned bits)
          kind := Kind.signed
          fill := fill.map (reinterpAsSigned bits)
      return { data := data, kind := kind, itemsize := inp.itemsize, fill := fill }"""


def _witness(data, kind, itemsize, fill, attr):
    inp = ("{ data := %s, kind := %s, itemsize := %s, fill := %s, unsignedAttr := %s }"
           % (data, kind, itemsize, fill, attr))
    return (
        "example : ¬ problem_spec_unsignedDecode\n"
        "    " + inp + "\n"
        "    (implementation_unsignedDecode\n"
        "      " + inp + ") := by\n"
        "  unfold problem_spec_unsignedDecode implementation_unsignedDecode decodeModel\n"
        "  simp only [Id.run, bind, pure]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS
    # =====================================================================
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the two reinterpreting "
                     "arms are reordered (unsigned-kind branch tested first, then "
                     "signed-kind). The two element kinds are mutually exclusive, so "
                     "the reorder is observationally identical on every input; each "
                     "arm's body is kept verbatim and no helper lemma / axiom is "
                     "introduced. Must verify (the frozen proof splits on the same "
                     "two kinds and closes), else the modeled decision is "
                     "SPEC-TOO-STRONG. Ports nagini's branch-reorder positive.",
    },
    {
        "id": "admissibility-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _PROOF_ADMISS),
        "rationale": "Pins the ground F2P ANSWER, not merely satisfiability: two "
                     "`have`s discharge by `decide` that at the F2P-shaped input "
                     "(unsigned kind, false-string attribute, 8-bit width, the "
                     "unsigned maximum 255 in both the array and the fill) the SPEC "
                     "admits exactly the record `{data := [-1], kind := .signed, "
                     "itemsize := 1, fill := some (-1)}`, and that the impl returns "
                     "that same record — i.e. 255 -> -1, the kind flips to signed and "
                     "the byte width is preserved. Then the frozen obligation is "
                     "closed verbatim. Verifies (else the modeled behavior is "
                     "unsatisfiable, or satisfied by a DIFFERENT value, at exactly "
                     "the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, both ground instances "
                     "are `have`s inside the existing tactic body. Ports nagini's "
                     "admissibility probe. NOTE (audit): the earlier form stated the "
                     "obligation at `implementation_unsignedDecode <input>`, which is "
                     "an instance of the theorem it sits in front of and so held for "
                     "whatever the impl returned — it could not have detected a wrong "
                     "decoded value. The literal answer record closes that.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, and (b) a
    # refutation witness pinning the violation at one concrete input, checked to
    # HOLD of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "prepatch-passthrough-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_PREPATCH),
        "refinement": "This IS the pre-fix behaviour: the routine had no branch for "
                      "an unsigned-kind array, so one carrying the false-string "
                      "attribute fell through and was returned unchanged (still the "
                      "unsigned bit pattern). The F2P scenario reads the decoded "
                      "value and asserts the signed view (the unsigned maximum -> "
                      "-1); a passthrough leaves the maximum, so the F2P would FAIL "
                      "and the faithful patch would NOT resolve. This is the spec "
                      "sensing the change (G-DIFF). Ports nagini's "
                      "prepatch-passthrough-collapse.",
        "rationale": "REJECT from the CHANGED clause: the spec pins the result to "
                     "the signed reinterpretation of the values (and flips the "
                     "kind), but the rival returns the input unchanged; identity != "
                     "signed reinterpretation whenever any value needs folding. "
                     "Binders: kind=unsigned, attr=false-string, itemsize=1, "
                     "data=[255], fill=none.",
        "witness": _witness("[255]", "Kind.unsigned", "1", "none", '"false"'),
    },
    {
        "id": "direction-swap-unsigned-view",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DIRSWAP),
        "refinement": "A faithful real patch that reinterpreted the unsigned-kind "
                      "array to the UNSIGNED dtype of the same width (rather than the "
                      "signed dtype) would be a no-op on the already-unsigned values "
                      "— the maximum stays the maximum instead of becoming -1 — and "
                      "would also produce the wrong element kind. The F2P asserts the "
                      "signed value, so it would FAIL and the faithful patch would "
                      "NOT resolve. Ports nagini's direction-swap.",
        "rationale": "REJECT from the CHANGED clause: the spec pins the signed "
                     "reinterpretation of the values but the rival applies the "
                     "unsigned (modulo-width) one, which disagrees on any value with "
                     "the top bit set. Distinct point from the prepatch rival "
                     "(data=[200]).",
        "witness": _witness("[200]", "Kind.unsigned", "1", "none", '"false"'),
    },
    {
        "id": "boundary-off-by-one-sign-bit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_BOUNDARY),
        "refinement": "A faithful real patch whose signed reinterpretation used a "
                      "strict sign-bit test would map the exact boundary value (top "
                      "bit set, remainder == half the modulus) to itself instead of "
                      "to the signed minimum (e.g. an 8-bit 128 stays 128 instead of "
                      "becoming -128, which is what the real fixed-width cast "
                      "produces). Any decoded array containing that boundary value "
                      "would disagree with the real cast, so the patch does not "
                      "faithfully resolve. Ports nagini's boundary off-by-one.",
        "rationale": "REJECT from the CHANGED clause: the rival's map diverges from "
                     "the spec's signed reinterpretation at the boundary value "
                     "(folds to itself, not to the signed minimum). Refuted at the "
                     "sign-bit boundary point data=[128], itemsize=1.",
        "witness": _witness("[128]", "Kind.unsigned", "1", "none", '"false"'),
    },
    {
        "id": "first-element-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FIRSTELT),
        "refinement": "A faithful real patch that folded every element except the "
                      "leading one would leave element 0 unsigned. On an array whose "
                      "leading element needs folding the decoded value would be the "
                      "raw unsigned value, not its signed view, so the asserted "
                      "value mismatches and the patch would NOT resolve. Ports "
                      "nagini's first-element passthrough (restricted to the leading "
                      "element).",
        "rationale": "REJECT from the CHANGED clause: the spec maps every value "
                     "(`data.map`), but the rival pushes the leading value unchanged; "
                     "they differ whenever element 0 needs folding. Moves the data "
                     "binder to a multi-element list [130, 5].",
        "witness": _witness("[130, 5]", "Kind.unsigned", "1", "none", '"false"'),
    },
    {
        "id": "fill-value-not-reinterpreted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FILLMISS),
        "refinement": "A faithful real patch that reinterpreted the array values but "
                      "left the fill value in its stored (unsigned) form would report "
                      "a fill value inconsistent with the decoded signed array — a "
                      "wrong sentinel that would misclassify genuine data as missing "
                      "(or vice versa) downstream. The decoded fill must be the same "
                      "signed reinterpretation, so the patch would NOT resolve. Ports "
                      "the fill obligation the nagini spec pins internally.",
        "rationale": "REJECT from the fill sub-clause of the CHANGED clause: the spec "
                     "pins `fill := inp.fill.map (reinterpAsSigned bits)` but the "
                     "rival leaves the fill unmapped; they differ when the fill needs "
                     "folding. The only rival moving the fill binder (some 255).",
        "witness": _witness("[0]", "Kind.unsigned", "1", "some 255", '"false"'),
    },
    {
        "id": "output-kind-not-flipped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_KINDMISS),
        "refinement": "A faithful real patch that reinterpreted the values but left "
                      "the reported element kind unsigned would decode the values "
                      "correctly yet mislabel the array's signedness; the F2P asserts "
                      "the decoded element kind is the signed dtype, so it would FAIL "
                      "and the patch would NOT resolve. Ports the kind-output "
                      "obligation.",
        "rationale": "REJECT from the kind sub-clause of the CHANGED clause: the spec "
                     "pins `kind := Kind.signed` but the rival leaves it unsigned. "
                     "Moves the itemsize binder to 2 (data=[40000]).",
        "witness": _witness("[40000]", "Kind.unsigned", "2", "none", '"false"'),
    },
    {
        "id": "existing-signed-direction-collapsed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_SIGNEDMISS),
        "refinement": "A faithful real patch that flipped the element kind for a "
                      "signed-kind array carrying the true-string but left its values "
                      "in the stored (signed) form would break the pre-existing "
                      "signed->unsigned direction that the PASS_TO_PASS suite pins "
                      "(the stored -1 must read back as the unsigned maximum, not stay "
                      "-1), so the patch would NOT resolve.",
        "rationale": "REJECT from the signed-kind + true-string clause: the spec pins "
                     "`data.map (reinterpAsUnsigned bits)` but the rival leaves the "
                     "values unmapped. Moves the kind binder to signed and the attr "
                     "binder to the true-string, data=[-1].",
        "witness": _witness("[-1]", "Kind.signed", "1", "none", '"true"'),
    },
    {
        "id": "no-attribute-passthrough-broken",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NONEMISS),
        "refinement": "A faithful real patch that altered the reported element kind "
                      "when no attribute is present would corrupt arrays the "
                      "convention says to leave alone (there is nothing to reinterpret "
                      "without the attribute), mislabeling their signedness; the "
                      "no-attribute path must be a pure passthrough, so the patch "
                      "would NOT resolve.",
        "rationale": "REJECT from the no-attribute passthrough clause: the spec pins "
                     "the input kind unchanged but the rival reports signed. Moves "
                     "the unsignedAttr binder to none and the kind binder to other.",
        "witness": _witness("[7]", "Kind.other", "1", "none", "none"),
    },
    {
        "id": "nonmatching-value-guard-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_GUARDMISS),
        "refinement": "A faithful real patch that reinterpreted an unsigned-kind "
                      "array for ANY attribute value (dropping the false-string test) "
                      "would transform arrays whose attribute is some other string — "
                      "the convention only reinterprets on the exact false-string — "
                      "corrupting their values, so the patch would NOT resolve.",
        "rationale": "REJECT from the unsigned-kind + non-false passthrough clause: "
                     "the spec passes the input through for a non-matching value but "
                     "the rival reinterprets it. Moves the unsignedAttr binder to a "
                     "non-matching value (\"0\").",
        "witness": _witness("[200]", "Kind.unsigned", "1", "none", '"0"'),
    },
    {
        "id": "residual-kind-passthrough-broken",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_OTHERMISS),
        "refinement": "A faithful real patch that reinterpreted arrays of the "
                      "residual element kind (weakening the unsigned test to "
                      "not-signed) would transform non-integer arrays the convention "
                      "leaves untouched — exactly the case that must warn and pass "
                      "through — corrupting them, so the patch would NOT resolve.",
        "rationale": "REJECT from the residual-kind passthrough clause: the spec "
                     "passes the input through when the kind is neither signed nor "
                     "unsigned, but the rival reinterprets it. Moves the kind binder "
                     "to other with the false-string attribute.",
        "witness": _witness("[200]", "Kind.other", "1", "none", '"false"'),
    },
    {
        "id": "byte-width-clobbered",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_WIDTHMISS),
        "refinement": "A faithful real patch that reinterpreted to a fixed ONE-BYTE "
                      "signed element type instead of the signed type of the array's "
                      "OWN byte width would narrow every wider array: the decoded "
                      "element type would be the 1-byte signed one rather than the "
                      "same-width one, and the wider F2P scenarios assert the "
                      "same-width signed type (and the value the same-width "
                      "reinterpretation produces, which for a wider array is not the "
                      "one-byte result), so those would FAIL and the patch would NOT "
                      "resolve. Width preservation is a separate obligation from the "
                      "values and the kind, and this rival is wrong ONLY in the width.",
        "rationale": "REJECT from the width-preservation clause: the spec pins "
                     "`itemsize := inp.itemsize` in every arm, but the rival reports 1 "
                     "in the reinterpreting arm. Single-fault — the values and the "
                     "element kind are reinterpreted correctly, so this is the only "
                     "rival that isolates the width. Added by audit: the battery's "
                     "docstring claimed width preservation as a defended obligation "
                     "while no rival attacked it, so nothing demonstrated the spec "
                     "senses it. Refutation point data=[65535], itemsize=2 (a WIDER "
                     "array, where the narrowed width is observable).",
        "witness": _witness("[65535]", "Kind.unsigned", "2", "none", '"false"'),
    },
    {
        "id": "signed-kind-nonmatching-guard-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_SIGNEDGUARDMISS),
        "refinement": "A faithful real patch that reinterpreted a signed-kind array "
                      "for ANY attribute value (dropping the true-string test) would "
                      "transform arrays whose attribute is some other string — the "
                      "convention only reinterprets on the exact true-string — "
                      "corrupting their values and mislabeling their signedness, so "
                      "the patch would NOT resolve.",
        "rationale": "REJECT from the signed-kind + non-true passthrough clause: the "
                     "spec passes the input through when the kind is signed and the "
                     "attribute value is not the true-string, but the rival "
                     "reinterprets it and flips the kind. Added by audit: the "
                     "docstring listed this clause among the defended top-level "
                     "clauses, but only its unsigned-kind mirror "
                     "(nonmatching-value-guard-dropped) had a rival, so this one was "
                     "undemonstrated. Moves the kind binder to signed with a "
                     "non-matching attribute value (\"maybe\"), data=[9].",
        "witness": _witness("[9]", "Kind.signed", "1", "none", '"maybe"'),
    },
]

# No AXIOM lane: the reinterpretation is modeled deeply as exact integer
# arithmetic (no `axiom`, no `opaque` callee), so there is nothing for the axiom
# lane to probe. The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
