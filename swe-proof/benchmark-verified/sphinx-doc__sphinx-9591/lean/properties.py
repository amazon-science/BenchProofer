# properties.py — G-PBT falsification battery (spec lane) for
# sphinx-doc__sphinx-9591, lean backend.
#
# NOT a Lean file. A manifest the G-PBT runner parses: each SPEC_TESTS entry is a
# FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# `impl` region and the `proof` region body differ, so markers.same_spec holds by
# construction and every `theorem correct_*` keeps its exact statement). Each
# reject case additionally carries a `witness`: a Lean snippet, checked in a copy
# of the file with the proof obligations removed, that PROVES the rival violates
# the spec at one concrete input.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE
#
#   implementation_propertyTypeAnnotation
#       {Node : Type} (mkText : String → Node)
#       (crossRefParser : String → List Node) (typ : String) : List Node
#
#   The modeled behavior is the ORDERED LIST OF INLINE CHILDREN that a
#   documented property's type annotation contributes to its signature. Two
#   renderings are possible for the text after the separator: one inert run of
#   plain text carrying the whole `": " ++ typ`, or the separator as its own
#   plain-text node followed by the nodes the type-parsing step yields (in which
#   type names become navigable cross-reference-aware nodes). The frozen spec
#   pins the second.
#
#   The single obligation is `theorem correct_propertyTypeAnnotation`, over the
#   postcondition
#
#     problem_spec_propertyTypeAnnotation mkText crossRefParser typ result :=
#       (C1)  (typ ≠ "" → result = mkText ": " :: crossRefParser typ)
#     ∧ (C2)  (typ = ""  → result = [])
#
#   C1 is a CONJUNCTION of three independent structural facts about the
#   present-type sub-domain, each separately attackable:
#     (C1a) the HEAD is the plain-text node built from the separator string `": "`
#           — not a parsed node, and not a different separator string;
#     (C1b) the TAIL is exactly the parsing step's output for `typ` — the parsed
#           nodes are spliced in, not discarded;
#     (C1c) the ORDER is head-then-tail, and the parsing step is applied to `typ`
#           itself (not to some other string).
#   C2 pins the no-declared-type sub-domain to the empty children list.
#
#   FRAMING (spec_guide §5, the referentially-transparent analogue of a frame
#   condition): NO output component is left free. In the present-type case the
#   head is pinned to the separator node and the tail to the parser's output; in
#   the absent case the whole list is pinned to `[]`. That is what makes the
#   uniqueness lane expressible at all: a rival cannot put anything anywhere in
#   the result without contradicting a pinned component.
#
#   CARRIER NOTE — why this surface is refutable at literal inputs. `Node` is a
#   universally-quantified type and `mkText` / `crossRefParser` are universally
#   quantified functions, so the spec is stated over parameters with no
#   computable content. But a ∀-quantified parameter is not an opaque term: a
#   witness may INSTANTIATE it. Each reject witness below instantiates the node
#   carrier to `String` (implicitly, by annotating the separator factory's
#   argument) with concrete `mkText` / `crossRefParser` functions, at which point
#   the whole relation is a decidable list-of-strings equation and `decide` closes
#   the refutation. Instantiating a ∀-binder is sound in the refutation direction:
#   the frozen spec is claimed for EVERY `Node`/`mkText`/`crossRefParser`, so
#   exhibiting one instantiation where the rival's result differs from the pinned
#   value refutes the rival's contract outright.
#
#   NO precondition is carried in the obligation's binder (`typ` is unrestricted
#   and both sub-domains are pinned), so there is no PRECOND-TOO-STRONG surface
#   beyond the satisfiability probe the admissibility case exhibits.
#
# F2P: the failing test asserts that a documented property whose declared type is
#      a simple name renders its annotation as the separator text followed by a
#      NAVIGABLE cross-reference for the type, rather than as one inert text run.
# P2P: ordinary signature rendering and existing cross-reference resolution must
#      keep working, and a property with NO declared type must gain no annotation
#      fragment at all.
#
# ---------------------------------------------------------------------------
# PORTED FROM the nagini sibling (its case ids in parentheses); see `assessment`
# in the submitted payload for the omissions and their reasons.
#   pos-hoisted-construction   <- pos-local-reorder
#   pos-early-return           <- pos-direct-fabrication (re-aimed; see below)
#   admiss-annotation-shapes   <- admiss-type-str
#   type-as-inert-text         <- type-as-inert-text  (the load-bearing one)
#   separator-parsed-not-text  <- separator-as-xref
#   wrong-separator-text       <- wrong-separator-text
#   parse-wrong-argument       <- wrong-type-text
#   emit-when-absent           <- emit-when-absent
#   parsed-nodes-discarded     <- (new; splits C1b off from C1a)
#   separator-appended-last    <- (new; isolates C1c ordering)
#   corrupt-type-string        <- frame-typ-write (behavioral image; see below)
#
# OMISSION ACCOUNTING. Exactly one nagini case has no counterpart above, and only
# HALF of it is inexpressible here:
#   frame-typ-write — nagini rejected this by the PERMISSION SYSTEM (writing the
#   read-only `typ` input needs full permission where only a half share is held).
#   That mechanism has no image on this carrier: `typ : String` is an immutable
#   value parameter, there is no permission algebra to violate, and no frame
#   condition to restate — so the PERMISSION probe is genuinely inexpressible.
#   Its BEHAVIORAL content is not. What nagini's own refinement describes is a
#   rival that corrupts the declared type string before rendering it, and that is
#   an ordinary value-level rival here; `corrupt-type-string` below carries it.
#   Recording the case as simply "dropped, no permission system" would have
#   retired the mechanism AND the behavior together, which is the part that would
#   have been a real loss of coverage.

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9591"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The FROZEN impl body and FROZEN proof body. Both anchors lie entirely inside
# the region they name (impl / proof) and are unique in the file, so every
# variant below is same_spec-clean by construction and the manifest breaks loudly
# (AssertionError at import) if the frozen solution ever drifts.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    let annotations := crossRefParser typ
    children := mkText ": " :: annotations
  return children"""

_GOLD_PROOF = """  intro Node mkText crossRefParser typ
  unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [Id.run, if_pos h]
    rfl
  · subst h
    rfl"""

assert _BASE.count(_GOLD_IMPL) == 1, "drift: frozen impl body"
assert _BASE.count(_GOLD_PROOF) == 1, "drift: frozen proof body"


# ===========================================================================
# SOUNDNESS POSITIVES — structurally different but CORRECT impls, each with a
# proof that actually closes for the NEW impl shape. The `theorem
# correct_propertyTypeAnnotation` STATEMENT is byte-identical in both; only the
# tactic body may move, and neither reaches for a helper lemma or a weakened
# obligation. If either failed to verify the spec would be SPEC-TOO-STRONG:
# rejecting a faithful correct implementation of the modeled behavior.
# ===========================================================================

# --- P1 HOISTED CONSTRUCTION ------------------------------------------------
# Build both pieces (the parsed nodes and the separator node) into locals BEFORE
# the guard, then assemble inside it. The parsing step is now evaluated
# unconditionally — harmless here, since the modeled parsing step is a total
# function of the type string and the assembled value is unchanged. This is the
# port of nagini's pos-local-reorder: the same "reshape only the order in which
# independent locals are constructed, keep the assembled order" move, re-aimed at
# the Lean carrier (locals hoisted out of the branch rather than reordered inside
# it, because the Lean impl has one assignment where nagini had two appends).
_P1_IMPL = """  let annotations := crossRefParser typ
  let sep := mkText ": "
  let mut children : List Node := []
  if typ ≠ "" then
    children := sep :: annotations
  return children"""
POS_HOISTED = _swap(_BASE, _GOLD_IMPL, _P1_IMPL)

# --- P2 EARLY RETURN + LIST APPEND -----------------------------------------
# Invert the guard into an early `return []` for the absent case, and assemble
# the present case with a singleton-append `[mkText ": "] ++ annotations` instead
# of a cons. Three independent reshapings at once (branch polarity, control flow,
# and the list-building operator), all observationally equal to the frozen impl.
# This is the port slot of nagini's pos-direct-fabrication, RE-AIMED: see the
# `rationale` for why the nagini case's own content does not exist on this
# carrier.
_P2_IMPL = """  if typ = "" then
    return []
  let annotations := crossRefParser typ
  return [mkText ": "] ++ annotations"""
_P2_PROOF = """  intro Node mkText crossRefParser typ
  unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
  refine ⟨fun h => ?_, fun h => ?_⟩
  · simp only [Id.run, if_neg h]
    rfl
  · subst h
    rfl"""
POS_EARLY_RETURN = _swap(_swap(_BASE, _GOLD_IMPL, _P2_IMPL),
                         _GOLD_PROOF, _P2_PROOF)


# ===========================================================================
# ADMISSIBILITY — the pinned relation must be SATISFIABLE on both sub-domains
# the modeled behavior distinguishes. Two anonymous `example`s are appended
# INSIDE the impl region (so same_spec still holds and no new named
# theorem/lemma is declared): one exhibits a result satisfying the relation for
# a declared simple type name (the shape the failing test feeds), the other for
# the no-declared-type case. Each is proved by discharging the RELEVANT arm and
# discharging the other arm's hypothesis as impossible — so neither example can
# be closed by vacuity of both arms. If these could not be built the
# postcondition would be unsatisfiable on the very inputs the behavior is about.
# ===========================================================================
_ADMISS_IMPL = _GOLD_IMPL + """

