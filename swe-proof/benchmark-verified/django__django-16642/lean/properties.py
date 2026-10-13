# properties.py — G-PBT falsification battery for django__django-16642 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a soundness positive that reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject" case
# carries a refutation `witness`: a self-contained snippet that ELABORATES against
# the rival and FAILS on the frozen solution, so the rejection is attributable to the
# spec and not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   implementation_contentType (contentType encoding : Option String) : String
#   Selects the response content type for a guessed `(contentType, encoding)` pair:
#   when the encoding is a recognized compression scheme its dedicated media type
#   OVERRIDES the guessed type; an unrecognized or absent encoding KEEPS the guessed
#   type; an absent or empty selection FALLS BACK to the generic binary media type.
#   The SINGLE postcondition `problem_spec_contentType` pins the whole result to ONE
#   equation `result = finalContentType contentType encoding`, which bundles several
#   independent obligations:
#     (C1) OVERRIDE: for each recognized scheme e ∈ {br, bzip2, compress, gzip, xz}
#          the result is that scheme's EXACT dedicated media type, regardless of the
#          guessed type. ALL FIVE keys carry their own rival, so the "for EACH
#          recognized scheme" quantifier is demonstrated key-by-key and not merely
#          asserted: br/compress are the two the fix adds, and gzip/xz/bzip2 are
#          pre-existing. The EXACT-VALUE sub-clause is additionally pinned at two
#          separate keys (br and bzip2), so a spec that fixed one scheme's precise
#          media type while leaving another's merely "overridden to SOMETHING" is
#          refuted rather than admitted.
#     (C2) KEEP / PASSTHROUGH: for an encoding that is absent or is not one of the
#          five recognized schemes, the result is the guessed type unchanged — the
#          encoding token is NEVER substituted for the type.
#     (C3) FALLBACK: when the selected type is absent (`none`) or empty (`""`), the
#          result is the generic binary media type "application/octet-stream". These
#          are TWO independent triggers on this carrier (`none` vs `some ""`) and an
#          impl can implement either one without the other, so each is attacked by
#          its own rival at its own probe point.
#
# CARRIER IS FULLY TRANSPARENT: both inputs are `Option String` and the whole
# computation (`finalContentType` / `encodingContentType`) is a concrete case split
# over string-literal equality. There are NO opaque callees, so every rejection can
# be `decide`d at a concrete literal input — no conditioning on the carrier is
# needed, and every witness is a closed proposition whose hypotheses are vacuously
# consistent (there are none).
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `frame-mut-write-input`: `content_type` was
#     Acc(list_pred(content_type),1/2) read-only and the rival wrote back into it).
#     Lean is referentially transparent — no aliasing, no fractional permission — so
#     a "store into a read-only input" rival is not expressible. The frame obligation
#     instead lives in the single result equation: the output is a pure function of
#     the two inputs with nothing left unconstrained.
#   * DIVERGENCE / NON-TERMINATION. Checked against what this bundle actually sets:
#     Solution.lean carries NO `set_option loom.semantics.termination` line at all,
#     so the partial-semantics known-spec-hole disposition does not apply. The
#     modeled operation is a straight-line, loop-free selection over two
#     `Option String` values, defined as a total Lean `def` that the elaborator
#     accepts with no termination obligation to discharge and no recursion to give a
#     measure for. There is no loop a rival could strip a decreasing measure from,
#     so the class is genuinely VACUOUS here rather than a hole — demonstrated by the
#     shape of the operation, not asserted. The nagini sibling carries no divergence
#     case either.
#   (ADMISSIBILITY DOES PORT — see `admiss-br-f2p-point`. An earlier revision of
#   this manifest recorded the lane as N/A because the frozen obligation carries no
#   precondition hypothesis. That reason was WRONG and is retracted: on a TOTAL
#   carrier the analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE
#   at exactly an F2P-shaped input, which a positive that discharges the obligation
#   at that concrete input — by evaluation, as a `have`, before closing the frozen
#   obligation verbatim — tests directly. It is landed below and it verifies.)
#   * AXIOM_TESTS (nagini's empty AXIOM_TESTS). The axiom lane is G-AX's job; this
#     gate ignores them. There are no opaque callees and no constraining axioms here
#     anyway.
#
# CARRIER NARROWING vs nagini: nagini modeled the type as `List[int]` (code points)
# and reproduced the passthrough as an explicit index loop with prefix invariants;
# its passthrough rival (`passthrough-returns-encoding`) copied the `encoding` list
# instead of the `content_type` list. This backend models the guessed type as
# `Option String` and the passthrough as `.getD`/identity, so the "return the
# encoding token" bug re-expresses as an override rival that substitutes the encoding
# token for an UNRECOGNIZED scheme (`weak-passthrough-echo-encoding`, clause C2). The
# nagini FALLBACK-to-octet-stream behavior (`content_type or "…"`) was folded into
# the loop there; here it is a transparent clause of its own (C3) and is attacked by
# `weak-drop-octet-fallback`. So the port keeps every value/partial-domain rival and
# ADDS a fallback rival the nagini carrier could not isolate.
from pathlib import Path

