"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-11510 (lean).

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

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models a single forwarding step ``forward_with_source_read(lines)`` under a
fractional-permission read-only contract, whose postcondition pins the forwarded
line sequence to ``hook(take(n-2)) ++ drop(n-2)`` with an UNINTERPRETED @Pure
``hook``. This Lean bundle models the SAME behaviour with a RICHER, referentially
transparent carrier: one total function returning an ``InsertOutcome`` with TWO
observable components — ``emitted`` (what payload, if any, is offered to the
hook) and ``outputLines`` (the line list finally parsed) — guarded by a
``hasListeners`` flag that nagini did not model. So the nagini cases carry over
as attacks on the two pinned conjuncts, and the extra structure (the emitted
payload, its document-name tag, and the no-listener guard branch) admits
additional carrier-specific rivals. The per-case mapping (or principled
omission) is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior, ``problem_spec_includedSource``). The
postcondition pins ``result`` to a single grounded computation over the inputs,
as a conjunction of two independent top-level clauses:

  * ``emitted`` — offered payload: ``some (docname, body)`` when a hook is
    registered (``docname`` derived from ``path`` via the opaque carrier, ``body``
    = the included lines with the trailing two marker lines removed and joined),
    else ``none``. The nagini "which region is offered" discriminator lives here:
    ``body`` must be exactly the markers-excluded prefix, joined.
  * ``outputLines`` — parsed line list: ``splitLines (srcRead body) ++ markers``
    when a hook is registered (the rewritten body re-split, with the two marker
    lines re-appended unchanged), else the input ``lines`` verbatim.

The BEHAVIOURAL DISCRIMINATOR (the fix): when a hook IS registered, the included
body is offered to the hook and its (possibly rewritten) result is what gets
parsed — included content must not bypass the hook — while the two trailing
marker lines are never offered and are preserved verbatim. The pre-fix behaviour
forwarded the included lines without offering them to the hook at all; the
``rival-forward-verbatim`` case below IS that pre-fix behaviour.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — the PERMISSION half is vacuous, the
    OBSERVABLE half is not. Lean is referentially transparent, so there is no
    heap permission to overwrite and no aliasing to exploit: the nagini rival's
    *rejection mechanism* (a store through a half-permission reference) has no
    instance here. But what that mechanism was protecting — the received line
    list must reach both components AS RECEIVED, never through a tampered copy —
    is a value-level property, and on this carrier it is expressible and
    refutable directly: ``rival-tamper-input`` below rebinds ``lines`` to a
    modified copy before deriving the body, and the ``emitted`` pin refutes it at
    a concrete input. Recording this class as wholly inexpressible would have
    left the port's only frame-discipline probe unlanded, so the substitute is
    NOT fabricated — it is the same obligation carried by the pin instead of by a
    permission.

  * OFFER-COUNT / DUPLICATE-EFFECT — VACUOUS, and MEASURED so rather than
    assumed. Three nagini rivals (``rival-duplicate-offer``,
    ``rival-extra-offer-full-lines``, ``rival-forge-place-second-offer``) turn on
    HOW MANY TIMES the hook is offered text, a quantity nagini rations with a
    permission and separates from the returned value. On this carrier ``srcRead``
    is a pure function, so an extra or duplicated application is not an extra
    effect — it produces a term definitionally equal to gold's. Built both
    shapes against the frozen spec and both VERIFY (exit 0): the gold body with a
    discarded second ``srcRead body``, and the gold body with a discarded
    ``srcRead (joinLines lines)`` over the full list. They verify because they
    ARE gold as values, so they are not wrong impls and shipping them as reject
    cases would be vacuous padding. The class is genuinely collapsed by
    referential transparency — not skipped for difficulty.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: both
    components are pinned to terms built only from the inputs (via the pure
    ``joinLines`` / ``splitLines`` and the total ``srcRead``); the only opaque
    leaf, ``pathToDocname``, is an unchanged path-normalising callee whose result
    is itself pinned into ``emitted`` (the impl cannot fill that tag with anything
    else), NOT an answer key for the modeled decision. There is no wrong echo that
    verifies. The nagini ``echo-attempt-honest`` positive control maps to the
    cheapest-implementation positive ``pos-inline-payload`` below.

  * REGION / VALUE — APPLIES. Rivals correct on part of the domain but diverging
    where the fix bites: forwarding verbatim (never offering the body), offering
    the FULL lines (markers included), holding out only ONE marker, forwarding
    verbatim on the empty-body sub-domain, discarding the re-split result, and
    (carrier-specific) emitting when no hook is registered or tagging the payload
    with the raw path instead of the derived document name.

  * DIRECTION / POSITION / IDENTITY of the offered text — APPLIES, and is a
    carrier-specific class nagini could not state, because there the offered
    region and the returned region were one uninterpreted ``hook`` application.
    Here ``emitted`` and ``outputLines`` are two independent observables, so the
    battery must also pin WHICH of the two texts is offered (the body handed to
    the hook, not the text handed back — ``rival-emit-rewritten``), WHERE the
    preserved marker lines sit in the parsed list (at the END, not the front —
    ``rival-markers-prepended``), WHICH line boundaries the re-split recognises
    (the full universal set, not LF alone — ``rival-naive-linesplit``), and that
    the sub-two-line boundary the ``Nat`` truncation admits is pinned like every
    other input (``rival-short-list-boundary``). All four were reached by writing
    new wrong impls against the frozen spec and confirming it rejects each one.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Each was checked to HOLD of its rival and to FAIL
on the frozen solution, so it discriminates rather than asserting a tautology.

The opaque ``pathToDocname`` never blocks refutation: it appears identically on
both sides of the ``emitted`` equation, so a witness attacking any OTHER part of
the payload (the ``none``/``some`` choice, or the ``body`` string) cancels it by
``injEq`` and finishes by ``decide`` on fully concrete data. The ONE rival that
attacks the document-name tag itself (``rival-raw-docname``) cannot compute
``pathToDocname`` — so it CONDITIONS on the carrier: under the single hypothesis
``pathToDocname "baz/baz.rst" ≠ "baz/baz.rst"`` the rival's tag (the raw path)
provably differs from the spec's, which is exactly the sub-domain where that
rival is wrong. The hypothesis is a single assumption about one opaque term, so
it is trivially satisfiable (not a contradictory binder pair).

