"""properties.py — G-PBT falsification battery for sympy__sympy-15976 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct buildSymbolNode`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  buildSymbolNode (name : List Char) (subs sups : Option Node) (bold : Bool)
      return (out : Node)
    ensures out = buildSymbol name subs sups bold                    (C0 master)
    ensures (subs = none ∧ sups = none) → out.tag = "mi".toList      (C-mi)
    ensures (subs ≠ none ∧ sups = none) → out.tag = "msub".toList    (C-msub)
    ensures (subs = none ∧ sups ≠ none) → out.tag = "msup".toList    (C-msup)
    ensures (subs ≠ none ∧ sups ≠ none) → out.tag = "msubsup".toList (C-msubsup)
    ensures bold = true → out.isBold = true                          (C-bold)

The method assembles the single presentation node that represents one printed
variable, from its base name and the (already-rendered) subscript / superscript
nodes that are present exactly when the variable carries scripts. The desired
behavior — pinned by ``buildSymbol`` in the frozen ``pure`` region: with no
scripts the node IS the bare base-name identifier; with only subscripts a
subscript container of the name and the subscript node; with only superscripts a
superscript container; with both a sub-and-superscript container of the name,
then the subscript node, then the superscript node — and the requested bold
styling lands on that representing node itself. The load-bearing content is the
master equality C0 (``out = buildSymbol …``): the four tag clauses are its
observable projections, isolating the top node's kind on each script sub-domain,
and C-bold isolates the bold marker.

FOUR INPUT BINDERS, all read-only values: ``name`` (the base name), ``subs`` and
``sups`` (each ``none``/``some`` — whether that script is present, and which node
it is), and ``bold`` (whether the styling attribute is requested). The reject
witnesses vary EVERY binder: ``subs``/``sups`` across ``none`` and ``some`` (all
four script sub-domains are probed — bare, sub-only, sup-only, both), ``bold``
across both truth values, and ``name`` across four distinct base names, one
rival abusing ``name`` directly, since a rival that mishandled only one script
sub-domain, or dropped the name, or ignored bold on the bare branch, would slip
past a battery that pinned those binders. ``subs`` is additionally varied WITHIN
``some``, across a single-piece node and a multi-piece row container: C0 pins the
supplied script node's identity, not just its presence, so a rival that places a
rewritten node rather than the one it was handed diverges only on the multi-piece
sub-domain and needs a witness there.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``buildSymbolNodeTester … = false`` says the extracted
program's result violates the postcondition at that concrete input) and closes by
``decide``, checked in a file whose ``prove_correct`` block has been stripped so
no tactic script can mask the verdict. ``decide`` reduces the extracted program by
kernel computation; the postcondition compares two ``Node`` values, so the tester
needs ``DecidableEq Node`` to reduce — and the frozen ``Node`` inductive (nested
``List Node`` children) derives only ``Inhabited``. Each witness therefore FIRST
brings a structural ``DecidableEq Node`` into scope (a mutual boolean equality
with its soundness/reflexivity proofs, appended to BOTH the rival and gold files,
so it is the witness's own vocabulary and exists identically on both sides), then
extracts the tester and states the refutation at a fully concrete input. This is a
witnessing convenience only: the frozen spec and the ``Node`` type are untouched,
and each rival's divergence from ``buildSymbol`` is real at the witnessed input.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can overwrite
    (the nagini sibling writes to the read-only base-name list and is rejected for
    insufficient permission). This backend is referentially transparent: every
    parameter is an immutable value (this bundle declares no ``mut`` binder), there
    is no heap and no aliasing, so there is no read-only input to mutate and no
    substitute probe. Not fabricated. (See footer.)
  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the reject lane: the tag clauses
    pin the top node's kind on each script sub-domain and C0 pins the full node,
    so a rival that re-wraps one branch in a spurious outer identifier, swaps the
    sub/super child order, drops the name, mis-tags the bare branch, rewrites a
    supplied script node instead of placing it whole, or skips the bold marker
    diverges from ``buildSymbol`` at a concrete input.
  * UNGROUNDED-ORACLE ECHO — N/A. ``buildSymbol`` is a fully unfolded ``def`` over
    the method's own arguments (the ``axioms`` region is empty — no opaque answer
    key to echo); the only way to satisfy the postcondition is to assemble the
    node correctly, which the positive control does honestly.

WITNESS PLACEMENT. The seven reject witnesses sit at SEVEN DISTINCT input points
(pts=7). Between them they move ``subs`` and ``sups`` across ``none``/``some``
(covering all four script sub-domains), ``bold`` across both values, ``name``
across four base names, and the SHAPE of a supplied script node across a
single-piece node and a multi-piece row container, so the manifest demonstrates
the post-image's dependence on every binder — including on the script node's
identity, not merely its presence — rather than on a single pinned shape. No two
rivals share a witness: each fails on the sub-domain its clause governs.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15976"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each lies WHOLLY inside the impl region (6-space indent, so it does
# NOT collide with the twin `match` / `mkMi` / `setBold` text in the frozen
# `pure` region at 4-space / 2-space indent) and is unique in the file. _swap
# asserts both facts at load, so the manifest breaks loudly on any spec drift.
# ---------------------------------------------------------------------------

# The whole impl-region node-choice match (the executable surface a shape rival
# reshapes wholesale). Rivals that touch a single arm swap the arm alone.
_MATCH = (
    "      match sups, subs with\n"
    "      | none,     none     => mname\n"
    "      | none,     some sub => .elem \"msub\".toList false [mname, sub]\n"
    "      | some sup, none     => .elem \"msup\".toList false [mname, sup]\n"
    "      | some sup, some sub => .elem \"msubsup\".toList false [mname, sub, sup]")
assert _BASE.count(_MATCH) == 1, "impl match anchor drift"

_ARM_NONE = "      | none,     none     => mname"
_ARM_MSUB = "      | none,     some sub => .elem \"msub\".toList false [mname, sub]"
_ARM_MSUP = "      | some sup, none     => .elem \"msup\".toList false [mname, sup]"
_ARM_MSS = "      | some sup, some sub => .elem \"msubsup\".toList false [mname, sub, sup]"
_MNAME = "    let mname : Node := .elem \"mi\".toList false [Node.text name]"
_SETBOLD = "    let x := setBold core bold"
_IMPL_START = "    -- impl-start"
for _a in (_ARM_NONE, _ARM_MSUB, _ARM_MSUP, _ARM_MSS, _MNAME, _SETBOLD, _IMPL_START):
    assert _BASE.count(_a) == 1, f"anchor drift: {_a!r}"

# The frozen proof body (tactic script only; elided from the spec view). The
# admissibility case retunes it to also clear an in-region assert goal, without
# touching the byte-identical `prove_correct buildSymbolNode` statement.
_PROOF_GOLD = (
    "prove_correct buildSymbolNode by\n"
    "  loom_solve <;>\n"
    "    cases sups <;> cases subs <;>\n"
    "      simp_all [buildSymbol, mkMi, setBold, Node.tag, Node.isBold]")
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


# ---------------------------------------------------------------------------
# Witness preamble. The postcondition compares `Node` values, so the tester
# cannot `decide` without `DecidableEq Node`; the frozen `Node` derives only
# `Inhabited`. Every witness first brings a structural `DecidableEq Node` into
# scope (its OWN vocabulary — appended to both the rival and the gold file, so it
# exists identically on both sides and references nothing the variant adds), then
# extracts the tester and states the refutation at concrete literals so `decide`
# reduces the (straight-line) extracted program without getting stuck.
# ---------------------------------------------------------------------------
_DEC_EQ = """
mutual
def nodeBEq : Node → Node → Bool
  | Node.text a,        Node.text b        => a == b
  | Node.elem t1 b1 c1, Node.elem t2 b2 c2 => (t1 == t2) && (b1 == b2) && nodeListBEq c1 c2
  | _, _ => false
