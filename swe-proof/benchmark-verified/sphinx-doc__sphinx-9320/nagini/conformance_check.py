#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9320 (nagini).

SHADOW
------
The three impl regions of `model.py`, copied VERBATIM with only the contract
calls removed. Nothing is renamed, reordered or "simplified": the bodies of
`validate_strict`, `validate_path_allowing_empty` and `abort_on_empty_reprompt`
below are character-for-character the text between each `# impl-start` /
`# impl-end` marker (checked by re-extracting both regions and comparing). The
`@Pure` helper `is_empty` from the module-level pure region is copied too; the
impl regions do not call it (it is contract-side), so it serves here only as an
internal cross-check of the abort leg.

The two `@ContractOnly` axiom callees have no body to copy, so per the G-CONF
contract they call the REAL repo callees they axiomatize (mapping.md section 1):

    expand_home(x)         ->  quickstart.path.expanduser   (os.path.expanduser;
                               the binding `from os import path` at
                               quickstart.py:17, called at quickstart.py:92)
    expand_home_value(x)   ->  the SAME quickstart.path.expanduser, in the
                               value-producing form an impl region can hold (its
                               Ensures ties it to expand_home)
    path_is_dir(x)         ->  quickstart.path.isdir        (os.path.isdir,
                               called at quickstart.py:93)

They are reached through the patched module's own `path` attribute, so the
axioms are exercised against exactly the objects the patched code calls rather
than assumed.

ORACLE
------
The REAL patched repo functions are CALLED, not transliterated -- all three need
nothing more than a `str` and a filesystem, so there is no reason to retype them
(a reimplementation would test this script's reading of the repo instead of the
repo itself):

    validate_strict              ->  quickstart.is_path            (:91-95)
    validate_path_allowing_empty ->  quickstart.is_path_or_empty   (added by
                                     patch.diff between :95 and :98)
    abort_on_empty_reprompt      ->  the real `ask_user` re-prompt loop
                                     (:218-228), DRIVEN in-process. The gold
                                     patch's second hunk only swaps the
                                     validator argument at :226, so that hunk is
                                     observable ONLY through the loop. The loop
                                     is entered by making `os.path.isfile`
                                     report an existing conf.py exactly once
                                     (the same lever the F2P test
                                     `test_exits_when_existing_confpy` pulls)
                                     and `quickstart.term_input` return the
                                     generated response; the loop's own
                                     `path.isdir` is left REAL, so the validator
                                     does real filesystem work. `d['path']` is
                                     preseeded so the first prompt reached IS the
                                     re-prompt. The outcome is read off as abort
                                     (`SystemExit` from :228 `sys.exit(1)`),
                                     rejected (`do_prompt` re-issues the SAME
                                     re-prompt after a `ValidationError`), or
                                     continue (any later prompt).

The gate applies patch.diff to /testbed before this script runs, so each of
these is the patched object; `main` refuses to run (exit 2) if
`is_path_or_empty` is absent, so a silently-unapplied patch cannot pass.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
The model carries a response as `List[int]` of Unicode code points (Nagini bans
`str` indexing) and its specification as `PSeq[int]` via `ToSeq`; the real
functions want `str`. The bridge is the code-point bijection
`s[k] <-> ord(s[k])`, so `''` <-> `[]`. Generation happens over `str` -- every
`str` lowers to a Requires-satisfying `List[int]`, since each precondition is
just `Acc(list_pred(x), 1/2)`, a readable list -- and each input is lowered per
call; shadow results are lifted back to `str` before comparison. The `PSeq` shim
supplies the carrier operations the regions use and `ToSeq` materializes a list
as one. A model `ValidationRejected` is compared against a real
`ValidationError` (mapping.md section 2).