-- ADMISSIBILITY PROBE (impl region only; no new named declaration). The pinned
-- relation is exhibited as SATISFIED on both sub-domains it distinguishes: a
-- documented simple type name, and no declared type at all.
example : problem_spec_propertyTypeAnnotation (Node := String)
    (fun s => s) (fun s => ["<" ++ s ++ ">"]) "str" [": ", "<str>"] := by
  unfold problem_spec_propertyTypeAnnotation
  refine ⟨fun _ => rfl, fun h => absurd h (by decide)⟩

example : problem_spec_propertyTypeAnnotation (Node := String)
    (fun s => s) (fun s => ["<" ++ s ++ ">"]) "" [] := by
  unfold problem_spec_propertyTypeAnnotation
  refine ⟨fun h => absurd h (by decide), fun _ => rfl⟩"""
ADMISS = _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL)


# ===========================================================================
# UNIQUENESS / REJECT rivals.
#
# Each rival edits ONLY the impl body; the frozen proof body is carried over
# verbatim, so the recorded rejection is a real "this impl does not satisfy the
# obligation" and never a rewritten obligation. Because the frozen tactic script
# is tuned to the frozen impl's syntactic shape, "the build failed" alone would
# NOT attribute the rejection to the spec — so every rival below ships a
# `witness` that was BUILT BOTH WAYS by hand: it elaborates against the rival
# (so the rival provably contradicts the spec) and FAILS against the frozen
# solution (so it is a discriminator, not a tautology).
#
# All witnesses instantiate the node carrier to `String` with concrete `mkText` /
# `crossRefParser` and state `¬ problem_spec_… … (implementation_… …)` at a
# literal `typ`, closed by `simp only [Id.run]; decide`. No witness binds a
# hypothesis, so none can be a contradictory-assumption forgery.
#
# Witness input points are deliberately SPREAD across every input binder rather
# than reusing one probe: `typ` takes seven distinct values (including the empty
# string), `mkText` takes the identity, a prefixing and a bracketing shape, and
# `crossRefParser` takes shapes that are argument-DEPENDENT and constant, of
# length one and length two. A binder every witness held fixed would be a binder
# no rival was built to abuse.
# ===========================================================================


def _witness(mk, cr, typ):
    """`¬ spec … (impl …)` at a literal input, decided after `Id.run` unfolds.

    The node carrier is instantiated to `String` IMPLICITLY, by annotating the
    separator factory's argument (`fun (s : String) => …`) and letting Lean infer
    `Node` from it, rather than by passing `(Node := String)` explicitly. Both
    elaborate identically, but the explicit named argument makes the applied
    argument list one longer than the spec predicate's binder list, and a
    coverage reader that aligns witness arguments to those binders positionally
    cannot then line them up — every witness parses as "unreadable" and the
    per-input-point coverage check silently degrades to a by-name one. Keeping
    the applied arguments in exact 1:1 correspondence with the declared binders
    is what lets the binder-variation check actually run.
    """
    return f"""example : ¬ problem_spec_propertyTypeAnnotation
    ({mk}) ({cr}) {typ}
    (implementation_propertyTypeAnnotation ({mk}) ({cr}) {typ}) := by
  unfold problem_spec_propertyTypeAnnotation implementation_propertyTypeAnnotation
  simp only [Id.run]
  decide"""


# --- W1 TYPE RENDERED AS ONE INERT TEXT RUN (the load-bearing discriminator) -
# Emit a SINGLE plain-text node carrying the whole `": " ++ typ` run and discard
# the parsing step's output entirely. This is the modeled image of the behavior
# the issue reports: the declared type is shown but never becomes navigable.
# Violates C1 on both the head (a one-element list whose element is the
# concatenated run, not the bare separator node) and the tail (the parsed nodes
# are absent).
_W1_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    children := [mkText (": " ++ typ)]
  return children"""
