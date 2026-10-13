-- Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
-- SPDX-License-Identifier: CC-BY-NC-4.0

-- Anchor module for the shared workspace. Importing Velvet.Std here forces the
-- transitive Velvet + Mathlib oleans to be built into .lake/ once, shared
-- read-only across every per-instance bundle.
import Velvet.Std
