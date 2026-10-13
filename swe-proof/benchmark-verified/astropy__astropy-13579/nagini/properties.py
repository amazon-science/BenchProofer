"""PBT manifest for astropy__astropy-13579 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
executes and stamps with RESULT. Spec cases are full model.py variants that share
the FROZEN spec byte-for-byte (region-surgery: only the text strictly inside an
`# impl-start` / `# impl-end` region is edited) and swap the implementation; they
are checked by Nagini verify + markers.same_spec. Axiom cases are real-callee
probes run in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md):

  Two modeled functions over a per-index selection:
    * `assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)`
      builds the length-`world_n_dim` vector whose slot `i` is
      `value_at(.., i)` = `supplied[i]` if `kept[i]` else `world_at_slice[i]`.
      Postcondition LOAD-BEARING clauses:
        - `ToSeq(Result()) == ref_world_vector(..)` (exact value at every slot),
        - the kept-slot pin `kept[iw] -> Result[iw] == supplied[iw]`,
        - the dropped-slot pin `not kept[iw] -> Result[iw] == world_at_slice[iw]`
          (THIS is the discriminating clause — the gold patch fixed exactly the
          dropped-slot fill from the constant `1.` to the at-view coordinate).
      ALL THREE input lists are READ-ONLY: `Acc(list_pred(x), 1/2)`. => the
      frame-mutation probe is MANDATORY.
    * `recovered_pixel(kept, supplied, world_at_slice, world_n_dim, dim)` feeds
      the assembled vector to the opaque deterministic callee `full_world_to_pixel`
      and states `Result() == full_world_to_pixel(ref_world_vector(..), dim)`.
      The oracle argument is GROUNDED (a pure function of the args), so there is
      no *wrong* echo of an answer key; the only way to break it is to feed the
      oracle a DIFFERENT vector (value-level mask) — covered below.

Axiom lane: one `@ContractOnly` axiom `full_world_to_pixel` (A-consumed). The
Nagini proof consumes ONLY its determinism (congruence: equal vectors -> equal
results; differing vectors NOT provably equal); it has NO `Ensures`, so the only
caller-domain obligation is its `Requires(dim >= 0)`. We probe (a) the real
callee's determinism/round-trip soundness on the issue WCS (reusing
axiom_check.py) and (b) containment: every call the model makes satisfies
`dim >= 0`.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13579"
FLOAT_ENCODING = None  # meta.json float_encoding is null (precision-independent; int carrier)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (all strictly INSIDE an impl region; editing them keeps spec).
# ---------------------------------------------------------------------------

# assemble_inverse_world: the per-slot value selection (the edited gold branch).
_ASM_SELECT = ("        if kept[iworld]:\n"
               "            v = supplied[iworld]\n"
               "        else:\n"
               "            v = world_at_slice[iworld]")

# recovered_pixel: the whole impl body (assemble -> feed oracle -> return).
_REC_BODY = ("    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)\n"
             "    res = full_world_to_pixel(ToSeq(assembled), dim)\n"
             "    return res")


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): assemble, branch-reorder ---------------
    # Structurally different (negated guard, branches swapped) but identical
    # behaviour. Keeps loop direction (forward append) and EVERY gold invariant
    # and framing Assert verbatim, so the gold proof obligations are untouched
    # (avoids the front-recursive-fold induction trap — only the executable
    # branch shape changes). MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-assemble-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ASM_SELECT,
            "        if not kept[iworld]:\n"
            "            v = world_at_slice[iworld]\n"
            "        else:\n"
            "            v = supplied[iworld]"),
        "rationale": "a correct impl with reordered/negated branches must still "
                     "verify against the frozen spec; the value at each slot is "
                     "unchanged (else SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): recovered_pixel, inline call -----------
    # Drops the intermediate `res` local; same call, same value. MUST verify.
    {
        "id": "pos-recovered-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _REC_BODY,
            "    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)\n"
            "    return full_world_to_pixel(ToSeq(assembled), dim)"),
        "rationale": "a behaviourally-identical reshape (inline the oracle call, "
                     "drop the temporary) must verify (else SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: precondition admits a normal F2P-shaped input ---------
    # recovered_pixel asserts the assembly precondition components it holds
    # (lengths, world_n_dim>=0) before the self-call, then proceeds with the
    # gold body. If the Requires could not be established for a legitimate input
    # the asserts / the call would fail => PRECOND-TOO-STRONG. It verifies, so
    # the precondition is satisfiable by an in-domain caller.
    {
        "id": "admiss-recovered-precond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _REC_BODY,
            "    Assert(world_n_dim >= 0)\n"
            "    Assert(len(kept) == world_n_dim)\n"
            "    Assert(len(supplied) == world_n_dim)\n"
            "    Assert(len(world_at_slice) == world_n_dim)\n"
            "    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)\n"
            "    res = full_world_to_pixel(ToSeq(assembled), dim)\n"
            "    return res"),
        "rationale": "the assembly precondition (lengths + world_n_dim>=0 + the "
                     "1/2 list_pred permissions threaded from recovered_pixel's "
                     "own Requires) is established for a normal input and the "
                     "self-call verifies (else PRECOND-TOO-STRONG).",
    },

    # -- FRAME-MUTATION (uniqueness): write a read-only input -----------------
    # MANDATORY: kept/supplied/world_at_slice are Acc(list_pred(.),1/2) read-only
    # inputs. This rival appends to `supplied` (only 1/2 permission held) to make
    # the slot fills "match" by side effect. It must be REJECTED for INSUFFICIENT
    # PERMISSION (list.append needs the full list_pred). Gold invariants/asserts
    # kept verbatim so the rejection is attributable to the write, not a proof gap.
    {
        "id": "frame-mutate-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASM_SELECT,
            "        if kept[iworld]:\n"
            "            v = supplied[iworld]\n"
            "        else:\n"
            "            supplied.append(world_at_slice[iworld])\n"
            "            v = world_at_slice[iworld]"),
        "refinement": "the faithful real patch (mutating the caller's supplied "
                      "world_arrays inside the assembly loop) corrupts the shared "
                      "input read on the next iteration and across callers, so it "
                      "would not produce the gold world vector and would not "
                      "resolve test_coupled_world_slicing.",
        "rationale": "rejected by the permission system: `supplied` is held at "
                     "Acc(list_pred,1/2); `list.append` requires the full "
                     "predicate, so the write is INSUFFICIENT-PERMISSION. If it "
                     "verified, the read-only frame is unguarded (SPEC-TOO-WEAK).",
    },

    # -- FRAME-MUTATION supporting case: write `kept` (the flag vector) -------
    {
        "id": "frame-mutate-kept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASM_SELECT,
            "        if kept[iworld]:\n"
            "            kept.append(False)\n"
            "            v = supplied[iworld]\n"
            "        else:\n"
            "            v = world_at_slice[iworld]"),
        "refinement": "mutating the kept-flag vector mid-loop changes which "
                      "dimensions are treated as kept/dropped for later indices, "
                      "so the assembled vector diverges from gold and the F2P "
                      "reproducer fails.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on `kept` "
                     "(held at 1/2). Frame integrity of the read-only flag vector.",
    },

    # -- PARTIAL-DOMAIN (uniqueness): wrong dropped-slot fill = the BUG -------
    # The gold edit. This rival reverts the dropped slot to a constant (the
    # pre-patch `world_arrays_new.append(1.)`). Correct on every KEPT index but
    # diverges on the DROPPED subdomain. Must be rejected by the dropped-slot
    # postcondition / the ref_world_vector loop invariant (model_prepatch.py
    # fails on exactly this clause).
    {
        "id": "partial-dropped-constant1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASM_SELECT,
            "        if kept[iworld]:\n"
            "            v = supplied[iworld]\n"
            "        else:\n"
            "            v = 1"),
        "refinement": "this IS the pre-patch bug: a dropped world slot filled with "
                      "the constant 1. instead of the at-view world coordinate. On "
                      "the coupled issue WCS the dropped spectral coordinate is "
                      "~1.05e-10, not 1, so the round trip breaks and "
                      "test_coupled_world_slicing fails (out_pix[0] is ~1.8e11, "
                      "not ~0).",
        "rationale": "rejected by `not kept[iw] -> Result[iw] == world_at_slice[iw]`"
                     " and by the `ToSeq(Result()) == ref_world_vector(..)` loop "
                     "invariant. If it verified, the discriminating fix is unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): dropped slot takes `supplied` -----------
    # A subtler wrong fill: use the supplied value (same dim) for the dropped
    # slot. Indistinguishable from gold on KEPT indices, wrong on DROPPED ones
    # whenever supplied[i] != world_at_slice[i]. Rejected by the dropped-slot pin.
    {
        "id": "partial-dropped-uses-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASM_SELECT,
            "        if kept[iworld]:\n"
            "            v = supplied[iworld]\n"
            "        else:\n"
            "            v = supplied[iworld]"),
        "refinement": "filling a dropped slot with the supplied per-dimension "
                      "value (rather than the at-view world coordinate) feeds the "
                      "wrong scalar into the coupled full inverse; on the issue WCS "
                      "the recovered pixel is not ~0, so the F2P fails.",
        "rationale": "rejected by `not kept[iw] -> Result[iw] == world_at_slice[iw]`"
                     " (and the ref_world_vector invariant): on the dropped "
                     "subdomain supplied[i] is not provably world_at_slice[i].",
    },

    # -- PARTIAL-DOMAIN supporting case: corrupt only the FIRST slot ----------
    # Correct on every index except iworld == 0, which is forced to a wrong
    # value. The loop invariant `ToSeq(world_arrays_new) == ref_world_vector(..,
    # iworld)` fails at the very first step => reject. Targets the input that
    # fails first (first-element sub-domain).
    {
        "id": "partial-first-slot-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASM_SELECT,
            "        if iworld == 0:\n"
            "            v = 0\n"
            "        elif kept[iworld]:\n"
            "            v = supplied[iworld]\n"
            "        else:\n"
            "            v = world_at_slice[iworld]"),
        "refinement": "a real patch correct on all but the first world dimension "
                      "still assembles a wrong vector (slot 0 carries a constant 0 "
                      "instead of value_at(..,0)); the full inverse is a function of "
                      "the whole vector, so the recovered pixel is wrong and the "
                      "F2P fails.",
        "rationale": "rejected by the `ToSeq(world_arrays_new) == ref_world_vector"
                     "(.., iworld)` loop invariant, which fails on the first "
                     "iteration. Partial-domain (first-element) divergence.",
    },

    # -- VALUE-LEVEL MASK (uniqueness): feed the oracle the WRONG vector ------
    # recovered_pixel's postcondition is `Result == full_world_to_pixel(
    # ref_world_vector(..), dim)`. The oracle argument is grounded, so a rival
    # cannot echo a wrong answer key — but it CAN call the (correct, opaque)
    # oracle on a DIFFERENT vector. Here it feeds `ToSeq(supplied)` (the
    # supplied-everywhere vector) instead of the assembled vector. Because the
    # callee is opaque, the result is NOT provably == oracle(ref_world_vector),
    # so this must be rejected.
    {
        "id": "mask-recovered-wrong-vector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _REC_BODY,
            "    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)\n"
            "    res = full_world_to_pixel(ToSeq(supplied), dim)\n"
            "    return res"),
        "refinement": "feeding the supplied-everywhere vector (no at-view fill in "
                      "the dropped slots) to the full inverse is exactly the "
                      "behaviour the bug exhibits on coupled axes — the recovered "
                      "kept pixel is wrong, so test_coupled_world_slicing fails.",
        "rationale": "rejected by `Result == full_world_to_pixel(ref_world_vector"
                     "(..), dim)`: the opaque callee on a vector that differs from "
                     "ref_world_vector in any dropped slot is NOT provably equal "
                     "to the required value (axiom determinism only). If it "
                     "verified, the oracle argument is unpinned (SPEC-TOO-WEAK).",
    },

    # -- VALUE-LEVEL MASK supporting case: feed a constant-filled vector ------
    # Reassembles with the constant-1 fill locally and feeds THAT to the oracle.
    # Same defect class as the bug, expressed at the recovered_pixel face.
    {
        "id": "mask-recovered-constant-vector",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _REC_BODY,
            "    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)\n"
            "    bad = []  # type: List[int]\n"
            "    j = 0\n"
            "    while j < world_n_dim:\n"
            "        Invariant(Acc(list_pred(bad)))\n"
            "        Invariant(0 <= j and j <= world_n_dim)\n"
            "        Invariant(len(bad) == j)\n"
            "        bad.append(1)\n"
            "        j += 1\n"
            "    res = full_world_to_pixel(ToSeq(bad), dim)\n"
            "    return res"),
        "refinement": "constant-filling the whole vector and feeding it to the full "
                      "inverse reproduces the pre-patch round-trip failure; the F2P "
                      "reproducer does not resolve.",
        "rationale": "rejected by `Result == full_world_to_pixel(ref_world_vector"
                     "(..), dim)`: the opaque callee on the constant vector is not "
                     "provably the required value.",
    },
]


# ===========================================================================
# AXIOM LANE  (one @ContractOnly axiom: full_world_to_pixel, A-consumed)
# ===========================================================================
#
# The runner mounts ONLY the probe script at /work; axiom_check.py / model.py are
# NOT in-container, so the axiom-soundness probe EMBEDS axiom_check.py's source
# (read on the HOST at manifest-load time) and executes the REAL callee
# self._wcs.world_to_pixel_values on the issue's coupled WCS — it never scrapes
# source. Files are opened utf-8-safe (no file reads needed here; pure runtime).

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# axiom-soundness: run the real callee (determinism + round-trip identity +
# discriminating-constant + FAIL_TO_PASS) via the persisted, gold-grounded
# axiom_check.py. exit 0 iff every obligation holds.
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
if __name__ != "__main__":
    pass
import sys as _sys
print("PBT axiom-soundness: running real callee soundness obligations "
      "(determinism, round-trip, discriminating-constant, FAIL_TO_PASS)")
_rc = main()
_sys.exit(0 if _rc == 0 else 1)
"""