INSTANCE = "django__django-16642"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"'
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the positives, whose different impl shapes need an (equally cheap, honest) reproof
# of the byte-identical theorem statement.
_PROOF = (
    "  intro contentType encoding\n"
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  cases encoding with\n"
    "  | none => cases contentType <;> rfl\n"
    "  | some e =>\n"
    "    simp only [Id.run, bind, pure]\n"
    '    by_cases hbr : e = "br"\n'
    "    · subst hbr; rfl\n"
    '    by_cases hbz : e = "bzip2"\n'
    "    · subst hbz; rfl\n"
    '    by_cases hco : e = "compress"\n'
    "    · subst hco; rfl\n"
    '    by_cases hgz : e = "gzip"\n'
    "    · subst hgz; rfl\n"
    '    by_cases hxz : e = "xz"\n'
    "    · subst hxz; rfl\n"
    "    · simp only [hbr, hbz, hco, hgz, hxz, if_false]\n"
    "      cases contentType <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-pure-delegate: a structurally different CORRECT impl written as a single pure
# expression `finalContentType contentType encoding` (no `Id.run do`, no `let mut`, no
# per-scheme `if` chain). Semantics identical on every input by construction. The
# theorem STATEMENT is byte-identical; its proof is reproven honestly with `rfl` (the
# impl is now definitionally the spec's RHS) — no new axiom/lemma/sorry, just the
# cheapest tactic for the new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition
# is bound to the monadic impl shape rather than the behaviour).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_contentType (contentType encoding : Option String) : String :=\n"
        "  finalContentType contentType encoding",
    ),
    _PROOF,
    "  intro contentType encoding\n"
    "  rfl",
)

# pos-reorder-branches: the five recognized-scheme branches are REVERSED (xz, gzip,
# compress, bzip2, br) instead of the frozen order. The keys are pairwise-disjoint
# string literals, so branch order is irrelevant and the output equals the frozen
# impl's on every input. The theorem STATEMENT is byte-identical; the proof is the
# frozen one with its `by_cases` split reordered to match (each subst;rfl closes the
# newly-first branch) — no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG
# (postcondition over-fit to the frozen branch order).
_POS_REORDER = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
        "  let mut ct := contentType\n"
        "  if let some e := encoding then\n"
        '    if e = "xz" then ct := some "application/x-xz"\n'
        '    else if e = "gzip" then ct := some "application/gzip"\n'
        '    else if e = "compress" then ct := some "application/x-compress"\n'
        '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
        '    else if e = "br" then ct := some "application/x-brotli"\n'
        "  match ct with\n"
        '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
        '  | none => return "application/octet-stream"',
    ),
    _PROOF,
    "  intro contentType encoding\n"
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  cases encoding with\n"
    "  | none => cases contentType <;> rfl\n"
    "  | some e =>\n"
    "    simp only [Id.run, bind, pure]\n"
    '    by_cases hxz : e = "xz"\n'
    "    · subst hxz; rfl\n"
    '    by_cases hgz : e = "gzip"\n'
    "    · subst hgz; rfl\n"
    '    by_cases hco : e = "compress"\n'
    "    · subst hco; rfl\n"
    '    by_cases hbz : e = "bzip2"\n'
    "    · subst hbz; rfl\n"
    '    by_cases hbr : e = "br"\n'
    "    · subst hbr; rfl\n"
    "    · simp only [hbr, hbz, hco, hgz, hxz, if_false]\n"
    "      cases contentType <;> rfl",
)


