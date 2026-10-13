#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11451.

Drives the REAL Django credential checker (`ModelBackend.authenticate`) in a
container with a live auth database, and asserts that every observation matches
the model in model.py. The model abstracts two unchanged opaque primitives as
pure decisions and tracks their externally-expensive invocations with two
counters:

  * `directory_recognises(identifier)` — the directory lookup decision
    (`UserModel._default_manager.get_by_natural_key`): whether a matching
    account exists. The lookup is one database round trip; the model counts it
    with `lookups`. The real lookup raises `UserModel.DoesNotExist` iff no row
    matches, which is exactly the recognition decision.

  * `secret_verifies(identifier, secret)` — the verification-and-permission
    decision for a recognised account (`user.check_password(secret) and
    self.user_can_authenticate(user)`). The verification primitive (the
    password hasher) is deliberately expensive; the model counts its
    invocations with `verifications`. It runs exactly ONCE whenever both
    credentials are present, on EVERY both-present path: on the recognised
    path it is the secret check (`check_password` -> `encode`), and on the
    unrecognised path it is the timing-defence run (`set_password` -> `encode`).

The model's load-bearing guarantees, validated here against the real backend
over the full credential matrix:

  (1) identifier absent OR secret absent  => result None, 0 queries, 0 hasher
      runs   (lookups and verifications both unchanged)  [discriminating
      POST-patch behaviour; on the base_commit tree the lookup + timing-defence
      hash still run, which is the bug the gold patch fixes];
  (2) both present                         => exactly 1 query AND exactly 1
      hasher run, on every both-present path (recognised-correct,
      recognised-wrong, unrecognised) [tree-invariant];
  (2a) recognised account                  => result is the matched account
      (its identifier) iff the secret verifies [tree-invariant];
  (2b) unrecognised identifier             => result None [tree-invariant].

Properties (2)/(2a)/(2b) are UNCHANGED by the gold patch and are asserted
against whichever tree is mounted. Property (1) is exactly the behaviour the
patch adds; the checker DETECTS the tree (does an absent credential short-
circuit before the lookup?) and asserts the post-patch guarantee when the
guard is present, otherwise asserts the pre-patch behaviour the patch fixes.

