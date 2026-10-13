"""properties.py — G-PBT falsification battery for django__django-17087 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region is changed — which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct buildReference`` obligation
survives with a byte-identical header) and swaps in a candidate implementation,
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: it must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted query):

  buildReference (module : String) (clsChain : List String)
                 (memberName : String) return (out : List String)
    require clsChain ≠ []
    ensures out = referencePath module clsChain memberName        -- (C1)
    ensures out.length = clsChain.length + 2                      -- (C2)
    ensures out.head? = some module                               -- (C3)
    ensures out.getLast? = some memberName                        -- (C4)

The modeled behaviour is the assembly of a DOTTED REFERENCE to a member reached
through a chain of enclosing qualifiers: the module path, then EVERY enclosing
qualifier name in order (outermost first), then the member's own name. The
reference is modeled as the list of its components rather than one fused string
(mapping.md §2: the ``.``-join is an order-preserving injection on these
dotted-identifier components, so component-list equality ⇔ emitted-string
equality). All three inputs are read-only — none is ``mut`` and nothing is
mutated (directive 5).

  Load-bearing clauses, and what each independently pins:
    (C1) out = referencePath module clsChain memberName — the DISCRIMINATING
         clause. It pins the reference to the FULL chain ``clsChain``, in order:
         a member reached through several nested qualifiers is named by the whole
         chain, never by the innermost qualifier alone and never with the outer
         ones dropped or permuted. Every rival below violates C1; one of them
         (``weak-reversed-chain``) violates ONLY C1, which is what isolates C1's
         ORDER content from the three structural clauses.
    (C2) out.length = clsChain.length + 2 — the component COUNT: exactly the
         module, the whole chain, and the member, with nothing fused away and
         nothing spurious added.
    (C3) out.head? = some module — the reference BEGINS at the module path.
    (C4) out.getLast? = some memberName — it ENDS exactly at the member's own
         name, with no trailing component and nothing glued onto it.

  There is no opaque answer-key oracle to echo: the ``axioms`` region declares no
  ``axiom`` (the components are plain data already in hand, modeled as the free
  inputs), and ``referencePath`` is a concrete structural ``def`` over those same
  inputs, so C1 is GROUNDED in the input carrier per directive 8. A rival cannot
  satisfy C1 by echoing anything — it has to actually assemble the components.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts a WIDER function returning a PAIR: the rendered reference AND the
accompanying module-import line, over four inputs (module, the owning
qualifier's bare innermost name, its full qualifier chain, the member name),
with the reference carried as a flat sequence of code points. This bundle models
only the purely functional core the fix turns on — HOW the enclosing chain enters
the reference — as a single ``List String`` of components. Two consequences:

  * The import line is NOT modeled here: it is unchanged behaviour that
    surrounds the modeled assembly (mapping.md §1), so the nagini rival attacking
    it has nothing to land on. Reported as an omission in the footer, not faked.
  * Conversely, the component-list carrier makes ORDER and the HEAD component
    independently attackable structure, where nagini's flat code-point
    concatenation fused them into a single sequence equality. Two rivals here
    (``weak-reversed-chain``, ``weak-drop-module``) have no nagini counterpart
    for exactly that reason — they are carrier-specific coverage of C1's order
    content and of C3, not padding.

  Note also that the nagini carrier passes the bare innermost qualifier name as
  a SEPARATE fourth input, so its central rival keys the reference on that input
  instead of the chain. This carrier has no such input: the innermost name is
  recoverable FROM the chain (``clsChain.getLast!``), so the same rival is
  re-expressed as collapsing the chain to its last element — the same wrong
  behaviour, spelled in this carrier's vocabulary.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS, no substitute fabricated. Lean and Velvet are
    referentially transparent: there is no heap, no aliasing, and no fractional
    permission, so there is no read-only input a rival could overwrite to satisfy
    a postcondition vacuously. The nagini sibling makes this class MANDATORY
    because its four inputs are held at half permission; that obligation has no
    image here, and the frozen method declares no ``mut`` binder at all.
  * WRONG-CHAIN-COMPONENT — APPLIES, and is the heart of the reject surface:
    a rival that names the member by the innermost enclosing qualifier alone,
    dropping every outer one (``weak-collapse-innermost``).
  * PARTIAL-DOMAIN near-misses — APPLY: a rival that fuses the last qualifier
    onto the member name (a missing separator), and one that appends a spurious
    empty trailing component (an extra separator). Both agree with the frozen
    spec on part of the structure and miss on the rest.
  * UNGROUNDED-ORACLE ECHO — N/A. ``referencePath`` is a concrete structural def
    over the very inputs the method receives, not an axiomatized oracle, so
    there is no answer-key to echo. (The nagini sibling reached the same
    conclusion about its own reference helpers.)
  * IMPORT-LINE attacks — NO COUNTERPART (see CARRIER NARROWING).

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each witness reaches the post-image through Velvet's own tester machinery:
``buildReferenceTester <module> <clsChain> <memberName> = false`` says the
extracted program's result VIOLATES the postcondition at that concrete input.
Checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. All inputs are concrete string/list literals — no
opaque term is involved, so ``decide`` computes and no witness needs to condition
on the carrier (hence no witness binds anything, and there are no assumptions
that could be jointly unsatisfiable).

The five rivals are refuted at FIVE DISTINCT input points, and every input binder
is varied across them (``pts=5``):
  * ``module``      — "mod_a" / "pkg.sub" (a dotted path) / "alpha" / "beta" /
                      "gamma"
  * ``clsChain``    — lengths 1, 2, 2, 2 and 3, with distinct contents. The
                      length-1 point matters specifically: on a single-qualifier
                      chain the collapse rival AGREES with the frozen spec, so
                      the near-miss refuted there (``weak-fuse-member``) is
                      demonstrated on a sub-domain where the central rival is
                      indistinguishable from gold — its rationale claims a
                      sub-domain the manifest actually exhibits.
  * ``memberName``  — "m1" / "build" / "go" / "run" / "do_it"
No two rivals share a witness: each is refuted at the input that distinguishes
IT, and each half of every witness was machine-checked (elaborates against the
rival, fails against the frozen solution).

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` — no outside
callee contract is consumed, and mapping.md §3 records no A-reference either
(the assembly is modeled deeply, and its fidelity is checked end-to-end by
G-CONF rather than G-AX, so this bundle ships no ``axiom_check.py``). The nagini
sibling's single AXIOM_TESTS probe validated ITS deep reference helpers against
the real rendering; that is the axiom lane's job, which this gate ignores, so it
is dropped rather than ported (footer).
"""
from pathlib import Path