TYPE_INERT = _swap(_BASE, _GOLD_IMPL, _W1_IMPL)
_W1_WITNESS = _witness('fun (s : String) => s', 'fun s => ["<" ++ s ++ ">"]', '"str"')

# --- W2 SEPARATOR ROUTED THROUGH THE PARSING STEP (C1a, head kind) ----------
# The parsed nodes are correctly spliced in and in the right order, but the
# separator is produced by the PARSING step applied to `": "` instead of by the
# plain-text-node factory. The separator would become a parsed/navigable node
# rather than the inert run it must be. Correct on the tail, wrong only on the
# head's provenance — the exact inert-vs-parsed distinction a text-only proxy
# would miss (the port of nagini's separator-as-xref).
_W2_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    let annotations := crossRefParser typ
    children := crossRefParser ": " ++ annotations
  return children"""
SEP_PARSED = _swap(_BASE, _GOLD_IMPL, _W2_IMPL)
_W2_WITNESS = _witness('fun (s : String) => "text[" ++ s ++ "]"',
                       'fun s => ["xref[" ++ s ++ "]"]', '"int"')

# --- W3 WRONG SEPARATOR STRING (C1a, head value) ----------------------------
# Head is built by the right factory and the tail is right; only the separator
# string is one character short (the trailing space is dropped), so the type
# would render flush against the colon. Near-miss on C1a's VALUE rather than its
# kind, which is why it gets its own witness input rather than sharing W2's.
_W3_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    let annotations := crossRefParser typ
    children := mkText ":" :: annotations
  return children"""
