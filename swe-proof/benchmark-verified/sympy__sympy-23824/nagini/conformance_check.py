#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23824 (nagini).

SHADOW: the impl region of model.py (`restore_leading`), copied verbatim below
with the contract calls (Requires/Ensures/Invariant) stripped. The impl region
uses only plain List[int] operations (PSeq/ToSeq appear only inside contracts),
so no sequence shim is needed. There are no @Pure helpers and no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo code the model models per mapping.md — the
leading-restore site inside `sympy.physics.hep.gamma_matrices.kahane_simplify`,
where the run of leading uncontracted gamma factors that was set aside is
restored in front of each core-result term. The gate applies patch.diff to
/testbed before this script runs (this script does NOT apply it);
PYTHONPATH=/testbed makes the patched module importable. Because the modeled
behaviour is an inline statement of a large algorithm rather than a standalone
function, the oracle is obtained by locating that exact statement in the
patched module's AST (the unique rebinding of the term list that consults the
first-contracted-factor position) and executing the REAL statement object —
the repo's own code, byte-for-byte, not a transliteration — over controlled
bindings of the names it reads (the factor-label list, the position of the
first contracted factor, and the list of core-result terms).

An end-to-end grounding leg additionally drives the FULL `kahane_simplify`
pipeline on real gamma-matrix products that carry a leading uncontracted run
in front of a contracted pair: the simplified expression must equal the
leading run, in its original left-to-right order, times the contraction's
scalar factor. A control probe confirms the expression-level comparison is
order-sensitive (a permuted leading run must NOT compare equal), so this leg
cannot pass vacuously.

TYPE BRIDGE (mapping.md section 2):
  leading <-> the slice of the factor-label list up to the first contracted
              factor's position; entries are integer index labels, so
              List[int] is exact. Realized by binding the label list to
              `leading` (sometimes with placeholder entries appended past the
              slice boundary, mirroring the real list's shape) and the
              position to len(leading).
  tail    <-> one core-result term, a plain list of integer index labels;
              the site rebuilds every term uniformly, so each (leading, term)
              pair the executed statement processes is one input to the
              modeled per-term operation.
  Result() <-> the corresponding rebuilt entry of the term list after the
              real statement executes.

INPUT DOMAIN: the Requires clauses demand only read-only list permissions, so
any pair of integer lists is in-domain. Generation covers the boundary shapes
(both empty, one empty, singletons, duplicated labels, longer runs) plus wide
fuzz over lengths 0..8 with small non-negative labels (the realistic carrier)
and occasional arbitrary integers. The read-only obligation is also checked:
the executed real statement must leave the input term lists unchanged.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz pairs.
Pinned fuzz seed: 23824.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random; sympy is the repo under test).
"""
import ast
import inspect
import json
import random
import sys

SEED = 23824
N_FUZZ = 100_000


# --- impl region of model.py, verbatim, contract calls stripped ---------------

def restore_leading(leading, tail):
    result = []  # type: list
    i = 0
    while i < len(leading):
        result.append(leading[i])
        i = i + 1
    j = 0
    while j < len(tail):
        result.append(tail[j])
        j = j + 1
    return result


# --- oracle: the real statement object, located in the patched module's AST ---

def locate_site(module):
    """Find the leading-restore statement inside kahane_simplify: the unique
    assignment that rebinds the term list (`resulting_indices`) and reads the
    first-contracted-factor position (`first_dum_pos`). Returns compiled code
    executing the repo's own statement, or None if not uniquely present."""
    src = inspect.getsource(module)
    tree = ast.parse(src)
    fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "kahane_simplify":
            fn = node
            break
    if fn is None:
        return None
    hits = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "resulting_indices"
                   for t in node.targets):
            continue
        names = {n.id for n in ast.walk(node.value)
                 if isinstance(n, ast.Name)}
        if "first_dum_pos" in names and "free_pos" in names:
            hits.append(node)
    if len(hits) != 1:
        return None
    mod = ast.Module(body=[hits[0]], type_ignores=[])
    ast.fix_missing_locations(mod)
    return compile(mod, "<leading-restore-site>", "exec")


def run_site(site_code, leading, terms, pad):
    """Execute the real statement over controlled bindings and return the
    rebuilt term list. `pad` appends placeholder entries past the slice
    boundary, mirroring the real label list's shape (they must be ignored)."""
    ns = {
        "free_pos": list(leading) + ([None] * pad),
        "first_dum_pos": len(leading),
        "resulting_indices": terms,
    }
    exec(site_code, ns)
    return ns["resulting_indices"]


