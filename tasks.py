"""
python-invoke tasks
https://docs.pyinvoke.org/en/stable.

Collection of shell commands for ansible.
Acts as documentation of the command and
correct parameters as well as shorthand
for complex parameters.
"""

from typing import Any

from invoke import context, task

ANSIBLE = 'ansible'
ANSIBLE_PLAYBOOK = 'ansible-playbook'
INVENTORY = 'dev-inventory.yml'
HOSTS = 'dev'
HOST_MANAGED = 'managed'
LOG_DIR = 'log'


def ctx_run(ctx: context, cmd: list[str]) -> None:
  """
  Boiler plate function to
  flatten the command list
  and run the command.
  """
  ctx.run(' '.join(cmd))


@task
def ssh(ctx: context, host: str = HOST_MANAGED) -> None:
  """
  Login to remote host via `ssh`.
  """
  cmd: list[str] = [
    'ssh',
    host,
  ]
  ctx_run(ctx, cmd)


@task
def clean(ctx: context) -> None:
  """
  Clear temporary/intermediate data.

  Clears:
  - log/*.log
  """
  cmd: list[str] = [
    'rm',
    '-rf',
    f'{LOG_DIR}/*.log',
  ]
  ctx_run(ctx, cmd)


@task
def ping(ctx: context, hosts: str = HOSTS, ask_pass: Any = False) -> None:
  """
  Ping all hosts via ansible
  If no pubkey auth is setup on the
  remote host, the optional
  flag `--ask-pass` is needed to
  switch to password based login.
  Mainly used for testing if all
  remote hosts are available.

  Note: May need an `ssh` login first
        if host key is not known, yet.
  """
  cmd: list[str] = [
    f'{ANSIBLE}',
    '--module-name ping',
    f'--inventory {INVENTORY}',
    hosts,
  ]

  if ask_pass:
    cmd.append('--ask-pass')

  ctx_run(ctx, cmd)


@task
def playbook(ctx: context, hosts: str = HOSTS, ask_pass: Any = False) -> None:
  """
  Run playbook.
  """
  cmd: list[str] = [
    ANSIBLE_PLAYBOOK,
    f'--inventory {INVENTORY}',
    'playbook.yml',
  ]

  if ask_pass:
    cmd.append('--ask-pass')

  ctx_run(ctx, cmd)
