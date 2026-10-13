#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14493 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert and the Acc/list_pred framing)
stripped. The @Pure helper `all_changed` and the proof-lemma methods
`lemma_unfold` / `lemma_change_free_kills` copy over as plain functions
(their contract lines stripped; the lemma bodies are side-effect-free).
`ToSeq` over the PSeq carrier becomes a plain `tuple` shim. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo generator the model models per mapping.md —
`django.contrib.staticfiles.storage.HashedFilesMixin.post_process` — driven
end to end inside the instance image (the gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched code
importable). The modeling boundary, per mapping.md section 2, is the inner
per-pass generator `self._post_process(...)`: the model collapses each pass
to one 0/1 outcome (the OR of that pass's `subst` values). The oracle
therefore stubs `_post_process` on a real storage instance so that pass i
yields a randomized decomposition of tuples whose `subst` values OR together
to exactly `pass_changed[i]` (exercising the real per-pass OR-aggregation),
sets the instance's pass-count attribute to `max_passes`, and runs the real
generator to exhaustion. The observable compared against the shadow's return
value is the value of the post-loop flag the real code consults: True iff
the run-limit sentinel entry (the one carrying a RuntimeError) is yielded.
Any exception escaping the real generator (e.g. an undefined-local read on
the zero-pass path) is itself a disagreement: the shadow always returns a
definite bool.

Type bridge (mapping.md section 2): `max_passes: int` is the instance's
configured pass count; `pass_changed: List[int]` of 0/1 flags is the per-pass
aggregate outcome of the inner generator (flag != 0 iff that pass produced at
least one substitution); the returned bool is the post-loop flag value.
Outputs compare with `==` on bools.

Input domain (the model's Requires): 0 <= max_passes <= len(pass_changed),
flags in {0, 1}. Boundary cases: ALL flag vectors of length 0..8 with EVERY
admissible max_passes (4097 cases, including the zero-pass configuration for
every vector). Fuzz: 100000 randomized (length up to 12, any admissible
count). >= 1e5 Requires-satisfying inputs total. Pinned fuzz seed: 14493.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import itertools
import random
import sys
import tempfile

SEED = 14493
N_FUZZ = 100_000

# --- shims for the model's carrier types --------------------------------------
ToSeq = tuple  # PSeq view of a list -> plain tuple


# --- pure helper from model.py, decorator + contracts stripped ----------------

def all_changed(flags, n):
    if n == 0:
        return True
    return flags[n - 1] != 0 and all_changed(flags, n - 1)


# --- proof-lemma methods from model.py, contracts stripped (bodies are
# --- side-effect-free; kept so the impl region below runs verbatim) -----------

def lemma_unfold(flags, n):
    pass


def lemma_change_free_kills(flags, k, n):
    if k < n - 1:
        lemma_change_free_kills(flags, k, n - 1)


# --- the impl region of model.py, verbatim (contract calls stripped) ----------

def run_passes(pass_changed, max_passes):
    substitutions = False
    i = 0
    while i < max_passes:
        substitutions = pass_changed[i] != 0
        if not substitutions:
            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
            return False
        lemma_unfold(ToSeq(pass_changed), i + 1)
        i = i + 1
    return substitutions


# --- oracle: drive the REAL patched post_process ------------------------------

def make_storage():
    """A minimal concrete storage carrying the real mixin under test."""
    from django.contrib.staticfiles.storage import (HashedFilesMixin,
                                                    StaticFilesStorage)

    class ProbeStorage(HashedFilesMixin, StaticFilesStorage):
        pass

    return ProbeStorage()


def real_post_loop_flag(storage, flags, max_passes, rng):
    """Run the REAL post_process with the inner per-pass generator stubbed at
    the modeling boundary and return the post-loop flag value it consulted
    (True iff the run-limit sentinel was yielded). Returns an exception
    instance if the real generator raised: the shadow never raises inside the
    Requires domain, so that reads as a disagreement."""
    calls = {"n": 0}

    def stub_post_process(paths, adjustable_paths, hashed_files):
        idx = calls["n"]
        calls["n"] += 1
        if idx == 0:
            # the single first pass the real function runs before the
            # counted pass loop; not part of the modeled per-pass outcomes
            return
        flag = flags[idx - 1]
        # decompose the per-pass aggregate into 0..3 yielded quadruples whose
        # subst values OR to the flag, exercising the real OR-aggregation
        if flag:
            k = rng.randint(1, 3)
            subs = [rng.random() < 0.5 for _ in range(k)]
            subs[rng.randrange(k)] = True
        else:
            k = rng.randint(0, 3)
            subs = [False] * k
        for j, s in enumerate(subs):
            yield ("file%d" % j, "file%d.hashed" % j, True, s)

    storage.max_post_process_passes = max_passes
    storage._post_process = stub_post_process
    try:
        try:
            yielded = list(storage.post_process({"dummy": storage},
                                                dry_run=False))
        except Exception as exc:  # a crash is a definite disagreement signal
            return exc
    finally:
        del storage._post_process
        del storage.max_post_process_passes
    return any(isinstance(processed, RuntimeError)
               for _name, _hashed, processed in yielded)


def check_case(storage, flags, max_passes, rng):
    shadow_out = run_passes(list(flags), max_passes)
    real_out = real_post_loop_flag(storage, flags, max_passes, rng)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n  flags=%r max_passes=%r\n"
                "  shadow=%r\n  real=%r"
                % (list(flags), max_passes, shadow_out, real_out))
    return None


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            STATIC_URL="/static/",
            STATIC_ROOT=tempfile.mkdtemp(prefix="conf14493_"),
        )
        django.setup()

    storage = make_storage()
    rng = random.Random(SEED)

    checked = 0
    # boundary: exhaustive over all 0/1 vectors of length 0..8, every count
    for length in range(0, 9):
        for combo in itertools.product((0, 1), repeat=length):
            for max_passes in range(0, length + 1):
                err = check_case(storage, list(combo), max_passes, rng)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    # fuzz: randomized vectors and counts, pinned seed
    for _ in range(N_FUZZ):
        length = rng.randint(0, 12)
        flags = [rng.randint(0, 1) for _ in range(length)]
        max_passes = rng.randint(0, length)
        err = check_case(storage, flags, max_passes, rng)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real post-loop flag on %d inputs "
          "(%d exhaustive boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)"}'
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
