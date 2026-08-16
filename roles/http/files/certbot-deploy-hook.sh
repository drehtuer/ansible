#!/bin/sh
# Reload the services that use the Let's Encrypt certificate after
# certbot renews it, and then check that DANE still holds.
#
# Runs from /etc/letsencrypt/renewal-hooks/deploy/, i.e. only when a
# certificate was actually renewed. Also runnable by hand, and by
# roles/http, as `certbot-deploy-hook.sh --verify` to do the DANE check
# alone against the live certificate.
set -eu

VERIFY_ONLY=0
[ "${1:-}" = "--verify" ] && VERIFY_ONLY=1

LINEAGE="${RENEWED_LINEAGE:-}"
if [ -z "${LINEAGE}" ]; then
  # Not called by certbot. Fall back to the only lineage on this host.
  LINEAGE="$(find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d | head -1)"
fi
CERT="${LINEAGE}/cert.pem"

if [ "${VERIFY_ONLY}" -eq 0 ]; then
  for unit in nginx postfix dovecot; do
    if systemctl is-active --quiet "${unit}"; then
      systemctl reload "${unit}" || true
    fi
  done
fi

# --- DANE ------------------------------------------------------------
#
# The TLSA records in roles/nsd pin this certificate's public key
# (3 1 1). roles/http passes --reuse-key so a renewal keeps that key and
# the pin stays true - but that is a convention, not a guarantee. A
# recreated lineage, a --force-renewal without key reuse, or a lost
# reuse_key line all change the key, and nothing else would notice: the
# certificate is perfectly valid, so every ordinary check passes while
# senders that validate DANE refuse the mail outright.
#
# Hence this. It cannot fix the records - they live in vault-encrypted
# inventory - but it can make the breakage loud at the moment it
# happens rather than whenever someone next looks.
#
# The names to check come from the certificate's own SANs rather than
# from configuration, so this stays correct when a domain is added
# without anyone remembering to update the hook.
[ -r "${CERT}" ] || { echo "no certificate at ${CERT}" >&2; exit 1; }

spki="$(openssl x509 -in "${CERT}" -pubkey -noout \
        | openssl pkey -pubin -outform DER \
        | openssl sha256 -r | cut -d' ' -f1)"

mismatch=""
for name in $(openssl x509 -in "${CERT}" -noout -ext subjectAltName 2>/dev/null \
              | tr ',' '\n' | sed -n 's/.*DNS://p' | grep '^mail\.' || true); do
  published="$(dig +short TLSA "_25._tcp.${name}" 2>/dev/null \
               | tr -d ' ' | sed 's/^311//' | tr 'A-Z' 'a-z')"
  [ -n "${published}" ] || continue          # no TLSA published for this name
  if [ "${published}" != "${spki}" ]; then
    mismatch="${mismatch}  _25._tcp.${name}
    published: ${published}
    certificate: ${spki}
"
  fi
done

if [ -n "${mismatch}" ]; then
  body="DANE is broken on $(hostname -f).

The TLSA records published in DNS no longer match the certificate this
host presents on port 25. Senders that validate DANE will refuse mail to
the affected domains until the records are corrected.

${mismatch}
Fix: update the TLSA value in nsd.zones for each name above to the
certificate hash, bump nothing (the signer owns the serial), and run
playbooks/nsd.yml. Then re-check with:

  certbot-deploy-hook.sh --verify
"
  echo "${body}" >&2
  # This host runs a mail server and root is aliased to a real address,
  # so mail is the one channel certain to be seen. Failing the hook
  # alone would only reach certbot's log.
  command -v mail >/dev/null 2>&1 && \
    echo "${body}" | mail -s "DANE mismatch on $(hostname -f)" root || true
  exit 1
fi

[ "${VERIFY_ONLY}" -eq 1 ] && echo "DANE ok: published TLSA matches the certificate"
exit 0
