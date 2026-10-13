"""properties.py — G-PBT falsification battery for django__django-14787 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a single record-valued input):

  attachIdentity (source : CallableAttrs) : CallableAttrs
      result.name.ownEntry     = transferredEntry source.name
      result.name.observed     = transferredEntry source.name
      result.module.ownEntry   = transferredEntry source.module
      result.module.observed   = transferredEntry source.module
      result.qualname.ownEntry = transferredEntry source.qualname
      result.qualname.observed = transferredEntry source.qualname
      result.wrapped           = true
      result.selfSufficient    = true

  A ``CallableAttrs`` bundles three identity attributes (``name``, ``module``,
  ``qualname : IdentityAttr``), a boolean ``wrapped`` flag, and a boolean
  ``selfSufficient`` flag recording whether a caller can run the callable
  supplying only the arguments of the call itself (as opposed to a callable that
  still expects the object it belongs to to be handed in first).

  TWO LAYERS PER ATTRIBUTE. An ``IdentityAttr`` is a PAIR of layers, not one
  value: ``ownEntry`` is what the callable's own attribute table holds, and
  ``observed`` is what a reader of that attribute on the callable is answered
  with. They are separate facts and they need not agree — the kind of thing a
  callable is may answer for an attribute ahead of the callable's own table,
  and then the table's entry is not what a reader observes while STILL being
  the entry that table hands on when the table is laid over another's. Both
  layers are consulted by the transfer, in a fixed order, and both layers of
  the result are pinned. The two-layer carrier is load-bearing: a one-layer
  encoding cannot express the class of sources whose table disagrees with what
  a reader observes, and on that class it predicts the wrong value for the
  result. ``transferredEntry`` is the entry the transfer leaves in the result's
  own table: the source's OWN table entry whenever its table holds one, and
  otherwise what a reader observes on the source. The ``*-pass-only`` and
  ``*-precedence-swapped`` rivals below are exactly the ways of getting that
  two-layer, two-pass structure wrong and are rejected.

  An ``AttrSlot`` (one layer of one attribute) has THREE states, not two:
  ``vacant`` (no entry at all), ``filled none`` (an entry whose content is
  nothing in particular), and ``filled (some s)`` (an entry containing the text
  ``s``). The three-state carrier is load-bearing and a two-state
  ``Option String`` would be WRONG here: ``AttrSlot.overlay`` dispatches on
  whether an entry is HELD, never on what the entry contains, so a source
  holding an entry that contains nothing in particular hands that entry on — it
  is NOT treated as no entry at all. Collapsing ``vacant`` and ``filled none``
  into one state would make the clauses predict no entry held at a source that
  really hands its own contentless entry on; the ``collapse-*`` rivals below are
  exactly that error and are rejected.

  The synthesised callable that acts on behalf of ``source`` must expose ALL of
  ``source``'s identity — at BOTH layers, each entry handed on verbatim,
  content and all — be recorded as delegating (``wrapped = true``), AND still be
  the self-sufficient callable the caller can run on its own
  (``selfSufficient = true``). The precondition is ``True``: the domain is
  UNRESTRICTED, so ``source`` may hold entries for only some of its three
  attributes, at either layer, any entry may contain nothing in particular, and
  the two layers may disagree. Where ``source`` supplies nothing at either
  layer, the result keeps what the freshly synthesised callable already had —
  which is nothing, for all three attributes at both layers alike: that callable
  holds nothing in its own table and answers for none of the three on its own
  account, so every reader-visible clause reduces to the transferred entry
  outright and NO facet carries a non-source fallback. The three facets are
  therefore symmetric, and a rejection can only turn on the transfer itself.

  The postcondition is a conjunction of EIGHT independent top-level clauses,
  each pinned to a distinct facet of the result:

    * ``result.name.ownEntry``/``result.name.observed`` — the NAME facet at each
      of its two layers. Load-bearing for the F2P: the observable inspects the
      assembled callable's name and requires it be present and equal to the
      original's, which a bare synthesised callable lacks. The two clauses are
      NOT redundant: an implementation can get the observed layer right and the
      table layer wrong (``weak-result-table-disagrees``), and what the table
      holds is what a FURTHER transfer off this callable would hand on.
    * ``result.module.ownEntry`` — the module entry the result's own table holds.
    * ``result.module.observed`` — what a reader observes for the module: the
      transferred entry, the synthesised callable answering for the module on no
      account of its own, so a reader finds an entry exactly where ``source``
      supplied one.
    * ``result.qualname.ownEntry``/``result.qualname.observed`` — the
      QUALIFIED-NAME facet at each layer.
    * ``result.wrapped = true``         — the delegation flag, a constant, not
      an echo of ``source.wrapped``.
    * ``result.selfSufficient = true``  — the USABILITY facet, a constant. The
      callable handed back must remain the one a caller can run with the
      arguments of the call alone. This clause is INDEPENDENT of the metadata
      clauses: the identity transfer copies the identity attributes and the
      delegation flag off ``source``, but never ``source``'s own usability,
      because the object handed back is the synthesised callable and not
      ``source``. So a construction that hands back ``source`` itself — or that
      transfers identity in the reverse direction, ending up with ``source`` as
      the object returned — carries exactly the right metadata and still
      violates this clause whenever ``source`` is not itself runnable on its
      own. That is the facet the metadata clauses cannot see, and it is what
      separates a synthesised-callable-with-borrowed-identity from the original.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY: there the modeled ``method`` is held at
    fractional (read-only) permission and a rival that overwrites one of its
    attributes to satisfy the postcondition vacuously is rejected for
    insufficient permission. Lean is referentially transparent: ``source`` is a
    plain immutable value, there is no half-permission to violate and no
    aliasing to exploit, so this class has NO expressible instance here and no
    substitute is fabricated for it. The read-only invariant nagini also pins
    (``method`` unchanged) is likewise automatic — nothing can mutate ``source``.

  * UNGROUNDED-ORACLE ECHO — APPLIES in one form. The postcondition is
    GROUNDED: each clause equates a result facet to a function of the input
    record (or to the concrete constant ``true``), fully transparent, and the
    bundle declares no ``opaque``/``axiom``, so there is no answer key to echo.
    What IS expressible is an echo of the ARGUMENT: hand the input record back
    (flag flipped) and do none of the transfer work. Under a one-layer reading
    of the surface that echo is indistinguishable from a correct construction;
    under the two-layer one it is refutable, and ``weak-argument-echo`` refutes
    it at a source whose two layers disagree.

  * LAYER-COLLAPSE / MISSING-PASS — APPLIES, and is the class the two-layer
    carrier and the two clauses per attribute exist for. The transfer consults
    the source at both layers, in a fixed order: what a reader observes first,
    then the source's own table laid over that, so the table entry is the one
    that survives. A rival that keeps only the first pass
    (``weak-observed-pass-only``) is right exactly on sources whose two layers
    agree and wrong on every source where they disagree; a rival that keeps only
    the second (``weak-table-pass-only``) is wrong at every plain function,
    including the F2P input; a rival that applies them in the other order
    (``weak-layer-precedence-swapped``) is wrong exactly where both layers are
    held and differ. All three are INVISIBLE to a one-layer encoding of the
    attribute surface, which is why the carrier keeps the layers apart.

  * STATE-COLLAPSE — APPLIES, and is the class the three-state ``AttrSlot``
    exists for. A rival that treats an entry containing nothing in particular as
    though no entry were held drops the entry where the real transfer hands the
    source's own entry on, so the assembled callable is left with nothing held
    for that attribute where the original supplied a contentless entry. Rejected
    below on the module facet and on the name facet, each at a contentless-entry
    source.

  * PARTIAL-DOMAIN (the pre-patch behavior) — APPLIES, and is the load-bearing
    rival. The pre-fix synthesised callable carried NONE of ``source``'s
    identity (a bare object). It fails the NAME presence+equality clauses on
    every genuine callable, and is refuted at the F2P-shaped input.

  * VALUE / DROP-FACET — APPLY. Rivals that copy a SIBLING facet into the name
    (right only where a callable's name token coincides with its module token),
    or that drop a single facet (the module entry, the qualified name), or that
    echo the delegation flag instead of asserting it, each violate exactly one
    clause on a distinct input and are refuted with distinct witnesses.

  * WRONG-OBJECT-RETURNED — APPLIES, and is the class the usability clause
    exists for. Two shapes are covered: transferring identity in the REVERSED
    direction (so the object handed back is ``source``, dressed with the
    synthesised callable's absent attributes) and handing back ``source``
    itself with only the delegation flag flipped. Both satisfy every metadata
    clause on a suitably chosen ``source`` — the metadata is indistinguishable
    from gold's there — and both violate the usability clause at a ``source``
    that is not runnable on its own. They are the rivals a metadata-only
    postcondition could not separate from gold.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was checked (via scripts/lean_verify.sh) to
HOLD of its rival and to FAIL on the frozen solution, so it discriminates rather
than asserting a tautology.

BINDER / CLAUSE COVERAGE. ``source`` is a single record; its five fields — three
of them two-layer pairs — are the input binders of the spec predicate. Each
reject rival attacks a distinct clause at a distinct concrete input point:
  * ``result.name.ownEntry`` — attacked by the prepatch rival (nothing held at
    either layer), the sibling rival (a wrong VALUE), the collapse-name rival (a
    contentless entry turned into no entry), the two pass-only rivals, the
    precedence-swapped rival, and the result-table rival (the only one that
    leaves the observed layer correct).
  * ``result.name.observed`` — attacked by the pass-only, precedence-swapped and
    argument-echo rivals.
  * ``result.module.ownEntry`` — attacked by the drop-module rival (entry
    dropped outright) and by the collapse-module rival (a contentless entry
    mistaken for no entry, so nothing is handed on where the transfer hands the
    source's entry on).
  * ``result.module.observed`` — attacked by those same two rivals, which drive
    both layers of the module facet from one entry, plus the result-table rival
    which pins it correct while getting the table layer wrong.
  * ``result.qualname.ownEntry``/``.observed`` — attacked by the drop-qualname
    rival.
  * ``result.wrapped = true``         — attacked by the wrapped-echo rival, which
    surfaces the flag's dependence on the input rather than on the constant.
  * ``result.selfSufficient = true``  — attacked by the reversed-transfer rival
    and by the return-the-source rival, both of which hand back ``source``
    rather than the synthesised callable and so inherit ``source``'s usability
    instead of asserting the constant. Each is refuted at a source chosen so
    that every metadata clause HOLDS there and the rejection isolates usability.
The fourteen reject witnesses probe fourteen DISTINCT input records, spread over
the plain-function shape (own table empty), the own-table shape (both layers
agreeing), the DISAGREEING shape (table entry differing from what a reader
observes — the class a one-layer model cannot express), the nothing-held shape,
and the contentless-entry shape. So the battery exercises the spec's dependence
on each field, on each of the two LAYERS, and on each of the THREE states a
layer can be in, rather than one point.

AXIOM lane: EMPTY. The metadata transfer is modeled deeply (``copyIdentity``);
the bundle consumes no ``opaque`` callee and no ``axiom`` (see mapping.md:
A-reference, not a consumed axiom), so there is no in-model axiom obligation for
the PBT axiom lane to re-discharge — the axiom lane is G-AX's job. AXIOM_TESTS is
empty.
"""
from pathlib import Path

