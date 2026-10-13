# properties.py — G-PBT falsification battery for psf__requests-2931 (lean lane).
# NOT a Lean module; a manifest the gate elaborates against the frozen spec.
# Ported from the nagini sibling's properties.py, re-expressed against this
# backend's carrier. Each case is a FULL Solution.lean that shares the frozen
# spec EXACTLY and differs only inside the impl region (and, for positives that
# reshape the impl, the proof tactic body) — so same_spec holds by construction
# and every rejection is attributable to the postcondition, not to a edited spec.
#
# Defended surface (read from Solution.lean):
#   implementation_encodeParams (data : Datum) : Datum
#   ONE obligation, `theorem correct_encodeParams`, over ONE input binder
#   `data : Datum` — a payload that is either a text value (`List Char`) or a
#   binary value (`List UInt8`), the constructor recording which.
#   ONE top-level postcondition clause, and it is a whole-value equation:
#     (C1) result = data
#   Because `Datum` is an inductive with two constructors each carrying a
#   sequence, that single clause is load-bearing in THREE independent ways, and
#   the rival set below attacks each separately:
#     (C1a) the KIND is preserved — a binary payload may not come back as a text
#           value, nor a text payload as a binary value;
#     (C1b) the CONTENTS are preserved elementwise — no element may be altered;
#     (C1c) the CONTENTS are preserved in ORDER and LENGTH — nothing dropped,
#           nothing permuted.
#   A rival can break exactly one of these while satisfying the other two, so a
#   battery that attacked only (C1a) would leave a content-mangling rival
#   uncaught. `decide` computes the whole predicate at a literal `Datum`, so
#   every witness below is stated at a concrete input with no binders at all —
#   no conditioning on an opaque carrier is needed, and no witness carries a
#   hypothesis that could be inconsistent.
#
# Carrier narrowing vs the nagini sibling — why this port is SMALLER, and why
# that is correct rather than a thinner battery:
#   * The nagini model contracted TWO functions over a `Value(is_bytes, data)`
#     record: `serialize_request_body` (the payload pass-through) and
#     `normalize_query_string` (the compensating coercion at the query-building
#     site), plus a `to_native` @Pure @ContractOnly axiom consumed by the second.
#     THIS bundle models only the FIRST of those (mapping.md "Scope": the second
#     site is a compensating coercion that re-establishes, at the query-params
#     call site only, the coercion the first site stops doing; it observably
#     changes nothing the F2P demands and nothing the frozen spec frames).
#     So every nagini case attached to `normalize_query_string` has NO
#     counterpart here — there is no such obligation to attack. Concretely:
#       - weak-normalize-preserve-tag  — DROPPED, unmodeled obligation.
#       - weak-normalize-drop-content  — DROPPED, unmodeled obligation. Its
#         ARGUMENT (content-dropping must be sensed by the content clause) is
#         NOT dropped: it is carried over onto the modeled obligation as
#         weak-drop-content below, where it attacks (C1c).
#       - pos-normalize-direct         — DROPPED, unmodeled obligation.
#       - admiss-normalize-binary-ascii — DROPPED, unmodeled obligation.
#     Chasing case-count parity here would mean fabricating rivals for a site
#     this bundle does not contract, so it is not attempted.
#   * nagini's two-field record (`is_bytes` tag + `data` content) becomes ONE
#     inductive value whose constructor IS the tag. A nagini rival that wrote a
#     wrong tag while keeping the content becomes a rival that returns the wrong
#     CONSTRUCTOR, and it must then also supply a content of the other
#     constructor's element type — which is why the kind-flipping rivals below
#     carry an explicit conversion rather than a bare constant.
#   * nagini's `to_native` axiom lane is DROPPED wholesale (AXIOM_TESTS = []):
#     `meta.axioms == []` here and the axioms region is empty, because the
#     modeled branch calls nothing at all — it is the identity. The axiom lane
#     is G-AX's job and this gate ignores it.
#   * The nagini ASCII precondition (`Implies(v.is_bytes, is_ascii(v.data))`)
#     belonged to the query-normalization site, not to the payload site. The
#     modeled obligation here has NO precondition — `correct_encodeParams` binds
#     `∀ (data : Datum)` with no hypothesis — so the whole `Datum` domain is
#     in-domain. That is what makes the non-ASCII binary payload (the reported
#     failure's shape) directly available as a witness point, and it is why the
#     nagini "to_native's Requires is UNESTABLISHED" half of
#     weak-serialize-native-decode has no analogue: on this carrier that rival is
#     refuted by (C1a) alone, at a point where the value simply differs.
#
# Vacuous / known-hole classes, stated per directive rather than silently
# omitted:
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. The nagini sibling
#     carries THREE such cases (frame-mut-serialize-data,
#     frame-mut-serialize-tag, frame-mut-normalize-data), each a rival that
#     writes the read-only input so the postcondition becomes trivially true,
#     rejected by Viper for insufficient permission (only a half share is held).
#     That whole class rests on fractional heap permissions. Lean is
#     referentially transparent: `data : Datum` is an immutable value, there is
#     no aliasable input to clobber and no permission to be insufficient, so the
#     rival cannot even be written. NOTHING to port, and no substitute is
#     fabricated. Note this is not a gap in the defended surface either — the
#     frame obligation the nagini permissions enforced is discharged here by the
#     spec SHAPE: `result = data` pins the whole value against the input, so
#     there is no unconstrained output component a rival could fill freely.
#   * DIVERGENCE / NON-TERMINATION lane — NOT SHIPPABLE here, but for a narrower
#     and measured reason than "the class does not exist". Corrected under audit:
#     an earlier revision of this header claimed a non-terminating implementation
#     "cannot be written at all" on this carrier. That is FALSE and was disproven
#     with real builds. `partial def implementation_encodeParams (data : Datum) :
#     Datum := implementation_encodeParams data` is writable, passes
#     `variant_scope.variant_problems` clean (it adds no axiom/sorry/theorem and
#     keeps the obligation statement byte-identical), and the frozen bundle
#     carries no `loom.semantics.termination` option at all — the lean backend has
#     no termination-semantics switch, so neither disposition in the F′ directive
#     applies verbatim. What actually blocks the case is the WITNESS half, and
#     that was measured rather than argued:
#       - the rival's build fails (`Tactic 'rfl' failed`), so it WOULD be recorded
#         as `rejected` — but on this backend that attributes nothing to the spec,
#         which is exactly what the witness requirement exists to catch;
#       - `partial def` is compiled with a `WellFounded`/opaque implementation and
#         generates NO equation lemmas, so every unconditional witness shape fails
#         on the RIVAL side — the half that must succeed: `unfold` reports "failed
#         to unfold `implementation_encodeParams`", `simp [implementation_
#         encodeParams]` reports "`simp` made no progress", and `decide +kernel`
#         cannot reduce the instance. Rival exit 1 in all three shapes, so there
#         is nothing to ship;
#       - the hypothesis-conditioned shape the opaque-carrier directive recommends
#         (`example (h : implementation_encodeParams p ≠ p) : ¬ problem_spec ...`)
#         DOES elaborate — but it elaborates against the FROZEN SOLUTION too
#         (rival 0, gold 0), because the hypothesis is what does all the work and
#         it is stated over a name both files declare. That is `witness-vacuous`,
#         an inconclusive gate outcome, not a refutation.
#     So the disposition is a KNOWN HOLE in the witness lane, not a vacuous class:
#     a diverging impl is expressible and is not refutable by any witness shape
#     tried here. It is recorded rather than silently omitted for that reason.
#     Distinct from the velvet situation, where under `set_option
#     loom.semantics.termination "partial"` a diverging impl VERIFIES outright
#     (the corpus-wide termination-semantics finding); here it fails to build, so it cannot mint a
#     false positive — the gap is only that its rejection is unattributable.
#   * AXIOM lane — DROPPED (see above). AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "psf__requests-2931"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly if the
# frozen solution ever changes. The impl region body and the proof TACTIC body
# are the only regions a variant may edit; the spec, the `Datum` carrier, and the
# byte-identical `theorem correct_encodeParams` STATEMENT are never touched.
# Each anchor lies entirely inside the region it edits and is unique in the file.

