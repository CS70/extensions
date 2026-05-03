A simple script for bulk-adding extensions on Gradescope.

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
