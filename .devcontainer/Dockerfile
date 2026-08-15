# syntax=docker/dockerfile:1
# https://docs.docker.com/reference/dockerfile/
FROM  ubuntu:26.04

LABEL name="Ansible controller" \
    description="Control node running Ubuntu 26.04" \
    version="1.11"

ARG   DEBIAN_FRONTEND=noninteractive
ARG   ARG_USER

ENV   LANG=en_US.utf8

RUN   \
    # apt cache folders as tmpfs, discarded after build.
    # No need to delete these folders later
    --mount=type=tmpfs,target=/var/lib/apt/lists \
    --mount=type=tmpfs,target=/var/cache/apt \
    \
    apt-get update \
    && apt-get upgrade \
    --yes \
    -qq \
    && apt-get install \
    --no-install-recommends \
    --yes \
    -qq \
    # Ansible. ansible-lint is not installed here - see the pinned
    # pip install below.
    ansible \
    # Let's be on the safe side,
    # our default shell should be
    # available
    bash \
    bash-completion \
    # git within devcontainer
    git \
    # locales support
    locales \
    # Python support
    python3.14 \
    python-is-python3 \
    # Invoke to organize cmd commands
    python3-invoke \
    # Molecule and its Docker driver, for the role
    # tests. pip is needed because neither is
    # packaged for Ubuntu 26.04.
    python3-pip \
    python3-venv \
    # User may become root
    sudo \
    # Editor
    neovim \
    luarocks \
    # Network
    ca-certificates \
    curl \
    iputils-ping \
    ssh \
    sshpass \
    wget \
    # Docker CLI, so molecule's docker driver can create and destroy
    # test containers over the host's docker socket, bind-mounted in
    # by devcontainer.json - no daemon runs in the container itself.
    # Ubuntu 26.04 packages its own build, so no extra apt repo (and
    # its distro-version gating) is needed.
    docker.io \
    docker-compose-v2 \
    # The deployment-test VM (.claude/skills/testlab). QEMU runs the
    # guest right here in the container against /dev/kvm, which
    # devcontainer.json passes through - the WSL2 kernel exposes KVM
    # and this host has nested virtualization enabled. No libvirt and
    # no root: the guest uses user-mode networking with a forwarded
    # SSH port, so nothing needs a bridge or NET_ADMIN.
    qemu-system-x86 \
    qemu-utils \
    # cloud-localds, which builds the cloud-init seed image that
    # gives the guest its user, SSH key and hostname on first boot.
    cloud-image-utils \
    # Attaches a terminal to the guest's serial console, which is the
    # way back in when SSH is broken.
    socat \
    # GitHub CLI apt repo, added below,
    # needs its keyring dir to exist first
    && install -d -m 755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install \
    --no-install-recommends \
    --yes \
    -qq \
    # GitHub CLI, not in Ubuntu's own repos
    gh \
    # Generate en_US.UTF-8 locales. No --alias-file: Ubuntu's
    # locales package no longer ships /usr/share/locale/locale.alias.
    && localedef \
    --inputfile=en_US \
    --force \
    --charmap=UTF-8 \
    en_US.UTF-8 \
    # Add non-root user
    && useradd \
    --create-home \
    --user-group \
    --shell /usr/bin/bash \
    ${ARG_USER} \
    # Passwordless sudo: this is a single-user dev environment, not a
    # multi-user host, and fix-docker-gid.sh (run every container
    # start, see devcontainer.json) needs it to fix up group
    # membership for the bind-mounted host docker socket.
    && echo "${ARG_USER} ALL=(ALL) NOPASSWD:ALL" \
    > /etc/sudoers.d/${ARG_USER} \
    && chmod 440 /etc/sudoers.d/${ARG_USER} \
    && inv \
    --print-completion-script=bash \
    > /etc/bash_completion.d/invoke \
    && gh completion \
    --shell bash \
    > /etc/bash_completion.d/gh

# Keep in sync with the versions installed by
# .github/workflows/lint.yml, so CI and the Dev
# Container lint with the same ansible-lint.
# Ubuntu's own ansible-lint package has no version
# pin, which previously let it drift out from under
# the repo silently - see doc/TODO.adoc. yamllint is
# pinned alongside it: Ubuntu only ships it as a
# dependency of the (now unused) ansible-lint
# package, and ansible-lint itself requires a newer
# yamllint than Ubuntu 26.04 packages.
ARG   ANSIBLE_LINT_VERSION=26.8.0
ARG   YAMLLINT_VERSION=1.38.0