_IMPL_OLD = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  -- A text or binary payload is handed back as-is.
  return data"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

# The frozen proof tactic body (everything after the theorem statement's `:= by`).
_PROOF_OLD = """\
  intro data
  rfl"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


# --- Witness helper. Every reject case states the frozen spec predicate directly
# at ONE concrete, `decide`-able payload; the negation elaborates iff the rival's
# output contradicts the spec there. Checked in a file with the frozen obligation
# removed, so the frozen tactic script cannot interfere with the verdict — which
# matters here because `intro data; rfl` breaks for ANY reshaped impl, correct or
# wrong, so the build verdict alone would attribute nothing to the spec.
# No witness binds anything, so none can rest on inconsistent hypotheses.
def _witness(arg):
    return f"""\
example : ¬ problem_spec_encodeParams ({arg})
    (implementation_encodeParams ({arg})) := by
  unfold problem_spec_encodeParams implementation_encodeParams
  decide"""


# The witness points. Each rival is refuted at the input that isolates ITS
# sub-domain, so no two rivals share a point and each `rationale`'s sub-domain
# claim is the one the manifest actually demonstrates. Verified by hand with
# scripts/lean_verify.sh: each elaborates against its rival and FAILS on the
# frozen solution, and each near-miss was additionally checked to be CORRECT
# (witness fails) at the other rivals' points.
_P_ASCII_BINARY = "Datum.binary [116, 101, 115, 116, 61, 102, 111, 111]"
_P_NONASCII_BINARY = "Datum.binary [195, 182, 195, 182, 195, 182]"
_P_HIGH_BINARY = "Datum.binary [255, 128, 200]"
_P_TEXT = "Datum.text ['l', 'i', 'f', 'e', '=', '4', '2']"
_P_TEXT_LONG = "Datum.text ['s', 't', 'u', 'f', 'f', '=', 'e', 'l', 'i', 'x', 'r']"
_P_TEXT_PAIR = "Datum.text ['x', '=', '1', '&', 'y', '=', '2']"
_P_TEXT_EMPTY = "Datum.text []"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG. Each is a
# structurally different but behaviourally identical impl, shipped WITH a proof
# that closes for the new shape. The theorem STATEMENT is byte-identical; only
# the tactic body changes. No new lemma, no new axiom, no sorry/admit.
# ===========================================================================

# pos-case-split: the port of nagini's pos-serialize-locals — a correct
# pass-through written in a different executable shape. Nagini reshaped by
# binding the tag and the content into locals before reconstructing the record;
# on this carrier the record IS the constructor, so the analogous reshape is to
# split on the constructor and rebuild each branch identically. This is the
# sharpest positive available here: it is the SAME SHAPE as the kind-flipping
# rivals below (an explicit two-branch match) and differs only in returning the
# matching constructor, so it demonstrates that the reject verdicts come from the
# spec and not from the impl having been reshaped at all. The frozen `rfl` no
# longer closes (the match blocks reduction on an opaque `data`), so the proof
# reproves by `cases data <;> rfl` — each branch then reduces definitionally.
_POS_CASE_SPLIT = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text s   => return .text s
  | .binary b => return .binary b"""

