#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13410 (nagini).

SHADOW: the impl region of model.py (``acquire`` / ``release``), copied
VERBATIM below with only the contract calls (Requires/Ensures) stripped.
The two @ContractOnly callees (``primitive_lock`` / ``primitive_release``)
are grounded in the REAL unchanged library callee they axiomatize per
mapping.md section 3: CPython's ``fcntl.flock``, invoked on a real file
descriptor of the shadow world with the trial's real flags. An out-of-band
``OSError`` from the real callee is surfaced as the model's
``LockUnavailable`` (the user-defined stand-in of mapping.md section 2).

ORACLE: the REAL patched repo helpers per mapping.md section 1 —
``django.core.files.locks.lock`` / ``unlock`` (the POSIX branch, the one
compiled inside the instance container). The gate applies patch.diff to
/testbed and sets PYTHONPATH=/testbed before running this script, so the
import resolves to the patched module.

TYPE BRIDGE (mapping.md section 2): the model carrier ``available`` is the
single observable bit "does the requested lock operation complete
normally". Each trial instantiates it as a concrete world: one temporary
file with an independent pre-existing holder descriptor that either does or
does not hold an incompatible flock, plus the subject descriptor the
checked helper then locks (non-blocking whenever contention is expected, so
nothing ever waits). The oracle and shadow worlds are configured
identically, and the helpers' boolean returns are compared directly
(identical concrete type). The WORLD-STATE EFFECT behind the booleans (the
``lock_held()`` / ``lock_freed()`` tokens of the spec) is compared
observationally: a third descriptor's non-blocking exclusive probe must be
refused while a side reports holding the lock and granted after that side
releases, identically for shadow and oracle.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): the helpers' precondition
is termination only, so every scenario below is in-domain. Boundary phase:
full enumeration of holder/request compatibility (no holder, shared holder,
exclusive holder, crossed with shared/exclusive requests, blocking and
non-blocking where the request completes, non-blocking where it contends),
crossed with both argument forms the repo helper accepts (file object and
raw integer fd), plus release-without-prior-acquisition probes. Fuzz phase:
100000 trials drawing scenario and argument form from a pinned PRNG.
Pinned seed: 13410 (the instance number; recorded in mapping.md section 5).

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import sys
import tempfile

SEED = 13410
N_FUZZ = 100000


# --- support declarations from model.py (the exception stand-in) -------------

class LockUnavailable(Exception):
    """Model stand-in for the out-of-band contention signal of the real
    low-level callee (mapping.md section 2)."""
    pass


# NO value sentinel is declared here, deliberately. The model's value clause is
# `Ensures(Result() is None)` -- the primitives hand back THE EMPTY VALUE, not a
# stand-in number -- so the shadow primitives below hand back the real callee's
# own return value unchanged. Substituting a number here would make the shadow
# disagree with the axiom it is meant to instantiate, on exactly the axis the
# reported boolean is decided.


# --- a concrete lock world instantiating the abstract `available` bit --------

