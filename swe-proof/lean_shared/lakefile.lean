-- Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
-- SPDX-License-Identifier: CC-BY-NC-4.0

import Lake
open Lake DSL

-- Shared Mathlib + Velvet workspace for all 500 per-instance bundles.
-- Velvet is pinned by exact commit (see PINS.md); Mathlib + Loom + cvc5/z3
-- are pulled transitively at the revisions Velvet's own lake-manifest fixes,
-- so we never bump Mathlib independently.
require Velvet from git
  "https://github.com/verse-lab/velvet.git" @ "2cf0acb04c510848e597aa6214b7665fea86319d"

package «lean_shared» where
  leanOptions := #[⟨`pp.unicode.fun, true⟩]

-- A trivial library target so `lake build` has something local to anchor on;
-- the real payload is the transitive Velvet + Mathlib oleans in .lake/.
@[default_target]
lean_lib «LeanShared» where