_POS_CASE_SPLIT_PROOF = """\
  intro data
  cases data <;> rfl"""

# pos-let-bound: the closest analogue of nagini's local-variable reshape — bind
# the payload to a local and return the local. Confirms the obligation does not
# secretly depend on the payload being returned by the syntactic name it arrived
# under. The frozen tactic body still closes (the `let` is definitionally
# transparent), so this case also pins that the frozen proof is not accidentally
# specific to the frozen spelling.
_POS_LET_BOUND = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  let payload := data
  return payload"""

# pos-pure-functional: the same behaviour with the imperative wrapper removed
# entirely (no `Id.run do`, no `return`) — a plain functional definition.
# Confirms the spec is a claim about the VALUE and not about the monadic
# encoding the frozen impl happens to use.
_POS_PURE = """\
def implementation_encodeParams (data : Datum) : Datum :=
  data"""

# pos-wrap-elements: ADDED UNDER AUDIT. Every positive above reshapes only the
# CONTROL FLOW — the payload's elements are handed back as the very terms that
# arrived, so `rfl`/`cases <;> rfl` closes each one definitionally. That left the
# soundness lane blind in the one direction the rival lane leans on hardest: the
# rivals weak-alter-elements and weak-decode-nonascii-only are rejected for
# touching ELEMENTS, and until now no positive established that the spec accepts
# an impl which rebuilds each element through a non-trivial arithmetic round trip
# that happens to be the identity. `UInt8.ofNat (x.toNat + 256)` is exactly that:
# `UInt8.ofNat` reduces mod 256, so adding a full period returns the same byte —
# behaviourally the identity, but NOT definitionally so, which is the point. This
# is the SPEC-TOO-STRONG probe that matters here, because a spec that only
# admitted syntactically-identical element terms would reject a faithful patch
# whose arithmetic differs. Proven, not assumed: the frozen `rfl` does not close,
# and the proof discharges the round trip via `UInt8.toNat_inj` plus
# `Nat.mod_eq_of_lt x.toNat_lt`. Statement byte-identical; no lemma, no axiom.
_POS_WRAP = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text s   => return .text s
  | .binary b => return .binary (b.map (fun x => UInt8.ofNat (x.toNat + 256)))"""