RUN   \
    # --system-site-packages, not a fully isolated
    # venv like molecule's below: ansible-lint has to
    # see the same ansible-core and collections the
    # rest of the toolchain uses, not a separate copy
    # of its own, or it aborts with "versions do not
    # match". Installing straight into the system
    # Python instead of a venv was tried first and
    # rejected - Ubuntu's `ansible` package pulls in
    # python3-ansible-compat as a dependency, which
    # has no pip RECORD file and can't be upgraded in
    # place, so pip aborts.
    python3 -m venv \
    --system-site-packages \
    /opt/ansible-lint \
    && /opt/ansible-lint/bin/pip install \
    --quiet \
    --no-cache-dir \
    "ansible-lint==${ANSIBLE_LINT_VERSION}" \
    "yamllint==${YAMLLINT_VERSION}" \
    && ln -s /opt/ansible-lint/bin/ansible-lint /usr/local/bin/ansible-lint \
    && ln -s /opt/ansible-lint/bin/yamllint /usr/local/bin/yamllint

# Keep in sync with the version installed by
# .github/workflows/lint.yml, so CI and the
# Dev Container lint with the same ruff.
ARG   RUFF_VERSION=0.16.3

RUN   \
    # Python linter/formatter, not packaged for
    # Ubuntu 26.04, so install the pinned release
    # binary. uname -m maps to the x86_64/aarch64
    # build names used by upstream.
    curl \
    --location \
    --fail \
    --silent \
    --show-error \
    "https://github.com/astral-sh/ruff/releases/download/${RUFF_VERSION}/ruff-$(uname -m)-unknown-linux-gnu.tar.gz" \
    | tar \
    --extract \
    --gzip \
    --directory=/usr/local/bin \
    --strip-components=1 \
    "ruff-$(uname -m)-unknown-linux-gnu/ruff"

# Keep in sync with the versions installed by
# .github/workflows/test.yml, so CI and the Dev
# Container test with the same molecule.
ARG   MOLECULE_VERSION=26.8.0
ARG   MOLECULE_PLUGINS_VERSION=26.7.15

RUN   \
    # Neither is packaged for Ubuntu 26.04, and pip
    # refuses to install into the system Python
    # (PEP 668), so molecule gets its own virtualenv
    # with the entry point linked onto PATH.
    python3 -m venv /opt/molecule \
    && /opt/molecule/bin/pip install \
    --quiet \
    --no-cache-dir \
    "molecule==${MOLECULE_VERSION}" \
    "molecule-plugins[docker]==${MOLECULE_PLUGINS_VERSION}" \
    && ln -s /opt/molecule/bin/molecule /usr/local/bin/molecule

COPY \
    --chmod=644 \
    ansible-galaxy.yml \
    /ansible-galaxy.yml

RUN \
    ansible-galaxy \
    install \
    --role-file \
    /ansible-galaxy.yml \
    # Collections go to a system-wide path rather than the default
    # ~/.ansible of whoever runs this (root, at build time - the
    # non-root user would never see them). /usr/share/ansible is
    # searched by every ansible-core, including the one inside the
    # molecule virtualenv, which has no collections of its own.
    && ansible-galaxy \
    collection \
    install \
    --requirements-file \
    /ansible-galaxy.yml \
    --collections-path \
    /usr/share/ansible/collections


COPY \
    --chmod=755 \
    fix-docker-gid.sh \
    /usr/local/share/fix-docker-gid.sh

COPY \
    --chmod=755 \
    fix-kvm-perms.sh \
    /usr/local/share/fix-kvm-perms.sh

USER ${ARG_USER}

# Can't set default user here, USER takes
# only a string, but our user name is stored
# in a secret file. Don't want to add an additional
# environment variable, we set the user
# in devcontainer.json via 'remoteUser'.
# This also takes care of mapping uid:gid correctly.

# Keep container running, vscode needs
# to attach to it
CMD [ "sleep", "infinity" ]
