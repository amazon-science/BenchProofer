"""PBT falsification manifest for django__django-13658.

NOT a Nagini module — a record of adversarial cases the runner (swebench_nagini.pbt)
parses. Each SPEC_TEST is a full model.py variant built by region-surgery: ONLY the
text inside the single `# impl-start` / `# impl-end` region is edited, so the frozen
spec (pure region + pre/post-conditions + class/signature decls) is provably untouched
and markers.same_spec holds. The invariants region is NESTED inside the impl region, so
loop invariants may also be reshaped without touching the spec.

Defended surface (model.py):
  build_settings_parser(self: Utility) -> Parser
  - READ-ONLY inputs (fractional permission): self.argv0_basename AND
    self.sys_argv0_basename, both at Acc(...,1/2). => frame-mutation MANDATORY.
  - Frame postconditions (model.py:95-98): both sources returned untouched at 1/2.
  - LOAD-BEARING postcondition (model.py:109):
        ToSeq(Result().prog) == program_name(ToSeq(self.argv0_basename))
    grounded in the utility's OWN first-argument basename (argv0_basename), NEVER the
    ambient sys_argv0_basename. The two sources are allowed to disagree.
  - program_name is a GROUNDED @Pure function of the argument (basename, except the
    bootstrap basename '__main__.py' -> 'python -m django'), fully unfolded — NOT an
    opaque answer-key oracle. There is therefore no *wrong* echo of program_name(...)
    that could verify: echoing it materialized is the cheapest CORRECT impl (the
    positive control covers that). The genuine SPEC-TOO-WEAK risk is sourcing prog
    from the WRONG argument (sys_argv0_basename) — the prepatch behaviour — and the
    wrong-source rival attacks exactly that.

A-reference (meta.deep_model_references): program_name is a deep model of the real
ManagementUtility.__init__ prog_name rule + the argparse explicit-prog adoption. No
@ContractOnly axiom is consumed. AXIOM_TESTS validate the A-reference soundness (real
callee == deep model) and caller-domain containment (every basename the model can pass
is in the rule's domain).
"""
from pathlib import Path

INSTANCE = "django__django-13658"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl body (verbatim from model.py impl region) — the anchor every
# variant edits. This is exactly the text BETWEEN `# impl-start` and `# impl-end`.
# ---------------------------------------------------------------------------
_GOLD_IMPL = '''    parser = Parser()

    # parser's program name := the utility's own computed program name.
    #   prog := program_name(argv0_basename)
    if ToSeq(self.argv0_basename) == bootstrap_name():
        # The bootstrap basename maps to the canonical module-invocation name.
        parser.prog = [112, 121, 116, 104, 111, 110, 32, 45, 109, 32,
                       100, 106, 97, 110, 103, 111]
        Assert(ToSeq(parser.prog) == module_invocation())
    else:
        i = 0
        while i < len(self.argv0_basename):
            # invariants-start
            Invariant(Acc(self.argv0_basename, 1 / 2) and Acc(list_pred(self.argv0_basename), 1 / 2))
            Invariant(ToSeq(self.argv0_basename) == Old(ToSeq(self.argv0_basename)))
            Invariant(Acc(parser.prog) and Acc(list_pred(parser.prog)))
            Invariant(parser is not self)
            Invariant(0 <= i and i <= len(self.argv0_basename))
            Invariant(len(parser.prog) == i)
            Invariant(ToSeq(parser.prog) == ToSeq(self.argv0_basename).take(i))
            # invariants-end
            parser.prog.append(self.argv0_basename[i])
            i = i + 1
        # parser.prog now equals the utility's own first-argument basename,
        # which (not being the bootstrap name) is exactly its program name.
        Assert(ToSeq(self.argv0_basename).take(len(self.argv0_basename)) == ToSeq(self.argv0_basename))
        Assert(ToSeq(parser.prog) == ToSeq(self.argv0_basename))
    return parser'''

# sanity: the anchor must be present exactly once in the base model.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl anchor drifted from model.py"