_POS_WRAP_PROOF = """\
  intro data
  cases data with
  | text s => rfl
  | binary b =>
    have h : ∀ x : UInt8, UInt8.ofNat (x.toNat + 256) = x := by
      intro x
      apply UInt8.toNat_inj.mp
      simp [Nat.mod_eq_of_lt x.toNat_lt]
    simp [implementation_encodeParams, problem_spec_encodeParams, h]"""


# ===========================================================================
# ADMISSIBILITY — the port of nagini's admiss-serialize-binary-nonascii. Nagini
# built a fresh in-domain Value and asserted the post-state with `Assert(...)`
# at the call site; the lean analogue states the frozen spec predicate at the
# same shapes as in-impl `have`s discharged by `decide`. It keeps the frozen
# impl body and the frozen proof script verbatim, so the only thing it can fail
# on is a regression in what the predicate admits at those concrete points.
#
# Strengthened beyond nagini's version in one way that matters: nagini asserted
# only that the expected post-state HOLDS. A predicate that held of everything
# would pass that. So this also asserts the kind-flipped answer is REFUSED at
# the same input — making the case a two-sided check that the predicate
# discriminates at the very shape the reported failure exercises, rather than
# merely admitting it.
# ===========================================================================
_ADMISS = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  -- The payload shape the reported failure exercises is admitted by the
  -- obligation, and at that shape the kind-preserving answer is the ONLY one the
  -- predicate accepts: the kind-flipping answer is refuted at the same point.
  have _hAdmitted : problem_spec_encodeParams
      (Datum.binary [195, 182, 195, 182, 195, 182])
      (Datum.binary [195, 182, 195, 182, 195, 182]) := by
    unfold problem_spec_encodeParams; decide
  have _hRefused : ¬ problem_spec_encodeParams
      (Datum.binary [195, 182, 195, 182, 195, 182])
      (Datum.text ['\\u00c3', '\\u00b6', '\\u00c3', '\\u00b6', '\\u00c3', '\\u00b6']) := by
    unfold problem_spec_encodeParams; decide
  have _hTextAdmitted : problem_spec_encodeParams
      (Datum.text ['t', 'e', 's', 't', '=', 'f', 'o', 'o'])
      (Datum.text ['t', 'e', 's', 't', '=', 'f', 'o', 'o']) := by
    unfold problem_spec_encodeParams; decide
  return data"""


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each edits ONLY the
# impl region and ships a witness proving it violates the spec at one concrete
# payload (elaborates against the rival, FAILS against the frozen solution).
# ===========================================================================

# weak-decode-to-text: the port of nagini's weak-serialize-native-decode — the
# pre-change behaviour, routing every payload through a native-text coercion so
# a binary payload comes back as a text value. Attacks (C1a) on the whole binary
# sub-domain. Witnessed at an ASCII binary payload rather than at the reported
# failure's non-ASCII one, deliberately: this rival is wrong on EVERY binary
# payload, so refuting it on the sub-domain where the tighter near-miss
# weak-decode-nonascii-only is still CORRECT is what keeps the two rivals'
# rationales distinct instead of collapsing them onto one point.
_WEAK_DECODE = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text s   => return .text s
  | .binary b => return .text (b.map (fun byte => Char.ofNat byte.toNat))"""

# weak-encode-to-binary: the mirror of the above and the port of nagini's
# weak-serialize-flip-tag — force the OTHER constructor, so a text payload comes
# back as a binary value. Attacks (C1a) on the text sub-domain. Nagini pinned the
# tag to the constant `True`; on this carrier forcing a constructor also forces a
# conversion of the contents, which is why the branch carries an explicit map.
# This is the rival that makes the text sub-domain of the binder load-bearing:
# without it every witness would sit on a binary payload and a rival that
# mishandled only text payloads would go unnoticed.
_WEAK_ENCODE = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text s   => return .binary (s.map (fun c => UInt8.ofNat c.toNat))
  | .binary b => return .binary b"""

# weak-drop-content: carries over the ARGUMENT of nagini's
# weak-normalize-drop-content (whose own obligation is unmodeled here) onto the
# modeled obligation. The KIND is preserved perfectly, so (C1a) is satisfied and
# every kind-based check passes; the contents are dropped. Attacks (C1c) — the
# clause that content-dropping must be sensed. Witnessed on a text payload, so
# the point is distinct from the kind rivals' points.
_WEAK_DROP = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text _   => return .text []
  | .binary _ => return .binary []"""

