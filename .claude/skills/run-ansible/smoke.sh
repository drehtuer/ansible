#!/usr/bin/env bash
# Drives this repo's automated checks the way an agent should: static
# tests always (fast, no container needed), molecule only if the
# Docker daemon is actually reachable (it needs one per role
# container). See ../../../doc/TESTING.adoc for what each layer
# catches.
#
# The bind-mounted host docker socket (see devcontainer.json) is only
# usable as root in a shell that predates fix-docker-gid.sh's group
# fix (see the Gotchas section in SKILL.md) - so molecule runs via
# `sudo -E`, preserving this shell's PATH so it still finds the
# molecule virtualenv.
#
# Usage: smoke.sh [--role=<role> ...]
# Extra args are passed straight through to `invoke test-molecule`.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$repo_root"

echo "== invoke test-static =="
invoke test-static

if sudo -n docker info >/dev/null 2>&1; then
  echo "== sudo invoke test-molecule $* =="
  sudo -E env "PATH=$PATH" invoke test-molecule "$@"
else
  cat <<'EOF'
== skipping invoke test-molecule: `sudo -n docker info` failed ==
   Either the Docker daemon isn't running, or this session has no
   passwordless sudo. See the Gotchas section in SKILL.md.
EOF
fi