# === (1) FRAME-MUTATION — MANDATORY (read-only inputs at Acc(...,1/2)) ======
# A rival that WRITES to the read-only input self.argv0_basename. The write
# (append) needs FULL list_pred permission, but the precondition grants only 1/2,
# so the verifier rejects this for INSUFFICIENT PERMISSION — the rejection fires
# at the .append() line, before any value reasoning is reached. The gold body
# (postconditions + invariants) is kept verbatim so the rejection is attributable
# solely to the inserted write, not to a value/frame clause.
_FRAME_MUT = _swap(
    _GOLD_IMPL,
    "    parser = Parser()\n",
    "    parser = Parser()\n"
    "    # ILLEGAL: write to the read-only half-permission input argv0_basename.\n"
    "    self.argv0_basename.append(120)\n",
)

# === (2) WRONG-SOURCE — the prepatch behaviour (SPEC-TOO-WEAK probe) =========
# Derive prog from the AMBIENT source self.sys_argv0_basename instead of the
# utility's own argv0_basename. This is exactly model_prepatch.py. It verifies
# ONLY when the two sources coincide; the postcondition pins prog to
# program_name(ToSeq(self.argv0_basename)), so whenever the sources disagree the
# value-postcond fails. MUST be rejected. Faithful real patch = the *unchanged*
# pre-patch CommandParser(...) (no prog=), which crashes / prints the wrong
# program name in the F2P test (own argv ['django-admin',...] vs mocked
# sys.argv [None,...]) — it does NOT resolve.
_WRONG_SOURCE = _swap(
    _GOLD_IMPL,
    _GOLD_IMPL,
    '''    parser = Parser()

    # WRONG SOURCE: derive prog from the ambient sys_argv0_basename (prepatch).
    i = 0
    while i < len(self.sys_argv0_basename):
        # invariants-start
        Invariant(Acc(self.sys_argv0_basename, 1 / 2) and Acc(list_pred(self.sys_argv0_basename), 1 / 2))
        Invariant(ToSeq(self.sys_argv0_basename) == Old(ToSeq(self.sys_argv0_basename)))
        Invariant(Acc(parser.prog) and Acc(list_pred(parser.prog)))
        Invariant(parser is not self)
        Invariant(0 <= i and i <= len(self.sys_argv0_basename))
        Invariant(len(parser.prog) == i)
        Invariant(ToSeq(parser.prog) == ToSeq(self.sys_argv0_basename).take(i))
        # invariants-end
        parser.prog.append(self.sys_argv0_basename[i])
        i = i + 1
    Assert(ToSeq(self.sys_argv0_basename).take(len(self.sys_argv0_basename)) == ToSeq(self.sys_argv0_basename))
    Assert(ToSeq(parser.prog) == ToSeq(self.sys_argv0_basename))
    return parser''',
)

# === (3) PARTIAL-DOMAIN — drop the bootstrap exception ======================
# Copy argv0_basename verbatim with NO bootstrap-name special case. Correct on
# every basename EXCEPT '__main__.py', where the spec requires the prog be the
# module-invocation name 'python -m django' but this impl yields '__main__.py'.
# So the value-postcond fails on exactly the bootstrap subdomain. MUST be
# rejected. Faithful real patch = prog=os.path.basename(self.argv[0]) WITHOUT the
# `if self.prog_name == '__main__.py'` remap — a `python -m django` invocation
# would report 'usage: __main__.py ...' instead of 'usage: python -m django ...',
# diverging from the documented behaviour the rule encodes; not a faithful fix.
_NO_BOOTSTRAP = _swap(
    _GOLD_IMPL,
    _GOLD_IMPL,
    '''    parser = Parser()

    # PARTIAL-DOMAIN: copy argv0_basename verbatim, OMITTING the bootstrap remap.
    i = 0
    while i < len(self.argv0_basename):
        # invariants-start
        Invariant(Acc(self.argv0_basename, 1 / 2) and Acc(list_pred(self.argv0_basename), 1 / 2))
        Invariant(ToSeq(self.argv0_basename) == Old(ToSeq(self.argv0_basename)))
        Invariant(Acc(parser.prog) and Acc(list_pred(parser.prog)))
        Invariant(parser is not self)
        Invariant(0 <= i and i <= len(self.argv0_basename))
        Invariant(len(parser.prog) == i)
        Invariant(ToSeq(parser.prog) == ToSeq(self.argv0_basename).take(i))
        # invariants-end
        parser.prog.append(self.argv0_basename[i])
        i = i + 1
    Assert(ToSeq(self.argv0_basename).take(len(self.argv0_basename)) == ToSeq(self.argv0_basename))
    Assert(ToSeq(parser.prog) == ToSeq(self.argv0_basename))
    return parser''',
)

