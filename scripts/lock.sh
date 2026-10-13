#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Record the package versions installed in the active environment.
#
#   bash scripts/lock.sh
#
# Writes constraints/<platform>-<interpreter>.txt, which scripts/setup.sh applies
# on a matching platform so that an install resolves to a tested dependency tree.
# Run this after changing a dependency in pyproject.toml, and commit the result.
#
# Constraints are not requirements: nothing here is installed unless pyproject.toml
# asks for it, directly or through another package.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
. "${here}/lib/common.sh"

require_python
lock="$(lock_file)"
mkdir -p "$(dirname -- "${lock}")"

# The filter lives in a Python file rather than a heredoc: this script's standard
# input is the pip output being read.
"${PYTHON}" -m pip freeze --exclude-editable |
  "${PYTHON}" "${here}/lib/lockfile.py" "$(platform_tag)" >"${lock}"

info "wrote $(relative "${lock}") ($(grep -c '==' "${lock}") pins)"