# The frozen proof's `intro` line — unique in the file and wholly inside
# proof-start/proof-end — so the admissibility positive can PREPEND a ground `have`
# without touching the theorem STATEMENT or the spec view.
_P_INTRO = "  intro contentType encoding\n"
assert _BASE.count(_P_INTRO) == 1, "intro anchor drifted from expected text"

# admiss-br-f2p-point: the ADMISSIBILITY lane, ported from nagini's
# `admiss-br-text-html`. The impl region is the FROZEN one, untouched; the proof
# body gains a leading ground `have` that discharges the obligation at exactly the
# F2P-shaped input (a guessed type present, encoding = the newly-recognized "br"
# scheme) BY EVALUATION, and only then closes the frozen obligation verbatim.
#
# Why this is the right analogue on a total carrier: the frozen obligation has no
# precondition hypothesis, so nothing can be PRECOND-TOO-STRONG in the literal
# nagini sense. The lane is NOT vacuous for that reason, though — the total-carrier
# analogue is the obligation being UNSATISFIABLE at a normal, F2P-shaped input,
# i.e. `problem_spec_contentType` demanding of the result something no impl could
# deliver there. A ground instance is what tests that directly: if the modeled
# behaviour were contradictory at this point the `have` could not be closed by
# evaluation, and the case would fail while every uniqueness rival still passed.
# Nothing is assumed (no new axiom/lemma/sorry, statement byte-identical, the
# ground instance is a `have` inside the existing tactic body).
_POS_ADMISS = _swap(
    _BASE,
    _P_INTRO,
    '  have _ground : problem_spec_contentType (some "text/html") (some "br")\n'
    '      (implementation_contentType (some "text/html") (some "br")) := by\n'
    '    have himpl : implementation_contentType (some "text/html") (some "br")\n'
    '        = "application/x-brotli" := by\n'
    "      unfold implementation_contentType\n"
    "      decide\n"
    "    rw [himpl]\n"
    "    unfold problem_spec_contentType finalContentType encodingContentType\n"
    "    decide\n" + _P_INTRO,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-drop-br-key: removes the "br" branch, so a "br" encoding falls through to the
# guessed type instead of the dedicated brotli media type. This IS the pre-patch bug
# for the newly-added "br" scheme. Correct on every other sub-domain but WRONG for
# encoding = "br". Attacks clause C1 (OVERRIDE), the "br" key.
_RIV_DROP_BR = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"',
)

# weak-drop-compress-key: removes the "compress" branch, so a "compress" encoding
# falls through to the guessed type instead of the dedicated compress media type. The
# other half of the pre-patch bug (the newly-added "compress" scheme). Attacks clause
# C1 (OVERRIDE), the "compress" key.
_RIV_DROP_COMPRESS = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"',
)

# weak-swap-br-value: maps "br" to the BZIP media type instead of the brotli one.
# Wrong only on the "br" sub-domain, and wrong in the VALUE rather than by falling
# through — a brotli payload described as bzip. Attacks clause C1 (OVERRIDE), the
# EXACT-VALUE sub-clause for "br".
_RIV_SWAP_BR = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-bzip"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"',
)

