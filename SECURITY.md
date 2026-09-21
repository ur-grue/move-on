# Security Policy

## Scope

Move On handles your private chat history on disk. Bugs that matter most:

- Data leaving the machine (any network call outside `escalate --send`)
- Files written outside `MOVEON.d/` or with permissions wider than 0600/0700
- Path traversal or resource exhaustion via crafted export archives
- Chat content appearing in error output, logs, or tracebacks

## Reporting

Email the maintainer via the address on the GitHub profile, or open a
[private security advisory](https://github.com/ur-grue/move-on/security/advisories/new).
Please do not open a public issue for a vulnerability.

You will get a reply within 7 days. Fixes for confirmed issues ship as a
patch release with a CHANGELOG entry.

## Supported versions

Only the latest release receives security fixes.