# === (4) PARTIAL-DOMAIN (supporting near-miss) — off-by-one truncation =======
# In the non-bootstrap branch, stop one code point short of the end. prog then
# equals argv0_basename minus its last char (and is empty for a 1-char basename),
# != program_name(...) on every non-empty basename. MUST be rejected. Faithful
# real patch = prog=self.prog_name[:-1], an obviously broken program name that
# would print a truncated name in the usage line; does not resolve. (Cheap
# supporting case, but carries a real refinement.)
_OFF_BY_ONE = _swap(
    _GOLD_IMPL,
    "        while i < len(self.argv0_basename):",
    "        while i + 1 < len(self.argv0_basename):",
)

# === (5) POSITIVE CONTROL — structurally-different CORRECT impl (verify) =====
# Branch-reorder: test the NEGATED bootstrap predicate first and swap the two
# arms. Identical proof obligations (the copy-loop invariants and the bootstrap
# Assert are preserved verbatim, just moved between arms), only the executable
# control-flow shape changes. A faithful correct impl MUST verify (else
# SPEC-TOO-STRONG). NOTE: this keeps every gold framing Assert and per-element
# loop invariant (pilot bug #2) and does NOT use forward-append against a
# front-recursive fold (pilot bug #3) — the copy loop is identical to gold.
_POS_CONTROL = _swap(
    _GOLD_IMPL,
    '''    if ToSeq(self.argv0_basename) == bootstrap_name():
        # The bootstrap basename maps to the canonical module-invocation name.
        parser.prog = [112, 121, 116, 104, 111, 110, 32, 45, 109, 32,
                       100, 106, 97, 110, 103, 111]
        Assert(ToSeq(parser.prog) == module_invocation())
    else:
        i = 0
        while i < len(self.argv0_basename):''',
    '''    if ToSeq(self.argv0_basename) != bootstrap_name():
        i = 0
        while i < len(self.argv0_basename):''',
)
# move the bootstrap arm to the end (after the loop+asserts), as the else-branch.
_POS_CONTROL = _swap(
    _POS_CONTROL,
    '''        Assert(ToSeq(self.argv0_basename).take(len(self.argv0_basename)) == ToSeq(self.argv0_basename))
        Assert(ToSeq(parser.prog) == ToSeq(self.argv0_basename))
    return parser''',
    '''        Assert(ToSeq(self.argv0_basename).take(len(self.argv0_basename)) == ToSeq(self.argv0_basename))
        Assert(ToSeq(parser.prog) == ToSeq(self.argv0_basename))
    else:
        # The bootstrap basename maps to the canonical module-invocation name.
        parser.prog = [112, 121, 116, 104, 111, 110, 32, 45, 109, 32,
                       100, 106, 97, 110, 103, 111]
        Assert(ToSeq(parser.prog) == module_invocation())
    return parser''',
)

# === (6) ADMISSIBILITY — a normal F2P-shaped input is accepted (verify) =====
# Straight-line in-region caller (NO nested def — avoids any translation risk,
# pilot bug class). At the top of the impl region we construct a FRESH Utility,
# give BOTH sources the representative F2P own-argv basename ('django-admin' code
# points), and call build_settings_parser(u). Nagini discharges that call against
# the CONTRACT (it does not unfold the body), so the call site must ESTABLISH the
# precondition Acc(...,1/2) on both basenames for this legitimate input — a fresh
# Utility holds full permission, splittable to 1/2. We then assert the
# postcondition holds for the returned parser. If the Requires cannot be
# established for this normal input the precondition is PRECOND-TOO-STRONG. The
# gold body is then run verbatim so the function itself still verifies.
_ADMISS = '''    u = Utility()
    # 'django-admin' as code points for BOTH sources (the F2P own-argv name).
    u.argv0_basename = [100, 106, 97, 110, 103, 111, 45, 97, 100, 109, 105, 110]
    u.sys_argv0_basename = [100, 106, 97, 110, 103, 111, 45, 97, 100, 109, 105, 110]
    admit_parser = build_settings_parser(u)
    Assert(ToSeq(admit_parser.prog) == program_name(ToSeq(u.argv0_basename)))

''' + _GOLD_IMPL