INSTANCE = "django__django-14787"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do\n"
    "  let mut bound : CallableAttrs := bareCallable\n"
    "  bound := copyIdentity source bound\n"
    "  return bound"
)

_PROOF_GOLD = (
    "  intro source _\n"
    "  unfold problem_spec_attachIdentity implementation_attachIdentity copyIdentity\n"
    "    IdentityAttr.transfer transferredEntry bareCallable\n"
    "  simp only [Id.run]\n"
    "  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩\n"
    "  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl\n"
    "  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl\n"
    "  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl\n"
    "  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl\n"
    "  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl\n"
    "  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"

# sanity: the usability clause is part of the frozen postcondition. If this
# anchor ever disappears the battery below stops testing the facet that the
# metadata clauses cannot see, so fail loudly at import rather than silently
# degrade to the metadata-only spec.
_USABILITY_CLAUSE = "  result.selfSufficient = true"
assert _BASE.count(_USABILITY_CLAUSE) == 1, (
    "the usability clause left the frozen postcondition; the reversed-transfer "
    "and return-the-source rivals below are no longer refutable")

# sanity: BOTH layers of the result are pinned, for each of the three
# attributes. The own-table clauses are what make the transfer's second pass
# observable; without them a rival that gets the reader-visible layer right and
# the table wrong satisfies the spec, and `weak-result-table-disagrees` below
# stops being refutable.
for _layer_clause in (
    "  result.name.ownEntry = transferredEntry source.name",
    "  result.module.ownEntry = transferredEntry source.module",
    "  result.qualname.ownEntry = transferredEntry source.qualname",
):
    assert _BASE.count(_layer_clause) == 1, (
        f"the own-table clause {_layer_clause.strip()!r} left the frozen "
        "postcondition; the layer rivals below are no longer refutable")


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced (spec + proof
    STATEMENT untouched)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# --------------------------------------------------------------------------- #
# input-record notation                                                        #
# --------------------------------------------------------------------------- #
# One layer of one attribute, in each of the carrier's three states.
_V = ".vacant"                     # no entry held at this layer
_N = ".filled none"                # an entry whose content is nothing in particular


def _T(s):
    """A layer holding an entry containing the text `s`."""
    return f'.filled (some "{s}")'


def _attr(observed, own=_V):
    """One attribute as the PAIR of layers it is."""
    return f"{{ observed := {observed}, ownEntry := {own} }}"


def _rec(name, module, qualname, wrapped="false", ss="false"):
    return ("{ name := " + name + ", module := " + module
            + ", qualname := " + qualname
            + f", wrapped := {wrapped}, selfSufficient := {ss} }}")


def _plain(n, m, q, **kw):
    """A PLAIN FUNCTION: a reader is answered for all three attributes and the
    callable's own table holds nothing. The commonest shape and the F2P's."""
    return _rec(_attr(_T(n)), _attr(_T(m)), _attr(_T(q)), **kw)


def _tabled(n, m, q, **kw):
    """A callable that keeps its identity in its OWN table, the table agreeing
    with what a reader observes."""
    return _rec(_attr(_T(n), _T(n)), _attr(_T(m), _T(m)), _attr(_T(q), _T(q)), **kw)


def _shadowed(n_obs, n_own, m_obs, m_own, q_obs, q_own, **kw):
    """A callable whose own table DISAGREES with what a reader observes: the kind
    of thing it is answers for the attribute ahead of its table, while the table
    still holds the entry it hands on. The class a one-layer model cannot
    express."""
    return _rec(_attr(_T(n_obs), _T(n_own)), _attr(_T(m_obs), _T(m_own)),
                _attr(_T(q_obs), _T(q_own)), **kw)


# The reviewer-shaped input, with the values the real routine is observed to
# produce: a callable whose own table holds "dummy" / "deco_patched" /
# "_update_method_wrapper.<locals>.dummy" while a reader of it is answered
# "m" / "__main__" / "Outer.m". The transfer hands the TABLE entries on, so the
# result is observed to carry the table's three values.
_SHADOW_REAL = _shadowed("m", "dummy", "__main__", "deco_patched",
                         "Outer.m", "_update_method_wrapper.<locals>.dummy")

# --------------------------------------------------------------------------- #
# POSITIVE-CONTROL impls + their re-proofs                                     #
# --------------------------------------------------------------------------- #
# (1) Structurally-different but CORRECT: drop the mutable-accumulator
# `Id.run do` and the `copyIdentity`/`bareCallable` composition, and write both
# layers of all three attributes as one direct record literal. The admissible
# domain is UNRESTRICTED (the precondition is `True`), so a source may supply
# nothing at either layer; where it does, the freshly synthesised callable holds
# nothing for that attribute and answers for it on no account of its own, so the
# result is observed to hold nothing there too. The literal spells the two-layer
# transfer formula out per attribute and is value-identical to gold on the whole
# domain.
_POS_RECORD = (
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs :=\n"
    "  let n := source.name.ownEntry.overlay source.name.observed\n"
    "  let m := source.module.ownEntry.overlay source.module.observed\n"
    "  let q := source.qualname.ownEntry.overlay source.qualname.observed\n"
    "  { name := { observed := n, ownEntry := n },\n"
    "    module := { observed := m, ownEntry := m },\n"
    "    qualname := { observed := q, ownEntry := q },\n"
    "    wrapped := true, selfSufficient := true }"
)
_POS_PROOF = (
    "  intro source _\n"
    "  unfold problem_spec_attachIdentity implementation_attachIdentity"
    " transferredEntry\n"
    "  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩\n"
    "  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl\n"
    "  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl\n"
    "  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl\n"
    "  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl\n"
    "  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl\n"
    "  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl"
)

# (2) The SEQUENTIAL two-pass construction, which is the shape the transfer
# really has: first place each attribute from what a reader observes on
# `source`, then lay `source`'s own table over the result's table as a whole,
# each pass writing to the SAME storage so the later one wins. Gold fuses the
# two passes into one `overlay` per attribute; this control keeps them apart and
# runs them in order, so it is a genuinely different implementation of the same
# function. If the spec could only be satisfied by the fused form it would be
# over-fitted to gold's shape; this case is what shows it is not.
_POS_TWO_PASS = (
    "def layOnto (srcLayer : AttrSlot) (dst : IdentityAttr) : IdentityAttr :=\n"
    "  let e := srcLayer.overlay dst.ownEntry\n"
    "  { observed := e.overlay dst.observed, ownEntry := e }\n"
    "\n"
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do\n"
    "  let mut bound : CallableAttrs := bareCallable\n"
    "  bound := { bound with name := layOnto source.name.observed bound.name,\n"
    "                        module := layOnto source.module.observed bound.module,\n"
    "                        qualname := layOnto source.qualname.observed bound.qualname }\n"
    "  bound := { bound with name := layOnto source.name.ownEntry bound.name,\n"
    "                        module := layOnto source.module.ownEntry bound.module,\n"
    "                        qualname := layOnto source.qualname.ownEntry bound.qualname,\n"
    "                        wrapped := true }\n"
    "  return bound"
)
_POS_TWO_PASS_PROOF = (
    "  intro source _\n"
    "  unfold problem_spec_attachIdentity implementation_attachIdentity layOnto"
    " transferredEntry bareCallable\n"
    "  simp only [Id.run]\n"
    "  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, rfl, rfl⟩\n"
    "  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl\n"
    "  · cases source.name.ownEntry <;> cases source.name.observed <;> rfl\n"
    "  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl\n"
    "  · cases source.module.ownEntry <;> cases source.module.observed <;> rfl\n"
    "  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl\n"
    "  · cases source.qualname.ownEntry <;> cases source.qualname.observed <;> rfl"
)


def _ground(record, label):
    """A ground `have` spliced ahead of the frozen tactic body: the obligation is
    SATISFIABLE at one concrete input, discharged by `decide`."""
    return (
        f"  have {label} : problem_spec_attachIdentity\n"
        f"      {record}\n"
        "      (implementation_attachIdentity\n"
        f"        {record}) := by\n"
        "    unfold problem_spec_attachIdentity implementation_attachIdentity"
        " copyIdentity IdentityAttr.transfer transferredEntry bareCallable\n"
        "    decide\n"
    )


# The F2P-shaped ground input: a genuine plain function named "method" in module
# "tests", itself NOT runnable on its own.
_ADMISS_PREFIX = _ground(
    _plain("method", "tests", "Test.method"), "_ground_plain")

# The DISAGREEING-layer ground input: the class the two-layer carrier exists
# for. Here the spec's required result is the one the real routine is observed
# to produce (the table's entries, not the reader-visible ones), so discharging
# this `have` by `decide` is a machine-checked statement that the modeled
# behavior agrees with the real one at that point.
_ADMISS_SHADOW_PREFIX = _ground(_SHADOW_REAL, "_ground_shadow")


# --------------------------------------------------------------------------- #
# REJECT (uniqueness / SPEC-TOO-WEAK) rival impls                              #
# --------------------------------------------------------------------------- #
def _entry_rival(n_expr, m_expr, q_expr, wrapped="true", ss="true"):
    """A rival of gold's SHAPE — both layers of the result driven by one entry
    per attribute — differing only in how that entry is computed. The freshly
    synthesised callable answers for NONE of the three attributes on its own
    account, so each attribute's reader-visible layer is the transferred entry
    outright and no facet carries a non-source fallback."""
    return (
        "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs :=\n"
        f"  let n := {n_expr}\n"
        f"  let m := {m_expr}\n"
        f"  let q := {q_expr}\n"
        "  { name := { observed := n, ownEntry := n },\n"
        "    module := { observed := m, ownEntry := m },\n"
        "    qualname := { observed := q, ownEntry := q },\n"
        f"    wrapped := {wrapped}, selfSufficient := {ss} }}"
    )


_GOLD_N = "transferredEntry source.name"
_GOLD_M = "transferredEntry source.module"
_GOLD_Q = "transferredEntry source.qualname"

# PREPATCH (name presence — the F2P clause): the pre-fix behavior, the freshly
# synthesised callable returned as-is, carrying none of `source`'s identity.
_PREPATCH = (
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do\n"
    "  let mut bound : CallableAttrs := bareCallable\n"
    "  return bound"
)

# SIBLING (name value — partial domain): compute the NAME facet from the MODULE
# attribute (rest gold). Right only where a callable's name token equals its
# module token; wrong otherwise.
_SIBLING = _entry_rival(_GOLD_M, _GOLD_M, _GOLD_Q)

# DROP-MODULE: transfer name and qualname, but leave the module entry absent.
_DROP_MODULE = _entry_rival(_GOLD_N, "AttrSlot.vacant", _GOLD_Q)

# DROP-QUALNAME: transfer name and module, but leave the qualified name absent.
_DROP_QUALNAME = _entry_rival(_GOLD_N, _GOLD_M, "AttrSlot.vacant")

# WRAP-ECHO: transfer all three attributes, but ECHO `source.wrapped` instead of
# asserting the delegation flag as the constant `true`.
_WRAP_ECHO = _entry_rival(_GOLD_N, _GOLD_M, _GOLD_Q, wrapped="source.wrapped")

# OBSERVED-PASS-ONLY: keep only the FIRST pass — place each attribute from what
# a reader observes on `source` and never lay `source`'s own table over the
# result's. Right exactly on sources whose two layers agree (every plain
# function, and every own-table callable whose table matches what a reader
# sees); wrong on every source where they disagree, where the table entry is the
# one that survives in the real transfer.
_OBSERVED_ONLY = _entry_rival("source.name.observed", "source.module.observed",
                              "source.qualname.observed")

# TABLE-PASS-ONLY: keep only the SECOND pass — lay `source`'s own table over the
# result's and never place anything from what a reader observes. Wrong at every
# plain function, whose table holds nothing at all.
_TABLE_ONLY = _entry_rival("source.name.ownEntry", "source.module.ownEntry",
                           "source.qualname.ownEntry")

# LAYER-PRECEDENCE-SWAPPED: both passes, in the WRONG order — what a reader
# observes laid over the source's own table instead of the other way round.
# Indistinguishable from gold unless both layers are held AND differ.
_PRECEDENCE_SWAPPED = _entry_rival(
    "source.name.observed.overlay source.name.ownEntry",
    "source.module.observed.overlay source.module.ownEntry",
    "source.qualname.observed.overlay source.qualname.ownEntry")

# RESULT-TABLE-DISAGREES: the reader-visible layer of the result is computed
# correctly, but the entry left in the result's OWN table is taken from the
# reader-visible layer of `source` instead of from the transfer. Satisfies every
# `observed` clause and violates the `ownEntry` ones — the rival that exists
# precisely because both layers of the result are pinned.
_RESULT_TABLE = (
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs :=\n"
    "  { name := { observed := transferredEntry source.name,\n"
    "              ownEntry := source.name.observed },\n"
    "    module := { observed := transferredEntry source.module,\n"
    "                ownEntry := source.module.observed },\n"
    "    qualname := { observed := transferredEntry source.qualname,\n"
    "                  ownEntry := source.qualname.observed },\n"
    "    wrapped := true, selfSufficient := true }"
)

# (No DROP-MODULE-FALLBACK rival: the destination the construction really builds
# answers for NONE of the three attributes on its own account, so no facet of the
# result carries a non-source fallback and "the transferred entry outright" is
# what every reader-visible clause states. A variant computing the module's
# reader-visible layer that way is value-identical to gold on the whole domain,
# i.e. not a rival at all — there is no input at which it and gold disagree, so
# no witness can discriminate it. The `result.module.observed` clause keeps its
# adversaries in the drop-module and collapse-module rivals below.)

# REVERSED-TRANSFER (usability): run the identity transfer the other way round,
# so the object handed back is `source` carrying the synthesised callable's
# (absent) attributes rather than the synthesised callable carrying `source`'s.
_REVERSED = (
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs := Id.run do\n"
    "  let mut bound : CallableAttrs := bareCallable\n"
    "  bound := copyIdentity bound source\n"
    "  return bound"
)

# COLLAPSE-MODULE (three-state carrier, MODULE facet): treat an entry whose
# content is nothing in particular as though NO entry were held, so the module
# facet is left with no entry at all where the real transfer hands the source's
# own contentless entry on.
_COLLAPSE_MODULE = _entry_rival(
    _GOLD_N,
    "(match transferredEntry source.module with"
    " | .filled (some s) => AttrSlot.filled (some s)"
    " | _ => AttrSlot.vacant)",
    _GOLD_Q)

# COLLAPSE-NAME (three-state carrier, NAME facet): the same collapse on the
# facet the F2P observable reads directly — an entry containing nothing in
# particular is turned into no entry at all.
_COLLAPSE_NAME = _entry_rival(
    "(match transferredEntry source.name with"
    " | .filled (some s) => AttrSlot.filled (some s)"
    " | _ => AttrSlot.vacant)",
    _GOLD_M, _GOLD_Q)

# RETURN-THE-SOURCE (usability): hand back `source` itself, flipping only the
# delegation flag.
_RETURN_SOURCE = (
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs :=\n"
    "  { source with wrapped := true }"
)

# ARGUMENT-ECHO (ungrounded oracle, argument form): hand the input record back
# with both booleans set to the constants the postcondition names, doing NONE of
# the transfer work. It derives its answer from the argument alone and is
# indistinguishable from a correct construction under a one-layer reading of the
# attribute surface.
_ARG_ECHO = (
    "def implementation_attachIdentity (source : CallableAttrs) : CallableAttrs :=\n"
    "  { source with wrapped := true, selfSufficient := true }"
)


def _witness(record, extra_unfold=""):
    """A Lean `example` stating the spec is VIOLATED at one concrete input.
    Checked in a proof-stripped file: it elaborates against the rival (the rival
    provably contradicts the spec at `record`) and FAILS against the frozen
    solution (gold satisfies the spec there), so it is a real discriminator."""
    # `bareCallable` is NOT unfolded by default: a rival that drives both layers
    # of each attribute from one entry never mentions it, and `unfold` fails
    # outright on a name absent from the goal. Cases whose rival does build on the
    # freshly synthesised callable ask for it via `extra_unfold`.
    unfold = ("problem_spec_attachIdentity implementation_attachIdentity"
              " transferredEntry" + extra_unfold)
    return (
        "example : ¬ problem_spec_attachIdentity\n"
        f"    {record}\n"
        "    (implementation_attachIdentity\n"
        f"      {record}) := by\n"
        f"  unfold {unfold}\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_attachIdentity`
    # STATEMENT is byte-identical; only the tactic body is re-proved for the new
    # shape. No helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-record-literal",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_RECORD), _PROOF_GOLD, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` and "
            "the `copyIdentity`/`bareCallable` composition, writing both layers of "
            "all three attributes as one direct record literal, must satisfy all "
            "eight clauses; if it cannot, the spec is SPEC-TOO-STRONG. "
            "Value-identical to gold on the whole domain (the entry transferred for "
            "each attribute is the source's own table entry where it holds one and "
            "what a reader observes otherwise; the synthesised callable is "
            "self-sufficient either way). Proof: after `unfold`, each clause closes "
            "by cases on the two layers of the corresponding attribute — no new "
            "declaration, axiom, or assumption token. Defends every top-level "
            "clause at once, INCLUDING the usability clause: it shows that clause is "
            "satisfiable by an ordinary correct construction and does not over-fit "
            "gold's shape."
        ),
    },
    {
        "id": "pos-two-pass-sequential",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_TWO_PASS), _PROOF_GOLD, _POS_TWO_PASS_PROOF),
        "rationale": (
            "the transfer really runs as TWO passes over the same storage — each "
            "attribute placed from what a reader observes on `source`, then "
            "`source`'s own table laid over the result's as a whole — and gold "
            "fuses them into one `overlay` per attribute. This control keeps the "
            "passes apart, runs them in order through a local helper, and must "
            "still satisfy all eight clauses. It is the case that shows the spec "
            "pins the FUNCTION rather than gold's fused form: a postcondition "
            "satisfiable only by the fused expression would be over-fitted, and a "
            "later realignment of either pass would be untestable. The helper `def` "
            "lives inside the impl region (so `same_spec` still holds) and no "
            "theorem, lemma, axiom or assumption token is introduced."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — positive controls confirming the obligation is SATISFIABLE
    # (non-vacuous) at concrete inputs rather than only provable in the abstract.
    # nagini's precondition-admission probe is the analogue; here each is
    # discharged as a ground `have` inside the proof region, alongside the frozen
    # obligation (closed verbatim).
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_PREFIX + _PROOF_GOLD),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a genuine plain "
            "function named \"method\" in module \"tests\", qualname "
            "\"Test.method\", whose own attribute table holds nothing and which is "
            "itself NOT runnable on its own) where the spec requires the "
            "synthesised callable to carry that exact identity at BOTH layers, be "
            "recorded as delegating, and still be runnable on its own, by `decide`; "
            "then the frozen obligation is closed verbatim. Verifies (else the spec "
            "is unsatisfiable at the normal input). The ground input deliberately "
            "sets the usability field FALSE on `source`, which is the real shape — "
            "the original expects its object handed in first — so the case also "
            "confirms the usability clause is admissible there rather than only "
            "when the input already satisfies it. Nothing is assumed: the theorem "
            "STATEMENT is byte-identical, the ground instance is a `have` inside the "
            "existing tactic body, and no new declaration/axiom/`sorry` is added."
        ),
    },
    {
        "id": "admiss-disagreeing-layers-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_SHADOW_PREFIX + _PROOF_GOLD),
        "rationale": (
            "the same non-vacuity check at the input class the two-layer carrier "
            "exists for: a source whose own attribute table holds "
            "\"dummy\"/\"deco_patched\"/\"_update_method_wrapper.<locals>.dummy\" "
            "while a reader of it is answered \"m\"/\"__main__\"/\"Outer.m\". Those "
            "are the values the real routine is observed on, and the spec's required "
            "result there is the TABLE's three entries, so discharging this `have` "
            "by `decide` is a machine-checked statement that the modeled behavior "
            "agrees with the real one at that point rather than only at inputs whose "
            "two layers coincide. A spec that predicted the reader-visible values "
            "would make this instance unprovable, so the case is a standing guard "
            "against a regression to a one-pass model."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would be
    # a true verify-does-not-imply-resolve break rather than an artifact, and (b)
    # a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-prepatch-name-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH),
        "refinement": (
            "this IS the pre-fix behavior: the synthesised callable is returned "
            "bare, carrying none of the source's identity. Its faithful real patch "
            "is exactly the pre-patch code, whose assembled callable has no name at "
            "all. The F2P observable reads the assembled callable's name and "
            "requires it equal the original's; with the name ABSENT that observable "
            "is unsatisfiable, so it does NOT resolve — this is the leg's prepatch."
        ),
        "rationale": (
            "REJECT from the clause `result.name.ownEntry = transferredEntry "
            "source.name`: at a genuine plain function the entry to transfer is the "
            "one a reader is answered with, and the bare result holds nothing at "
            "either layer, so the clause fails. Refuted at the F2P-shaped input "
            "(name \"method\", module \"tests\", qualname \"Test.method\", own table "
            "empty). Attacks the load-bearing name presence facet."
        ),
        "witness": _witness(_plain("method", "tests", "Test.method"),
                            extra_unfold=" bareCallable"),
    },
    {
        "id": "weak-sibling-name-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SIBLING),
        "refinement": (
            "computing the NAME facet from the MODULE attribute corresponds to a "
            "patch that sets the assembled callable's name to the original's module "
            "(e.g. \"tests\") instead of its name (e.g. \"method\"). The F2P asserts "
            "the observed name equals the original's name, so it FAILS on the actual "
            "fixture (name token != module token). It only happens to be right where "
            "a callable's name coincides with its module; it does NOT resolve. "
            "Verifying => SPEC-TOO-WEAK."
        ),
        "rationale": (
            "REJECT from the name clauses: the rival pins both layers of the "
            "result's name to the module attribute's transferred entry, which is not "
            "provably equal to the name's. Refuted where the two tokens differ "
            "(name \"a\", module \"b\") — a distinct input point exercising the name "
            "facet on a wrong VALUE rather than an absence."
        ),
        "witness": _witness(_plain("a", "b", "c")),
    },
    {
        "id": "weak-drop-module",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_MODULE),
        "refinement": (
            "dropping the module transfer corresponds to a patch that transfers the "
            "name (and qualname) but leaves the assembled callable without a module "
            "of its own. The FAIL_TO_PASS observable reads the assembled callable's "
            "module with a defaulted getattr and asserts the answer is not None; "
            "with the transfer dropped the read finds nothing at all on the "
            "synthesised callable and falls to that default, so the assertion "
            "fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result.module.ownEntry = transferredEntry source.module`: "
            "at a callable supplying a module the rival leaves the result's table "
            "empty of it, so the clause fails (and the reader-visible module clause "
            "fails with it, nothing at all standing where the original's module "
            "should). Refuted at (name \"f\", module \"mod\", qualname \"q\"), "
            "varying the module field off the values the other rivals hold it at."
        ),
        "witness": _witness(_plain("f", "mod", "q")),
    },
    {
        "id": "weak-drop-qualname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_QUALNAME),
        "refinement": (
            "dropping the qualified-name transfer corresponds to a patch that "
            "transfers name and module but leaves the assembled callable without its "
            "qualified name. The wrapper-assignment surface the fix preserves "
            "includes the qualified name; an absent one leaves the assembled "
            "callable missing a preserved attribute. It does NOT faithfully resolve."
        ),
        "rationale": (
            "REJECT from the qualname clauses: at a callable supplying a qualified "
            "name the result holds nothing at either layer, so both fail. Refuted at "
            "(name \"h\", module \"hm\", qualname \"H.h\"), a distinct input point "
            "exercising the qualname field."
        ),
        "witness": _witness(_plain("h", "hm", "H.h")),
    },
    {
        "id": "weak-wrapped-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRAP_ECHO),
        "refinement": (
            "echoing the source's delegation flag instead of asserting it "
            "corresponds to a patch that never records the assembled callable as "
            "delegating to the original — the `__wrapped__` link the real "
            "wrapper-assignment routine always sets, last of all. A synthesised "
            "callable begins un-delegating, so the echo leaves it that way, "
            "diverging from the gold behavior; it does NOT faithfully resolve."
        ),
        "rationale": (
            "REJECT from the clause `result.wrapped = true`: the flag is a CONSTANT "
            "in the spec, not an echo of `source.wrapped`. At a source with "
            "`wrapped = false` the rival returns `wrapped = false`, so the clause "
            "fails. Refuted at (name \"w\", module \"wm\", qualname \"W.w\", "
            "wrapped false) — the only rival that varies the `wrapped` input field, "
            "demonstrating the clause's independence from it."
        ),
        "witness": _witness(_plain("w", "wm", "W.w")),
    },
    {
        "id": "weak-observed-pass-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OBSERVED_ONLY),
        "refinement": (
            "keeping only the per-attribute pass corresponds to a patch that copies "
            "each identity attribute by READING it off the original and never lays "
            "the original's own attribute table over the assembled callable's. The "
            "real routine does both, and the table pass runs SECOND, into the same "
            "storage — so wherever the original's table disagrees with what a reader "
            "of it is answered, the table's entry is the one the assembled callable "
            "ends up carrying. That disagreement is not exotic: it is what the "
            "decorator stack itself produces, so a patch stopping after the first "
            "pass leaves the assembled callable reporting a different identity from "
            "the one downstream code actually sees, and the wrapper-assignment "
            "observable reads that identity. It does NOT faithfully resolve. This is "
            "the rival a ONE-LAYER model of the attribute surface cannot express, "
            "and it is right on every input whose two layers agree — so no spread of "
            "ordinary witnesses exposes it; verifying => SPEC-TOO-WEAK on the second "
            "pass specifically."
        ),
        "rationale": (
            "REJECT from `result.name.ownEntry = transferredEntry source.name` and "
            "its `observed` twin: `transferredEntry` hands on the source's own table "
            "entry whenever its table holds one, and the rival hands on what a "
            "reader observes instead. Refuted at the disagreeing-layer input (table "
            "\"dummy\"/\"deco_patched\"/\"_update_method_wrapper.<locals>.dummy\", "
            "reader-visible \"m\"/\"__main__\"/\"Outer.m\") — the real values the "
            "routine is observed on, and an input point in a state no other rival's "
            "witness visits."
        ),
        "witness": _witness(_SHADOW_REAL),
    },
    {
        "id": "weak-table-pass-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_TABLE_ONLY),
        "refinement": (
            "keeping only the whole-table pass corresponds to a patch that lays the "
            "original's own attribute table over the assembled callable's and never "
            "copies the attributes one by one. A plain function keeps NO identity in "
            "its own table — its name, module and qualified name are answered for by "
            "the kind of thing it is — so this patch transfers nothing at all for the "
            "commonest original there is, which is exactly the shape the F2P uses. "
            "The assembled callable is left with no name, so the observable is "
            "unsatisfiable and it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the name clauses at the F2P-shaped input: the source's table "
            "holds nothing, so `transferredEntry` is what a reader observes, while "
            "the rival transfers the (empty) table. Refuted at (name \"method\", "
            "module \"tests\", qualname \"Test.method\", own table empty) — the same "
            "input the prepatch rival is refuted at, reached by the opposite error, "
            "which is what makes the pair evidence that BOTH passes are pinned."
        ),
        "witness": _witness(_plain("method", "tests", "Test.method")),
    },
    {
        "id": "weak-layer-precedence-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PRECEDENCE_SWAPPED),
        "refinement": (
            "running both passes in the other order corresponds to a patch that lays "
            "the original's attribute table over the assembled callable FIRST and "
            "then copies the attributes one by one on top, so the per-attribute copy "
            "wins where the real routine lets the table win. The two passes write to "
            "the same storage, and which runs last decides what the assembled "
            "callable reports for every attribute the original holds at both layers "
            "with different values. On such an original this patch publishes the "
            "reader-visible value where the real construction publishes the table's, "
            "so the wrapper-assignment observable sees a different identity. It does "
            "NOT faithfully resolve."
        ),
        "rationale": (
            "REJECT from the name clauses: `transferredEntry` lets the source's own "
            "table entry survive, the rival lets the reader-visible one survive, and "
            "the two differ exactly when both layers are held and disagree. Refuted "
            "at (table \"held-name\"/\"held-mod\"/\"held-qual\", reader-visible "
            "\"seen-name\"/\"seen-mod\"/\"seen-qual\") — a second, distinct "
            "disagreeing-layer input point, so this rival and the observed-pass-only "
            "one are refuted at different records."
        ),
        "witness": _witness(_shadowed("seen-name", "held-name",
                                      "seen-mod", "held-mod",
                                      "seen-qual", "held-qual")),
    },
    {
        "id": "weak-result-table-disagrees",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RESULT_TABLE),
        "refinement": (
            "this patch makes the assembled callable REPORT the right identity while "
            "leaving the wrong entries in its own attribute table: what a reader of "
            "the assembled callable is answered is computed correctly, but the table "
            "is filled from the reader-visible layer of the original rather than from "
            "the transfer. The table is not decoration — it is what a FURTHER "
            "transfer off this callable hands on, which is exactly what happens when "
            "decorators stack, and it is what the wrapper-assignment tests inspect "
            "through the assembled callable's own attribute dictionary. So the "
            "divergence is observable one decorator later and it does NOT faithfully "
            "resolve. It is the rival that exists because BOTH layers of the result "
            "are pinned: against a postcondition that constrained only what a reader "
            "observes, it would verify."
        ),
        "rationale": (
            "REJECT from `result.name.ownEntry = transferredEntry source.name` "
            "ALONE: every `observed` clause holds of this rival by construction, so "
            "the rejection is attributable to the own-table clause and to nothing "
            "else. Refuted at a source whose name layers disagree (table \"dummy\", "
            "reader-visible \"m\") while its module and qualified name agree at both "
            "layers, so only the name's table clause can fail."
        ),
        "witness": _witness(_rec(_attr(_T("m"), _T("dummy")),
                                 _attr(_T("tests"), _T("tests")),
                                 _attr(_T("Q.m"), _T("Q.m")))),
    },
    {
        "id": "weak-reversed-transfer-usability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REVERSED),
        "refinement": (
            "running the identity transfer in the REVERSED direction corresponds to "
            "a patch that dresses the ORIGINAL callable with the synthesised "
            "callable's attributes and hands the original back, instead of dressing "
            "the synthesised callable with the original's identity. The object the "
            "caller then runs is the original, which still expects the object it "
            "belongs to to be handed in first — so invoking it with the arguments of "
            "the call alone fails outright, taking the F2P observable and the "
            "pre-existing decorator tests with it. It does NOT resolve. This rival "
            "is INVISIBLE to the metadata clauses at the witness input, so it is the "
            "rival that made a metadata-only postcondition too weak; verifying => "
            "SPEC-TOO-WEAK on the usability facet specifically."
        ),
        "rationale": (
            "REJECT from the clause `result.selfSufficient = true`: the rival hands "
            "back the input object, so the result's usability is `source`'s rather "
            "than the constant `true`. Refuted at a source that is NOT runnable on "
            "its own whose three attributes are each held at both layers with the "
            "same content (name \"r\", module \"rm\", qualname \"R.r\", "
            "selfSufficient false) — where all six metadata clauses hold and only "
            "this clause fails, which is exactly what makes the witness attributable "
            "to the usability clause and to nothing else. Each attribute is held at "
            "BOTH layers because the reversed transfer hands the source's own table "
            "entry back at both; at a source whose table were empty the own-entry "
            "clauses would fail too and the witness would no longer isolate "
            "usability."
        ),
        "witness": _witness(
            _tabled("r", "rm", "R.r"),
            extra_unfold=" copyIdentity IdentityAttr.transfer"),
    },
    {
        "id": "weak-return-source-usability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RETURN_SOURCE),
        "refinement": (
            "handing back the ORIGINAL callable with only the delegation flag "
            "flipped corresponds to a patch that skips the synthesised callable "
            "entirely and passes the original down to the decorators. The original "
            "still expects the object it belongs to to be supplied first, so the "
            "decorated call — made with the arguments of the call alone — fails, "
            "breaking the F2P observable and the pre-existing decorator tests. It "
            "does NOT resolve. Like the reversed-transfer rival it satisfies every "
            "metadata clause at the witness input, so only the usability clause "
            "separates it from gold."
        ),
        "rationale": (
            "REJECT from the clause `result.selfSufficient = true`: the result IS "
            "the input record (bar the delegation flag), so its usability is "
            "`source`'s, not the constant `true`. Refuted at a source that is not "
            "runnable on its own whose three attributes are held at both layers with "
            "the same content (name \"s\", module \"sm\", qualname \"S.s\") — a "
            "distinct input point from the reversed-transfer rival's, exercising the "
            "same clause through a different wrong construction, and one where every "
            "metadata clause holds of the rival."
        ),
        "witness": _witness(_tabled("s", "sm", "S.s")),
    },
    {
        "id": "weak-argument-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ARG_ECHO),
        "refinement": (
            "handing the ORIGINAL back with both flags set to the values the "
            "postcondition names corresponds to a patch that performs no transfer at "
            "all and merely asserts the two booleans — the argument-echo form of an "
            "ungrounded oracle. Its faithful real patch returns the original callable "
            "and claims it is runnable on its own, which is false: the original still "
            "expects the object it belongs to first, so the decorated call fails and "
            "the F2P observable is unsatisfiable. It does NOT resolve. It is included "
            "because the echo is the cheapest way to satisfy a postcondition, and "
            "under a ONE-LAYER reading of the attribute surface it would be "
            "indistinguishable from a correct construction."
        ),
        "rationale": (
            "REJECT from the name clauses: the echo copies BOTH layers of the "
            "original verbatim, so at a source whose two layers disagree the result "
            "reports the reader-visible value while its table holds the other, where "
            "the transfer makes both the table's. Refuted at a third, distinct "
            "disagreeing-layer input (table \"kept\"/\"kept-mod\"/\"kept-qual\", "
            "reader-visible \"shown\"/\"shown-mod\"/\"shown-qual\"). Note this rival "
            "is rejected on the METADATA, not on usability: it sets the usability "
            "flag to the constant, which is why the echo needs the two-layer clauses "
            "to be refutable at all."
        ),
        "witness": _witness(_shadowed("shown", "kept", "shown-mod", "kept-mod",
                                      "shown-qual", "kept-qual")),
    },
    {
        "id": "weak-collapse-module-contentless-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_COLLAPSE_MODULE),
        "refinement": (
            "collapsing an entry that contains nothing in particular into 'no "
            "entry held' corresponds to a patch that consults an attribute's "
            "CONTENT to decide whether to transfer it, instead of consulting "
            "whether the entry is held at all. The real transfer is driven by "
            "whether the entry is held, so a source holding a contentless "
            "module entry has that entry handed on verbatim; this rival drops it "
            "and leaves the assembled callable holding no module at all. A "
            "downstream reader inspecting the assembled callable's module "
            "therefore finds nothing where the real construction shows the "
            "original's own (contentless) entry, so reading that attribute raises "
            "instead of answering. It does NOT faithfully resolve. Verifying => "
            "SPEC-TOO-WEAK on the three-state carrier: it is the rival a two-state "
            "present/absent encoding of the attribute surface cannot distinguish "
            "from gold."
        ),
        "rationale": (
            "REJECT from the module clauses: `overlay` dispatches on whether an "
            "entry is HELD, never on its content, so at a source holding "
            "`filled none` the transferred entry is `filled none` while the rival "
            "yields `vacant`. Refuted at (name \"method\", "
            "module = a contentless entry a reader is answered with, qualname "
            "\"Test.method\") — an input point in the carrier's THIRD state, which "
            "no other rival visits on the module facet. The name and qualname legs "
            "hold there, so the rejection is attributable to the module clauses "
            "alone."
        ),
        "witness": _witness(_rec(_attr(_T("method")), _attr(_N),
                                 _attr(_T("Test.method")))),
    },
    {
        "id": "weak-collapse-name-contentless-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_COLLAPSE_NAME),
        "refinement": (
            "the same content-driven collapse on the NAME facet, the one the F2P "
            "observable reads: a patch that transfers an attribute only when its content "
            "is text leaves the assembled callable holding NO name entry where the "
            "real transfer hands on the original's contentless one. The F2P "
            "observable reads the assembled callable's name attribute; with no "
            "entry held that read raises rather than returning the original's "
            "entry, which is the very failure mode the issue reports. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the name clauses: they equate both layers of the result to "
            "the transferred entry on the three-state carrier, so at a source whose "
            "name is a contentless entry they require `filled none` while the rival "
            "yields `vacant`. Refuted at (name = a contentless entry, module "
            "\"tests\", qualname \"Test.method\") — a distinct input point from the "
            "collapse-module rival's, exercising the carrier's third state on the "
            "facet the F2P observable reads, where the module clauses are satisfied "
            "and cannot be confused for the cause."
        ),
        "witness": _witness(_rec(_attr(_N), _attr(_T("tests")),
                                 _attr(_T("Test.method")))),
    },
]


# The metadata transfer is modeled deeply (`copyIdentity`); no consumed axiom and
# no opaque callee, so there is no in-model axiom obligation for the PBT axiom
# lane to re-discharge (that lane belongs to G-AX in any case).
AXIOM_TESTS = []