WRONG_SEP = _swap(_BASE, _GOLD_IMPL, _W3_IMPL)
_W3_WITNESS = _witness('fun (s : String) => s', 'fun s => [s]', '"Point"')

# --- W4 PARSING STEP APPLIED TO THE WRONG STRING (C1c, argument) ------------
# Head correct, tail produced by the right step, order right — but the step is
# applied to the separator string instead of to the declared type, so the
# navigable node would target the wrong thing. Attacks the ARGUMENT rather than
# the result: refutable because the two calls are distinguishable under any
# parser shape that is not constant, which the witness instantiates.
_W4_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    let annotations := crossRefParser ": "
    children := mkText ": " :: annotations
  return children"""
PARSE_WRONG_ARG = _swap(_BASE, _GOLD_IMPL, _W4_IMPL)
_W4_WITNESS = _witness('fun (s : String) => "t" ++ s', 'fun s => [s ++ "!"]', '"T"')

# --- W5 PARSED NODES DISCARDED (C1b, tail) ---------------------------------
# The parsing step still RUNS (so a proxy that only checks "was the step
# reached" is satisfied) but its output is thrown away: only the separator node
# is emitted. Head correct, order vacuously correct, tail empty. Splits C1b off
# from C1a, which W1 attacks jointly — so a rival wrong only about the tail is
# demonstrated to be caught.
_W5_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    let _annotations := crossRefParser typ
    children := [mkText ": "]
  return children"""
