# GTUBE is the standard anti-spam test string. By default RSpamd
# treats it as a passthrough result that rejects outright, bypassing
# the thresholds in actions.conf entirely - which makes the spam path
# untestable and is inconsistent with rejecting nothing else.
#
# "all" scores the test patterns normally instead, and enables the
# variants for the other actions (the add_header variant starts with
# Y rather than X). Legitimate mail never contains these strings.
gtube_patterns = "all";

dns {
  nameserver = [ "127.0.0.1" ];
  timeout = 1s;
  sockets = 16;
}
