# Duplicate-code similarity threshold of zero disables the check

## Introduction

Pylint's duplicate-code detection lives in `pylint/checkers/similar.py`. The
`Similar` engine compares a set of appended source files and reports blocks of
consecutive similar lines whose length meets or exceeds a configurable
threshold. That threshold is exposed two ways:

- the `min-similarity-lines` option of the `SimilarChecker` (config field
  `min_similarity_lines`, mirrored onto the engine's `min_lines` attribute), and
- the `-d` / `--duplicates` command-line option of the standalone `symilar`
  entry point (`pylint.checkers.similar.Run`).

Today, setting the threshold to `0` does not turn the check off. Because zero is
compared against the count of matching lines, every line trivially satisfies the
threshold and the engine reports essentially all code as duplicated. Users
expect a threshold of `0` to behave the way it does in other linters (e.g.
flake8), namely to **disable** the check entirely.

The goal is: a threshold of `0` disables duplicate-code analysis (no comparison,
no report, no messages), while every positive threshold keeps producing exactly
the same similarity analysis and report as before. This document specifies the
observable behavior involved, localized to the `Similar` engine's run/analysis
path and the standalone `symilar` runner.

## Requirement 1: A zero threshold disables the similarity analysis

**User story:** As a user configuring pylint, I want setting the duplicate-code
line threshold to `0` to turn the check off, so that I can disable duplicate-code
detection the same way a `0` disables numeric checks in other linters.

**Acceptance criteria**

1. WHEN the similarity engine's configured minimum-similar-lines threshold is
   `0` and its analysis run is invoked, THEN the engine SHALL perform no
   similarity comparison and SHALL produce no output.
2. WHEN the analysis run is invoked with a threshold of `0`, THEN the engine
   SHALL NOT emit any duplicate-code report text to standard output (the
   captured standard-output content SHALL be empty).
3. WHEN the analysis run is invoked with a threshold of `0`, THEN the engine
   SHALL NOT compute or accumulate any similarity/duplication results and SHALL
   NOT raise any duplicate-code message.
4. IF the threshold is `0`, THEN the disabling behavior SHALL take effect
   regardless of how many source files have been appended and regardless of
   their content (including files that would otherwise be reported as
   duplicates).

## Requirement 2: The standalone `symilar` runner honors a zero threshold and exits cleanly

**User story:** As a user of the `symilar` command line tool, I want passing a
duplicates threshold of `0` to disable duplicate detection and exit successfully,
so that scripting around the tool sees a clean, empty result.

**Acceptance criteria**

1. WHEN the standalone runner (`Run`) is invoked with the duplicates threshold
   option set to `0`, THEN it SHALL run the engine with a threshold of `0` and
   SHALL write nothing to standard output.
2. WHEN the standalone runner completes with a threshold of `0` and at least one
   input file argument, THEN it SHALL terminate by exiting the process with
   status code `0` (success).
3. The standalone runner SHALL parse the duplicates threshold option value as an
   integer, so that a supplied value of `0` reaches the engine as the integer
   `0`.

## Requirement 3: Positive thresholds keep the existing analysis and report unchanged

**User story:** As a user relying on duplicate-code detection, I want any
nonzero threshold to behave exactly as it did before, so that disabling on `0`
does not weaken normal detection.

**Acceptance criteria**

1. WHEN the analysis run is invoked with a threshold of `1` or greater, THEN the
   engine SHALL compute similarities among the appended files and SHALL render
   and emit the resulting duplication report exactly as it did prior to this
   change.
2. The engine SHALL treat only the exact value `0` as the disable signal; any
   other threshold value SHALL leave the analysis enabled.
3. WHEN a threshold of `1` or greater is configured through the checker option,
   THEN duplicate-code messages SHALL continue to be raised for blocks of
   similar lines whose length meets or exceeds that threshold, and the
   duplicated-line statistics SHALL continue to be reported as before.

## Requirement 4: Preserve the existing similarity-detection behavior and options

**User story:** As a maintainer, I want all pre-existing similarity behaviors and
configuration options to remain intact, so that adding the zero-disables rule is
purely additive.

**Acceptance criteria**

1. The engine SHALL continue to strip and ignore comment lines from the
   comparison when comment-ignoring is enabled, and SHALL continue to compare
   them when it is disabled.
2. The engine SHALL continue to strip and ignore docstrings when
   docstring-ignoring is enabled.
3. The engine SHALL continue to strip and ignore import statements (including
   multi-line imports) when import-ignoring is enabled, and SHALL continue to
   include imports in the comparison when it is disabled.
4. The engine SHALL continue to strip and ignore function/method signatures
   (including class methods and empty functions) when signature-ignoring is
   enabled, and SHALL continue to include them when it is disabled.
5. The engine SHALL continue to disregard lines without meaningful content so
   that they do not trigger a similarity match.
6. WHEN invoked with a help request, THEN the standalone runner SHALL display
   usage information; WHEN invoked with no file arguments, THEN it SHALL display
   usage information and exit with a nonzero status.
7. The engine SHALL continue to expose its per-file map data unchanged for the
   parallel map/reduce path.