PARSED_DISCARDED = _swap(_BASE, _GOLD_IMPL, _W5_IMPL)
_W5_WITNESS = _witness('fun (s : String) => s', 'fun s => ["Q"]', '"bool"')

# --- W6 SEPARATOR APPENDED LAST (C1c, order) -------------------------------
# Both components are exactly right and the parsing step gets the right
# argument; only the ORDER is inverted (separator after the parsed nodes). The
# annotation would read as the type followed by a trailing separator. Isolates
# the ordering conjunct of C1, which no other rival attacks alone; the witness
# uses a two-element parser output, since a one-element output would make some
# ordering errors harder to separate.
_W6_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    let annotations := crossRefParser typ
    children := annotations ++ [mkText ": "]
  return children"""
SEP_LAST = _swap(_BASE, _GOLD_IMPL, _W6_IMPL)
_W6_WITNESS = _witness('fun (s : String) => s', 'fun s => ["A", "B"]', '"x"')

# --- W7 EMIT WHEN NO TYPE IS DECLARED (C2) ---------------------------------
# Drop the guard: always assemble the fragment. Fully correct on the
# present-type sub-domain (C1 holds), wrong only on the no-declared-type
# sub-domain, where C2 demands the empty list. The only rival whose witness
# moves `typ` to the empty string — without it the spec's dependence on the
# guard would be untested (the port of nagini's emit-when-absent).
_W7_IMPL = """  let mut children : List Node := []
  let annotations := crossRefParser typ
  children := mkText ": " :: annotations
  return children"""
EMIT_WHEN_ABSENT = _swap(_BASE, _GOLD_IMPL, _W7_IMPL)
_W7_WITNESS = _witness('fun (s : String) => s', 'fun s => [s]', '""')

# --- W8 DECLARED TYPE STRING CORRUPTED BEFORE RENDERING (C1c, argument) ------
# The behavioral image of nagini's frame-typ-write. Every structural fact of C1
# is respected — the head is the right factory applied to the right separator,
# the tail IS the parsing step's output, and the order is head-then-tail — but
# the step is applied to a MUTATED copy of the declared type rather than to `typ`
# itself, so the annotation describes a string the property never declared.
# Distinct from parse-wrong-argument, which substitutes an unrelated constant:
# this one is `typ`-DEPENDENT, so a spec pinning only "the tail mentions typ
# somehow" or "the parser was called on something derived from typ" would admit
# it. That makes it the near-miss on C1c's argument, where W4 is the far miss.
_W8_IMPL = """  let mut children : List Node := []
  if typ ≠ "" then
    let typ := typ ++ "?"
    let annotations := crossRefParser typ
    children := mkText ": " :: annotations
  return children"""
CORRUPT_TYPE = _swap(_BASE, _GOLD_IMPL, _W8_IMPL)
_W8_WITNESS = _witness('fun (s : String) => s', 'fun s => ["ref->" ++ s]', '"str"')


SPEC_TESTS = [
    # -------------------- positives --------------------
    {
        "id": "pos-hoisted-construction",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_HOISTED,
        "rationale": "structurally different but CORRECT impl: both components "
        "(the parsed nodes and the separator text node) are constructed into "
        "locals BEFORE the guard, and only the assembly stays inside it. The "
        "assembled value is unchanged, so the frozen tactic body still closes "
        "the identical obligation with no helper lemma. Port of nagini's "
        "pos-local-reorder ('reshape the order independent locals are built in, "
        "keep the assembled order'), re-aimed at this carrier: the Lean impl has "
        "one assignment where nagini had two appends, so the available reshaping "
        "is hoisting the locals out of the branch. MUST verify; if it cannot, "
        "the spec rejects a faithful correct impl => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_EARLY_RETURN,
        "rationale": "structurally different but CORRECT impl reshaped three "
        "independent ways at once: the guard polarity is INVERTED, the absent "
        "case becomes an early `return []`, and the present case is assembled "
        "with a singleton list append instead of a cons. Observationally equal "
        "to the frozen impl, and reproved honestly for the new shape (the "
        "branch-polarity flip means the frozen `if_pos` step becomes `if_neg`); "
        "the obligation statement is byte-identical and no lemma is added. This "
        "is the port SLOT of nagini's pos-direct-fabrication, RE-AIMED: that "
        "case built the navigable node directly instead of routing through a "
        "callee contract, which requires the spec to pin the node's CONTENT. "
        "Here the parsing step is universally quantified rather than "
        "axiomatized, so its output has no content a rival could fabricate and "
        "the nagini case has no counterpart; this positive exercises the same "
        "risk (does the spec accept a correct impl that reaches the pinned value "
        "by a different route?) on the structure the spec does pin. MUST "
        "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-annotation-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "port of nagini's admiss-type-str. Two anonymous examples "
        "in the impl region exhibit the pinned relation as SATISFIED on both "
        "sub-domains it distinguishes: a documented simple type name (the shape "
        "the failing test feeds), where the fragment is the separator node "
        "followed by the parsed node, and the no-declared-type case, where it is "
        "empty. Each discharges the relevant arm and refutes the other arm's "
        "hypothesis, so neither is closed by both arms being vacuous. The frozen "
        "obligation is untouched and no named declaration is added. If this "
        "could not verify the postcondition would be unsatisfiable on the very "
        "inputs the behavior is about => the analogue of PRECOND-TOO-STRONG "
        "(the obligation carries no precondition hypothesis, so satisfiability "
        "of the relation is the whole admissibility surface here).",
    },
    # -------------------- rivals --------------------
    {
        "id": "type-as-inert-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": TYPE_INERT,
        "rationale": "rejected by C1 (`typ ≠ \"\" → result = mkText \": \" :: "
        "crossRefParser typ`) on BOTH of its structural facts: the fragment is "
        "one plain-text node carrying the whole concatenated run, so the head is "
        "not the bare separator node and the parsing step's output is absent "
        "from the tail. This is the load-bearing discriminator of the modeled "
        "change — the rendering in which the declared type is shown but never "
        "becomes navigable.",
        "refinement": "a faithful real patch of this shape emits the declared "
        "type as a single inert run of literal text after the separator. The "
        "failing test asserts the annotation's children are the separator text "
        "followed by a NAVIGABLE cross-reference node for the type name, and it "
        "compares node KINDS, not just rendered text — a single inert text run "
        "renders the same characters and still fails the comparison. So this "
        "impl would NOT resolve; it is exactly the behavior the issue reports.",
        "witness": _W1_WITNESS,
    },
    {
        "id": "separator-parsed-not-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SEP_PARSED,
        "rationale": "rejected by C1a, the head's PROVENANCE: the tail is "
        "correct and in the right order, but the separator is produced by "
        "applying the parsing step to the separator string instead of by the "
        "plain-text-node factory, so `result`'s head is not `mkText \": \"`. "
        "Port of nagini's separator-as-xref: a double-mask on the head, since "
        "the rendered characters can coincide while the node's kind diverges — "
        "the distinction a text-only proxy misses. Witness varies `mkText` to a "
        "bracketing shape (distinct from every other witness) precisely so the "
        "head's provenance, not its characters, is what separates rival from "
        "frozen.",
        "refinement": "a faithful real patch routing the literal separator "
        "through the type-parsing step rather than the plain-text factory makes "
        "the annotation's FIRST child a parsed/navigable node. The failing test "
        "requires that first child to be a plain text node carrying exactly the "
        "separator, and compares node kinds — so it would NOT resolve. The "
        "P2P signature-rendering tests read the same children, so a separator "
        "of the wrong kind is observable there too.",
        "witness": _W2_WITNESS,
    },
    {
        "id": "wrong-separator-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WRONG_SEP,
        "rationale": "rejected by C1a, the head's VALUE: the head is built by "
        "the right factory and the tail is exactly the parsing step's output, "
        "but the separator string is one character short (the trailing space is "
        "dropped), so `result`'s head is `mkText \":\"`, not `mkText \": \"`. "
        "Port of nagini's wrong-separator-text. A NEAR-MISS of the "
        "separator-parsed rival above — it agrees with the frozen behavior on "
        "the head's kind and differs only in the string — so it carries its own "
        "witness input (identity `mkText`, an argument-dependent one-element "
        "parser, `typ = \"Point\"`) rather than sharing one.",
        "refinement": "a faithful real patch emitting the separator without its "
        "trailing space renders the type flush against the colon. The failing "
        "test pins the leading child's text to exactly the two-character "
        "separator, so a one-character-short separator fails the text "
        "comparison and would NOT resolve.",
        "witness": _W3_WITNESS,
    },
    {
        "id": "parse-wrong-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARSE_WRONG_ARG,
        "rationale": "rejected by C1's tail: the head is right, the order is "
        "right, and the parsing step is genuinely invoked — but on the separator "
        "string instead of on the declared type, so the tail is `crossRefParser "
        "\": \"` where C1 pins `crossRefParser typ`. Attacks the ARGUMENT rather "
        "than the result, which is what makes it refutable at all over a "
        "universally-quantified parsing step: no property of the parser is "
        "needed, only one instantiation under which the two calls differ. Port "
        "of nagini's wrong-type-text (there the node carried the separator text "
        "instead of the type name — the same 'annotation describes the wrong "
        "string' defect, expressed on this carrier as the wrong argument).",
        "refinement": "a faithful real patch parsing the wrong string produces a "
        "navigable node targeting something other than the declared type. The "
        "failing test asserts the cross-reference carries exactly the declared "
        "type name, so an annotation describing any other string fails and would "
        "NOT resolve. It is also correct only on the degenerate input where the "
        "declared type happens to equal the separator string, which the tested "
        "scenario never feeds.",
        "witness": _W4_WITNESS,
    },
    {
        "id": "parsed-nodes-discarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARSED_DISCARDED,
        "rationale": "rejected by C1's tail alone: the parsing step still RUNS "
        "on the right argument (so a proxy checking only 'was the step reached' "
        "is satisfied) but its output is dropped, leaving just the separator "
        "node. Head correct, order vacuously correct, tail empty. Splits the "
        "tail conjunct off from the head conjunct that type-as-inert-text "
        "attacks jointly, so a rival wrong ONLY about the tail is demonstrated "
        "to be caught rather than assumed to be.",
        "refinement": "a faithful real patch that computed the parsed annotation "
        "nodes and then assembled the fragment without splicing them in emits an "
        "annotation consisting of the separator and nothing else — the declared "
        "type would vanish from the rendered signature entirely. The failing "
        "test asserts a child for the type name after the separator, and the "
        "P2P property/signature tests read the same rendered annotation, so this "
        "would NOT resolve.",
        "witness": _W5_WITNESS,
    },
    {
        "id": "separator-appended-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SEP_LAST,
        "rationale": "rejected by C1's ORDER: both components are exactly right "
        "and the parsing step gets the right argument, but the separator is "
        "appended AFTER the parsed nodes, so `result` is `crossRefParser typ ++ "
        "[mkText \": \"]` where C1 pins the cons. Isolates the ordering "
        "conjunct, which no other rival attacks alone — a spec that pinned only "
        "membership or length would admit it. Witness uses a TWO-element parser "
        "output (unique among these witnesses) so the reordering is visible in "
        "the list shape rather than only in a one-element swap.",
        "refinement": "a faithful real patch assembling the annotation's "
        "children with the separator last renders the declared type before the "
        "colon-space, i.e. a trailing separator. The failing test pins the "
        "children in order — separator first, then the type's node — so an "
        "inverted order fails the positional comparison and would NOT resolve; "
        "the P2P signature tests read the same ordered children.",
        "witness": _W6_WITNESS,
    },
    {
        "id": "emit-when-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": EMIT_WHEN_ABSENT,
        "rationale": "rejected by C2 (`typ = \"\" → result = []`): the guard is "
        "dropped, so a fragment is assembled even when no type is declared. "
        "Fully correct on the present-type sub-domain — C1 holds — and wrong "
        "only on the other arm, so the rejection isolates C2. This is the ONLY "
        "rival whose witness moves `typ` to the empty string; without it the "
        "spec's dependence on the guard binder would never be probed and a rival "
        "that mishandled just the no-type case would verify. Port of nagini's "
        "emit-when-absent.",
        "refinement": "a faithful real patch dropping the presence guard "
        "attaches a spurious separator-only annotation to every documented "
        "property that declares no type. The no-declared-type arm of the failing "
        "test and the P2P property/object rendering tests expect no annotation "
        "fragment at all there, and would see an extra annotation child — so it "
        "would NOT resolve.",
        "witness": _W7_WITNESS,
    },
    {
        "id": "corrupt-type-string",
        "kind": "uniqueness",
        "expect": "reject",
        "module": CORRUPT_TYPE,
        "rationale": "rejected by C1's tail via its ARGUMENT: the head is "
        "`mkText \": \"`, the tail is genuinely the parsing step's output, and "
        "the order is the cons C1 pins — but the step is applied to a MUTATED "
        "copy of the declared type (a character appended) rather than to `typ`, "
        "so the tail is `crossRefParser (typ ++ \"?\")` where C1 pins "
        "`crossRefParser typ`. This is the behavioral image of nagini's "
        "frame-typ-write, whose own mechanism (writing a read-only input against "
        "a half permission share) is inexpressible here because `typ : String` is "
        "an immutable value parameter with no permission algebra. The behavior it "
        "describes — the rendered annotation targeting a string the property "
        "never declared — is expressible, and this is it. Strictly nearer the "
        "frozen impl than parse-wrong-argument: that rival substitutes an "
        "unrelated CONSTANT, this one stays a function OF `typ`, so a spec that "
        "pinned only 'the parser was called on something derived from typ' would "
        "still admit it.",
        "refinement": "a faithful real patch that adjusted the declared type "
        "string before handing it to the type-parsing step renders a navigable "
        "cross-reference to a type name that differs from the one the property "
        "declares. The failing test asserts the cross-reference carries exactly "
        "the declared type name, so an annotation targeting any other string "
        "fails the comparison and would NOT resolve; the P2P cross-reference "
        "resolution tests read the same target, so a corrupted name also breaks "
        "resolution against the real inventory.",
        "witness": _W8_WITNESS,
    },
]