Two further bridge facts, both read off the repo rather than assumed:

  * `do_prompt` strips the response before handing it to the validator
    (`x = term_input(prompt).strip()`, quickstart.py:109), and refinement.md C1
    abstracts `do_prompt` to "the value its validator accepts". So on the abort
    leg the model's `x` denotes the VALIDATOR'S ARGUMENT, and the bridge for
    that leg is `raw -> raw.strip()`: the real loop is driven with the raw
    response and the shadow is run on its stripped form. No input is dropped by
    this; it only puts the two sides at the same point in the pipeline. (The
    `default` argument at :226 is `''`, which is falsy, so the :110-111
    default-substitution branch never fires and needs no bridging.)
  * `os.path.expanduser` is NOT total: on a `~`-prefixed response containing a
    NUL byte or a lone surrogate it raises `ValueError` / `UnicodeEncodeError`
    out of `pwd.getpwnam`, which `do_prompt`'s `except ValidationError` does not
    catch. Such an outcome is recorded as a third class, `('error', <type>)`, on
    BOTH sides rather than excluded from the domain: the shadow reaches the same
    real callee at the same point, so the two sides agree there and the inputs
    stay in the generated space. (That the `@Pure @ContractOnly expand_home`
    axiom is declared total over `Requires(True)` while the real callee can
    raise is an axiom-totality observation for G-AX, not a shadow/oracle
    disagreement; it is noted in mapping.md's `## G-CONF` section.)

LEGS
----
Each modeled function's observable outcome is compared per leg, so the report
names precisely which one diverges:

  * ROUTING -- accepted vs rejected vs errored. This is the leg the gold patch
    changes (the empty response: rejected before, accepted after).
  * VALUE   -- the string an acceptance returns. The real `is_path` REBINDS its
    argument before returning it (`x = path.expanduser(x)` at quickstart.py:92,
    then `return x` at :95), so an acceptance returns the HOME-EXPANDED response,
    not the response as typed. The model's impl mirrors that rebind
    (`expanded = expand_home_value(x)` ... `return expanded`) and its
    postcondition states `ToSeq(Result()) == expand_home(ToSeq(x))`, so under the
    documented bridge the model's returned value must equal the expansion of the
    response. (`expanduser('')` is `''`, so the empty response is unaffected and
    the abort affordance is independent of this leg.)
  * ABORT   -- abort / continue / rejected out of the real re-prompt loop.

INPUTS
------
>= 1e5 Requires-satisfying inputs: boundary cases first (the empty response --
the F2P shape; every impl branch taken: empty-accept, non-empty accept,
non-empty reject; real existing directories, tilde forms, whitespace, NUL,
surrogate and astral code points) then seeded fuzz to fill the count. The run
aborts with exit 2 if any impl branch went unexercised, so a green result cannot
come from a generator that misses the branch the gold patch changed. Pinned
seed: 9320 (recorded in mapping.md under `## G-CONF`).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib only.
"""
import contextlib
import io
import json
import os
import random
import sys
import tempfile

SEED = 9320
N_FUZZ = 100000
MAX_SHOWN = 6


# --- PSeq shim: the immutable-sequence carrier the regions use ---------------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- the type bridge (mapping.md section 2) ----------------------------------

def to_codepoints(s):
    """str -> List[int] (the model carrier)."""
    return [ord(ch) for ch in s]


def from_codepoints(x):
    """List[int] / PSeq[int] -> str (the repo reality)."""
    return "".join(chr(c) for c in x)


# --- model.py's exception, and the REAL callees its axioms stand for ---------

class ValidationRejected(Exception):
    """model.py's stand-in for the repo's ValidationError."""


_QS = None


def _qs():
    global _QS
    if _QS is None:
        from sphinx.cmd import quickstart
        _QS = quickstart
    return _QS


def expand_home(x):
    """@ContractOnly expand_home -> the REAL os.path.expanduser, reached through
    the patched module's own `path` binding (quickstart.py:17, called at :92)."""
    return ToSeq(to_codepoints(_qs().path.expanduser(from_codepoints(x))))


def expand_home_value(x):
    """@ContractOnly expand_home_value -> the same REAL os.path.expanduser as
    `expand_home`, in the value-producing form an impl region can hold. Its
    Ensures ties it to expand_home, so it resolves to the same callee."""
    return to_codepoints(_qs().path.expanduser(from_codepoints(x)))


def path_is_dir(x):
    """@ContractOnly path_is_dir -> the REAL os.path.isdir, reached through the
    patched module's own `path` binding (called at quickstart.py:93)."""
    return _qs().path.isdir(from_codepoints(x))


# --- model.py pure region, contracts stripped (verbatim) ---------------------

def is_empty(x):
    return len(x) == 0


# --- model.py impl regions, contracts stripped (verbatim) -------------------

def validate_strict(x):
    # impl-start
    expanded = expand_home_value(x)
    if not path_is_dir(ToSeq(expanded)):
        raise ValidationRejected()
    return expanded
    # impl-end


def validate_path_allowing_empty(x):
    # impl-start
    if len(x) == 0:
        result = list(x)  # type: List[int]
        return result
    return validate_strict(x)
    # impl-end


def abort_on_empty_reprompt(x):
    # impl-start
    validated = validate_path_allowing_empty(x)
    aborts = len(validated) == 0
    return aborts
    # impl-end


# --- shadow outcomes, in the comparable encoding -----------------------------

def shadow_validator(fn, s):
    """('ok', returned_str) accepted / ('reject',) / ('error', type)."""
    try:
        return ('ok', from_codepoints(fn(to_codepoints(s))))
    except ValidationRejected:
        return ('reject',)
    except (ValueError, UnicodeError) as exc:
        return ('error', type(exc).__name__)


def shadow_abort(s):
    """The shadow's view of the loop outcome."""
    try:
        return 'abort' if abort_on_empty_reprompt(to_codepoints(s)) else 'continue'
    except ValidationRejected:
        return 'rejected'
    except (ValueError, UnicodeError) as exc:
        return 'error:' + type(exc).__name__


# --- oracle outcomes: the REAL patched functions ----------------------------

def oracle_validator(fn, s):
    try:
        return ('ok', fn(s))
    except _qs().ValidationError:
        return ('reject',)
    except (ValueError, UnicodeError) as exc:
        return ('error', type(exc).__name__)


REPROMPT_MARK = 'Please enter a new root path'


class _PromptReached(Exception):
    def __init__(self, prompt):
        Exception.__init__(self, prompt)
        self.prompt = prompt


def oracle_abort(raw, preset_path):
    """Drive the REAL patched `ask_user` re-prompt loop (quickstart.py:218-228).

    `preset_path` seeds d['path'] so the first prompt reached IS the re-prompt.
    `os.path.isfile` reports an existing conf.py exactly once, so the loop is
    entered and then left; `path.isdir` stays REAL. The second request for input
    ends the drive: the same re-prompt again means the validator rejected, any
    other prompt means the loop was left normally.
    """
    qs = _qs()
    ospath = qs.path
    calls = [0]

    def mock_input(prompt):
        calls[0] += 1
        if calls[0] == 1:
            return raw
        raise _PromptReached(prompt)

    seen_conf_py = [False]

    def mock_isfile(_p):
        if not seen_conf_py[0]:
            seen_conf_py[0] = True
            return True
        return False

    old_input = qs.term_input
    old_isfile = ospath.isfile
    qs.term_input = mock_input
    ospath.isfile = mock_isfile
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                qs.ask_user({'path': preset_path})
                return 'fellthrough'
            except SystemExit:
                return 'abort'
            except _PromptReached as reached:
                return ('rejected' if REPROMPT_MARK in reached.prompt
                        else 'continue')
            except (ValueError, UnicodeError) as exc:
                return 'error:' + type(exc).__name__
    finally:
        qs.term_input = old_input
        ospath.isfile = old_isfile


# --- input domain -----------------------------------------------------------

def boundary_inputs(existing):
    """Boundary cases: the F2P shape first, then every impl branch, then the
    awkward corners. `existing` holds real directories built for this run."""
    cases = [
        "",                     # the F2P shape: empty re-prompt -> abort
        " ", "  ", "\t", "\n",  # non-empty, not a directory
        ".", "..", "/", "//", "/.",
        "~", "~/", "~//", "~/.", "~root", "~root/", "~nouser_zzz",
        "~nouser_zzz/sub", "~/..", "~/../root",
        "/tmp", "/etc", "/nonexistent_zzz_9320", "relative/path",
        "a", "x" * 64, "conf.py", "./", ".//",
        "\x00", "a\x00b", "~\x00", "~a\x00b", "~/\x00",
        "\x85", "\xa0", "\u2028", "\u3000",
        "\ud800", "~\ud800", "~/\ud800",
        "\U0001F600", "~\U0001F600", "e\u0301", "r\xe9ns",
        "\u65e5\u672c", "C:\\proj", "name with spaces",
    ]
    for d in existing:
        cases.append(d)
        cases.append(d + "/")
        cases.append(d + "/nonexistent_zzz")
    return cases


def fuzz_inputs(n, rng, existing):
    """Seeded fuzz over the same space: real directories and their
    neighbourhoods, tilde forms, and free code-point soup. The empty response is
    drawn often so the branch the gold patch changed stays hot."""
    alphabet = list("abcZ09 ./~\\:;-_%") + [
        "\t", "\x00", "\x85", "\xa0", "\u2028", "\u3000",
        "\ud800", "\U0001F600", "\xe9", "\u2022",
    ]
    tildes = ["~", "~/", "~root", "~root/", "~nouser_zzz"]
    for _ in range(n):
        roll = rng.random()
        if roll < 0.12:
            yield ""
        elif roll < 0.34:
            base = rng.choice(existing)
            tail = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 4)))
            yield base if rng.random() < 0.5 else os.path.join(base, tail)
        elif roll < 0.50:
            tail = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))
            yield rng.choice(tildes) + tail
        else:
            k = rng.randint(0, 16)
            yield "".join(rng.choice(alphabet) for _ in range(k))


