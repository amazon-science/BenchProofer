#!/usr/bin/env python3
"""G-AX executable soundness check for pallets__flask-5014.

Executes the REAL repo code (`flask.Blueprint.__init__`, which delegates to the
unchanged base initialiser `flask.scaffold.Scaffold.__init__` via
`super().__init__`) and asserts every observation is permitted by `model.py`.

Two SEPARATE obligations are checked — the previous version conflated them and
only ever fuzzed the validation `name` while passing the always-resolvable
`__name__` as `import_name`, so it never exercised the `init_base` axiom's
ACTUAL claim (the behaviour of the base initialiser over an arbitrary
`import_name`). They are now split:

  (A) init_base AXIOM (A-consumed) — `model.py`'s `init_base(import_name)`.
      Its contract is now the WEAKEST sound one: on a Requires-satisfying
      `import_name` it MAY complete normally (`Ensures`) OR MAY fail as a unit
      (`Exsures(BaseInitError, ...)`). It is NOT promised to always return.
      We fuzz the AXIOM'S OWN argument — arbitrary `import_name`, holding the
      blueprint `name` at a fixed ACCEPTED value — against the real base init
      and assert that whatever the real callee does (return or raise) is a
      permitted outcome of the (weakened) axiom. Because the real base init
      reaches `get_root_path(import_name)` -> `pkgutil.get_loader(import_name)`,
      it RAISES (e.g. ImportError) on unresolvable dotted names — so we also
      assert the raise path is actually reachable. This is the path the OLD
      axiom (Ensures-only, no Exsures) over-claimed away and the OLD checker
      never touched; this checker would FAIL against that old axiom.

  (B) VALIDATION DECISION (the modeled control flow A3+A4) — the real
      constructor rejects EXACTLY the empty / dot-containing names with
      `ValueError`, and accepts every non-empty dot-free name, holding
      `import_name` at the resolvable `__name__`. The empty-name rejection is
      a POST-patch behaviour, so this obligation is asserted against whichever
      tree we are mounted on: we DETECT the tree (does `Blueprint('', __name__)`
      raise?) and check the decision against the expectation for that tree —
      post-patch: reject empty; pre-patch (base_commit): accept empty. Either
      way the dot rejection and the accept set must match the model.

Imports only `flask` (the repo under test) plus stdlib. Exit 0 iff every
obligation holds.
"""
import random
import sys

import flask


# ---------------------------------------------------------------------------
# model.py reject predicate, over the str carrier (len==0 or code point 46).
# ---------------------------------------------------------------------------
def model_rejects(name):
    return len(name) == 0 or ("." in name)


# A fixed ACCEPTED blueprint name (non-empty, dot-free) — so that obligation
# (A) isolates the base-init behaviour over `import_name` and never trips a
# name guard.
ACCEPTED_NAME = "ok"


def base_init_outcome(import_name):
    """Run the real base initialiser over `import_name` (with an accepted
    blueprint name so no name guard fires) and report the outcome:
      ("return", None)         normal completion
      ("raise", exc)           failed as a unit (any exception)
    Constructing a real Blueprint runs super().__init__ -> Scaffold.__init__,
    which (when root_path is unset, the default here) calls
    get_root_path(import_name) -> pkgutil.get_loader(import_name)."""
    try:
        flask.Blueprint(ACCEPTED_NAME, import_name)
        return ("return", None)
    except BaseException as exc:  # noqa: BLE001 — any failure of the base init
        return ("raise", exc)


def real_constructs(name, import_name=__name__):
    """True iff the REAL flask.Blueprint constructor accepts `name` with a
    resolvable `import_name` (constructs without raising ValueError); False iff
    it raises ValueError. Used only for the validation-decision obligation, so
    `import_name` is held resolvable to isolate the name decision."""
    try:
        flask.Blueprint(name, import_name)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Obligation (A): the init_base axiom over arbitrary import_name.