def nodeListBEq : List Node → List Node → Bool
  | [], [] => true
  | x :: xs, y :: ys => nodeBEq x y && nodeListBEq xs ys
  | _, _ => false
end
mutual
theorem nodeBEq_correct : ∀ a b : Node, nodeBEq a b = true → a = b
  | Node.text a,        Node.text b        => by simp [nodeBEq]
  | Node.elem t1 b1 c1, Node.elem t2 b2 c2 => by
      intro h
      simp only [nodeBEq, Bool.and_eq_true, beq_iff_eq] at h
      obtain ⟨⟨ht, hb⟩, hc⟩ := h
      subst ht; subst hb
      have := nodeListBEq_correct c1 c2 hc
      subst this; rfl
  | Node.text _, Node.elem _ _ _ => by simp [nodeBEq]
  | Node.elem _ _ _, Node.text _ => by simp [nodeBEq]
theorem nodeListBEq_correct : ∀ a b : List Node, nodeListBEq a b = true → a = b
  | [], [] => by simp [nodeListBEq]
  | x :: xs, y :: ys => by
      intro h
      simp only [nodeListBEq, Bool.and_eq_true] at h
      obtain ⟨hx, hxs⟩ := h
      have h1 := nodeBEq_correct x y hx
      have h2 := nodeListBEq_correct xs ys hxs
      subst_vars; rfl
  | [], _ :: _ => by simp [nodeListBEq]
  | _ :: _, [] => by simp [nodeListBEq]
