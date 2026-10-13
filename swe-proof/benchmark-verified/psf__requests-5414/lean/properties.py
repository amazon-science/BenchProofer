"""properties.py — G-PBT falsification battery for psf__requests-5414 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds by construction and the single
``theorem correct_validateHost`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the same host-validation step as a PROCEDURE over a half-permission
``List[int]`` input plus two boolean summaries (``host_is_ascii``,
``encodable``), signalling rejection by RAISING and pinning the two rejection
sub-domains in an ``Exsures``. This Lean bundle models the SAME single purely
functional core as a total function ``List Char → Except Unit (List Char)``:
rejection is ``Except.error ()`` (both rejection sites produce the identical
error, so they collapse to one value) and acceptance is ``Except.ok h`` carrying
the host forward. Every nagini rival that attacks a MODELED clause carries over;
the classes that were nagini-specific (frame/permission mutation, termination)
are recorded in ``assessment`` rather than fabricated.

The carrier NARROWS in one direction and WIDENS in another, and both matter:

  * NARROWS: nagini's ``Exsures`` and normal-completion ``Ensures`` are two
    separate obligations over the same routine. Here there is one predicate with
    three leaves, so nagini's "returned normally when it should have raised" and
    "raised when it should have returned" rivals both become "the result value
    disagrees with the spec's value at this host".
  * WIDENS: nagini summarises the host as ONE bit (``host_is_ascii``) plus one
    code point (``host[0]``), and summarises the encoder as one bit
    (``encodable``). Here the whole host is present as a ``List Char`` and the
    encoder is a real function of it. So this bundle can attack things nagini
    structurally could not: an ASCII test that inspects only the FIRST code
    point, an accepted host that is not carried through UNCHANGED, and an
    over-rejection keyed on a reserved character appearing anywhere rather than
    in the leading position. Three rivals below exist only because of that
    widening.

DEFENDED SURFACE (one modeled behavior; ONE spec predicate, THREE leaves).
``problem_spec_validateHost host result`` pins EXACTLY:

  * (L1 ascii/reserved)  ``isAscii host ∧ startsWithInvalid host``
    ⟹ ``result = Except.error ()`` — an all-ASCII host whose leading code point
    is reserved is REJECTED;
  * (L2 ascii/accepted)  ``isAscii host ∧ ¬startsWithInvalid host``
    ⟹ ``result = Except.ok host`` — every other all-ASCII host is accepted and
    carried through UNCHANGED (this is the frame clause: the accepted host is
    pinned to the input value, not merely to "some ok value");
  * (L3 non-ascii)  ``¬isAscii host`` ⟹ ``result = idnaEncode host`` — a host
    with any non-ASCII code point takes the encoder's outcome EXACTLY, in both
    directions (its ok value and its rejection).

Both helper predicates are GROUNDED in the input: ``isAscii`` is a spelled-out
``List.all`` over the code points and ``startsWithInvalid`` is a spelled-out
test on the head. Neither is an opaque answer key an implementation could echo
without doing the work, so the "wrong ungrounded-oracle echo" class is N/A here
exactly as it is in the nagini sibling; its slot is filled by honest positive
controls (``pos-inline-screen`` in particular, which inlines the head test as
its unfolded body and must still verify).

THE BEHAVIOURAL DISCRIMINATOR. The reserved-leading-character screen covers TWO
reserved characters, not one: a wildcard marker and a leading dot that would
introduce an empty leading label. The public issue reports that requesting
``http://.example.com`` currently fails with a low-level encoding error instead
of the intended invalid-label rejection, and the FAIL_TO_PASS test asserts the
invalid-label rejection for exactly that URL. ``rival-star-only`` below is the
pre-fix behavior (screen the wildcard marker only) and ``rival-dot-only`` is its
mirror (screen the leading dot only); the mirror breaks the PASS_TO_PASS case
for the wildcard host, which is why a "fix" in that direction is not a fix.

BINDER STRUCTURE. The spec predicate has exactly ONE input binder, ``host``
(``result`` is the output position). It is load-bearing through FOUR independent
observables — whether every code point is ASCII, what the LEADING code point is,
the host's full value as carried forward, and the value handed to the encoder —
and the reject witnesses move all four: they probe ``[]``, ``['.', 'a']``,
``['*', 'a']``, ``['a', '.', 'b']``, ``['a', 'b']``, ``['a', 'é']``, ``['é']``,
``['ü', 'a']`` and ``['b', 'ü']``, i.e. nine DISTINCT input points (``pts=9``)
spanning all-ASCII/mixed, reserved/non-reserved leading code point, reserved
character in a NON-leading position, non-ASCII in leading vs non-leading
position, and the empty host at the domain boundary. No observable of the single
binder is held fixed across the battery.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — the nagini class is VACUOUS, but its
    OBLIGATION is not, and it is attacked. The nagini sibling's mandatory
    ``frame-mutation`` rival writes to a half-permission input and is rejected
    for insufficient permission. Lean is referentially transparent: ``host`` is
    an immutable value, there is no aliasing and no permission to under-hold, so
    that exact probe cannot be written. What survives the translation is the
    FRAME OBLIGATION in the SPEC_GUIDE §0.5 sense — "when the spec relates a
    result to its inputs, pin the unchanged parts explicitly" — which lives in
    L2 as ``result = Except.ok host`` rather than ``∃ h, result = Except.ok h``.
    ``rival-not-carried-through`` attacks precisely that: it accepts the right
    hosts and rejects the right hosts, and only the VALUE it carries forward
    differs. So the class is re-expressed, not fabricated and not dropped.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, same reasoning as the nagini sibling
    (both helpers are unfolded computations over the input). Positive controls
    stand in its place.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery: rivals
    that agree with the frozen spec on most hosts and diverge exactly where one
    leaf bites.

  * DIVERGENCE / NON-TERMINATION — SPLIT, and the two halves have DIFFERENT
    dispositions. An earlier revision of this manifest recorded the whole class
    as vacuous on the grounds that "an unbounded loop has no spelling in a total
    ``def``". Half of that is right and half was measured WRONG; both halves were
    re-derived with real builds rather than argued.

    - SELF-RECURSION — genuinely VACUOUS, and demonstrated. Replacing the impl
      body with ``implementation_validateHost host`` is refused by Lean's own
      elaborator before the spec is ever consulted: ``fail to show termination
      for implementation_validateHost … no parameters suitable for structural
      recursion``. The variant on a non-fixed argument (``host.reverse``) is
      refused the same way (``failed to eliminate recursive application``). So
      there is no rival to judge and nothing for the spec to admit — the nagini
      ``nonterm-self-recursion`` probe is not expressible.

    - UNBOUNDED LOOP — EXPRESSIBLE, and a KNOWN GAP rather than a vacuous class.
      ``while true do h := h`` inside the existing ``Id.run do`` block DOES
      elaborate as a total ``def`` (Lean routes it through ``Lean.Loop.forIn``,
      whose termination is not the ``def``'s obligation), and the resulting
      variant does NOT verify. So the sibling's ``nonterm-endless-loop`` rival
      HAS a spelling here, contrary to what this manifest previously said.
      It is not shippable, though, for a reason that is itself measured: no
      witness can discriminate it. The loop term is irreducible in the kernel, so
      every refutation attempt failed on BOTH sides with a stuck reduction rather
      than a verdict —
        * literal + ``decide`` / ``decide +kernel``: ``failed to synthesize
          Decidable ¬if false = true then …`` on the rival AND on gold;
        * refutation over the computable projection ``Except.toOption``:
          ``did not reduce to `isTrue` or `isFalse` `` on both;
        * ``simp [implementation_validateHost]``: leaves
          ``¬(forIn Lean.Loop.mk … ).run = ['a','b']`` unsolved on both.
      Conditioning on the impl's own value instead (``implementation_validateHost
      ['a','b'] ≠ Except.ok ['a','b']``) elaborates against the rival AND against
      GOLD (exit 0 both sides) — i.e. it is VACUOUS, which is precisely what the
      gate's second half exists to catch, so it must not be shipped. That is a
      carrier limit on the WITNESS, not a spec hole: the rival is in fact
      rejected. Recorded as a gap so it stays visible; see ``assessment`` in the
      accounting block below. Contrast velvet, where under partial termination
      semantics such an impl VERIFIES (a real spec hole,
      ``the corpus-wide termination-semantics finding``); this bundle's carrier rejects it.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes NOTHING to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that pins the rival's concrete result at one
input, rewrites the spec's branch selectors to their computed values, and closes.
Two witness shapes appear:

  * the ASCII-leaf rivals (L1/L2) refute at literal inputs and bind NOTHING, so
    there are no hypotheses whose consistency could be in question. Both branch
    selectors and the whole body are computable at a literal host, so a term-mode
    ``have himpl ... := rfl`` pins the rival's value and the KERNEL decides it;
  * the non-ASCII-leaf rivals (L3) CONDITION ON THE CARRIER instead of computing
    it. ``idnaEncode`` is ``opaque``, so no literal input decides L3 and
    ``decide`` would get stuck on the opaque term. Each such witness assumes
    exactly ONE inequation about ONE application of that callee — e.g.
    ``idnaEncode ['é'] ≠ Except.ok ['é']`` — which is precisely the sub-domain
    where the rival is wrong, and is a strictly stronger claim than any single
    literal could make. One hypothesis about one term cannot be
    self-contradictory, and each was run through the gate's own
    ``consistency_probe`` (``example <binders> : False``) to confirm ``False`` is
    NOT derivable from it. The opacity that blocks ``decide`` blocks the KERNEL
    too, so these witnesses may NOT pin the rival's value with a ``rfl``: they
    ``cases h : idnaEncode <host>`` FIRST and reduce afterwards, which is what
    makes their gold-side failure depend on WHAT IS CLAIMED rather than on what
    happens to be reducible. That ordering is a MEASURED requirement, not a
    stylistic preference — see FORGERY-CHECKED below and ``_w_idna``.

Every witness below was checked with real ``lake env lean`` builds in BOTH
directions — it elaborates against its rival and FAILS on the frozen solution —
so each is a discriminator that was SEEN to discriminate, not a tautology.

FORGERY-CHECKED. "Fails on gold" is only evidence if the failure TRACKS THE
CLAIM, so each witness was additionally re-derived against a claim-flipping
control: the witness with its ``¬`` dropped (i.e. asserting the frozen solution
is CORRECT at that host) was built on both sides. On every case the flipped claim
fails against the RIVAL too, so no forgery of that shape clears the gate's first
half. The gold-side failure was then shown to be SEMANTIC rather than a tactic
mismatch by pinning gold's actual value at each witness input:

  * the five ASCII-leaf cases (L1/L2, including the empty-host boundary case) —
    ``example : implementation_validateHost <host> = <gold's value> := rfl``
    elaborates against GOLD and FAILS against the rival, so the two impls really
    do compute different values there and the witness's ``himpl … := rfl`` failed
    on gold because the equation is FALSE for gold, not because the term is
    irreducible;
  * the four non-ASCII-leaf cases (L3) FAILED that control as first written, and
    were RE-AUTHORED because of it. Their earlier witnesses pinned the rival's
    value with a term-mode ``have himpl : implementation_validateHost <host> =
    <the rival's constant> := rfl`` (three cases) or split on the WRONG encoder
    application (the mangled-argument case). At a non-ASCII host gold's body is
    blocked on the ``opaque`` encoder, so that step failed on gold WITHOUT EVER
    REACHING THE SPEC — and the failure did not move when the claim did:

      - shipped claim: ``:74:65: error: Type mismatch / rfl / has type /
        ?m.9 = ?m.9 / but is expected to have type /
        implementation_validateHost ['é'] = Except.ok ['é']``;
      - the claim that is TRUE of gold: ``:74:66: error: Type mismatch / rfl /
        has type / ?m.7 = ?m.7 / but is expected to have type /
        implementation_validateHost ['é'] = idnaEncode ['é']``.

    Same tactic, same exit 1, the same content-free ``?m.N = ?m.N``, with only the
    expected type differing — measured for all three ``rfl``-shaped cases
    (``['é']``, ``['ü', 'a']``, ``['a', 'é']``). For the mangled-argument case the
    tactic-mode twin behaved the same way: ``The left-hand side match idnaEncode
    ['b', 'ü'] with … is not definitionally equal to the right-hand side
    Except.ok enc`` was unchanged when the right-hand side was replaced by the
    true-of-gold ``idnaEncode ['b', 'ü']``, because the case split was taken on
    the OTHER application and left gold's blocked. An exit code that does not move
    when the claim is inverted attests nothing, so all four witnesses now split on
    the encoder BEFORE evaluating anything. Re-measured on the manifest's own
    generated text, at each witness's own input:

      - against its RIVAL each still elaborates (exit 0);
      - against GOLD each fails BECAUSE THE SPEC INSTANCE IS DISCHARGED for gold —
        ``Type mismatch / Ne.symm hne / has type / Except.ok ['é'] ≠ Except.ok enc
        / but is expected to have type / ¬True`` (drop-encoder and
        ascii-first-char-only), ``unsolved goals / case ok / … / ⊢ False``
        (reject-all-nonascii), ``… but is expected to have type ¬(match Except.ok
        enc2 with …) = Except.ok enc2`` (encode-mangled-host). The goal COLLAPSED:
        gold's value at that host IS the encoder's outcome, which is the spec's own
        equation. None of the four trips the gate's ``_stuck_screen`` (checked with
        the gate's own predicate), so none is a stuck reduction in a verdict's
        clothing;
      - and the OPPOSITE CLAIM — same binder, same prefix, ``¬`` dropped, i.e.
        asserting the frozen solution IS correct at that host — now BUILDS against
        gold (exit 0) while FAILING against the rival with the RIVAL's own value
        exhibited: ``⊢ Except.ok ['é'] = Except.ok enc``,
        ``⊢ Except.error () = Except.ok enc``,
        ``⊢ Except.ok ['a', 'é'] = Except.ok enc``, ``⊢ enc1 = enc2``.

    So on all nine reject cases the gold-side exit code TURNS ON THE CLAIM, which
    is the whole content of "and it FAILS on the frozen solution".

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
either leaves the reported URL accepted (so the FAIL_TO_PASS invalid-label
assertion still fails) or newly breaks a PASS_TO_PASS host — the wildcard host,
the international hosts that must round-trip, or the ordinary hosts whose
reconstructed network location must be byte-for-byte unchanged.

AXIOM lane: DROPPED. The nagini sibling's two ``AXIOM_TESTS`` probes (soundness
and containment for its encoder abstraction) belong to G-AX, which this gate
ignores; this bundle's encoder is an ``opaque`` callee with no consumed
property axiom, and ``axiom_check.py`` already covers it.
"""
from pathlib import Path