BINDER / POINT SPREAD. The reject witnesses move every input binder rather than
fixing them at one convenient point: ``hasListeners`` takes both ``true`` and
``false``; ``srcRead`` takes the identity and a non-identity constant
(``fun _ => "Z"``); ``path`` varies (``"foo.rst"``, ``"p.rst"``,
``"baz/baz.rst"``); and ``lines`` ranges over 1-, 2-, 3-, 4- and 5-line inputs,
including BOTH boundaries the ``Nat`` truncation creates — the empty body at
n==2 (``rival-partial-empty-body``) and the saturating sub-marker case at n==1
(``rival-short-list-boundary``). Both top-level conjuncts (``emitted`` and
``outputLines``) are attacked, and the ``outputLines`` attacks separate the ways
that list can be wrong independently of one another: wrong CONTENT
(``rival-discard-resplit``), wrong marker POSITION at identical content
(``rival-markers-prepended``), and the wrong LINE-BOUNDARY SET in the re-split
itself (``rival-naive-linesplit``).

Counted honestly: THIRTEEN reject witnesses over TEN distinct
``(hasListeners, srcRead, path, lines)`` points, not thirteen distinct points.
Three rivals (``rival-forward-verbatim``, ``rival-markers-prepended``,
``rival-tamper-input``) refute at the same 3-line identity-hook point, and two
(``rival-discard-resplit``, ``rival-emit-rewritten``) share the constant-hook
point. That reuse is deliberate and is not padding: each of those rivals is
wrong in a DIFFERENT component at that shared input, so the witnesses discharge
different clauses of the same conjunction rather than re-probing one clause. But
the spread claim is about the ten points, and a reader should not infer more.

The n==2 boundary carries TWO rivals for the same reason, and they are not a
duplicate pair: ``rival-partial-empty-body`` attacks whether the hook is offered
anything there at all, and ``rival-alias-empty-body`` attacks which REGION is
offered once it is. The second is the only case in the battery whose refutation
is forced through ``emitted`` because ``outputLines`` provably cannot see it —
at that input under the identity hook the rival's parsed list is equal to gold's.

WHAT THE POSITIVES DO AND DO NOT SHOW. ``pos-reorder-locals`` and
``pos-inline-payload`` both keep the frozen ``Id.run do`` / ``if`` skeleton, so
between them they establish only that the spec tolerates renaming and inlining
locals — a weak reshape. ``pos-match-no-idrun`` was added to carry the real
weight: it drops the monadic wrapper entirely and case-splits with ``match``
rather than ``if``, so the impl's syntactic shape shares almost nothing with the
frozen one, and it must still verify. A reshape that could NOT be re-proven
would be a soundness hole in the spec; this one closes with the frozen tactic
script unchanged.

