###############################################################################
# export PATH=$HOME/Software/codium/bin:$PATH
export PATH=$HOME/Software/pycharm/bin:$PATH
export PATH=$HOME/Software/python/bin:$PATH
# export LD_LIBRARY_PATH=$HOME/Software/python/lib:$LD_LIBRARY_PATH

export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# export PATH=$HOME/Software/snowsql:$PATH
export PATH=$HOME/Software/jedit:$PATH
# export PATH=$HOME/Software/chromium-latest-linux:$PATH

set -o vi
export PS1="\n\u@\H:\w $ "
export PS1="\n\w $ "
export VISUAL=vim
export EDITOR="$VISUAL"

umask 0022

. ~/.alias
. ~/.function
# . ~/.password

###############################################################################
###############################################################################
# From https://www.thomaslaurenson.com/blog/2018-07-02/better-bash-history/
HISTTIMEFORMAT='%F %T '
HISTFILESIZE=-1
HISTSIZE=10000
HISTCONTROL=ignoredups'

om history configuration
# Configure BASH to append (rather than overwrite the history):'
shopt -s histappend

# Attempt to save all lines of a multiple-line command in the same entry'
shopt -s cmdhist

# After each command, append to the history file and reread it'
export PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND$"\n"}history -a; history -c; history -r"

###############################################################################


# The next line updates PATH for the Google Cloud SDK.
if [ -f '/home/jason/Software/google-cloud-sdk/path.bash.inc' ]; then . '/home/jason/Software/google-cloud-sdk/path.bash.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/home/jason/Software/google-cloud-sdk/completion.bash.inc' ]; then . '/home/jason/Software/google-cloud-sdk/completion.bash.inc'; fi