INSTANCE = "psf__requests-5414"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the file (asserted by _swap at import, so the manifest breaks loudly on drift).
# ---------------------------------------------------------------------------

# impl region -------------------------------------------------------------
# The branch selector that routes a host with non-ASCII code points to the
# encoder.
_I_ASCII_TEST = "    if !isAscii host then"
# The whole non-ASCII arm: consult the encoder, keep its accepted host, or
# propagate its rejection.
_I_NONASCII_ARM = """    if !isAscii host then
      match idnaEncode host with
      | Except.ok enc => h := enc
      | Except.error () => return Except.error ()"""
# The reserved-leading-character screen (head line only, and head + body).
_I_SCREEN_HEAD = "    else if startsWithInvalid host then"
_I_SCREEN_ARM = """    else if startsWithInvalid host then
      return Except.error ()"""
# The accepted-host return: what value is carried forward.
_I_CARRY = "    return Except.ok h"
# The entire implementation body, for the shape-changing positive control.
_I_BODY = """  Id.run do
    let mut h := host
    if !isAscii host then
      match idnaEncode host with
      | Except.ok enc => h := enc
      | Except.error () => return Except.error ()
    else if startsWithInvalid host then
      return Except.error ()
    return Except.ok h"""

# proof region ------------------------------------------------------------
# The frozen tactic body, for cases that legitimately re-prove. The
# `theorem correct_validateHost` STATEMENT is NEVER touched by any swap below.
_P_BODY = """  intro host
  unfold problem_spec_validateHost implementation_validateHost
  simp only [Id.run]
  by_cases ha : isAscii host
  · simp only [ha, if_true, Bool.not_true]
    by_cases hs : startsWithInvalid host <;> simp only [hs, if_true] <;> rfl
  · simp only [ha, Bool.not_false]
    cases h : idnaEncode host with
    | ok enc => rfl
    | error e => rfl"""
