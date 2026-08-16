#!/bin/sh
# Reload the services that use the Let's Encrypt certificate after
# certbot renews it. Without this they keep serving the expired one
# until something restarts them by chance.
#
# Runs from /etc/letsencrypt/renewal-hooks/deploy/, i.e. only when a
# certificate was actually renewed.
set -eu

for unit in nginx postfix dovecot; do
  if systemctl is-active --quiet "${unit}"; then
    systemctl reload "${unit}" || true
  fi
done