INSTANCE = "django__django-17087"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen assembly body plus the closing
# ---- marker, so every swap lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap). The `-- impl-end` marker is re-appended
# ---- by `_impl`, so no variant can leak an edit past the region boundary.
_IMPL = ("    let out := (module :: clsChain) ++ [memberName]\n"
         "    return out\n"
         "    -- impl-end")

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header survives, which every variant keeps
# ---- byte-identical). NO case below retunes it: each soundness reshape returns
# ---- a value the frozen script already closes, so the proof region is left
# ---- untouched everywhere. Asserted present so the manifest breaks loudly if
# ---- the frozen solution ever changes.
_PROOF = ("prove_correct buildReference by\n"
          "  loom_solve\n"
          "  all_goals simp_all [referencePath]")
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced (the
    closing `-- impl-end` marker is re-appended)."""
    return _swap(_BASE, _IMPL, new_body + "\n    -- impl-end")


# ---- witness preamble. `buildReferenceTester <args> = false` says the extracted
# ---- program's result violates the method's postcondition at that input. The
# ---- method's only `require` is `clsChain ≠ []`, and every witness below passes
# ---- a NON-EMPTY chain, so each input genuinely reaches the postcondition
# ---- rather than passing vacuously through a violated precondition.
_TESTER = (
    "extract_program_for buildReference\n"
    "prove_precondition_decidable_for buildReference\n"
    "prove_postcondition_decidable_for buildReference\n"
    "derive_tester_for buildReference\n\n"
)


def _witness(module, chain, member):
    chain_lit = "[" + ", ".join(f'"{c}"' for c in chain) + "]"
    return (_TESTER
            + f'example : buildReferenceTester "{module}" {chain_lit} '
              f'"{member}" = false := by\n  decide\n')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen spelling of the assembly). Every
    # control below leaves the proof region untouched: the frozen tactic script
    # closes each one unchanged — no new lemma, no induction, no proof
    # weakening. There is no oracle to echo, so each control does the real work
    # of assembling the components in order.
    #
    # STRENGTH OF A CONTROL — the distinction these three cases are graded on.
    # A reshape that is DEFINITIONALLY EQUAL to the frozen assembly is closed by
    # the very same reduction that closes gold, so it cannot detect over-fitting:
    # it passes by construction whatever the spec says. Such a control is honest
    # but decorative. `pos-cons-assoc` is of that kind and is labelled as such
    # rather than advertised as an over-fit probe. The other two are NOT
    # definitionally equal to `(module :: clsChain) ++ [memberName]` — `rfl`
    # fails on both equations, machine-checked — so they reach the frozen script
    # with a goal it has to actually close via `referencePath`, which is what a
    # SPEC-TOO-STRONG probe has to do to mean anything.
    # =====================================================================
    {
        "id": "pos-cons-assoc",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: re-associate the assembly — cons the module onto the
        # already-terminated chain, rather than terminating the consed chain.
        # Same component sequence, different bracketing.
        "module": _impl("    let out := module :: (clsChain ++ [memberName])\n"
                        "    return out"),
        "rationale": (
            "re-associating the assembly (cons the module onto "
            "`clsChain ++ [memberName]` instead of appending `[memberName]` to "
            "`module :: clsChain`) yields the identical component sequence, so "
            "C1 still discharges and C2/C3/C4 follow as before. A "
            "structurally-different but CORRECT reshape must verify; if it "
            "fails => SPEC-TOO-STRONG (the spec would be pinned to one "
            "bracketing of an associative assembly rather than to the reference "
            "it denotes). Ports the nagini sibling's statement/expression "
            "reorder positive. STRENGTH: WEAK, and recorded as weak rather than "
            "overstated — `(m :: c) ++ [n]` and `m :: (c ++ [n])` are "
            "DEFINITIONALLY EQUAL (`List.cons_append` holds by `rfl`, "
            "machine-checked), because `++` recurses on its left argument and a "
            "cons head is already in normal form. So this control is closed by "
            "the same reduction that closes gold and would pass against a spec "
            "over-fit to the frozen bracketing. It is retained as a cheap "
            "statement-shape control and as the port of its nagini counterpart; "
            "the load-bearing SPEC-TOO-STRONG evidence is `pos-front-append` "
            "and `pos-foldr-chain`, whose equations `rfl` does NOT close."
        ),
    },
    {
        "id": "pos-front-append",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build inner-to-outer — the terminated chain is bound to a
        # named local, then the module path is consed on. The tail is built by a
        # REVERSE ROUND TRIP rather than by `++ [memberName]`, so the resulting
        # equation is NOT definitionally equal to the frozen assembly: the frozen
        # script has to close it through `referencePath` rather than by the
        # reduction that already closes gold.
        "module": _impl("    let tail := (memberName :: clsChain.reverse).reverse\n"
                        "    let out := module :: tail\n"
                        "    return out"),
        "rationale": (
            "assembled inner-to-outer through a named intermediate: the chain "
            "terminated by the member name is bound to a local, then the module "
            "path is consed on. The tail is produced by a reverse round trip — "
            "`(memberName :: clsChain.reverse).reverse` — which denotes exactly "
            "`clsChain ++ [memberName]` but is NOT definitionally equal to it: "
            "`rfl` FAILS on `c ++ [n] = (n :: c.reverse).reverse` "
            "(machine-checked), since `reverse` cannot reduce under a variable "
            "list. That is what makes this a real SPEC-TOO-STRONG probe rather "
            "than a restatement — the goal reaching the frozen tactic script is "
            "one the gold reduction does NOT already close, so it exercises "
            "C1-C4 against a genuinely different route to the same reference. "
            "Ports the nagini sibling's tail-then-front build positive (which "
            "assembled the reference right-to-left through named "
            "intermediates); if it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-foldr-chain",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: thread the member name through a fold over the chain instead
        # of appending it. A different RECURSION shape (foldr over clsChain, not
        # `++`), so again not definitionally equal to the frozen assembly.
        "module": _impl("    let out := module :: clsChain.foldr\n"
                        "               (fun c acc => c :: acc) [memberName]\n"
                        "    return out"),
        "rationale": (
            "the chain is threaded onto the member name by an explicit FOLD "
            "rather than by list append: `clsChain.foldr (fun c acc => c :: acc) "
            "[memberName]` rebuilds the same tail through a different recursion "
            "operator. Correct (foldr with cons over a starting list is append), "
            "so C1-C4 must all still discharge. Like `pos-front-append` and "
            "unlike `pos-cons-assoc`, this is NOT definitionally equal to the "
            "frozen assembly — `rfl` FAILS on `c ++ [n] = c.foldr (fun x acc => "
            "x :: acc) [n]` (machine-checked), because `foldr` is stuck on a "
            "variable list — so the frozen script must close a goal the gold "
            "reduction leaves open. ADDED with no nagini counterpart: a second "
            "INDEPENDENT non-defeq route to the reference, so the "
            "SPEC-TOO-STRONG evidence does not rest on one reshape whose only "
            "trick is `reverse`. If it fails => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's `require clsChain ≠ []` could in principle
    # exclude the very inputs the fix is about, and a post-image no impl can
    # meet reads exactly like a post-image every impl meets. This case
    # discharges an in-region `assert` at a DISCRIMINATING nested shape (a
    # two-qualifier chain, where naming by the innermost qualifier alone differs
    # from naming by the whole chain): the precondition admits it, and at that
    # input the post-image is both satisfiable and non-degenerate — the required
    # reference is a definite component list AND is distinct from the collapsed
    # one. The frozen impl body is kept verbatim below the assert, so the
    # method's own obligation still discharges and the assert is live.
    # =====================================================================
    {
        "id": "admiss-nested-chain-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            '      ((["Outer", "Inner"] : List String) ≠ []\n'
            '       ∧ referencePath "mod_a" ["Outer", "Inner"] "m1"\n'
            '         = ["mod_a", "Outer", "Inner", "m1"]\n'
            '       ∧ referencePath "mod_a" ["Outer", "Inner"] "m1"\n'
            '         ≠ ["mod_a", "Inner", "m1"]))\n'
            "    let out := (module :: clsChain) ++ [memberName]\n"
            "    return out"),
        "rationale": (
            "admissibility at the shape the fix is ABOUT: a member reached "
            "through two enclosing qualifiers. The assert establishes (a) the "
            "precondition `clsChain ≠ []` admits that chain, so the "
            "discriminating sub-domain is not excluded by the require clause "
            "(else PRECOND-TOO-STRONG and every rival would pass vacuously); "
            "(b) the post-image at that input is SATISFIABLE — the required "
            "reference is a definite four-component list; and (c) it is "
            "NON-DEGENERATE — that reference is distinct from the one naming the "
            "member by the innermost qualifier alone, so C1 really does separate "
            "the two behaviours rather than being met by both. The frozen impl "
            "body is preserved verbatim so C1-C4 still discharge. Re-aims the "
            "nagini sibling's admissibility caller, which built an F2P-shaped "
            "nested input and checked the contract was establishable on it."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # its OWN concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Every clause is attacked:
    # C1 by all five, C2 by four, C3 by weak-drop-module, C4 by
    # weak-fuse-member and weak-trailing-empty; weak-reversed-chain violates C1
    # ALONE, isolating C1's order content from the structural clauses.
    # =====================================================================
    {
        "id": "weak-collapse-innermost",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-change behaviour in this carrier's vocabulary: name the
        # member by the module, the INNERMOST enclosing qualifier only, and the
        # member name — dropping every outer qualifier in the chain. Violates C1
        # (the chain is not kept whole) and C2 (three components, not
        # chain.length + 2) whenever the chain has more than one qualifier.
        "module": _impl("    let out := [module, clsChain.getLast!, memberName]\n"
                        "    return out"),
        "refinement": (
            "this is the pre-change behaviour, and it is the defect the issue "
            "reports: a member reached through an enclosing qualifier chain is "
            "named as though it sat directly in the module, by its innermost "
            "enclosing qualifier alone. The issue states the contrast exactly — "
            "the emitted reference was the collapsed one where the required "
            "reference keeps the outer qualifier too — and the reference so "
            "emitted does not name anything importable, which is why the "
            "reported workflow errors out. The failing test asserts the emitted "
            "reference string EXACTLY, and this rival emits the collapsed "
            "reference at every input whose chain has more than one qualifier, "
            "so a real patch shipping it would NOT resolve. It is the pre-patch "
            "skeleton the bundle's own G-DIFF pre-image demonstrates."
        ),
        "rationale": (
            "REJECT from C1 (out = referencePath module clsChain memberName): "
            "the reference must contain the ENTIRE chain in order, and this "
            "rival keeps only its last element, so it also breaks C2 "
            "(out.length = clsChain.length + 2) for every chain longer than "
            "one. This is the CENTRAL rival — if it verified => SPEC-TOO-WEAK "
            "and the spec would not see the reported bug at all. Witness at "
            "module=\"mod_a\", chain=[\"Outer\", \"Inner\"], member=\"m1\": the "
            "shortest chain on which collapsing is observable. Ports the nagini "
            "sibling's wrong-carrier rival, which keyed the reference on the "
            "separate bare-innermost-name input; here that input does not exist, "
            "so the same wrong behaviour is spelled as collapsing the chain."
        ),
        "witness": _witness("mod_a", ["Outer", "Inner"], "m1"),
    },
    {
        "id": "weak-fuse-member",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: keep the whole chain, but GLUE the member name onto the
        # chain's last qualifier instead of contributing it as its own component
        # — a missing separator. Violates C1, C2 (one component short) and C4
        # (the last component is the fused text, not the member name).
        "module": _impl("    let out := (module :: clsChain.dropLast)\n"
                        "               ++ [clsChain.getLast! ++ memberName]\n"
                        "    return out"),
        "refinement": (
            "gluing the member name onto the innermost qualifier emits a "
            "reference with the separator between them missing, naming a single "
            "run-together identifier that does not exist. The failing test "
            "compares the emitted reference string exactly, so this would NOT "
            "resolve — and it fails on the ENTIRE tested domain, since every "
            "input has a non-empty member name. A real patch that assembled the "
            "components without their separator would be wrong everywhere, not "
            "only on nested inputs."
        ),
        "rationale": (
            "REJECT from C1, C2 (out.length = clsChain.length + 2: fusing two "
            "components into one leaves the reference a component short) and C4 "
            "(out.getLast? = some memberName: the final component is the fused "
            "text, not the member's own name). A NEAR-MISS that agrees with the "
            "frozen spec over MORE of the domain than the central rival, so it "
            "gets its own discriminating input: module=\"pkg.sub\" (a dotted "
            "module path), chain=[\"Host\"] — a SINGLE-qualifier chain, where "
            "weak-collapse-innermost agrees with gold exactly. Refuting it "
            "there demonstrates the sub-domain its rationale claims, and varies "
            "the clsChain binder down to length 1. Re-expresses the nagini "
            "sibling's missing-separator partial-domain rival, whose flat "
            "code-point carrier spelled the same defect as a dropped separator "
            "glyph."
        ),
        "witness": _witness("pkg.sub", ["Host"], "build"),
    },
    {
        "id": "weak-trailing-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss in the other direction: the whole correct reference, plus a
        # spurious EMPTY trailing component — a trailing separator. Right on
        # every prefix, wrong on the suffix. Violates C1, C2 (one component too
        # many) and C4 (the last component is empty, not the member name).
        "module": _impl('    let out := (module :: clsChain) ++ [memberName, ""]\n'
                        "    return out"),
        "refinement": (
            "appending an empty trailing component emits the correct reference "
            "followed by a dangling separator. The failing test asserts the "
            "emitted reference exactly, and a trailing separator makes it a "
            "different string that names nothing, so a real patch emitting it "
            "would NOT resolve. It is the mirror of the fused-component defect: "
            "both leave the reference off by exactly one component, in opposite "
            "directions."
        ),
        "rationale": (
            "REJECT from C1, C2 (out.length = clsChain.length + 2: one component "
            "TOO MANY) and C4 (out.getLast? = some memberName: the reference "
            "must END at the member's own name, with no trailing component). "
            "Pins the exact-assembly guarantee from the over-production side, "
            "where weak-fuse-member attacks it from the under-production side, "
            "so the count clause is attacked in both directions. Witness at "
            "module=\"alpha\", chain=[\"A\", \"B\", \"C\"] — the DEEPEST chain "
            "probed (length 3), member=\"go\". Re-expresses the nagini sibling's "
            "trailing-separator partial-domain rival."
        ),
        "witness": _witness("alpha", ["A", "B", "C"], "go"),
    },
    {
        "id": "weak-reversed-chain",
        "kind": "uniqueness",
        "expect": "reject",
        # The subtlest rival: every component is present, exactly once, and the
        # reference begins at the module and ends at the member name — but the
        # enclosing chain is emitted INNERMOST-first. Violates C1 and NOTHING
        # ELSE: C2, C3 and C4 all still hold, so C1's ORDER content is the sole
        # reason for the rejection.
        "module": _impl("    let out := (module :: clsChain.reverse) ++ [memberName]\n"
                        "    return out"),
        "refinement": (
            "emitting the enclosing qualifiers innermost-first inverts the "
            "nesting the reference is supposed to express, naming a path that "
            "does not resolve (the outer qualifier is looked for inside the "
            "inner one). The failing test asserts the emitted reference exactly, "
            "so a real patch that walked the enclosing chain in the wrong "
            "direction would NOT resolve — and this is a live failure mode for "
            "this fix specifically, since collecting an enclosing chain "
            "naturally yields it innermost-first and must be reversed to be "
            "emitted."
        ),
        "rationale": (
            "REJECT from C1 (out = referencePath module clsChain memberName) "
            "ALONE. This rival satisfies C2 (the count is right — every "
            "component appears exactly once), C3 (it still begins at the module "
            "path) and C4 (it still ends at the member name), so its rejection "
            "is attributable to C1's ORDER content and to nothing else. That is "
            "what makes it the load-bearing test of C1 as a whole-sequence "
            "equality rather than a bag-of-components check: if it verified => "
            "SPEC-TOO-WEAK, and the spec would be pinning WHICH qualifiers "
            "appear without pinning the nesting order they express. It also "
            "shows the three structural clauses cannot substitute for C1. NO "
            "nagini counterpart: that carrier fused the reference into a flat "
            "code-point sequence, so order was not separately attackable — this "
            "is carrier-specific coverage the component-list model exposes. "
            "Witness at module=\"beta\", chain=[\"P\", \"Q\"], member=\"run\"."
        ),
        "witness": _witness("beta", ["P", "Q"], "run"),
    },
    {
        "id": "weak-drop-module",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the module path entirely: emit the chain terminated by the member
        # name. Violates C1, C2 (one component short) and C3 (the reference
        # begins at the outermost qualifier, not the module path). The only
        # rival attacking C3.
        "module": _impl("    let out := clsChain ++ [memberName]\n"
                        "    return out"),
        "refinement": (
            "omitting the module path emits a bare qualifier-relative name with "
            "no module to resolve it against; nothing downstream can locate the "
            "member, and the accompanying module import would refer to a module "
            "the reference never mentions. The failing test asserts the emitted "
            "reference exactly — including its leading module path — so a real "
            "patch that rebuilt the reference from the qualifier chain and "
            "forgot to re-prefix the module would NOT resolve. A plausible "
            "regression precisely because this fix is about replacing the middle "
            "component of the reference, which invites rewriting the assembly."
        ),
        "rationale": (
            "REJECT from C3 (out.head? = some module — the reference must BEGIN "
            "at the module path), and also C1 and C2 (one component short). The "
            "ONLY rival attacking C3, so without it that clause would be "
            "defended by the positives alone and never falsified: a rival "
            "mishandling just the leading component would verify and the battery "
            "would not notice. It also varies the `module` binder in the way "
            "that matters most — by removing its contribution entirely. NO "
            "nagini counterpart: that carrier had no separate head-component "
            "clause to attack (its module was fused into the flat sequence), and "
            "its analogous rival attacked the separate import-line output, which "
            "this bundle does not model. Witness at module=\"gamma\", "
            "chain=[\"X\", \"Y\"], member=\"do_it\"."
        ),
        "witness": _witness("gamma", ["X", "Y"], "do_it"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 5 uniqueness rivals) plus 1 AXIOM_TESTS
# probe, over a WIDER function: four inputs (module, the owning qualifier's bare
# innermost name, its full qualifier chain, the member name) returning a PAIR
# (the rendered reference as a flat code-point sequence, and the accompanying
# module-import line), with two load-bearing postcondition clauses. THIS bundle
# models only the purely functional core the fix turns on — the assembly of the
# reference's COMPONENTS — as `buildReference (module, clsChain, memberName) ->
# List String` with four clauses (C1 the full-chain reference, C2 the component
# count, C3 the head, C4 the last). Every nagini case is accounted for below.
#
#   nagini case                    -> here
#   -----------------------------------------------------------------------
#   pos-direct-reorder             -> pos-cons-assoc                RE-SHAPED
#                                     (WEAK control: definitionally equal to the
#                                      frozen assembly, so it cannot detect
#                                      over-fitting; kept and labelled, not
#                                      counted as SPEC-TOO-STRONG evidence)
#   pos-tailbuild                  -> pos-front-append              RE-SHAPED
#                                     (built on a reverse round trip so the
#                                      equation is NOT defeq to gold's append)
#   admissibility-nested-shape     -> admiss-nested-chain-nondegenerate
#                                                                   RE-AIMED
#   wrong-carrier-simple-name      -> weak-collapse-innermost        PORTED
#                                     (re-expressed: the bare-innermost-name
#                                      input does not exist on this carrier, so
#                                      the rival collapses the chain to its last
#                                      element instead of reading a separate
#                                      input — same wrong behaviour)
#   partial-domain-missing-dot     -> weak-fuse-member          RE-EXPRESSED
#                                     (a dropped separator glyph becomes two
#                                      components fused into one)
#   partial-domain-trailing-dot    -> weak-trailing-empty       RE-EXPRESSED
#                                     (a spurious trailing separator glyph
#                                      becomes a spurious empty component)
#   frame-mutation-module          -> OMITTED: VACUOUS CLASS. Lean and Velvet
#                                     are referentially transparent — no heap,
#                                     no aliasing, no fractional permission — so
#                                     there is no read-only input a rival could
#                                     write to. The nagini case exists only
#                                     because its inputs are held at half
#                                     permission. No substitute fabricated.
#                                     INEXPRESSIBILITY MACHINE-CHECKED: writing
#                                     to an input needs a `mut` binder, i.e. an
#                                     edit to the method SIGNATURE, which lies
#                                     outside the impl region — the variant is
#                                     rejected by `variant_problems` as "spec
#                                     view differs (same_spec failed)", so no
#                                     in-scope rival of this class can exist.
#   drop-import-prefix             -> OMITTED: NO COUNTERPART (carrier
#                                     narrowing). The accompanying module-import
#                                     line is a SECOND output of the nagini
#                                     function and is unchanged behaviour
#                                     surrounding the modeled assembly
#                                     (mapping.md §1); this bundle returns only
#                                     the reference components, so there is no
#                                     clause for that rival to violate. The
#                                     nearest thing this carrier DOES expose —
#                                     losing the module path from the reference
#                                     itself — is covered by weak-drop-module,
#                                     which is a different defect against a
#                                     different clause (C3), not a stand-in.
#                                     INEXPRESSIBILITY MACHINE-CHECKED: emitting
#                                     a second output needs the return type to
#                                     become a pair, again a SIGNATURE edit
#                                     outside the impl region — rejected by
#                                     `variant_problems` as "spec view differs
#                                     (same_spec failed)".
#   AXIOM_TESTS/aref-render-soundness -> DROPPED: the axiom lane is G-AX's job
#                                     and this gate ignores AXIOM_TESTS. Moot
#                                     regardless: mapping.md §3 records no
#                                     axioms and no A-references for this bundle
#                                     (the assembly is modeled deeply and its
#                                     fidelity is checked end-to-end by G-CONF),
#                                     so it ships no axiom_check.py and G-AX is
#                                     a skip.
#   (no diverge-*/nonterm-*/       -> nothing to port, and the class is CLOSED BY
#    weak-diverge case exists)        THE SEMANTICS. CORRECTED: an earlier version
#                                     of this row said that under `termination
#                                     "partial"` a diverging impl satisfies every
#                                     ensures clause vacuously and VERIFIES, so
#                                     the frozen spec ADMITS it, and filed a known
#                                     spec hole against an internal findings doc.
#                                     Line 4 reads "total", as it does in all 500
#                                     velvet bundles, and the `set_option`
#                                     elaborator itself opens `TotalCorrectness`
#                                     (Options.lean:169-186), so the cited cohort
#                                     has no referent. Under `total` a
#                                     postcondition is claimed of ALL runs, every
#                                     loop owes a strictly decreasing measure, and
#                                     a diverging rival is REJECTED. No reject
#                                     case is shippable even so, for a WITNESS
#                                     reason: the refusal fires at the `method`,
#                                     so no witness can elaborate against it.
#
# ADDED HERE with no nagini counterpart (carrier-specific coverage, not
# padding). Modeling the reference as a list of COMPONENTS rather than a flat
# code-point sequence gives the spec two structural clauses nagini's carrier
# fused away, and each needs its own attacker:
#   weak-reversed-chain   -> attacks C1's ORDER content in ISOLATION (C2, C3, C4
#                            all still hold), proving C1 is a whole-sequence
#                            equality and not a bag-of-components check.
#   weak-drop-module      -> the only attacker of C3 (the reference begins at the
#                            module path); without it C3 would be defended but
#                            never falsified.
#   pos-foldr-chain       -> a second positive whose equation is NOT
#                            definitionally equal to the frozen assembly, so the
#                            SPEC-TOO-STRONG evidence rests on two independent
#                            non-defeq routes (a reverse round trip and a fold)
#                            rather than on one.
#
# COVERAGE SUMMARY. 4 obligations/clauses, each DEFENDED (4 verify cases) and
# ATTACKED: C1 by all 5 rivals, C2 by 4, C3 by weak-drop-module, C4 by
# weak-fuse-member + weak-trailing-empty. All 3 input binders are varied across
# the reject witnesses, at 5 DISTINCT input points (pts=5): `module` takes 5
# distinct values including a dotted path and, in weak-drop-module, is dropped
# from the output entirely; `clsChain` takes chains of length 1, 2, 2, 2, 3 with
# distinct contents — including the length-1 point where the central rival
# agrees with gold, so the near-miss refuted there demonstrates the sub-domain
# its rationale claims; `memberName` takes 5 distinct values. No binder is held
# at a single value by every witness.
# ---------------------------------------------------------------------------
