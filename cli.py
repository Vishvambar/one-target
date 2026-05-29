#!/usr/bin/env python3
import argparse
import sqlite3
import os
import sys

DB_DIR = os.path.expanduser("~/.local/share/onetarget")
DB_PATH = os.path.join(DB_DIR, "data.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

SEQUENCE = ['ACADEMIC', 'PROJECT', 'EXTRA_LEARNING']

def get_db_connection():
    if not os.path.exists(DB_DIR):
        try:
            os.makedirs(DB_DIR)
        except OSError:
            pass
            
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Initialize schema if tables don't exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if not cursor.fetchone():
            if os.path.exists(SCHEMA_PATH):
                with open(SCHEMA_PATH, 'r') as f:
                    conn.executescript(f.read())
            else:
                # Fallback schema if schema.sql is missing
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS backlog (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL CHECK(category IN ('ACADEMIC', 'PROJECT', 'EXTRA_LEARNING')),
                        description TEXT NOT NULL,
                        due_date TEXT,
                        priority INTEGER NOT NULL,
                        status TEXT NOT NULL CHECK(status IN ('PENDING', 'PROMOTED')) DEFAULT 'PENDING',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL CHECK(category IN ('ACADEMIC', 'PROJECT', 'EXTRA_LEARNING')),
                        description TEXT NOT NULL,
                        status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'RESOLVED', 'ABANDONED')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER NOT NULL,
                        report TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(task_id) REFERENCES tasks(id)
                    );
                """)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1)

def get_active_task(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE status = 'ACTIVE' ORDER BY id DESC LIMIT 1")
    return cursor.fetchone()

def cmd_set(args):
    conn = get_db_connection()
    active_task = get_active_task(conn)
    
    if active_task:
        print(f"Error: You already have an active target: '{active_task['description']}'")
        print("Please report on it before setting a new one.")
        sys.exit(1)
        
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (category, description, status) VALUES (?, ?, 'ACTIVE')", (args.category, args.description))
    conn.commit()
    print(f"Target locked manually: [{args.category}] '{args.description}'")
    print("Focus.")

def cmd_add(args):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO backlog (category, description, due_date, priority) 
        VALUES (?, ?, ?, ?)
    """, (args.category, args.description, args.due_date, args.priority))
    conn.commit()
    print(f"Added to backlog: [{args.category}] {args.description} (Priority: {args.priority}, Due: {args.due_date})")

def cmd_auto(args):
    conn = get_db_connection()
    active_task = get_active_task(conn)
    if active_task:
        print(f"Error: You already have an active target: '{active_task['description']}'")
        print("Please report on it before auto-assigning a new one.")
        sys.exit(1)
        
    cursor = conn.cursor()
    
    # Fetch category of the latest entry in the logs table
    cursor.execute("""
        SELECT t.category 
        FROM logs l
        JOIN tasks t ON l.task_id = t.id
        ORDER BY l.created_at DESC 
        LIMIT 1
    """)
    last_log = cursor.fetchone()
    
    last_category = last_log['category'] if last_log else None
    
    if last_category and last_category in SEQUENCE:
        next_idx = (SEQUENCE.index(last_category) + 1) % len(SEQUENCE)
    else:
        next_idx = 0
        
    # Attempt to find a task starting from next_idx
    for i in range(len(SEQUENCE)):
        target_category = SEQUENCE[(next_idx + i) % len(SEQUENCE)]
        
        # Priority ASC (lower number is higher priority), Due Date ASC
        cursor.execute("""
            SELECT id, description, priority, due_date 
            FROM backlog 
            WHERE status = 'PENDING' AND category = ? 
            ORDER BY priority ASC, due_date ASC 
            LIMIT 1
        """, (target_category,))
        
        task = cursor.fetchone()
        
        if task:
            # Promote task
            cursor.execute("""
                INSERT INTO tasks (category, description, status) 
                VALUES (?, ?, 'ACTIVE')
            """, (target_category, task['description']))
            new_task_id = cursor.lastrowid
            
            cursor.execute("UPDATE backlog SET status = 'PROMOTED' WHERE id = ?", (task['id'],))
            conn.commit()
            
            print(f"Target locked (Auto-promoted from {target_category}): '{task['description']}'")
            print("Focus.")
            return
            
    print("Backlog is completely empty. No tasks available to auto-assign.")

