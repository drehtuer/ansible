---
name: run-ansible
description: Build, lint, and test this Ansible role/playbook repo. Use when asked to run its tests, run molecule, lint it, render templates, check for drift, or verify a role/playbook change actually works. Not a web/desktop app — driven via the `invoke` task runner and the `.claude/skills/run-ansible/smoke.sh` driver.
---

This repo is Ansible automation (roles + playbooks), not a running app — there's nothing to launch or screenshot. It's driven through `invoke` tasks (`tasks.py`), and the primary agent path is `.claude/skills/run-ansible/smoke.sh`, which runs the static tests and then molecule (if Docker is reachable). All paths below are relative to the repo root.

## Prerequisites

Nothing to install if you're inside the project's Dev Container (`.devcontainer/`) — `ansible`, `ansible-lint`, `yamllint`, `ruff`, `invoke`, `molecule` and `docker` are already on `PATH` there. Verify:

```bash
which invoke ansible ansible-playbook molecule docker
```

## Run (agent path)

```bash
.claude/skills/run-ansible/smoke.sh
```

This always runs `invoke test-static` (renders every `*.j2` template and validates every `meta/argument_specs.yml` against the fake `inventories/test/` inventory — no host or container needed, takes a few seconds). Verified output ends with:

```
TASK [Report] ***
ok: [testhost] => {
    "msg": "10 argument specs validated, 25 templates rendered"
}
PLAY RECAP ***
testhost : ok=10  changed=0  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

It then checks `docker info`. If a daemon is reachable it runs `invoke test-molecule` (extra args are passed through, e.g. `--role=users` to test one role); otherwise it prints why it skipped and leaves it at that — see Gotchas below, this could not be exercised end-to-end in this sandbox.

Test one role directly, bypassing the driver:

```bash
invoke test-molecule --role=users
# or: cd roles/users && molecule test
```

`invoke test-molecule` without `--role` discovers every role under `roles/*/molecule/*/molecule.yml` (today: `apt`, `cron`, `users`) and runs each in turn.

## Test

```bash
invoke test        # test-static, then test-molecule
invoke lint         # yamllint --strict, ansible-lint (production profile), ruff
invoke lint --fix   # same, applying what the tools can fix automatically
```

`invoke test-static` and `invoke lint --fix` (ruff/yamllint parts) were run in this session and pass. `invoke lint` currently fails here — see Troubleshooting.

## Run (human path)

Applying a playbook against real machines or checking drift needs the vault password and SSH access to real hosts, neither of which exist in a sandbox — don't attempt these here:

```bash
invoke run-playbook --playbook=playbooks/users.yml --ask-become-pass
invoke check-drift   # --check --diff against inventories/machines.yml, local only
```

## Gotchas

- **No Docker daemon in this sandbox, and no way to start one.** `docker info` fails (`no such file or directory` on `/var/run/docker.sock`), and `sudo` here demands a password this session doesn't have, so `dockerd` can't be started manually either. In the real Dev Container this is provided by `.devcontainer/docker-init.sh`, run as root via the image's `ENTRYPOINT` (see that repo's own devcontainer PR) — it starts `dockerd --storage-driver=vfs` and waits for the socket. If you land in a shell that has this, `invoke test-molecule` should just work; if you don't, `test-molecule` cannot be exercised and `smoke.sh` will tell you so rather than hang.
- **`molecule test` needs the `community.docker` collection somewhere ansible-core's own collection search path sees** — not just wherever `ansible-galaxy` happens to have put it. The Dockerfile installs collections to `/usr/share/ansible/collections` for exactly this reason (see the comment above the `ansible-galaxy collection install` step in `.devcontainer/Dockerfile`); a collection sitting only under `/usr/lib/python3/dist-packages/ansible_collections` (the apt-packaged one) is invisible to molecule's own virtualenv unless you point `ANSIBLE_COLLECTIONS_PATH` at its **parent** directory (the one containing `ansible_collections/`, not that directory itself) — e.g. `ANSIBLE_COLLECTIONS_PATH=/usr/lib/python3/dist-packages molecule test`. Confirmed in this session: pointing it at `.../ansible_collections` directly still fails with `Collection 'community.docker' not found`; pointing it at the parent fixes that specific error (molecule then gets as far as the Docker-daemon check above).
- **Molecule needs an init-enabled image**, not a plain `ubuntu:24.04`/`26.04` — most roles use `systemd_service`, which needs PID 1 to be systemd. Scenarios already pull `geerlingguy/docker-ubuntu2404-ansible` with `privileged: true` and `/lib/systemd/systemd` as the command; don't change that.
- **`invoke test-molecule --role=<name>` only accepts roles that actually have a scenario** (`roles/<name>/molecule/*/molecule.yml`). Passing an unknown name fails fast with the list of available roles rather than doing anything.

## Troubleshooting

- **`ansible_compat.errors.InvalidPrerequisiteError: Collection 'community.docker' not found in [...]`**: see the collections-path Gotcha above.
- **`ERROR Unable to contact the Docker daemon`**: no `dockerd` reachable — see the Docker-daemon Gotcha above. Not fixable without root in this sandbox.
- **`invoke lint` fails with 18× `var-naming[no-role-prefix]`** (e.g. `roles/http/tasks/main.yml:24` on `set_fact: php_version`, and one per role's `defaults/main.yml`), and reports `Profile 'production' was required, but 'min' profile passed`, even though `doc/STATUS.adoc` claims the whole repo passes `production`. `ansible-lint` is installed unpinned in the Dockerfile (`RUN ... ansible-lint`, no version), so this is very likely version drift between what's on `PATH` here (`ansible-lint 26.1.1`) and whatever version the repo was last actually green against, rather than a real regression to fix as part of an unrelated change. `yamllint --strict` and both `ruff` checks pass cleanly on their own.
