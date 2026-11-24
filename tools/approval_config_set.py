"""`zeus config set|unset` approval-policy invocation pattern for :mod:`tools.approval_detection`."""

# Top-level `zeus` flags that consume a SEPARATE word (`--profile work`): the value-taking subset
# of `zeus_cli._parser.top_level_value_flag_sets`, so `zeus --profile work config set ...` does
# not read "work" as the subcommand. Any other flag is a bare token (`--json`, `--flag=value`).
_ZEUS_TOP_LEVEL_VALUE_FLAGS = (
    r'(?:--profile|-p|--config|--model|-m|--provider|--reasoning|--toolsets|-t'
    r'|--resume|-r|--skills|-s|--oneshot|-z|--usage-file|--in|--cpu-profile)'
)

# `-p`/`--profile` is stripped from ANYWHERE before `--` (`_parser.scan_profile_flag`), so it can sit
# between `config` and `set` or before the key too. A `VAR=value` word may be quoted (`NOTE='a b'`).
_ZEUS_PROFILE_OPTION = r'(?:(?:-p|--profile)[ \t]+[^\s]++|--profile=[^\s]++)'
_SHELL_WORD = r'''(?:[^\s'"]++|'[^']*+'|"[^"]*+")*+'''

# `zeus config set|unset <key>` — the invocations that rewrite the agent's own approval
# policy. Anchored to the INVOCATION (program word, `config set|unset`, policy key), so a read of
# the text (`grep -r 'zeus config set' docs`) stays ungated. Option runs are ATOMIC/possessive:
# nested `(?:\s+...)*` backtracked exponentially on long flag runs (0.34s at 30 flags).
_ZEUS_CONFIG_SET_APPROVAL_POLICY = (
    # The program: the `zeus` binary (or the macOS `ai.zeus`), or the module form
    # `python -m zeus_cli.main` that the updater and the cron lifecycle guard invoke.
    # Optional leading `VAR=value` assignments (`ZEUS_HOME=... zeus config set ...`).
    r'(?>(?:\w++=' + _SHELL_WORD + r'[ \t]+)*)'
    r'(?:(?:(?:[a-z]:)?[^\s:]*?/)?(?:ai\.)?zeus(?:\.exe)?\b'
    r'|(?:(?:[a-z]:)?[^\s:]*?/)?python[0-9.]*(?:\.exe)?\b[ \t]+(?:-[^\s]+[ \t]+)*?-m[ \t]*zeus_cli\.main\b)'
    r'(?>(?:[ \t]+(?:' + _ZEUS_TOP_LEVEL_VALUE_FLAGS + r'[ \t]+[^\s]++'
    r'|--?[\w-]++(?:=[^\s]++)?))*)'  # global options before the subcommand
    r'[ \t]+config(?>(?:[ \t]+' + _ZEUS_PROFILE_OPTION + r')*)'  # `-p` also parses after a subcommand
    r'[ \t]+(?:set|unset)\b[ \t]*'  # the `config set` / `config unset` subcommand
    r'(?>(?:(?:' + _ZEUS_PROFILE_OPTION + r'|--?[\w-]++)[ \t]+)*)'  # `--force`, `-p work`
    r'["\']?(?:approvals(?:\.[\w.-]++)*|command_allowlist)\b'  # the approval-policy key, maybe quoted
)
