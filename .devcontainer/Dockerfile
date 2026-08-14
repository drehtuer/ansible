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
    # Ansible
    ansible \
    ansible-lint \
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