DIVERGENCE lane: PART vacuous and PART a known hole, and the split is decided by
whether the diverging term reaches an observable. This bundle's frozen solution
sets no ``loom.semantics.termination`` at all (no lean bundle in this corpus does;
the option is a velvet-family one), so there is no separate termination
obligation for a diverging rival to fail — the obligation is the single ``theorem
correct_includedSource``, and plain Lean's own totality requirement is what
stands in for it. Five diverging rival shapes were built and their exit codes
read (this paragraph previously claimed the second and third shapes below were
REJECTED; they are not, and the corrected reason is the interesting one):

  * a helper ``def`` with no decreasing measure is rejected by Lean itself
    (``fail to show termination for spinForever``, exit 1) BEFORE the spec is
    consulted — so the rejection attests to the elaborator, not to the
    postcondition;
  * marking that helper ``partial`` and binding its result to an UNUSED local
    makes the file VERIFY — exit 0, ``#print axioms`` clean. Not rejected. The
    divergence is discarded, so the returned ``InsertOutcome`` is the frozen term
    and the rival is gold as a value (confirmed separately: a
    ``implementation … = <the frozen body>`` equality check closes, exit 0);
  * an inline ``while true`` loop whose result is likewise discarded also
    VERIFIES (exit 0), for the same reason;
  * so to make divergence observable it has to FEED a component. A ``partial``
    helper applied to the body text before it is offered is genuinely REJECTED by
    the pin (exit 1, the frozen ``rfl`` fails against the wrapped body term) —
    but its refutation witness cannot be landed on this carrier. A concrete
    witness gets STUCK rather than deciding: reduction stalls at
    ``(pathToDocname "foo.rst").data.hasDecEq``, i.e. on the OPAQUE
    document-name carrier, and the gate reads a stuck build as
    ``witness-undecided`` rather than as a pass. A witness that CONDITIONS on the
    helper instead is barred by the witness-vocabulary rule (measured: the scope
    check reports the helper as "declared by the variant but not by the frozen
    solution, so its failure on gold would be an unknown name rather than a
    satisfied spec");
  * marking the MODELED function itself ``partial`` is refused by the elaborator
    (``could not prove that the type … is nonempty``, exit 1) — again the
    elaborator, not the spec.

So the class does not collapse to one verdict. Divergence that does not reach an
observable is VACUOUS on a total, referentially transparent carrier — the value
is gold's, and the spec is right to verify it. Divergence that DOES reach an
observable is rejected by the spec, but no witness makes that rejection
attributable, because every concrete refutation at a listener-registered input
must pass through the opaque document-name tag and gets stuck there. That
residue is the known hole, and it is recorded rather than padded with a rival
whose ``reject`` would rest on a reduction limit instead of on the spec.

AXIOM lane: EMPTY here. The bundle declares one ``opaque`` carrier
(``pathToDocname``, the unchanged path-normalising step) and consumes no
``axiom`` (the proof closes by ``rfl``). The axiom lane belongs to G-AX; this
gate ignores it, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-11510"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole gold impl do-block body (between the do header and -- impl-end). Used
# as one replaceable block so no stale local survives to mask a rejection.
_GOLD_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    -- Set aside the trailing two marker lines; join the rest into the body.\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    -- Tag with the document name derived from the included file's path.\n"
    "    let docname := pathToDocname path\n"
    "    -- Offer the body to the hook; take back the (possibly rewritten) text.\n"
    "    let modified := srcRead body\n"
    "    -- Re-split and re-attach the marker lines; this is what gets parsed.\n"
    "    let newLines := splitLines modified ++ markers\n"
    "    return { emitted := some (docname, body), outputLines := newLines }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
assert _BASE.count(_GOLD_BODY) == 1, "gold impl body landmark drift"

# The frozen proof body (proof region). Only the tactic body may change.
_FROZEN_PROOF = (
    "  intro hasListeners srcRead path lines\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  cases hasListeners <;> exact ⟨rfl, rfl⟩"
)
assert _BASE.count(_FROZEN_PROOF) == 1, "frozen proof landmark drift"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ---------------------------------------------------------------------------

# Structurally-different but CORRECT: markers computed first, docname next, the
# body given a different local name (`auth`), the re-split output bound to a
# single local. Same value flow, so the result is identical on every input and
# the frozen proof still closes (the locals zeta-reduce; `⟨rfl, rfl⟩` holds).
_POS_REORDER_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let markers := lines.drop (n - 2)\n"
    "    let docname := pathToDocname path\n"
    "    let auth := joinLines (lines.take (n - 2))\n"
    "    let out := splitLines (srcRead auth) ++ markers\n"
    "    return { emitted := some (docname, auth), outputLines := out }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_POS_REORDER = _swap(_BASE, _GOLD_BODY, _POS_REORDER_BODY)

# Cheapest-implementation positive (the grounded-oracle control): inline every
# local directly into the returned structure. No answer key to echo — the
# payload and the parsed lines are assembled from the inputs. Must verify; the
# frozen proof closes after the inlined terms reduce.
_POS_INLINE_BODY = (
    "  if hasListeners then\n"
    "    return { emitted := some (pathToDocname path, joinLines (lines.take (lines.length - 2))),\n"
    "             outputLines := splitLines (srcRead (joinLines (lines.take (lines.length - 2)))) ++\n"
    "               lines.drop (lines.length - 2) }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_POS_INLINE = _swap(_BASE, _GOLD_BODY, _POS_INLINE_BODY)

# STRONG RESHAPE positive: abandon the monadic skeleton altogether. No `Id.run`,
# no `do`, no `if` — the branch is a `match` on the Bool and each arm is a bare
# structure literal. Almost nothing of the frozen impl's syntactic form survives,
# which is the point: the two positives above both keep the `Id.run do`/`if`
# skeleton, so they only show the spec tolerates renaming and inlining. The value
# produced is identical on every input, so the frozen proof still closes.
_IMPL_HEAD = (
    "def implementation_includedSource\n"
    "    (hasListeners : Bool) (srcRead : String → String)\n"
    "    (path : String) (lines : List String) : InsertOutcome := Id.run do\n"
)
assert _BASE.count(_IMPL_HEAD) == 1, "impl header landmark drift"
_POS_MATCH_IMPL = (
    "def implementation_includedSource\n"
    "    (hasListeners : Bool) (srcRead : String → String)\n"
    "    (path : String) (lines : List String) : InsertOutcome :=\n"
    "  match hasListeners with\n"
    "  | true =>\n"
    "    { emitted := some (pathToDocname path, joinLines (lines.take (lines.length - 2))),\n"
    "      outputLines := splitLines (srcRead (joinLines (lines.take (lines.length - 2)))) ++\n"
    "        lines.drop (lines.length - 2) }\n"
    "  | false => { emitted := none, outputLines := lines }\n"
)
_POS_MATCH = _swap(_BASE, _IMPL_HEAD + _GOLD_BODY + "\n", _POS_MATCH_IMPL)

# ADMISSIBILITY. Discharge the obligation BY EVALUATION at the F2P-shaped
# hook-registered input (a rewriting hook, the nested-includes scenario), as a
# `have` inside the existing tactic body, then close the frozen obligation
# verbatim. Nothing is assumed: no new declaration, the theorem statement is
# byte-identical.
#
# The outcome argument is written out as CONCRETE LITERALS rather than as
# `implementation_includedSource <the same inputs>`. That is the whole substance
# of the case and it was measured, not assumed. Stated in the self-applied form
# `problem_spec P (implementation P)`, the `have` is a closed instance of the
# theorem being proven, so `⟨rfl, rfl⟩` closes it by matching the impl against
# itself — nothing in the pinned computation is ever evaluated, and the identical
# `have` closes at inputs the F2P does not exercise at all (measured: the same
# shape at `true (fun s => s) "" []` elaborates, exit 0). It could therefore not
# distinguish "the obligation is satisfiable at the F2P input" from "the
# obligation is satisfiable anywhere", which is exactly the PRECOND-TOO-STRONG
# reading this lane exists to test.
#
# Naming the outcome by literals forces the kernel to reduce both pinned
# components at that input: the offered payload's body text and the parsed line
# list, markers included, in position. Measured load-bearing — each of these
# perturbations of a single literal FAILS to elaborate: the parsed lines left
# un-rewritten, the offered body given as the rewritten text, the marker tail
# dropped, the marker tail moved to the front.
#
# The hook is written as an explicit branch on the body text rather than via
# `String.replace`, because `String.replace` does not reduce in the kernel here
# (measured: `"…".replace … = "…"` fails by both `rfl` and `decide +kernel`), so
# a `replace`-shaped hook would have made the `have` unclosable by evaluation and
# sent this case back to the self-applied form for a TOOLING reason. `splitLines`
# and the whole pinned computation DO reduce (`splitLines "a\nb" = ["a","b"]`
# closes by `rfl`), so the evaluating form is available on this carrier.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_includedSource true\n"
    "      (fun s => if s = \"The #magical foo.\" then \"The amazing foo.\" else s)\n"
    "      \"baz/baz.rst\" [\"The #magical foo.\", \"\", \"marker\"]\n"
    "      { emitted := some (pathToDocname \"baz/baz.rst\", \"The #magical foo.\"),\n"
    "        outputLines := [\"The amazing foo.\", \"\", \"marker\"] } := ⟨rfl, rfl⟩\n"
    + _FROZEN_PROOF
)
_ADMISS = _swap(_BASE, _FROZEN_PROOF, _ADMISS_PROOF)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ---------------------------------------------------------------------------

# (A) FORWARD-VERBATIM — the actual pre-patch behaviour (== Solution_prepatch).
# The included lines are forwarded WITHOUT being offered to the hook and nothing
# is emitted, even when a hook is registered. Both conjuncts fail at
# hasListeners=true: emitted is `none` where the spec pins `some (…)`.
_VERBATIM_BODY = "  return { emitted := none, outputLines := lines }"
_RIVAL_VERBATIM = _swap(_BASE, _GOLD_BODY, _VERBATIM_BODY)

# (B) OFFER-FULL-LINES — the markers-not-excluded bug. The FULL gathered lines
# (markers INCLUDED) are offered to the hook: body = join(lines.take n),
# markers = lines.drop n (empty). The emitted body is then the whole joined input
# rather than the markers-excluded prefix.
_FULL_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take n)\n"
    "    let markers := lines.drop n\n"
    "    return { emitted := some (pathToDocname path, body), outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_FULL = _swap(_BASE, _GOLD_BODY, _FULL_BODY)

