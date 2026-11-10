# ADR-0001: Pipeline loading is the single parse path; config validation cannot be skipped

- Status: accepted
- Date: 2026-11-10
- Issue: #46

## Context

The Pipeline config used to be parsed twice, by two independent modules: `ConfigValidator` (for the validate step) and `JenkinsfileGenerator` (for generation). They disagreed: the validator ignored Blackboard data, dropped its YAML line map, and could not report per-field Feature config errors. A `--no-validation` flag let users skip the validator, but generation validated the same models through Pydantic anyway, so the flag only skipped the *reporting*, not the checks.

## Decision

- One module, Pipeline loading (`generator.core.pipeline_loading`), is the only code that reads and parses a Pipeline config. It applies Blackboard data, parses YAML with line tracking, validates the Pipeline config and every declared Feature config, and returns either a Loaded pipeline or located Validation messages.
- Both `--validate` and generation consume that result. The generator takes a Loaded pipeline, never a path.
- `--no-validation` is removed. Config validation is a precondition of generation and always runs, as does template validation.

## Consequences

- Validation and generation can no longer disagree about whether a config is valid.
- Do not add a second parsing path (e.g. a fast path in the generator, or a separate linter-style validator that re-reads the YAML). Extend Pipeline loading instead.
- Do not reintroduce a flag that skips config validation; there is nothing to generate from an invalid config.
