# Delivery-time filing, run for every user via sieve_before.
#
# RSpamd's milter adds `X-Spam: Yes` to anything at or above the
# add_header threshold in roles/spam/files/rspamd/actions.conf. That
# is the only thing this looks at - the score itself is in
# X-Spamd-Result if a human wants to know why.
#
# :create so the mailbox exists on first spam even for an account that
# has never opened it. `stop` prevents any later rule filing it again.
require ["fileinto", "mailbox"];

if header :contains "X-Spam" "Yes" {
    fileinto :create "Spam";
    stop;
}
