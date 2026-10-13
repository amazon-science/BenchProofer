"""Twin-artifact model for django__django-14771.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A development server, when it relaunches itself in a child process, must
  reconstruct the command line that started it so the child runs under the
  same interpreter configuration as the parent. Two kinds of interpreter-level
  options carried on the original command line have to be forwarded.

  After the interpreter path and the warning options, when the running
  interpreter is the reference C implementation, the reconstruction must also
  forward every interpreter implementation option that was supplied, in the
  order supplied. Each such option is a (name, value) pair and is forwarded as
  a single token built from the option flag and the name; when the value is the
  boolean-present sentinel (the option was given with no value) the token is
  just flag+name, and otherwise the token is flag+name+'='+value. When the
  running interpreter is NOT the reference C implementation, no such options are
  forwarded (the empty list). These forwarded option tokens are inserted into
  the leading arguments before the rest of the command line is appended, so
  they precede the entry script / module name and the program arguments in
  every reconstruction shape.

  The remaining reconstruction is unchanged: a module launch ('-m PACKAGE')
  re-invokes that package as a module followed by the program arguments; a
  plain launch whose entry script exists appends the whole argument vector; a
  launch whose entry script is gone takes a platform-specific recovery path
  represented abstractly here.

Strings are modelled as ``PSeq[int]`` of Unicode code points and the argument
vector / option lists as ``PSeq[PSeq[int]]`` of their elements (Nagini bans
``str`` indexing). The implementation-option pairs are carried by three
index-aligned pure sequences: the option NAMES ``opt_keys``, a per-option
boolean ``opt_is_flag`` (true iff the value is the present-with-no-value
sentinel), and the option VALUES ``opt_vals`` (meaningful only where
``opt_is_flag`` is false). All inputs are immutable pure-sequence values
(read-only inputs -- pure values cannot be mutated, so directive-5 read-only
safety holds by construction). The forwarded-option token list is modelled
deeply by the front-recursive pure fold ``option_tokens`` (one token per
option, per the flag/value rule above); no callee is axiomatized -- the
forwarding that the change is about is spelled out, not hidden behind an axiom,
and is validated against its real runtime semantics out-of-band by
axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The option-forwarding rule -- "on the reference
# interpreter, each supplied (name, value) implementation option becomes a
# flag+name token, or flag+name+'='+value when a value is present" -- and the
# guard that no options are forwarded on a non-reference interpreter are
# modelled deeply by `option_tokens` / `is_reference_impl` below; they are
# validated against the real interpreter-option and implementation-identity
# runtime semantics out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
@Pure
def dash_x() -> PSeq[int]:
    # The implementation-option flag '-X'.
    return PSeq(45, 88)


@Pure
def eq() -> PSeq[int]:
    # The name/value separator '='.
    return PSeq(61)


@Pure
def dash_m() -> PSeq[int]:
    # The module-execution flag '-m'.
    return PSeq(45, 109)


@Pure
def windows_recovery() -> PSeq[PSeq[int]]:
    # Abstract sentinel for the unchanged platform-specific recovery path taken
    # when the entry script no longer exists. Distinct from any normally-built
    # argument vector (it carries the single recovery marker element [0]).
    return PSeq(PSeq(0))


@Pure
def is_module_launch(package_reported: bool, launch_package: PSeq[int]) -> bool:
    """A module launch is detected exactly when a launch package is reported
    and its name is non-empty (deep model of the unchanged module-launch
    predicate)."""
    return package_reported and len(launch_package) > 0


@Pure
def option_token(key: PSeq[int], is_flag: bool, val: PSeq[int]) -> PSeq[int]:
    """The single token forwarded for one implementation option (name, value):
    flag+name when the value is the present-with-no-value sentinel, else
    flag+name+'='+value."""
    if is_flag:
        return dash_x() + key
    return dash_x() + key + eq() + val


@Pure
def option_tokens(keys: PSeq[PSeq[int]],
                  flags: PSeq[bool],
                  vals: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The forwarded implementation-option tokens, one per option, in order.
    Front-recursive so a single unfold is available to callers per step."""
    Requires(len(keys) == len(flags) and len(flags) == len(vals))
    if len(keys) == 0:
        return PSeq(PSeq(0)).take(0)
    return PSeq(option_token(keys[0], flags[0], vals[0])) \
        + option_tokens(keys.drop(1), flags.drop(1), vals.drop(1))
# pure-end


def child_arguments(prefix: PSeq[PSeq[int]],
                    is_reference_impl: bool,
                    opt_keys: PSeq[PSeq[int]],
                    opt_is_flag: PSeq[bool],
                    opt_vals: PSeq[PSeq[int]],
                    package_reported: bool,
                    launch_package: PSeq[int],
                    argv: PSeq[PSeq[int]],
                    script_exists: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The three index-aligned option sequences describe the same options.
    Requires(len(opt_keys) == len(opt_is_flag)
             and len(opt_is_flag) == len(opt_vals))
    # The argument vector always carries at least the entry script element.
    Requires(len(argv) >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The forwarded implementation-option tokens: on the reference interpreter,
    # one token per supplied option per the flag/value rule, in order; on any
    # other interpreter, none. Inserted into the leading arguments, before the
    # rest of the command line, in every reconstruction shape.
    # (A) Module launch: leading args (+ forwarded options) then the module
    # flag, the launched package ITSELF, then the program arguments.
    Ensures(Implies(is_module_launch(package_reported, launch_package),
                    Result() == prefix
                    + (option_tokens(opt_keys, opt_is_flag, opt_vals)
                       if is_reference_impl else PSeq(PSeq(0)).take(0))
                    + PSeq(dash_m(), launch_package)
                    + argv.drop(1)))
    # (B) Not a module launch, entry script present: leading args (+ forwarded
    # options) then the whole argument vector unchanged (entry script included).
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and script_exists,
                    Result() == prefix
                    + (option_tokens(opt_keys, opt_is_flag, opt_vals)
                       if is_reference_impl else PSeq(PSeq(0)).take(0))
                    + argv))
    # (C) Not a module launch, entry script absent: the unchanged recovery path.
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and not script_exists,
                    Result() == windows_recovery()))
    # post-conditions-end
    # impl-start
    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    options = empty
    if is_reference_impl:
        i = len(opt_keys)
        while i > 0:
            # invariants-start
            Invariant(0 <= i and i <= len(opt_keys))
            Invariant(len(opt_keys) == len(opt_is_flag)
                      and len(opt_is_flag) == len(opt_vals))
            Invariant(options == option_tokens(opt_keys.drop(i),
                                                opt_is_flag.drop(i),
                                                opt_vals.drop(i)))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
                               opt_vals[i - 1])
            options = PSeq(tok) + options
            i = i - 1
    leading = prefix + options
    if package_reported and len(launch_package) > 0:
        return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return leading + argv
    # impl-end
