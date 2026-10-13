"""Twin-artifact model for django__django-14315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database client builds a process environment mapping for the external
  shell it launches. Two related observations are pinned.

  (1) The environment a backend reports for a command. The mapping is built
      from the connection settings; when no environment variable is required
      the built mapping is empty. The reported value normalises an empty
      mapping to ``None``: an empty mapping and ``None`` are indistinguishable
      to the caller, while a non-empty mapping is reported verbatim.

  (2) The effective environment handed to the launched subprocess. Given the
      mapping reported for the command (which may be ``None`` or empty) and the
      current process environment ``os.environ``, the effective environment is
      ``None`` whenever the command mapping is ``None`` or empty -- so the
      subprocess inherits ``os.environ`` rather than receiving an empty
      environment. When the command mapping is non-empty the effective
      environment is the merge of ``os.environ`` with the command mapping, the
      command mapping's entries taking precedence.

  The consequence that matters: an empty command mapping must yield ``None``
  (the subprocess then inherits ``os.environ``), never an empty mapping (which
  would launch the subprocess with no inherited variables at all).

Modelling choices (Nagini fragment):
  * An environment mapping is a ``Dict[int, int]`` from variable-name token to
    value token; only membership, per-key value, and emptiness are observed,
    so integer identity is the faithful carrier (mapping.md §2).
  * "absent environment" (the ``None`` the subprocess inherits ``os.environ``
    for) is carried by an ``Optional[Dict[int, int]]`` whose ``None`` case is
    the distinguished value.
  * The merge of two mappings (an unchanged standard mapping-unpacking the
    code invokes) is the single callee ``env_merge``; its standard semantics
    are validated against real Python out-of-band (axiom_check.py, G-AX).

Building the environment for the launched subprocess is a bounded,
straight-line computation: each operation MUST terminate and deliver its
value (a total-correctness obligation, carried as MustTerminate in the
preconditions). Nagini verifies partial correctness by default, so without
the obligation an implementation that diverges would satisfy every value
postcondition only vacuously and would hang the shell launch forever.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def env_merge(base: Dict[int, int], overlay: Dict[int, int]) -> Dict[int, int]:
    """Standard mapping merge ``{**base, **overlay}`` (an unchanged callee the
    code invokes): a fresh non-empty mapping holding every key of either input,
    with ``overlay``'s value winning on a shared key. Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(Acc(dict_pred(overlay), 1 / 2))
    # The real mapping-unpacking merge is a single bounded primitive step; the
    # strictly smaller measure (1 < 2) lets a contracted caller holding
    # MustTerminate(2) invoke it without leaking its own obligation.
    Requires(MustTerminate(1))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(overlay), 1 / 2))
    Ensures(len(base) == Old(len(base)))
    Ensures(len(overlay) == Old(len(overlay)))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every key of overlay is present with overlay's value (overlay wins).
    Ensures(Forall(int, lambda k: (Implies(k in overlay,
                                            (k in Result()) and Result()[k] == overlay[k]),
                                    [[k in overlay], [k in Result()]])))
    # Every key of base that overlay does not override keeps base's value.
    Ensures(Forall(int, lambda k: (Implies((k in base) and not (k in overlay),
                                            (k in Result()) and Result()[k] == base[k]),
                                    [[k in base], [k in Result()]])))
    # No spurious keys: the merge holds only keys of one of the inputs.
    Ensures(Forall(int, lambda k: (Implies(k in Result(), (k in base) or (k in overlay)),
                                    [[k in Result()]])))
# axioms-end


# pure-start
# No pure helpers: the normalisation/merge selection is the behaviour under
# specification and is spelled out in the impl regions; the unchanged mapping
# merge it composes is the env_merge callee (axioms region).
# pure-end


def normalized_environment(env: Dict[int, int]) -> Optional[Dict[int, int]]:
    # pre-conditions-start
    Requires(Acc(dict_pred(env), 1 / 2))
    # TERMINATION: reporting the command environment is bounded straight-line
    # work that MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body would satisfy the value
    # postconditions only vacuously yet never deliver the reported mapping.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(env), 1 / 2))
    # An empty mapping is normalised to None ...
    Ensures(Implies(len(env) == 0, Result() is None))
    # ... and a non-empty mapping is reported verbatim (the same mapping).
    Ensures(Implies(len(env) > 0, Result() is env))
    # post-conditions-end
    # impl-start
    return env
    # impl-end


def effective_environment(env: Optional[Dict[int, int]],
                          base: Dict[int, int]) -> Optional[Dict[int, int]]:
    # pre-conditions-start
    Requires(Implies(env is not None, Acc(dict_pred(env), 1 / 2)))
    Requires(Acc(dict_pred(base), 1 / 2))
    # TERMINATION: computing the effective environment for the subprocess is
    # bounded straight-line work (a None/emptiness decision plus at most one
    # bounded merge) that MUST actually complete (total correctness). Under
    # partial-correctness semantics a diverging body — e.g. hanging instead of
    # handing the subprocess its environment — would satisfy the value
    # postconditions only vacuously and the shell would never be launched.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(env is not None, Acc(dict_pred(env), 1 / 2)))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Implies(Result() is not None, Acc(dict_pred(Result()))))
    # None (inherit os.environ) exactly when the command mapping is None/empty.
    Ensures(Implies(env is None, Result() is None))
    Ensures(Implies(env is not None and len(env) == 0, Result() is None))
    Ensures(Implies(env is not None and len(env) > 0, Result() is not None))
    # When non-empty, the result is the merge: the command mapping's entries
    # win, and the process environment's other entries are carried through.
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies(k in env,
                                       (k in Result()) and Result()[k] == env[k]),
                               [[k in env], [k in Result()]]))))
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies((k in base) and not (k in env),
                                       (k in Result()) and Result()[k] == base[k]),
                               [[k in base], [k in Result()]]))))
    # No spurious keys: the effective environment holds only keys of the
    # command mapping or of the process environment (the merge adds nothing).
    Ensures(Implies(env is not None and len(env) > 0,
        Forall(int, lambda k: (Implies(k in Result(), (k in env) or (k in base)),
                               [[k in Result()]]))))
    # post-conditions-end
    # impl-start
    if env is None:
        return None
    if len(env) == 0:
        return None
    merged = env_merge(base, env)
    return merged
    # impl-end
