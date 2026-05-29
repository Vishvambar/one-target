# One-Target

**One-Target** is a terminal-native productivity and accountability tool designed to enforce strict single-tasking. Built specifically for Linux (optimized for Fedora), it uses zero external pip dependencies and relies entirely on Python's standard libraries.

At its core, it features a **3-Bucket Stateful Cycle Assigner** that intelligently rotates through categories (Academic, Project, Extra Learning) to help you maintain balanced progress without decision fatigue.

## Features

- 🔒 **Strict Single-Task Locking:** Once you lock a target, the system blocks you from assigning new tasks until you formally report on the current one (resolving or abandoning it).
- 🔄 **3-Bucket Stateful Cycle:** The `auto` command intelligently analyzes your logs and assigns the highest priority task from the next category in the sequence: `ACADEMIC` → `PROJECT` → `EXTRA_LEARNING`.
- 🗃️ **Local SQLite Database:** All tasks, backlogs, and accountability logs are securely stored locally at `~/.local/share/onetarget/data.db`.
- 👁️ **Terminal Hook:** Automatically injects a silent hook into your `.bashrc` so your active target is printed at the top of every new terminal session. 

## Installation

1. Clone or download this repository.
2. Make the installation script executable:
   ```bash
   chmod +x install.sh
   ```
3. Run the installation script:
   ```bash
   ./install.sh
   ```
4. Reload your terminal environment:
   ```bash
   source ~/.bashrc
   ```

*Note: The script creates a symlink at `~/.local/bin/target`. Ensure this directory is in your system `$PATH`.*

## Commands Reference

The primary executable is `target`.

### Backlog & Auto-Assignment

- **`target add <category> "<description>" <due_date> <priority>`**
  Add a new task to your backlog. 
  - *Categories:* Must be exactly `ACADEMIC`, `PROJECT`, or `EXTRA_LEARNING`.
  - *Priority:* Integer (lower number = higher priority).
  - *Example:* `target add "ACADEMIC" "Study Data Structures" "2026-06-15" 1`

- **`target auto`**
  Evaluates the last completed category, cycles to the next one, and auto-promotes the highest priority pending task from the backlog to become your active target.

### Manual Target Management

- **`target set <category> "<description>"`**
  Bypass the backlog and manually force a new active target right now. Fails if you already have an active target.

- **`target status`**
  Prints your currently active target, its category, and when you started it.

- **`target report ["<your report/log>"]`**
  The only way to unlock the system. It prompts you to mark the active target as `(R)ESOLVED` or `(A)BANDONED` and saves your progress report to the permanent log.
  
- **`target list`**
  Displays a tabulated history of your last 10 tasks and their final statuses.

## Workflow Example

1. Populate your backlog with `target add`.
2. Run `target auto` to lock your first target.
3. Work until finished.
4. Run `target report "Completed chapter 1"` to unlock the system.
5. Run `target auto` to instantly pull your next task from the next category in the cycle.
# one-target