def _variant(impl_body: str) -> str:
    return _swap(_BASE, _GOLD_IMPL, impl_body)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_CONTROL),
        "rationale": (
            "Structurally-different but CORRECT impl: the bootstrap predicate is "
            "negated and its arm moved to the end; the copy-loop and every gold "
            "framing Assert/invariant are preserved verbatim (pilot bug #2/#3 avoided). "
            "It must satisfy ToSeq(Result().prog)==program_name(ToSeq(self.argv0_basename)); "
            "if it fails to verify the postcondition is SPEC-TOO-STRONG."),
    },
    {
        "id": "admissibility-django-admin",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": (
            "A nested in-region caller constructs a Utility with the F2P own-argv "
            "name 'django-admin' for both sources and calls build_settings_parser, "
            "establishing the precondition (Acc(...,1/2) on both basenames) for a "
            "normal input. If the Requires cannot be established the precondition is "
            "PRECOND-TOO-STRONG. Caller + gold body both live inside the impl region, "
            "so same_spec holds."),
    },
    {
        "id": "frame-mut-argv0-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRAME_MUT),
        "refinement": (
            "A faithful real patch that WROTE to the utility's own argv[0] basename "
            "(e.g. self.argv = [mutated, ...] then prog from it) is not the gold fix; "
            "the gold fix only READS self.prog_name to set prog=self.prog_name and "
            "leaves the argv untouched. A mutate-then-derive patch changes the "
            "utility's recorded program name globally and would corrupt downstream "
            "uses of self.prog_name in execute(), diverging from the F2P expectation "
            "of 'usage: django-admin shell'."),
        "rationale": (
            "self.argv0_basename is a READ-ONLY input at Acc(list_pred,1/2); the "
            ".append() write needs FULL permission, so the verifier rejects this for "
            "INSUFFICIENT PERMISSION (the permission system, not a value clause). The "
            "gold value/frame postconditions are kept verbatim so the rejection is "
            "attributable solely to the write. This is the #1 weakness class and "
            "mandatory because the input is read-only."),
    },
    {
        "id": "wrong-source-ambient-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_WRONG_SOURCE),
        "refinement": (
            "This is model_prepatch.py exactly: prog derived from the AMBIENT "
            "sys_argv0_basename (the unchanged pre-patch CommandParser(...) with no "
            "prog=, which argparse defaults to basename(sys.argv[0])). In the F2P test "
            "the utility's own argv is ['django-admin',...] while sys.argv is mocked to "
            "[None,...]; the ambient source is not merely different but UNUSABLE "
            "(basename(None) raises). The faithful real patch (no change) crashes / "
            "yields the wrong program name and does NOT resolve the F2P."),
        "rationale": (
            "The load-bearing postcondition (model.py:109) pins prog to "
            "program_name(ToSeq(self.argv0_basename)); deriving from sys_argv0_basename "
            "satisfies it ONLY when the two sources coincide, so whenever they disagree "
            "the value-postcond fails and the verifier rejects. If this VERIFIED the "
            "spec would be SPEC-TOO-WEAK (admits the wrong-source / prepatch impl)."),
    },
    {
        "id": "partial-domain-no-bootstrap-remap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_NO_BOOTSTRAP),
        "refinement": (
            "A faithful real patch = prog=os.path.basename(self.argv[0]) WITHOUT the "
            "`if self.prog_name == '__main__.py': prog_name='python -m django'` remap. "
            "Correct on every basename except the bootstrap one, where it reports "
            "'usage: __main__.py ...' instead of the canonical 'usage: python -m django "
            "...'. It diverges from the documented program-name rule the A-reference "
            "(G-AX) validates; the prog the test pre-scan relies on is wrong on that "
            "subdomain, so it is not the faithful fix."),
        "rationale": (
            "The postcondition uses program_name(...), which remaps the bootstrap "
            "basename to module_invocation(); a verbatim copy yields '__main__.py' on "
            "that input, failing the value-postcond on exactly the bootstrap subdomain. "
            "If it verified the spec would be SPEC-TOO-WEAK on the bootstrap domain."),
    },
    {
        "id": "partial-domain-off-by-one-truncate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_OFF_BY_ONE),
        "refinement": (
            "Supporting near-miss with a real refinement: a faithful real patch = "
            "prog=self.prog_name[:-1] (truncate the last char). The pre-scan would "
            "report 'usage: django-admi ...' instead of 'usage: django-admin ...', a "
            "broken program name that fails the F2P assertion on the exact rendered "
            "usage string; it does not resolve."),
        "rationale": (
            "Stopping the copy loop one code point short makes prog a strict prefix of "
            "argv0_basename (empty for a 1-char basename), != program_name(...) on every "
            "non-empty basename. The loop invariant len(parser.prog)==i still holds at "
            "i==len-1, but the post-loop framing Assert(ToSeq(parser.prog)==ToSeq("
            "self.argv0_basename)) and the postcondition both fail. Rejected by the "
            "value-postcond; verifying would be SPEC-TOO-WEAK."),
    },
]