# --- differential driver ----------------------------------------------------

LEGS = ["strict_routing", "strict_value",
        "lenient_routing", "lenient_value", "abort"]


def main():
    qs = _qs()
    if not hasattr(qs, "is_path_or_empty"):
        print("G-CONF ERROR: patched sphinx.cmd.quickstart has no "
              "is_path_or_empty -- the gold patch is not applied")
        print(json.dumps({"error": "gold patch not applied"}))
        return 2

    rng = random.Random(SEED)
    counts = dict((k, 0) for k in LEGS)
    diffs = dict((k, []) for k in LEGS)
    branches = {"empty_accept": 0, "nonempty_accept": 0, "nonempty_reject": 0}
    checked = 0

    with tempfile.TemporaryDirectory() as tmp:
        sub = os.path.join(tmp, "sub")
        os.mkdir(sub)
        deep = os.path.join(sub, "deeper")
        os.mkdir(deep)
        existing = [tmp, sub, deep, os.getcwd(),
                    os.path.expanduser("~"), "/tmp"]
        preset = tmp  # seeds d['path'] so the first prompt IS the re-prompt

        def record(leg, s, shadow, oracle):
            counts[leg] += 1
            if shadow != oracle and len(diffs[leg]) < MAX_SHOWN:
                diffs[leg].append((s, shadow, oracle))

        def check(s):
            # --- validate_strict <-> is_path (:91-95) ---
            sh = shadow_validator(validate_strict, s)
            orc = oracle_validator(qs.is_path, s)
            record("strict_routing", s, sh[0], orc[0])
            if sh[0] == 'ok' and orc[0] == 'ok':
                record("strict_value", s, sh, orc)

            # --- validate_path_allowing_empty <-> is_path_or_empty ---
            sh = shadow_validator(validate_path_allowing_empty, s)
            orc = oracle_validator(qs.is_path_or_empty, s)
            record("lenient_routing", s, sh[0], orc[0])
            if sh[0] == 'ok' and orc[0] == 'ok':
                record("lenient_value", s, sh, orc)
            if sh[0] == 'ok':
                branches["empty_accept" if s == "" else "nonempty_accept"] += 1
            elif sh[0] == 'reject':
                branches["nonempty_reject"] += 1

            # --- abort_on_empty_reprompt <-> the real ask_user loop ---
            # bridge: do_prompt strips (:109) before calling the validator, and
            # the model's x denotes the validator's argument (refinement.md C1).
            stripped = s.strip()
            sh_a = shadow_abort(stripped)
            orc_a = oracle_abort(s, preset)
            record("abort", s, sh_a, orc_a)
            # internal cross-check of the abort leg against the pure predicate
            if sh_a in ('abort', 'continue'):
                expected = ('abort' if is_empty(ToSeq(to_codepoints(stripped)))
                            else 'continue')
                if sh_a != expected:
                    record("abort", s, sh_a, "INTERNAL:" + expected)

        boundary = boundary_inputs(existing)
        for s in boundary:
            check(s)
            checked += 1
        for s in fuzz_inputs(N_FUZZ, rng, existing):
            check(s)
            checked += 1

    total_diffs = sum(len(v) for v in diffs.values())
    diverging = [k for k in LEGS if diffs[k]]

    for leg in diverging:
        print("DISAGREEMENT on leg %s (%d shown):" % (leg, len(diffs[leg])))
        for s, shadow, oracle in diffs[leg]:
            print("  input=%r codepoints=%r" % (s, to_codepoints(s)))
            print("    shadow (model.py impl region, verbatim) = %r" % (shadow,))
            print("    oracle (real patched repo function)     = %r" % (oracle,))

    for name in sorted(branches):
        if branches[name] == 0:
            print("G-CONF ERROR: impl branch %s never exercised" % name)
            print(json.dumps({"error": "branch %s unexercised" % name}))
            return 2

    summary = {
        "checked": checked,
        "seed": SEED,
        "shadow": "direct (contract-stripped impl region, verbatim)",
        "oracle": "called (is_path, is_path_or_empty, ask_user re-prompt loop)",
        "legs_checked": counts,
        "branches": branches,
        "diverging_legs": diverging,
        "disagreements": total_diffs,
    }

    if total_diffs:
        routing_clean = not [k for k in diverging
                            if k.endswith("routing") or k == "abort"]
        print("G-CONF FAIL: the verbatim shadow of model.py's impl regions "
              "disagrees with the real patched repo function on leg(s) %s over "
              "%d inputs (seed=%d). Routing/abort legs: %s."
              % (", ".join(diverging), checked, SEED,
                 "clean" if routing_clean else "DIVERGING (see above)"))
        print(json.dumps(summary))
        return 1

    print("G-CONF OK: the verbatim shadow of model.py's impl regions agrees "
          "with the real patched is_path / is_path_or_empty / ask_user "
          "re-prompt loop on %d inputs (%d boundary + %d fuzz, seed %d); "
          "0 disagreements." % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