def check_batch(site_code, leading, tails, pad):
    """Diff shadow vs oracle for one leading run over several core terms.
    Each (leading, tail) pair is one input. Returns (n, err_or_None)."""
    terms_in = [list(t) for t in tails]
    snapshot = [list(t) for t in terms_in]
    rebuilt = run_site(site_code, leading, terms_in, pad)
    if terms_in != snapshot:
        return 0, ("DISAGREEMENT (read-only inputs mutated)\n"
                   "  leading=%r tails=%r after=%r"
                   % (leading, snapshot, terms_in))
    if len(rebuilt) != len(tails):
        return 0, ("DISAGREEMENT (term count)\n  leading=%r tails=%r\n"
                   "  real=%r" % (leading, tails, rebuilt))
    n = 0
    for tail, real in zip(tails, rebuilt):
        shadow = restore_leading(list(leading), list(tail))
        n += 1
        if shadow != list(real):
            return n, ("DISAGREEMENT\n  leading=%r tail=%r\n"
                       "  shadow=%r\n  real=%r"
                       % (leading, tail, shadow, real))
    return n, None


# --- end-to-end grounding leg: the full real pipeline --------------------------

def grounding_leg():
    """Drive the FULL kahane_simplify on gamma products with a leading
    uncontracted run before a contracted pair; the result must be the leading
    run in original order times the contraction's scalar factor. Returns an
    error string or None."""
    from sympy.physics.hep.gamma_matrices import (
        GammaMatrix as G, LorentzIndex, kahane_simplify)
    from sympy.tensor.tensor import tensor_indices

    mu, rho, sigma, a1, a2 = tensor_indices("mu, rho, sigma, a1, a2",
                                            LorentzIndex)
    runs = [
        [rho],
        [rho, sigma],
        [sigma, rho],
        [rho, sigma, a1],
        [a2, rho, sigma, a1],
    ]
    for lead in runs:
        expr = G(lead[0])
        for idx in lead[1:]:
            expr = expr * G(idx)
        expected = 4 * expr
        simplified = kahane_simplify(expr * G(mu) * G(-mu))
        if not simplified.equals(expected):
            return ("DISAGREEMENT (end-to-end)\n  leading run=%r\n"
                    "  real result=%r\n  expected (order-preserving)=%r"
                    % (lead, simplified, expected))
    # control: the comparison must be order-sensitive, else this leg is vacuous
    probe = kahane_simplify(G(rho) * G(sigma) * G(mu) * G(-mu))
    if probe.equals(4 * G(sigma) * G(rho)):
        return ("VACUOUS GROUNDING: expression comparison is not sensitive "
                "to the leading run's order")
    return None


def main():
    import sympy.physics.hep.gamma_matrices as gm  # REAL patched module

    site_code = locate_site(gm)
    if site_code is None:
        print("ERROR: could not uniquely locate the leading-restore "
              "statement in the patched module")
        return 2

    err = grounding_leg()
    if err:
        print(err)
        return 1

    labels = list(range(0, 12))

    boundary_leadings = [
        [],
        [0],
        [5],
        [0, 1],
        [1, 0],
        [3, 3],
        [0, 1, 2],
        [2, 1, 0],
        [7, 7, 7],
        [0, 1, 2, 3, 4],
        [-1, 0, 1],
    ]
    boundary_tails = [
        [],
        [0],
        [9],
        [0, 1],
        [1, 0],
        [4, 4],
        [5, 6, 7],
        [3, 2, 1, 0],
        [-2, 10],
    ]

    checked = 0
    for lead in boundary_leadings:
        for pad in (0, 3):
            n, err = check_batch(site_code, lead, boundary_tails, pad)
            checked += n
            if err:
                print(err)
                return 1

    # fuzz: random (leading, tails) batches; each (leading, tail) pair is one
    # input to the modeled per-term operation. Pinned seed 23824.
    rng = random.Random(SEED)
    while checked < N_FUZZ + len(boundary_leadings) * 2 * len(boundary_tails):
        k = rng.randint(0, 8)
        lead = [rng.choice(labels) for _ in range(k)]
        if rng.random() < 0.05:
            lead = [rng.randint(-10**6, 10**6) for _ in range(k)]
        tails = []
        for _ in range(rng.randint(1, 6)):
            m = rng.randint(0, 8)
            t = [rng.choice(labels) for _ in range(m)]
            if rng.random() < 0.05:
                t = [rng.randint(-10**6, 10**6) for _ in range(m)]
            tails.append(t)
        pad = rng.choice((0, 1, 4))
        n, err = check_batch(site_code, lead, tails, pad)
        checked += n
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real leading-restore site on %d "
          "(leading, term) inputs (boundary grid + fuzz, seed %d); "
          "end-to-end grounding leg passed with an order-sensitivity control."
          % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region of "
                                "restore_leading)",
                      "oracle": "real statement object located in the "
                                "patched module AST + full-pipeline "
                                "grounding leg"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