# === AXIOM LANE — the single A-reference `program_name` =====================
# meta.json: axioms=[] (NO consumed @ContractOnly axiom), but there is ONE
# A-reference deep model `program_name` validated by axiom_check.py (G-AX). The
# plan's axiom lane applies to A-reference deep models too. The probes below run
# in the instance image (apply_gold=True) but import ONLY stdlib (argparse, os,
# sys) — the same modules the changed code uses (pilot bug #4: we CALL the real
# routines, never scrape source; pilot bug #5: no file reads; pilot bug #6: the
# probe is self-contained, embeds the rule, mounts nothing).

# axiom-soundness: the deep model program_name(basename) MUST equal the REAL
# ManagementUtility.__init__ prog_name computation on every basename, AND the real
# argparse parser MUST adopt an explicit prog verbatim (the post-patch branch the
# model's contract relies on). This mirrors axiom_check.py §3.1+§3.2.
_AX_SOUND_PROBE = r'''
import argparse, os, random, string, sys

def model_program_name(basename):
    # model.py pure `program_name` over a basename string (model carries code points).
    if basename == "__main__.py":
        return "python -m django"
    return basename

def real_utility_prog_name(argv0):
    # REAL ManagementUtility.__init__ self.prog_name (django/core/management/__init__.py:190-192).
    prog_name = os.path.basename(argv0)
    if prog_name == "__main__.py":
        prog_name = "python -m django"
    return prog_name

def make_parser(prog):
    kwargs = dict(usage="%(prog)s subcommand [options] [args]",
                  add_help=False, allow_abbrev=False)
    if prog is not None:
        kwargs["prog"] = prog
    return argparse.ArgumentParser(**kwargs)

def check_rule(argv0):
    basename = os.path.basename(argv0)
    expected = real_utility_prog_name(argv0)      # real __init__ computation
    observed = model_program_name(basename)       # model.py pure program_name
    assert observed == expected, (
        "program_name deep model UNSOUND on argv0=%r: real=%r model=%r"
        % (argv0, expected, observed))

def check_adopts_prog(prog):
    # POST-patch branch: parser built with prog=p reports program name p verbatim.
    p = make_parser(prog)
    assert p.prog == prog, ("parser did not adopt explicit prog=%r: got %r" % (prog, p.prog))

def check_default_is_ambient(fake_sys_argv0):
    # PRE-patch branch: with no prog, argparse defaults to basename(sys.argv[0]).
    saved = sys.argv
    try:
        sys.argv = [fake_sys_argv0, "help"]
        p = make_parser(None)
        exp = os.path.basename(fake_sys_argv0)
        assert p.prog == exp, ("default prog mismatch for sys.argv[0]=%r: exp %r got %r"
                               % (fake_sys_argv0, exp, p.prog))
    finally:
        sys.argv = saved

boundary = ["django-admin", "manage.py", "/usr/local/bin/django-admin", "./manage.py",
            "/a/b/c/manage.py", "__main__.py", "/path/to/__main__.py", "foo",
            "foo/bar/baz", "django-admin.py", "a"]
for a in boundary:
    check_rule(a)
for prog in ["django-admin", "manage.py", "python -m django", "foo", "a",
             "django-admin.py", "x y z"]:
    check_adopts_prog(prog)
for a in boundary:
    check_default_is_ambient(a)
# discriminating F2P case: own argv 'django-admin', ambient would be wrong.
check_rule("django-admin"); check_adopts_prog("django-admin"); check_default_is_ambient("/x/sub.py")

rng = random.Random(13658)
alphabet = string.ascii_letters + string.digits + "._-/ "
for _ in range(20000):
    n = rng.randint(1, 24)
    body = "".join(rng.choice(alphabet) for _ in range(n))
    if rng.random() < 0.1:
        argv0 = (body.rsplit("/", 1)[0] + "/" if "/" in body else "") + "__main__.py"
    else:
        argv0 = body
    check_rule(argv0)
    prog = real_utility_prog_name(argv0)
    if prog:
        check_adopts_prog(prog)
print("AXIOM-SOUND OK: program_name deep model == real prog_name and argparse adopts "
      "explicit prog (post-patch) / defaults to basename(sys.argv[0]) (pre-patch) on "
      "%d boundary + 20000 fuzz inputs" % len(boundary))
sys.exit(0)
'''

