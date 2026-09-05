#!/usr/bin/env python3
"""
BEDA Automated Business Enquiry Handling System
Batch CLI Runner, Seeder, and Development Server
"""

import os
import sys
import argparse
import uvicorn

from app.config import DATABASE_PATH, DATA_PATH, ANTHROPIC_API_KEY
from app.database import init_db, get_db_connection
from app.seeder import seed_database_from_file
from app.orchestrator import process_enquiry, process_all_enquiries
from app.entity_resolver import run_level_1_crm_resolution

def cmd_reset(args):
    """Resets SQLite database file and re-seeds from data/data.md."""
    print("--- Resetting BEDA SQLite Database ---")
    if os.path.exists(DATABASE_PATH):
        try:
            os.remove(DATABASE_PATH)
            print(f"[OK] Removed existing database: {DATABASE_PATH}")
        except Exception as e:
            print(f"[WARN] Could not remove {DATABASE_PATH}: {e}")

    init_db(DATABASE_PATH)
    seed_database_from_file(DATA_PATH, db_path=DATABASE_PATH)
    print(f"[OK] Database re-initialized and seeded cleanly from {DATA_PATH}.")

def cmd_seed(args):
    """Seeds database defensively from data/data.md."""
    print(f"--- Seeding Database from {DATA_PATH} ---")
    init_db(DATABASE_PATH)
    seed_database_from_file(DATA_PATH, db_path=DATABASE_PATH)
    print("[OK] Seeding complete.")

def cmd_process(args):
    """Processes enquiries through the multi-stage pipeline."""
    is_live = args.live and bool(ANTHROPIC_API_KEY)
    use_fixtures = not is_live

    mode_label = "LIVE LLM (Claude Haiku 4.5 & Sonnet 5)" if is_live else "DETERMINISTIC FIXTURES"
    print("\n" + "=" * 65)
    print(" BEDA Automated Business Enquiry Handling Pipeline")
    print(f" Execution Mode: {mode_label}")
    print("=" * 65 + "\n")

    if args.all:
        conn = get_db_connection(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM enquiries ORDER BY id ASC")
        rows = cursor.fetchall()
        enq_ids = [r["id"] for r in rows]
        conn.close()

        if not enq_ids:
            print("No enquiries found in database. Auto-seeding from data/data.md...")
            init_db(DATABASE_PATH)
            seed_database_from_file(DATA_PATH, db_path=DATABASE_PATH)
            conn = get_db_connection(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM enquiries ORDER BY id ASC")
            enq_ids = [r["id"] for r in cursor.fetchall()]
            conn.close()

        for enq_id in enq_ids:
            res = process_enquiry(enq_id, db_path=DATABASE_PATH, use_fixtures=use_fixtures)
            confirm_flag = " [!] NEEDS CONFIRMATION" if res.get("needs_confirmation") else ""
            cat = res.get("category") or "none"
            owner = res.get("assigned_owner") or "None"
            status = res.get("status") or "UNKNOWN"
            print(f"  [{res['id']}]  Category: {cat:<17} | Owner: {owner:<30}{confirm_flag:<24} | Status: {status}")

        print("\n" + "-" * 65)
        print(" [SUCCESS] All enquiries processed and queued for human review.")
        print(" Open review dashboard at: http://127.0.0.1:8000")
        print("-" * 65 + "\n")

    elif args.id:
        res = process_enquiry(args.id, db_path=DATABASE_PATH, use_fixtures=use_fixtures)
        print(f"Processed {args.id}:")
        for k, v in res.items():
            print(f"  {k}: {v}")
    else:
        print("Error: Specify either --all (-a) or --id <ENQUIRY_ID>.")

def cmd_serve(args):
    """Launches the FastAPI review dashboard."""
    print(f"Starting BEDA Review Dashboard on http://{args.host}:{args.port}")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)

def main():
    parser = argparse.ArgumentParser(description="BEDA Business Enquiry Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: reset
    p_reset = subparsers.add_parser("reset", help="Reset database and re-seed from scratch")
    p_reset.set_defaults(func=cmd_reset)

    # Command: seed
    p_seed = subparsers.add_parser("seed", help="Defensively seed database from data.md")
    p_seed.set_defaults(func=cmd_seed)

    # Command: process
    p_proc = subparsers.add_parser("process", help="Process inbound enquiries")
    p_proc.add_argument("-a", "--all", action="store_true", help="Process all 12 enquiries")
    p_proc.add_argument("--id", type=str, help="Process single enquiry by ID (e.g. E001)")
    p_proc.add_argument("--live", action="store_true", help="Use live Claude API instead of fixtures")
    p_proc.set_defaults(func=cmd_process)

    # Command: serve
    p_serve = subparsers.add_parser("serve", help="Start FastAPI development server")
    p_serve.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    p_serve.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()