# (C) ONE-MARKER — only the LAST line is held out of the hook instead of the
# final two: body = join(lines.take (n-1)), markers = lines.drop (n-1). The
# emitted body then contains the blank-line marker.
_ONE_MARKER_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take (n - 1))\n"
    "    let markers := lines.drop (n - 1)\n"
    "    return { emitted := some (pathToDocname path, body), outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_ONE_MARKER = _swap(_BASE, _GOLD_BODY, _ONE_MARKER_BODY)

# (D) PARTIAL-DOMAIN — correct whenever the body is non-empty (n > 2) but
# forwards verbatim (emits nothing) when the body is empty (n == 2, the
# two-markers-only include the model admits). On the n==2 sub-domain emitted is
# `none` where the spec pins `some (docname, "")`.
_PARTIAL_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    if n == 2 then\n"
    "      return { emitted := none, outputLines := lines }\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    return { emitted := some (pathToDocname path, body), outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_PARTIAL = _swap(_BASE, _GOLD_BODY, _PARTIAL_BODY)

# (E) DISCARD-RESPLIT — offers the body to the hook (emitted is correct) but
# forwards the ORIGINAL lines to be parsed instead of the re-split rewritten
# body. Isolates the `outputLines` conjunct: with a rewriting hook the parsed
# lines differ from the input while emitted still matches gold.
_DISCARD_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    return { emitted := some (pathToDocname path, body), outputLines := lines }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_DISCARD = _swap(_BASE, _GOLD_BODY, _DISCARD_BODY)

# (F) ALWAYS-EMIT — ignores the listener guard and runs the hook path even when
# no hook is registered. At hasListeners=false emitted is `some (…)` where the
# spec pins `none` (and outputLines is re-split rather than verbatim).
_ALWAYS_BODY = (
    "  let n := lines.length\n"
    "  let body := joinLines (lines.take (n - 2))\n"
    "  let markers := lines.drop (n - 2)\n"
    "  return { emitted := some (pathToDocname path, body), outputLines := splitLines (srcRead body) ++ markers }"
)
_RIVAL_ALWAYS = _swap(_BASE, _GOLD_BODY, _ALWAYS_BODY)

# (G) RAW-DOCNAME — tags the emitted payload with the raw `path` instead of the
# derived document name. Attacks the document-name component of `emitted`; refuted
# by conditioning on the opaque carrier (see witness).
_RAWDOC_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    return { emitted := some (path, body), outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_RAWDOC = _swap(_BASE, _GOLD_BODY, _RAWDOC_BODY)

# (H) EMIT-REWRITTEN — offers the right region but reports the WRONG one of the
# two texts: the payload carries the text the hook handed BACK rather than the
# text that was offered to it. `outputLines` is fully correct, so this isolates
# the identity of the offered text — a distinction that only exists because this
# carrier makes the offered payload and the parsed list two independent
# observables.
_EMIT_REWRITTEN_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    return { emitted := some (pathToDocname path, srcRead body),\n"
    "             outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_EMIT_REWRITTEN = _swap(_BASE, _GOLD_BODY, _EMIT_REWRITTEN_BODY)

# (I) MARKERS-PREPENDED — keeps the two marker lines and keeps them unrewritten,
# but re-attaches them at the FRONT of the parsed list instead of the end. Every
# line is present and `emitted` is correct, so only the marker POSITION clause of
# `outputLines` can reject it.
_MARKERS_PREPENDED_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    return { emitted := some (pathToDocname path, body),\n"
    "             outputLines := markers ++ splitLines (srcRead body) }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_MARKERS_PREPENDED = _swap(_BASE, _GOLD_BODY, _MARKERS_PREPENDED_BODY)

# (J) SHORT-LIST-BOUNDARY — correct on every input with at least the two marker
# lines, but special-cases the sub-two-line inputs the `Nat` truncation admits
# (`n < 2`, where saturating subtraction makes the body empty and every line a
# marker): it treats the whole list as body, offers it, and drops the marker
# tail. Attacks the ONE input region no other rival moves.
_SHORT_LIST_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    if n < 2 then\n"
    "      return { emitted := some (pathToDocname path, joinLines lines),\n"
    "               outputLines := splitLines (srcRead (joinLines lines)) }\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    return { emitted := some (pathToDocname path, body),\n"
    "             outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_SHORT_LIST = _swap(_BASE, _GOLD_BODY, _SHORT_LIST_BODY)

# (K) TAMPER-INPUT — the frame-discipline probe, carried by the value pin instead
# of by a permission (see the ADVERSARIAL READ note above). The received line list
# is rebound to a MODIFIED copy before the body and markers are derived, so both
# components describe a list that was never received. Every step after the tamper
# is the frozen one, so the rejection is attributable to the tamper alone.
_TAMPER_BODY = (
    "  if hasListeners then\n"
    "    let lines := lines.set 0 \"X\"\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    return { emitted := some (pathToDocname path, body),\n"
    "             outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_TAMPER = _swap(_BASE, _GOLD_BODY, _TAMPER_BODY)

# (L) ALIAS-EMPTY-BODY — the SECOND way the n==2 boundary can be wrong, and a
# different one from `rival-partial-empty-body`. There the rival emits `none` on
# that sub-domain (the offer is skipped entirely); here the offer HAPPENS but over
# the wrong region: the whole gathered list is passed as the body (markers
# INCLUDED, i.e. the offered text aliases the received list) and the marker tail
# is not re-appended. Correct on every other input.
#
# This point is the one where the two observables come apart in the opposite
# direction from every other rival: under the IDENTITY hook the `outputLines`
# component AGREES with gold at n==2 (`splitLines "" ++ ["m1","m2"]` and
# `splitLines "m1\nm2"` are both `["m1","m2"]`), so the parsed-list clause cannot
# see this rival at all and only the `emitted` body — `""` for gold against
# `"m1\nm2"` for the rival — separates them. That makes it the sharpest available
# probe that the OFFERED REGION is pinned independently of what gets parsed.
_ALIAS_EMPTY_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    if n == 2 then\n"
    "      return { emitted := some (pathToDocname path, joinLines lines),\n"
    "               outputLines := splitLines (srcRead (joinLines lines)) }\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    return { emitted := some (pathToDocname path, body),\n"
    "             outputLines := splitLines (srcRead body) ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_ALIAS_EMPTY = _swap(_BASE, _GOLD_BODY, _ALIAS_EMPTY_BODY)

# (M) NAIVE-LINESPLIT — attacks the IDENTITY of the re-split step itself, the one
# named component of `outputLines` that no other rival moves. Every rival above
# takes `splitLines` as given and varies what is fed to it or what is appended to
# its result; this one keeps the whole gold value flow and substitutes a re-split
# that cuts at LF ONLY, ignoring the other universal line boundaries. Correct on
# every input whose rewritten body contains no non-LF boundary, so the two agree
# on the bulk of the domain and separate exactly on the boundary set.
#
# The replacement is written as an explicit recursive impl-region helper rather
# than via `String.splitOn`, and that is a measured necessity, not a style
# choice: `String.splitOn` does NOT reduce in the kernel here (measured: a
# `"x\ry".splitOn "\n" = …` equation fails by BOTH `decide +kernel` and `rfl`),
# so a `splitOn`-shaped rival elaborates and is rejected but admits no concrete
# witness — it would have been a second entry in the known-hole lane instead of a
# landable case. The recursive form reduces, so `decide` closes on it.
_NAIVE_SPLIT_HELPER = (
    "/-- A re-split that cuts only at LF, ignoring the other line boundaries. -/\n"
    "def naiveSplitGo : List Char → List Char → List (List Char)\n"
    "  | [], acc => [acc.reverse]\n"
    "  | c :: rest, acc =>\n"
    "      if c = '\\n' then\n"
    "        if rest.isEmpty then [acc.reverse]\n"
    "        else acc.reverse :: naiveSplitGo rest []\n"
    "      else naiveSplitGo rest (c :: acc)\n"
    "\n"
    "def naiveSplitLines (s : String) : List String :=\n"
    "  if s = \"\" then [] else (naiveSplitGo s.toList []).map String.mk\n"
)
_NAIVE_SPLIT_BODY = (
    "  if hasListeners then\n"
    "    let n := lines.length\n"
    "    let body := joinLines (lines.take (n - 2))\n"
    "    let markers := lines.drop (n - 2)\n"
    "    let modified := srcRead body\n"
    "    return { emitted := some (pathToDocname path, body),\n"
    "             outputLines := naiveSplitLines modified ++ markers }\n"
    "  else\n"
    "    return { emitted := none, outputLines := lines }"
)
_RIVAL_NAIVE_SPLIT = _swap(_BASE, _IMPL_HEAD,
                           _NAIVE_SPLIT_HELPER + "\n" + _IMPL_HEAD)
_RIVAL_NAIVE_SPLIT = _swap(_RIVAL_NAIVE_SPLIT, _GOLD_BODY, _NAIVE_SPLIT_BODY)


# ---- witness tactic bodies (checked HOLD-on-rival / FAIL-on-gold) ----

_W_VERBATIM = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  exact Option.noConfusion h1\n"
)

_W_FULL = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"foo.rst\" [\"p\",\"q\",\"r\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"foo.rst\" [\"p\",\"q\",\"r\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  rw [Option.some.injEq, Prod.mk.injEq] at h1\n"
    "  simp only [joinLines, List.length, List.take, List.drop] at h1\n"
    "  exact absurd h1.2 (by decide)\n"
)

_W_ONE_MARKER = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"p.rst\" [\"x\",\"y\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"p.rst\" [\"x\",\"y\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  rw [Option.some.injEq, Prod.mk.injEq] at h1\n"
    "  simp only [joinLines, List.length, List.take, List.drop] at h1\n"
    "  exact absurd h1.2 (by decide)\n"
)

_W_PARTIAL = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"foo.rst\" [\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"foo.rst\" [\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  exact Option.noConfusion h1\n"
)