# weak-decode-nonascii-only: a strictly TIGHTER near-miss than weak-decode-
# to-text, which is wrong on the whole binary sub-domain and so could be refuted
# almost anywhere. This one coerces a binary payload to a text value ONLY when
# some element is outside the 7-bit range, and is otherwise a faithful
# pass-through — correct on every text payload AND on every ASCII binary
# payload. It therefore violates (C1a) on exactly the sub-domain the reported
# failure occupies, and is witnessed at precisely that shape. Verified by hand
# that its witness FAILS at the ASCII-binary and text points, i.e. that the
# near-miss claim is demonstrated and not merely asserted.
_WEAK_NONASCII = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text s   => return .text s
  | .binary b =>
    if b.all (fun byte => byte.toNat < 128) then
      return .binary b
    else
      return .text (b.map (fun byte => Char.ofNat byte.toNat))"""

# weak-alter-elements: NO nagini counterpart, and it closes a real gap. Every
# rival above either flips the kind or empties the contents; none returns a
# payload of the RIGHT kind and the RIGHT length whose ELEMENTS differ. This one
# preserves the kind always and clears the high bit of each element of a binary
# payload, so it is correct on every text payload and every ASCII binary payload
# and wrong only on binary content carrying an element at or above 128 — wrong
# there WITHOUT flipping the kind, which no other rival probes. Attacks (C1b).
# Witnessed at a high-element binary payload distinct from the near-miss above.
_WEAK_ALTER = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text s   => return .text s
  | .binary b => return .binary (b.map (fun byte => byte % 128))"""