# weak-passthrough-echo-encoding: for an UNRECOGNIZED encoding token (not one of the
# five schemes) it substitutes the encoding token itself for the guessed type — the
# `dict.get(encoding, encoding)` shape from the nagini `passthrough-returns-encoding`
# rival, re-expressed on this carrier. Correct on the five recognized schemes and on
# encoding = none, but WRONG for any other `some e`: it must KEEP the guessed type.
# Attacks clause C2 (KEEP / PASSTHROUGH).
_RIV_PASS_ECHO = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "    else ct := some e\n"
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"',
)

# weak-drop-octet-fallback: replaces the absent/empty fallback with `ct.getD ""`, so
# an absent selection yields the empty string instead of the generic binary media
# type. Correct whenever a type is present, but WRONG when both inputs leave the
# selection absent. Attacks clause C3 (FALLBACK). This clause the nagini carrier
# folded into the passthrough loop; here it is isolable.
_RIV_DROP_OCTET = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    '  return ct.getD ""',
)


# weak-drop-gzip-key: removes the "gzip" branch, so a "gzip" encoding falls through to
# the guessed type. Unlike the br/compress rivals this attacks a PRE-EXISTING override
# key: the battery's C1 claim is "for EACH of the five recognized schemes", and without
# this the three long-standing keys were pinned by nothing — a spec that had dropped
# them entirely would still have passed every other case here. Attacks clause C1
# (OVERRIDE) on a key the fix did not add.
_RIV_DROP_GZIP = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"',
)

# weak-keep-empty-type: keeps the absent→octet-stream arm but DROPS the empty-string
# guard, so a PRESENT-but-empty selection is returned as "" instead of the generic
# binary media type. C3 has two independent triggers on this carrier — `none` and
# `some ""` — and `weak-drop-octet-fallback` only distinguishes the `none` one (it
# collapses BOTH to ""). This rival is correct at `none` and wrong only at `some ""`,
# so it isolates the half of C3 that was previously unattacked.
_RIV_KEEP_EMPTY = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "  match ct with\n"
    "  | some s => return s\n"
    '  | none => return "application/octet-stream"',
)

# weak-drop-xz-key: removes the "xz" branch. The THIRD pre-existing override key.
# With only the gzip rival added, C1's "for EACH of the five schemes" claim was
# demonstrated for 3 of 5; a spec that had dropped the "xz" key alone would still
# have passed. Attacks clause C1 (OVERRIDE) on the last unpinned key.
_RIV_DROP_XZ = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/x-bzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"',
)

# weak-swap-bzip2-value: maps "bzip2" to the GZIP media type instead of the bzip
# one. The EXACT-VALUE sub-clause of C1 was previously pinned only at "br"
# (weak-swap-br-value), i.e. only for a key the fix adds; a spec that pinned the
# exact value for "br" but merely "bzip2 was overridden to SOMETHING" would have
# passed. Wrong only on the "bzip2" sub-domain, and wrong in the VALUE rather than
# by falling through. Attacks clause C1 (OVERRIDE), exact value, pre-existing key.
_RIV_SWAP_BZIP2 = _swap(
    _BASE,
    _IMPL,
    "def implementation_contentType (contentType encoding : Option String) : String := Id.run do\n"
    "  let mut ct := contentType\n"
    "  if let some e := encoding then\n"
    '    if e = "br" then ct := some "application/x-brotli"\n'
    '    else if e = "bzip2" then ct := some "application/gzip"\n'
    '    else if e = "compress" then ct := some "application/x-compress"\n'
    '    else if e = "gzip" then ct := some "application/gzip"\n'
    '    else if e = "xz" then ct := some "application/x-xz"\n'
    "  match ct with\n"
    '  | some s => return (if s.isEmpty then "application/octet-stream" else s)\n'
    '  | none => return "application/octet-stream"',
)


