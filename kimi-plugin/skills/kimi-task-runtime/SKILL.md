---
name: kimi-task-runtime
description: Task delegation and background job management for kimi-cli
user-invocable: true
---

# Kimi Task Runtime

Use this skill to delegate tasks to background kimi processes and manage long-running jobs.

## Commands

### Run a task
```bash
python3 kimi-plugin/scripts/kimi-companion.py task "your prompt here"
```

### Run in background
```bash
python3 kimi-plugin/scripts/kimi-companion.py task "your prompt" --background
```

### Check status
```bash
python3 kimi-plugin/scripts/kimi-companion.py status
python3 kimi-plugin/scripts/kimi-companion.py status <job-id>
```

### Get result
```bash
python3 kimi-plugin/scripts/kimi-companion.py result <job-id>
```

### Cancel job
```bash
python3 kimi-plugin/scripts/kimi-companion.py cancel <job-id>
```

### Review code
```bash
python3 kimi-plugin/scripts/kimi-companion.py review
```

## Job States

- `pending` - Job created but not started
- `running` - Currently executing
- `completed` - Finished successfully
- `error` - Failed with error
- `timeout` - Exceeded time limit
- `cancelled` - Manually cancelled

## State Storage

Jobs are stored in: `~/.kimi/kimi-plugin-state/jobs/`
