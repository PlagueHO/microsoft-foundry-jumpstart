---
name: create-skill-from-pr

description: "**WORKFLOW SKILL** — Generate a reusable GitHub Copilot Agent Skill from a single-purpose refactoring or tech debt Pull Request. WHEN: \"create skill from PR\", \"generate skill from pull request\", \"PR to skill\", \"reusable refactoring skill\", \"tech debt skill from PR\". INVOKES: GitHub MCP tools, file system. FOR SINGLE OPERATIONS: Use GitHub MCP directly to read PR diffs."

metadata:
  author: plagueho.os
  version: "1.1"
  reference: https://github.com/PlagueHO/plagueho.os/

compatibility:
  - GitHub Copilot
  - GitHub Copilot CLI

argument-hint: Provide a GitHub Pull Request reference (e.g., `owner/repo#123` or full URL) that performs a single refactoring or tech debt remediation task. I will analyze the PR and generate a reusable Agent Skill based on its changes.

user-invocable: true
---

# Create a Reusable Skill from a GitHub Pull Request

Analyze a GitHub PR performing a **single refactoring or tech debt remediation
task** and generate a standalone Agent Skill folder — `SKILL.md` plus optional
bundled assets — reusable across repositories.

Follows the [Agent Skills specification](https://agentskills.io/specification)
and this repository's [skills README](../README.md).

## Prerequisites

- A GitHub PR reference (e.g., `owner/repo#123` or full PR URL).
- GitHub MCP Server tools (`get_pull_request`, `get_pull_request_diff`,
  `get_pull_request_files`) or equivalent access to PR metadata and diff.

## Process

### Step 1 — Retrieve PR Metadata

1. Use `get_pull_request` to collect:
   - Title and description
   - Labels and linked issues
   - Branch names
2. Use `get_pull_request_files` to get the changed file list.
3. Use `get_pull_request_diff` to get the full diff.

### Step 2 — Validate PR Scope

Verify the PR represents a **single, well-defined refactoring or tech debt
remediation task**.

**STOP and ask the user** if:

- The PR mixes unrelated changes (e.g., dependency upgrade *and* code style
  migration).
- The PR is a feature addition, bug fix, or behavioral change — not a
  refactoring/tech debt task.
- The PR description is vague/missing and the diff doesn't indicate a single
  repeatable pattern.
- The diff requires multiple distinct skills to describe.

When stopping:

- List detected change types.
- Explain why they can't form a single skill.
- Ask which subset to focus on.

### Step 3 — Identify the Transformation Pattern

Extract from the validated PR:

1. **Goal** — One-sentence summary of the refactoring
   (e.g., *"Replace deprecated `HttpClientFactory` calls with the new
   `IHttpClientFactory` dependency-injection pattern."*).
2. **Trigger / detection criteria** — How to identify code needing this
   transformation (e.g., file globs, import statements, API usage patterns,
   naming conventions).
3. **Step-by-step transformation** — Ordered mechanical changes from the PR.
   Each step: actionable instruction with before/after examples from the diff.
4. **Edge cases and exceptions** — Non-obvious decisions in the diff
   (e.g., conditional handling for a parameter, intentionally skipped files).
5. **Validation** — How to verify correct transformation
   (e.g., build, lint, or test commands from the PR or CI).
6. **Bundled assets** — Determine if the skill benefits from optional asset
   types in [Bundled Assets (Step 3a)](#step-3a--plan-bundled-assets).

### Step 3a — Plan Bundled Assets

Review the PR diff. Only include assets that help the agent perform the
transformation.

| Directory | Purpose | When to include |
|-----------|---------|-----------------|
| `scripts/` | Executable automation (shell, PowerShell, Python) | PR uses or benefits from a helper script (e.g., bulk renames, AST transforms, API calls) |
| `references/` | Documentation loaded into agent context | Detailed background, API reference, or > 5-step workflow pushing `SKILL.md` over 500 lines |
| `assets/` | Static files used as-is in output | PR produces/consumes static artefacts (images, config baselines, report templates) |
| `templates/` | Starter code the agent customizes per project | PR introduces boilerplate varying by project (e.g., config template, Dockerfile scaffold) |

Ask the user: *"Should I include any helper scripts, reference docs, static
assets, or templates alongside the skill? I recommend: `<your suggestions>`"*

### Step 4 — Generate the Skill

Create the skill directory per [Output Format](#output-format). The skill must:

- Be **self-contained** — followable without knowledge of the original PR.
- Use **concrete before/after code examples** from the PR diff for each step.
- Include only necessary tools and commands.
- Reference the source PR only in metadata, not the instructions body.
- Include `allowed-tools` **only** when specific tools beyond defaults are
  required (see [Frontmatter Reference](#frontmatter-reference)).
- Keep `SKILL.md` **under 500 lines**. Split complex reference material into
  `references/` files.

### Step 5 — Determine Skill Placement

Ask where to save the skill. Suggest:

- **Project skill**: `.github/skills/<skill-name>/SKILL.md` in the current repo.
- **Personal skill**: `~/.copilot/skills/<skill-name>/SKILL.md` for
  cross-project use.

Derive `<skill-name>` from Step 3's goal (lowercase, hyphen-separated, 3–5
words, max 64 chars). Confirm with the user before writing.

### Step 6 — Write and Verify

1. Create the skill directory.
2. Write `SKILL.md`.
3. Write planned bundled assets into subdirectories.
4. Run the [Validation Checklist](#validation-checklist).
5. Present a summary:
   - Generated directory tree
   - Description of each file
   - Decisions or trade-offs made

## Output Format

### Directory Structure

```text
<skill-name>/
├── SKILL.md                 # Required — main instructions
├── scripts/                 # Optional — executable automation
│   └── <script-name>.sh
├── references/              # Optional — docs loaded into context
│   └── <reference-name>.md
├── assets/                  # Optional — static files used as-is
│   └── <asset-name>.ext
└── templates/               # Optional — starter code the agent customizes
    └── <template-name>.ext
```

### SKILL.md Template

Generated `SKILL.md` must follow this template:

````markdown
---
name: <skill-name>
description: >
  <Clear description of what the skill does and when to use it.
  Include trigger keywords for agent discovery. 10–1024 characters.>
# Optional — restrict which tools the agent may use.
# Omit to allow any available tool.
# allowed-tools:
#   - read_file
#   - grep_search
#   - replace_string_in_file
#   - run_in_terminal

metadata:
  author: <author or org>
  version: "<semver>"
  source-pr: "<owner/repo#number>"
  generated-by: create-skill-from-pr
---

# <Skill Title>

<One-paragraph description of the refactoring goal, why it matters, and the
expected outcome.>

## Detection

Identify files and code requiring this transformation:

- File patterns: `<glob patterns>`
- Code patterns: `<search terms, regex, or AST patterns>`

## Steps

1. **<Step title>**

   <Instruction>

   **Before:**

   ```<lang>
   <original code from PR>
   ```

   **After:**

   ```<lang>
   <transformed code from PR>
   ```

2. **<Step title>**

   <Instruction with before/after if applicable>

<!-- Repeat for each distinct step. -->
<!-- For > 5-7 steps, move sub-steps into references/<topic>.md. -->

## Edge Cases

- <Description of an edge case and how to handle it.>

## Validation

1. <Command or check to verify correctness, e.g., build, lint, test.>
2. <Additional verification steps if any.>

## Requirements

- <Any tooling, runtime, or access requirements.>
````

### Frontmatter Reference

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Lowercase, hyphens for spaces, max 64 chars, must match folder name |
| `description` | Yes | 10–1024 chars. State **what**, **when**, include **keywords** |
| `allowed-tools` | No | YAML list of tool names. Omit to allow all tools |
| `metadata.author` | No | Author name or organization |
| `metadata.version` | No | Semver string (e.g., `"1.0"`) |
| `metadata.source-pr` | No | Original PR reference (e.g., `owner/repo#123`) |
| `metadata.generated-by` | No | Set to `create-skill-from-pr` for traceability |

### Bundled Asset Guidelines

- **Scripts** (`scripts/`): Include a comment header with purpose and usage.
  Handle missing dependencies gracefully. Prefer cross-platform approaches or
  provide platform variants.
- **References** (`references/`): Markdown files with detailed documentation,
  API references, or extended steps that would push `SKILL.md` past 500 lines.
  Link from the main body with relative paths.
- **Assets** (`assets/`): Static files consumed or produced by the
  transformation. Keep each under 5 MB.
- **Templates** (`templates/`): Starter code the agent copies and customizes per
  project. Use placeholder comments (e.g., `<!-- TODO: replace -->`) for spots
  the agent fills in.

## Validation Checklist

After generating the skill, verify:

- [ ] Folder name is lowercase with hyphens, max 64 characters
- [ ] `name` field matches folder name exactly
- [ ] `description` is 10–1024 characters, explains what and when
- [ ] `description` includes trigger keywords for agent discovery
- [ ] `SKILL.md` body is under 500 lines
- [ ] All bundled assets are under 5 MB each
- [ ] No hardcoded credentials, secrets, or internal URLs
- [ ] All resource references use relative paths from skill root
- [ ] Before/after code examples present for each transformation step
- [ ] Edge cases documented
- [ ] Validation commands included

## Important Rules

- **Single responsibility**: Each skill addresses exactly one refactoring or
  tech debt pattern. Never combine multiple patterns.
- **No behavioral changes**: The skill must preserve existing behavior. If the
  PR introduced behavioral changes, exclude those parts and note the exclusion.
- **Concrete examples over abstract rules**: Always include before/after code
  from the actual PR diff. Abstract descriptions alone are insufficient.
- **Idempotent guidance**: Steps must be safe to run on already-transformed
  code (detect and skip already-migrated code).
- **Security**: Do not include secrets, credentials, or internal URLs from the
  source PR.
- **Size discipline**: Keep `SKILL.md` under 500 lines. Split large content
  into `references/` files. Keep bundled assets under 5 MB each.

## Example

User: *"Create a skill from PlagueHO/my-project#42"*

1. Retrieve PR #42: renames all `.test.js` files to `.spec.js` and updates
   import paths.
2. Confirm it is a single refactoring task.
3. Identify that a helper script speeds up bulk renames — suggest
   `scripts/rename-tests.sh`.
4. Generate skill `rename-test-to-spec`:

   ```text
   rename-test-to-spec/
   ├── SKILL.md
   └── scripts/
       └── rename-tests.sh
   ```

5. `SKILL.md` contains:
   - **Frontmatter**: `name`, `description`, `metadata` with `source-pr`
   - **Detection**: files matching `**/*.test.js`
   - **Step 1**: Rename `*.test.js` → `*.spec.js`
   - **Step 2**: Update imports referencing old filenames
   - **Edge cases**: Files already using `.spec.js` are skipped
   - **Validation**: `npm test` passes
   - **Requirements**: Node.js, bash (for helper script)
6. Ask the user where to save and write all files.