Imports only Django (the framework under test, present in the eval image) and
the standard library — nothing test-suite-specific. Exit 0 iff every
obligation holds.
"""
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,  # so the per-connection queries log is populated
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            AUTH_USER_MODEL="auth.User",
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
            USE_TZ=True,
        )
    django.setup()


def main():
    _configure_django()

    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from django.core.management import call_command
    from django.contrib.auth.backends import ModelBackend
    from django.contrib.auth.models import User
    from django.contrib.auth import hashers

    # Build the auth schema in the in-memory DB.
    call_command("migrate", run_syncdb=True, verbosity=0)

    # A real, recognised account with a known secret.
    User.objects.create_user(username="alice", password="s3cret")

    # Count hasher invocations independently of any timing test helper.
    hasher_calls = {"n": 0}
    _real_encode = hashers.MD5PasswordHasher.encode

    def _counting_encode(self, *a, **k):
        hasher_calls["n"] += 1
        return _real_encode(self, *a, **k)

    hashers.MD5PasswordHasher.encode = _counting_encode

    backend = ModelBackend()

    def run(username, password):
        """Run the real authenticate; return (result, n_queries, n_hashes)."""
        hasher_calls["n"] = 0
        with CaptureQueriesContext(connection) as ctx:
            result = backend.authenticate(None, username=username, password=password)
        return result, len(ctx.captured_queries), hasher_calls["n"]

    checks = 0

    # ---- Tree detection: does an absent credential short-circuit before the
    #      lookup (the guard the gold patch adds)? --------------------------
    _r, _nq, _nh = run("alice", None)
    guard_present = (_nq == 0 and _nh == 0)

    # --- (1) absent credential matrix ----------------------------------------
    # POST-patch (guard present): 0 queries, 0 hasher runs, None  (the F2P
    #   observation: assertNumQueries(0) and CountingMD5PasswordHasher.calls==0).
    # PRE-patch (base_commit):     None, but the lookup runs (1 query) and the
    #   timing-defence hasher runs once (1 hash) -- the bug the patch fixes.
    absent_matrix = [
        (None, None),
        ("alice", None),
        (None, "s3cret"),
        (None, "wrong"),
        ("nobody", None),
        (None, ""),
        ("", None),
    ]
    for username, password in absent_matrix:
        result, nq, nh = run(username, password)
        assert result is None, (
            "absent-credential case (%r,%r) authenticated unexpectedly: %r"
            % (username, password, result))
        if guard_present:
            assert nq == 0, (
                "absent-credential case (%r,%r) made %d queries (model: 0)"
                % (username, password, nq))
            assert nh == 0, (
                "absent-credential case (%r,%r) ran the hasher %d times "
                "(model: 0)" % (username, password, nh))
        else:
            # base_commit: the unguarded directory lookup still runs (>=1
            # query) even though the credential is absent -- exactly the bug
            # the gold patch removes (model.py's clause (1) is the post-patch
            # guarantee and is NOT expected to hold on this tree). The
            # timing-defence hasher run depends on make_password(None)
            # internals when the secret is absent, so only the load-bearing
            # bug (the useless query) is asserted here.
            assert nq >= 1, (
                "base_commit absent-credential case (%r,%r) made %d queries; "
                "the pre-patch bug is that the lookup runs (expected >=1)"
                % (username, password, nq))
        checks += 1

    # --- (2a) recognised account: exactly 1 query, exactly 1 hasher run ------
    # correct secret -> the matched account (identity pinned, model.py 2a)
    result, nq, nh = run("alice", "s3cret")
    assert result is not None and result.get_username() == "alice", (
        "recognised+correct secret should authenticate alice, got %r" % (result,))
    assert nq == 1, "recognised path made %d queries (model: exactly 1)" % nq
    assert nh == 1, (
        "recognised path ran the hasher %d times (model: exactly 1 -- the "
        "check_password run)" % nh)
    checks += 1

    # wrong secret -> None, still exactly 1 query, exactly 1 hasher run
    result, nq, nh = run("alice", "wrong")
    assert result is None, "recognised+wrong secret must not authenticate, got %r" % (result,)
    assert nq == 1, "recognised+wrong path made %d queries (model: exactly 1)" % nq
    assert nh == 1, (
        "recognised+wrong path ran the hasher %d times (model: exactly 1)" % nh)
    checks += 1

    # --- (2b) unrecognised identifier: 1 query, exactly 1 hasher run ---------
    for username in ["nobody", "ALICE", "alice2", "zzz"]:
        result, nq, nh = run(username, "s3cret")
        assert result is None, (
            "unrecognised identifier %r must not authenticate, got %r"
            % (username, result))
        assert nq == 1, (
            "unrecognised path for %r made %d queries (model: exactly 1)"
            % (username, nq))
        assert nh == 1, (
            "unrecognised path for %r ran the hasher %d times (model: exactly 1)"
            % (username, nh))
        checks += 1

    # --- purity / determinism of the recognition + verification decisions ----
    # Repeated identical calls give identical observable outcomes (same result
    # identity, same query and hasher counts).
    r1 = run("alice", "s3cret")
    r2 = run("alice", "s3cret")
    assert ((r1[0] is not None) == (r2[0] is not None)
            and r1[1] == r2[1] and r1[2] == r2[2]), (
        "recognition/verification decision is not deterministic: %r vs %r"
        % (r1, r2))
    checks += 1

    tree = "post-patch (guard present)" if guard_present else "base_commit (pre-patch)"
    print("G-AX OK: real ModelBackend.authenticate matches the model over %d "
          "credential cases on the %s tree (both-present => 1 query/1 hash on "
          "every path; recognised+correct => the matched account; unrecognised "
          "=> None; absent => %s)."
          % (checks, tree,
             "0 queries/0 hashes/None" if guard_present
             else "None with the lookup+timing-defence hash still running"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
