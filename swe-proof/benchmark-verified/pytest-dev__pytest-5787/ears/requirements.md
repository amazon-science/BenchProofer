# Requirements: preserve chained exceptions across report serialization

## Introduction

pytest can reduce a test/collection report to a plain, builtin-only data
structure and later reconstruct the report from that data. This round trip is
what lets distributed test runners (for example `pytest-xdist`) send a failure
representation from a worker process back to the controlling process. The
relevant code lives in `src/_pytest/reports.py`: the `BaseReport._to_json`
method reduces a report to builtin data, and the `BaseReport._from_json`
classmethod rebuilds a report (a `TestReport` or `CollectReport`) from that
data.

A report's failure representation is carried in its `longrepr` attribute. When a
failing test raised an exception that was chained to other exceptions (via
`raise ... from ...`, i.e. an explicit `__cause__`, or via an exception raised
while handling another, i.e. an implicit `__context__`), the failure
representation is an `ExceptionChainRepr` (from `_pytest._code.code`). This
object holds an ordered list of links — one per exception in the chain — where
each link is a triple of (traceback representation, crash-location
representation, and a human-readable description string that introduces the next
exception, e.g. "The above exception was the direct cause of the following
exception:" or "During handling of the above exception, another exception
occurred:"; the description is absent for the final/outermost link). A failure
with no chaining is instead represented by a `ReprExceptionInfo`, which carries a
single traceback and crash location.

The defect: at the base revision the serialization step recorded only the
outermost exception's traceback and crash and discarded the chain links, and the
reconstruction step always rebuilt a single-exception `ReprExceptionInfo`. As a
result, a chained exception collapsed to just its final exception after a round
trip — which is why, under `pytest-xdist`, chained-exception failures printed
only the last exception while a plain (non-distributed) run printed the whole
chain.

The goal is to make the serialize/deserialize round trip in
`src/_pytest/reports.py` preserve the entire exception chain — every link, in
order, including each link's description — so that a reconstructed report
displays the complete chained traceback, while leaving the single-exception case
and all surrounding report-serialization behavior unchanged.

## Requirement 1: Serialize the full exception chain

**User story:** As a developer using a distributed test runner, I want a chained
exception's failure representation to be fully captured when a report is reduced
to builtin data, so that no exception in the chain is lost in transport.

**Acceptance criteria**

1. WHEN `_to_json` is called on a report whose `longrepr` is an
   `ExceptionChainRepr`, THEN the produced data SHALL include an ordered
   collection of records representing every link of the chain, with the same
   count and same order as the original chain (no link dropped, none reordered).
2. WHEN serializing such a chained representation, THEN for each link the
   produced data SHALL record that link's traceback representation, its
   crash-location representation, and its description string (or the absence of a
   description for a link that has none).
3. WHEN `_to_json` is called on a report whose `longrepr` is a single-exception
   representation (a `ReprExceptionInfo`, i.e. not chained), THEN the produced
   data SHALL indicate the absence of any chain (so that reconstruction rebuilds
   a single-exception representation, not a chained one).
4. The system SHALL, for any failure representation that exposes a traceback and
   a crash location, continue to record that outermost traceback
   representation, outermost crash-location representation, and the
   representation's attached sections in the produced data.

## Requirement 2: Reconstruct the full exception chain

**User story:** As a developer, I want the report rebuilt from transported data
to contain the complete exception chain, so that the reconstructed failure
matches what a local run would show.

**Acceptance criteria**

1. WHEN `_from_json` is given data that includes a non-empty ordered chain of
   links, THEN the reconstructed report's `longrepr` SHALL be an
   `ExceptionChainRepr` whose chain has the same number of links, in the same
   order, as were recorded.
2. WHEN reconstructing a chained representation, THEN each rebuilt link SHALL
   carry the traceback representation, crash-location representation, and
   description recorded for that link, so that the reconstructed chain is
   equivalent to the original.
3. IF the transported failure data records the absence of a chain, THEN
   `_from_json` SHALL reconstruct a single-exception representation
   (`ReprExceptionInfo`) rather than a chained one.
4. WHEN reconstructing any failure representation that carries a traceback and
   crash location, THEN `_from_json` SHALL restore its sections onto the rebuilt
   representation.
5. The reconstruction of chained and single-exception representations SHALL
   behave identically for both `TestReport` and `CollectReport` report types.

## Requirement 3: Round-trip fidelity for chained exceptions

**User story:** As a developer, I want serializing then deserializing a chained
failure to reproduce the original failure, so that transported reports are
faithful.

**Acceptance criteria**

1. WHEN a report whose `longrepr` is an `ExceptionChainRepr` is reduced to data
   by `_to_json` and that data is passed to `_from_json`, THEN the resulting
   report's `longrepr` SHALL again be an `ExceptionChainRepr` with the same
   number of links, in the same order, as the original.
2. WHEN such a round trip is performed on a chain of length two or more (a
   genuinely multi-stage failure), THEN the reconstructed chain SHALL NOT
   collapse to a single link; every intermediate and originating exception's
   traceback text and each link's description SHALL be recoverable from the
   reconstructed representation.
3. WHEN sections were attached to the failure representation before
   serialization, THEN the reconstructed representation SHALL carry the same
   sections after the round trip.
4. WHEN the reconstructed chained representation is rendered to a terminal
   writer, THEN it SHALL render without error.

## Requirement 4: Preserve single-exception serialization behavior

**User story:** As a developer, I want the pre-existing behavior for
non-chained failures and for the surrounding report fields to be unchanged, so
that fixing the chained case introduces no regression.

**Acceptance criteria**

1. WHEN a report whose `longrepr` is a single-exception `ReprExceptionInfo` is
   round-tripped through `_to_json` and `_from_json`, THEN the reconstructed
   `longrepr` SHALL be a `ReprExceptionInfo` preserving its traceback,
   crash location, and sections.
2. WHEN `_to_json` serializes a report, THEN it SHALL continue to convert any
   filesystem-path-valued report attributes to their string form and SHALL
   continue to represent the report's captured `result` as absent, matching the
   pre-existing serialization framing.
3. WHEN a report's `longrepr` is a plain string (or otherwise carries no
   traceback/crash structure), THEN `_to_json` SHALL preserve it as-is (as a
   string or its original value) and a round trip SHALL leave it recoverable.
4. WHEN `_from_json` encounters a serialized per-frame traceback record whose
   recorded type is not a recognized kind, THEN it SHALL raise an error
   reporting the unexpected type rather than silently producing a malformed
   report.
5. The system SHALL keep the serialized data composed only of builtin data
   types (such as dicts, lists, tuples, strings, numbers, and None) so that it
   remains suitable for transport.
