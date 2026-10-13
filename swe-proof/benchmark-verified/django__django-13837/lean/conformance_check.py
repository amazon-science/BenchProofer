#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_getChildArguments against the patch.diff behaviour (post-patch
`get_child_arguments`).

The impl region is all-R (refinement.md): no A-tagged op, so we run a real
fuzz. We build two functions over the SAME bridged seven-tuple input
`(executable, warnoptions, argv, launchPackage, scriptPresent, exeAlt, scriptAlt)`:

* `shadow`  — the op-for-op transcription of `implementation_getChildArguments`
              (Lean `Id.run do` skeleton) into Python.
* `patched` — an independent reconstruction of the post-patch django
              `get_child_arguments()` control flow, driven by the same bridged
              environment values (mapping.md type bijection).

The Lean result type `Except String (List String)` is bridged to a Python pair
`("ok", list)` / `("error", msg)`. We assert zero disagreements over >=10^5
fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import pathlib
import random
import sys

SEED = 13837          # pinned in mapping.md
N = 120_000           # >= 10^5


def posix_str(s):
    """Transcription of Lean `posixStr` (POSIX-path string normalization,
    i.e. str(Path(s)) semantics: drop empty/'.' segments, keep '//' or '/'
    root, empty relative path renders as '.')."""
    segs = [p for p in s.split("/") if p != "" and p != "."]
    if s.startswith("//") and not s.startswith("///"):
        root = "//"
    elif s.startswith("/"):
        root = "/"
    else:
        root = ""
    if not segs:
        return "." if root == "" else root
    return root + "/".join(segs)


def shadow(executable, warnoptions, argv, launchPackage,
           scriptPresent, exeAlt, scriptAlt):
    """Transcription of implementation_getChildArguments."""
    args = [executable]
    for o in warnoptions:
        args = args + ["-W" + o]
    if launchPackage != "":
        return ("ok", args + ["-m", launchPackage] + argv[1:])
    elif not scriptPresent:
        if exeAlt is not None:
            return ("ok", [exeAlt] + argv[1:])
        elif scriptAlt is not None:
            return ("ok", args + [scriptAlt] + argv[1:])
        else:
            head = argv[0] if argv else ""
            return ("error", "Script " + posix_str(head) + " does not exist.")
    else:
        return ("ok", args + argv)


def patched(executable, warnoptions, argv, launchPackage,
            scriptPresent, exeAlt, scriptAlt):
    """Independent reconstruction of the post-patch get_child_arguments().

    Post-patch Python (mapping.md bijection applied):
        args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]
        if __main__.__spec__ is not None and __main__.__spec__.parent:
            args += ['-m', __main__.__spec__.parent]; args += sys.argv[1:]
        elif not py_script.exists():
            if exe_entrypoint.exists(): return [str(exe_entrypoint), *sys.argv[1:]]
            if script_entrypoint.exists(): return [*args, str(script_entrypoint), *sys.argv[1:]]
            raise RuntimeError('Script %s does not exist.' % py_script)
        else:
            args += sys.argv
        return args

    `__main__.__spec__ is not None and __main__.__spec__.parent` is truthy
    exactly when launchPackage != "" (mapping.md), and the emitted token equals
    launchPackage. `py_script` is `Path(sys.argv[0])`, so the diagnostic in the
    missing-script branch renders `str(Path(argv[0]))`, i.e. the POSIX-normalized
    path — we use the REAL pathlib here so the shadow's `posix_str` is checked
    against genuine `Path` rendering.
    """
    args = [executable] + ["-W%s" % o for o in warnoptions]
    if launchPackage != "":
        out = list(args)
        out += ["-m", launchPackage]
        out += argv[1:]
        return ("ok", out)
    elif not scriptPresent:
        if exeAlt is not None:
            return ("ok", [exeAlt] + argv[1:])
        if scriptAlt is not None:
            return ("ok", list(args) + [scriptAlt] + argv[1:])
        head = argv[0] if argv else ""
        py_script = pathlib.PurePosixPath(head)
        return ("error", "Script %s does not exist." % py_script)
    else:
        return ("ok", list(args) + argv)


def rand_str(rng, alphabet="abc/._-django pkg0123", lo=0, hi=8):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(lo, hi)))


def rand_case(rng):
    executable = rng.choice(["/usr/bin/python", "python", rand_str(rng)])
    warnoptions = [rng.choice(["error", "all", "ignore", rand_str(rng)])
                   for _ in range(rng.randint(0, 3))]
    # argv head is the script path; tail are program args. Oversample path
    # shapes that Path() normalizes (trailing '/', '//', './', empty, roots).
    head = rng.choice([rand_str(rng), rand_str(rng), rand_str(rng),
                       "", "a/", "sub//x.py", "a/./b", "./foo", "x.py/",
                       "/", "//", "///", "//x", "///x", ".", "./",
                       rand_str(rng, alphabet="a/."),
                       rand_str(rng, alphabet="/."),
                       rand_str(rng) + "/"])
    argv = [head] + [rand_str(rng) for _ in range(rng.randint(0, 4))]
    # launchPackage: oversample "" and "django" boundary plus arbitrary labels
    launchPackage = rng.choice(["", "", "", "django", "pkg_other",
                                "utils_tests.test_module", rand_str(rng)])
    scriptPresent = rng.choice([True, False])
    exeAlt = rng.choice([None, None, rand_str(rng)])
    scriptAlt = rng.choice([None, None, rand_str(rng)])
    return (executable, warnoptions, argv, launchPackage,
            scriptPresent, exeAlt, scriptAlt)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        ("python", [], ["script.py", "runserver"], "", True, None, None),
        ("python", [], ["m.py", "runserver"], "django", True, None, None),
        ("python", [], ["m.py", "runserver"], "pkg_other", True, None, None),
        ("python", [], ["m.py", "runserver"], "utils_tests.test_module",
         True, None, None),
        ("python", ["error"], ["s", "a", "b"], "", False, "s.exe", None),
        ("python", ["all"], ["s"], "", False, None, "s-script.py"),
        ("python", [], ["missing"], "", False, None, None),
        ("python", ["error", "all"], ["s", "runserver"], "", True, None, None),
        # missing-script diagnostic: Path() normalization of argv[0]
        ("python", [], ["a/"], "", False, None, None),
        ("python", [], [""], "", False, None, None),
        ("python", [], ["sub//x.py"], "", False, None, None),
        ("python", [], ["a/./b"], "", False, None, None),
        ("python", [], ["./foo"], "", False, None, None),
        ("python", [], ["x.py/"], "", False, None, None),
        ("python", [], ["//x"], "", False, None, None),
        ("python", [], ["///x"], "", False, None, None),
        ("python", [], ["/"], "", False, None, None),
        ("python", [], ["//"], "", False, None, None),
        ("python", [], ["."], "", False, None, None),
    ]
    cases = fixed + [rand_case(rng) for _ in range(N)]

    for c in cases:
        got = shadow(*c)
        want = patched(*c)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((c, got, want))

    if disagreements:
        print("G-CONF FAIL: %d disagreements" % disagreements)
        for c, g, w in examples:
            print("  in=%r shadow=%r patched=%r" % (c, g, w))
        return 1

    print("G-CONF OK: %d inputs, 0 disagreements (seed=%d)" % (len(cases), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