end
mutual
theorem nodeBEq_refl : ∀ a : Node, nodeBEq a a = true
  | Node.text a => by simp [nodeBEq]
  | Node.elem t b c => by
      simp only [nodeBEq, Bool.and_eq_true, beq_self_eq_true, true_and]
      exact nodeListBEq_refl c
theorem nodeListBEq_refl : ∀ a : List Node, nodeListBEq a a = true
  | [] => by simp [nodeListBEq]
  | x :: xs => by
      simp only [nodeListBEq, Bool.and_eq_true]
      exact ⟨nodeBEq_refl x, nodeListBEq_refl xs⟩
end
instance : DecidableEq Node := fun a b =>
  if h : nodeBEq a b = true then .isTrue (nodeBEq_correct a b h)
  else .isFalse (fun heq => h (heq ▸ nodeBEq_refl a))

extract_program_for buildSymbolNode
prove_precondition_decidable_for buildSymbolNode
prove_postcondition_decidable_for buildSymbolNode
derive_tester_for buildSymbolNode
"""


def _tester(call):
    """A refutation witness: the `DecidableEq Node` + tester preamble, then a
    `decide`d claim that the extracted program violates the postcondition at one
    concrete input. `call` is the tester application that must equal `false`."""
    return _DEC_EQ + f"\nexample : {call} = false := by\n  decide\n"


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot verify the spec is
    # SPEC-TOO-STRONG. The gold matches on `sups, subs`; this reshaped impl
    # matches on `subs, sups` (arms permuted to the identical node on every
    # sub-domain). The frozen proof (`cases sups <;> cases subs <;> simp_all`)
    # still closes because it splits on both scrutinees regardless of order.
    # Observationally identical for every input.
    # =====================================================================
    {
        "id": "pos-control-match-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _MATCH,
            "      match subs, sups with\n"
            "      | none,     none     => mname\n"
            "      | some sub, none     => .elem \"msub\".toList false [mname, sub]\n"
            "      | none,     some sup => .elem \"msup\".toList false [mname, sup]\n"
            "      | some sub, some sup => .elem \"msubsup\".toList false [mname, sub, sup]"),
        "rationale": (
            "matching on `subs, sups` with the arms permuted lands on the SAME "
            "representing node as the gold `sups, subs` match on every script "
            "sub-domain, so `out = buildSymbol …` and all four tag clauses and "
            "C-bold still hold on the whole domain; the frozen proof splits on "
            "both scrutinees and closes unchanged. A correct reshape must verify, "
            "else the postcondition is SPEC-TOO-STRONG (rejects a faithful impl "
            "over the order the node choice is written)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require`, so the usual "a normal
    # input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like one every impl meets. This case discharges an
    # in-region `assert`, at the representative F2P-shaped input (a variable with
    # a subscript and no superscript, plain), that the post-image is concrete and
    # non-degenerate there: the representing node is exactly the subscript
    # container of the base-name identifier and the subscript node — NOT a bare
    # identifier and NOT an identifier re-wrapping a container. The surrounding
    # impl is kept verbatim so the method's own obligation still discharges; the
    # proof is retuned only to clear the extra assert goal by `rfl` (allowed — the
    # tactic body is elided from the spec view). The assert is live: a false claim
    # about that point leaves an unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START + "\n"
                  "    assert (with_name_prefix `admiss\n"
                  "      (buildSymbol \"x\".toList (some (Node.text \"2\".toList)) none false\n"
                  "        = Node.elem \"msub\".toList false [Node.elem \"mi\".toList false [Node.text \"x\".toList], Node.text \"2\".toList]))"),
            _PROOF_GOLD,
            "prove_correct buildSymbolNode by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "      | rfl\n"
            "      | (cases sups <;> cases subs <;>\n"
            "          simp_all [buildSymbol, mkMi, setBold, Node.tag, Node.isBold])"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "input: for a subscript-only variable it demands the representing node "
            "be exactly the subscript container of the base-name identifier and the "
            "subscript node — pinning the top kind AND the ordered children, not a "
            "bare identifier and not an identifier wrapping the container. The "
            "in-region assert must discharge (else the obligation is unsatisfiable "
            "/ degenerate at the point the fix cares about); the impl is kept "
            "verbatim so the method's own `ensures` still discharges."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. The frozen proof is kept
    # (it fails to close for the wrong impl — that is the rejection); attribution
    # to the spec comes from the witness, checked in a proof-stripped file.
    # =====================================================================

    # C-msub / C0 — subscript-only branch reverts to the pre-fix shape: the
    # representing node stays a bare identifier that wraps the subscript container
    # as its single child, instead of BEING the container.
    {
        "id": "weak-subs-outer-identifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ARM_MSUB,
            "      | none,     some sub => .elem \"mi\".toList false [.elem \"msub\".toList false [mname, sub]]"),
        "refinement": (
            "this is the pre-fix behavior on the subscript-only domain: the "
            "representing node is an identifier wrapping the subscript container as "
            "its only child, so its top kind is the identifier, not the subscript "
            "container. The failing scenario pins the top kind of a subscript-only "
            "variable to be the subscript container (with the identifier and the "
            "subscript node as its direct children); a real patch that left the "
            "outer identifier wrapper would render the extra enclosing element the "
            "scenario forbids and would NOT resolve."),
        "rationale": (
            "REJECT from C-msub (`(subs ≠ none ∧ sups = none) → out.tag = "
            "\"msub\".toList`): this returns tag `mi`; and independently from C0 "
            "(`out = buildSymbol …`), which on this sub-domain is the container "
            "itself, not an identifier wrapping it. Refuted at name=\"x\", "
            "subs=some(text \"2\"), sups=none, bold=false — the subscript-only "
            "sub-domain."),
        "witness": _tester(
            "buildSymbolNodeTester \"x\".toList (some (Node.text \"2\".toList)) none false"),
    },

    # C-msup / C0 — the mirror of the above on the superscript-only branch: it
    # re-wraps the superscript container in a spurious outer identifier. A near
    # miss to the subs rival — it agrees with gold on every domain EXCEPT
    # superscript-only, so it carries its own discriminating input (sups=some,
    # subs=none) and moves the sups binder to `some`.
    {
        "id": "weak-sups-outer-identifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ARM_MSUP,
            "      | some sup, none     => .elem \"mi\".toList false [.elem \"msup\".toList false [mname, sup]]"),
        "refinement": (
            "the pre-fix behavior on the superscript-only domain: the representing "
            "node is an identifier wrapping the superscript container. The failing "
            "scenario pins the top kind of a superscript-only variable to be the "
            "superscript container itself; a real patch leaving the outer "
            "identifier wrapper would emit the extra enclosing element the scenario "
            "forbids and would NOT resolve. Distinct from the subscript rival: it "
            "diverges only on the superscript-only domain, so it needs its own "
            "input."),
        "rationale": (
            "REJECT from C-msup (`(subs = none ∧ sups ≠ none) → out.tag = "
            "\"msup\".toList`): this returns tag `mi`; and from C0. Refuted at "
            "name=\"x\", subs=none, sups=some(text \"3\"), bold=false — the "
            "superscript-only sub-domain, moving the sups binder to `some`."),
        "witness": _tester(
            "buildSymbolNodeTester \"x\".toList none (some (Node.text \"3\".toList)) false"),
    },

    # C0 — combined (sub-and-superscript) branch swaps the sub/super child ORDER.
    # The top kind is still the sub-and-superscript container, so the tag clauses
    # all hold; only the master equality C0 is violated, and only when the two
    # script nodes differ. Abuses the both-scripts sub-domain (subs≠none ∧
    # sups≠none), which no other rival touches.
    {
        "id": "weak-combined-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ARM_MSS,
            "      | some sup, some sub => .elem \"msubsup\".toList false [mname, sup, sub]"),
        "refinement": (
            "the sub-and-superscript container is positional: the subscript node is "
            "the second child, the superscript node the third. Gold places the "
            "subscript node before the superscript node; this swaps them. On a "
            "variable carrying BOTH scripts, whose two script nodes differ, the "
            "scenario's ordered children check sees the wrong node in each slot; a "
            "real patch that appended the superscript before the subscript would "
            "produce that visibly different tree and would NOT resolve."),
        "rationale": (
            "REJECT from C0 (`out = buildSymbol …`), whose combined case is the "
            "container of [identifier, subscript node, superscript node] IN THAT "
            "ORDER; this returns the last two swapped, unequal whenever the "
            "subscript and superscript nodes differ (the tag clauses still hold, so "
            "C0 is the sole discriminator — verifying would leave the child order "
            "unpinned, partial-domain SPEC-TOO-WEAK). Refuted at name=\"x\", "
            "subs=some(text \"2\"), sups=some(text \"3\"), bold=false — the "
            "both-scripts sub-domain."),
        "witness": _tester(
            "buildSymbolNodeTester \"x\".toList (some (Node.text \"2\".toList)) (some (Node.text \"3\".toList)) false"),
    },

    # C-bold — applies bold styling only when the variable carries scripts,
    # silently skipping it on the bare-identifier branch. Abuses the bare
    # sub-domain WITH bold=true — the only case moving the bold binder to true.
    {
        "id": "weak-bold-drop-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SETBOLD,
            "    let x := match sups, subs with\n"
            "      | none, none => core\n"
            "      | _, _ => setBold core bold"),
        "refinement": (
            "gold applies the bold styling to the representing node for EVERY kind, "
            "including a bare identifier with no scripts. This applies it only when "
            "a script is present, so a plain bold variable with no scripts loses "
            "its bold marker. A real patch that set the bold attribute only inside "
            "the script branches would drop the bold styling on a bare bold symbol, "
            "which the bold-symbol scenarios observe, and would NOT resolve."),
        "rationale": (
            "REJECT from C-bold (`bold = true → out.isBold = true`): on the bare "
            "sub-domain with bold=true this leaves the node unstyled, so isBold is "
            "false; also from C0. Refuted at name=\"x\", subs=none, sups=none, "
            "bold=true — the bare sub-domain, moving the bold binder to true."),
        "witness": _tester(
            "buildSymbolNodeTester \"x\".toList none none true"),
    },

    # C0 — the base-name identifier ignores `name`, emitting an empty text child.
    # The top kind is correct on every branch (tag clauses hold), so C0 is the
    # sole discriminator, and it is the ONLY rival that abuses the `name` binder.
    {
        "id": "weak-name-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _MNAME,
            "    let mname : Node := .elem \"mi\".toList false [Node.text []]"),
        "refinement": (
            "the base-name identifier is built with an empty text child instead of "
            "the variable's actual base name, so the printed variable loses its "
            "name entirely. Every scenario reads the base name back from the "
            "identifier's text; a real patch that dropped the name would render a "
            "nameless symbol and would NOT resolve."),
        "rationale": (
            "REJECT from C0 (`out = buildSymbol …`), which grounds the identifier's "
            "text in `name`; the tag clauses constrain only the top kind and stay "
            "satisfied, so C0 is the sole discriminator and the ONLY probe of the "
            "`name` binder. Refuted at name=\"y\" (non-empty), subs=none, "
            "sups=none, bold=false — a bare identifier whose name is dropped."),
        "witness": _tester(
            "buildSymbolNodeTester \"y\".toList none none false"),
    },

    # C0 — the script node handed in is not PLACED WHOLE: a multi-piece script
    # (which unchanged infrastructure renders as a row container) is re-tagged
    # down to a bare identifier over the same pieces, while a single-piece
    # script is passed through untouched. The top kind is right on every branch
    # (all four tag clauses hold) and the rival AGREES with gold whenever the
    # subscript node is not a row container, so it diverges only on the
    # multi-piece sub-domain — the one sub-domain no other rival reaches.
    {
        "id": "weak-script-node-retagged",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ARM_MSUB,
            "      | none,     some sub => .elem \"msub\".toList false [mname,\n"
            "          match sub with\n"
            "          | .elem t _ ch => if t = \"mrow\".toList then .elem \"mi\".toList false ch else sub\n"
            "          | .text v      => .text v]"),
        "refinement": (
            "the routine's contract with its inputs is that an already-rendered "
            "script node is placed WHOLE into the container: the assembly chooses "
            "where the node goes, never what it is. This rival rewrites the node "
            "on the way in, flattening a multi-piece script's row container into a "
            "bare identifier over the same pieces. A real patch that rebuilt the "
            "script node instead of appending the rendered one would present a "
            "multi-piece subscript as a single identifier where the scenario reads "
            "back a row container, and would NOT resolve — while a variable whose "
            "subscript is a single piece would still render correctly, which is "
            "exactly what makes this a partial-domain miss rather than a total one."),
        "rationale": (
            "REJECT from C0 (`out = buildSymbol …`), which places `sub` itself as "
            "the container's second child; this places a rewritten node. The four "
            "tag clauses constrain only the top kind and stay satisfied, so C0 is "
            "the sole discriminator — verifying would leave the spec indifferent to "
            "whether the script node is preserved, partial-domain SPEC-TOO-WEAK. "
            "Refuted at name=\"x\", subs=some(row container over two pieces), "
            "sups=none, bold=false — the multi-piece script sub-domain, which no "
            "other rival reaches. Confirmed partial: the same witness shape at a "
            "SINGLE-piece subscript does NOT refute this rival (it agrees with gold "
            "there), so the case pins the multi-piece sub-domain specifically."),
        "witness": _tester(
            "buildSymbolNodeTester \"x\".toList "
            "(some (Node.elem \"mrow\".toList false [Node.text \"2\".toList, Node.text \"a\".toList])) "
            "none false"),
    },

    # C-mi — the bare-identifier branch emits the wrong top kind (a spurious
    # subscript-tagged wrapper) for a variable with no scripts. Abuses the bare
    # sub-domain and pins C-mi, the one tag clause no other rival attacks.
    {
        "id": "weak-bare-wrong-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ARM_NONE,
            "      | none,     none     => .elem \"msub\".toList false [mname]"),
        "refinement": (
            "a variable with no scripts must be presented as the bare base-name "
            "identifier; this wraps it in a subscript-tagged container instead. The "
            "failing scenario pins the top kind of a plain symbol to the identifier "
            "itself; a real patch emitting a script container for a scriptless "
            "symbol would produce the wrong element and would NOT resolve."),
        "rationale": (
            "REJECT from C-mi (`(subs = none ∧ sups = none) → out.tag = "
            "\"mi\".toList`): this returns tag `msub` on the bare sub-domain; also "
            "from C0. C-mi is attacked by no other rival. Refuted at name=\"z\", "
            "subs=none, sups=none, bold=false — the bare sub-domain."),
        "witness": _tester(
            "buildSymbolNodeTester \"z\".toList none none false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 4 partial-domain uniqueness
# rivals) plus 0 AXIOM_TESTS (the sibling models the node-choice deeply too; its
# footer records AXIOM_TESTS == []).
#
#   sibling case                              -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder                       -> pos-control-match-reorder    PORTED
#   admiss-f2p-shape                          -> admiss-postimage-nondegenerate RE-AIMED
#   frame-mutate-name                         -> (none)                       VACUOUS
#   partial-domain-subs-prepatch-root         -> weak-subs-outer-identifier   PORTED
#   partial-domain-combined-order-swap        -> weak-combined-order-swap     PORTED
#   partial-domain-bold-drop-bare             -> weak-bold-drop-bare          PORTED
#   partial-domain-group-collapse             -> weak-script-node-retagged    PORTED (re-aimed)
#
# Plus THREE rivals with no direct sibling but demanded by binder/clause
# coverage on THIS carrier: weak-sups-outer-identifier (C-msup, the sup-only
# mirror of the subs rival — the sibling's four-branch nagini build folded the
# sup-only case into its reorder positive, but here the sup-only tag clause is an
# independent conjunct that needs its own attacker); weak-name-dropped (the
# `name` binder — a value input the sibling's abstracted-flags carrier did not
# expose as a rival surface, but which C0 grounds here); weak-bare-wrong-tag
# (C-mi, the bare-branch tag clause).
#
# VACUOUS (frame-mutate-name): the sibling writes to the read-only base-name
#   list, which carries a fractional heap permission (`Acc(list_pred(name),1/2)`),
#   and is rejected for INSUFFICIENT PERMISSION before any value reasoning. This
#   backend is referentially transparent: `name`, `subs`, `sups`, `bold` are
#   immutable values, this bundle declares no `mut` binder, and there is no heap
#   or aliasing. There is no read-only input to overwrite and no permission
#   system to trip, so the class is vacuous. No substitute is fabricated (per the
#   porting map, this class is legitimately dropped here rather than replaced).
# RE-AIMED (admissibility): the sibling establishes that the half-permission
#   base-name input is readable and a normal F2P-shaped return is reachable via a
#   self-call. There is no precondition and no permission here, so that probe is
#   vacuous. It is re-aimed at the residual admissibility risk on a total domain:
#   that the post-image is unsatisfiable / degenerate at the interesting point.
#   The case discharges an in-region assert pinning the F2P-shaped subscript-only
#   node to exactly the subscript container of the identifier and the subscript
#   node — concrete and non-degenerate.
# PORTED / re-aimed (partial-domain-group-collapse -> weak-script-node-retagged):
#   the sibling attacks the rendering of a MULTI-piece script into a row container
#   vs a single-piece script into a bare identifier (its `group_tag` oracle). That
#   RENDERING is indeed unchanged upstream infrastructure here — `subs` / `sups`
#   arrive already rendered (mapping.md §2) — so the sibling's rival, which
#   miscomputes the rendering, has no direct counterpart. But the sub-domain it
#   probes survives the carrier change: C0 requires the already-rendered node be
#   placed WHOLE, so an impl that REWRITES the incoming node — flattening a
#   multi-piece row container to a bare identifier over the same pieces while
#   passing a single-piece node through — violates C0 on exactly the multi-piece
#   sub-domain and nowhere else. The tag clauses cannot see it (the top kind stays
#   right), so C0 alone discriminates, and the witness at a row-container subscript
#   refutes it while the same shape at a single-piece subscript does not. The
#   distinction the sibling cared about is therefore expressible on this carrier;
#   it needed re-aiming from "renders the script wrong" to "does not place the
#   rendered script", not dropping.
#
# BINDER / CLAUSE COVERAGE. Clauses: C-mi (weak-bare-wrong-tag), C-msub
#   (weak-subs-outer-identifier), C-msup (weak-sups-outer-identifier), C-msubsup
#   content + child order (weak-combined-order-swap), C-bold (weak-bold-drop-bare),
#   and the master C0 is attacked by every rival (weak-name-dropped isolates it).
#   All four tag clauses, the bold clause, and the master equality are attacked.
#   Binders: `subs` moved across none/some, `sups` across none/some (all four
#   script sub-domains probed), `bold` across false/true, `name` across three
#   base names with one rival abusing it directly, and the SHAPE of a script node
#   varied (a single-piece node vs a multi-piece row container) by
#   weak-script-node-retagged, which also pins that the node is placed whole.
#   SEVEN DISTINCT witness inputs (pts=7); no two rivals share a witness — each
#   fails only on the sub-domain its clause governs (the subs and sups
#   outer-identifier rivals agree with gold off their own branch, so each carries
#   its own input).
#
# AXIOM_TESTS: empty. No axiomatized callee to probe (the node-assembly is modeled
#   deeply; mapping.md §3 records no `axiom`). This gate ignores AXIOM_TESTS
#   regardless.
AXIOM_TESTS = []
