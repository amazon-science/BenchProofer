"""Twin-artifact model for sympy__sympy-14531.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual renderer carries two pieces of its OWN state: a CONFIGURATION flag
  that selects how a fractional number is written, and a NAME REGISTRY that
  records the simple names it has rendered. When the flag is OFF a fraction p/q
  (in lowest terms, q>=2) is written plainly as "p/q"; when the flag is ON the
  numerator is wrapped, so p/q is written "S(p)/q". The registry holds one entry
  per DISTINCT name, in the order the names were first rendered.

  When the renderer renders a COMPOUND expression (a relation between two
  operands, or a limit, whose slots are filled by three operands together with
  the DIRECTION it is taken in), EVERY operand slot must be rendered BY THIS
  RENDERER. An operand slot may be filled by ANY operand: a fractional number, a
  simple name, or an operand whose own rendering rule is not modeled here.
  Rendering a compound therefore

    * emits, in each slot, THIS renderer's rendering of that slot's operand
      UNDER THIS RENDERER'S OWN CONFIGURATION -- so a fractional operand's
      numerator is wrapped exactly when the whole is rendered with the flag ON,
      and an operand whose rule is not modeled is nonetheless rendered by THIS
      renderer at THIS configuration rather than at an ambient default; and
    * leaves THIS renderer's registry extended by whatever each slot's operand
      registers, the slots taken LEFT TO RIGHT: a name is appended unless
      already present, a fractional number registers nothing, and an operand
      whose rule is not modeled contributes whatever it contributes -- which is
      not modeled, but which only THIS renderer can produce.

  The surrounding template text ("Eq(", ", ", ")", "Limit(", ", dir='", "')") is
  independent of both. The registry is independent of the configuration flag:
  which names are entered does not depend on how fractions are written.

  A limit's template has TWO forms, selected by its direction. When the direction
  is the distinguished one the text is closed off directly after the third
  operand; otherwise a FOURTH slot spells the direction out, introduced by
  ", dir='" and closed by "')". That fourth slot is an operand slot like any
  other -- it is rendered BY THIS RENDERER at THIS renderer's configuration, and
  it contributes to THIS renderer's registry just as the other three do. Which
  form is taken is not something the renderer decides: it reads the direction off
  the compound it was handed, so both forms are stated here and neither may be
  assumed away.

  Equivalently: rendering an operand is an operation OF THE RENDERER THAT OWNS
  the compound, never a detached re-rendering by some ambient default renderer,
  and never a reproduction of the operand's text at the compound site. A
  detached re-rendering is observable twice over: it loses the configuration (so
  a fractional operand comes out unwrapped while the flag is ON) and it loses the
  registration (so a name never reaches this renderer's registry). BOTH
  observables are stated here, because a detached re-rendering of a NAME yields
  the very same TEXT the owning renderer would yield -- text alone cannot tell
  the two apart, which is why the registry is part of the specification and not a
  side note. And because a slot may hold an operand of ANY kind, reproducing the
  text of the kinds that ARE modeled is not enough either: the specification
  speaks of every slot, whatever fills it.

Strings are modelled as `List[int]`/`PSeq[int]` of code points (Nagini bans
`str` indexing). The configuration flag is modelled as a `bool`. A simple name
is modelled by its single code point, which is both its rendered text and its
registry key, so the registry is a `List[int]`/`PSeq[int]` of code points too.
An operand is modelled by a triple `(k, u, v)`: `k == 0` is the fractional
number `u/v`, `k == 1` is the simple name with code point `u`, and `k == 2` is an
operand whose own rendering rule is NOT modelled, identified by the abstract
handle `u`. A limit's direction is modelled by a `bool` (`plus`, selecting which
of the two template forms applies) together with the abstract handle `ud` of the
operand that fills the fourth slot -- an operand of that same third kind, since a
direction is not a fractional number and not a simple name. For that third kind the rendered text and the registry effect are
UNINTERPRETED functions of the operand (and, for the text, of the configuration):
nothing about them is assumed, so the only way to obtain either is to have THIS
renderer render that operand. The decimal spelling of a non-negative integer is
an unchanged leaf callee and is axiomatised (`digits`); it is deterministic in
its argument, which is all the proof needs.

The fractional operand domain is the canonical, non-collapsing region: a proper
fraction in lowest terms (q>=2, numerator and denominator coprime). Whole
numbers and non-reduced pairs canonicalise to a different carrier and are
reached, in this model, as operands of the third (unmodelled-rule) kind. A name
operand is a single lowercase letter (code points 97..122): its rendered text is
that one character under either configuration, and its registry key is that same
code point; longer names are likewise reached as the third kind.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def digits(n: int) -> PSeq[int]:
    """Decimal spelling of a non-negative integer as a code-point sequence — the
    unchanged leaf callee (`str(int)`). The only fact the proof needs is that it
    is a deterministic function of `n` (so `digits(p)` is the same whichever
    configuration is active) and non-empty. Provenance + executable soundness
    check: mapping.md §3 / axiom_check.py."""
    Requires(n >= 0)
    Ensures(len(Result()) >= 1)


@Pure
@ContractOnly
def coprime(p: int, q: int) -> bool:
    """Abstract predicate: p and q share no common factor (the operand is a
    fraction already in lowest terms). The fractional carrier only renders as
    `digits(p)/digits(q)` when it is canonical; a non-reduced pair denotes a
    DIFFERENT canonical fraction and is out of the modeled domain. Used purely to
    restrict the operand domain — the proof does not otherwise depend on it.
    G-AX enforces the matching domain filter (`gcd(p,q)==1`)."""


@Pure
@ContractOnly
def opaque_text(a: int, wrap: bool) -> PSeq[int]:
    """UNINTERPRETED. The text THIS renderer produces for the operand with
    abstract handle `a` when THIS renderer is configured by `wrap`. Nothing about
    its shape is assumed — not its length, not its alphabet, not any relation
    between the two configurations — so no implementation can produce this value
    by reproducing an operand's text itself: the only way to obtain it is to have
    THIS renderer render that operand (`render_unmodeled`) at the configuration
    the compound carries. The `wrap` argument is what makes the propagation
    observable at such a slot: a detached ambient-default re-rendering yields
    `opaque_text(a, False)`, a value the verifier cannot equate with
    `opaque_text(a, wrap)`. Provenance + executable soundness check:
    mapping.md §3.5 / axiom_check.py."""


@Pure
@ContractOnly
def opaque_registry(r: PSeq[int], a: int) -> PSeq[int]:
    """UNINTERPRETED. THIS renderer's name registry after IT has rendered the
    operand with abstract handle `a`, starting from the registry `r`. How many
    names such an operand contributes, which they are, and in what order is NOT
    modelled. Two facts are modelled by the shape of the signature: the effect is
    a function of the registry it starts FROM (so effects compose left to right
    along the operand slots) and it does NOT depend on the configuration
    (registration is independent of how fractions are written). Because the
    function is uninterpreted, an implementation cannot reproduce this effect by
    writing into the registry itself. mapping.md §3.5 / axiom_check.py."""


@ContractOnly
def render_unmodeled(a: int, wrap: bool, reg: List[int]) -> List[int]:
    """THIS renderer rendering an operand whose own rendering rule is not
    modelled — the recursive dispatch to whichever rule that operand has. Its
    body is deliberately absent: the callee is unchanged behaviour, and the whole
    specification content at such a slot is that the compound CALLS IT, with the
    compound's own configuration and the compound's own registry, rather than
    reproducing the operand's text or registry effect itself. Termination of
    rendering an operand is assumed (mapping.md §3.5)."""
    Requires(Acc(list_pred(reg)))
    Requires(MustTerminate(6))
    Ensures(Acc(list_pred(Result())))
    Ensures(Acc(list_pred(reg)))
    Ensures(ToSeq(Result()) == opaque_text(a, wrap))
    Ensures(ToSeq(reg) == opaque_registry(Old(ToSeq(reg)), a))
# axioms-end


# pure-start
@Pure
def lit_S_open() -> PSeq[int]:
    # 'S('
    return PSeq(83, 40)


@Pure
def lit_close_slash() -> PSeq[int]:
    # ')/'
    return PSeq(41, 47)


@Pure
def lit_slash() -> PSeq[int]:
    # '/'
    return PSeq(47)


@Pure
def render_rational(wrap: bool, p: int, q: int) -> PSeq[int]:
    """The text of a single proper-fraction operand p/q (lowest terms, q>=2)
    under configuration `wrap`. This is the leaf renderer whose result MUST flow
    up into every compound using the SAME `wrap` the compound is rendered with.

        wrap      -> 'S(' + digits(p) + ')/' + digits(q)
        not wrap  -> digits(p) + '/' + digits(q)
    """
    Requires(p >= 0 and q >= 2 and coprime(p, q))
    if wrap:
        return lit_S_open() + digits(p) + lit_close_slash() + digits(q)
    return digits(p) + lit_slash() + digits(q)


@Pure
def is_name(c: int) -> bool:
    """`c` is the carrier of a simple name operand: a single lowercase letter,
    identified with its code point. Its rendered text is that one character
    under EITHER configuration, and its registry key is that same code point."""
    return 97 <= c and c <= 122


@Pure
def lit_name(c: int) -> PSeq[int]:
    """The text a name operand renders to: the one code point that names it.
    Configuration-independent — which is exactly why the text of this slot
    cannot on its own witness that the OWNING renderer rendered it."""
    Requires(is_name(c))
    return PSeq(c)


@Pure
def registered(r: PSeq[int], c: int) -> PSeq[int]:
    """The renderer's name registry after IT renders the name `c`: `c` appended
    at the end, unless the registry already holds it. One entry per DISTINCT
    name, in first-render order. Note `registered(r, c)` is never `r` unless `c`
    is already in `r`, so a slot whose name the renderer did not render is
    visible here even though its text is unchanged."""
    Requires(is_name(c))
    if c in r:
        return r
    return r + PSeq(c)


@Pure
def is_atom(k: int, u: int, v: int) -> bool:
    """`(k, u, v)` denotes an operand that may fill a slot of a compound:

        k == 0 : the fractional number u/v, proper and in lowest terms
        k == 1 : the simple name with code point u
        k == 2 : an operand whose own rendering rule is NOT modelled, with
                 abstract handle u (v is immaterial)

    Every slot of every modeled compound ranges over ALL THREE kinds. The third
    kind is what makes the obligation "this slot is rendered by THIS renderer"
    inescapable: its text and its registry effect are uninterpreted, so they
    cannot be reproduced at the compound site."""
    if k == 1:
        return is_name(u)
    if k == 0:
        return u >= 0 and v >= 2 and coprime(u, v)
    return k == 2


@Pure
def atom_text(k: int, u: int, v: int, wrap: bool) -> PSeq[int]:
    """THIS renderer's rendering of the operand `(k, u, v)` at configuration
    `wrap`: the fraction's own text under `wrap` for the fractional kind, the one
    code point for a name, and the uninterpreted `opaque_text(u, wrap)` for an
    operand whose rule is not modelled."""
    Requires(is_atom(k, u, v))
    if k == 1:
        return lit_name(u)
    if k == 0:
        return render_rational(wrap, u, v)
    return opaque_text(u, wrap)


@Pure
def atom_registry(r: PSeq[int], k: int, u: int, v: int) -> PSeq[int]:
    """THIS renderer's registry after IT renders the operand `(k, u, v)` from the
    registry `r`: a name is appended unless present, a fractional number
    registers nothing, and an operand whose rule is not modelled contributes the
    uninterpreted `opaque_registry(r, u)`. Configuration-independent throughout."""
    Requires(is_atom(k, u, v))
    if k == 1:
        return registered(r, u)
    if k == 0:
        return r
    return opaque_registry(r, u)


@Pure
def lit_eq_open() -> PSeq[int]:
    # 'Eq('
    return PSeq(69, 113, 40)


@Pure
def lit_comma_space() -> PSeq[int]:
    # ', '
    return PSeq(44, 32)


@Pure
def lit_rparen() -> PSeq[int]:
    # ')'
    return PSeq(41)


@Pure
def lit_limit_open() -> PSeq[int]:
    # 'Limit('
    return PSeq(76, 105, 109, 105, 116, 40)


@Pure
def lit_dir_open() -> PSeq[int]:
    # ", dir='" — the separator that introduces the direction slot
    return PSeq(44, 32, 100, 105, 114, 61, 39)


@Pure
def lit_quote_rparen() -> PSeq[int]:
    # "')" — closes the direction slot and the whole template
    return PSeq(39, 41)


@Pure
def eq_text(wrap: bool, kl: int, ul: int, vl: int,
            kr: int, ur: int, vr: int) -> PSeq[int]:
    """The full text of the relation Eq(left, right): the constant template (open
    bracket, separator, close bracket) with EACH operand slot filled by THIS
    renderer's rendering of that operand at THIS renderer's configuration
    `wrap`. Both slots range over all three operand kinds."""
    Requires(is_atom(kl, ul, vl) and is_atom(kr, ur, vr))
    return (lit_eq_open() + atom_text(kl, ul, vl, wrap) + lit_comma_space()
            + atom_text(kr, ur, vr, wrap) + lit_rparen())


@Pure
def eq_registry(r: PSeq[int], kl: int, ul: int, vl: int,
                kr: int, ur: int, vr: int) -> PSeq[int]:
    """The registry after the renderer renders Eq(left, right): the two slots'
    registry effects composed LEFT TO RIGHT. Independent of `wrap`."""
    Requires(is_atom(kl, ul, vl) and is_atom(kr, ur, vr))
    return atom_registry(atom_registry(r, kl, ul, vl), kr, ur, vr)


@Pure
def limit_text(wrap: bool, plus: bool, ke: int, ue: int, ve: int,
               kz: int, uz: int, vz: int,
               k0: int, u0: int, v0: int, ud: int) -> PSeq[int]:
    """The full text of a limit over (body, variable, point) taken in a given
    direction: the constant template with EACH operand slot filled by THIS
    renderer's rendering of that operand at THIS renderer's configuration
    `wrap`. The template has two forms, selected by the direction:

        plus      -> 'Limit(' e ', ' z ', ' z0 ')'
        not plus  -> 'Limit(' e ', ' z ', ' z0 ", dir='" d "')"

    In the second form the direction is a FOURTH slot, filled by THIS renderer's
    rendering of the direction operand `ud` at the same configuration -- so the
    text of that slot is `opaque_text(ud, wrap)`, exactly as at any other slot
    holding an operand whose own rule is not modelled."""
    Requires(is_atom(ke, ue, ve) and is_atom(kz, uz, vz) and is_atom(k0, u0, v0))
    if plus:
        return (lit_limit_open() + atom_text(ke, ue, ve, wrap) + lit_comma_space()
                + atom_text(kz, uz, vz, wrap) + lit_comma_space()
                + atom_text(k0, u0, v0, wrap) + lit_rparen())
    return (lit_limit_open() + atom_text(ke, ue, ve, wrap) + lit_comma_space()
            + atom_text(kz, uz, vz, wrap) + lit_comma_space()
            + atom_text(k0, u0, v0, wrap) + lit_dir_open()
            + opaque_text(ud, wrap) + lit_quote_rparen())


@Pure
def limit_registry(r: PSeq[int], plus: bool, ke: int, ue: int, ve: int,
                   kz: int, uz: int, vz: int,
                   k0: int, u0: int, v0: int, ud: int) -> PSeq[int]:
    """The registry after the renderer renders the limit: the slots' registry
    effects composed LEFT TO RIGHT, in the order the slots appear in the template
    (so the slots are separately visible). In the second template form the
    DIRECTION slot is one of them, and it comes last: its effect is the
    uninterpreted `opaque_registry(., ud)` applied after the other three, so a
    renderer that spells the direction out without rendering it is visible here.
    Independent of `wrap` throughout."""
    Requires(is_atom(ke, ue, ve) and is_atom(kz, uz, vz) and is_atom(k0, u0, v0))
    if plus:
        return atom_registry(atom_registry(atom_registry(r, ke, ue, ve),
                                           kz, uz, vz), k0, u0, v0)
    return opaque_registry(atom_registry(atom_registry(atom_registry(r, ke, ue, ve),
                                                       kz, uz, vz), k0, u0, v0), ud)
# pure-end


def render_equation(wrap: bool, kl: int, ul: int, vl: int,
                    kr: int, ur: int, vr: int, reg: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(is_atom(kl, ul, vl) and is_atom(kr, ur, vr))
    # `reg` is THIS renderer's own registry and is WRITTEN by this call, so it is
    # held at FULL list permission rather than Acc(..., 1/2); the postconditions
    # state exactly how it grows, so the permission is not a licence to scribble.
    Requires(Acc(list_pred(reg)))
    Requires(MustTerminate(20))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(Acc(list_pred(reg)))
    # (1) TEXT: the rendered relation is the constant template with EACH operand
    # slot filled by THIS renderer's rendering of that operand under THIS
    # renderer's own configuration `wrap`. A renderer that renders a slot under
    # an ambient default configuration (ignoring `wrap`) violates this; so does
    # one that reproduces a slot's text at the compound site, because for an
    # operand whose rule is not modelled that text is not reproducible.
    Ensures(ToSeq(Result()) == eq_text(wrap, kl, ul, vl, kr, ur, vr))
    # (2) REGISTRY: rendering the relation leaves THIS renderer's registry
    # extended by BOTH slots' registry effects, left to right. A renderer that
    # emits a slot without rendering it — a detached re-rendering, or a constant
    # token, or a reproduction of the text — produces the right text for some
    # operand kinds but does not grow the registry, and violates this.
    Ensures(ToSeq(reg) == eq_registry(Old(ToSeq(reg)), kl, ul, vl, kr, ur, vr))
    # post-conditions-end
    # impl-start
    # PRE-PATCH: each operand slot is re-rendered by a DETACHED ambient-default
    # renderer (its own fresh registry, the default configuration) instead of by
    # the renderer that owns the compound. The name slots come out with exactly
    # the right TEXT, so only the registry clause and the wrap-dependent slots
    # can tell the difference.
    out = []  # type: List[int]
    fresh = []  # type: List[int]
    out = out + [69, 113, 40]                          # 'Eq('
    if kl == 1:
        out = out + materialize(lit_name(ul))            # detached: right text, NO registration
    elif kl == 0:
        out = out + render_operand(False, ul, vl, fresh)  # detached: ambient default config
    else:
        out = out + render_unmodeled(ul, False, fresh)     # detached: a fresh ambient renderer
    out = out + [44, 32]                               # ', '
    if kr == 1:
        out = out + materialize(lit_name(ur))            # detached: right text, NO registration
    elif kr == 0:
        out = out + render_operand(False, ur, vr, fresh)  # detached: ambient default config
    else:
        out = out + render_unmodeled(ur, False, fresh)     # detached: a fresh ambient renderer
    out = out + [41]                                   # ')'
    return out
    # impl-end


def render_directed_limit(wrap: bool, plus: bool, ke: int, ue: int, ve: int,
                          kz: int, uz: int, vz: int,
                          k0: int, u0: int, v0: int, ud: int,
                          reg: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(is_atom(ke, ue, ve) and is_atom(kz, uz, vz) and is_atom(k0, u0, v0))
    # As in render_equation: `reg` is written, hence full list permission.
    Requires(Acc(list_pred(reg)))
    Requires(MustTerminate(24))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(Acc(list_pred(reg)))
    # (1) TEXT: whichever of the two template forms the DIRECTION selects, with
    # each operand slot of that form -- the three operands, and in the second form
    # the direction as a fourth slot -- rendered by THIS renderer under THIS
    # renderer's configuration.
    Ensures(ToSeq(Result()) == limit_text(wrap, plus, ke, ue, ve, kz, uz, vz,
                                          k0, u0, v0, ud))
    # (2) REGISTRY: every slot's registry effect, composed left to right, the
    # direction slot last when it is present. Because the slots are independently
    # parameterised, each one is separately visible here; a slot emitted as text
    # without being rendered by this renderer violates this clause.
    Ensures(ToSeq(reg) == limit_registry(Old(ToSeq(reg)), plus, ke, ue, ve,
                                         kz, uz, vz, k0, u0, v0, ud))
    # post-conditions-end
    # impl-start
    # PRE-PATCH: as in render_equation, EVERY slot -- the three operands and, in
    # the second template form, the direction -- is re-rendered by a detached
    # ambient-default renderer.
    out = []  # type: List[int]
    fresh = []  # type: List[int]
    out = out + [76, 105, 109, 105, 116, 40]           # 'Limit('
    if ke == 1:
        out = out + materialize(lit_name(ue))            # detached: right text, NO registration
    elif ke == 0:
        out = out + render_operand(False, ue, ve, fresh)  # detached: ambient default config
    else:
        out = out + render_unmodeled(ue, False, fresh)     # detached: a fresh ambient renderer
    out = out + [44, 32]                               # ', '
    if kz == 1:
        out = out + materialize(lit_name(uz))            # detached: right text, NO registration
    elif kz == 0:
        out = out + render_operand(False, uz, vz, fresh)  # detached: ambient default config
    else:
        out = out + render_unmodeled(uz, False, fresh)     # detached: a fresh ambient renderer
    out = out + [44, 32]                               # ', '
    if k0 == 1:
        out = out + materialize(lit_name(u0))            # detached: right text, NO registration
    elif k0 == 0:
        out = out + render_operand(False, u0, v0, fresh)  # detached: ambient default config
    else:
        out = out + render_unmodeled(u0, False, fresh)     # detached: a fresh ambient renderer
    if plus:
        out = out + [41]                                   # ')'
        return out
    out = out + [44, 32, 100, 105, 114, 61, 39]         # ", dir='"
    out = out + render_unmodeled(ud, False, fresh)      # detached: a fresh ambient renderer
    out = out + [39, 41]                                # "')"
    return out
    # impl-end


def render_atom(k: int, u: int, v: int, wrap: bool,
                reg: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(is_atom(k, u, v))
    Requires(Acc(list_pred(reg)))
    Requires(MustTerminate(12))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(Acc(list_pred(reg)))
    # ONE operand slot, rendered BY THIS RENDERER: the operand's text at the
    # configuration it was GIVEN (the parent passes its own `wrap`), and the
    # registry effect that rendering that operand has on the registry it was
    # given. For the unmodelled kind BOTH are uninterpreted, so this obligation
    # can only be discharged by asking the renderer.
    Ensures(ToSeq(Result()) == atom_text(k, u, v, wrap))
    Ensures(ToSeq(reg) == atom_registry(Old(ToSeq(reg)), k, u, v))
    # post-conditions-end
    # impl-start
    if k == 1:
        return render_name(u, reg)
    if k == 0:
        return render_operand(wrap, u, v, reg)
    return render_unmodeled(u, wrap, reg)
    # impl-end


def render_name(c: int, reg: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(is_name(c))
    Requires(Acc(list_pred(reg)))
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(Acc(list_pred(reg)))
    # Rendering a name by THIS renderer has two results at once: the name's text,
    # and the name entered in this renderer's registry. Neither may be dropped.
    Ensures(ToSeq(Result()) == lit_name(c))
    Ensures(ToSeq(reg) == registered(Old(ToSeq(reg)), c))
    # post-conditions-end
    # impl-start
    if not (c in reg):
        reg.append(c)
    return [c]
    # impl-end


def render_operand(wrap: bool, p: int, q: int, reg: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(p >= 0 and q >= 2 and coprime(p, q))
    Requires(Acc(list_pred(reg)))
    Requires(MustTerminate(8))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(Acc(list_pred(reg)))
    # The operand is rendered under the configuration it is GIVEN — the caller
    # passes its own `wrap`, so the operand text tracks the parent's setting.
    Ensures(ToSeq(Result()) == render_rational(wrap, p, q))
    # A fractional operand is not a name: rendering it leaves the registry alone,
    # so a compound's registry growth is attributable to its other slots.
    Ensures(ToSeq(reg) == Old(ToSeq(reg)))
    # post-conditions-end
    # impl-start
    if wrap:
        return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))
    return materialize(digits(p)) + [47] + materialize(digits(q))
    # impl-end


def materialize(s: PSeq[int]) -> List[int]:
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == s)
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(s):
        # invariants-start
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(s))
        Invariant(ToSeq(out) == s.take(i))
        Invariant(MustTerminate(len(s) - i + 1))
        # invariants-end
        out = out + [s[i]]
        Assert(s.take(i) + PSeq(s[i]) == s.take(i + 1))
        i = i + 1
    Assert(s.take(len(s)) == s)
    return out
    # impl-end