# The frozen proof's `intro` line, so a ground instance can be prepended as a
# `have` without disturbing the rest of the script.
_P_INTRO = "  intro host\n"


# ---------------------------------------------------------------------------
# Witness scaffolds.
#
# _w_ascii: the ASCII leaves (L1/L2) are fully computable, so the refutation is
#   stated at a LITERAL host. `himpl := rfl` pins the rival's result (this is the
#   half that fails on the frozen solution, since gold computes a different
#   value there), the two branch selectors are rewritten to their computed
#   literals, and `simp` closes on the resulting `Except` constructor clash.
#   Binds nothing => no consistency question.
#
# _w_idna: the non-ASCII leaf (L3) is stated over the `opaque` encoder, so there
#   is no literal to compute and `decide` would get stuck. The refutation is
#   CONDITIONED on the carrier instead: assume exactly one inequation about the
#   one encoder application in play. `hne` says the spec's value at this host
#   differs from the constant the rival produces there, which is exactly the
#   sub-domain where the rival is wrong. The opaque application also blocks the
#   KERNEL, so the script must SPLIT on it (`cases h : idnaEncode <host>`) before
#   it evaluates anything -- that is the step that makes gold's failure depend on
#   what is claimed rather than on what is reducible; see `_w_idna`'s own
#   docstring and FORGERY-CHECKED in the module docstring for the builds.
#
# _r_nonascii: the `simp only` set both impls' bodies reduce under ONCE that
#   split has happened. Shared by `_w_idna` and by the mangled-argument witness,
#   which needs a different SHAPE (two encoder applications) but the same
#   reduction.
# ---------------------------------------------------------------------------
def _w_ascii(host, impl_result, ascii_val, screen_val):
    """Refute an ASCII leaf at a literal host."""
    return (
        f"example : ¬ problem_spec_validateHost {host}\n"
        f"    (implementation_validateHost {host}) := by\n"
        f"  have himpl : implementation_validateHost {host} = {impl_result} := rfl\n"
        "  unfold problem_spec_validateHost\n"
        f"  rw [himpl, show isAscii {host} = {ascii_val} from rfl,\n"
        f"      show startsWithInvalid {host} = {screen_val} from rfl]\n"
        "  simp\n")


def _r_nonascii(host, *extra, indent=0):
    """The `simp only` set that evaluates EITHER impl at this literal host, once a
    `cases` on the encoder has replaced the opaque application by a constructor.

    `Id.run` opens the block, the `show isAscii ... = false from rfl` fact takes
    the non-ASCII branch, the constructor lets the `match` the split unblocked
    iota-reduce, and `bind`/`pure` collapse the block's unit bind to a VALUE.
    `extra` carries the per-case facts a rival's own selector or argument forces
    into the goal (a first-code-point test, a reversed argument). A fact that
    does not apply to one of the two subjects is inert -- the two impls take
    different routes through the same block -- so the linter's "unused simp
    argument" note is expected and does not affect any build's exit code.
    `indent` is the column the emitted block will sit at (continuation lines get
    two more); an arm body passes 0 because `_arm` re-indents the whole block.
    """
    lemmas = ["Id.run", f"show isAscii {host} = false from rfl", *extra,
              "Bool.not_false", "if_true", "bind", "pure"]
    lines, cur = [], "simp only ["
    for i, lem in enumerate(lemmas):
        piece = lem + ("]" if i == len(lemmas) - 1 else ", ")
        if len(cur) + len(piece) + indent > 86 and cur.strip() != "simp only [":
            lines.append(cur.rstrip())
            cur = "  "
        cur += piece
    lines.append(cur.rstrip())
    return ("\n" + " " * (indent + 2)).join(lines)


def _w_idna(host, impl_result, ok_arm, err_arm):
    """Refute the non-ASCII leaf, conditioning on the opaque encoder.

    ONE hypothesis about ONE application of the callee: the encoder's outcome at
    this host is not the constant the rival returns there. Jointly satisfiable by
    construction (a single inequation about a single opaque term), and confirmed
    so by the gate's `consistency_probe`.

    The FIRST tactic step after the `show` is `cases h : idnaEncode <host>`, and
    it is load-bearing rather than cosmetic. `idnaEncode` is `opaque`, so with
    that application left standing NEITHER impl's `do` block reduces and a
    term-mode `rfl` pinning the rival's value fails against gold no matter what
    is claimed -- which is exactly how an earlier revision of these witnesses
    failed on gold, measured in FORGERY-CHECKED. Splitting first replaces the
    encoder by a constructor, after which `_r_nonascii` evaluates the block to a
    VALUE on both sides: gold's value IS the encoder's outcome, so the spec's
    equation becomes `True` and gold fails BECAUSE the spec holds there, while
    the rival's value is its own constant and `hne` closes the goal.

    The `show` step is a pure definitional unfolding of the spec at this leaf
    (the branch selector is computable at a literal host) and holds for ANY
    implementation, so it never decides the outcome either.
    """
    return (
        f"example (hne : idnaEncode {host} ≠ {impl_result}) :\n"
        f"    ¬ problem_spec_validateHost {host} "
        f"(implementation_validateHost {host}) := by\n"
        f"  show ¬ (implementation_validateHost {host} = idnaEncode {host})\n"
        "  unfold implementation_validateHost\n"
        f"  cases h : idnaEncode {host} with\n"
        f"  | ok enc =>\n{_arm(ok_arm)}"
        f"  | error e =>\n{_arm(err_arm)}")


def _arm(block):
    """A tactic-arm body: `block`'s lines placed at column 4."""
    return "".join(f"    {ln}\n" if ln.strip() else "\n"
                   for ln in block.strip("\n").split("\n"))


# The closing steps of an `ok` arm in which the rival's value and the encoder's
# are both `Except.ok`: `hne` is stated about the ENCODER's application, the goal
# about the rival's value, so `h` orients one onto the other.
_FLIP = "rw [h] at hne\nexact Ne.symm hne"