# axiom-containment: enumerate EXACTLY the callee inputs the MODEL can reach and
# assert each lies in the axiom's Requires domain. full_world_to_pixel's only
# Requires is `dim >= 0`. The model calls it in recovered_pixel with the SAME
# `dim` it was given, and recovered_pixel's own Requires is `dim >= 0`; nothing
# else reaches the callee. So every reachable `dim` satisfies dim >= 0. We make
# this concrete by checking the model's pre/postcondition text encodes dim>=0 in
# every caller and that no other call site exists. (Static, stdlib-only,
# utf-8-safe; runs in-container but reads nothing from disk.)
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

_AX_COVER_PROBE = (
    "import sys, ast\n"
    "SRC = " + repr(_MODEL_SRC) + "\n"
    "tree = ast.parse(SRC)\n"
    "# 1) every call to full_world_to_pixel passes `dim` as its 2nd argument,\n"
    "#    and the only caller is recovered_pixel, whose Requires includes dim>=0.\n"
    "callers = {}\n"
    "for node in ast.walk(tree):\n"
    "    if isinstance(node, ast.FunctionDef):\n"
    "        callers[node.name] = node\n"
    "calls = []  # (enclosing_func, second_arg_src)\n"
    "for fname, fnode in callers.items():\n"
    "    for sub in ast.walk(fnode):\n"
    "        if isinstance(sub, ast.Call) and getattr(sub.func, 'id', None) == 'full_world_to_pixel':\n"
    "            if len(sub.args) != 2:\n"
    "                print('UNEXPECTED arity to full_world_to_pixel:', len(sub.args)); sys.exit(1)\n"
    "            calls.append((fname, ast.dump(sub.args[1])))\n"
    "print('full_world_to_pixel call sites (caller, dim-arg):')\n"
    "for c in calls: print('  ', c)\n"
    "# expected: one call inside recovered_pixel's body passing the param `dim`,\n"
    "# and one inside the postcondition Ensures (also passing `dim`).\n"
    "callers_set = set(f for f, _ in calls)\n"
    "if not callers_set:\n"
    "    print('NO call sites found'); sys.exit(1)\n"
    "if callers_set - {'recovered_pixel'}:\n"
    "    print('UNEXPECTED caller of full_world_to_pixel:', callers_set); sys.exit(1)\n"
    "# 2) the `dim` passed is the parameter `dim`, and recovered_pixel requires dim>=0.\n"
    "rp = callers['recovered_pixel']\n"
    "req_texts = []\n"
    "for sub in ast.walk(rp):\n"
    "    if isinstance(sub, ast.Call) and getattr(sub.func, 'id', None) == 'Requires':\n"
    "        req_texts.append(ast.dump(sub))\n"
    "has_dim_ge_0 = any('dim' in t and 'Gt' not in t.replace('GtE','') and ('GtE' in t or 'Compare' in t) for t in req_texts)\n"
    "# robust check: literal 'dim >= 0' appears in recovered_pixel's source slice\n"
    "rp_src = ''\n"
    "lines = SRC.splitlines()\n"
    "rp_src = '\\n'.join(lines[rp.lineno-1: getattr(rp, 'end_lineno', rp.lineno)])\n"
    "if 'dim >= 0' not in rp_src:\n"
    "    print('recovered_pixel does NOT require dim>=0; axiom Requires(dim>=0) may be unreachable-safe'); sys.exit(1)\n"
    "dim_args = set(a for _, a in calls)\n"
    "non_param = [a for a in dim_args if a != ast.dump(ast.Name(id='dim', ctx=ast.Load()))]\n"
    "if non_param:\n"
    "    print('a full_world_to_pixel call passes a non-`dim` second arg:', non_param)\n"
    "    print('  (still sound iff that arg is provably >=0, but flag for review)')\n"
    "    sys.exit(1)\n"
    "print('AXIOM-CONTAINMENT OK: every full_world_to_pixel call passes the `dim` "
    "parameter; the only caller recovered_pixel requires dim>=0, which is exactly "
    "the axiom Requires(dim>=0). Every caller-reachable callee input is inside the "
    "axiom domain.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-full_world_to_pixel",
        "axiom": "full_world_to_pixel",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the proof consumes full_world_to_pixel's DETERMINISM; the "
                     "real callee self._wcs.world_to_pixel_values must be "
                     "deterministic (and the at-view round-trip must recover the "
                     "slice pixel while the constant-1 fill does not). If the real "
                     "callee violated determinism, the axiom (and the proof) would "
                     "be AXIOM-UNSOUND. Runs the gold-grounded axiom_check.py in "
                     "the instance image.",
    },
    {
        "id": "ax-cover-full_world_to_pixel",
        "axiom": "full_world_to_pixel",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "full_world_to_pixel's Requires is dim>=0; the only model "
                     "caller (recovered_pixel) passes its own `dim`, which its "
                     "Requires pins to dim>=0. Every caller-reachable callee input "
                     "is inside the axiom domain (containment holds); a reachable "
                     "input outside dim>=0 would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
