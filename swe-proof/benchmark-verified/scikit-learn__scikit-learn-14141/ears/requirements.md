# Requirements: Report the joblib version in scikit-learn's version diagnostics

## Introduction

scikit-learn ships a debugging utility, `sklearn.utils._show_versions`, that
prints system information and the installed versions of the project's main
Python dependencies. The dependency overview is assembled by
`_get_deps_info()` (a helper in `sklearn/utils/_show_versions.py`) and rendered
by the public `show_versions()` function.

Because scikit-learn relies on `joblib` at runtime (parallelism and
serialization), `joblib` must appear in this diagnostic report just like the
other core dependencies (numpy, scipy, pandas, etc.). Today it is missing.

The goal is to make `_get_deps_info()` include `joblib` in its returned
dependency-version mapping (and therefore in the output of `show_versions()`),
without disturbing any of the other reported information.

## Requirement 1: Report the joblib dependency version

**User story:** As a scikit-learn user filing a bug report, I want the version
diagnostics to include `joblib`, so that maintainers can see which joblib
version is installed.

**Acceptance criteria**

1. WHEN `_get_deps_info()` is called, THEN the returned mapping SHALL contain
   an entry keyed `joblib`.
2. WHEN `_get_deps_info()` resolves the `joblib` entry, THEN the helper SHALL
   record the installed `joblib` module's reported version string as that
   entry's value when the module is importable.
3. IF the `joblib` module cannot be imported, THEN `_get_deps_info()` SHALL set
   the `joblib` entry's value to the same null/absent marker it uses for any
   other unavailable dependency, rather than raising an error.
4. WHEN `show_versions()` prints the Python-dependency section, THEN the
   rendered output SHALL include the `joblib` name alongside its resolved
   version.

## Requirement 2: Preserve the existing dependency and system reporting

**User story:** As a maintainer, I want the addition of `joblib` to leave every
other reported field intact, so that existing diagnostics keep working.

**Acceptance criteria**

1. The system SHALL keep every previously reported dependency entry in the
   mapping returned by `_get_deps_info()`, including `pip`, `setuptools`,
   `sklearn`, `numpy`, `scipy`, `Cython`, `pandas`, and `matplotlib`.
2. WHEN `_get_deps_info()` resolves any dependency entry, THEN the helper SHALL
   record that dependency's reported version when importable, or the
   null/absent marker when it is not, applying the same resolution rule to
   every listed dependency.
3. WHEN `_get_sys_info()` is called, THEN the returned mapping SHALL still
   contain the `python`, `executable`, and `machine` entries.
4. WHEN `show_versions()` is called, THEN its printed output SHALL still
   include the system information, the BLAS section, and the Python-dependency
   section (for example the `python` and `numpy` names and a `BLAS` heading).
