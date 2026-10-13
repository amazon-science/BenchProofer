"""properties.py — G-PBT falsification battery for sympy__sympy-23534 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and every ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled total function):

  implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult

  A name argument is either a single token (``NameSpec.tok``) or a nested
  sequence of such arguments (``NameSpec.seq``). The construction must mirror
  the nesting shape of ``names`` and stamp EVERY constructed leaf with the
  requested class ``cls``, including leaves nested below one or more sequence
  layers. The postcondition is the relational predicate

    problem_spec_symbols cls names result := BuildsUnder cls names result

  where ``BuildsUnder`` is defined inductively over the two constructors:

    (P-tok)  a token maps to a leaf tagged with THE REQUESTED CLASS ``cls`` and
             that token: ``BuildsUnder cls (tok s) (leaf cls s)``;
    (P-seq)  a sequence maps to a container of the SAME LENGTH whose entries are
             the recursively-specified results, each carrying the SAME requested
             class: ``Forall₂ (BuildsUnder cls) items rs``.

  The predicate has two independent, load-bearing dimensions:

    * SHAPE — the result mirrors the nesting of ``names`` (a sequence yields a
      ``node`` of the same length via ``Forall₂``); a leaf/node mismatch or a
      wrong entry count refutes it.
    * CLASS-TAG — the requested class reaches every leaf at every nesting depth
      (``leaf cls s``, never ``leaf defaultClass s``); this is the observable
      the fix restores.

  The ``Forall₂`` in (P-seq) is POINTWISE, not merely length-matching, so the
  SHAPE dimension has three independently refutable sub-clauses: the entry COUNT
  (too many / too few entries), the entry ORDER (entry k of the result must be
  the sub-result of entry k of the input, not of some other entry), and the
  NESTING DEPTH of each entry (a sub-sequence's own ``node`` layer may not be
  collapsed into its parent). And (P-tok) constrains the leaf's SOURCE TOKEN as
  well as its class tag, so a leaf carrying the right class but the wrong token
  is refutable too.

  Input binders of the spec predicate: ``cls`` (the requested class tag),
  ``names`` (the name argument), ``result``. The reject witnesses below vary
  ``cls`` across four distinct non-default values (1, 3, 2, 4) and ``names``
  across both constructors and THREE nesting depths (a bare token; a
  single-entry sequence; a two-entry sequence; a sequence nested inside a
  sequence), plus the EMPTY sequence — the base case of the ``Forall₂``
  recursion, and the one ``names`` value at which the sequence arm produces a
  result without ever entering its loop body. No dimension is probed at a single
  fixed point and the recursion is exercised past the one-layer case where a
  depth-insensitive defect hides.

  WHAT THE SPEC PINS, PROVEN RATHER THAN SAMPLED. ``BuildsUnder cls names`` is
  FUNCTIONAL: it relates each ``(cls, names)`` to exactly one ``result``. This
  was machine-checked during the audit of this battery, as two theorems built
  against the frozen file (in scratch, not shipped — a variant may not add
  theorems):

    spec_det  : BuildsUnder cls n r → BuildsUnder cls n r' → r = r'
    spec_pins : (∀ cls names, problem_spec_symbols cls names (f cls names)) →
                ∀ cls names, f cls names = implementation_symbols cls names

  ``spec_det`` goes by ``NameSpec.rec`` with the list motive carrying the
  pointwise uniqueness of ``Forall₂``; ``spec_pins`` is then ``spec_det`` applied
  to the frozen ``correct_symbols``. Together they settle the two directions this
  battery's rivals can only sample:

    * SPEC-TOO-WEAK is IMPOSSIBLE. Any impl that verifies is pointwise equal to
      the frozen impl, so no wrong impl can satisfy the frozen obligation —
      whatever dimension it is wrong on, and at whatever input. The reject cases
      below therefore attest to the spec's discriminating power at concrete
      points rather than to its adequacy in general, which is settled above.
    * SPEC-TOO-STRONG is confined to the PROOF, not the spec. Every impl
      agreeing pointwise with the frozen one satisfies the predicate, so a
      correct reshape can only fail by being unable to close its own proof — a
      tactic burden, never a spec rejection. ``pos-map-attach`` demonstrates that
      the burden is dischargeable for a genuinely different algorithmic shape.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini bundle held the ``names``
    container at a fractional (read-only) permission and its MANDATORY frame
    probe wrote back into it (``names[i] = names[i]``) to be rejected for
    insufficient permission. Lean is referentially transparent: the input
    carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini ``S-frame-mut`` rival has
    NO expressible instance here and no substitute is fabricated for it. See
    'assessment'.

  * WRONG-CLASS (nagini ``S-wrong-class``, THE prepatch bug) — PORTED, and
    tripled. The nagini rival forwarded the default class into the per-entry
    recursion instead of the requested ``cls``. On this carrier that is a rival
    whose nested recursion builds ``leaf defaultClass`` (rival A). Because the
    Lean model makes the token base case ALSO carry the class tag concretely,
    the same defect has a second expressible form — a token built under the
    default class (rival C) — which the nagini String-only carrier could not
    separate. Rival D is the PARTIAL-DOMAIN form of the same defect: the class is
    forwarded correctly for every token entry and dropped only when the entry is
    itself a sequence, so it is correct at depth 1 and wrong only at depth >= 2.
    All three attack the CLASS-TAG dimension, at both constructors and at two
    nesting depths, so the tag clause is pinned at every depth rather than only
    at the depth the shallowest rival happens to visit.

  * PARTIAL-DOMAIN / STRUCTURE (nagini ``S-partial-firstentry`` / ``S-flat``) —
    PORTED at the SEQUENCE level. What does NOT port is the per-token
    MULTIPLICITY dimension the nagini rivals turned on (a range token ``'q:2'``
    expands to two objects): this carrier ABSTRACTS the unchanged token-parsing
    internals (range expansion / scalar-vs-tuple collapsing) to a single
    class-tagged ``leaf``, so a token is one leaf and the INTRA-token
    multiplicity distinction has no counterpart here. The structural clause the
    nagini rivals attacked THROUGH that dimension does port, one level up, and
    is attacked here directly: the ``Forall₂`` is pointwise over the sequence's
    own entries. So ``S-flat``'s collapsing attack is rival F (it splices a
    single-entry sub-sequence's contents into its parent, erasing one ``node``
    layer — a genuine structure-flattening, refuted by the depth clause exactly
    as ``S-flat`` was refuted by the multiplicity clause), ``S-partial``'s
    over-production is rival B (two leaves for a one-entry sequence, refuted by
    the entry count), and the under-production dual is rival G (zero leaves for a
    one-entry sequence). Rival E adds the ORDER sub-clause the nagini battery had
    no analogue for. See 'assessment' for the intra-token multiplicity dimension
    that genuinely does not port.

  * WRONG-TOKEN — NEW on this carrier, no nagini analogue. The nagini leaves were
    bare class tags (``int``s), so a leaf carried no source-token component and
    there was nothing to get wrong; this carrier's ``leaf cls s`` pins the token
    too. Rival H returns a leaf with the requested class but a constant token,
    which the ``BuildsUnder.tok`` clause refutes. Without it the ``s`` component
    of (P-tok) is unattacked and an impl could stamp the right class onto the
    wrong name and still be attested to by this battery.

  * UNGROUNDED-ORACLE ECHO — VACUOUS (as in nagini). ``BuildsUnder`` is grounded
    structurally in ``cls`` and ``names`` (an inductive relation, fully unfolded
    over the produced result); there is no opaque answer-key to echo. The only
    "echo" available is to forward the WRONG tag — which is exactly the
    wrong-class rivals. The honest analogues are the POSITIVE CONTROLS
    (``pos-*``) that must verify.

  * POSITIVE CONTROL (soundness) + ADMISSIBILITY — PORTED (nagini ``S-pos`` /
    ``S-admiss``). Three structurally-different CORRECT impls that must verify,
    and one ground-instance admissibility probe. The two local-binding positives
    are data-flow reshapes that keep the frozen accumulation, so they close under
    the frozen proof verbatim; ``pos-map-attach`` is the strong one — it drops the
    mutable accumulator and the ``for`` loop entirely for a direct ``map``, so the
    frozen loop lemma is not merely re-used but no longer needed, and the case
    must supply its own (shorter) proof of the SAME byte-identical obligation. A
    spec that admitted only the accumulator shape would be SPEC-TOO-STRONG, and
    only a reshape that changes the shape can detect that.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input: it first REDUCES the rival's ``implementation_symbols`` at that
input to a closed value (the WF-recursive ``Id.run``/``for`` body is unfolded
with a fixed ``simp only`` set), then derives ``¬ problem_spec_symbols …`` by
inverting the ``BuildsUnder`` constructors. Each was machine-checked to ELABORATE
against its rival and to FAIL against the frozen solution, and the gold-side
failure was READ, not just counted: in every case it is the reduction step
reporting the two concrete values as unequal (e.g. ``node [leaf 1 "q"] = node
[leaf defaultClass "q"]``), a SEMANTIC refutation of the concrete claim rather
than an unknown identifier, a type error or a stuck reduction.

That reading is not left as an impression. Every witness here was additionally
subjected to the FORGERY experiment, which is what distinguishes a gold-side exit
code that carries information about the CLAIM from one that would appear for any
claim at all. For each case a second file was built differing from the witness
ONLY in the value it claims — the rival's reduced value replaced by GOLD's own —
and the two builds compared. In every case the result inverts cleanly: the
``hval`` reduction step that fails on gold in the real witness SUCCEEDS on gold in
the flipped file (the error moves downstream to ``⊢ False`` under a hypothesis
that witnesses the spec HOLDING there, e.g. ``a✝ : BuildsUnder 3 (tok "y")
(leaf 3 "y")``), and FAILS on the rival instead, with the two values transposed.
Flipping the claim's SIGN (asserting ``problem_spec_symbols`` rather than its
negation) likewise keeps gold failing, but at a different step and with a
different goal. So gold's exit code tracks what the witness asserts in both
directions, and none of these cases is the hollow shape where an error appears
regardless of the claim. Each is a real discriminator, not a tautology and not a
tooling artifact.

Two witnesses (``rival-reverse-order``, ``rival-wrong-token``) refute a leaf
whose SOURCE TOKEN, not whose class tag, is wrong. Inverting those with a bare
``cases`` makes Lean solve a String-literal equation during dependent
elimination and it fails with ``Dependent elimination failed`` on the rival AND
on gold — a tooling failure that discriminates nothing and would be recorded as
``witness-unproven``. Both therefore invert through a small helper the witness
declares FOR ITSELF (so it exists in both builds and is not a name only one side
has), turning the hypothesis into an equation that ``simp`` refutes.

DIVERGENCE lane: NOT SHIPPABLE HERE, and measured rather than assumed. This
bundle sets NO ``loom.semantics.termination`` option — it is plain Lean 4 with
Mathlib, where totality is not a discharged side obligation but a property of the
definition itself, so the "total vs partial" disposition that governs this class
elsewhere does not apply as written. Two diverging rivals were built to decide it:

  * a ``def`` whose sequence arm recurses on the WHOLE input rather than on an
    entry. It does not merely fail to verify, it fails to DEFINE: Lean reports
    ``well-founded recursion cannot be used, `implementation_symbols` does not
    take any (non-fixed) arguments`` at the definition site. There is no impl
    here for a witness to be about.
  * a ``partial def`` on the same recursion, which is the only way to write a
    non-terminating impl on this carrier at all. It DEFINES, but ``partial``
    makes the constant opaque to reduction: the frozen ``rfl``-style unfolding
    fails (``implementation_symbols cls (tok s)`` is not definitionally equal to
    ``leaf cls s``), and a witness cannot reduce it either. Measured: a witness
    refuting it fails on the rival AND on gold with ``Dependent elimination
    failed`` — identical text on both sides, i.e. a tooling failure that
    discriminates nothing, which the gate would correctly refuse as
    ``witness-unproven``.

So this class is a KNOWN HOLE rather than a vacuous one: a ``partial`` impl is
expressible and is not refutable by any witness on this carrier, because the
opacity that makes it non-terminating is the same opacity that blocks the
reduction a witness needs. Note that ``variant_scope`` bans ``partial`` in
witnesses but not in a variant's impl region, so the hole is real rather than
merely unreached. It is recorded here, not papered over with a substitute rival.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` (the ``expand_entry``
A-reference deep-model soundness probe against real ``sympy.symbols``) belong to
G-AX, which the G-PBT spec lane ignores. This carrier declares NO ``opaque``
callee and consumes NO ``axiom … _prop`` (``correct_symbols`` closes by
structural induction), so there is no axiom-soundness obligation for this gate.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23534"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl or proof region and is
# unique in the file, so every replacement preserves same_spec by construction.
# ---------------------------------------------------------------------------

# The recursive call that threads the requested class into each sub-spec (the
# line the fix governs).
_REC = "      result := result ++ [implementation_symbols cls nm.val]"

# The token base case (also carries the class tag on this carrier).
_TOK = "  | NameSpec.tok s => return SymResult.leaf cls s\n"

# The frozen proof preamble; the admissibility case prepends a `have` here.
_PROOF_INTRO = "  intro cls names\n  unfold problem_spec_symbols\n"

# The frozen well-founded-recursion discharge. A rival that adds a `match` inside
# the loop body splits this goal, so it needs the same tactic under `all_goals`.
_DECREASING = ("  simp_wf\n"
               "  exact lt_of_lt_of_le (List.sizeOf_lt_of_mem nm.property) "
               "(Nat.le_add_left _ _)")

# The whole frozen impl body and the whole frozen proof body — the anchors the
# one reshape that abandons the accumulator has to replace wholesale.
_IMPL_BODY = _BASE[_BASE.index("def implementation_symbols"):
                   _BASE.index("-- impl-end")].rstrip()
_PROOF_BODY = _BASE[_BASE.index("/-- The desugared"):
                    _BASE.index("-- proof-end")].rstrip()

assert _BASE.count(_REC) == 1, "recursion anchor drifted from Solution.lean"
assert _BASE.count(_TOK) == 1, "token-arm anchor drifted from Solution.lean"
assert _BASE.count(_PROOF_INTRO) == 1, "proof-intro anchor drifted from Solution.lean"
assert _BASE.count(_DECREASING) == 1, "decreasing_by anchor drifted from Solution.lean"
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drifted from Solution.lean"
assert _BASE.count(_PROOF_BODY) == 1, "proof-body anchor drifted from Solution.lean"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot satisfy the frozen obligation
# the spec is SPEC-TOO-STRONG. Each keeps the `theorem correct_symbols`
# statement byte-identical and introduces no helper lemma, axiom, or assumption.
# The gold proof body still closes because the reshape reduces definitionally to
# the frozen accumulation.
# ---------------------------------------------------------------------------

# pos-let-binding: bind the constructed leaf to a local in the TOKEN arm before
# returning it. Same value on every branch; the frozen proof closes (the local
# zeta-reduces).
_POS_LET = _swap(
    _BASE, _TOK,
    "  | NameSpec.tok s =>\n"
    "    let r := SymResult.leaf cls s\n"
    "    return r\n",
)

# pos-local-sub: bind the recursive sub-result to a local before appending it in
# the SEQUENCE arm. Same accumulation, so the postcondition is unchanged and the
# frozen proof body still discharges.
_POS_SUB = _swap(
    _BASE, _REC,
    "      let sub := implementation_symbols cls nm.val\n"
    "      result := result ++ [sub]",
)

# pos-map-attach: the STRONG reshape. Abandons `Id.run do` / `let mut` / `for`
# for a direct `List.map` over the attached entries — a different algorithmic
# SHAPE, not a data-flow tweak, so the frozen accumulator loop lemma is not just
# unused but inapplicable, and the case must reprove the SAME byte-identical
# obligation from its own (shorter) unfolding. If the frozen spec could only be
# satisfied by the accumulator shape it would be SPEC-TOO-STRONG; this is the
# case that would detect that, which neither local-binding positive can.
_POS_MAP = _swap(
    _BASE, _IMPL_BODY,
    "def implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult :=\n"
    "  match names with\n"
    "  | NameSpec.tok s => SymResult.leaf cls s\n"
    "  | NameSpec.seq items =>\n"
    "    SymResult.node (items.attach.map (fun nm => implementation_symbols cls nm.val))\n"
    "termination_by names\n"
    "decreasing_by\n" + _DECREASING,
)
_POS_MAP = _swap(
    _POS_MAP, _PROOF_BODY,
    "theorem tok_unfold (cls : ClassId) (s : String) :\n"
    "    implementation_symbols cls (NameSpec.tok s) = SymResult.leaf cls s := by\n"
    "  conv_lhs => unfold implementation_symbols\n"
    "\n"
    "theorem seq_unfold (cls : ClassId) (items : List NameSpec) :\n"
    "    implementation_symbols cls (NameSpec.seq items) =\n"
    "      SymResult.node (items.map (fun nm => implementation_symbols cls nm)) := by\n"
    "  conv_lhs => unfold implementation_symbols\n"
    "  simp [List.map_attach]\n"
    "\n"
    "theorem correct_symbols : ∀ (cls : ClassId) (names : NameSpec),\n"
    "    problem_spec_symbols cls names (implementation_symbols cls names) := by\n"
    + _PROOF_INTRO +
    "  induction names using NameSpec.rec with\n"
    "  | tok s => rw [tok_unfold]; exact BuildsUnder.tok s\n"
    "  | seq items ih => rw [seq_unfold]; exact BuildsUnder.seq items _ ih\n"
    "  | nil => exact List.Forall₂.nil\n"
    "  | cons head tail ih1 ih2 => exact List.Forall₂.cons ih1 ih2",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation is discharged at a ground, F2P-shaped input (a
# one-entry sequence built under a non-default class) as a `have` prepended to
# the frozen tactic body, then the frozen obligation is closed verbatim. If that
# ground instance could not be discharged, the modeled behavior would be
# unsatisfiable at exactly the shape the F2P exercises — the analogue of
# PRECOND-TOO-STRONG. The frozen theorem carries no precondition hypothesis (the
# behavior is total), so this ground-instance form is the honest analogue of the
# nagini precondition-admission probe. Nothing is assumed: no new declaration,
# the statement is byte-identical, the ground instance is proved by reducing the
# impl and applying the spec constructors.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE, _PROOF_INTRO,
    _PROOF_INTRO +
    "  have _ground : problem_spec_symbols 1 (NameSpec.seq [NameSpec.tok \"q\"])\n"
    "      (implementation_symbols 1 (NameSpec.seq [NameSpec.tok \"q\"])) := by\n"
    "    have hval : implementation_symbols 1 (NameSpec.seq [NameSpec.tok \"q\"])\n"
    "        = SymResult.node [SymResult.leaf 1 \"q\"] := by\n"
    "      simp only [implementation_symbols, Id.run, List.attach, List.attachWith,\n"
    "        List.pmap, List.forIn_cons, List.forIn_nil, ForInStep.yield, bind, pure,\n"
    "        List.nil_append, List.append_assoc, List.singleton_append]\n"
    "    rw [problem_spec_symbols, hval]\n"
    "    exact BuildsUnder.seq _ _ (List.Forall₂.cons (BuildsUnder.tok \"q\") List.Forall₂.nil)\n",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each ships the FROZEN proof body verbatim (a `sorry` would
# violate variant scope), so its rejection is the frozen script failing against
# the reshaped impl — which is exactly why the WITNESS, not the rejection,
# attributes the failure to the spec. Each witness reduces the rival's impl at
# one concrete input and inverts `BuildsUnder`.
# ---------------------------------------------------------------------------

# rival-wrong-class-nested (A): the nested recursion drops the requested class,
# building sub-results under the default class. Attacks the CLASS-TAG dimension
# at a sequence-nested leaf. THIS IS the ported prepatch bug.
_RIVAL_A = _swap(
    _BASE, _REC,
    "      result := result ++ [implementation_symbols defaultClass nm.val]",
)

# rival-wrong-class-base (C): the token base case builds under the default class
# instead of the requested class. Attacks the CLASS-TAG dimension at the token
# constructor — a form the nagini String-only carrier could not separate.
_RIVAL_C = _swap(
    _BASE, _TOK,
    "  | NameSpec.tok s => return SymResult.leaf defaultClass s\n",
)

# rival-over-produce (B): emit TWO leaves per sequence entry, breaking the
# same-length shape mirror. Attacks the SHAPE dimension (the Forall₂ entry
# count). The class is forwarded correctly, so only the shape clause refutes it.
_RIVAL_B = _swap(
    _BASE, _REC,
    "      result := result ++ [implementation_symbols cls nm.val, "
    "implementation_symbols cls nm.val]",
)

# rival-wrong-class-deep (D): PARTIAL-DOMAIN form of the class-tag defect. The
# requested class is forwarded correctly whenever the entry is a token, and
# dropped only when the entry is itself a SEQUENCE — so the rival is CORRECT at
# nesting depth 1 and wrong only at depth >= 2. Rivals A and C are both refuted
# at depth 1, so neither would notice a defect confined to the deeper layers;
# this is the case that pins the tag clause at every depth of the recursion.
# The extra `match` splits the well-founded-recursion goal, hence `all_goals`.
_RIVAL_D = _swap(
    _swap(_BASE, _REC,
          "      match nm.val with\n"
          "      | NameSpec.seq _ =>\n"
          "        result := result ++ [implementation_symbols defaultClass nm.val]\n"
          "      | NameSpec.tok _ =>\n"
          "        result := result ++ [implementation_symbols cls nm.val]"),
    _DECREASING,
    "  all_goals simp_wf\n"
    "  all_goals exact lt_of_lt_of_le (List.sizeOf_lt_of_mem nm.property) "
    "(Nat.le_add_left _ _)",
)

# rival-reverse-order (E): prepend each sub-result instead of appending it, so a
# multi-entry sequence comes back in REVERSE order. Every leaf carries the right
# class and the entry COUNT is right, so neither the tag clause nor the length
# refutes it: only the POINTWISE half of Forall₂ does (entry k of the result must
# be entry k of the input's sub-result). No other rival attacks pointwiseness —
# they are all refuted at a one-entry sequence, where order is unobservable.
_RIVAL_E = _swap(
    _BASE, _REC,
    "      result := [implementation_symbols cls nm.val] ++ result",
)

# rival-flatten-nested (F): STRUCTURE-COLLAPSING (the S-flat analogue). When a
# sub-result is a single-entry container, splice its content into the parent
# instead of keeping it as a nested container — erasing one `node` layer. The
# entry count at the top level is preserved and every leaf carries the requested
# class, so this is refuted ONLY by the depth/nesting half of the shape mirror:
# `BuildsUnder cls (seq [...]) r` demands r be a `node`, and this rival hands
# back the leaf that was inside it.
_RIVAL_F = _swap(
    _BASE, _REC,
    "      let sub := implementation_symbols cls nm.val\n"
    "      match sub with\n"
    "      | SymResult.node [one] => result := result ++ [one]\n"
    "      | _ => result := result ++ [sub]",
)

# rival-under-produce (G): the dual of B — emit NO entry for a sequence entry, so
# the result container is SHORTER than its input. B's over-production and G's
# under-production are refuted by opposite directions of the Forall₂ length
# clause (a leftover `cons` vs a leftover input entry with no result entry), and
# a spec pinning only `length result ≤ length items` would admit exactly this one.
_RIVAL_G = _swap(
    _BASE, _REC,
    "      if result.isEmpty then result := [] else\n"
    "        result := result ++ [implementation_symbols cls nm.val]",
)

# rival-empty-seq (I): correct on every input the rest of the battery visits, and
# wrong ONLY at the EMPTY sequence, which it returns as a leaf instead of an empty
# container. This is the base case of the `Forall₂` recursion and the one `names`
# value at which the sequence arm returns without executing its loop body once, so
# every other rival's witness — each stated at a bare token or a NON-empty
# sequence — agrees with the frozen impl here. A partial-domain defect confined to
# the empty container would otherwise be attested to by this battery; refuted by
# (P-seq), which forces `seq []` to a `node`, never a leaf.
_RIVAL_I = _swap(
    _BASE, "  | NameSpec.seq items =>\n",
    "  | NameSpec.seq [] => return SymResult.leaf cls \"\"\n"
    "  | NameSpec.seq items =>\n",
)

# rival-tok-wrapped (J): the token arm wraps its leaf in a one-entry container, so
# a bare token comes back as a `node` where the spec demands a `leaf`. This is the
# DUAL of `rival-flatten-nested` — that one collapses a container layer away at
# the sequence constructor, this one invents a container layer at the token
# constructor — and (P-tok) refutes it directly: `BuildsUnder cls (tok s) r` forces
# `r` to be `leaf cls s`. Note the leaf inside carries the right class and the
# right token, so neither the tag clause nor the token clause touches this rival:
# only the leaf-vs-node discrimination of (P-tok) does.
_RIVAL_J = _swap(
    _BASE, _TOK,
    "  | NameSpec.tok s => return SymResult.node [SymResult.leaf cls s]\n",
)

# rival-wrong-token (H): the leaf carries the REQUESTED class but a constant
# source token instead of the entry's own. Attacks the `s` component of (P-tok),
# which no other rival touches — every one of them stamps the right token and
# gets the class or the shape wrong. Without this case an impl could apply the
# requested class to the wrong name and this battery would still attest to it.
_RIVAL_H = _swap(
    _BASE, _TOK,
    "  | NameSpec.tok s => return SymResult.leaf cls \"z\"\n",
)


# ---- witnesses (each machine-checked: elaborates vs rival, fails vs frozen) --
# Shared impl-reduction block: unfolds the WF-recursive Id.run/for body at a
# concrete single-entry input to a closed value.
def _wit_seq(cls, tok, rival_val, invert):
    return (
        f"example : ¬ problem_spec_symbols {cls} (NameSpec.seq [NameSpec.tok \"{tok}\"])\n"
        f"    (implementation_symbols {cls} (NameSpec.seq [NameSpec.tok \"{tok}\"])) := by\n"
        f"  have hval : implementation_symbols {cls} (NameSpec.seq [NameSpec.tok \"{tok}\"])\n"
        f"      = {rival_val} := by\n"
        "    simp only [implementation_symbols, Id.run, List.attach, List.attachWith,\n"
        "      List.pmap, List.forIn_cons, List.forIn_nil, ForInStep.yield, bind, pure,\n"
        "      List.nil_append, List.append_assoc, List.singleton_append]\n"
        "  rw [hval, problem_spec_symbols]\n"
        "  intro h\n"
        f"{invert}\n"
    )


# A: reduced value has a leaf under defaultClass; inverting the seq/cons gives a
# `BuildsUnder cls (tok "q") (leaf defaultClass "q")` which the tok constructor
# refutes.
_WIT_A = _wit_seq(
    1, "q", "SymResult.node [SymResult.leaf defaultClass \"q\"]",
    "  cases h with\n  | seq _ _ hf => cases hf with | cons h1 _ => cases h1",
)

# B: reduced value is a two-leaf node for a one-entry sequence; inverting the
# Forall₂ leaves a second cons that `nil` cannot match (length mismatch).
_WIT_B = _wit_seq(
    3, "y", "SymResult.node [SymResult.leaf 3 \"y\", SymResult.leaf 3 \"y\"]",
    "  cases h with\n  | seq _ _ hf => cases hf with | cons _ t1 => cases t1",
)

# C: token built under the default class; the tok constructor of BuildsUnder
# requires the requested class, so it is refuted directly.
_WIT_C = (
    "example : ¬ problem_spec_symbols 2 (NameSpec.tok \"x\")\n"
    "    (implementation_symbols 2 (NameSpec.tok \"x\")) := by\n"
    "  have hval : implementation_symbols 2 (NameSpec.tok \"x\")\n"
    "      = SymResult.leaf defaultClass \"x\" := by\n"
    "    simp only [implementation_symbols, Id.run, bind, pure]\n"
    "  rw [hval, problem_spec_symbols]\n"
    "  intro h\n"
    "  cases h\n"
)


# The reduction set the deeper/multi-entry inputs need: the single-entry helper
# above never has to step a `cons` onto a non-empty accumulator, so it omits the
# append lemmas that a two-entry or twice-nested input requires.
_SIMP_DEEP = (
    "    simp only [implementation_symbols, Id.run, List.attach, List.attachWith,\n"
    "      List.pmap, List.forIn_cons, List.forIn_nil, ForInStep.yield, bind, pure,\n"
    "      List.nil_append, List.append_nil, List.append_assoc, List.singleton_append,\n"
    "      List.cons_append]\n"
)

# An inversion helper the witness declares FOR ITSELF (so it exists in both the
# rival and the gold build, and is not a name only one side has). Needed where the
# refuted leaf differs from the required one in its STRING component: `cases` on
# such a hypothesis makes Lean solve a String-literal equation in dependent
# elimination and it reports `Dependent elimination failed` on BOTH sides — a
# tooling failure, not a refutation. Inverting to an equation and discharging it
# with `simp` refutes the concrete claim instead.
_INV_TOK = (
    "  have inv_tok : ∀ (c : ClassId) (s : String) (r : SymResult),\n"
    "      BuildsUnder c (NameSpec.tok s) r → r = SymResult.leaf c s := by\n"
    "    intro c s r hr; cases hr; rfl\n"
)


def _wit_at(cls, names, rival_val, invert, simp=_SIMP_DEEP):
    """A refutation at an arbitrary concrete `names`, not just a 1-entry seq."""
    return (
        f"example : ¬ problem_spec_symbols {cls} ({names})\n"
        f"    (implementation_symbols {cls} ({names})) := by\n"
        f"  have hval : implementation_symbols {cls} ({names})\n"
        f"      = {rival_val} := by\n"
        + simp +
        "  rw [hval, problem_spec_symbols]\n"
        "  intro h\n"
        f"{invert}\n"
    )


# D: at seq[seq[tok "q"]] the rival's OUTER entry is a sequence, so it recurses
# under the default class and the depth-2 leaf carries defaultClass. Refuted by
# inverting two seq/cons layers and then the tok constructor. Note the input has
# to be twice-nested: at depth 1 this rival agrees with gold, which is the point.
_WIT_D = _wit_at(
    1, "NameSpec.seq [NameSpec.seq [NameSpec.tok \"q\"]]",
    "SymResult.node [SymResult.node [SymResult.leaf defaultClass \"q\"]]",
    "  cases h with\n"
    "  | seq _ _ hf => cases hf with\n"
    "    | cons h1 _ => cases h1 with\n"
    "      | seq _ _ hg => cases hg with | cons h2 _ => cases h2",
)

# E: at a TWO-entry sequence the rival returns the entries reversed. The first
# result entry must be the sub-result of the first input entry (leaf _ "a") but is
# leaf _ "b"; inverted through inv_tok because the mismatch is in the String.
_WIT_E = _wit_at(
    1, "NameSpec.seq [NameSpec.tok \"a\", NameSpec.tok \"b\"]",
    "SymResult.node [SymResult.leaf 1 \"b\", SymResult.leaf 1 \"a\"]",
    _INV_TOK +
    "  cases h with\n"
    "  | seq _ _ hf => cases hf with\n"
    "    | cons h1 _ => have hbad := inv_tok _ _ _ h1; simp at hbad",
)

# F: at seq[seq[tok "q"]] the inner single-entry container is spliced away, so the
# result's only entry is a LEAF where the spec demands a node (the input entry is
# a sequence). `cases` on that hypothesis has no applicable constructor.
_WIT_F = _wit_at(
    1, "NameSpec.seq [NameSpec.seq [NameSpec.tok \"q\"]]",
    "SymResult.node [SymResult.leaf 1 \"q\"]",
    "  cases h with\n  | seq _ _ hf => cases hf with | cons h1 _ => cases h1",
)

# G: the one-entry sequence comes back EMPTY. Forall₂ between a one-element input
# list and `[]` has no constructor: `nil` needs both empty, `cons` needs both
# non-empty, so `cases hf` closes the goal with no cases left.
_WIT_G = _wit_at(
    4, "NameSpec.seq [NameSpec.tok \"a\"]", "SymResult.node []",
    "  cases h with\n  | seq _ _ hf => cases hf",
    simp=(
        "    simp only [implementation_symbols, Id.run, List.attach, List.attachWith,\n"
        "      List.pmap, List.forIn_cons, List.forIn_nil, ForInStep.yield, bind, pure,\n"
        "      List.nil_append, List.append_nil, List.append_assoc,\n"
        "      List.singleton_append, List.cons_append, List.isEmpty_nil,\n"
        "      List.isEmpty_iff, reduceIte]\n"
    ),
)

# H: the leaf carries the requested class but a constant token. BuildsUnder.tok
# demands the leaf's token BE the input token, so `leaf 1 "z"` for input `tok "a"`
# is refuted — via inv_tok, since the mismatch is the String component.
_WIT_H = _wit_at(
    1, "NameSpec.tok \"a\"", "SymResult.leaf 1 \"z\"",
    _INV_TOK + "  have hbad := inv_tok _ _ _ h\n  simp at hbad",
    simp="    simp only [implementation_symbols, Id.run, bind, pure]\n",
)


# I: at the EMPTY sequence the rival returns a leaf. Needs the deep reduction set
# even though the input is small: the `for` runs zero times, so the accumulator is
# never stepped and `List.attach`/`forIn_nil` must take the term to `node []` on
# gold. `cases h` then has no applicable constructor (the spec forces a `node`).
_WIT_I = _wit_at(
    1, "NameSpec.seq []", "SymResult.leaf 1 \"\"",
    "  cases h",
)

# J: at a bare token the rival returns a one-entry node. `BuildsUnder.tok` is the
# only constructor whose input is a `tok`, and it forces a `leaf`, so inverting the
# hypothesis leaves no applicable case. The leaf inside carries the correct class
# and token, so this is refuted purely by the leaf-vs-node shape of (P-tok).
_WIT_J = _wit_at(
    1, "NameSpec.tok \"a\"", "SymResult.node [SymResult.leaf 1 \"a\"]",
    "  cases h",
    simp="    simp only [implementation_symbols, Id.run, bind, pure]\n",
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-let-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": "Structurally-different CORRECT impl: the constructed leaf "
                     "in the token arm is bound to a local before being returned. "
                     "The value returned on every branch is unchanged, so both "
                     "dimensions of the postcondition (shape mirror + class-tag) "
                     "still hold; must verify (else SPEC-TOO-STRONG — a faithful "
                     "correct impl rejected). The frozen proof body is retained "
                     "verbatim (the local zeta-reduces before the induction).",
    },
    {
        "id": "pos-local-sub",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SUB,
        "rationale": "Structurally-different CORRECT impl: the recursive "
                     "sub-result is bound to a local `sub` before being appended "
                     "in the sequence arm (a data-flow reshape). The accumulation "
                     "and the class threaded into every sub-spec are unchanged, so "
                     "the postcondition is unchanged; must verify (else "
                     "SPEC-TOO-STRONG). The frozen proof discharges without any "
                     "new lemma (the local zeta-reduces to the frozen append).",
    },
    {
        "id": "pos-map-attach",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": "The STRONG correct reshape: a different algorithmic shape, "
                     "not a data-flow tweak. The mutable accumulator and the `for` "
                     "loop are dropped for a direct `map` over the attached "
                     "entries, so the frozen loop lemma is inapplicable rather "
                     "than merely unused, and the case reproves the SAME "
                     "byte-identical `correct_symbols` statement from its own "
                     "unfolding (no new axiom, no assumption, no restated "
                     "obligation — only the tactic body differs, which variant "
                     "scope permits). This is the case that can detect "
                     "SPEC-TOO-STRONG: a spec satisfiable only by the frozen "
                     "accumulator shape would reject a faithful correct impl, and "
                     "the two local-binding positives are too close to the frozen "
                     "form to notice. Verifies, so the spec constrains the "
                     "input-output relation and not the algorithm.",
    },
    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "The obligation is discharged at a ground F2P-shaped input "
                     "(a one-entry sequence built under a non-default class) as a "
                     "`have` prepended to the frozen tactic body; the frozen "
                     "obligation is then closed verbatim. Verifies (else the "
                     "modeled behavior would be unsatisfiable at the shape the F2P "
                     "exercises — the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, the `correct_symbols` statement "
                     "is byte-identical, and the ground instance is proved by "
                     "reducing the impl and applying the spec constructors.",
    },
    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "rival-wrong-class-nested",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_A,
        "refinement": "This IS the base-commit bug: the per-entry recursion "
                      "receives the default class instead of the requested class, "
                      "mirroring the missing class-forwarding in the sequence "
                      "branch. A faithful real patch on the unpatched branch makes "
                      "a nested constructed object carry the default class rather "
                      "than the requested one, so the added F2P assertion (a "
                      "nested object built under a function class must be of the "
                      "function class, not the default) FAILS -> the instance is "
                      "NOT resolved.",
        "rationale": "REJECT from the CLASS-TAG dimension of BuildsUnder at a "
                     "sequence-nested leaf: the requested class `cls=1` must reach "
                     "every leaf, but this rival builds the nested leaf under the "
                     "default class. Witness reduces the rival's impl at "
                     "seq[tok \"q\"] to node[leaf defaultClass \"q\"] and inverts "
                     "the seq/cons + tok constructors to derive the contradiction; "
                     "it fails on gold, whose leaf carries `cls`.",
        "witness": _WIT_A,
    },
    {
        "id": "rival-wrong-class-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_C,
        "refinement": "The token construction drops the requested class and builds "
                      "the object under the default class. A faithful real patch "
                      "that constructed a single-token object under the default "
                      "class rather than the requested class would make even the "
                      "un-nested case produce the wrong class; the pre-existing "
                      "single-token cls tests (a token built under a requested "
                      "class must be of that class) FAIL -> NOT resolved. This is "
                      "the same class-dropping defect at the token constructor, a "
                      "form the nagini String-only carrier could not separate.",
        "rationale": "REJECT from the CLASS-TAG dimension at the TOKEN "
                     "constructor: BuildsUnder.tok requires the leaf carry the "
                     "requested class `cls=2`, but this rival builds it under the "
                     "default class. Witness reduces the rival's impl at tok \"x\" "
                     "to leaf defaultClass \"x\" and inverts the tok constructor; "
                     "it fails on gold (leaf carries `cls`). Varies the `cls` "
                     "binder (2) and the `names` binder (a token, vs a sequence in "
                     "the other rivals).",
        "witness": _WIT_C,
    },
    {
        "id": "rival-over-produce",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_B,
        "refinement": "Emitting an extra object per sequence entry has no gold "
                      "counterpart (the gold appends exactly one recursively-built "
                      "result per entry). A faithful real patch that duplicated "
                      "each entry's result would make a returned container longer "
                      "than its input sequence; the pre-existing shape assertions "
                      "(the deconstruction of a same-shape nested result into "
                      "separate tuples) FAIL -> NOT resolved. This is the "
                      "sequence-level form of the nagini over-production attack "
                      "(`S-partial-firstentry`); its under-production dual is "
                      "`rival-under-produce` and the collapsing attack "
                      "(`S-flat`) is `rival-flatten-nested`.",
        "rationale": "REJECT from the SHAPE dimension: BuildsUnder.seq requires "
                     "Forall₂ between the input entries and the result entries "
                     "(equal length), but this rival emits two leaves for a "
                     "one-entry sequence. The class is forwarded correctly, so "
                     "ONLY the shape clause refutes it. Witness reduces the "
                     "rival's impl at seq[tok \"y\"] to a two-leaf node and "
                     "inverts the Forall₂ (the second cons cannot match nil); it "
                     "fails on gold, whose result has one entry. Varies the `cls` "
                     "binder (3).",
        "witness": _WIT_B,
    },
    {
        "id": "rival-wrong-class-deep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_D,
        "refinement": "The PARTIAL-DOMAIN form of the class-forwarding defect: the "
                      "requested class reaches every object built from a token "
                      "entry, and is dropped only when the entry is itself a "
                      "sequence. A faithful real patch of this shape resolves the "
                      "one-layer case and still builds objects under the default "
                      "class two or more layers down, so an assertion on a "
                      "twice-nested request (an object nested under two sequence "
                      "layers must carry the requested class) FAILS -> NOT "
                      "resolved. The nagini analogue is `S-partial-firstentry`: "
                      "correct on almost the whole domain, wrong on one "
                      "sub-domain, which the all-domain rivals cannot pinpoint.",
        "rationale": "REJECT from the CLASS-TAG dimension at nesting depth >= 2. "
                     "This rival AGREES with the frozen impl on every input the "
                     "other class-tag rivals are refuted at (a bare token, a "
                     "sequence of tokens), so it is the only case that pins the "
                     "tag clause below the first sequence layer — the recursion's "
                     "own inductive step. Witness reduces the rival at "
                     "seq[seq[tok \"q\"]] to node[node[leaf defaultClass \"q\"]] "
                     "and inverts two seq/cons layers plus the tok constructor; it "
                     "fails on gold, whose depth-2 leaf carries `cls`. Varies the "
                     "`names` binder to a twice-nested spec, a depth no other case "
                     "reaches.",
        "witness": _WIT_D,
    },
    {
        "id": "rival-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_E,
        "refinement": "Prepending each entry's result instead of appending it has "
                      "no gold counterpart (the gold builds the container in input "
                      "order). A faithful real patch that accumulated in reverse "
                      "would return a container whose entries are correct objects "
                      "in the WRONG positions; the pre-existing equality "
                      "assertions on a multi-entry request (which compare the "
                      "returned container positionally against the expected "
                      "objects) FAIL -> NOT resolved.",
        "rationale": "REJECT from the POINTWISE half of the SHAPE dimension. Every "
                     "leaf carries the requested class and the entry COUNT is "
                     "exactly right, so neither the tag clause nor a length "
                     "argument touches this rival: only Forall₂'s pointwise "
                     "pairing does (result entry k must be the sub-result of input "
                     "entry k). Every other reject case is refuted at a one-entry "
                     "or bare-token input where order is unobservable, so without "
                     "this case a spec pinning only the multiset of results would "
                     "pass this battery. Witness reduces the rival at a TWO-entry "
                     "sequence to the reversed node and refutes the first pairing; "
                     "it fails on gold, whose entries are in input order. Varies "
                     "the `names` binder to a two-entry sequence.",
        "witness": _WIT_E,
    },
    {
        "id": "rival-flatten-nested",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_F,
        "refinement": "Splicing a single-entry sub-container's contents into its "
                      "parent has no gold counterpart (the gold keeps one result "
                      "entry per input entry, whatever that entry's own shape). "
                      "This is the documented prior verify-not-resolve break in "
                      "its carrier-faithful form: a real patch that collapses a "
                      "one-element group into its parent returns a bare object "
                      "where the caller deconstructs a container, so the "
                      "positional deconstruction in the existing assertions raises "
                      "instead of comparing -> NOT resolved.",
        "rationale": "REJECT from the NESTING-DEPTH half of the SHAPE dimension. "
                     "The top-level entry count is preserved and every leaf "
                     "carries the requested class, so this rival is refuted "
                     "neither by the tag clause nor by any length argument: what "
                     "refutes it is that `BuildsUnder cls (seq items) r` forces `r` "
                     "to be a `node`, and this rival returns the leaf that was "
                     "inside it — one whole container layer erased. The nagini "
                     "`S-flat` analogue: shape-count right, structure collapsed. "
                     "Witness reduces the rival at seq[seq[tok \"q\"]] to "
                     "node[leaf 1 \"q\"] and inverts to a BuildsUnder of a "
                     "sequence against a leaf, which has no constructor; it fails "
                     "on gold, which keeps the inner node.",
        "witness": _WIT_F,
    },
    {
        "id": "rival-under-produce",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_G,
        "refinement": "Emitting no object for an entry has no gold counterpart "
                      "(the gold appends exactly one result per entry). A faithful "
                      "real patch that skipped an entry would return a container "
                      "SHORTER than the request; the existing positional "
                      "assertions would index past the end or compare unequal "
                      "containers -> NOT resolved.",
        "rationale": "REJECT from the SHAPE dimension in the opposite direction to "
                     "`rival-over-produce`: Forall₂ is refuted here by an input "
                     "entry with NO matching result entry (neither `nil` nor "
                     "`cons` applies to a one-element list against `[]`), where "
                     "the over-producer is refuted by a leftover result entry. A "
                     "spec that bounded the result length only from above would "
                     "admit exactly this rival while still rejecting the "
                     "over-producer, so the two are not redundant. Witness reduces "
                     "the rival at seq[tok \"a\"] to an EMPTY node; it fails on "
                     "gold, whose result has one entry. Varies the `cls` binder "
                     "(4).",
        "witness": _WIT_G,
    },
    {
        "id": "rival-wrong-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_H,
        "refinement": "Building the object from a constant name rather than the "
                      "requested one has no gold counterpart (the gold constructs "
                      "each object from its own name token). A faithful real patch "
                      "of this shape would apply the requested class correctly and "
                      "still return objects with the wrong names, so every "
                      "existing assertion comparing returned objects against "
                      "named expected objects FAILS -> NOT resolved.",
        "rationale": "REJECT from the SOURCE-TOKEN component of (P-tok), the one "
                     "part of the postcondition no other case attacks: every other "
                     "rival stamps the correct token and gets the class or the "
                     "shape wrong, so without this case an impl could carry the "
                     "requested class onto the wrong name and this battery would "
                     "still attest to it. This dimension has no nagini analogue at "
                     "all — there a leaf was a bare class tag with no token "
                     "component to corrupt. Witness reduces the rival at tok \"a\" "
                     "to leaf 1 \"z\" and inverts BuildsUnder.tok, which forces the "
                     "leaf's token to BE the input token; it fails on gold, whose "
                     "leaf carries \"a\". The inversion goes through a helper the "
                     "witness declares for itself (present in both builds) because "
                     "`cases` on a String-literal mismatch fails in dependent "
                     "elimination on BOTH sides, which would discriminate nothing.",
        "witness": _WIT_H,
    },
    {
        "id": "rival-empty-seq",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_I,
        "refinement": "Returning a bare object for an EMPTY request has no gold "
                      "counterpart (the gold returns an empty container of the same "
                      "shape as the empty request). A faithful real patch of this "
                      "shape is correct for every non-empty request and returns a "
                      "single object where the caller expects an empty container, so "
                      "any existing assertion that deconstructs or compares the "
                      "result of an empty request raises or compares unequal -> NOT "
                      "resolved.",
        "rationale": "REJECT from the SHAPE dimension at the BASE CASE of the "
                     "Forall₂ recursion: `BuildsUnder cls (seq []) r` forces `r` to "
                     "be `node []`, and this rival hands back a leaf. This is the "
                     "PARTIAL-DOMAIN case for the one `names` value no other case in "
                     "this battery visits — every other reject witness is stated at "
                     "a bare token or a NON-EMPTY sequence, and the positives only "
                     "quantify, so this rival AGREES with the frozen impl at every "
                     "input the rest of the battery discriminates at. It is also the "
                     "only input at which the sequence arm produces a result without "
                     "executing its loop body once. Witness reduces the rival at "
                     "seq [] to leaf 1 \"\" and inverts; it fails on gold, which "
                     "reduces to node [].",
        "witness": _WIT_I,
    },
    {
        "id": "rival-tok-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_J,
        "refinement": "Wrapping a single constructed object in a one-element "
                      "container has no gold counterpart (the gold returns the "
                      "object itself for a single-token request). A faithful real "
                      "patch of this shape would make every single-token request "
                      "return a container instead of an object, so the pre-existing "
                      "single-token assertions compare an object against a container "
                      "-> NOT resolved. This is the DUAL of the collapsing break in "
                      "`rival-flatten-nested`: one erases a container layer, this "
                      "one invents it.",
        "rationale": "REJECT from the leaf-vs-node discrimination of (P-tok), a "
                     "sub-clause no other case attacks in this direction: "
                     "`rival-flatten-nested` attacks the COLLAPSING direction and "
                     "does so at the sequence constructor, while this rival INVENTS "
                     "a container layer at the token constructor. The wrapped leaf "
                     "carries the requested class AND the correct source token, so "
                     "neither the tag clause nor the token clause refutes it — only "
                     "the fact that BuildsUnder.tok forces the result to be a `leaf` "
                     "does. Witness reduces the rival at tok \"a\" to "
                     "node [leaf 1 \"a\"] and inverts, leaving no applicable "
                     "constructor; it fails on gold, whose result is the bare leaf.",
        "witness": _WIT_J,
    },
]
