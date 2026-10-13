# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Exception hierarchy.

Every error raised deliberately by this package derives from `BenchproofError`,
so an embedding application can catch the whole surface with one clause.
"""

from __future__ import annotations


class BenchproofError(Exception):
    """Base class for all errors raised by benchproofer."""


class ConfigError(BenchproofError):
    """Settings are missing or inconsistent."""


class PluginError(BenchproofError):
    """A plugin could not be resolved, loaded, or validated."""


class BenchmarkError(BenchproofError):
    """A benchmark could not be fetched or normalized."""


class BundleError(BenchproofError):
    """A bundle is missing required artifacts or violates its schema."""


class MarkerError(BundleError):
    """Marker regions in a solution file are missing, unbalanced, or duplicated."""


class GateError(BenchproofError):
    """A gate could not reach a judgment.

    Raising this is how a gate says "I do not know", which is recorded as an
    ``error`` verdict and never as a finding against the artifact.
    """


class ProviderError(BenchproofError):
    """A language-model provider failed or returned an unusable response."""
