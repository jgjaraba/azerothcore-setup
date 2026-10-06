# ADR-0006: Use azerothcore-setup as the OpenCode project workspace

Status: Accepted
Date: 2026-10-06

## Context

The project previously kept a canonical OpenCode configuration in
`harness/opencode/` and copied it into `/home/dev/azerothcore` before use. This
created two versions of the same configuration, a synchronization script, a
managed-install marker and validation based on copied-file equality. OpenCode
was then launched from the AzerothCore source tree even though the private
project control repository owns the active agent instructions and durable
knowledge.

## Decision

Launch OpenCode directly from `/home/dev/azerothcore-setup`:

```sh
cd ~/azerothcore-setup
opencode
```

The active configuration is `opencode.jsonc`, project instructions are in the
root `AGENTS.md`, and the three project agents are in `.opencode/agents/`.
There is no canonical-versus-installed copy and no harness installation or sync
step.

`/home/dev/azerothcore` is a trusted external project root in the configuration.
Agents may work in both roots. Before substantive work inside AzerothCore,
agents explicitly read its root `AGENTS.md` and applicable nested `AGENTS.md`
files. Upstream instructions govern that repository but do not override private
project rules.

The OpenCode configuration and agents in `azerothcore-setup` are the exact
files executed. The private files formerly installed into AzerothCore are
removed; upstream `.agents/` instructions and unrelated local OpenCode package
metadata remain untouched.

## Alternatives considered

### Continue copying the private configuration into AzerothCore

Rejected: it duplicates active configuration, depends on a sync step and makes
the launched workspace differ from the private repository that owns the setup.

### Put private configuration in global OpenCode settings

Rejected: this would make project behavior depend on machine-wide configuration
and weaken reproducibility.

## Consequences

### Positive

- The ordinary launch command uses the committed project configuration directly.
- Agent access to both project roots is explicit.
- No installation marker, copied configuration, synchronization script or
  copied-file validation remains.
- AzerothCore upstream instructions remain in their own repository and are
  explicitly consulted when required.

### Negative / trade-offs

- The user must launch OpenCode from `azerothcore-setup` for these project
  agents and instructions to load.
- External-directory access to AzerothCore is intentionally trusted in this
  disposable DEV environment.

## References

- `opencode.jsonc`
- `AGENTS.md`
- `.opencode/agents/`
- `scripts/agent/validate-opencode.sh`
- ADR-0001: Keep durable project knowledge outside the AzerothCore checkout