# --- witnesses ---------------------------------------------------------------------
# Each witness states `¬ problem_spec_contentType ct enc (impl ct enc)` at a concrete
# input, unfolds the spec + impl (+ the two transparent helpers), and `decide`s the
# disequality. The carrier is fully transparent, so no hypothesis is needed: each
# witness is a closed proposition (vacuously consistent — the gate's inconsistency
# probe has nothing to contradict). Each ELABORATES against its rival (which produces
# the wrong string there) and FAILS on gold (which satisfies the spec everywhere).

# OVERRIDE, "br" key: encoding "br" with a guessed type present. gold => brotli type;
# the drop-br rival keeps the guessed "text/html".
_WIT_DROP_BR = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "text/html") (some "br")\n'
    '      (implementation_contentType (some "text/html") (some "br")) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)

# OVERRIDE, "compress" key: encoding "compress" with a guessed type present.
# gold => compress type; the drop-compress rival keeps the guessed "text/html".
# Varies the `encoding` binder to a DIFFERENT recognized scheme than the br witnesses.
_WIT_DROP_COMPRESS = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "text/html") (some "compress")\n'
    '      (implementation_contentType (some "text/html") (some "compress")) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)

# OVERRIDE, exact value for "br": gold => brotli type; the swap rival => bzip type.
# Same input as drop-br but the rival disagrees in the VALUE, not by falling through.
_WIT_SWAP_BR = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "text/html") (some "br")\n'
    '      (implementation_contentType (some "text/html") (some "br")) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)

# KEEP / PASSTHROUGH: an UNRECOGNIZED encoding token with a guessed type present.
# gold keeps the guessed "text/plain"; the echo rival substitutes the token
# "identity". Varies the `encoding` binder to a non-recognized `some e`.
_WIT_PASS_ECHO = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "text/plain") (some "identity")\n'
    '      (implementation_contentType (some "text/plain") (some "identity")) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)

# FALLBACK: both inputs absent (no guessed type, no encoding). gold => the generic
# binary media type; the drop-octet rival => the empty string. Varies BOTH binders to
# `none`, the only point the fallback clause is reachable.
_WIT_DROP_OCTET = (
    "example :\n"
    "    ¬ problem_spec_contentType none none\n"
    "      (implementation_contentType none none) := by\n"
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)


# OVERRIDE, "gzip" key (a PRE-EXISTING scheme): gold => the gzip media type; the
# drop-gzip rival keeps the guessed "text/html". Varies the `encoding` binder to a
# recognized scheme the fix did not add.
_WIT_DROP_GZIP = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "text/html") (some "gzip")\n'
    '      (implementation_contentType (some "text/html") (some "gzip")) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)

# FALLBACK, the empty-string trigger: a PRESENT but empty guessed type with no
# encoding. gold => the generic binary media type; the keep-empty rival => "". Varies
# the `contentType` binder to `some ""`, a probe point no other case reaches (the
# other fallback case uses `none`).
_WIT_KEEP_EMPTY = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "") none\n'
    '      (implementation_contentType (some "") none) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)


# OVERRIDE, "xz" key (the third PRE-EXISTING scheme): gold => the xz media type;
# the drop-xz rival keeps the guessed "text/html".
_WIT_DROP_XZ = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "text/html") (some "xz")\n'
    '      (implementation_contentType (some "text/html") (some "xz")) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)

