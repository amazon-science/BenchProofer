# Requirements: FITS format identification for non-FITS paths

## Introduction

The FITS format-identifier `is_fits` in `astropy/io/fits/connect.py` is used by
the unified I/O registry's `identify_format` (`astropy.io.registry`) to decide
whether a given input denotes a FITS source. It receives the operation
`origin`, a `filepath`, a `fileobj`, and any additional positional arguments
(`*args`).

A regression made the function crash with `IndexError: tuple index out of
range` whenever it was asked to identify a path that has no FITS filename
extension and no positional arguments were supplied (for example, when the I/O
registry probes every registered identifier for a non-FITS filename such as an
`.ecsv` path). This happened because, for a path without a recognised FITS
extension, the function stopped returning a definite answer and instead fell
through to an unconditional access of the first positional argument
(`args[0]`), which is absent in that call pattern.

The goal is to make `is_fits` always yield a definite boolean verdict for a
path input — including a negative verdict for a path that is not a FITS file —
so that identification of non-FITS inputs no longer depends on, or indexes
into, the positional arguments.

## Requirement 1: Definite verdict for filename paths

**User story:** As a user calling `identify_format` (or otherwise driving the
astropy I/O registry) on a filename, I want the FITS identifier to give a clear
yes/no answer based on the filename, so that identifying a non-FITS file never
raises an error.

**Acceptance criteria**

1. WHEN `is_fits` is called with no readable file object but with a non-empty
   `filepath`, THEN `is_fits` SHALL return a boolean determined solely by
   whether the path matches a recognised FITS filename, without accessing any
   positional argument.
2. WHEN `is_fits` is called with such a `filepath` whose name, compared
   case-insensitively, ends with one of the recognised FITS suffixes
   (`.fits`, `.fits.gz`, `.fit`, `.fit.gz`, `.fts`, `.fts.gz`), THEN `is_fits`
   SHALL return `True`.
3. WHEN `is_fits` is called with such a `filepath` whose name, compared
   case-insensitively, ends with none of the recognised FITS suffixes, THEN
   `is_fits` SHALL return `False`.
4. IF `is_fits` is called with a `filepath` that has no FITS extension and with
   no positional arguments supplied, THEN `is_fits` SHALL return `False` and
   SHALL NOT raise `IndexError` or any other exception.
5. WHEN a caller invokes the I/O registry's `identify_format` for a non-FITS
   filename with an empty positional-argument list, THEN the FITS identifier
   SHALL contribute a negative (non-matching) result rather than propagating an
   error.

## Requirement 2: Preserve file-object and object-based identification

**User story:** As a maintainer relying on existing FITS-identification
behavior, I want the readable-stream and in-memory-object detection paths to
keep working exactly as before, so that the fix introduces no regression.

**Acceptance criteria**

1. WHEN `is_fits` is called with a readable file object, THEN `is_fits` SHALL
   read its leading 30 bytes, restore the object's original stream position,
   and return `True` only if those bytes equal the FITS signature.
2. WHILE a readable file object is provided, the FITS identifier SHALL base its
   verdict on that object's leading bytes and SHALL NOT consult the `filepath`
   or the positional arguments.
3. WHEN `is_fits` is called with neither a readable file object nor a
   `filepath`, and at least one positional argument is supplied, THEN `is_fits`
   SHALL return `True` if and only if the first positional argument is an
   instance of one of the recognised FITS object types (an HDU list, a table
   HDU, a binary-table HDU, or a groups HDU).
4. The FITS identifier SHALL continue to return correct positive verdicts for
   genuine FITS filenames and FITS objects, so that reading and writing tables
   through the FITS format via the registry continues to select the FITS format
   as before.