# axiom-containment: the model passes ToSeq(self.argv0_basename) — an ARBITRARY
# code-point sequence (any basename string) — to program_name. The real
# program_name rule (basename, with '__main__.py' -> 'python -m django') is TOTAL:
# it has NO domain restriction (no precondition on the basename). Therefore every
# caller-reachable input lies in the rule's domain — containment is trivially
# satisfied. The probe asserts the real rule accepts (does not raise on / is
# defined for) every basename the model can construct, including the empty string,
# the bootstrap name, and arbitrary unicode-codepoint strings.
_AX_CONTAIN_PROBE = r'''
import os, random, string, sys

def real_utility_prog_name(argv0):
    prog_name = os.path.basename(argv0)
    if prog_name == "__main__.py":
        prog_name = "python -m django"
    return prog_name

# The model passes argv0_basename as code points; any basename string is reachable.
# Enumerate the domain edges the model's Requires admits (a List[int] of ANY length
# >= 0, ANY code points): empty, single char, the bootstrap name, paths, unicode.
reachable = ["", "a", "django-admin", "manage.py", "__main__.py", "/x/__main__.py",
             "foo bar", "weird\tname", "é中文", "x" * 256]
for basename in reachable:
    # The rule is total: it is defined (returns a str, never raises) for every
    # basename the caller can reach. Covering MORE than the caller reaches would
    # be sound; the defect would be a reachable input the rule rejects. None do.
    out = real_utility_prog_name(basename)
    assert isinstance(out, str), ("rule undefined on reachable basename %r" % basename)

# Randomized: arbitrary code-point strings (what ToSeq(argv0_basename) materializes).
rng = random.Random(20136)
for _ in range(5000):
    n = rng.randint(0, 40)
    s = "".join(chr(rng.randint(1, 0x2FFF)) for _ in range(n))
    out = real_utility_prog_name(s)
    assert isinstance(out, str)
print("AXIOM-CONTAINMENT OK: program_name rule is total; every caller-reachable "
      "basename (List[int] of any length/code points) is in its domain "
      "(no precondition restriction). 10 edge + 5000 fuzz inputs covered.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-program-name",
        "axiom": "program_name",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "The A-reference deep model program_name must equal the REAL "
            "ManagementUtility.__init__ prog_name (basename, with '__main__.py' -> "
            "'python -m django') and the real argparse parser must adopt an explicit "
            "prog verbatim (the post-patch branch the contract relies on). Probe CALLS "
            "the real argparse/os routines (pilot bug #4 avoided), stdlib-only. If the "
            "real callee disagrees on any input => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-contain-program-name",
        "axiom": "program_name",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Containment: the model passes ToSeq(self.argv0_basename) — an arbitrary "
            "code-point sequence — to program_name. The real rule is TOTAL (no "
            "precondition on the basename), so every caller-reachable basename "
            "(empty, bootstrap, paths, arbitrary unicode) is in its domain. A "
            "reachable input outside the domain would be AXIOM-TOO-WEAK-FOR-CALLER; "
            "none exists."),
    },
]
