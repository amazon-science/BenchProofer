"""Twin-artifact model for sphinx-doc__sphinx-8459.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documentation step records, into a per-object mapping, the rendered
  annotation of each parameter of a callable (and of its return), so a later
  rendering pass can present each parameter's type. Each parameter that carries
  an annotation contributes one entry: the parameter's name maps to the
  rendered form of that parameter's resolved annotation; a parameter with no
  annotation contributes nothing. The return annotation, when present, is
  recorded under a single reserved name slot.

  The behaviour pinned here is HOW an annotation source is resolved before it is
  recorded. The step is configured with a user-supplied alias map from an
  annotation source token to the token it should resolve to. The resolution
  honours that map:

    * when the alias map governs an annotation source token (the token is a key
      of the map), the recorded annotation is the alias's target token — the
      user-chosen name is preserved exactly as configured;

    * when the alias map does NOT govern the source token, the recorded
      annotation is the token's own underlying expansion (the form the source
      resolves to with no alias overrides).

  The consequence that matters: a parameter whose annotation source is an alias
  the user configured is recorded under the configured alias, NOT under the
  expanded underlying form — and this holds whether or not the surrounding
  rendering mode would otherwise expand it. A recorded mapping that ignores the
  configured alias map and expands every source token is rejected.

Modelling choices (Nagini fragment):
  * A callable's parameters and return are modelled as explicit named slots: two
    parameters (name token + annotation source token + has-annotation flag each)
    and a return (source token + has flag). The real step records each parameter
    independently, so a small constant number of named slots faithfully captures
    the per-slot recording without a loop; the tested callable has exactly two
    parameters and a return. Distinct names / annotation strings are interned as
    distinct ``int`` tokens; only identity and mapping membership are observed
    (mapping.md §2), so integer identity is faithful.
  * The configured alias map is a ``Dict[int, int]`` (source token -> resolved
    token). The recorded mapping is a ``Dict[int, int]`` (name token -> recorded
    annotation token), with the return recorded under the reserved key
    ``KEY_RETURN()``.
  * ``resolve(tok, aliases)`` is the deep model of how one source token is
    resolved given the alias map: the alias's target when the map governs it,
    otherwise the token's underlying expansion ``expand(tok)``. ``resolve`` /
    ``expand`` model the underlying annotation resolver and are validated ==
    the real resolution behaviour out-of-band by axiom_check.py (G-AX); they
    are NOT consumed axioms.

The alias map is read, not mutated, so it is held at fractional permission
(required AND ensured); the freshly built recorded mapping is returned at full
permission. No string indexing is used (Nagini bans it). Dict access is guarded
by an explicit membership test before subscription. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The alias-honouring annotation resolution is modelled
# DEEPLY by `resolve` / `expand` in the pure region; the proof never depends on
# a `@ContractOnly` contract. The underlying resolver is the A-reference that
# axiom_check.py (G-AX) validates the deep model against, not a consumed axiom.
# axioms-end


# pure-start
@Pure
def KEY_RETURN() -> int:
    # The reserved name slot under which the return annotation is recorded.
    # Distinct from every parameter-name token (pinned by a precondition).
    return -1


@Pure
def expand(tok: int) -> int:
    """The underlying expansion of an annotation source token when NO alias
    governs it: the form the source resolves to with no alias overrides. Modeled
    deeply (the per-token expansion); validated == the real no-alias resolver by
    axiom_check.py (G-AX). Encoded so an aliased source and its expansion are
    DIFFERENT tokens unless the source is its own underlying type."""
    return tok + 1000


@Pure
def resolve(tok: int, aliases: Dict[int, int]) -> int:
    """The recorded annotation token for one source token under the alias map:
    the alias's target when the map governs the token, otherwise the token's own
    underlying expansion. This is the alias-honouring resolution the recorded
    annotation must reflect."""
    Requires(Acc(dict_pred(aliases), 1 / 4))
    if tok in aliases:
        return aliases[tok]
    return expand(tok)
# pure-end


def record_annotations(name0: int, raw0: int, has0: bool,
                       name1: int, raw1: int, has1: bool,
                       aliases: Dict[int, int],
                       ret_raw: int, ret_has: bool) -> Dict[int, int]:
    # pre-conditions-start
    # The alias map is read, not mutated: fractional permission.
    Requires(Acc(dict_pred(aliases), 1 / 2))
    # Parameter names are distinct from each other and from the reserved return
    # slot, so each parameter's recorded entry is independent of the others and
    # of the return entry (the real mapping is keyed by distinct names).
    Requires(name0 != name1)
    Requires(name0 != KEY_RETURN())
    Requires(name1 != KEY_RETURN())
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(aliases), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    # (1) Each annotated parameter contributes one entry: its name maps to the
    #     ALIAS-RESOLVED annotation token `resolve(raw, aliases)` — the
    #     configured alias when the map governs the source, else its underlying
    #     expansion. An implementation that ignores the alias map (records the
    #     expansion regardless) violates this whenever an alias governs the
    #     source and differs from the expansion.
    Ensures(Implies(has0,
                    name0 in Result()
                    and Result()[name0] == resolve(raw0, aliases)))
    Ensures(Implies(has1,
                    name1 in Result()
                    and Result()[name1] == resolve(raw1, aliases)))
    # (2) A parameter with no annotation contributes no entry under its name.
    Ensures(Implies(not has0, not (name0 in Result())))
    Ensures(Implies(not has1, not (name1 in Result())))
    # (3) The return annotation, when present, is recorded under the reserved
    #     slot, also alias-resolved; when absent, the reserved slot is unset.
    Ensures(Implies(ret_has,
                    KEY_RETURN() in Result()
                    and Result()[KEY_RETURN()] == resolve(ret_raw, aliases)))
    Ensures(Implies(not ret_has, not (KEY_RETURN() in Result())))
    # post-conditions-end
    # impl-start
    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    return annotation
    # impl-end