_W_DISCARD = (
    "example : ¬ problem_spec_includedSource true (fun _ => \"Z\") \"foo.rst\" [\"a\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun _ => \"Z\") \"foo.rst\" [\"a\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨_, h2⟩\n"
    "  simp only [joinLines, splitLines, List.length, List.take, List.drop] at h2\n"
    "  exact absurd h2 (by decide)\n"
)

_W_ALWAYS = (
    "example : ¬ problem_spec_includedSource false (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource false (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  exact Option.noConfusion h1\n"
)

_W_RAWDOC = (
    "-- Conditioned on the opaque carrier: whenever the derived document name\n"
    "-- differs from the raw path, the rival's tag (the raw path) differs from the\n"
    "-- spec's — exactly the sub-domain where the rival is wrong. One assumption\n"
    "-- about one opaque term (satisfiable), not a contradictory binder pair.\n"
    "example (hpd : pathToDocname \"baz/baz.rst\" ≠ \"baz/baz.rst\") :\n"
    "    ¬ problem_spec_includedSource true (fun s => s) \"baz/baz.rst\" [\"a\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"baz/baz.rst\" [\"a\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  rw [Option.some.injEq, Prod.mk.injEq] at h1\n"
    "  exact hpd h1.1.symm\n"
)


_W_EMIT_REWRITTEN = (
    "example : ¬ problem_spec_includedSource true (fun _ => \"Z\") \"foo.rst\" [\"a\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun _ => \"Z\") \"foo.rst\" [\"a\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  rw [Option.some.injEq, Prod.mk.injEq] at h1\n"
    "  simp only [joinLines, List.length, List.take, List.drop] at h1\n"
    "  exact absurd h1.2 (by decide)\n"
)

_W_MARKERS_PREPENDED = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨_, h2⟩\n"
    "  simp only [joinLines, splitLines, List.length, List.take, List.drop] at h2\n"
    "  exact absurd h2 (by decide)\n"
)

# The n==1 point: `lines.length - 2` saturates to 0, so the spec pins the body to
# the join of NO lines (the empty text) and every line to the marker tail. The
# rival offers the whole list instead, so the `emitted` body differs. The literal
# length has to be reduced before `injEq` applies, hence the arithmetic lemmas.
_W_SHORT_LIST = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"foo.rst\" [\"a\"]\n"
    "    (implementation_includedSource true (fun s => s) \"foo.rst\" [\"a\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, List.length_cons, List.length_nil, Nat.reduceAdd,\n"
    "    Nat.reduceLT, reduceIte, Nat.reduceSub, List.take, List.drop, joinLines]\n"
    "  rintro ⟨h1, _⟩\n"
    "  rw [Option.some.injEq, Prod.mk.injEq] at h1\n"
    "  exact absurd h1.2 (by decide)\n"
)

_W_TAMPER = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"foo.rst\" [\"a\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨h1, _⟩\n"
    "  rw [Option.some.injEq, Prod.mk.injEq] at h1\n"
    "  simp only [joinLines, List.length, List.take, List.drop, List.set] at h1\n"
    "  exact absurd h1.2 (by decide)\n"
)