# ---------------------------------------------------------------------------
def check_axiom_init_base():
    # import_name values that REACH get_root_path and are unresolvable -> the
    # real base init RAISES (the path the OLD axiom over-claimed away). These
    # are the panel's minimal counterexamples plus relatives.
    raising_import_names = [
        ".",                 # relative / unresolvable dotted name
        "..",
        "no.such.package",   # unresolvable dotted name
        "definitely.not.a.real.module.xyzzy",
        "a.b.c.d.e",
        ".leading",
        "trailing.",
        "no_such_top_level_module_qwertyz",
    ]
    # import_name values that resolve (the base init returns normally).
    returning_import_names = [
        __name__,            # this module — always resolvable
        "flask",             # an importable package
        "os",
        "sys",
        "__main__",          # get_root_path special-cases this -> cwd
    ]

    saw_raise = False
    saw_return = False

    # The (weakened) axiom permits BOTH a normal return AND a base-init
    # failure for any Requires-satisfying import_name. So for soundness every
    # observed outcome is permitted by construction; what we MUST additionally
    # establish is that the RAISE path is real (otherwise the no-raise
    # over-claim would have been harmless). We assert at least one in-domain
    # import_name raises and at least one returns — exercising both posts.
    for imp in raising_import_names:
        kind, exc = base_init_outcome(imp)
        if kind == "raise":
            saw_raise = True
        else:
            saw_return = True  # tolerated: some envs may resolve oddly
        # Either outcome is permitted by the weakened axiom (Ensures or
        # Exsures(BaseInitError, ...)); nothing to reject here.

    for imp in returning_import_names:
        kind, exc = base_init_outcome(imp)
        if kind == "raise":
            saw_raise = True
        else:
            saw_return = True

    # randomized fuzz over dotted / relative / nonsense import_names
    rng = random.Random(50140)
    segalpha = list("abcXYZ_") + [""]
    for _ in range(2000):
        nseg = rng.randint(0, 4)
        seg = ["".join(rng.choice(list("abcdefghxyz_")) for _ in range(rng.randint(0, 5)))
               for _ in range(nseg)]
        imp = ".".join(seg)
        kind, exc = base_init_outcome(imp)
        if kind == "raise":
            saw_raise = True
        else:
            saw_return = True

    # The init_base axiom's raise post (Exsures(BaseInitError, ...)) must be
    # justified by a reachable raise; the OLD Ensures-only axiom forbade this.
    assert saw_raise, (
        "init_base axiom soundness: expected the real base initialiser to RAISE "
        "on at least one Requires-satisfying import_name (e.g. '.', "
        "'no.such.package') — this is the path the no-raise over-claim missed; "
        "the model's axiom models it via Exsures(BaseInitError, base_init_can_fail).")
    assert saw_return, (
        "init_base axiom soundness: expected the real base initialiser to RETURN "
        "normally on at least one resolvable import_name (e.g. __name__) — the "
        "Ensures(base_init_can_complete) post.")

    # The two witnesses base_init_can_complete / base_init_can_fail are stated over
    # the base callee's OWN argument and are silent about the blueprint name, which
    # is sound only if the base-init outcome does not depend on `name` (it is not
    # even a parameter of Scaffold.__init__). A ValueError is a NAME-guard
    # rejection, NOT a base-init failure — the base init itself completed, so it
    # counts as "did not fail" here.
    def base_init_failed_observed(import_name, blueprint_name):
        try:
            flask.Blueprint(blueprint_name, import_name)
            return False
        except ValueError:
            return False  # name-guard rejection: base init completed
        except BaseException:  # noqa: BLE001
            return True   # base init failed as a unit
    for imp in (raising_import_names + returning_import_names):
        a = base_init_failed_observed(imp, "ok")
        b = base_init_failed_observed(imp, "alsofine")
        assert a == b, (
            "the base-init outcome DEPENDS on the blueprint name for import_name %r "
            "(%s vs %s) — the witnesses are stated over import_name alone, so they "
            "must be name-silent" % (imp, a, b))

    # INDEPENDENCE of the two witnesses. The axiom deliberately does NOT claim the
    # outcome is a function of import_name: each exit hands out its own witness and
    # neither is the negation of the other. That is the faithful claim ONLY IF the
    # real base init can do EITHER for one and the same import_name — otherwise a
    # single predicate of import_name would model it. Route: the constructor's
    # optional root_path argument, which skips get_root_path entirely
    # (scaffold.py:96), so an import_name that fails through get_root_path
    # completes when root_path is supplied. (The ambient module table is a second
    # route: get_root_path reads sys.modules at helpers.py:572 and populates it via
    # __import__ at helpers.py:590, so a namespace package with no __file__ flips
    # from completing to RuntimeError across its own import.)
    def outcome_with_root_path(import_name, root_path):
        try:
            flask.Blueprint(ACCEPTED_NAME, import_name, root_path=root_path)
            return "return"
        except BaseException:  # noqa: BLE001
            return "raise"
    both = [imp for imp in raising_import_names
            if base_init_outcome(imp)[0] == "raise"
            and outcome_with_root_path(imp, "/tmp") == "return"]
    assert both, (
        "no import_name was found on which the real base init both FAILS and "
        "COMPLETES, so the two independent witnesses are unmotivated — a single "
        "predicate of import_name would model the callee")