# The mangled-argument witness (rival-encode-mangled-host) cannot use `_w_idna`:
# TWO encoder applications are in play -- the spec's `idnaEncode ['b', 'ü']` and the
# rival's `idnaEncode ['ü', 'b']` -- and the rival's is spelled
# `idnaEncode (['b', 'ü'].reverse)` until the reduction rewrites it, so a `cases`
# taken FIRST silently misses it (measured: the witness then fails against its own
# rival, exit 1, `¬(match idnaEncode ['ü', 'b'] with ...) = Except.ok enc2` still
# standing). The reduction therefore runs first and BOTH applications are then
# split. Three of the four corners are decided by the values; the error/error
# corner is the one where the rival AGREES with the spec (both hand back a
# rejection), so it is closed from `hne` and the two split hypotheses alone.
_W_MANGLED = f"""example (hne : idnaEncode ['ü', 'b'] ≠ idnaEncode ['b', 'ü']) :
    ¬ problem_spec_validateHost ['b', 'ü'] (implementation_validateHost ['b', 'ü']) := by
  show ¬ (implementation_validateHost ['b', 'ü'] = idnaEncode ['b', 'ü'])
  unfold implementation_validateHost
  {_r_nonascii("['b', 'ü']",
               "show (['b', 'ü'] : List Char).reverse = ['ü', 'b'] from rfl",
               indent=2)}
  cases h2 : idnaEncode ['b', 'ü'] with
  | ok enc2 =>
    cases h1 : idnaEncode ['ü', 'b'] with
    | ok enc1 =>
      rw [h1, h2] at hne
      exact hne
    | error e1 => simp
  | error enc2 =>
    cases h1 : idnaEncode ['ü', 'b'] with
    | ok enc1 => simp
    | error e1 => exact absurd (h1.trans h2.symm) hne
"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_validateHost` STATEMENT byte-identical, adds no
    # declaration, and closes the obligation for real. (All three: verified by a
    # real build.)
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-REORDER: test the ASCII case FIRST (the frozen impl tests the
        # negated form first), nest the reserved-leading-character screen inside
        # the ASCII arm, and move the encoder consultation to the else arm, with
        # each arm returning directly instead of threading the mutable host.
        # Behaviourally identical on every host:
        #   ASCII + reserved leading char -> Except.error ()
        #   ASCII + otherwise             -> Except.ok host
        #   any non-ASCII code point      -> the encoder's outcome, both ways
        # A pure control-flow reshape, definitionally equal to the frozen body,
        # so the FROZEN tactic body still closes unchanged.
        "module": _swap(
            _BASE, _I_BODY,
            """  Id.run do
    if isAscii host then
      if startsWithInvalid host then
        return Except.error ()
      return Except.ok host
    else
      match idnaEncode host with
      | Except.ok enc => return Except.ok enc
      | Except.error () => return Except.error ()"""),
        "rationale": "structurally different but CORRECT: branch order flipped "
                     "(ASCII case tested first, the reserved-leading-character "
                     "screen nested in the ASCII arm, the encoder consultation "
                     "moved to the else arm, each arm returning directly rather "
                     "than threading a mutable host). Identical result on every "
                     "host, so all three leaves L1/L2/L3 still hold — must "
                     "verify, else SPEC-TOO-STRONG. Definitionally equal to the "
                     "frozen body, so the FROZEN proof body closes it unchanged; "
                     "statement byte-identical, no new axiom/lemma. Ports "
                     "nagini's pos-control-reorder, whose reshape is the same "
                     "flip expressed over a raising procedure.",
    },
    {
        "id": "pos-inline-screen",
        "kind": "soundness",
        "expect": "verify",
        # Honest cheapest impl: inline the reserved-leading-character predicate
        # as its own unfolded body (a head test against the two reserved code
        # points) instead of calling the named helper. This is the SAME
        # computation, so it must satisfy a postcondition phrased over the named
        # helper. Re-proved: one `have` states the definitional equality of the
        # inlined form with the helper and feeds it to the frozen `simp only`,
        # after which the frozen script closes verbatim.
        "module": _swaps(
            _BASE,
            (_I_SCREEN_HEAD,
             "    else if (match host with | [] => false "
             "| c :: _ => c == '*' || c == '.') then"),
            (_P_BODY,
             """  intro host
  have hsw : (match host with | [] => false | c :: _ => c == '*' || c == '.')
      = startsWithInvalid host := rfl
  unfold problem_spec_validateHost implementation_validateHost
  simp only [Id.run, hsw]
  by_cases ha : isAscii host
  · simp only [ha, if_true, Bool.not_true]
    by_cases hs : startsWithInvalid host <;> simp only [hs, if_true] <;> rfl
  · simp only [ha, Bool.not_false]
    cases h : idnaEncode host with
    | ok enc => rfl
    | error e => rfl"""),
        ),
        "rationale": "honest cheapest impl: the reserved-leading-character "
                     "predicate is INLINED as its unfolded body (head tested "
                     "against the two reserved code points, empty host false) "
                     "rather than called by name — the SAME computation, so it "
                     "must satisfy the postcondition phrased over the named "
                     "helper. This is the positive control standing in for the "
                     "(N/A) ungrounded-oracle slot: the predicate is GROUNDED in "
                     "the host's head, so there is no wrong echo to build — the "
                     "only way to satisfy L1/L2 is to actually perform the head "
                     "test, which this does. Must verify, else SPEC-TOO-STRONG. "
                     "Re-proved by one definitional `have` fed to the frozen "
                     "`simp only`; statement byte-identical, no new axiom/lemma. "
                     "Ports nagini's pos-inline-oracle.",
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        # A different IDIOM, not just a different branch order: drop the
        # imperative `Id.run do` / `let mut` / early-`return` shape entirely and
        # write the same function as a `match` on the ASCII test with two pure
        # arms. Same result on every host. Re-proved (the frozen script's
        # `Id.run` reduction no longer applies) by case analysis on the ASCII
        # test alone.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             """  match isAscii host with
  | false => idnaEncode host
  | true => if startsWithInvalid host then Except.error () else Except.ok host"""),
            (_P_BODY,
             """  intro host
  unfold problem_spec_validateHost implementation_validateHost
  cases ha : isAscii host <;> simp"""),
        ),
        "rationale": "structurally different but CORRECT in a different IDIOM: "
                     "the imperative do-block with a mutable host and early "
                     "returns is replaced by a pure `match` on the ASCII test "
                     "with two functional arms. Identical result on every host, "
                     "so L1/L2/L3 all still hold — must verify, else "
                     "SPEC-TOO-STRONG, which would mean the spec had been "
                     "tailored to the frozen impl's control-flow shape rather "
                     "than to its behavior. Re-proved by case analysis on the "
                     "ASCII test (the frozen `Id.run` reduction no longer "
                     "applies); statement byte-identical, no new axiom/lemma. "
                     "This case has NO nagini counterpart — nagini's carrier is "
                     "a procedure with a raise, so 'same function, non-imperative "
                     "idiom' is not expressible there.",
    },

    {
        "id": "pos-demorgan-selector",
        "kind": "soundness",
        "expect": "verify",
        # A positive control on the BRANCH SELECTOR, which the other three
        # positives leave alone. All three of those reshape the BRANCH BODIES (or
        # the whole idiom) while keeping the selector `!isAscii host` verbatim, so
        # none of them tests whether L3's routing condition was specified
        # behaviourally or transcribed. This one re-expresses the selector by De
        # Morgan — "some code point is NOT ASCII" instead of "not every code point
        # IS ASCII" — which is the same Bool but NOT definitionally equal (the
        # frozen `rfl`-shaped steps do not close it; it needs
        # `List.all_eq_not_any_not`). That is the point: it is the only positive in
        # the battery whose proof the frozen tactic body cannot discharge, so it is
        # the only one that could have caught a spec tailored to the frozen
        # selector's syntactic form.
        "module": _swaps(
            _BASE,
            (_I_ASCII_TEST,
             "    if host.any (fun c => !decide (c.toNat < 128)) then"),
            (_P_BODY,
             """  intro host
  have hsel : host.any (fun c => !decide (c.toNat < 128)) = !isAscii host := by
    unfold isAscii
    simp [List.all_eq_not_any_not]
  unfold problem_spec_validateHost implementation_validateHost
  simp only [Id.run, hsel]
  by_cases ha : isAscii host
  · simp only [ha, if_true, Bool.not_true]
    by_cases hs : startsWithInvalid host <;> simp only [hs, if_true] <;> rfl
  · simp only [ha, Bool.not_false]
    cases h : idnaEncode host with
    | ok enc => rfl
    | error e => rfl"""),
        ),
        "rationale": "structurally different but CORRECT, on the one region the "
                     "other positives do not touch: the BRANCH SELECTOR. The "
                     "routing condition is re-expressed by De Morgan — `host.any "
                     "(fun c => !ascii c)` in place of `!host.all (fun c => ascii "
                     "c)` — which denotes the same Bool but is NOT definitionally "
                     "equal, so unlike pos-branch-reorder the frozen tactic body "
                     "does NOT close it and the case needs a real lemma "
                     "(`List.all_eq_not_any_not`) to re-prove. That is exactly "
                     "why it is here: a spec that had been tailored to the frozen "
                     "selector's SHAPE rather than to which hosts it routes would "
                     "reject this faithful impl, and no other positive in the "
                     "battery would notice. Must verify, else SPEC-TOO-STRONG. "
                     "Statement byte-identical, no new axiom/lemma. Added by the "
                     "audit; no nagini counterpart (nagini receives the ASCII "
                     "verdict as a precomputed bit, so its selector cannot be "
                     "reshaped at all).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at
    # normal, in-domain inputs, in BOTH directions. The frozen theorem carries no
    # precondition hypothesis at all (it is `∀ host, ...`), so nagini's
    # "the Requires admits an F2P-shaped input" probe re-expresses as: discharge
    # the spec predicate by evaluation at a reported-shaped rejecting host AND at
    # an ordinary accepted host, and confirm the implementation actually REACHES
    # both outcomes, then close the frozen obligation verbatim. If the predicate
    # were unsatisfiable at exactly a normal input (the analogue of
    # PRECOND-TOO-STRONG) these `have`s could not close. Nothing is assumed: no
    # new declaration, statement byte-identical, ground instances are `have`s
    # prepended inside the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground-both-outcomes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            """  have _rejected : problem_spec_validateHost ['.', 'e', 'x'] (Except.error ()) := by
    unfold problem_spec_validateHost
    rw [show isAscii ['.', 'e', 'x'] = true from rfl,
        show startsWithInvalid ['.', 'e', 'x'] = true from rfl]
    simp
  have _accepted : problem_spec_validateHost ['e', 'x'] (Except.ok ['e', 'x']) := by
    unfold problem_spec_validateHost
    rw [show isAscii ['e', 'x'] = true from rfl,
        show startsWithInvalid ['e', 'x'] = false from rfl]
    simp
  have _reached : implementation_validateHost ['.', 'e', 'x'] = Except.error ()
      ∧ implementation_validateHost ['e', 'x'] = Except.ok ['e', 'x'] :=
    ⟨rfl, rfl⟩