def cmd_status(args):
    conn = get_db_connection()
    active_task = get_active_task(conn)
    
    if active_task:
        print(f"ACTIVE TARGET [{active_task['category']}]: {active_task['description']}")
        print(f"Started: {active_task['created_at']}")
    else:
        print("No active target. Run 'target auto' or 'target set' to lock one.")

def cmd_report(args):
    conn = get_db_connection()
    active_task = get_active_task(conn)
    
    if not active_task:
        print("Error: No active target to report on.")
        sys.exit(1)
        
    print(f"Active target [{active_task['category']}]: '{active_task['description']}'")
    
    if not args.report:
        # Prompt user if report is not provided
        args.report = input("Enter your post-mortem/progress report: ").strip()
        
    while True:
        try:
            status = input("Mark as (R)ESOLVED or (A)BANDONED? ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\nReport cancelled.")
            sys.exit(1)
            
        if status in ('R', 'A', 'RESOLVED', 'ABANDONED'):
            if status in ('R', 'RESOLVED'):
                final_status = 'RESOLVED'
            else:
                final_status = 'ABANDONED'
            break
        print("Please enter R or A.")
        
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (final_status, active_task['id']))
    cursor.execute("INSERT INTO logs (task_id, report) VALUES (?, ?)", (active_task['id'], args.report))
    conn.commit()
    print(f"Target {final_status.lower()}. Log saved. System unlocked.")

def cmd_list(args):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, description, status, created_at FROM tasks ORDER BY id DESC LIMIT 10")
    tasks = cursor.fetchall()
    
    if not tasks:
        print("No active/past tasks found.")
        return
        
    print(f"{'ID':<4} | {'CAT':<14} | {'STATUS':<10} | {'DATE':<19} | {'DESCRIPTION'}")
    print("-" * 80)
    for t in tasks:
        print(f"{t['id']:<4} | {t['category'][:14]:<14} | {t['status']:<10} | {t['created_at'][:19]:<19} | {t['description']}")

def cmd_hook(args):
    # Silent command for .bashrc
    try:
        conn = get_db_connection()
        active_task = get_active_task(conn)
        if active_task:
            print(f"[TARGET - {active_task['category']}] {active_task['description']}")
    except:
        pass # Must remain silent

def main():
    parser = argparse.ArgumentParser(description="One-Target Scheduler - Stateful Cycle Assigner")
    parser.add_argument("--hook", action="store_true", help=argparse.SUPPRESS)
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    parser_set = subparsers.add_parser("set", help="Manually set a new active target")
    parser_set.add_argument("category", type=str, choices=SEQUENCE, help="Category of the target")
    parser_set.add_argument("description", type=str, help="Description of the target")
    
    parser_add = subparsers.add_parser("add", help="Add a new task to the backlog")
    parser_add.add_argument("category", type=str, choices=SEQUENCE, help="Category of the task")
    parser_add.add_argument("description", type=str, help="Description of the task")
    parser_add.add_argument("due_date", type=str, help="Due date (e.g. YYYY-MM-DD)")
    parser_add.add_argument("priority", type=int, help="Priority (integer, lower is higher priority)")
    
    parser_auto = subparsers.add_parser("auto", help="Auto-assign the next target from the backlog")
    
    parser_status = subparsers.add_parser("status", help="Print the current active target")
    
    parser_report = subparsers.add_parser("report", help="Report on the active target to unlock the system")
    parser_report.add_argument("report", type=str, nargs='?', default=None, help="Your post-mortem/progress report")
    
    parser_list = subparsers.add_parser("list", help="Display history of the last 10 tasks")
    
    args = parser.parse_args()
    
    if args.hook:
        cmd_hook(args)
        return
        
    if args.command == "set":
        cmd_set(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "auto":
        cmd_auto(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
