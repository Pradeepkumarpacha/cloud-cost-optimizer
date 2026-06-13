from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, Resource, ScanReport, RemediationCommand
from app.finops_engine import parse_billing_file, detect_orphans, generate_cli_command, calculate_savings
import json

router = APIRouter()

@router.post("/scan")
async def scan_billing_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload AWS/Azure billing export (JSON or CSV) and detect orphaned resources."""
    if not (file.filename.endswith(".json") or file.filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only JSON or CSV files are supported")

    content = await file.read()
    try:
        records = parse_billing_file(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    orphans = detect_orphans(records)
    savings = calculate_savings(orphans)

    # Clear previous data and save new scan
    db.query(Resource).delete()
    db.query(RemediationCommand).delete()

    provider = records[0].get("cloud_provider", "AWS") if records else "AWS"

    for r in orphans:
        resource = Resource(
            resource_id=r.get("resource_id", f"res-{id(r)}"),
            resource_type=r.get("resource_type", "unknown"),
            resource_name=r.get("resource_name", "unnamed"),
            cloud_provider=r.get("cloud_provider", provider),
            region=r.get("region", "us-east-1"),
            monthly_cost=float(r.get("monthly_cost", 0)),
            status=r.get("status", "orphaned"),
            last_used=str(r.get("last_used", "unknown")),
            tags=json.dumps(r.get("tags", {}))
        )
        db.add(resource)

        cmd = generate_cli_command(r)
        remediation = RemediationCommand(
            resource_id=r.get("resource_id", ""),
            command_type="CLI",
            command=cmd,
            risk_level=r.get("risk_level", "MEDIUM")
        )
        db.add(remediation)

    report = ScanReport(
        filename=file.filename,
        cloud_provider=provider,
        total_resources=len(records),
        orphaned_count=len(orphans),
        total_waste_monthly=savings["monthly_savings"],
        total_waste_annual=savings["annual_savings"]
    )
    db.add(report)
    db.commit()

    return {
        "message": "Scan complete",
        "total_resources_scanned": len(records),
        "orphaned_resources_found": len(orphans),
        "estimated_monthly_waste": f"${savings['monthly_savings']:,.2f}",
        "estimated_annual_waste": f"${savings['annual_savings']:,.2f}"
    }

@router.get("/orphans")
def get_orphans(db: Session = Depends(get_db)):
    """Get all detected orphaned resources."""
    resources = db.query(Resource).all()
    return [
        {
            "resource_id": r.resource_id,
            "resource_type": r.resource_type,
            "resource_name": r.resource_name,
            "cloud_provider": r.cloud_provider,
            "region": r.region,
            "monthly_cost": r.monthly_cost,
            "annual_cost": round(r.monthly_cost * 12, 2),
            "status": r.status,
            "last_used": r.last_used
        }
        for r in resources
    ]

@router.get("/sample-data")
def get_sample_data():
    """Returns sample billing data format for reference."""
    return {
        "format": "JSON Array",
        "sample": [
            {"resource_id": "vol-0abc123", "resource_type": "ebs", "resource_name": "old-data-disk",
             "cloud_provider": "AWS", "region": "us-east-1", "monthly_cost": 45.00, "status": "unattached", "last_used": "2025-11-01"},
            {"resource_id": "i-0def456", "resource_type": "ec2", "resource_name": "test-server",
             "cloud_provider": "AWS", "region": "us-west-2", "monthly_cost": 120.00, "status": "stopped", "last_used": "2025-10-15"},
            {"resource_id": "eipalloc-0ghi789", "resource_type": "elastic_ip", "resource_name": "unused-ip",
             "cloud_provider": "AWS", "region": "us-east-1", "monthly_cost": 3.60, "status": "unassociated", "last_used": "never"}
        ]
    }