""" + _P_INTRO),
        "rationale": "the modeled behavior is SATISFIABLE at normal in-domain "
                     "inputs in both directions, and the implementation reaches "
                     "both: the spec predicate is discharged by evaluation at a "
                     "host shaped like the one the public issue reports (all "
                     "ASCII, reserved leading code point -> rejected) and at an "
                     "ordinary accepted host (all ASCII, unreserved leading code "
                     "point -> accepted UNCHANGED), and a third `have` confirms "
                     "the implementation actually produces those two outcomes. "
                     "If either were unsatisfiable the `have` could not close — "
                     "the analogue of PRECOND-TOO-STRONG on a spec whose "
                     "obligation quantifies over ALL hosts with no hypothesis. "
                     "Nothing is assumed: no new declaration, statement "
                     "byte-identical, ground instances are `have`s inside the "
                     "existing tactic body. Ports nagini's "
                     "admissibility-readonly-host (its readable-input half is "
                     "vacuous here — see assessment).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve, and (b) a witness pinning the
    # violation at one concrete input, seen to hold of the rival and to FAIL on
    # the frozen solution.
    # =====================================================================

    # ---- L1: the pre-fix behavior — screen only the wildcard marker ----
    {
        "id": "rival-star-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Screen ONLY the wildcard marker, letting an all-ASCII host with a
        # leading dot be accepted. Agrees with the frozen spec on every other
        # host.
        "module": _swap(
            _BASE, _I_SCREEN_ARM,
            """    else if (match host with | [] => false | c :: _ => c == '*') then
      return Except.error ()"""),
        "refinement": "THIS IS THE PRE-FIX BEHAVIOR — the reserved-leading-"
                      "character screen covers the wildcard marker only, so an "
                      "all-ASCII host beginning with a dot is accepted and "
                      "carried on into network-location reconstruction. On the "
                      "URL the public issue reports (`http://.example.com`) the "
                      "faithful counterpart therefore does NOT produce the "
                      "intended invalid-label rejection, and the FAIL_TO_PASS "
                      "test asserting exactly that rejection for exactly that URL "
                      "still fails. The patch would NOT resolve; this is the "
                      "defect the fix exists to remove.",
        "rationale": "REJECT from L1: at an all-ASCII host whose leading code "
                     "point is a dot, `startsWithInvalid` is true so the spec "
                     "pins `Except.error ()`, but the rival returns "
                     "`Except.ok host`. Refuted at the literal host "
                     "['.', 'a'] — the smallest host of the reported shape. "
                     "Ports nagini's partial-star-only (there the rival returns "
                     "normally where the Ensures demands a raise; here it returns "
                     "the accepting value where the spec demands the rejecting "
                     "one).",
        "witness": _w_ascii("['.', 'a']", "Except.ok ['.', 'a']", "true", "true"),
    },

    # ---- L1: the mirror miss — screen only the leading dot ----
    {
        "id": "rival-dot-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror: screen ONLY the leading dot, letting an all-ASCII host with
        # a leading wildcard marker be accepted. A NEAR-MISS of the opposite
        # sign to rival-star-only, so it gets its OWN witness at the input that
        # distinguishes it (the wildcard host, where star-only agrees with gold).
        "module": _swap(
            _BASE, _I_SCREEN_ARM,
            """    else if (match host with | [] => false | c :: _ => c == '.') then
      return Except.error ()"""),
        "refinement": "the mirror miss: it screens the leading dot but no longer "
                      "screens the wildcard marker, so an all-ASCII host "
                      "beginning with a wildcard is accepted. That host has its "
                      "OWN PASS_TO_PASS assertions — the invalid-URL case for "
                      "`http://*example.com` and the bad-URL cases for "
                      "`http://*` and `http://*.google.com` — all of which "
                      "demand the invalid-label rejection and would newly FAIL. "
                      "So the faithful counterpart trades a fixed test for "
                      "several broken ones and does NOT resolve, even though it "
                      "does handle the reported URL.",
        "rationale": "REJECT from L1, at the OTHER reserved code point: at an "
                     "all-ASCII host whose leading code point is the wildcard "
                     "marker, `startsWithInvalid` is true so the spec pins "
                     "`Except.error ()`, but the rival returns `Except.ok host`. "
                     "Refuted at ['*', 'a'] — deliberately a DIFFERENT input "
                     "point from rival-star-only, since the two rivals agree "
                     "with the frozen spec on each other's witness and a shared "
                     "witness would claim a sub-domain neither demonstrates. "
                     "Ports nagini's partial-dot-only.",
        "witness": _w_ascii("['*', 'a']", "Except.ok ['*', 'a']", "true", "true"),
    },

    # ---- L2: over-rejection — screen the reserved character ANYWHERE ----
    {
        "id": "rival-reserved-anywhere",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-rejection: screen the wildcard marker in leading position but
        # reject a dot occurring ANYWHERE in the host rather than only as the
        # leading code point. Correct on both reserved leading code points;
        # wrong on the ordinary hosts that contain a dot internally.
        # NOT expressible in the nagini sibling, whose only view of the host is
        # its first code point (see the PORT NOTE's "WIDENS" paragraph).
        "module": _swap(
            _BASE, _I_SCREEN_ARM,
            """    else if (match host with | [] => false | c :: _ => c == '*') || host.contains '.' then
      return Except.error ()"""),
        "refinement": "over-rejection keyed on POSITION: the screen fires on a "
                      "reserved character anywhere in the host rather than only "
                      "in the leading position. The faithful counterpart would "
                      "reject essentially every ordinary dotted host name, so the "
                      "PASS_TO_PASS cases that require ordinary URLs to be "
                      "prepared successfully (the plain host round-trip, the "
                      "already-encoded host, the parameter and mutation cases) "
                      "would all newly raise instead — the patch does NOT "
                      "resolve. It is the mirror hazard of the fix: widening the "
                      "screen is correct only in the LEADING position, and a "
                      "spec that did not pin the position would admit this.",
        "rationale": "REJECT from L2: at an all-ASCII host containing a reserved "
                     "character in a NON-leading position, `startsWithInvalid` is "
                     "FALSE so the spec pins `Except.ok host`, but the rival "
                     "returns `Except.error ()`. Refuted at ['a', '.', 'b'] — a "
                     "third distinct input point, and the only one probing the "
                     "reserved character away from the head, which is exactly the "
                     "observable of `host` that separates the screen's position "
                     "sensitivity from mere membership.",
        "witness": _w_ascii("['a', '.', 'b']", "Except.error ()", "true", "false"),
    },

    # ---- L2 (frame): the accepted host is not carried through unchanged ----
    {
        "id": "rival-not-carried-through",
        "kind": "uniqueness",
        "expect": "reject",
        # The FRAME rival (see the PORT NOTE): accepts exactly the right hosts
        # and rejects exactly the right hosts — only the VALUE carried forward on
        # acceptance is altered. This is what nagini's mandatory
        # frame-mutation class becomes on a referentially transparent carrier:
        # the obligation "the unchanged part equals its input value" is real
        # here, it lives in L2, and this rival attacks it directly.
        "module": _swap(_BASE, _I_CARRY, "    return Except.ok h.reverse"),
        "refinement": "the accept/reject DECISION is completely correct here; "
                      "only the host handed onward is not the host that came in. "
                      "A faithful counterpart that rewrote the host while "
                      "validating it would corrupt the network location "
                      "reconstructed from it, so every PASS_TO_PASS case that "
                      "asserts a specific prepared URL — the plain host "
                      "round-trip, the already-encoded host, the bracketed-IPv6 "
                      "hosts, the mutation and parameter cases — would fail on a "
                      "mangled host even though the invalid-label behavior is "
                      "right. The patch does NOT resolve. A spec that said only "
                      "'some accepted value' rather than 'this host' would admit "
                      "this rival, which is exactly the frame hole SPEC_GUIDE "
                      "§0.5 warns about.",
        "rationale": "REJECT from L2, the FRAME conjunct: the spec pins "
                     "`result = Except.ok host` — the input value itself — not "
                     "merely `∃ h, result = Except.ok h`. The rival returns "
                     "`Except.ok host.reverse`, which differs on any "
                     "non-palindromic host. Refuted at ['a', 'b'], a fourth "
                     "distinct point, and the only witness that varies the host's "
                     "VALUE while holding both branch selectors at the accepting "
                     "combination — so it is the only one that could catch a "
                     "rival whose decision logic is perfect. Re-expresses "
                     "nagini's mandatory frame-mutation rival (there: writing to "
                     "a half-permission input; here: not preserving the input "
                     "value in the result).",
        "witness": _w_ascii("['a', 'b']", "Except.ok ['b', 'a']", "true", "false"),
    },

    # ---- L3: drop the encoder consultation entirely ----
    {
        "id": "rival-drop-encoder",
        "kind": "uniqueness",
        "expect": "reject",
        # On the non-ASCII path, skip the encoder and carry the host through
        # unchanged. Correct on every all-ASCII host.
        "module": _swap(
            _BASE, _I_NONASCII_ARM,
            """    if !isAscii host then
      h := host"""),
        "refinement": "drops the encoder consultation on the non-ASCII path, so "
                      "an internationalized host is neither re-encoded nor "
                      "rejected — it is passed through verbatim. The faithful "
                      "counterpart would fail the PASS_TO_PASS cases that require "
                      "international host names to be prepared into their encoded "
                      "form (the several non-ASCII host round-trips), and would "
                      "also stop rejecting the un-encodable international host "
                      "the bad-URL suite expects to be refused — so it would "
                      "regress in both directions and does NOT resolve.",
        "rationale": "REJECT from L3: the spec pins `result = idnaEncode host` "
                     "for any host with a non-ASCII code point, but the rival "
                     "returns the constant `Except.ok host` there, ignoring the "
                     "encoder entirely. CONDITIONED ON THE CARRIER (the encoder "
                     "is opaque, so no literal decides L3): the witness assumes "
                     "the single inequation `idnaEncode ['é'] ≠ Except.ok ['é']` "
                     "— precisely the sub-domain where ignoring the encoder is "
                     "wrong — and derives the contradiction. Refuted at ['é'], a "
                     "fifth distinct point and the first with a non-ASCII code "
                     "point. Ports nagini's control-flow-drop-encoder.",
        "witness": _w_idna(
            "['é']", "Except.ok ['é']",
            _r_nonascii("['é']") + "\n" + _FLIP,
            _r_nonascii("['é']") + "\nsimp"),
    },

    # ---- L3: reject every non-ASCII host outright ----
    {
        "id": "rival-reject-all-nonascii",
        "kind": "uniqueness",
        "expect": "reject",
        # The opposite sign: reject every host with a non-ASCII code point
        # instead of deferring to the encoder. Correct on every all-ASCII host,
        # and correct on the non-ASCII hosts the encoder happens to refuse.
        "module": _swap(
            _BASE, _I_NONASCII_ARM,
            """    if !isAscii host then
      return Except.error ()"""),
        "refinement": "over-rejects in the other direction: every host with a "
                      "non-ASCII code point is refused outright rather than "
                      "offered to the encoder. The faithful counterpart would "
                      "reject the international host names the PASS_TO_PASS "
                      "round-trip cases require to be prepared SUCCESSFULLY into "
                      "their encoded form, so those tests fail — the patch does "
                      "NOT resolve, even though it does reject the reported URL "
                      "(for the wrong reason, and only incidentally). Ports "
                      "nagini's control-flow-always-raise-nonascii, whose "
                      "over-rejection is caught there by the Exsures's "
                      "requirement that a rejection be one of the two permitted "
                      "cases.",
        "rationale": "REJECT from L3, the OPPOSITE direction to "
                     "rival-drop-encoder: the spec pins `result = idnaEncode "
                     "host`, so the encoder's ACCEPTANCES must be honored too, "
                     "but the rival returns the constant `Except.error ()` on "
                     "every non-ASCII host. CONDITIONED ON THE CARRIER: the "
                     "witness assumes the single inequation "
                     "`idnaEncode ['ü', 'a'] ≠ Except.error ()` — the sub-domain "
                     "where blanket rejection is wrong. Refuted at ['ü', 'a'], a "
                     "sixth distinct point, deliberately NOT ['é'] (the two "
                     "rivals fail for opposite reasons and agree with the frozen "
                     "spec wherever the other is wrong, so they must not share a "
                     "witness).",
        "witness": _w_idna(
            "['ü', 'a']", "Except.error ()",
            _r_nonascii("['ü', 'a']") + "\nsimp",
            # the encoder rejected too, so the rival's blanket `Except.error ()`
            # AGREES with the spec here: `hne` and the split are what close it.
            "exact absurd h hne"),
    },

    # ---- L3: the ASCII test inspects only the leading code point ----
    {
        "id": "rival-ascii-first-char-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Route to the encoder based on the LEADING code point alone rather than
        # on all of them, so a host that is ASCII at the head but not later is
        # mis-routed into the ASCII branch and accepted unchanged. Correct on
        # every host whose non-ASCII code points include the first.
        # NOT expressible in the nagini sibling, which receives the ASCII verdict
        # as a single precomputed bit (see the PORT NOTE's "WIDENS" paragraph).
        "module": _swap(
            _BASE, _I_ASCII_TEST,
            "    if !(match host with | [] => true "
            "| c :: _ => decide (c.toNat < 128)) then"),
        "refinement": "mis-routes on the BRANCH SELECTOR rather than inside "
                      "either branch: the decision to consult the encoder is "
                      "taken from the leading code point alone instead of from "
                      "all of them, so a host that begins with an ASCII "
                      "character and continues with a non-ASCII one skips the "
                      "encoder and is passed through verbatim. That is the shape "
                      "of nearly every real international host name, so the "
                      "faithful counterpart would fail the PASS_TO_PASS "
                      "international round-trip cases (their hosts all begin with "
                      "an ASCII letter and carry the non-ASCII code point later) "
                      "— the patch does NOT resolve.",
        "rationale": "REJECT from L3 via the branch selector: `isAscii` quantifies "
                     "over EVERY code point, so a host that is ASCII only at the "
                     "head still takes the encoder leaf, where the spec pins "
                     "`result = idnaEncode host`; the rival returns "
                     "`Except.ok host`. CONDITIONED ON THE CARRIER: the witness "
                     "assumes `idnaEncode ['a', 'é'] ≠ Except.ok ['a', 'é']`. "
                     "Refuted at ['a', 'é'], a seventh distinct point and the "
                     "only one where the non-ASCII code point is NOT leading — "
                     "the observable of `host` that no other witness moves, and "
                     "the one this rival exists to abuse. This case has NO nagini "
                     "counterpart: nagini receives the ASCII verdict as a "
                     "precomputed boolean, so a rival cannot compute it wrongly "
                     "there.",
        "witness": _w_idna(
            "['a', 'é']", "Except.ok ['a', 'é']",
            # this rival routes on the FIRST code point, so its own selector and
            # the screen it then reaches are in the goal as well.
            _r_nonascii("['a', 'é']",
                        "show decide ('a'.toNat < 128) = true from rfl",
                        "show startsWithInvalid ['a', 'é'] = false from rfl",
                        "Bool.not_true", "Bool.false_eq_true", "if_false") + "\n" + _FLIP,
            _r_nonascii("['a', 'é']",
                        "show decide ('a'.toNat < 128) = true from rfl",
                        "show startsWithInvalid ['a', 'é'] = false from rfl",
                        "Bool.not_true", "Bool.false_eq_true", "if_false") + "\nsimp"),
    },

    # ---- L2 (boundary): the EMPTY host is rejected ----
    {
        "id": "rival-reject-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The screen's empty-list arm is flipped from `false` to `true`, so the
        # empty host is rejected instead of accepted. Agrees with the frozen spec
        # on every NON-empty host, in both leaves and both directions — the
        # divergence is at exactly one input, and it is the one input no other
        # witness in this battery visits. Added by the audit: every pre-existing
        # rival differs from gold on hosts of length >= 1, so the empty host was
        # the single un-probed point of the one input binder, and a rival that got
        # only that case wrong would have slipped through unnoticed.
        "module": _swap(
            _BASE, _I_SCREEN_ARM,
            """    else if (match host with | [] => true | c :: _ => c == '*' || c == '.') then
      return Except.error ()"""),
        "refinement": "flips the screen's decision on the EMPTY host only. A "
                      "faithful counterpart would refuse a URL whose parsed host "
                      "is empty with the invalid-label error, at a point where the "
                      "surrounding preparation logic has already decided how an "
                      "empty host is to be handled and is relying on this step to "
                      "pass it through. The reported URL is unaffected (its host "
                      "is non-empty), so the FAIL_TO_PASS assertion is untouched, "
                      "while the PASS_TO_PASS cases that drive an empty-host URL "
                      "to its own distinct outcome would newly get the "
                      "invalid-label rejection instead — a different exception "
                      "from a different site, which is what those cases pin. So "
                      "it regresses without fixing anything: the patch does NOT "
                      "resolve.",
        "rationale": "REJECT from L2 at the DOMAIN BOUNDARY: the frozen spec has "
                     "no precondition — it quantifies over ALL hosts including the "
                     "empty one — and `startsWithInvalid []` is FALSE by the "
                     "helper's own `[] => false` arm, so L2 pins `Except.ok []`. "
                     "The rival returns `Except.error ()` there. Refuted at the "
                     "literal empty host, an EIGHTH distinct input point and the "
                     "shortest one: length 0, which no other witness in the "
                     "battery reaches (all seven others probe length 1-3). This "
                     "is the case that makes the `∀ host` in the obligation "
                     "load-bearing at its edge rather than only on its interior. "
                     "No nagini counterpart: that carrier EXCLUDES the empty host "
                     "by a `len(host) > 0` Requires, so the input this rival is "
                     "wrong at is out of contract there and cannot be attacked.",
        "witness": _w_ascii("([] : List Char)", "Except.error ()", "true", "false"),
    },

    # ---- L3 (frame): the encoder is consulted on a MANGLED host ----
    {
        "id": "rival-encode-mangled-host",
        "kind": "uniqueness",
        "expect": "reject",
        # The L3 FRAME rival, and the mirror of rival-not-carried-through one leaf
        # over. It consults the encoder — so it cannot be caught by
        # rival-drop-encoder's or rival-reject-all-nonascii's witnesses, both of
        # which key on the encoder being IGNORED — but feeds it the REVERSED host.
        # Added by the audit: L3 pins `result = idnaEncode host`, i.e. the
        # encoder's outcome AT THIS HOST, and no pre-existing rival attacks the
        # ARGUMENT position. A rival that consults the right callee on the wrong
        # value satisfies "defers to the encoder" while violating the clause.
        "module": _swap(
            _BASE, _I_NONASCII_ARM,
            """    if !isAscii host then
      match idnaEncode host.reverse with
      | Except.ok enc => h := enc
      | Except.error () => return Except.error ()"""),
        "refinement": "the encoder IS consulted and its outcome IS honored in both "
                      "directions — only the host handed to it is not the host "
                      "that came in. A faithful counterpart that normalised or "
                      "re-ordered the host before encoding it would encode a "
                      "DIFFERENT name than the one requested, so the "
                      "PASS_TO_PASS cases that require each international host to "
                      "be prepared into ITS OWN encoded form would fail on a "
                      "wrong-but-well-formed encoded host, and the un-encodable "
                      "international host the bad-URL suite expects to be refused "
                      "could be accepted (its reversal need not be un-encodable). "
                      "The reported URL is all-ASCII and unaffected, so nothing is "
                      "fixed either — the patch does NOT resolve.",
        "rationale": "REJECT from L3, the ARGUMENT position, which no other rival "
                     "attacks: the spec pins `result = idnaEncode host` — the "
                     "encoder applied to THIS host — and the rival returns "
                     "`idnaEncode host.reverse`. It therefore defers to the "
                     "encoder in both directions and is invisible to the two "
                     "existing L3 witnesses, which both key on the encoder being "
                     "ignored or short-circuited. This is the L3 analogue of "
                     "rival-not-carried-through: same frame obligation, one leaf "
                     "over. CONDITIONED ON THE CARRIER (the encoder is opaque, so "
                     "no literal decides L3): the witness assumes the single "
                     "inequation `idnaEncode ['ü', 'b'] ≠ idnaEncode ['b', 'ü']`, "
                     "i.e. that the encoder is not reversal-invariant at this "
                     "host, which is exactly the sub-domain where mangling the "
                     "argument is wrong. One inequation between two applications "
                     "of one opaque callee cannot be self-contradictory, and the "
                     "gate's consistency_probe confirms `False` is not derivable "
                     "from it. Refuted at ['b', 'ü'], a NINTH distinct input "
                     "point, deliberately not reusing ['a', 'é'] (which "
                     "rival-ascii-first-char-only already owns) so that neither "
                     "case claims a sub-domain the other demonstrates.",
        "witness": _W_MANGLED,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals) plus 2 AXIOM_TESTS. This
# bundle models the SAME single purely-functional core, so 8 of the 10 sibling
# cases carry over; 1 cannot be written on a total, referentially transparent
# carrier, 1 can be written but not witnessed, and both are recorded as such.
# Six cases are ADDED, each exploiting an observable this carrier exposes and
# nagini's does not. Every sibling case is accounted for below.
#
#   sibling case                          -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder                   -> pos-branch-reorder          PORTED
#   pos-inline-oracle                     -> pos-inline-screen           PORTED
#   admissibility-readonly-host           -> admiss-ground-both-outcomes RE-EXPRESSED
#   frame-mutation-write-host             -> rival-not-carried-through   RE-EXPRESSED
#   partial-star-only                     -> rival-star-only             PORTED
#   partial-dot-only                      -> rival-dot-only              PORTED
#   control-flow-drop-encoder             -> rival-drop-encoder          PORTED
#   control-flow-always-raise-nonascii    -> rival-reject-all-nonascii   PORTED
#   nonterm-self-recursion                -> (none)                      VACUOUS
#   nonterm-endless-loop                  -> (none)                      GAP (unwitnessable)
#   (none)                                -> pos-pure-functional         ADDED
#   (none)                                -> pos-demorgan-selector       ADDED (audit)
#   (none)                                -> rival-reserved-anywhere     ADDED
#   (none)                                -> rival-ascii-first-char-only ADDED
#   (none)                                -> rival-reject-empty          ADDED (audit)
#   (none)                                -> rival-encode-mangled-host   ADDED (audit)
#   AXIOM_TESTS (2)                       -> (none)                      DROPPED (G-AX)
#
# RE-EXPRESSED (admiss-ground-both-outcomes): the sibling's admissibility case
#   re-derives, in-region, that a half-permission input is READABLE and that the
#   `len(host) > 0` precondition is usable, then reaches a normal return. Both
#   halves change here. There is no permission to hold (nothing to re-derive
#   about readability), and the frozen obligation carries NO precondition
#   hypothesis at all — it is `∀ host, ...`, with the empty host handled by the
#   spec rather than excluded by a Requires. So the honest analogue is the
#   surviving half: discharge the predicate by evaluation at normal in-domain
#   inputs in BOTH directions and confirm the implementation reaches both
#   outcomes.
# RE-EXPRESSED (rival-not-carried-through): the sibling's MANDATORY
#   frame-mutation rival writes to a read-only input and is rejected for
#   insufficient permission. That probe has no spelling here — no permissions, no
#   aliasing, no mutable input. But the frame OBLIGATION does survive, as
#   SPEC_GUIDE §0.5's "pin the unchanged parts explicitly", and it is load-bearing
#   in L2 (`result = Except.ok host`, not `∃ h, result = Except.ok h`). So rather
#   than declaring the class vacuous, the port attacks the surviving obligation
#   with a rival whose decision logic is flawless and whose only defect is the
#   value it carries forward.
# ADDED (6 cases), each attacking a real load-bearing clause of the SAME modeled
#   spec, none fabricated for an unmodeled behavior. Three came from the port;
#   three (marked AUDIT) were added by the independent audit of this battery,
#   which found each of the three clause positions below un-probed:
#   * pos-pure-functional — a second, stronger positive control. The sibling's
#     positives both keep the imperative procedure shape (its carrier has no
#     other); here the whole idiom can change, which tests that the spec was
#     written against the BEHAVIOR and not against the frozen impl's control flow.
#   * pos-demorgan-selector (AUDIT) — the only positive whose proof the FROZEN
#     tactic body cannot discharge. The port's three positives all reshape the
#     branch BODIES or the idiom while keeping the selector `!isAscii host`
#     verbatim, so all three are definitionally equal to the frozen body on the
#     routing decision and none of them could have detected a spec tailored to the
#     selector's syntactic form. This one re-expresses the selector by De Morgan
#     (same Bool, NOT defeq) and must re-prove with `List.all_eq_not_any_not`.
#   * rival-reserved-anywhere — attacks L2 through the screen's POSITION
#     sensitivity. Nagini's carrier hands the rival only `host[0]`, so
#     "reserved character somewhere else in the host" is not expressible there;
#     on this carrier the whole host is present and the over-rejection is the
#     mirror hazard of the fix itself.
#   * rival-ascii-first-char-only — attacks L3 through the BRANCH SELECTOR.
#     Nagini receives the ASCII verdict as a precomputed boolean parameter, so no
#     rival can compute it wrongly there; here `isAscii` is a real quantification
#     over the host and a rival can under-approximate it.
#   * rival-reject-empty (AUDIT) — attacks L2 at the DOMAIN BOUNDARY. Every one of
#     the port's seven rivals differs from gold only on hosts of length >= 1, so
#     the empty host — the one input the frozen `∀ host` obligation covers and no
#     witness visited — was unattacked. Nagini cannot host this rival at all: its
#     `len(host) > 0` Requires puts the input out of contract.
#   * rival-encode-mangled-host (AUDIT) — attacks L3 in the ARGUMENT position.
#     L3 pins `result = idnaEncode host`; the port's two L3 rivals both key on the
#     encoder being IGNORED, so a rival that consults the right callee on the
#     WRONG value satisfied every existing witness while violating the clause.
# VACUOUS (nonterm-self-recursion): DEMONSTRATED, not asserted. Replacing the impl
#   body with `implementation_validateHost host` (or `... host.reverse`) is refused
#   by Lean's own elaborator before the spec is consulted — `fail to show
#   termination … no parameters suitable for structural recursion` / `failed to
#   eliminate recursive application`. There is no rival to judge, so nothing for
#   the spec to admit.
# GAP (nonterm-endless-loop): EXPRESSIBLE but UNWITNESSABLE, which is a gap and
#   not a vacuous class. `while true do h := h` inside the existing `Id.run do`
#   block DOES elaborate as a total `def` — Lean routes it through
#   `Lean.Loop.forIn`, whose termination is not this `def`'s obligation — and the
#   variant does NOT verify, so the spec does reject it. But no witness can attest
#   to that rejection: the loop term is kernel-irreducible, so a literal `decide`,
#   `decide +kernel`, a refutation over the computable `Except.toOption`
#   projection, and `simp [implementation_validateHost]` all fail IDENTICALLY on
#   the rival and on gold (stuck `Decidable` synthesis / `did not reduce to
#   isTrue or isFalse` / an unsolved `forIn Lean.Loop.mk` goal), while a witness
#   conditioned on the impl's own value elaborates against BOTH (exit 0 each side)
#   and is therefore VACUOUS — exactly what the gate's second half rejects. So the
#   case is not shippable and the class is recorded as a KNOWN GAP in the witness
#   carrier, NOT as a spec hole (the spec is fine here) and NOT as vacuous (the
#   rival exists). This is still the opposite disposition from velvet, where under
#   `set_option loom.semantics.termination "partial"` such an impl VERIFIES — a
#   real spec hole recorded in `the corpus-wide termination-semantics finding` (measured: all 401
#   `partial` bundles admit it, all 99 `total` bundles reject it). This bundle's
#   carrier is total and rejects it.
#
# POINT SPREAD. The nine reject witnesses probe nine DISTINCT hosts (pts=9).
# The spec predicate has ONE input binder, so the invariant that matters is that
# every OBSERVABLE of it is moved:
#   host                 case                          leaf  observable probed
#   []                   rival-reject-empty            L2    the EMPTY host (len 0)
#   ['.', 'a']           rival-star-only               L1    leading dot
#   ['*', 'a']           rival-dot-only                L1    leading wildcard
#   ['a', '.', 'b']      rival-reserved-anywhere       L2    reserved, NON-leading
#   ['a', 'b']           rival-not-carried-through     L2    the host's VALUE
#   ['é']                rival-drop-encoder            L3    non-ASCII, leading
#   ['ü', 'a']           rival-reject-all-nonascii     L3    non-ASCII, leading
#   ['a', 'é']           rival-ascii-first-char-only   L3    non-ASCII, NON-leading
#   ['b', 'ü']           rival-encode-mangled-host     L3    the encoder's ARGUMENT
# Across them: all-ASCII and mixed hosts; reserved and unreserved leading code
# points; both reserved code points individually; a reserved code point in a
# non-leading position; a non-ASCII code point in leading AND in non-leading
# position; the empty host; lengths 0, 1, 2 and 3. All three leaves are attacked
# (L1 twice, L2 three times, L3 four times), each in both directions where the
# leaf has two (L1 under-rejection at each reserved code point; L2 both an
# over-rejection away from the head and an over-rejection at the empty host; L3 a
# dropped consultation, a blanket rejection, a mis-routed selector and a mangled
# argument). Both FRAME positions are attacked — the result value carried forward
# (L2) and the value handed to the callee (L3). No observable of `host` is held
# fixed across the battery, so no rival that mishandled only one of them could
# slip through unnoticed.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores it.
# The sibling's two probes (soundness + containment for its encoder abstraction)
# have a counterpart in this bundle's `axiom_check.py`; here the encoder is an
# `opaque` callee used identically in spec and impl with NO consumed property
# axiom, so the proof assumes nothing about it and there is no axiom strength to
# probe from this lane.
AXIOM_TESTS = []
