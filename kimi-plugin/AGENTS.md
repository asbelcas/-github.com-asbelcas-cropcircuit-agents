# Kimi Plugin Architecture

A task delegation and background job management system for kimi-cli, inspired by OpenAI's codex-plugin-cc.

## Structure

```
kimi-plugin/
├── AGENTS.md              # This file
├── commands/              # Command definitions (markdown)
├── prompts/               # Prompt templates
├── scripts/               # Python implementation
│   └── kimi-companion.py  # Main companion script
├── skills/                # kimi-cli skills
│   └── kimi-task-runtime/
│       └── SKILL.md
└── state/                 # Job state storage (runtime)
```

## Installation

The skill is auto-installed to kimi-cli's skill directory:
- Source: `cropcircuit/kimi-plugin/skills/kimi-task-runtime/`
- Target: `~/.local/share/uv/tools/kimi-cli/lib/python3.13/site-packages/kimi_cli/skills/kimi-task-runtime/`

## Usage

### From kim-cli

```bash
# The skill is automatically available
# See: /kimi-task-runtime
```

### Direct Python

```bash
cd cropcircuit

# Run a task
python3 kimi-plugin/scripts/kimi-companion.py task "Explain this codebase"

# Run in background
python3 kimi-plugin/scripts/kimi-companion.py task "Analyze dependencies" --background

# Check all jobs
python3 kimi-plugin/scripts/kimi-companion.py status

# Check specific job
python3 kimi-plugin/scripts/kimi-companion.py status 20260401-102500-abc123

# Get result
python3 kimi-plugin/scripts/kimi-companion.py result 20260401-102500-abc123

# Cancel job
python3 kimi-plugin/scripts/kimi-companion.py cancel 20260401-102500-abc123

# Review code
python3 kimi-plugin/scripts/kimi-companion.py review
```

## Architecture

### Job Lifecycle

1. **Create** → `pending` state
2. **Start** → `running` state  
3. **Complete** → `completed` / `error` / `timeout` / `cancelled`

### State Storage

Jobs are stored as JSON files in:
- `~/.kimi/kimi-plugin-state/jobs/<job-id>.json`

Each job contains:
- `id`: Unique job identifier
- `type`: Task type (task, review, etc.)
- `prompt`: The original prompt
- `status`: Current state
- `result`: Output when complete
- `pid`: Process ID (for background jobs)
- Timestamps: `created_at`, `started_at`, `completed_at`

### Comparison to codex-plugin-cc

| Feature | codex-plugin-cc | kimi-plugin |
|---------|-----------------|-------------|
| Language | Node.js | Python |
| CLI | `codex` | `kimi` |
| Plugin system | Claude Code native | kimi-cli skills |
| Job storage | Filesystem | Filesystem |
| Background jobs | ✅ | ✅ |
| Status tracking | ✅ | ✅ |
| Cancel | ✅ | ✅ |
| Review | ✅ | ✅ |

## Commands Reference

### task
Run a kimi task with optional background execution.

### status
List jobs or check specific job status.

### result
Retrieve completed job output.

### cancel
Terminate a running job.

### review
Code review using git context.
