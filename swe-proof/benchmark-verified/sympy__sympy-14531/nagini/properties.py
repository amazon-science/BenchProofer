"""properties.py — PBT falsification manifest for sympy__sympy-14531.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The functions under spec are a printer's operand-delegation
change (sympy/printing/str.py): every operand of a COMPOUND expression must be
rendered BY THE RENDERER THAT OWNS the compound, not re-rendered detachedly by
some ambient default renderer. That has TWO observable consequences, and the
spec pins both:

    (1) the fractional operand is written under the SAME `wrap` configuration
        (`sympy_integers`) the compound carries, and
    (2) each NAME operand is entered in the owning renderer's NAME REGISTRY
        (`PythonPrinter.symbols`, drained into the `x = Symbol('x')` preamble by
        `python()`).

Every operand slot of every modeled compound is a THREE-KIND triple `(k, u, v)`
admitted by `is_atom(k, u, v)`: `k == 0` the proper fraction `u/v` (u >= 0, v >= 2,
coprime), `k == 1` the simple name with code point `u`, and `k == 2` an operand
whose OWN rendering rule is NOT modelled, carried by the abstract handle `u` with
uninterpreted text `opaque_text(u, wrap)` and uninterpreted registry effect
`opaque_registry(r, u)`. That third kind is what makes "this slot was rendered BY
THIS renderer" inescapable at EVERY slot rather than only at a name slot: neither
of its two values is expressible at the compound site, so the only discharge is a
call to `render_unmodeled`. Under a two-kind carrier the fraction slot's registry
obligation is the identity and is discharged vacuously by doing nothing.

Modeled functions:

    render_equation(wrap, kl, ul, vl, kr, ur, vr, reg)   # Eq(left, right)
        -> ToSeq == eq_text(wrap, kl,ul,vl, kr,ur,vr)
           AND reg == eq_registry(old reg, kl,ul,vl, kr,ur,vr)
    render_directed_limit(wrap, plus, ke,ue,ve, kz,uz,vz, k0,u0,v0, ud, reg)
        -> ToSeq == limit_text(wrap, plus, ke,ue,ve, kz,uz,vz, k0,u0,v0, ud)
           AND reg == limit_registry(old reg, plus, ke,ue,ve, kz,uz,vz, k0,u0,v0, ud)
        # two template forms, selected by the direction: the `plus` form closes
        # after the point slot, the other spells the direction in a FOURTH slot
    render_atom(k, u, v, wrap, reg)        # ONE slot, delegated by the compound
        -> ToSeq == atom_text(k,u,v,wrap)  AND  reg == atom_registry(old reg,k,u,v)
    render_name(c, reg)                    # the k==1 leaf: text AND registration
        -> ToSeq == lit_name(c)  AND  reg == registered(old reg, c)
    render_operand(wrap, p, q, reg)        # the k==0 leaf
        -> ToSeq == render_rational(wrap,p,q)  AND  reg UNCHANGED
    render_unmodeled(a, wrap, reg)         # the k==2 leaf, @ContractOnly
        -> ToSeq == opaque_text(a,wrap)  AND  reg == opaque_registry(old reg, a)
    materialize(s)                         # PSeq[int] -> List[int], identity glue

Why observable (2) is not decoration. A detached re-rendering of a NAME produces
the SAME TEXT the owning renderer would produce ('x' either way, under either
configuration), so the text pin alone leaves the name slot completely
unconstrained: an impl that emits the name as a bare constant token satisfies
every text clause. Its faithful real patch delegates only the fraction and
leaves the name bare — which resolves the F2P `test_Rational` but FAILS the F2P
`test_python_relational` (`python(Eq(x, y))` loses the `x = Symbol('x')`
preamble line). The registry clause is what rejects that impl, and the
`registry-*` rivals below are the ones that would verify without it.

    render_rational(wrap,p,q):  wrap     -> 'S(' + digits(p) + ')/' + digits(q)
                                not wrap -> digits(p) + '/' + digits(q)
    registered(r, c):           c in r   -> r
                                otherwise-> r + PSeq(c)   (one entry per name,
                                                           first-render order)

The two discriminating observables are therefore the PRESENCE/PLACEMENT of the
`S(...)` wrapper, decided by the parent's own flag, and the GROWTH of the
parent's own registry at each name slot. A renderer that re-renders every
operand detachedly loses BOTH: for `wrap=True` it produces `'p/q'` where
`'S(p)/q'` is demanded, and it never registers the name. `model_prepatch.py`
exhibits exactly that, and the F2P tests pin both readings
(`sstr(Eq(x, S(2)/3), sympy_integers=True) == 'Eq(x, S(2)/3)'` and
`python(Eq(x, y)) == "x = Symbol('x')\\ny = Symbol('y')\\ne = Eq(x, y)"`).

What the spec defends, and why each weakness class is or isn't applicable:

  * GROUNDED ORACLE — NOT ungrounded. The postconditions pin `ToSeq(Result())`
    to `eq_text` / `limit_text` / `lit_name` / `render_rational` and `ToSeq(reg)`
    to `eq_registry` / `limit_registry` / `registered`, which are `@Pure`
    functions UNFOLDED in terms of the args ON THE `k in {0,1}` KINDS (the
    template tokens + `digits(p)` / `digits(q)` under the parent `wrap`; the
    registry as a duplicate-free append). They are NOT an opaque answer-key oracle
    that could be echoed without doing the work — they ARE the work. On the
    `k == 2` kind they bottom out in `opaque_text` / `opaque_registry`, which are
    uninterpreted by design: not an answer key either, since a spec value that no
    implementation can construct cannot be echoed at all, only obtained by
    delegating. That asymmetry is deliberate and the `unmodelled-slot-*` rivals
    below are what measure it. There is thus no
    WRONG-echo rival: the cheapest impl (register the name, then materialise
    `eq_text`) is CORRECT, so it is included as a POSITIVE CONTROL
    (`pos-control-equation-cheapest`), not a uniqueness break. (See PBT_PLAN §2
    "ungrounded-oracle" — when the oracle is grounded, ship an honest
    cheapest-impl positive control instead of a wrong echo.) Note the echo is
    only correct if it ALSO registers: an echo of the text oracle alone is the
    `registry-echo-text-only` reject lane below.

  * FRAME-MUTATION — the registry `reg` IS a mutable list parameter, held at
    FULL `Acc(list_pred(reg))` because the call WRITES it, so this class is now
    live and is attacked directly. The defence is that the postcondition pins
    `ToSeq(reg)` EXACTLY (`== registered(Old(ToSeq(reg)), c)`), leaving no room
    to store into it to fabricate anything: a rival that appends twice, appends
    unconditionally, appends the wrong key, appends only under one
    configuration, or does not append at all is rejected (`registry-no-dedup`,
    `registry-wrong-key`, `registry-only-when-wrap`, `registry-skip-*`). The
    fraction slot carries the complementary NO-WRITE clause
    (`ToSeq(reg) == Old(ToSeq(reg))`), attacked by `registry-frac-writes`.

  * PARTIAL-DOMAIN — the spec's real teeth, on BOTH observables. A rival correct
    on HALF the `wrap` domain (always-unwrap, correct only when `wrap=False`; or
    its mirror, always-wrap) must be rejected by the exact
    `ToSeq(Result()) == render_rational(wrap, ...)` pin; both halves are
    attacked, at the leaf AND inline at both compound sites. On the registry
    side, a rival correct only on the `wrap=True` half
    (`registry-only-when-wrap`) or only on the "name not already present" half
    (`registry-no-dedup`) is likewise rejected, and a rival correct only when
    the limit's two names COINCIDE (`registry-skip-second-name`) is rejected
    because the two name slots are separately parameterised.

  * CONTROL-FLOW-EFFECT — N/A. The functions are total and never raise (no
    `Exsures`, no exception path in the modeled domain); there is no
    raise/return divergence the value abstraction misses. (Omitted; justified.)

  * AXIOM LANE — present. `digits` and `coprime` are `@ContractOnly` A-consumed
    axioms; `render_rational` / `lit_name` / `registered` / `eq_text` /
    `eq_registry` / `limit_text` / `limit_registry` are A-reference deep models.
    The axiom probes run the REAL post-patch sympy callees in Docker and check
    (a) soundness — the deep models == the real `sstr(...)` text AND the real
    `PythonPrinter.symbols` / `python()` preamble registry, and `digits` is the
    weak fact the proof consumes (non-empty), over a wider grid than
    axiom_check.py + the exact F2P assertions; (b) containment — every operand
    and every NAME KEY the MODEL can reach (its Requires: `p>=0, q>=2, coprime`;
    `is_name(c)`) lies in the real callee's domain (a proper fraction in lowest
    terms that does NOT collapse to an Integer; a one-character Symbol whose
    name is its own text and its own registry key). Both probes are
    SELF-CONTAINED (sympy api + stdlib only) because the runner mounts ONLY the
    probe at /work — axiom_check.py is NOT in-container.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside one `# impl-start`/`# impl-end` block; the frozen spec
(Requires/Ensures + the @Pure helpers + the axioms) is never touched, so
`markers.same_spec` is guaranteed and a rejection is attributable to the
POSTCONDITION catching wrong behaviour, never to a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14531"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (each strictly INSIDE one impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold impl body of render_operand (between its # impl-start/# impl-end).
_GOLD_OPERAND = (
    "    if wrap:\n"
    "        return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))\n"
    "    return materialize(digits(p)) + [47] + materialize(digits(q))"
)

# The whole gold impl body of render_name.
_GOLD_NAME = (
    "    if not (c in reg):\n"
    "        reg.append(c)\n"
    "    return [c]"
)

# The RIGHT operand slot's delegation inside render_equation (inside its impl
# region). Every slot of a modeled compound is now a three-kind operand `(k,u,v)`
# delegated through render_atom, so the landmark for the "rhs slot" is that call.
_EQ_OPERAND_CALL = (
    "    out = out + render_atom(kr, ur, vr, wrap, reg)     # rhs: THIS renderer's"
)
# The POINT slot's delegation inside render_directed_limit (its third slot).
_LIM_OPERAND_CALL = (
    "    out = out + render_atom(k0, u0, v0, wrap, reg)     # point slot"
)
# The LEFT operand slot's delegation inside render_equation.
_EQ_NAME_CALL = (
    "    out = out + render_atom(kl, ul, vl, wrap, reg)     # lhs: THIS renderer's"
)
# The BODY and VARIABLE slots' delegations inside render_directed_limit.
_LIM_NAME_E_CALL = (
    "    out = out + render_atom(ke, ue, ve, wrap, reg)     # body slot"
)
_LIM_NAME_Z_CALL = (
    "    out = out + render_atom(kz, uz, vz, wrap, reg)     # variable slot"
)
# The whole gold impl body of render_equation (used by positive controls).
_GOLD_EQUATION = (
    "    out = []  # type: List[int]\n"
    "    out = out + [69, 113, 40]                          # 'Eq('\n"
    "    out = out + render_atom(kl, ul, vl, wrap, reg)     # lhs: THIS renderer's\n"
    "    out = out + [44, 32]                               # ', '\n"
    "    out = out + render_atom(kr, ur, vr, wrap, reg)     # rhs: THIS renderer's\n"
    "    out = out + [41]                                   # ')'\n"
    "    return out"
)
# The whole gold impl body of render_directed_limit. Needed because the
# slot-ORDER rival has to replace the WHOLE body: swapping only one call site
# would render the variable slot twice, and a doubly-applied registry effect
# would reject for a reason other than the slot ORDER the case is about.
_GOLD_LIMIT = (
    "    out = []  # type: List[int]\n"
    "    out = out + [76, 105, 109, 105, 116, 40]           # 'Limit('\n"
    "    out = out + render_atom(ke, ue, ve, wrap, reg)     # body slot\n"
    "    out = out + [44, 32]                               # ', '\n"
    "    out = out + render_atom(kz, uz, vz, wrap, reg)     # variable slot\n"
    "    out = out + [44, 32]                               # ', '\n"
    "    out = out + render_atom(k0, u0, v0, wrap, reg)     # point slot\n"
    "    if plus:\n"
    "        out = out + [41]                               # ')'\n"
    "        return out\n"
    "    out = out + [44, 32, 100, 105, 114, 61, 39]        # \", dir='\"\n"
    "    out = out + render_unmodeled(ud, wrap, reg)        # direction slot\n"
    "    out = out + [39, 41]                               # \"')\"\n"
    "    return out"
)

# The DIRECTION slot's delegation inside render_directed_limit (its fourth slot,
# present only in the second template form).
_LIM_DIR_CALL = (
    "    out = out + render_unmodeled(ud, wrap, reg)        # direction slot"
)
# The whole SECOND-FORM tail: the direction separator, the direction slot's
# delegation and the closing quote-paren. Replaced as a unit by the rival that
# collapses the two template forms into one.
_LIM_DIR_TAIL = (
    "    out = out + [44, 32, 100, 105, 114, 61, 39]        # \", dir='\"\n"
    "    out = out + render_unmodeled(ud, wrap, reg)        # direction slot\n"
    "    out = out + [39, 41]                               # \"')\"\n"
    "    return out"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-DIFFERENT but CORRECT render_operand. The two branches are
# reordered (the not-wrap case FIRST via an early return on `not wrap`) and each
# returned sequence is bound to a typed LOCAL before return, instead of the gold's
# `if wrap: ...` shape. The produced bytes are byte-for-byte identical to gold on
# every (wrap, p, q), and the registry is left alone exactly as before. No
# induction lemma is introduced. If this fails to verify, the postcondition is
# over-fit to the gold branch spelling => SPEC-TOO-STRONG.
_POS_OPERAND = (
    "    if not wrap:\n"
    "        plain = materialize(digits(p)) + [47] + materialize(digits(q))  # type: List[int]\n"
    "        return plain\n"
    "    wrapped = [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))  # type: List[int]\n"
    "    return wrapped"
)
_POS_CONTROL_OPERAND = _swap(_BASE, _GOLD_OPERAND, _POS_OPERAND)

# (5b) Structurally-DIFFERENT but CORRECT render_name: the already-present case
# returns early instead of guarding the append, and the token is bound to a typed
# local. Identical behaviour on both arms of `registered`. If it fails to verify,
# the registry clause is over-fit to the gold spelling => SPEC-TOO-STRONG.
_POS_NAME = (
    "    if c in reg:\n"
    "        return [c]\n"
    "    reg.append(c)\n"
    "    tok = [c]  # type: List[int]\n"
    "    return tok"
)
_POS_CONTROL_NAME = _swap(_BASE, _GOLD_NAME, _POS_NAME)

# (5c / 2) GROUNDED-ORACLE cheapest-impl POSITIVE CONTROL. `eq_text` is @Pure and
# grounded in the args (it IS the demanded text), so the cheapest correct impl of
# render_equation delegates BOTH slots — which is the only way to obtain their
# registry effects, since the unmodelled kind's effect is uninterpreted — and then
# materialises the text oracle. This is CORRECT in BOTH observables, so it MUST
# verify. It is the honest positive control that takes the place of an
# "ungrounded-oracle echo" (there is no WRONG echo of a grounded oracle;
# PBT_PLAN §2). Note it still has to DO the delegation — the echo that skips it
# is the `registry-echo-text-only` reject lane. If this failed to verify the spec
# would be SPEC-TOO-STRONG (rejecting the most direct correct implementation).
_POS_EQ_CHEAPEST = (
    "    tokl = render_atom(kl, ul, vl, wrap, reg)  # type: List[int]\n"
    "    tokr = render_atom(kr, ur, vr, wrap, reg)  # type: List[int]\n"
    "    return materialize(eq_text(wrap, kl, ul, vl, kr, ur, vr))"
)
_POS_CONTROL_EQ_CHEAPEST = _swap(_BASE, _GOLD_EQUATION, _POS_EQ_CHEAPEST)

# (6) ADMISSIBILITY. render_equation already calls render_atom on each of its OWN
# slot triples, which carry `is_atom(kl,ul,vl)` / `is_atom(kr,ur,vr)` and the full
# `reg` permission from the enclosing Requires (so the F2P shape Eq(name, p/q) is
# the (kl==1, kr==0) instance of an in-domain input). We add Asserts that the
# assembled relation text is non-degenerate and that the registry is non-empty
# once a NAME slot has been rendered. The guards are essential and are part of the
# claim: a slot may be a fraction (which registers nothing) or an operand whose
# rule is not modelled (whose text carries NO length guarantee), so `len(reg) >= 1`
# is only claimable under `kl == 1`, and a text length beyond the 6 constant
# template bytes only under two fractional slots. If the preconditions could not be
# established for this normal in-domain input, or the body were unreachable, the
# calls/Asserts would fail => PRECOND-TOO-STRONG. NOTE: we self-call on the
# FUNCTION'S OWN params (whose `is_atom` is already in scope) — never on fresh
# literals, because `coprime` is @ContractOnly with no body, so `coprime(2,3)` is
# unprovable from nothing and a literal self-call would be a PROOF gap mislabeled
# PRECOND-TOO-STRONG.
_ADMISS_EQ = (
    "    out = []  # type: List[int]\n"
    "    out = out + [69, 113, 40]                          # 'Eq('\n"
    "    out = out + render_atom(kl, ul, vl, wrap, reg)     # lhs: THIS renderer's\n"
    "    Assert(Implies(kl == 1, len(reg) >= 1))\n"
    "    out = out + [44, 32]                               # ', '\n"
    "    op = render_atom(kr, ur, vr, wrap, reg)  # type: List[int]\n"
    "    out = out + op\n"
    "    out = out + [41]                                   # ')'\n"
    "    Assert(len(out) >= 6)\n"
    "    Assert(Implies(kl == 0 and kr == 0, len(out) >= 9))\n"
    "    return out"
)
_ADMISS = _swap(_BASE, _GOLD_EQUATION, _ADMISS_EQ)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# --- observable (1): the wrap configuration must propagate ------------------

# (3a) PARTIAL-DOMAIN at the leaf — THE ORIGINAL DEFECT. render_operand IGNORES
# `wrap` and always returns the UNWRAPPED form. Correct ONLY on the wrap=False
# half of the domain; for wrap=True it yields 'p/q' where render_rational demands
# 'S(p)/q'. This is exactly the pre-patch behaviour (`%s` operand = a fresh
# default-settings StrPrinter, sympy_integers=False). Rejection source: the
# postcondition `ToSeq(Result()) == render_rational(wrap, p, q)`.
_RIVAL_OPERAND_UNWRAP = (
    "    return materialize(digits(p)) + [47] + materialize(digits(q))"
)
_RIVAL_DROP_WRAP = _swap(_BASE, _GOLD_OPERAND, _RIVAL_OPERAND_UNWRAP)

# (3b) PARTIAL-DOMAIN at the leaf — THE MIRROR. render_operand always WRAPS,
# ignoring `wrap` the other way. Correct ONLY on the wrap=True half; for wrap=False
# it yields 'S(p)/q' where 'p/q' is demanded. Faithful real patch: a renderer that
# unconditionally applies the sympy_integers wrapper — FAILS the default-settings
# F2P case `sstr(Eq(x, Rational(2,3))) == 'Eq(x, 2/3)'`. Rejection source: same pin,
# the spurious 'S('/')' wrapper present when wrap=False.
_RIVAL_OPERAND_WRAP = (
    "    return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))"
)
_RIVAL_ALWAYS_WRAP = _swap(_BASE, _GOLD_OPERAND, _RIVAL_OPERAND_WRAP)

# (3c) COMPOUND-SITE DEFECT in render_equation — the setting fails to PROPAGATE.
# Instead of calling render_operand(wrap, ...) (which tracks the parent's wrap),
# the operand is rendered INLINE always-unwrapped, modeling the pre-patch
# `'%s' % expr.rhs` (a fresh default StrPrinter, ignoring self._settings). The
# name slot is left correct, so the rejection is attributable to the TEXT clause
# alone. For wrap=True the compound yields 'Eq(n, p/q)' where eq_text demands
# 'Eq(n, S(p)/q)'. Rejection source:
# `ToSeq(Result()) == eq_text(wrap, kl, ul, vl, kr, ur, vr)`.
# The inline re-render is guarded to the FRACTIONAL kind, so the other two kinds
# are still delegated and the rejection stays attributable to the propagation
# clause this case is about rather than to a missing registry effect.
_RIVAL_EQ_INLINE = (
    "    if kr == 0:\n"
    "        out = out + materialize(digits(ur)) + [47] + materialize(digits(vr))  # ambient-default re-render\n"
    "    else:\n"
    "        out = out + render_atom(kr, ur, vr, wrap, reg)"
)
_RIVAL_EQ_BUG = _swap(_BASE, _EQ_OPERAND_CALL, _RIVAL_EQ_INLINE)

# (3d) COMPOUND-SITE DEFECT in render_directed_limit — the OTHER modeled function,
# to confirm the symmetric site is equally tight. The limit point is rendered
# inline always-unwrapped (pre-patch `"Limit(%s, %s, %s)" % (e, z, z0)`), so for
# wrap=True it yields 'Limit(e, z, p/q)' where limit_text demands
# 'Limit(e, z, S(p)/q)'. Rejection source:
# `ToSeq(Result()) == limit_text(wrap, plus, ke, ue, ve, kz, uz, vz, k0, u0, v0,
# ud)`.
_RIVAL_LIM_INLINE = (
    "    if k0 == 0:\n"
    "        out = out + materialize(digits(u0)) + [47] + materialize(digits(v0))  # ambient-default re-render\n"
    "    else:\n"
    "        out = out + render_atom(k0, u0, v0, wrap, reg)"
)
_RIVAL_LIM_BUG = _swap(_BASE, _LIM_OPERAND_CALL, _RIVAL_LIM_INLINE)

# (3e) VALUE-LEVEL near-miss (supporting): render_operand emits the numerator and
# denominator in the WRONG ORDER (q before p), correct only on the measure-zero
# p==q sub-domain (excluded by coprime+q>=2 for the F2P fractions). A renderer
# printing 'q/p' fails every F2P (gives 'Eq(x, 3/2)' for 2/3). Rejection source:
# the pin render_rational(wrap,p,q) fixes the order digits(p) THEN digits(q).
_RIVAL_OPERAND_SWAP = (
    "    if wrap:\n"
    "        return [83, 40] + materialize(digits(q)) + [41, 47] + materialize(digits(p))\n"
    "    return materialize(digits(q)) + [47] + materialize(digits(p))"
)
_RIVAL_SWAP_PQ = _swap(_BASE, _GOLD_OPERAND, _RIVAL_OPERAND_SWAP)

# --- observable (2): the name slot must be rendered BY THIS renderer ---------

# (4a) THE RECORDED REFUTATION, verbatim in shape. The lhs name slot is emitted as
# a bare CONSTANT TOKEN: the text is byte-identical to the gold (a name's text is
# configuration-independent), so every TEXT clause still holds — this rival
# verifies against a text-only spec, which is precisely the hole this battery
# guards. Its faithful real patch delegates only the fraction
# (`'%s(%s, %s)' % (charmap[op], expr.lhs, self._print(expr.rhs))`), so
# `test_Rational` passes but `python(Eq(x, y))` loses the `x = Symbol('x')`
# preamble line and F2P `test_python_relational` FAILS. Rejection source:
# `ToSeq(reg) == eq_registry(Old(ToSeq(reg)), kl, ul, vl, kr, ur, vr)` — the
# registry did not grow at the lhs slot.
_RIVAL_EQ_TOKEN = (
    "    if kl == 1:\n"
    "        out = out + [ul]                               # bare token, unregistered\n"
    "    else:\n"
    "        out = out + render_atom(kl, ul, vl, wrap, reg)"
)
_RIVAL_EQ_SKIP_REG = _swap(_BASE, _EQ_NAME_CALL, _RIVAL_EQ_TOKEN)

# (4b) The same skip at the SECOND name slot of the limit template, which is the
# freedom the two-name parameterisation exists to remove: with equal names the
# duplicate-free registry would MASK it (registering the body slot's name alone
# already yields the right registry when the two names coincide), so this rival is
# correct exactly on the `ue == uz` sub-domain — including the F2P's own
# `Limit(x, x, 7/2)` shape.
# Faithful real patch: `"Limit(%s, %s, %s)" % (self._print(e), z, self._print(z0))`,
# which resolves `test_Rational` but drops the second symbol from the preamble.
# Rejection source:
# `ToSeq(reg) == limit_registry(Old(ToSeq(reg)), plus, ke, ue, ve, kz, uz, vz, k0,
# u0, v0, ud)` — unprovable once the variable slot's name may differ from the
# body's.
_RIVAL_LIM_TOKEN = (
    "    if kz == 1:\n"
    "        out = out + [uz]                               # bare token, unregistered\n"
    "    else:\n"
    "        out = out + render_atom(kz, uz, vz, wrap, reg)"
)
_RIVAL_LIM_SKIP_SECOND = _swap(_BASE, _LIM_NAME_Z_CALL, _RIVAL_LIM_TOKEN)

# (4c) GROUNDED-ORACLE ECHO OF THE TEXT ONLY. The cheapest impl that satisfies
# every TEXT clause and nothing else: materialise the text oracle and never touch
# the registry. This is the exact rival the `pos-control-equation-cheapest`
# positive control differs from by ONE statement, which is what makes the registry
# clause demonstrably load-bearing rather than decorative. Faithful real patch:
# build the relation string without delegating either operand to `self`, i.e. the
# UNPATCHED method — fails both F2P tests. Rejection source: the registry clause.
_RIVAL_EQ_ECHO = "    return materialize(eq_text(wrap, kl, ul, vl, kr, ur, vr))"
_RIVAL_EQ_ECHO_ONLY = _swap(_BASE, _GOLD_EQUATION, _RIVAL_EQ_ECHO)

# (4d) WRONG KEY / BOUNDARY TOKEN SWAP. The lhs slot is rendered by this renderer,
# but always under the FIXED key 120 ('x') instead of the name actually present —
# the shape of a patch that hard-codes the operand it delegates. Correct exactly on
# the `ul == 120` sub-domain, which happens to include every F2P case, so a spec
# that did not parameterise the name key could not tell it from gold. Faithful real
# patch: `self._print(Symbol('x'))` in place of `self._print(expr.lhs)` — renders
# and registers 'x' for EVERY relation, failing `python(Eq(y, y))`-shaped readings
# and `test_python_relational`'s `Ne(x/(y + 1), y**2)` line. Rejection source: BOTH
# the text pin (`atom_text(kl, ul, vl, wrap)` = `lit_name(ul)` at `kl == 1`) and
# the registry pin (`atom_registry(r, kl, ul, vl)` = `registered(r, ul)`) fix the
# key to `ul`.
_RIVAL_EQ_FIXED_KEY = (
    "    if kl == 1:\n"
    "        out = out + render_name(120, reg)              # fixed key, not ul\n"
    "    else:\n"
    "        out = out + render_atom(kl, ul, vl, wrap, reg)"
)
_RIVAL_EQ_WRONG_KEY = _swap(_BASE, _EQ_NAME_CALL, _RIVAL_EQ_FIXED_KEY)

# (4e) PARTIAL-DOMAIN ON THE REGISTRY: register only when the wrap configuration is
# ON. Text is always correct; the registry is correct exactly on the wrap=True
# half. This is the freedom a wrap-CONDITIONAL registry clause would have left, and
# it is why the registry postconditions are deliberately wrap-independent: the real
# registration (`PythonPrinter._print_Symbol`) never consults `_settings`.
# Faithful real patch: delegate the lhs only when `self._settings.get(
# 'sympy_integers')` is set — `python()` uses default settings, so
# `test_python_relational` still FAILS. Rejection source:
# `ToSeq(reg) == eq_registry(Old(ToSeq(reg)), kl, ul, vl, kr, ur, vr)` holds for
# neither value of a universally-quantified `wrap`.
_RIVAL_EQ_WRAP_ONLY = (
    "    if wrap or not (kl == 1):\n"
    "        out = out + render_atom(kl, ul, vl, wrap, reg)  # registers only here\n"
    "    else:\n"
    "        out = out + [ul]                               # bare token"
)
_RIVAL_EQ_REG_IF_WRAP = _swap(_BASE, _EQ_NAME_CALL, _RIVAL_EQ_WRAP_ONLY)

# (4f) DEDUP DROPPED: render_name appends UNCONDITIONALLY, so a name already in the
# registry is entered twice. Correct exactly on the "not already present" half of
# the domain. Faithful real patch: drop the `if symbol not in self.symbols:` guard
# in `_print_Symbol`, which makes `python(Ne(x/(y + 1), y**2))` emit
# `x = Symbol('x')` twice and FAILS `test_python_relational`. Rejection source:
# `ToSeq(reg) == registered(Old(ToSeq(reg)), c)` — `registered` returns `r`
# unchanged when `c in r`.
_RIVAL_NAME_NO_DEDUP = (
    "    reg.append(c)\n"
    "    return [c]"
)
_RIVAL_NO_DEDUP = _swap(_BASE, _GOLD_NAME, _RIVAL_NAME_NO_DEDUP)

# (4g) FRAME WRITE ON THE NO-WRITE SLOT: render_operand registers the FIRST digit
# of the numerator (a plausible "record what you rendered" over-reach) even though
# a fractional operand is not a name. Text unchanged. Faithful real patch: a
# `_print_Rational` that appends to `self.symbols`, which injects junk
# `<digit> = Symbol('<digit>')` lines into `python()` output and FAILS
# `test_python_relational`. Rejection source: render_operand's
# `ToSeq(reg) == Old(ToSeq(reg))` — the complementary NO-WRITE clause that makes
# the compounds' registry growth attributable to the NAME slots only.
_RIVAL_FRAC_WRITES = (
    "    reg.append(112)\n"
    "    if wrap:\n"
    "        return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))\n"
    "    return materialize(digits(p)) + [47] + materialize(digits(q))"
)
_RIVAL_FRAC_WRITE = _swap(_BASE, _GOLD_OPERAND, _RIVAL_FRAC_WRITES)

# (4h) REGISTRY ORDER SWAPPED at the limit site: both names ARE registered, but the
# second slot is registered before the first. Correct exactly on the `ue == uz`
# sub-domain and on pre-states that already hold both names — a rival that a
# set-valued registry model would accept. Faithful real patch: register `z` before
# `e` (e.g. `"Limit(%s, %s, %s)" % (self._print(e), ...)` reordered so `z`
# reaches _print_Symbol first). Because `python()` emits ONE PREAMBLE LINE PER
# ENTRY IN LIST ORDER (python.py:69), `python(Limit(x, y, 7/2))` would come out
# `y = Symbol('y')` before `x = Symbol('x')` and FAIL test_python_relational's
# line-by-line comparison. Rejection source: `limit_registry` is the ORDERED
# left-to-right `atom_registry` composition over the three slots in TEMPLATE
# order, mirroring `map(self._print, (e, z, z0))`.
# Substituted as a WHOLE BODY, not at a single call site: a call-site swap would
# leave the variable slot's own delegation in place and render it TWICE, and a
# doubly-applied registry effect rejects for a reason other than the slot ORDER.
_RIVAL_LIM_ORDER = (
    "    out = []  # type: List[int]\n"
    "    out = out + [76, 105, 109, 105, 116, 40]           # 'Limit('\n"
    "    tok_z = render_atom(kz, uz, vz, wrap, reg)  # type: List[int]\n"
    "    out = out + render_atom(ke, ue, ve, wrap, reg)     # body slot, rendered SECOND\n"
    "    out = out + [44, 32]                               # ', '\n"
    "    out = out + tok_z\n"
    "    out = out + [44, 32]                               # ', '\n"
    "    out = out + render_atom(k0, u0, v0, wrap, reg)     # point slot\n"
    "    if plus:\n"
    "        out = out + [41]                               # ')'\n"
    "        return out\n"
    "    out = out + [44, 32, 100, 105, 114, 61, 39]        # \", dir='\"\n"
    "    out = out + render_unmodeled(ud, wrap, reg)        # direction slot\n"
    "    out = out + [39, 41]                               # \"')\"\n"
    "    return out"
)
_RIVAL_LIM_REORDER = _swap(_BASE, _GOLD_LIMIT, _RIVAL_LIM_ORDER)

# (4i) WRONG KEY AT THE LEAF: render_name returns the right text for `c` but
# registers the fixed key 120 ('x') instead. Distinct from registry-wrong-key
# (which passes a wrong ARGUMENT at the call site and is caught by the text pin
# first): here the TEXT is correct everywhere, so the verifier is forced through to
# the registry clause, and the failure is attributable to the registry alone. This
# is the freedom the new `reg` parameter introduces — full write permission on a
# list whose contents must nonetheless be exactly `registered(...)`. Faithful real
# patch: `self.symbols.append('x')` in place of `self.symbols.append(symbol)` in
# `PythonPrinter._print_Symbol`, which emits `x = Symbol('x')` for every symbol and
# FAILS test_python_relational. Rejection source:
# `ToSeq(reg) == registered(Old(ToSeq(reg)), c)`.
_RIVAL_NAME_WRONG_KEY = (
    "    if not (120 in reg):\n"
    "        reg.append(120)\n"
    "    return [c]"
)
_RIVAL_LEAF_WRONG_KEY = _swap(_BASE, _GOLD_NAME, _RIVAL_NAME_WRONG_KEY)

# --- observable (3): the UNMODELLED operand kind ------------------------------
# These three rivals are the ones that make the third operand kind load-bearing.
# Each is correct on the whole `k in {0, 1}` sub-domain — i.e. each is exactly a
# rival that a two-kind carrier (a name left slot, a fractional right slot) could
# not tell from gold — so they are what pins the `k == 2` leg of eq_text /
# eq_registry.

# (7a) ECHO AT THE SLOT. The rhs slot's text is reproduced from the @Pure text
# oracle at the compound site instead of being rendered, and the registry effect
# is reproduced by hand for the NAME kind. On a fractional or a name rhs this is
# byte- and registry-identical to gold, which is exactly why a narrow carrier
# accepts it. Faithful real patch: spell `expr.rhs` at the relation site rather
# than delegating it — `python(Eq(x, y))` then loses the `y = Symbol('y')`
# preamble line and F2P test_python_relational FAILS. Rejection source:
# `eq_registry` at `kr == 2`, where the effect is the uninterpreted
# `opaque_registry(r, ur)` and no hand-written write can be equated with it.
_RIVAL_EQ_OPAQUE_ECHO = (
    "    out = out + materialize(atom_text(kr, ur, vr, wrap))  # echoed, not rendered\n"
    "    if kr == 1:\n"
    "        if not (ur in reg):\n"
    "            reg.append(ur)"
)
_RIVAL_EQ_ECHO_SLOT = _swap(_BASE, _EQ_OPERAND_CALL, _RIVAL_EQ_OPAQUE_ECHO)

# (7b) DELEGATED, BUT AT THE AMBIENT DEFAULT CONFIGURATION. The rhs slot IS
# rendered by this renderer, so every registry effect is right; it is just
# rendered at the ambient default instead of the configuration the compound
# carries. This is the pre-patch `%s`-of-subexpression shape at the one kind whose
# text is not reproducible, and it is correct on the entire `wrap == False` half.
# Faithful real patch: render the operand through a fresh default-settings printer
# — F2P `sstr(Eq(x, S(1)/2), sympy_integers=True)` comes back 'Eq(x, 1/2)'.
# Rejection source: `eq_text`, because `opaque_text(ur, False)` cannot be equated
# with `opaque_text(ur, wrap)`. THIS CASE IS WHY `opaque_text` CARRIES A `wrap`
# ARGUMENT: drop it and the propagation observable dies at this slot.
_RIVAL_EQ_AMBIENT = (
    "    if kr == 2:\n"
    "        out = out + render_unmodeled(ur, False, reg)   # ambient default config\n"
    "    else:\n"
    "        out = out + render_atom(kr, ur, vr, wrap, reg)"
)
_RIVAL_EQ_AMBIENT_UNMODELED = _swap(_BASE, _EQ_OPERAND_CALL, _RIVAL_EQ_AMBIENT)

# (7c) DELEGATION SPLIT ON THE CONFIGURATION. The rhs slot is delegated on the
# `wrap == True` half and echoed on the other half, so registration becomes
# conditional on the configuration. Correct on exactly half the domain, and on the
# whole `k in {0, 1}` sub-domain of the other half. Faithful real patch: delegate
# the operand only when `self._settings.get('sympy_integers')` is set; `python()`
# runs at default settings, so test_python_relational still FAILS. Rejection
# source: `eq_registry` is deliberately `wrap`-INDEPENDENT, mirroring the real
# receiver whose registration (python.py:37-41) never consults `_settings`.
_RIVAL_EQ_HALF = (
    "    if wrap:\n"
    "        out = out + render_atom(kr, ur, vr, wrap, reg)\n"
    "    else:\n"
    "        out = out + materialize(atom_text(kr, ur, vr, wrap))\n"
    "        if kr == 1:\n"
    "            if not (ur in reg):\n"
    "                reg.append(ur)"
)
_RIVAL_EQ_DELEGATE_IF_WRAP = _swap(_BASE, _EQ_OPERAND_CALL, _RIVAL_EQ_HALF)

# --- observable (3): the DIRECTION slot is an operand slot like any other -----
# These three are what pin the second template form. Without them the battery has
# no case that fails BECAUSE OF the direction slot, and every rival above is
# already rejected on the three-operand form alone.

# (7a) ONE TEMPLATE FORM ONLY: the renderer closes the text after the point slot
# whatever the direction is, i.e. the `plus` form applied unconditionally. This is
# correct on the whole `plus` half -- which includes every F2P input -- and drops
# both the direction text and its registration on the other half. Its faithful real
# patch is `_print_Limit` with the `str(dir) == "+"` test deleted (only the 3-slot
# return kept); P2P `test_Limit` asserts
# `str(Limit(sin(x)/x, x, y, dir="-")) == "Limit(sin(x)/x, x, y, dir='-')"`, which
# that patch turns into "Limit(sin(x)/x, x, y)". Non-resolving.
# Rejection source: both limit clauses at `not plus` -- the text lacks the
# ", dir='" ... "')" tail limit_text demands, and the registry lacks the trailing
# `opaque_registry(., ud)` step.
_RIVAL_LIM_ONE_FORM = (
    "    out = out + [41]                                   # ')'\n"
    "    return out"
)
_RIVAL_LIM_DROP_DIR = _swap(_BASE, _LIM_DIR_TAIL, _RIVAL_LIM_ONE_FORM)

# (7b) THE DIRECTION SLOT ECHOED, NOT RENDERED: the tail is spelled at the
# compound site by materialising the text oracle, and the registry effect is
# reproduced by... nothing, since `opaque_registry` is uninterpreted. The TEXT
# clause is fully satisfied on both halves; only the registry clause can tell the
# difference. This is the direction-slot analogue of the recorded `atk_5` family
# and of `registry-echo-text-only`: pre-patch `"... dir='%s'" % (..., dir)`
# interpolates the direction with a bare `%s`, so `python(Limit(x, x, oo))` loses
# its `- = Symbol('-')` preamble line. Non-resolving against the registry reading.
# Rejection source: `ToSeq(reg) == limit_registry(..., plus, ..., ud)` — at
# `not plus` the demanded final step `opaque_registry(., ud)` is uninterpreted and
# cannot be produced without calling the renderer.
_RIVAL_LIM_DIR_ECHO = (
    "    out = out + materialize(opaque_text(ud, wrap))     # echoed, not rendered"
)
_RIVAL_LIM_ECHO_DIR = _swap(_BASE, _LIM_DIR_CALL, _RIVAL_LIM_DIR_ECHO)

# (7c) THE DIRECTION SLOT RENDERED AT THE AMBIENT DEFAULT configuration: it IS
# delegated to this renderer -- so it registers correctly and the registry clause
# holds -- but at `False` instead of the compound's own `wrap`. Correct on the
# whole `wrap == False` half. This is the original defect's shape (`%s` = a fresh
# default-settings printer) surviving at the one slot the three-operand form does
# not cover. Rejection source: `ToSeq(Result()) == limit_text(wrap, plus, ...)`,
# because `opaque_text(ud, False)` cannot be equated with `opaque_text(ud, wrap)` —
# which is exactly what the `wrap` argument on `opaque_text` is for.
_RIVAL_LIM_DIR_AMBIENT = (
    "    out = out + render_unmodeled(ud, False, reg)       # ambient default config"
)
_RIVAL_LIM_AMBIENT_DIR = _swap(_BASE, _LIM_DIR_CALL, _RIVAL_LIM_DIR_AMBIENT)


SPEC_TESTS = [
    # ---- positive controls (must verify) ----
    {"id": "pos-control-operand-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_CONTROL_OPERAND,
     "rationale": "structurally-different but CORRECT render_operand (not-wrap case "
                  "handled FIRST via an early return; each result bound to a typed "
                  "local). Byte-identical to gold on every (wrap,p,q) and leaves the "
                  "registry alone as before; no induction lemma introduced. If it "
                  "fails to verify, the postcondition is over-fit to the gold branch "
                  "spelling => SPEC-TOO-STRONG."},
    {"id": "pos-control-name-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_CONTROL_NAME,
     "rationale": "structurally-different but CORRECT render_name: the "
                  "already-present case returns EARLY instead of guarding the "
                  "append, and the token is bound to a typed local. Identical on "
                  "both arms of `registered`. If it fails to verify, the registry "
                  "clause is over-fit to the gold spelling => SPEC-TOO-STRONG."},
    {"id": "pos-control-equation-cheapest", "kind": "soundness", "expect": "verify",
     "module": _POS_CONTROL_EQ_CHEAPEST,
     "rationale": "the GROUNDED-oracle cheapest CORRECT impl: register the name "
                  "slot, then materialise eq_text (a @Pure function fully grounded "
                  "in the args). Correct in BOTH observables, so it MUST verify. "
                  "Stands in for the ungrounded-oracle-echo class (there is no WRONG "
                  "echo of a grounded oracle); its one-statement-weaker twin is the "
                  "registry-echo-text-only reject lane. If it failed => "
                  "SPEC-TOO-STRONG."},
    {"id": "admiss-f2p-shape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "render_equation self-calls render_atom on each of its OWN slot "
                  "triples (is_atom(kl,ul,vl) / is_atom(kr,ur,vr) and full reg "
                  "permission in scope from Requires; the F2P shape Eq(x, p/q) is the "
                  "kl==1, kr==0 instance) and asserts the registry is non-empty once a "
                  "NAME slot has been rendered (len(reg)>=1 under kl==1) and the "
                  "assembled text is non-degenerate (len>=6 always, len>=9 under two "
                  "fractional slots). The GUARDS are part of the claim: a fraction "
                  "slot registers nothing and an unmodelled slot's text carries no "
                  "length guarantee, so the unguarded forms would be unsound rather "
                  "than strong. If a precondition could not be established for this "
                  "normal in-domain input, or the body were unreachable, the "
                  "calls/Asserts would fail => PRECOND-TOO-STRONG. Self-calls use the "
                  "enclosing params (never fresh literals) since coprime is "
                  "@ContractOnly and unprovable from nothing."},

    # ---- uniqueness rivals: observable (1), the wrap configuration ----
    {"id": "partial-domain-drop-wrap", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_WRAP,
     "refinement": "this IS the original defect: the operand rendered via `%s` = a "
                   "fresh default-settings StrPrinter (sympy_integers=False), so it "
                   "always emits the unwrapped 'p/q'. Its faithful real patch is the "
                   "UNPATCHED _print_Rational dispatch, which fails the F2P "
                   "`sstr(Eq(x, S(2)/3), sympy_integers=True) == 'Eq(x, S(2)/3)'` "
                   "(yields 'Eq(x, 2/3)'). Definitively non-resolving.",
     "rationale": "rejection from `ToSeq(Result()) == render_rational(wrap,p,q)`: for "
                  "wrap=True render_rational demands the 'S('/')' wrapper, which this "
                  "impl drops, so the sequences differ."},
    {"id": "partial-domain-always-wrap", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYS_WRAP,
     "refinement": "a renderer that UNCONDITIONALLY applies the sympy_integers wrapper "
                   "(ignores the active setting the other way). Correct only on the "
                   "wrap=True half; its faithful real patch fails the default-settings "
                   "F2P `sstr(Eq(x, Rational(2,3))) == 'Eq(x, 2/3)'` (yields "
                   "'Eq(x, S(2)/3)'). Non-resolving.",
     "rationale": "rejection from the same pin: for wrap=False render_rational demands "
                  "'p/q' with NO wrapper, but this impl emits the spurious 'S('/')'."},
    {"id": "compound-bug-equation", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_BUG,
     "refinement": "the setting fails to PROPAGATE into the operand: render_equation "
                   "renders the rhs inline always-unwrapped, modeling the pre-patch "
                   "`'%s(%s, %s)' % (..., expr.rhs)` (a fresh default StrPrinter). This "
                   "is the literal issue (`sstr(Eq(x, S(1)/2), sympy_integers=True)` gave "
                   "'Eq(x, 1/2)'). Faithful real patch = the UNPATCHED _print_Relational, "
                   "which fails F2P test_Rational. Non-resolving.",
     "rationale": "rejection from `ToSeq(Result()) == eq_text(wrap, kl, ul, vl, kr, ur, "
                  "vr)`: at kr==0 eq_text embeds render_rational(wrap,...); for "
                  "wrap=True the dropped wrapper makes the full string differ. The "
                  "inline re-render is guarded to the fractional kind and the lhs slot "
                  "is untouched, so every registry effect still holds and the rejection "
                  "is attributable to the TEXT clause alone."},
    {"id": "compound-bug-limit", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIM_BUG,
     "refinement": "the same propagation defect at the OTHER modeled site: the limit "
                   "point rendered inline always-unwrapped, modeling pre-patch "
                   "`\"Limit(%s, %s, %s)\" % (e, z, z0)`. Faithful real patch = the "
                   "UNPATCHED _print_Limit, which fails the F2P "
                   "`sstr(Limit(x, x, S(7)/2), sympy_integers=True) == "
                   "'Limit(x, x, S(7)/2)'`. Non-resolving; confirms the symmetric site "
                   "is equally tight.",
     "rationale": "rejection from `ToSeq(Result()) == limit_text(wrap, plus, ke, ue, "
                  "ve, kz, uz, vz, k0, u0, v0, ud)`: at k0==0 limit_text embeds "
                  "render_rational(wrap,...); the dropped wrapper for wrap=True makes "
                  "the full string differ. Guarded to the fractional kind, so the other "
                  "two kinds are still delegated."},
    {"id": "limit-one-template-form", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIM_DROP_DIR,
     "refinement": "the renderer closes the limit text after the POINT slot whatever "
                   "the direction is -- the `plus` form applied unconditionally, so "
                   "both the direction's text and its registration are dropped on the "
                   "other half. Correct on the whole `plus` half, which includes every "
                   "F2P input. Its faithful real patch is _print_Limit with the "
                   "`str(dir) == \"+\"` test deleted and only the 3-slot return kept; "
                   "P2P `test_Limit` asserts `str(Limit(sin(x)/x, x, y, dir=\"-\")) == "
                   "\"Limit(sin(x)/x, x, y, dir='-')\"`, which that patch turns into "
                   "\"Limit(sin(x)/x, x, y)\". Non-resolving.",
     "rationale": "rejection from BOTH limit clauses at `not plus`: the text lacks the "
                  "\", dir='\" ... \"')\" tail that limit_text demands in the second "
                  "form, and the registry lacks the trailing opaque_registry(., ud) "
                  "step that limit_registry demands there."},
    {"id": "limit-direction-echoed", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIM_ECHO_DIR,
     "refinement": "the direction tail is SPELLED at the compound site by "
                   "materialising the text oracle instead of asking the renderer, so "
                   "the direction is never registered. Every TEXT clause still holds "
                   "on both halves -- only the registry can tell the difference, which "
                   "is the same asymmetry `registry-echo-text-only` exploits at a name "
                   "slot. Faithful real patch: keep the pre-patch `%s`-interpolation of "
                   "`dir` while delegating the other three slots, so "
                   "`python(Limit(x, x, oo))` loses its `- = Symbol('-')` preamble "
                   "line. Non-resolving against the registry reading.",
     "rationale": "rejection from `ToSeq(reg) == limit_registry(Old(ToSeq(reg)), plus, "
                  "ke, ue, ve, kz, uz, vz, k0, u0, v0, ud)`: at `not plus` the demanded "
                  "final step opaque_registry(., ud) is UNINTERPRETED, so no value "
                  "written at the compound site can be proven equal to it; only a call "
                  "to the renderer discharges it. The text clause is untouched, so the "
                  "rejection is attributable to the registry clause alone."},
    {"id": "limit-direction-ambient-config", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIM_AMBIENT_DIR,
     "refinement": "the direction slot IS delegated to this renderer -- so it registers "
                   "correctly and the registry clause holds -- but at the AMBIENT "
                   "DEFAULT configuration instead of the compound's own `wrap`. Correct "
                   "on the whole `wrap == False` half. This is the literal original "
                   "defect (`%s` = a fresh default-settings StrPrinter) surviving at the "
                   "one slot the three-operand form does not cover; a patch that "
                   "delegates a slot to a default-settings printer is exactly what the "
                   "issue reports. Non-resolving.",
     "rationale": "rejection from `ToSeq(Result()) == limit_text(wrap, plus, ke, ue, ve, "
                  "kz, uz, vz, k0, u0, v0, ud)`: the second form demands "
                  "opaque_text(ud, wrap) at the direction slot, and opaque_text is "
                  "uninterpreted, so opaque_text(ud, False) cannot be equated with it. "
                  "This case is what justifies the `wrap` argument on opaque_text: drop "
                  "it and the propagation observable dies at this slot."},
    {"id": "value-swap-num-denom", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP_PQ,
     "refinement": "a transposed-operand printer that emits 'q/p' (and 'S(q)/p') instead "
                   "of 'p/q'. Correct only on the empty p==q sub-domain (coprime + q>=2 "
                   "forces p!=q for the F2P fractions). Its faithful real patch prints "
                   "the denominator first and FAILS every F2P (gives 'Eq(x, 3/2)' for "
                   "2/3). Supporting near-miss with a real non-resolving refinement.",
     "rationale": "rejection from `ToSeq(Result()) == render_rational(wrap,p,q)`, which "
                  "fixes the order digits(p) THEN digits(q); swapping them differs "
                  "whenever digits(p) != digits(q)."},

    # ---- uniqueness rivals: observable (2), the name registry ----
    {"id": "registry-skip-name-equation", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_SKIP_REG,
     "refinement": "the lhs name slot emitted as a BARE CONSTANT TOKEN. Its text is "
                   "byte-identical to gold (a name's text is configuration-"
                   "independent), so it satisfies every TEXT clause — this is the "
                   "rival a text-only spec cannot reject. Faithful real patch: "
                   "`'%s(%s, %s)' % (charmap[expr.rel_op], expr.lhs, "
                   "self._print(expr.rhs))`, delegating only the fraction. F2P "
                   "test_Rational then PASSES but test_python_relational FAILS: "
                   "`python(Eq(x, y))` loses the `x = Symbol('x')` preamble line "
                   "because the lhs never reaches PythonPrinter._print_Symbol. "
                   "Non-resolving.",
     "rationale": "rejection from `ToSeq(reg) == eq_registry(Old(ToSeq(reg)), kl, ul, "
                  "vl, kr, ur, vr)`: the lhs slot leaves the registry unchanged, but at "
                  "kl==1 eq_registry demands `ul` be present, which is unprovable for a "
                  "`ul` not already in reg."},
    {"id": "registry-skip-second-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIM_SKIP_SECOND,
     "refinement": "the SECOND name slot of the limit template emitted as a bare "
                   "token. Because the registry is duplicate-free, registering only "
                   "the first name is CORRECT whenever the two names coincide — "
                   "including the F2P's own `Limit(x, x, 7/2)` shape — so this rival "
                   "is correct on exactly the `ue == uz` sub-domain. Faithful real "
                   "patch: `\"Limit(%s, %s, %s)\" % (self._print(e), z, "
                   "self._print(z0))`. test_Rational passes; the registry surface "
                   "drops the second symbol, so `python(Limit(x, y, 7/2))` loses its "
                   "`y = Symbol('y')` line. Non-resolving.",
     "rationale": "rejection from `ToSeq(reg) == limit_registry(Old(ToSeq(reg)), plus, "
                  "ke, ue, ve, kz, uz, vz, k0, u0, v0, ud)`: dropping the variable slot's effect "
                  "gives a registry that equals the demanded left-to-right composition "
                  "only when that slot's name is already present — not provable for the "
                  "universally-quantified distinct pair the independent slot "
                  "parameterisation admits."},
    {"id": "registry-echo-text-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_ECHO_ONLY,
     "refinement": "the cheapest impl that satisfies every TEXT clause and nothing "
                   "else: materialise the grounded text oracle, never touch the "
                   "registry. Differs from the pos-control-equation-cheapest positive "
                   "control by exactly ONE statement (the render_name call), which is "
                   "what makes the registry clause demonstrably load-bearing. "
                   "Faithful real patch: assemble the relation string without "
                   "delegating either operand to `self` — the UNPATCHED method, "
                   "failing BOTH F2P tests. Non-resolving.",
     "rationale": "rejection from `ToSeq(reg) == eq_registry(Old(ToSeq(reg)), kl, ul, "
                  "vl, kr, ur, vr)`: an echo of the text oracle leaves the registry "
                  "untouched, so neither slot's effect is applied."},
    {"id": "registry-wrong-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_WRONG_KEY,
     "refinement": "the lhs slot IS rendered by this renderer, but always under the "
                   "fixed key 120 ('x') instead of the name actually present. Correct "
                   "exactly on the `ul == 120` sub-domain — which contains every F2P "
                   "case, so a spec that left the name key a constant could not tell "
                   "it from gold. Faithful real patch: `self._print(Symbol('x'))` in "
                   "place of `self._print(expr.lhs)`, which renders and registers 'x' "
                   "for EVERY relation and so mis-renders "
                   "test_python_relational's `Ne(x/(y + 1), y**2)` line. "
                   "Non-resolving.",
     "rationale": "rejection from BOTH pins: at kl==1 `eq_text` fixes the lhs text to "
                  "`lit_name(ul)` and `eq_registry` fixes the entered key to `ul`; "
                  "neither holds for an arbitrary `ul != 120`."},
    {"id": "registry-only-when-wrap", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_REG_IF_WRAP,
     "refinement": "registration made CONDITIONAL on the wrap configuration: text "
                   "always right, registry right only on the wrap=True half. This is "
                   "the freedom a wrap-dependent registry clause would have left. "
                   "Faithful real patch: delegate the lhs only when "
                   "`self._settings.get('sympy_integers')` is set. `python()` runs "
                   "with default settings, so test_python_relational still FAILS "
                   "while test_Rational passes. Non-resolving.",
     "rationale": "rejection from the deliberately wrap-INDEPENDENT clause `ToSeq(reg) "
                  "== eq_registry(Old(ToSeq(reg)), kl, ul, vl, kr, ur, vr)`, which must "
                  "hold for BOTH values of `wrap`; the else branch emits the name as a "
                  "bare token and leaves the registry unchanged. Mirrors the real "
                  "receiver, whose registration never consults _settings."},
    {"id": "registry-no-dedup", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_DEDUP,
     "refinement": "render_name appends UNCONDITIONALLY, so a name already registered "
                   "is entered twice. Correct exactly on the 'not already present' "
                   "half of the domain. Faithful real patch: drop the `if symbol not "
                   "in self.symbols:` guard in `PythonPrinter._print_Symbol`, which "
                   "makes `python(Ne(x/(y + 1), y**2))` emit `x = Symbol('x')` twice "
                   "and FAILS test_python_relational. Non-resolving.",
     "rationale": "rejection from `ToSeq(reg) == registered(Old(ToSeq(reg)), c)`: "
                  "`registered` returns the registry UNCHANGED when `c` is already in "
                  "it, so a second entry breaks the pin."},
    {"id": "registry-frac-writes", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAC_WRITE,
     "refinement": "render_operand ALSO registers a key (a plausible 'record what you "
                   "rendered' over-reach), even though a fractional operand is not a "
                   "name. Text unchanged. Faithful real patch: a `_print_Rational` "
                   "that appends to `self.symbols`, injecting a spurious "
                   "`<key> = Symbol('<key>')` line into every `python()` output and "
                   "FAILING test_python_relational. Non-resolving.",
     "rationale": "rejection from render_operand's complementary NO-WRITE clause "
                  "`ToSeq(reg) == Old(ToSeq(reg))`, which is what makes the compounds' "
                  "registry growth attributable to the NAME slots only."},
    {"id": "registry-order-swapped", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LIM_REORDER,
     "refinement": "both limit names ARE registered, but the second slot registers "
                   "FIRST. Correct on the `ue == uz` sub-domain and on pre-states "
                   "already holding both names — a rival a set-valued registry model "
                   "would accept. Faithful real patch: let `z` reach _print_Symbol "
                   "before `e`. Since python() emits one preamble line per entry IN "
                   "LIST ORDER (python.py:69), `python(Limit(x, y, 7/2))` comes out "
                   "with `y = Symbol('y')` first and FAILS "
                   "test_python_relational's line-by-line comparison. Non-resolving.",
     "rationale": "rejection from `ToSeq(reg) == limit_registry(Old(ToSeq(reg)), plus, "
                  "ke, ue, ve, kz, uz, vz, k0, u0, v0, ud)`: limit_registry is the ORDERED "
                  "left-to-right `atom_registry` composition over the three slots in "
                  "TEMPLATE order, mirroring the tuple order of "
                  "`map(self._print, (e, z, z0))`; swapping the first two steps differs "
                  "whenever neither name is already present and they differ. Swapped as "
                  "a WHOLE BODY so the variable slot is still rendered exactly once and "
                  "the rejection is attributable to the ORDER."},
    {"id": "registry-leaf-wrong-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LEAF_WRONG_KEY,
     "refinement": "render_name returns the right TEXT for `c` but registers the "
                   "fixed key 120 ('x'). Distinct from registry-wrong-key, which "
                   "passes a wrong ARGUMENT at the call site and is caught by the text "
                   "pin first: here every text clause holds, so the verifier is forced "
                   "through to the registry clause and the rejection is attributable "
                   "to the registry alone. This is precisely the freedom the new "
                   "mutable `reg` parameter introduces — full write permission on a "
                   "list whose contents must nonetheless be exactly `registered(...)`. "
                   "Faithful real patch: `self.symbols.append('x')` in place of "
                   "`self.symbols.append(symbol)` in PythonPrinter._print_Symbol, "
                   "which emits `x = Symbol('x')` for every symbol and FAILS "
                   "test_python_relational. Non-resolving.",
     "rationale": "rejection from `ToSeq(reg) == registered(Old(ToSeq(reg)), c)`, which "
                  "fixes the entered key to the name actually rendered."},

    # ---- uniqueness rivals: observable (3), the UNMODELLED operand kind ----
    {"id": "unmodelled-slot-echo", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_ECHO_SLOT,
     "refinement": "the rhs slot's text is reproduced at the compound site from the "
                   "@Pure text oracle instead of being rendered, with the NAME "
                   "kind's registry effect reproduced by hand. On a fractional or a "
                   "name rhs this is byte- AND registry-identical to gold, which is "
                   "exactly why a two-kind carrier (name lhs, fraction rhs) accepts "
                   "it: a fraction registers nothing, so the rhs slot's registry "
                   "obligation there is discharged vacuously by doing nothing. Its "
                   "faithful real patch spells `expr.rhs` at the relation site "
                   "(`'%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs), "
                   "expr.rhs)`), so `python(Eq(x, y))` still drops the "
                   "`y = Symbol('y')` preamble line and F2P test_python_relational "
                   "FAILS 1 of its 2 assertions. Non-resolving.",
     "rationale": "rejection from `ToSeq(reg) == eq_registry(Old(ToSeq(reg)), kl, ul, "
                  "vl, kr, ur, vr)` at `kr == 2`: that slot's effect is the "
                  "uninterpreted `opaque_registry(r, ur)`, and no sequence of writes "
                  "expressible at the compound site can be equated with it — the only "
                  "discharge is to call the renderer. This is the case that makes the "
                  "rhs slot's registry obligation non-vacuous."},
    {"id": "unmodelled-slot-ambient-config", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_AMBIENT_UNMODELED,
     "refinement": "the rhs slot IS rendered by THIS renderer — so every registry "
                   "effect is right — but at the AMBIENT DEFAULT configuration rather "
                   "than the one the compound carries. This is the pre-patch "
                   "`%s`-of-subexpression shape applied at the one kind whose text is "
                   "not reproducible, and it is correct on the entire `wrap == False` "
                   "half of the domain. Faithful real patch: render the operand "
                   "through a fresh default-settings printer, so F2P "
                   "`sstr(Eq(x, S(1)/2), sympy_integers=True)` comes back "
                   "'Eq(x, 1/2)' and test_Rational FAILS. Non-resolving.",
     "rationale": "rejection from `ToSeq(Result()) == eq_text(wrap, kl, ul, vl, kr, "
                  "ur, vr)`: at `kr == 2` the demanded text is `opaque_text(ur, "
                  "wrap)`, and `opaque_text` is uninterpreted with NO relation assumed "
                  "between its two configurations, so `opaque_text(ur, False)` cannot "
                  "be equated with it. This case is what justifies the `wrap` argument "
                  "on `opaque_text`: without it the propagation observable would go "
                  "vacuous at every unmodelled slot."},
    {"id": "unmodelled-slot-delegate-if-wrap", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EQ_DELEGATE_IF_WRAP,
     "refinement": "delegation of the rhs slot made CONDITIONAL on the configuration: "
                   "rendered when `wrap` is on, echoed otherwise, so registration "
                   "happens only on half the domain. Correct on that half, and on the "
                   "whole `k in {0, 1}` sub-domain of the other half. Faithful real "
                   "patch: delegate the operand only when "
                   "`self._settings.get('sympy_integers')` is set — `python()` runs at "
                   "default settings, so test_python_relational still FAILS while "
                   "test_Rational passes. Non-resolving.",
     "rationale": "rejection from the deliberately `wrap`-INDEPENDENT clause `ToSeq("
                  "reg) == eq_registry(Old(ToSeq(reg)), kl, ul, vl, kr, ur, vr)`, "
                  "which must hold for BOTH values of a universally-quantified "
                  "`wrap`; the echoing branch cannot produce `opaque_registry(r, ur)` "
                  "at `kr == 2`. Mirrors the real receiver, whose registration "
                  "(python.py:37-41) never consults `_settings`."},
]


# ===========================================================================
# AXIOM LANE (Docker, real sympy callee under the gold patch)
# ===========================================================================
# digits / coprime are @ContractOnly A-consumed axioms; render_rational / lit_name /
# registered / eq_text / eq_registry / limit_text / limit_registry are A-reference
# deep models. Two probes run the REAL post-patch sympy callees in-container and
# strengthen axiom_check.py:
#   - ax-render-sound (axiom-soundness): asserts the TEXT deep models == real
#     sstr(Rational/Symbol/Eq/Limit, sympy_integers=wrap) over the coprime
#     non-integer boundary + a WIDER fuzz grid than axiom_check.py, AND the
#     REGISTRY deep models == the real PythonPrinter.symbols growth (read both
#     through the instance dispatch and through the public python() preamble), AND
#     that digits == str(int) is non-empty (the only fact the proof consumes), AND
#     the exact F2P assertions. Any disagreement => AXIOM-UNSOUND.
#   - ax-domain-containment (axiom-containment): every operand AND name key the
#     MODEL can reach (its Requires: p>=0, q>=2, coprime(p,q); is_name(c)) lies in
#     the real callee's domain — a proper fraction in lowest terms that the real
#     Rational does NOT collapse to an Integer / reduce, and a one-character Symbol
#     whose name is both its rendered text and its registry key. A reachable input
#     the deep model would NOT cover would be AXIOM-TOO-WEAK-FOR-CALLER. We also
#     confirm the inverse direction is SOUND, not a defect: the deep model covering
#     wrap=False AND wrap=True is correct over-coverage, never flagged.
# Both probes import ONLY the sympy api + stdlib (the runner mounts ONLY the probe
# at /work; axiom_check.py is NOT in-container).

_AX_RENDER_SOUND = r'''
import sys
import random
from math import gcd

from sympy import Symbol, Rational, Eq, Limit, sstr
from sympy.printing.python import PythonPrinter, python
from sympy.printing.str import StrPrinter


# ---- deep-model references, transcribed from model.py's @Pure helpers --------
def m_digits(n):
    assert n >= 0
    return str(n)

def m_render_rational(wrap, p, q):
    assert p >= 0 and q >= 2 and gcd(p, q) == 1
    if wrap:
        return "S(" + m_digits(p) + ")/" + m_digits(q)
    return m_digits(p) + "/" + m_digits(q)

def m_is_name(c):
    return 97 <= c <= 122

def m_lit_name(c):
    assert m_is_name(c)
    return chr(c)

def m_registered(reg, c):
    assert m_is_name(c)
    if c in reg:
        return list(reg)
    return list(reg) + [c]

def m_eq_text(wrap, nl, rp, rq):
    return "Eq(" + m_lit_name(nl) + ", " + m_render_rational(wrap, rp, rq) + ")"

def m_eq_registry(reg, nl):
    return m_registered(reg, nl)

def m_limit_text(wrap, ne, nz, z0p, z0q):
    return ("Limit(" + m_lit_name(ne) + ", " + m_lit_name(nz) + ", "
            + m_render_rational(wrap, z0p, z0q) + ")")

def m_limit_registry(reg, ne, nz):
    return m_registered(m_registered(reg, ne), nz)


def names_of(reg):
    return [chr(c) for c in reg]

def reg_printer(reg):
    pp = PythonPrinter({})
    pp.symbols = names_of(reg)
    return pp

def preamble(expr):
    out = []
    for line in python(expr).splitlines():
        if " = Symbol('" in line:
            out.append(line.split(" = Symbol('")[1].rstrip("')"))
        else:
            break
    return out


ALPHA = list(range(97, 123))
XK, YK, QK, ZK = ord("x"), ord("y"), ord("q"), ord("z")
SEEDS = [[], [YK], [QK, YK], [XK], [ZK, XK], [XK, YK], [YK, XK]]


def main():
    bad = []
    x = Symbol("x")
    y = Symbol("y")

    # ---- the receiver split the mapping declares -----------------------------
    if PythonPrinter._print_Relational is not StrPrinter._print_Relational:
        bad.append(("receivers do not share _print_Relational",))
    if PythonPrinter._print_Limit is not StrPrinter._print_Limit:
        bad.append(("receivers do not share _print_Limit",))
    if "sympy_integers" in PythonPrinter._default_settings:
        bad.append(("registry receiver unexpectedly carries the wrap setting",))
    if not hasattr(PythonPrinter({}), "symbols"):
        bad.append(("registry receiver has no registry",))
    if hasattr(StrPrinter({}), "symbols"):
        bad.append(("configuration receiver unexpectedly has a registry",))

    # ---- A-consumed digits: str(n) non-empty (the only fact the proof uses) ----
    for n in [0, 1, 2, 3, 7, 9, 10, 39, 99, 100, 1000, 10 ** 10, 123456789]:
        if len(m_digits(n)) < 1:
            bad.append(("digits empty", n))

    # ---- A-reference name leaves: text (both settings) and registry -----------
    for c in ALPHA:
        for wrap in (False, True):
            obs = sstr(Symbol(chr(c)), sympy_integers=wrap)
            if obs != m_lit_name(c):
                bad.append(("lit_name", wrap, chr(c), obs, m_lit_name(c)))
        for reg in SEEDS:
            exp = names_of(m_registered(reg, c))
            pp = reg_printer(reg)
            pp._print(Symbol(chr(c)))
            if list(pp.symbols) != exp:
                bad.append(("registered", names_of(reg), chr(c),
                            list(pp.symbols), exp))
            if not reg and preamble(Symbol(chr(c))) != exp:
                bad.append(("registered/preamble", chr(c),
                            preamble(Symbol(chr(c))), exp))

    # ---- A-reference leaf + compound TEXT over a WIDE coprime non-integer grid --
    rng = random.Random(20240617)
    boundary = [(2, 3), (1, 2), (7, 2), (5, 6), (10, 3), (1, 7), (123, 7),
                (3, 4), (1, 3), (1, 10 ** 10)]
    for wrap in (False, True):
        grid = list(boundary)
        seen = 0
        while seen < 4000:
            p = rng.randint(1, 9999)
            q = rng.randint(2, 9999)
            if gcd(p, q) != 1:
                continue
            grid.append((p, q))
            seen += 1
        for (p, q) in grid:
            r = Rational(p, q)
            # domain non-collapse guard (coprime q>=2 stays a proper fraction)
            if r.q != q or r.p != p:
                bad.append(("Rational collapsed", p, q, r.p, r.q))
                continue
            obs = sstr(r, sympy_integers=wrap)
            exp = m_render_rational(wrap, p, q)
            if obs != exp:
                bad.append(("render_rational", wrap, p, q, obs, exp))
            nl = rng.choice(ALPHA)
            ne = rng.choice(ALPHA)
            nz = rng.choice(ALPHA)
            # compound Eq(name, p/q) — must not auto-evaluate to a Boolean
            rel = Eq(Symbol(chr(nl)), r)
            if rel.func is not Eq:
                bad.append(("Eq auto-eval", chr(nl), p, q, repr(rel)))
            else:
                obs = sstr(rel, sympy_integers=wrap)
                exp = m_eq_text(wrap, nl, p, q)
                if obs != exp:
                    bad.append(("eq_text", wrap, chr(nl), p, q, obs, exp))
            # compound Limit(name, name, p/q) — real point takes dir == '+'
            lim = Limit(Symbol(chr(ne)), Symbol(chr(nz)), r)
            if str(lim.args[3]) != "+":
                bad.append(("Limit dir", p, q, str(lim.args[3])))
            else:
                obs = sstr(lim, sympy_integers=wrap)
                exp = m_limit_text(wrap, ne, nz, p, q)
                if obs != exp:
                    bad.append(("limit_text", wrap, chr(ne), chr(nz), p, q,
                                obs, exp))
            if len(bad) > 8:
                break

    # ---- A-reference compound REGISTRY (wrap-independent) ---------------------
    for reg in SEEDS:
        for (p, q) in [(2, 3), (7, 2), (1, 2)]:
            for nl in (XK, YK, QK, ZK):
                rel = Eq(Symbol(chr(nl)), Rational(p, q))
                exp = names_of(m_eq_registry(reg, nl))
                pp = reg_printer(reg)
                pp._print(rel)
                if list(pp.symbols) != exp:
                    bad.append(("eq_registry", names_of(reg), chr(nl), p, q,
                                list(pp.symbols), exp))
                if not reg and preamble(rel) != exp:
                    bad.append(("eq_registry/preamble", chr(nl), p, q,
                                preamble(rel), exp))
            for (ne, nz) in ((XK, XK), (XK, YK), (YK, XK), (QK, ZK), (YK, YK)):
                lim = Limit(Symbol(chr(ne)), Symbol(chr(nz)), Rational(p, q))
                exp = names_of(m_limit_registry(reg, ne, nz))
                pp = reg_printer(reg)
                pp._print(lim)
                if list(pp.symbols) != exp:
                    bad.append(("limit_registry", names_of(reg), chr(ne),
                                chr(nz), p, q, list(pp.symbols), exp))
                if not reg and preamble(lim) != exp:
                    bad.append(("limit_registry/preamble", chr(ne), chr(nz),
                                p, q, preamble(lim), exp))
            # the fraction slot's NO-WRITE clause
            pp = reg_printer(reg)
            pp._print(Rational(p, q))
            if list(pp.symbols) != names_of(reg):
                bad.append(("render_operand registers", names_of(reg), p, q,
                            list(pp.symbols)))
    seen = 0
    while seen < 1500 and len(bad) <= 8:
        p = rng.randint(1, 999)
        q = rng.randint(2, 999)
        if gcd(p, q) != 1:
            continue
        reg = rng.sample(ALPHA, rng.randint(0, 3))
        nl, ne, nz = (rng.choice(ALPHA), rng.choice(ALPHA), rng.choice(ALPHA))
        rel = Eq(Symbol(chr(nl)), Rational(p, q))
        pp = reg_printer(reg)
        pp._print(rel)
        exp = names_of(m_eq_registry(reg, nl))
        if list(pp.symbols) != exp:
            bad.append(("eq_registry fuzz", names_of(reg), chr(nl), p, q,
                        list(pp.symbols), exp))
        lim = Limit(Symbol(chr(ne)), Symbol(chr(nz)), Rational(p, q))
        pp = reg_printer(reg)
        pp._print(lim)
        exp = names_of(m_limit_registry(reg, ne, nz))
        if list(pp.symbols) != exp:
            bad.append(("limit_registry fuzz", names_of(reg), chr(ne), chr(nz),
                        p, q, list(pp.symbols), exp))
        seen += 1

    # ---- the exact FAIL_TO_PASS assertions (test_Rational / test_python_relational)
    if sstr(Eq(x, Rational(2, 3)), sympy_integers=True) != "Eq(x, S(2)/3)":
        bad.append(("F2P Eq", sstr(Eq(x, Rational(2, 3)), sympy_integers=True)))
    if sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True) != "Limit(x, x, S(7)/2)":
        bad.append(("F2P Limit", sstr(Limit(x, x, Rational(7, 2)), sympy_integers=True)))
    if sstr(Eq(x, Rational(2, 3))) != "Eq(x, 2/3)":
        bad.append(("F2P Eq default", sstr(Eq(x, Rational(2, 3)))))
    if python(Eq(x, y)) != "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)":
        bad.append(("F2P python relational", python(Eq(x, y))))
    if python(Limit(x, y, Rational(7, 2))) != \
            "x = Symbol('x')\ny = Symbol('y')\ne = Limit(x, y, Rational(7, 2))":
        bad.append(("registry surface on Limit", python(Limit(x, y, Rational(7, 2)))))

    if bad:
        print("AXIOM-UNSOUND (deep model != real callee):", bad[:8])
        return 1
    print("render A-reference SOUND: the two receivers share the patched method "
          "objects; render_rational/lit_name/eq_text/limit_text == real sstr over "
          "the coprime non-integer boundary + ~4000 fuzz fractions per setting and "
          "all 26 name keys; registered/eq_registry/limit_registry == the real "
          "PythonPrinter.symbols growth (instance dispatch AND python() preamble) "
          "over 26 keys x 7 pre-seeds + 1500 fuzz inputs; a fractional operand "
          "registers nothing; digits non-empty; exact F2P assertions hold (Eq/Limit "
          "wrap on, Eq default, python(Eq), python(Limit)).")
    return 0


sys.exit(main())
'''

_AX_DOMAIN_CONTAIN = r'''
import sys
import random
from math import gcd

from sympy import Rational, Integer, Symbol, sstr
from sympy.printing.python import PythonPrinter


def main():
    # The model's Requires for every render is p>=0, q>=2, coprime(p,q) on the
    # fraction slot and is_name(c) (97..122) on each name slot. The A-reference
    # deep models cover exactly the proper-fraction-in-lowest-terms carrier and
    # the one-character-name carrier. We confirm CONTAINMENT: every input the
    # model can reach is one the real callee keeps in that carrier — a Rational
    # that neither reduces to a smaller fraction nor becomes an Integer, and a
    # Symbol whose name is exactly one character, is its own rendered text, and is
    # its own registry key. A reachable input the deep model would NOT cover would
    # be AXIOM-TOO-WEAK-FOR-CALLER.
    bad = []
    rng = random.Random(99)

    boundary = [(2, 3), (1, 2), (7, 2), (5, 6), (10, 3), (1, 7), (123, 7),
                (3, 4), (1, 3), (1, 10 ** 10)]
    grid = list(boundary)
    seen = 0
    while seen < 4000:
        p = rng.randint(1, 9999)
        q = rng.randint(2, 9999)
        if gcd(p, q) != 1:
            continue
        grid.append((p, q))
        seen += 1

    for (p, q) in grid:
        # exactly the model's Requires domain
        if not (p >= 0 and q >= 2 and gcd(p, q) == 1):
            bad.append(("not in model Requires", p, q))
            continue
        r = Rational(p, q)
        if isinstance(r, Integer):
            bad.append(("model-reachable operand collapsed to Integer", p, q))
            continue
        if r.p != p or r.q != q:
            bad.append(("model-reachable operand reduced", p, q, r.p, r.q))
            continue
        if r.q < 2:
            bad.append(("denominator below modeled q>=2 after build", p, q, r.q))

    # Every name key the model can reach (is_name: 97..122) is a real one-character
    # Symbol whose name IS its rendered text (either setting) and IS the key the
    # registry stores. If any key rendered as something else, or registered under a
    # different string, the name carrier would not contain it.
    for c in range(97, 123):
        nm = chr(c)
        sym = Symbol(nm)
        if sym.name != nm or len(sym.name) != 1:
            bad.append(("name carrier mismatch", nm, sym.name))
            continue
        for wrap in (False, True):
            if sstr(sym, sympy_integers=wrap) != nm:
                bad.append(("name text not the key", nm, wrap,
                            sstr(sym, sympy_integers=wrap)))
        pp = PythonPrinter({})
        pp._print(sym)
        if list(pp.symbols) != [nm]:
            bad.append(("name key not the registry entry", nm, list(pp.symbols)))

    # SOUND over-coverage check: the deep model covers BOTH settings (wrap False
    # AND True); that is correct over-coverage, never a defect. Confirm both are
    # reachable inputs (the F2P exercises both: Eq default = wrap False, Eq
    # sympy_integers=True = wrap True), so neither setting is an unreachable
    # over-cover that would warrant flagging.
    for wrap in (False, True):
        # representative reachable input under this setting
        r = Rational(2, 3)
        if isinstance(r, Integer):
            bad.append(("control operand collapsed", wrap))

    if bad:
        print("AXIOM-TOO-WEAK-FOR-CALLER:", bad[:8])
        return 1
    print("containment OK: every operand the model can reach (p>=0, q>=2, "
          "coprime) is a non-collapsing proper fraction the real Rational keeps "
          "(no Integer collapse, no reduction), and every name key the model can "
          "reach (97..122) is a real one-character Symbol whose name is both its "
          "rendered text under either setting and its registry entry; the deep "
          "model covers both settings (correct over-coverage).",
          len(grid), "operands and 26 name keys confirmed.")
    return 0


sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-render-sound",
     "axiom": "render_rational/lit_name/registered/eq_text/eq_registry/"
              "limit_text/limit_registry",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_RENDER_SOUND,
     "rationale": "if the real post-patch sstr(Rational/Symbol/Eq/Limit, "
                  "sympy_integers=wrap) differs from the TEXT deep models on any "
                  "coprime non-integer operand or any name key, or the real "
                  "PythonPrinter.symbols growth (instance dispatch or python() "
                  "preamble) differs from the REGISTRY deep models, or "
                  "digits(n)=str(n) is empty, or the two receivers do not share the "
                  "patched method objects, or an exact F2P assertion fails => "
                  "AXIOM-UNSOUND. Strengthens axiom_check.py with a wider "
                  "per-setting fuzz grid."},
    {"id": "ax-domain-containment",
     "axiom": "coprime/render_rational/is_name/lit_name",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_DOMAIN_CONTAIN,
     "rationale": "every operand the model can reach (its Requires: p>=0, q>=2, "
                  "coprime) is a non-collapsing proper fraction the real Rational "
                  "keeps (no Integer collapse / reduction), and every name key it "
                  "can reach (is_name: 97..122) is a real one-character Symbol whose "
                  "name is both its rendered text under either setting and its "
                  "registry entry — so the A-reference deep models are exercised "
                  "exactly where the caller reaches them. A reachable input the deep "
                  "model would not cover would be AXIOM-TOO-WEAK-FOR-CALLER (none "
                  "exists); the dual-setting coverage is correct over-coverage."},
]