class World(object):
    """One temporary file with three independent open file descriptions:
    ``holder`` (the pre-existing other party), ``subject`` (the descriptor
    the checked helper operates on) and ``observer`` (a third party used
    only for the effect probes)."""

    def __init__(self, tag):
        import fcntl  # POSIX-only; the instance container is Linux
        self.fcntl = fcntl
        fd, self.path = tempfile.mkstemp(prefix="conf13410_%s_" % tag)
        os.close(fd)
        self.holder = open(self.path, "rb")
        self.subject = open(self.path, "rb")
        self.observer = open(self.path, "rb")

    def configure(self, holder_mode):
        """Reset all three descriptions, then have the other party hold
        ``holder_mode`` (a flock mode, or None for no pre-existing lock)."""
        fcntl = self.fcntl
        for f in (self.holder, self.subject, self.observer):
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        if holder_mode is not None:
            fcntl.flock(self.holder.fileno(), holder_mode | fcntl.LOCK_NB)

    def observer_contends(self):
        """AGGREGATE reading: True iff a third party's non-blocking exclusive
        request is refused right now (i.e. SOME description holds a lock).
        Cannot attribute the lock to a particular description, so it is only a
        faithful stand-in for the model's holds_lock() when the subject is the
        only possible holder."""
        fcntl = self.fcntl
        try:
            fcntl.flock(self.observer.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True
        fcntl.flock(self.observer.fileno(), fcntl.LOCK_UN)
        return False

    def subject_holds(self):
        """PER-DESCRIPTION reading — the model's holds_lock() (mapping.md §1):
        does the SUBJECT description itself still hold a claim?

        `flock(2)` locks belong to open file descriptions, so the aggregate
        probe above cannot answer this whenever another description holds a
        compatible claim. This drops the OTHER party's claim first, so any
        remaining lock can only be the subject's. It is therefore DESTRUCTIVE of
        the holder's claim and must be called only after the trial's own
        observations are finished; `configure()` rebuilds the world per trial.
        """
        fcntl = self.fcntl
        try:
            fcntl.flock(self.holder.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        return self.observer_contends()

    def close(self):
        for f in (self.holder, self.subject, self.observer):
            try:
                self.fcntl.flock(f.fileno(), self.fcntl.LOCK_UN)
            except OSError:
                pass
            f.close()
        try:
            os.unlink(self.path)
        except OSError:
            pass


# --- @ContractOnly callees grounded in the REAL unchanged library callee -----
# mapping.md section 3: the axiomatized primitives ARE fcntl.flock. The shadow
# therefore invokes the real fcntl.flock on the shadow world's subject
# descriptor with the trial's real flags. The `available` parameter is not
# consulted here: the driver configured the world so the real callee completes
# normally exactly on the available case, and it cross-checks that afterwards.

def _assert_empty_value(value, which):
    """Axioms-region sanity on every shadow primitive call: the real callee's
    normal-completion value must be THE EMPTY VALUE, as the axiom says, and must
    answer none of the questions a number answers. If it ever did answer one, a
    body could decide the reported boolean by interrogating the value, and this
    shadow -- which discards the value, as the checked impl region does -- would
    stop being a faithful instantiation of the axiom."""
    if value is not None:
        print("AXIOM DRIFT: real %s success value %r is not the empty value"
              % (which, value))
        sys.exit(1)
    if value:
        print("AXIOM DRIFT: real %s success value %r counts as 'set'"
              % (which, value))
        sys.exit(1)


_SHADOW_WORLD = None   # set per trial by the driver
_SHADOW_FLAGS = 0      # real flock flags for the current trial


def primitive_lock(available):
    fcntl = _SHADOW_WORLD.fcntl
    try:
        ret = fcntl.flock(_SHADOW_WORLD.subject.fileno(), _SHADOW_FLAGS)
    except OSError:
        raise LockUnavailable()
    _assert_empty_value(ret, "acquisition")
    return ret


def primitive_release():
    fcntl = _SHADOW_WORLD.fcntl
    ret = fcntl.flock(_SHADOW_WORLD.subject.fileno(), fcntl.LOCK_UN)
    _assert_empty_value(ret, "release")
    return ret


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def acquire(available):
    try:
        primitive_lock(available)
        return True
    except LockUnavailable:
        return False


def release():
    primitive_release()
    return True


# --- oracle: the real patched repo helpers ------------------------------------

def real_locks():
    from django.core.files import locks
    return locks


# --- scenario table -------------------------------------------------------------

def scenarios(fcntl):
    EX, SH, NB = fcntl.LOCK_EX, fcntl.LOCK_SH, fcntl.LOCK_NB
    return [
        # (name, holder_mode, request_flags, available)
        ("free-ex-nb",  None, EX | NB, True),
        ("free-ex-blk", None, EX,      True),
        ("free-sh-nb",  None, SH | NB, True),
        ("free-sh-blk", None, SH,      True),
        ("sh-sh-nb",    SH,   SH | NB, True),   # compatible: completes
        ("sh-sh-blk",   SH,   SH,      True),   # compatible: completes
        ("sh-ex-nb",    SH,   EX | NB, False),  # incompatible: contends
        ("ex-ex-nb",    EX,   EX | NB, False),  # incompatible: contends
        ("ex-sh-nb",    EX,   SH | NB, False),  # incompatible: contends
    ]


# --- differential driver ---------------------------------------------------------

def run_trial(locks, ow, sw, scen, use_raw_fd):
    """One acquire (+release when acquired) trial on identically configured
    oracle and shadow worlds; returns an error string on disagreement."""
    global _SHADOW_WORLD, _SHADOW_FLAGS
    name, holder_mode, flags, available = scen
    fcntl = ow.fcntl
    # AGGREGATE effect probe: only meaningful when the subject's exclusive lock
    # is the sole lock in its world (a pre-existing holder would mask it).
    do_effect = holder_mode is None and bool(flags & fcntl.LOCK_EX)
    # PER-DESCRIPTION effect probe: valid in EVERY scenario, including the
    # shared-holder ones the aggregate probe cannot speak about. This is the
    # observable the model's holds_lock() actually denotes, so comparing it is
    # what makes the exit-state clauses conformance-checked rather than
    # merely asserted. Run LAST in each trial because it drops the holder.
    do_subject_effect = True

    # oracle side (real patched repo helpers)
    ow.configure(holder_mode)
    f_arg = ow.subject.fileno() if use_raw_fd else ow.subject
    oracle_acq = locks.lock(f_arg, flags)
    oracle_held = ow.observer_contends() if do_effect else None
    oracle_rel = locks.unlock(f_arg) if oracle_acq else None
    oracle_freed = ((not ow.observer_contends())
                    if (do_effect and oracle_acq) else None)

    # shadow side (contract-stripped impl region over the real callee)
    sw.configure(holder_mode)
    _SHADOW_WORLD, _SHADOW_FLAGS = sw, flags
    shadow_acq = acquire(available)
    shadow_held = sw.observer_contends() if do_effect else None
    shadow_rel = release() if shadow_acq else None
    shadow_freed = ((not sw.observer_contends())
                    if (do_effect and shadow_acq) else None)

    # PER-DESCRIPTION exit-state comparison (after all aggregate observations).
    # On the acquire-success path the subject must hold its claim; after the
    # release it must not. Compared oracle-vs-shadow in every scenario.
    oracle_subject = ow.subject_holds() if do_subject_effect else None
    shadow_subject = sw.subject_holds() if do_subject_effect else None
    if oracle_subject != shadow_subject:
        return ("DISAGREEMENT on per-description exit state, scenario %r "
                "(available=%r, flags=%r, arg=%s):\n"
                "  shadow (impl region)  subject-holds=%r\n"
                "  real (patched locks)  subject-holds=%r"
                % (name, available, flags,
                   "raw fd" if use_raw_fd else "file object",
                   shadow_subject, oracle_subject))
    # The model's release clause Ensures(holds_lock() is False) must hold on the
    # REAL callee under this reading, in every scenario -- including the
    # shared-holder world where the aggregate probe still answers "held".
    if oracle_acq and oracle_rel and oracle_subject:
        return ("AXIOM UNSOUND on scenario %r: after the real release the "
                "SUBJECT still holds its claim, contradicting "
                "Ensures(holds_lock() is False)" % (name,))

    if ((shadow_acq, shadow_rel, shadow_held, shadow_freed)
            != (oracle_acq, oracle_rel, oracle_held, oracle_freed)):
        return ("DISAGREEMENT on scenario %r (available=%r, flags=%r, "
                "arg=%s):\n"
                "  shadow (impl region)  acquire=%r release=%r "
                "held-effect=%r freed-effect=%r\n"
                "  real (patched locks)  acquire=%r release=%r "
                "held-effect=%r freed-effect=%r"
                % (name, available, flags,
                   "raw fd" if use_raw_fd else "file object",
                   shadow_acq, shadow_rel, shadow_held, shadow_freed,
                   oracle_acq, oracle_rel, oracle_held, oracle_freed))
    if shadow_acq != available:
        # world-setup cross-check: the abstract bit and the real completion
        # must coincide by construction of the configured world
        return ("INTERNAL: world setup drift on scenario %r — real "
                "completion %r != abstract available %r"
                % (name, shadow_acq, available))
    return None


def release_only_trial(locks, ow, sw, use_raw_fd):
    """Release on a subject that holds no lock.

    An EXECUTABLE-SHAPE probe on the impl region, not a model-domain claim: the
    release helper is documented as dropping a claim the caller already holds,
    so a caller with no claim is not the situation the contract describes. What
    is checked here is only that the contract-stripped impl region and the real
    patched `unlock` still agree on the reported boolean in this degenerate
    world (both report True, since `flock(LOCK_UN)` on an unheld description
    succeeds) -- i.e. the impl region has no hidden dependence on there being a
    prior acquisition. No exit-state clause is asserted for it."""
    global _SHADOW_WORLD, _SHADOW_FLAGS
    ow.configure(None)
    f_arg = ow.subject.fileno() if use_raw_fd else ow.subject
    oracle_rel = locks.unlock(f_arg)

    sw.configure(None)
    _SHADOW_WORLD, _SHADOW_FLAGS = sw, 0
    shadow_rel = release()

    if shadow_rel != oracle_rel:
        return ("DISAGREEMENT on release-without-acquisition (arg=%s):\n"
                "  shadow (impl region)  release=%r\n"
                "  real (patched locks)  release=%r"
                % ("raw fd" if use_raw_fd else "file object",
                   shadow_rel, oracle_rel))
    return None


def main():
    if os.name == "nt":
        # The modeled branch is the POSIX one; it does not exist here.
        print(json.dumps({"status": "skip",
                          "reason": "non-POSIX host: modeled branch absent"}))
        return 0
    locks = real_locks()
    ow, sw = World("oracle"), World("shadow")
    checked = 0
    try:
        scens = scenarios(ow.fcntl)

        # boundary: full scenario enumeration x both argument forms
        for scen in scens:
            for use_raw_fd in (False, True):
                err = run_trial(locks, ow, sw, scen, use_raw_fd)
                if err:
                    print(err)
                    return 1
                checked += 1
        for use_raw_fd in (False, True):
            err = release_only_trial(locks, ow, sw, use_raw_fd)
            if err:
                print(err)
                return 1
            checked += 1
        n_boundary = checked

        # randomized fuzz over the scenario table (pinned seed)
        rng = random.Random(SEED)
        for _ in range(N_FUZZ):
            scen = scens[rng.randrange(len(scens))]
            use_raw_fd = bool(rng.getrandbits(1))
            err = run_trial(locks, ow, sw, scen, use_raw_fd)
            if err:
                print(err)
                return 1
            checked += 1
    finally:
        ow.close()
        sw.close()

    print("G-CONF OK: shadow impl == real patched lock/unlock on %d trials "
          "(%d boundary + %d fuzz, seed %d); booleans, release reports and "
          "held/freed effect probes all agree; 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "primitives grounded in the real fcntl.flock)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