# The n==2 point again, but discriminating on the OFFERED region rather than on
# whether an offer happened. The `n == 2` guard has to be reduced before the `if`
# can be eliminated, so the length literal is normalised first (same reason the
# short-list witness carries arithmetic lemmas); after that the `emitted` bodies
# are two concrete `intercalate` terms and `decide` separates them. Note the
# refutation MUST come from `emitted`: at this input the rival's `outputLines`
# coincides with gold's under the identity hook.
_W_ALIAS_EMPTY = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"e.rst\" [\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"e.rst\" [\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, List.length_cons, List.length_nil, Nat.reduceAdd,\n"
    "    Nat.reduceEqDiff, beq_self_eq_true, Nat.reduceSub, reduceIte,\n"
    "    List.take, List.drop, joinLines]\n"
    "  rintro ⟨h1, _⟩\n"
    "  rw [Option.some.injEq, Prod.mk.injEq] at h1\n"
    "  exact absurd h1.2 (by decide)\n"
)


# The re-split boundary point. The body text carries a bare CR, which IS a line
# boundary for the modeled re-split and is NOT one for an LF-only cut, so at this
# input the two parsed lists provably differ while `emitted` and the marker tail
# agree. No intermediate normalisation of the equation is needed (and none is
# wanted: on the frozen solution `simp` closes the clause outright, so a witness
# that pre-normalised would die at the `simp` and hide WHY gold refuses it).
# Measured discrimination: on the rival `h2` is the concrete inequation between
# the two re-splits; on the frozen solution `h2 : True` — i.e. the clause is
# PROVED there — so `decide` reports `¬True` is false and the witness fails.
_W_NAIVE_SPLIT = (
    "example : ¬ problem_spec_includedSource true (fun s => s) \"r.rst\" [\"x\\ry\",\"m1\",\"m2\"]\n"
    "    (implementation_includedSource true (fun s => s) \"r.rst\" [\"x\\ry\",\"m1\",\"m2\"]) := by\n"
    "  unfold problem_spec_includedSource implementation_includedSource\n"
    "  simp only [Id.run, pure, reduceIte]\n"
    "  rintro ⟨_, h2⟩\n"
    "  exact absurd h2 (by decide)\n"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "structurally-different but CORRECT: markers computed first, the "
                     "document-name tag next, the body given a different local name, the "
                     "re-split output bound to one local. Value flow into both components "
                     "is identical on every input, so `result = implementation …` holds and "
                     "the frozen proof (`cases … <;> ⟨rfl, rfl⟩`) still closes after the "
                     "locals zeta-reduce. Must verify, else the postcondition is over-fit "
                     "to one statement order/local layout (SPEC-TOO-STRONG). Ports the "
                     "nagini reorder positive to the single modeled site.",
    },
    {
        "id": "pos-inline-payload",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": "the output is GROUNDED in the inputs (no opaque answer key to echo: "
                     "the payload and parsed lines are assembled from the inputs via the "
                     "pure helpers and the total hook effect). The cheapest impl inlines "
                     "every local directly into the returned structure; the assembled value "
                     "is unchanged on every input, so it must verify. Demonstrates the spec "
                     "is NOT echo-vulnerable (else this would be a reject case). Ports the "
                     "nagini echo-attempt-honest control; the opaque `pathToDocname` is a "
                     "pinned tag, not a modeled-decision oracle.",
    },
    {
        "id": "pos-match-no-idrun",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": "the STRONG reshape positive: the monadic skeleton is abandoned "
                     "entirely — no `Id.run`, no `do`, no `if`; the branch is a `match` on "
                     "the Bool and each arm is a bare structure literal. Almost none of the "
                     "frozen impl's syntactic form survives, so unlike the two positives "
                     "above (which keep the `Id.run do`/`if` skeleton and vary only local "
                     "names and inlining) this one actually tests that the postcondition "
                     "pins a VALUE rather than a shape. The value produced is identical on "
                     "every input, so it must verify; if it did not, the spec would reject a "
                     "faithful correct impl (SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation is discharged BY EVALUATION at the F2P-shaped "
                     "hook-registered input (a rewriting hook, the nested-includes "
                     "scenario): the outcome is named by CONCRETE LITERALS, so closing the "
                     "`have` reduces both pinned components at that input — the offered "
                     "payload's body text, and the parsed line list with the marker tail "
                     "present and in position — rather than matching the impl against "
                     "itself. Verifies (else the modeled behavior is unsatisfiable at "
                     "exactly the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG). Load-bearing, measured: perturbing any single "
                     "literal (parsed lines left un-rewritten, offered body given as the "
                     "rewritten text, marker tail dropped, marker tail moved to the front) "
                     "makes the `have` fail to elaborate. Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, the ground "
                     "instance is a `have` inside the existing tactic body. Ports the "
                     "nagini admissibility (F2P-shape) probe. NOTE the self-applied form "
                     "`problem_spec P (implementation P)` would NOT do: it is a closed "
                     "instance of the theorem being proven, closes without evaluating the "
                     "pinned computation, and was measured to close at degenerate inputs "
                     "the F2P never exercises.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "rival-forward-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_VERBATIM,
        "refinement": "this is the PRE-PATCH behaviour (== Solution_prepatch): the included "
                      "lines reach the parser without being offered to the hook and no "
                      "payload is emitted. Its faithful real patch is precisely the "
                      "un-patched inclusion that FAILS both F2P tests (the source-read "
                      "handler never sees the included document; the nested rewrite never "
                      "reaches the parsed body). So it would NOT resolve.",
        "rationale": "the discriminating bug the patch fixes. REJECT from the `emitted` "
                     "conjunct: at hasListeners=true the spec pins `some (docname, body)` "
                     "and the rival returns `none`. Binder spread: hasListeners=true, "
                     "identity hook, a 3-line input. If it verified => SPEC-TOO-WEAK "
                     "(admits the un-patched code).",
        "witness": _W_VERBATIM,
    },
    {
        "id": "rival-offer-full-lines",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FULL,
        "refinement": "offers the FULL gathered lines (the two trailing framing markers "
                      "INCLUDED) to the hook instead of the markers-excluded prefix. A "
                      "faithful real patch dropping the marker-exclusion would offer the "
                      "wrong text to the hook (markers parsed as authored content), so the "
                      "handler records / rewrites the wrong body and the F2P assertions on "
                      "the offered/parsed text fail. It would NOT resolve.",
        "rationale": "marker-not-excluded bug. REJECT from the `emitted` body: the spec "
                     "pins the joined markers-excluded prefix and the rival emits the whole "
                     "joined input. Refuted on a 5-line input (a distinct point from the "
                     "one-marker rival). If it verified => SPEC-TOO-WEAK (marker frame "
                     "hollow).",
        "witness": _W_FULL,
    },
    {
        "id": "rival-one-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ONE_MARKER,
        "refinement": "holds out only the LAST line from the hook instead of the final TWO. "
                      "A faithful real patch using a one-marker slice would offer the "
                      "blank-line marker to the hook and reattach only the trailing marker, "
                      "diverging from the two-marker frame and parsing the blank-line marker "
                      "as body — FAILING the F2P marker-exclusion assertion. So it would NOT "
                      "resolve.",
        "rationale": "off-by-one on the marker count. REJECT from the `emitted` body: the "
                     "spec pins the join of `take (n-2)` and the rival emits the join of "
                     "`take (n-1)`. Refuted on a 4-line input (distinct from the full-lines "
                     "rival's 5-line point). If it verified => SPEC-TOO-WEAK (marker count "
                     "unpinned).",
        "witness": _W_ONE_MARKER,
    },
    {
        "id": "rival-partial-empty-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PARTIAL,
        "refinement": "correct whenever the body is non-empty (n > 2) but forwards verbatim "
                      "(emits nothing) when the body is empty (n == 2, the two-markers-only "
                      "include the model admits). A faithful real patch of this shape (skip "
                      "the hook for an empty included body) would not offer the empty body "
                      "to the hook, diverging from gold (which always offers when a hook is "
                      "registered) — observable to a handler that records every offered "
                      "document. So it would NOT resolve.",
        "rationale": "partial-domain: pins only the n>2 sub-domain. REJECT from the "
                     "`emitted` conjunct on the n==2 boundary: the spec pins "
                     "`some (docname, \"\")` and the rival returns `none`. Moves the `lines` "
                     "binder to the 2-element empty-body boundary. If it verified => "
                     "SPEC-TOO-WEAK (empty-body sub-domain unpinned).",
        "witness": _W_PARTIAL,
    },
    {
        "id": "rival-discard-resplit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DISCARD,
        "refinement": "offers the body to the hook correctly but forwards the ORIGINAL "
                      "lines to be parsed instead of the hook's re-split rewritten body. A "
                      "faithful real patch of this shape would emit the event but discard "
                      "its effect, so the rewritten content never reaches the parser — "
                      "exactly the observable the issue reports (the replacement is computed "
                      "but does not make it into the output). It would NOT resolve.",
        "rationale": "REJECT from the `outputLines` conjunct (isolated: `emitted` still "
                     "matches gold): with a non-identity hook the spec pins "
                     "`splitLines (srcRead body) ++ markers` while the rival forwards the "
                     "input `lines`. Moves the `srcRead` binder to a non-identity constant. "
                     "If it verified => SPEC-TOO-WEAK (the parsed-lines clause hollow).",
        "witness": _W_DISCARD,
    },
    {
        "id": "rival-always-emit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ALWAYS,
        "refinement": "ignores the listener guard and runs the hook path unconditionally. A "
                      "faithful real patch that intercepted inclusion even with no "
                      "source-read listener registered would emit an event and re-split the "
                      "text where the original behaviour is a pure pass-through — perturbing "
                      "the no-listener path the P2P suite relies on (line accounting / "
                      "unchanged parse). It would NOT resolve.",
        "rationale": "REJECT from the guard branch of the `emitted` conjunct: at "
                     "hasListeners=false the spec pins `none` and the rival emits "
                     "`some (…)`. The ONLY rival moving the hasListeners binder to false, so "
                     "that input is demonstrated live rather than held fixed by every "
                     "witness. If it verified => SPEC-TOO-WEAK (the no-listener guard "
                     "unpinned).",
        "witness": _W_ALWAYS,
    },
    {
        "id": "rival-raw-docname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_RAWDOC,
        "refinement": "tags the emitted payload with the raw include path instead of the "
                      "derived document name. A faithful real patch that passed the raw path "
                      "as the document tag would route the source-read event under the wrong "
                      "docname, so a handler keyed on the derived name (the F2P test asserts "
                      "the derived `baz/baz` key) would not observe the offered text. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the document-name component of `emitted`. Refuted by "
                     "CONDITIONING on the opaque carrier: under "
                     "`pathToDocname \"baz/baz.rst\" ≠ \"baz/baz.rst\"` the rival's tag (the "
                     "raw path) provably differs from the spec's derived tag — the "
                     "sub-domain where the rival is wrong. The only rival attacking the "
                     "document-name tag and the only one moving `path` to \"baz/baz.rst\". "
                     "If it verified => SPEC-TOO-WEAK (the payload tag unpinned).",
        "witness": _W_RAWDOC,
    },
    {
        "id": "rival-emit-rewritten",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EMIT_REWRITTEN,
        "refinement": "reports the text the hook handed BACK as the payload that was "
                      "offered to it, instead of the text actually offered. A faithful real "
                      "patch of this shape would tell every registered handler that it was "
                      "given the already-transformed text, so a handler that records what it "
                      "was asked to transform records the wrong content, and a second "
                      "handler in the chain would be reasoning about the wrong input. The "
                      "parsed output is unaffected, so this diverges from gold only in what "
                      "is reported — which the F2P recording handler observes directly. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the body component of `emitted`, with `outputLines` left "
                     "fully correct — so the case isolates the IDENTITY of the offered text, "
                     "a distinction that exists only because this carrier exposes the "
                     "offered payload and the parsed list as two independent observables (in "
                     "the nagini model both were one `hook` application, so this rival had "
                     "no instance there). Refuted at the non-identity constant hook "
                     "`fun _ => \"Z\"`, where the offered body and the returned text "
                     "provably differ. If it verified => SPEC-TOO-WEAK (the spec would pin "
                     "only that SOMETHING was offered, not which text).",
        "witness": _W_EMIT_REWRITTEN,
    },
    {
        "id": "rival-markers-prepended",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_MARKERS_PREPENDED,
        "refinement": "preserves the two marker lines and keeps them unrewritten, but "
                      "re-attaches them at the FRONT of the parsed list instead of the end. "
                      "A faithful real patch of this shape would hand the parser the "
                      "provenance markers before the content they are supposed to close, so "
                      "the line accounting the surrounding machinery derives from them is "
                      "attributed to the wrong span — the P2P line-number expectations break "
                      "even though every line is still present. It would NOT resolve.",
        "rationale": "REJECT from the marker POSITION in `outputLines`. `emitted` matches "
                     "gold and the multiset of output lines matches gold, so neither the "
                     "payload clause nor any content-only reading of the parsed clause can "
                     "reject it — only the ORDER can. This is the third distinct way "
                     "`outputLines` can be wrong (the other two being wrong content, "
                     "`rival-discard-resplit`, and dropped markers); without it the spec's "
                     "`++ markers` could be a set union for all the battery shows. If it "
                     "verified => SPEC-TOO-WEAK (marker position unpinned).",
        "witness": _W_MARKERS_PREPENDED,
    },
    {
        "id": "rival-short-list-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SHORT_LIST,
        "refinement": "correct on every input carrying at least the two marker lines, but "
                      "special-cases the sub-two-line inputs: it treats the whole list as "
                      "body, offers that, and drops the marker tail. A faithful real patch of "
                      "this shape would branch on the gathered list being shorter than the "
                      "marker frame and handle it by a different rule than the one the "
                      "surrounding machinery guarantees, so the two behaviours disagree on "
                      "exactly the degenerate inputs the frame is supposed to make "
                      "impossible — an unreviewable special case whose observable effect is "
                      "an offered payload and a parsed list that no other code path can "
                      "produce. It would NOT resolve.",
        "rationale": "REJECT on the n<2 sub-domain, the ONE input region no other rival "
                     "moves. `lines.length - 2` saturates at 0 under `Nat` subtraction, so "
                     "the spec pins the body to the join of NO lines and the marker tail to "
                     "the whole list; the rival inverts both. Moves the `lines` binder to a "
                     "1-element list, the second of the two truncation boundaries (the other "
                     "being n==2, `rival-partial-empty-body`). If it verified => "
                     "SPEC-TOO-WEAK (the saturating-subtraction boundary unpinned, leaving "
                     "the spec silent on a domain it explicitly admits).",
        "witness": _W_SHORT_LIST,
    },
    {
        "id": "rival-tamper-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TAMPER,
        "refinement": "derives both components from a MODIFIED copy of the received line "
                      "list rather than from the list as received. This is the "
                      "carrier-appropriate instance of the nagini frame-mutation probe: "
                      "there the rejection came from the permission system, here from the "
                      "value pin, but the obligation is the same one — the received content "
                      "must reach both observables untouched. A faithful real patch that "
                      "rewrote its gathered input before offering it would hand the hook, "
                      "and the parser, content the author never wrote; no resolving patch "
                      "does this, so it would NOT resolve.",
        "rationale": "REJECT from the body component of `emitted`: the spec pins the body to "
                     "the join of the RECEIVED lines' markers-excluded prefix, and the rival "
                     "supplies the prefix of a tampered copy. Every step after the tamper is "
                     "the frozen one, so the rejection is attributable to the tamper alone "
                     "and not to a reshape. Lands the case class the port had recorded as "
                     "wholly inexpressible on a referentially transparent carrier: the "
                     "PERMISSION mechanism is indeed vacuous here, but the property it "
                     "protected is value-level and refutable. If it verified => "
                     "SPEC-TOO-WEAK (frame discipline hollow — the spec would not require "
                     "the received lines to be the ones used).",
        "witness": _W_TAMPER,
    },
    {
        "id": "rival-alias-empty-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ALIAS_EMPTY,
        "refinement": "at the empty-body boundary (n == 2) it offers the WHOLE gathered list "
                      "— the two trailing framing markers included, i.e. the offered text "
                      "aliases the received list — and forwards the rewritten result with no "
                      "marker tail re-appended. Correct on every other input. A faithful real "
                      "patch of this shape would, for an included file whose body is empty, "
                      "show every registered handler the framing markers as though they were "
                      "authored content and hand the parser the rewritten markers instead of "
                      "the preserved ones. That is observable to the recording handler the "
                      "F2P installs (it records the text it was offered, which would carry "
                      "the marker lines) and it breaks the marker frame the surrounding "
                      "machinery relies on. So it would NOT resolve.",
        "rationale": "REJECT from the `emitted` body on the n==2 boundary, and this is the "
                     "SECOND distinct way that boundary can be wrong — "
                     "`rival-partial-empty-body` attacks whether an offer happens there "
                     "(it emits `none`), while this one lets the offer happen and attacks "
                     "WHICH REGION is offered (the whole list rather than the "
                     "markers-excluded prefix, which at n==2 is the empty text). Sharper "
                     "than any other rival in one specific respect: at this input under the "
                     "identity hook the rival's `outputLines` COINCIDES with gold's "
                     "(`splitLines \"\" ++ [\"m1\",\"m2\"]` and `splitLines \"m1\\nm2\"` are "
                     "both `[\"m1\",\"m2\"]`), so the parsed-lines clause cannot separate it "
                     "and only the offered-region clause can — which is exactly the "
                     "independence of the two observables this carrier exposes. Ports the "
                     "nagini `rival-alias-empty-body` case, whose rejection there came from "
                     "the offered region having no matching licence at the boundary. If it "
                     "verified => SPEC-TOO-WEAK (the offered region unpinned at the "
                     "boundary, where the body is empty and every line is a marker).",
        "witness": _W_ALIAS_EMPTY,
    },
    {
        "id": "rival-naive-linesplit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NAIVE_SPLIT,
        "refinement": "keeps the entire gold value flow — the same offered payload, the same "
                      "hook application, the same preserved marker tail in the same position — "
                      "and changes only WHICH re-split turns the rewritten text back into "
                      "lines: it cuts at LF only, ignoring the other universal line "
                      "boundaries. A faithful real patch of this shape would re-split "
                      "hook-rewritten included content on newlines alone, so any handler that "
                      "returns text carrying a bare CR (or any other non-LF boundary) has its "
                      "output handed to the parser as ONE line where the surrounding machinery "
                      "counts several. The mapping notes a prior counterexample of exactly "
                      "this shape (listener output containing a bare CR), so this is a live "
                      "disagreement and not a hypothetical one. It would NOT resolve.",
        "rationale": "REJECT from the re-split component of `outputLines`, and it is the one "
                     "named part of the pinned computation NO other rival moves: every rival "
                     "above takes the modeled re-split as given and varies what is fed to it, "
                     "what is appended to its result, or where the markers land. Without this "
                     "case the spec's `splitLines` could be any LF-only cut for all the "
                     "battery shows — which matters here specifically because that helper "
                     "carries the full universal-line-boundary semantics and is the "
                     "differentially fuzzed part of the model. Refuted at a body text "
                     "containing a bare CR under the identity hook: a boundary for the modeled "
                     "re-split, not one for the rival's. If it verified => SPEC-TOO-WEAK (the "
                     "line-boundary set unpinned).",
        "witness": _W_NAIVE_SPLIT,
    },
]

# No AXIOM lane: the bundle consumes no `axiom` (the single `opaque pathToDocname`
# carrier is validated by G-AX as an A-reference, not a consumed contract). The
# nagini AXIOM_TESTS belong to the axiom gate and are dropped here.
AXIOM_TESTS = []
