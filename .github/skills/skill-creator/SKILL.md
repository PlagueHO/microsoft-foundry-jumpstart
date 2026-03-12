---
name: skill-creator

description: >-
  **WORKFLOW SKILL** — Create a new Agent Skill from a user's description and
  goal, following the agentskills.io specification. Scaffolds directory structure,
  generates SKILL.md with YAML frontmatter, and validates the result. WHEN:
  "create a skill", "new skill", "scaffold a skill", "build a skill", "make a
  skill for", "generate skill", "skill from scratch", "add a new agent skill".
  INVOKES: run_in_terminal for scaffolding scripts. FOR SINGLE OPERATIONS: Use
  directly to create the SKILL.md file manually.

metadata:
  author: plagueho.os
  version: "1.0"
  reference: https://agentskills.io/specification

compatibility:
  - GitHub Copilot
  - GitHub Copilot CLI
  - VS Code

argument-hint: >-
  Describe what the skill should do (e.g., "a skill that generates Bicep
  modules from a requirements description") and optionally where to save it
  (e.g., `.github/skills/` or `~/.copilot/skills/`).

user-invocable: true
---

# Skill Creator

Create a new [Agent Skill](https://agentskills.io/specification) from a user's
description and goal. The workflow interviews the user, scaffolds the directory
structure, generates a conformant `SKILL.md`, optionally creates bundled assets
(scripts, references, templates), and validates the result against the spec.

## Prerequisites

- **Node.js** (for `npx skills-ref validate` — optional but recommended).
- **PowerShell 7+** (Windows) or **Bash** (macOS/Linux) for scaffolding scripts.

## Process

### Step 0 — Extract from Conversation

Before asking questions, review the conversation history. If the user has been
following a multi-step workflow, methodology, or repeatable process (e.g., a
debugging approach, review checklist, refactoring pattern, deployment procedure),
generalize it into a reusable skill. Extract:

- The **step-by-step process** being followed.
- **Decision points** and branching logic.
- **Quality criteria** or completion checks.
- **Tools and commands** used at each step.

If an existing prompt file (`.prompt.md`) is provided as input, treat its
instructions as the workflow to convert — extract the process, inputs,
outputs, and validation steps from the prompt and map them to skill structure.

If no clear workflow emerges from context, proceed to Step 1.

### Step 1 — Capture Intent

Understand what the skill should do. If the user has already described the goal,
or if Step 0 extracted a workflow, derive the answers below from what is already
known. Otherwise, ask:

1. **Purpose**: What should this skill enable the agent to do?
2. **Trigger**: When should the skill activate? (user phrases, keywords, contexts)
3. **Output**: What is the expected result? (files, code, terminal commands, etc.)
4. **Tools**: Does the skill need specific tools? (e.g., `run_in_terminal`,
   `fetch_webpage`, MCP tools)
5. **Placement**: Where should the skill live?
   - **Project skill**: `.github/skills/<skill-name>/` (this repo)
   - **Personal skill**: `~/.copilot/skills/<skill-name>/` (cross-project)
   - **Custom path**: user-specified location

Derive a `<skill-name>` from the purpose: lowercase, hyphens for spaces, 1–64
characters, no leading/trailing/consecutive hyphens. Confirm with the user.

### Step 2 — Research and Plan

Before writing, gather context:

1. **Check for similar existing skills** on
   [skillsdirectory.org](https://www.skillsdirectory.org/) using `fetch_webpage`.
   If a relevant skill already exists, **STOP** and ask the user whether to
   adopt it, adapt it, or proceed with a new one.
2. **Search the codebase** for patterns, conventions, or prior art that the
   skill should reference.
3. **Plan bundled assets** — decide whether the skill needs:

   | Directory | Purpose | When to include |
   |-----------|---------|-----------------|
   | `scripts/` | Executable automation (PowerShell, Shell, Python) | Task has deterministic/repeatable steps that benefit from scripting |
   | `references/` | Documentation loaded into agent context | Detailed background that would push SKILL.md past 500 lines |
   | `assets/` | Static resources (templates, schemas, config files) | Skill consumes or produces static artefacts |

   If scripts are needed, **always provide both PowerShell (.ps1) and Shell
   (.sh) variants** for cross-platform support.

4. **Ask the user** to confirm the plan: *"Here is what I plan to create:
   `<directory tree>`. Should I proceed?"*

### Step 3 — Scaffold the Skill

Use the scaffolding scripts to create the directory structure and template
`SKILL.md`. The scripts are in this skill's `scripts/` directory.

**PowerShell** (Windows):

```powershell
& "<skill-creator-path>/scripts/New-AgentSkill.ps1" `
    -Name "<skill-name>" `
    -Description "<description>" `
    -OutputPath "<target-parent-directory>" `
    -Author "<author>" `
    -IncludeScripts `
    -IncludeReferences `
    -IncludeAssets
```

**Shell** (macOS/Linux):

```bash
"<skill-creator-path>/scripts/new-agent-skill.sh" \
    --name "<skill-name>" \
    --description "<description>" \
    --output-path "<target-parent-directory>" \
    --author "<author>" \
    --include-scripts \
    --include-references \
    --include-assets
```

The scripts create the directory tree and a template `SKILL.md` with all
required frontmatter fields pre-populated.

### Step 4 — Write the SKILL.md Body

Edit the generated `SKILL.md` to add the full skill instructions. Follow
these writing guidelines:

#### Frontmatter

| Field | Required | Guidelines |
|-------|----------|------------|
| `name` | Yes | 1–64 chars, lowercase `a-z`, digits, hyphens only. Must match directory name. |
| `description` | Yes | 1–1024 chars. State **what** the skill does AND **when** to use it. Include trigger keywords. Make descriptions slightly "pushy" to improve triggering. |
| `license` | No | License name or path to bundled LICENSE file. |
| `compatibility` | No | Environment requirements (tools, runtimes, network access). |
| `metadata` | No | Arbitrary key-value pairs (author, version, reference URL). |

> **Note:** Do NOT include `allowed-tools` in generated skills. This field is not compatible with GitHub Copilot.

#### Description Best Practices

**Good** — specific, includes trigger keywords, explains when to use:

```yaml
description: >-
  Extract text and tables from PDF files, fill PDF forms, and merge
  multiple PDFs. Use when working with PDF documents or when the user
  mentions PDFs, forms, or document extraction.
```

**Bad** — vague, no trigger context:

```yaml
description: Helps with PDFs.
```

#### Body Writing Patterns

- Use **imperative form** for instructions ("Create the file", not "You should
  create the file").
- Include **step-by-step instructions** with clear headings.
- Provide **input/output examples** where applicable.
- Document **edge cases** and how to handle them.
- Keep the body **under 500 lines**. Move detailed reference material to
  `references/` files.
- Use **relative paths** from the skill root when referencing bundled files.
- Explain **why** instructions matter — agents respond better to reasoning than
  rigid MUST/NEVER directives.

#### Progressive Disclosure

Skills load in three levels — design for efficient context use:

1. **Metadata** (~100 tokens): `name` + `description` — always in the agent's
   context for all skills.
2. **SKILL.md body** (< 5000 tokens recommended): Full instructions — loaded
   when the skill triggers.
3. **Bundled resources** (as needed): `scripts/`, `references/`, `assets/` —
   loaded on demand.

### Step 5 — Create Bundled Assets

If the plan includes bundled assets, create them now.

#### Scripts (`scripts/`)

- Include a comment header with purpose and usage.
- Handle missing dependencies gracefully with clear error messages.
- **Always provide both PowerShell and Shell variants.**
- Make scripts self-contained or document dependencies clearly.

#### References (`references/`)

- Markdown files with focused, detailed documentation.
- Include a table of contents for files over 300 lines.
- Link clearly from the main `SKILL.md` body.

#### Assets (`assets/`)

- Static files consumed or produced by the skill.
- Keep each file under 5 MB.
- Use placeholder comments for spots the agent should customize.

### Step 6 — Validate

Run validation to ensure the skill conforms to the
[Agent Skills specification](https://agentskills.io/specification).

**Using NPX** (recommended if Node.js is available):

```bash
npx skills-ref validate "<skill-directory-path>"
```

**Manual checklist** — verify all of the following:

- [ ] Directory name is lowercase with hyphens, 1–64 characters
- [ ] `name` field matches directory name exactly
- [ ] `name` contains only lowercase letters, digits, and hyphens
- [ ] `name` does not start or end with a hyphen
- [ ] `name` does not contain consecutive hyphens (`--`)
- [ ] `description` is 1–1024 characters, non-empty
- [ ] `description` explains what the skill does AND when to use it
- [ ] `description` includes trigger keywords for agent discovery
- [ ] `compatibility` (if present) is 1–500 characters
- [ ] `SKILL.md` body is under 500 lines
- [ ] All bundled file references use relative paths from skill root
- [ ] No hardcoded credentials, secrets, or internal URLs
- [ ] Scripts (if any) exist in both PowerShell and Shell variants
- [ ] All files are under 5 MB each

### Step 7 — Present the Result

Show the user:

1. The generated directory tree.
2. A summary of each file and its purpose.
3. The full `description` field for review — this is the primary triggering
   mechanism, so getting it right is critical.
4. Any trade-offs or decisions made.

Ask: *"Does this look correct? Would you like to adjust the description,
add more steps, or include additional bundled assets?"*

## Quick Reference — `name` Field Rules

| Rule | Example | Valid? |
|------|---------|--------|
| Lowercase only | `pdf-processing` | Yes |
| Digits allowed | `gpt4-helper` | Yes |
| Uppercase | `PDF-Processing` | No |
| Leading hyphen | `-pdf` | No |
| Trailing hyphen | `pdf-` | No |
| Consecutive hyphens | `pdf--processing` | No |
| Over 64 characters | `this-is-a-very-long-...` | No |

## Skill Directory Structure Reference

```text
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable automation
│   ├── do-thing.ps1  #   PowerShell variant
│   └── do-thing.sh   #   Shell variant
├── references/       # Optional: detailed documentation
│   └── REFERENCE.md
├── assets/           # Optional: templates, schemas, static resources
│   └── template.md
└── LICENSE           # Optional: license file
```