# ---------------------------------------------------------------------------
# Obligation (B): the empty/dot validation decision over name.
# ---------------------------------------------------------------------------
def check_validation_decision():
    # Detect the tree: post-patch rejects the empty name, base_commit accepts it.
    empty_rejected = not real_constructs("")

    # boundary names whose decision is INDEPENDENT of the empty-name guard
    accept = [
        "a",                # minimal non-empty, dot-free
        "test",             # a typical blueprint name
        "my_blueprint",
        "admin-panel",      # hyphen is fine
        "ünïcодe",  # non-ASCII, dot-free, non-empty
        " ",                # a single space is non-empty and dot-free
        "0",
        "a b c",            # spaces ok
    ]
    reject_dot = [
        ".",                # dot only
        "a.b",              # dotted
        "app.ui",           # the existing test_dotted_name_not_allowed case
        ".leading",
        "trailing.",
    ]
    for name in accept:
        assert real_constructs(name), (
            "accepted name %r must construct" % name)
    for name in reject_dot:
        assert not real_constructs(name), (
            "dotted name %r must raise ValueError" % name)

    # the empty name: decision depends on the tree we are mounted on.
    if empty_rejected:
        # post-patch tree (gold applied): empty name must raise (the F2P case
        # tests/test_blueprints.py::test_empty_name_not_allowed) and the model
        # agrees (model_rejects('') is True).
        assert model_rejects(""), "model must reject empty name"
        assert not real_constructs(""), (
            "post-patch: empty name must raise ValueError "
            "(test_empty_name_not_allowed)")
    else:
        # base_commit tree (no gold): the empty-name guard is absent, so the
        # real constructor ACCEPTS the empty name. That is the pre-patch
        # behaviour the gold patch fixes; the model's reject of '' is exactly
        # the discriminating new behaviour and is NOT expected to hold here.
        assert real_constructs(""), (
            "base_commit: empty name constructs (the guard is not yet present)")

    # randomized fuzz over a code-point alphabet incl. dots/spaces, on a
    # resolvable import_name, for the NON-empty (tree-independent) decisions.
    rng = random.Random(5014)
    alphabet = list("abcXYZ012._- .") + ["é", "•"]
    for _ in range(20000):
        n = rng.randint(1, 8)  # non-empty: avoid the tree-dependent '' case
        name = "".join(rng.choice(alphabet) for _ in range(n))
        if not name:
            continue
        constructed = real_constructs(name)
        rejected_by_model = model_rejects(name)
        assert constructed == (not rejected_by_model), (
            "validation mismatch on %r: real constructs=%s, model rejects=%s"
            % (name, constructed, rejected_by_model))


def main():
    check_axiom_init_base()
    check_validation_decision()
    print("G-AX OK: (A) init_base axiom sound — real base initialiser both "
          "RETURNS (resolvable import_name) and RAISES (unresolvable dotted "
          "import_name e.g. '.', 'no.such.package'), both permitted by the "
          "weakened axiom (Ensures / Exsures(BaseInitError)); (B) empty/dot "
          "validation decision matches the model over boundary + 20000 fuzz "
          "names (empty-name decision checked against the mounted tree).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
