"""Local, consented pilot measurements. Planned slots never count as operators."""

import argparse
import csv
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("csv", type=Path)
parser.add_argument("--support-hourly-eur", type=float, default=40)
args = parser.parse_args()
rows = list(csv.DictReader(args.csv.open()))
real = [r for r in rows if r["status"] in ("in_progress", "completed")]
useful = [
    r
    for r in real
    if r["installation_success"] == "yes"
    and r["first_backup_success"] == "yes"
    and r["restore_success"] == "yes"
]
for row in real:
    if not row["operator_code"] or not row["consent_date"]:
        raise SystemExit(
            "Actual operator rows require an anonymous code and consent date."
        )
    for field in (
        "installation_minutes",
        "restore_minutes",
        "support_minutes",
        "incident_count",
    ):
        if row[field] and float(row[field]) < 0:
            raise SystemExit("Measured time/count cannot be negative.")
known_support = [r for r in real if r["support_minutes"] != ""]
minutes = (
    sum(float(r["support_minutes"]) for r in known_support) if known_support else None
)
summary = {
    "registered_actual_operators": len(real),
    "useful_installations_and_restores": len(useful),
    "target": 5,
    "support_minutes_measured": minutes,
    "operators_with_support_measurement": len(known_support),
    "support_cost_eur_at_assumed_rate": (
        round(minutes * args.support_hourly_eur / 60, 2)
        if minutes is not None
        else None
    ),
    "assumed_support_hourly_eur": args.support_hourly_eur,
    "explicit_cloud_requests": sum(r["cloud_requested"] == "yes" for r in real),
    "cloud_decision": "Evidence insufficient; keep self-hosted validation, no hosted spending.",
    "note": "Local manual measurements; no fabricated participants, sales or support time.",
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