# OVERRIDE, exact value for "bzip2" (a PRE-EXISTING scheme): gold => the bzip media
# type; the swap-bzip2 rival => the gzip media type. Varies the `encoding` binder to
# a recognized scheme whose exact VALUE no other case pins.
_WIT_SWAP_BZIP2 = (
    "example :\n"
    '    ¬ problem_spec_contentType (some "text/html") (some "bzip2")\n'
    '      (implementation_contentType (some "text/html") (some "bzip2")) := by\n'
    "  unfold problem_spec_contentType implementation_contentType finalContentType encodingContentType\n"
    "  decide"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-pure-delegate",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "structurally-different but CORRECT impl written as a single pure expression "
            "delegating to the modeled selection function (no `Id.run do`, no `let mut`, no "
            "per-scheme `if` chain). Semantics identical on every input by construction. The "
            "theorem STATEMENT is byte-identical; its proof is reproven honestly with `rfl` (the "
            "impl is now definitionally the spec's RHS) — no new axiom/lemma/sorry, just the "
            "cheapest tactic for the new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition "
            "is bound to the monadic impl shape rather than the behaviour)."
        ),
    },
    {
        "id": "pos-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "the five recognized-scheme branches are REVERSED (the keys are pairwise-disjoint "
            "string literals, so branch order is irrelevant to the case split). Output equals the "
            "frozen impl's on every input. The theorem STATEMENT is byte-identical; the proof is "
            "the frozen one with its `by_cases` split reordered to match — no new axiom/lemma/"
            "sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to the frozen branch "
            "order)."
        ),
    },

    {
        "id": "admiss-br-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ADMISSIBILITY, ported from the nagini sibling's `admiss-br-text-html`. The "
            "obligation is discharged at exactly the F2P-shaped input — a guessed type "
            "present with the newly-recognized 'br' compression scheme — by evaluation as "
            "a leading `have`, and only then is the frozen obligation closed verbatim. On "
            "this TOTAL carrier the frozen obligation carries no precondition hypothesis, "
            "so nothing can be PRECOND-TOO-STRONG in the literal nagini sense; the lane is "
            "NOT vacuous for that reason, though, because the total-carrier analogue is the "
            "obligation being UNSATISFIABLE at a normal F2P-shaped input, i.e. the "
            "postcondition demanding of the result something no implementation could "
            "deliver there. The ground instance tests that directly: were the modeled "
            "behaviour contradictory at this point, the `have` could not be closed by "
            "evaluation and this case would fail while every uniqueness rival still "
            "passed. Nothing is assumed — no new axiom/lemma/sorry, the theorem STATEMENT "
            "is byte-identical, and the ground instance is a `have` inside the existing "
            "tactic body. If it FAILS => the spec is unsatisfiable at an F2P input."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-drop-br-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_BR,
        "refinement": (
            "omits the 'br' override key, so a 'br'-encoded response falls through to the guessed "
            "type — this IS the pre-patch behaviour for the newly-added 'br' scheme. Its faithful "
            "real patch is the override dict WITHOUT the 'br' entry; the F2P regression "
            "(a compressed response served with the uncompressed Content-Type) is exactly a "
            "'.br' payload described by the guessed type instead of application/x-brotli, so the "
            "test FAILS. It would NOT resolve — this is precisely the bug the patch fixes (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause C1 (OVERRIDE, 'br' key). For encoding='br' the spec fixes the "
            "result to application/x-brotli, but the rival returns the guessed type. Witness probes "
            "encoding='br' with a present guessed type; the carrier is transparent so `decide` "
            "closes the disequality at the literal. If it VERIFIES => SPEC-TOO-WEAK (the 'br' "
            "override is unpinned)."
        ),
        "witness": _WIT_DROP_BR,
    },
    {
        "id": "weak-drop-compress-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_COMPRESS,
        "refinement": (
            "omits the 'compress' override key — the other half of the pre-patch bug. Its faithful "
            "real patch is the override dict WITHOUT the 'compress' entry; a '.Z' payload is served "
            "with the guessed type rather than application/x-compress, so the F2P assertion for the "
            "compress scheme FAILS. It would NOT resolve (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause C1 (OVERRIDE, 'compress' key). For encoding='compress' the spec "
            "fixes the result to application/x-compress, but the rival returns the guessed type. "
            "Witness varies the `encoding` binder to a DIFFERENT recognized scheme than the 'br' "
            "witnesses ('compress'); `decide` closes it at the literal. If it VERIFIES => "
            "SPEC-TOO-WEAK (the 'compress' override is unpinned)."
        ),
        "witness": _WIT_DROP_COMPRESS,
    },
    {
        "id": "weak-swap-br-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP_BR,
        "refinement": (
            "maps 'br' to application/x-bzip instead of application/x-brotli — a brotli payload "
            "described under the bzip media type. Its faithful real patch is the override dict with "
            "a wrong value for 'br'; the F2P assertion expecting application/x-brotli for a '.br' "
            "response FAILS. It would NOT resolve (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause C1 (OVERRIDE, exact-value sub-clause for 'br'). Same input as the "
            "drop-br rival, but the rival disagrees in the VALUE rather than by falling through: "
            "application/x-brotli vs application/x-bzip differ byte-for-byte. `decide` closes it. "
            "If it VERIFIES => SPEC-TOO-WEAK (the exact 'br' value is unpinned — a spec pinning only "
            "'br was overridden to SOMETHING' would miss this)."
        ),
        "witness": _WIT_SWAP_BR,
    },
    {
        "id": "weak-passthrough-echo-encoding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PASS_ECHO,
        "refinement": (
            "for an unrecognized encoding token it substitutes the token itself for the guessed "
            "type — the `dict.get(encoding, encoding)` shape. Its faithful real patch returns the "
            "encoding token as the Content-Type for every non-compressed file, so ordinary "
            "content-type behaviour (e.g. a plain-text file served as 'text/plain') breaks across "
            "the P2P suite. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (KEEP / PASSTHROUGH). For an encoding that is not one of the five "
            "recognized schemes the spec keeps the guessed type, but the rival returns the encoding "
            "token. Witness varies the `encoding` binder to a non-recognized `some e` ('identity') "
            "with a present guessed type; `decide` closes it. If it VERIFIES => SPEC-TOO-WEAK (the "
            "passthrough of the guessed type is unpinned)."
        ),
        "witness": _WIT_PASS_ECHO,
    },
    {
        "id": "weak-drop-octet-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_OCTET,
        "refinement": (
            "replaces the absent/empty fallback with a plain default of the empty string, so an "
            "absent selection yields '' instead of the generic binary media type. Its faithful real "
            "patch drops the `content_type or 'application/octet-stream'` guard; a response with no "
            "guessed type would be sent with an empty Content-Type, which the regression/P2P "
            "behaviour forbids. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (FALLBACK). When the selection is absent the spec substitutes "
            "'application/octet-stream', but the rival yields the empty string. Witness varies BOTH "
            "binders to `none` — the only point the fallback clause is reachable, a distinct probe "
            "point from every other rival (which hold a present guessed type). `decide` closes it. "
            "If it VERIFIES => SPEC-TOO-WEAK (the octet-stream fallback is unpinned)."
        ),
        "witness": _WIT_DROP_OCTET,
    },
    {
        "id": "weak-drop-gzip-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_GZIP,
        "refinement": (
            "omits the 'gzip' override key — a PRE-EXISTING scheme, not one the fix adds. Its "
            "faithful real patch is the override association missing its long-standing 'gzip' "
            "entry; a '.gz' payload is then served with the guessed type of the underlying file "
            "instead of application/gzip, so the existing regression row for the gzip scheme "
            "FAILS. It would NOT resolve (G-DIFF): it breaks behaviour that already worked."
        ),
        "rationale": (
            "REJECTED by clause C1 (OVERRIDE, 'gzip' key). Added by AUDIT: the other three C1 "
            "rivals all attack the two schemes the fix introduces, so nothing in the battery "
            "pinned the three pre-existing keys — the C1 claim quantifies over ALL FIVE schemes "
            "and only two of them were demonstrated. Witness varies the `encoding` binder to a "
            "recognized scheme outside the fix; `decide` closes the disequality at the literal. "
            "If it VERIFIES => SPEC-TOO-WEAK (the pre-existing overrides are unpinned)."
        ),
        "witness": _WIT_DROP_GZIP,
    },
    {
        "id": "weak-keep-empty-type",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEEP_EMPTY,
        "refinement": (
            "keeps the absent-selection default but drops the EMPTY-string half of the guard, so "
            "a present-but-empty guessed type is emitted verbatim. Its faithful real patch tests "
            "only for an absent type rather than for falsiness, so a response whose guessed type "
            "is the empty string goes out with an empty Content-Type header — the same observable "
            "defect the fallback forbids. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (FALLBACK, the empty-string trigger). Added by AUDIT: C3 has "
            "TWO independent triggers on this carrier, `none` and `some \"\"`, and an impl can "
            "satisfy either without the other. `weak-drop-octet-fallback` collapses both to \"\" "
            "so it is refuted at `none` and demonstrates nothing about `some \"\"`; this rival is "
            "CORRECT at `none` and wrong only at `some \"\"`, forcing that half to be pinned "
            "separately. Witness varies the `contentType` binder to `some \"\"` — a probe point no "
            "other case in the battery reaches. If it VERIFIES => SPEC-TOO-WEAK (the empty-type "
            "half of the fallback is unpinned, and the spec would admit an empty Content-Type)."
        ),
        "witness": _WIT_KEEP_EMPTY,
    },
    {
        "id": "weak-drop-xz-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_XZ,
        "refinement": (
            "omits the 'xz' override key — the third PRE-EXISTING scheme, not one the fix "
            "adds. Its faithful real patch is the override association missing its "
            "long-standing 'xz' entry; a '.xz' payload is then served with the guessed type "
            "of the underlying file instead of application/x-xz, so the existing regression "
            "row for the xz scheme FAILS. It would NOT resolve (G-DIFF): it breaks "
            "behaviour that already worked."
        ),
        "rationale": (
            "REJECTED by clause C1 (OVERRIDE, 'xz' key). Added by AUDIT: with only the gzip "
            "rival present, the C1 claim quantifying over ALL FIVE recognized schemes was "
            "demonstrated for three of them (br, compress, gzip) and 'xz' was pinned by "
            "nothing — a spec that had dropped the 'xz' key alone would have passed the "
            "battery unchanged. Witness varies the `encoding` binder to the last "
            "unattacked recognized scheme; `decide` closes the disequality at the literal. "
            "If it VERIFIES => SPEC-TOO-WEAK (the 'xz' override is unpinned)."
        ),
        "witness": _WIT_DROP_XZ,
    },
    {
        "id": "weak-swap-bzip2-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP_BZIP2,
        "refinement": (
            "maps 'bzip2' to application/gzip instead of application/x-bzip — a bzip2 "
            "payload described under the gzip media type. Its faithful real patch is the "
            "override association carrying a wrong value for its long-standing 'bzip2' "
            "entry; the existing regression row expecting application/x-bzip for a '.bz2' "
            "response FAILS. It would NOT resolve (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by clause C1 (OVERRIDE, exact-value sub-clause for 'bzip2'). Added by "
            "AUDIT: the EXACT-VALUE sub-clause was previously pinned only at 'br' "
            "(weak-swap-br-value), i.e. only for a key the fix adds. Every rival on a "
            "pre-existing key attacked it by DROPPING the key, so a spec that pinned the "
            "exact value for 'br' but only 'bzip2 was overridden to SOMETHING' would have "
            "passed. This rival keeps the key present and wrong in the VALUE, and it stays "
            "correct on every other sub-domain. Witness probes encoding='bzip2'; `decide` "
            "closes it at the literal. If it VERIFIES => SPEC-TOO-WEAK (the exact 'bzip2' "
            "value is unpinned)."
        ),
        "witness": _WIT_SWAP_BZIP2,
    },
]


# No @ContractOnly axioms are consumed by this spec: there are no opaque callees, and
# the whole content-type selection (`finalContentType` / `encodingContentType`) is
# modeled DEEPLY over transparent `Option String` carriers. The axiom lane is empty
# here and belongs to G-AX regardless.
AXIOM_TESTS = []
