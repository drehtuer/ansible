require ["vnd.dovecot.pipe", "copy", "imapsieve"];
if true {
  pipe :copy "rspamd-learn-spam.sh";
}