# weak-permute-content: NO nagini counterpart. Preserves the kind AND the exact
# multiset of elements AND the length, permuting only their ORDER. If (C1) were
# ever weakened to a length-and-membership relation rather than a whole-value
# equation, every other rival here would still be caught and this one would not.
# Attacks (C1c) at the ordering half specifically.
_WEAK_PERMUTE = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text s   => return .text s.reverse
  | .binary b => return .binary b.reverse"""

# weak-empty-boundary: NO nagini counterpart. The tightest near-miss in the set —
# a faithful pass-through everywhere EXCEPT the empty text payload, where it
# flips the kind. Correct on every non-empty payload of either kind and on the
# empty binary payload, so it is refutable at exactly one point in the whole
# domain. It is here because the empty payload is the boundary a fuzzer over
# random contents is least likely to hit while every other rival is refuted at a
# non-empty one, and because it is the case that shows (C1) is pinned pointwise
# rather than on "typical" inputs. Attacks (C1a) at the empty-content boundary.
_WEAK_EMPTY = """\
def implementation_encodeParams (data : Datum) : Datum := Id.run do
  match data with
  | .text []  => return .binary []
  | .text s   => return .text s
  | .binary b => return .binary b"""


# A refinement argument shared by the kind-flipping rivals. Stated once and
# referenced, rather than restated per case, because it is genuinely the same
# argument at different inputs.
_REF_KIND = (
    "The single F2P assertion is that a binary payload survives preparation as "
    "a binary value. A faithful real patch built from this rival re-introduces "
    "exactly the coercion whose removal the F2P demands: on the reported input "
    "(a binary payload whose elements lie outside the 7-bit range) the real "
    "coercion raises a decode error, and on any input where it does not raise, "
    "the payload comes back as a text value so the F2P's kind assertion fails. "
    "Either way the F2P does NOT resolve, so a rival of this shape that "
    "VERIFIED would be a true verify-does-not-imply-resolve break rather than "
    "an artifact of the port.")


SPEC_TESTS = [
    # ---------------- positives (soundness) ----------------
    {
        "id": "pos-case-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_CASE_SPLIT, _POS_CASE_SPLIT_PROOF),
        "rationale": (
            "Ports nagini pos-serialize-locals. A correct pass-through in a "
            "different executable shape: split on the payload kind and rebuild "
            "each branch with the matching constructor. Deliberately the SAME "
            "two-branch shape as the kind-flipping rivals, differing only in "
            "which constructor each branch returns — so it demonstrates that "
            "those rivals are rejected by clause (C1) and not merely because "
            "reshaping the impl breaks the frozen `rfl`. The frozen tactic body "
            "does not close for this shape (a match blocks reduction on an "
            "opaque `data`), so the proof reproves with `cases data <;> rfl`, "
            "which closes because each branch reduces definitionally. The "
            "theorem statement is byte-identical and no lemma or axiom is added. "
            "If this could not verify => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-let-bound",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LET_BOUND),
        "rationale": (
            "Ports nagini pos-serialize-locals' local-variable reshape directly: "
            "bind the payload to a local and return the local. Shows clause (C1) "
            "does not depend on the payload being returned under the syntactic "
            "name it arrived under. The frozen tactic body is kept verbatim and "
            "still closes (the `let` is definitionally transparent), which also "
            "pins that the frozen proof is not accidentally specific to the "
            "frozen spelling. If this failed => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE),
        "rationale": (
            "The same behaviour with the imperative wrapper removed entirely — a "
            "plain functional definition, no `Id.run do` and no `return`. "
            "Confirms clause (C1) is a claim about the returned VALUE and not "
            "about the monadic encoding the frozen impl happens to use. The "
            "frozen tactic body still closes. If this failed => SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-wrap-elements",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_WRAP, _POS_WRAP_PROOF),
        "rationale": (
            "ADDED UNDER AUDIT to close a real gap in the soundness lane. Every "
            "other positive reshapes only the control flow and hands each element "
            "back as the term it arrived as, so all of them close definitionally. "
            "None established that clause (C1) admits an impl that REBUILDS each "
            "element through non-trivial arithmetic which is only "
            "extensionally the identity — and that is precisely the direction the "
            "rival lane leans on, since weak-alter-elements and "
            "weak-decode-nonascii-only are both rejected for touching elements. "
            "This impl maps every byte through `UInt8.ofNat (x.toNat + 256)`: "
            "`UInt8.ofNat` reduces mod 256, so adding one full period returns the "
            "same byte, making it behaviourally identical to the frozen impl but "
            "NOT definitionally equal to it. The frozen tactic body does not "
            "close; the proof discharges the round trip with `UInt8.toNat_inj` "
            "and `Nat.mod_eq_of_lt x.toNat_lt`, adding no lemma and no axiom, "
            "with the theorem statement byte-identical. If this could not verify "
            "=> SPEC-TOO-STRONG: the spec would be rejecting a faithful "
            "pass-through merely for computing its elements a different way."
        ),
    },

    # ---------------- admissibility ----------------
    {
        "id": "admiss-payload-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "Ports nagini admiss-serialize-binary-nonascii. The obligation binds "
            "`∀ (data : Datum)` with NO precondition, so the whole payload "
            "domain — including the binary payload with out-of-7-bit-range "
            "elements that the reported failure exercises — is in-domain. This "
            "case keeps the frozen impl and the frozen proof verbatim and adds "
            "in-impl `have`s pinning the predicate at that shape and at a text "
            "shape, so the only thing it can fail on is a regression in what the "
            "predicate admits there. Strengthened beyond the nagini version: "
            "besides asserting the expected answer is ADMITTED it also asserts "
            "the kind-flipped answer is REFUSED at the same input, which a "
            "predicate that held of everything would fail — making this a "
            "two-sided check that the predicate discriminates at the reported "
            "failure's shape rather than merely accepting it. If the admitted "
            "halves failed => PRECOND-TOO-STRONG (the obligation would be "
            "rejecting the very input the change targets)."
        ),
    },

    # ---------------- rivals (uniqueness) ----------------
    {
        "id": "weak-decode-to-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DECODE),
        "witness": _witness(_P_ASCII_BINARY),
        "rationale": (
            "Ports nagini weak-serialize-native-decode — the pre-change "
            "behaviour: every payload is routed through a native-text coercion, "
            "so a binary payload comes back as a text value. REJECT comes from "
            "clause (C1) via (C1a), the kind half: at the witness payload the "
            "returned value is a text value where the binder is a binary one, so "
            "`result = data` is false. Wrong on the ENTIRE binary sub-domain of "
            "the `data` binder. Witnessed at an ASCII binary payload rather than "
            "at the reported failure's shape on purpose — that is the sub-domain "
            "where the tighter near-miss weak-decode-nonascii-only is still "
            "correct, so the two rivals are refuted at different points and "
            "neither rationale claims a sub-domain the other's witness "
            "demonstrates. Note the nagini version was ALSO rejectable for an "
            "unestablished ASCII precondition on the coercion; that half has no "
            "analogue here, since the modeled obligation carries no "
            "precondition, and (C1a) alone is fatal."
        ),
        "refinement": _REF_KIND,
    },
    {
        "id": "weak-encode-to-binary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ENCODE),
        "witness": _witness(_P_TEXT),
        "rationale": (
            "Ports nagini weak-serialize-flip-tag, mirrored onto this carrier. "
            "Nagini pinned the tag to the constant `True`; here forcing the "
            "binary constructor also forces a conversion of the contents, so the "
            "branch carries an explicit map. REJECT from clause (C1) via (C1a) "
            "on the TEXT sub-domain: at the witness payload a text value is "
            "returned as a binary one. This is the rival that makes the text "
            "half of the `data` binder load-bearing — without it every witness "
            "in the battery would sit on a binary payload, and a rival that "
            "mishandled only text payloads would verify unnoticed. "
            "Partial-domain: correct on binary payloads."
        ),
        "refinement": (
            "This rival is the reason the F2P alone cannot certify the change. "
            "The F2P asserts only that a binary payload stays binary, which "
            "unconditionally returning a binary value satisfies — so a faithful "
            "real patch of this shape WOULD resolve the F2P while being plainly "
            "wrong. What it breaks is the rest of the suite: several "
            "PASS_TO_PASS tests prepare a text payload and assert the prepared "
            "body equals a text value (`pr.body == 'life=42'`, "
            "`'stuff=elixr' == prep.body`, `p.body == urlencode(data)`), and a "
            "payload coerced to a binary value fails those equalities. So its "
            "faithful patch does not leave the instance resolved, and a "
            "verifying rival here would be a true verify-does-not-imply-resolve "
            "break."
        ),
    },
    {
        "id": "weak-drop-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP),
        "witness": _witness(_P_TEXT_LONG),
        "rationale": (
            "Carries over the ARGUMENT of nagini weak-normalize-drop-content — "
            "that content-dropping must be sensed by the content half of the "
            "postcondition — onto the obligation this bundle actually models "
            "(the nagini case's own obligation is unmodeled here; see the header "
            "note). The KIND is preserved perfectly, so (C1a) is satisfied and "
            "every kind-based check passes; the CONTENTS are emptied. REJECT "
            "from clause (C1) via (C1c): at the witness payload an empty "
            "sequence is returned where the binder carries a non-empty one. "
            "Witnessed on a text payload, a point distinct from every kind "
            "rival's."
        ),
        "refinement": (
            "A faithful real patch that returned an emptied payload would leave "
            "the F2P's own assertion satisfied — an empty binary value is still "
            "a binary value — but destroys the payload every body- and "
            "query-carrying test observes: the PASS_TO_PASS assertions on the "
            "prepared body equalling a specific text value, and the "
            "query-building test that pins a prepared URL to a specific query "
            "string, all compare against non-empty content and would fail "
            "against emptied content. Its faithful patch does not resolve the "
            "instance."
        ),
    },
    {
        "id": "weak-decode-nonascii-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONASCII),
        "witness": _witness(_P_NONASCII_BINARY),
        "rationale": (
            "A strictly TIGHTER near-miss than weak-decode-to-text, shipped "
            "separately because that rival is wrong across the whole binary "
            "sub-domain and so could be refuted almost anywhere, which would "
            "leave the reported failure's own sub-domain untested by any "
            "witness. This one coerces a binary payload to a text value ONLY "
            "when some element lies outside the 7-bit range, and is otherwise a "
            "faithful pass-through: correct on every text payload AND on every "
            "ASCII binary payload. REJECT from clause (C1) via (C1a) on exactly "
            "the sub-domain the reported failure occupies, and it is witnessed "
            "at precisely that shape. Its near-miss claim is demonstrated, not "
            "asserted: the same witness statement was checked by hand to FAIL "
            "against this rival at both the ASCII-binary and the text point, "
            "confirming it agrees with the frozen solution there."
        ),
        "refinement": _REF_KIND,
    },
    {
        "id": "weak-alter-elements",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALTER),
        "witness": _witness(_P_HIGH_BINARY),
        "rationale": (
            "NO nagini counterpart; it closes a real gap in the ported set. "
            "Every other rival either flips the payload KIND or empties the "
            "contents — none returns a payload of the right kind and the right "
            "length whose ELEMENTS differ, so clause (C1b) would otherwise be "
            "attacked by nobody. This rival always preserves the kind and clears "
            "the high bit of each element of a binary payload: correct on every "
            "text payload and every ASCII binary payload, wrong only on binary "
            "content carrying an element at or above 128 — and wrong there "
            "WITHOUT flipping the kind, which no other witness probes. REJECT "
            "from clause (C1) via (C1b) at the witness payload, whose elements "
            "are all above the cut and are therefore all altered. The point is "
            "distinct from weak-decode-nonascii-only's, so the two "
            "non-7-bit-range rivals do not share a witness despite both living "
            "in that sub-domain: they fail there for different reasons (kind vs "
            "elements) and are refuted at different inputs."
        ),
        "refinement": (
            "This is the subtlest of the set for the F2P: a faithful real patch "
            "that returned the payload as a binary value with each element "
            "masked WOULD satisfy the F2P assertion, which only checks that the "
            "prepared body is a binary value and never inspects its content. It "
            "nonetheless silently corrupts every payload carrying an element "
            "outside the 7-bit range — including the reported input, whose "
            "elements are exactly such — so the behaviour the issue asks for is "
            "not delivered, and the PASS_TO_PASS assertions comparing a prepared "
            "body against specific content fail wherever masking changes it. Its "
            "faithful patch does not resolve the instance in any meaningful "
            "sense, so a verifying rival here would be a true "
            "verify-does-not-imply-resolve break."
        ),
    },
    {
        "id": "weak-permute-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PERMUTE),
        "witness": _witness(_P_TEXT_PAIR),
        "rationale": (
            "NO nagini counterpart. Preserves the payload kind AND the exact "
            "multiset of elements AND the length, permuting only their ORDER. "
            "REJECT from clause (C1) via (C1c), the ordering half: at the "
            "witness payload the reversed sequence differs from the binder's. "
            "This is the rival that shows (C1) is a whole-value equation and not "
            "a length-and-membership relation — if the clause were ever weakened "
            "that way, every other rival in this battery would still be caught "
            "and this one would not, which is exactly the blind spot a "
            "content-preserving-but-reordering implementation would exploit."
        ),
        "refinement": (
            "A faithful real patch returning a reversed payload satisfies the "
            "F2P assertion outright (a reversed binary value is still a binary "
            "value, and the F2P checks nothing else), so the F2P cannot "
            "distinguish it. It is nonetheless wrong: the PASS_TO_PASS tests "
            "that pin a prepared body to a specific text value and a prepared "
            "URL to a specific query string compare content in order and fail "
            "against a reversed payload. Its faithful patch does not leave the "
            "instance resolved."
        ),
    },
    {
        "id": "weak-empty-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY),
        "witness": _witness(_P_TEXT_EMPTY),
        "rationale": (
            "NO nagini counterpart; the tightest near-miss in the set. A "
            "faithful pass-through everywhere EXCEPT the empty text payload, "
            "where it flips the kind — correct on every non-empty payload of "
            "either kind and on the empty binary payload, so it is refutable at "
            "exactly ONE point in the whole domain. REJECT from clause (C1) via "
            "(C1a) at that point. It is shipped because every other witness sits "
            "on a non-empty payload, and the empty payload is both the boundary a "
            "fuzzer over random contents is least likely to hit and the one that "
            "shows (C1) is pinned pointwise across the binder rather than on "
            "typical inputs. Its near-miss claim is demonstrated: the same "
            "witness statement was checked by hand to FAIL against this rival at "
            "a non-empty text point and at a binary point."
        ),
        "refinement": (
            "A faithful real patch special-casing an empty text payload to a "
            "binary value passes the F2P, which never prepares an empty payload. "
            "It is still not the change the issue asks for, and it regresses the "
            "surrounding behaviour: an empty payload silently changes kind, so "
            "the prepared body stops comparing equal to the empty text value "
            "callers and the PASS_TO_PASS body assertions expect. Because the "
            "F2P is blind to this input entirely, a rival of this shape that "
            "VERIFIED would be precisely a verify-does-not-imply-resolve break "
            "that no amount of F2P evidence would reveal."
        ),
    },
]


# The axiom lane is G-AX's job and this gate ignores it; the nagini sibling's two
# to_native probes have no counterpart here because the modeled branch calls
# nothing (`meta.axioms == []`, axioms region empty). See the header.
AXIOM_TESTS = []
