"""Bulk-grant due-date / late-due-date extensions on a Gradescope assignment.

Usage:
    GRADESCOPE_EMAIL=... GRADESCOPE_PASSWORD=... \\
    python3 extend_assignment.py \\
        --url https://www.gradescope.com/courses/1226014/assignments/8054263/grade \\
        --csv students.csv \\
        --late-due 2026-05-10T23:59:00

Examples:
    # Extend only the late due date:
    python3 extend_assignment.py --url ... --csv ... --late-due 2026-05-10T23:59:00

    # Extend only the due date:
    python3 extend_assignment.py --url ... --csv ... --due 2026-05-08T23:59:00

    # Extend both:
    python3 extend_assignment.py --url ... --csv ... \\
        --due 2026-05-08T23:59:00 --late-due 2026-05-10T23:59:00

CSV must have an `email` column header.
At least one of --due or --late-due is required (if both, --due <= --late-due).
Dates are ISO 8601, interpreted in America/Los_Angeles.
"""

import argparse
import csv
import os
import re
import sys
import zoneinfo
from datetime import datetime

from gradescopeapi.classes.connection import GSConnection
from gradescopeapi.classes.extensions import update_student_extension

TZ = zoneinfo.ZoneInfo("America/Los_Angeles")
URL_RE = re.compile(r"/courses/(\d+)/assignments/(\d+)")


def parse_url(url: str) -> tuple[str, str]:
    m = URL_RE.search(url)
    if not m:
        raise ValueError(f"Could not parse course/assignment IDs from URL: {url}")
    return m.group(1), m.group(2)


def load_emails(csv_path: str) -> list[str]:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        if "email" not in (reader.fieldnames or []):
            raise ValueError(f"CSV {csv_path} must have an 'email' column header")
        return [row["email"].strip().lower() for row in reader if row.get("email")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Gradescope assignment URL")
    parser.add_argument("--csv", required=True, help="CSV with an 'email' column")
    parser.add_argument(
        "--due",
        help="New due date (ISO 8601, America/Los_Angeles)",
    )
    parser.add_argument(
        "--late-due",
        help="New late due date (ISO 8601, America/Los_Angeles)",
    )
    args = parser.parse_args()

    if not args.due and not args.late_due:
        parser.error("Must provide at least one of --due or --late-due")

    email = os.environ.get("GRADESCOPE_EMAIL")
    password = os.environ.get("GRADESCOPE_PASSWORD")
    if not email or not password:
        print("Set GRADESCOPE_EMAIL and GRADESCOPE_PASSWORD env vars.", file=sys.stderr)
        return 1

    course_id, assignment_id = parse_url(args.url)
    due = datetime.fromisoformat(args.due).replace(tzinfo=TZ) if args.due else None
    late_due = (
        datetime.fromisoformat(args.late_due).replace(tzinfo=TZ)
        if args.late_due
        else None
    )
    if due and late_due and due > late_due:
        print("--due must be <= --late-due", file=sys.stderr)
        return 1
    emails = load_emails(args.csv)

    print(f"Course {course_id}, assignment {assignment_id}")
    if due:
        print(f"New due date:      {due.isoformat()}")
    if late_due:
        print(f"New late due date: {late_due.isoformat()}")
    print(f"Students in CSV: {len(emails)}")

    connection = GSConnection()
    connection.login(email, password)

    members = connection.account.get_course_users(course_id) or []
    email_to_uid = {
        m.email.strip().lower(): m.user_id for m in members if m.email and m.user_id
    }

    updated, skipped, failed = 0, 0, 0
    for student_email in emails:
        user_id = email_to_uid.get(student_email)
        if not user_id:
            print(f"  SKIP {student_email} (not in roster)")
            skipped += 1
            continue
        try:
            ok = update_student_extension(
                session=connection.session,
                course_id=course_id,
                assignment_id=assignment_id,
                user_id=user_id,
                due_date=due,
                late_due_date=late_due,
            )
        except Exception as e:
            print(f"  FAIL {student_email}: {e}")
            failed += 1
            continue
        if ok:
            print(f"  OK   {student_email}")
            updated += 1
        else:
            print(f"  FAIL {student_email} (non-200 response)")
            failed += 1

    print(f"\nUpdated: {updated}, skipped: {skipped}, failed: {failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
