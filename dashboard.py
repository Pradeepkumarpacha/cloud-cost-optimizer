from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, Resource, ScanReport, RemediationCommand

router = APIRouter()

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get full dashboard summary with savings and breakdown."""
    total_resources = db.query(Resource).count()
    total_waste = db.query(func.sum(Resource.monthly_cost)).scalar() or 0

    by_type = db.query(Resource.resource_type, func.count(Resource.id), func.sum(Resource.monthly_cost))\
        .group_by(Resource.resource_type).all()

    by_provider = db.query(Resource.cloud_provider, func.count(Resource.id), func.sum(Resource.monthly_cost))\
        .group_by(Resource.cloud_provider).all()

    by_region = db.query(Resource.region, func.count(Resource.id), func.sum(Resource.monthly_cost))\
        .group_by(Resource.region).all()

    by_risk = db.query(RemediationCommand.risk_level, func.count(RemediationCommand.id))\
        .group_by(RemediationCommand.risk_level).all()

    last_report = db.query(ScanReport).order_by(ScanReport.scanned_at.desc()).first()

    return {
        "summary": {
            "total_orphaned_resources": total_resources,
            "monthly_waste": round(float(total_waste), 2),
            "annual_waste": round(float(total_waste) * 12, 2),
            "last_scan": last_report.scanned_at.isoformat() if last_report else None,
            "file_scanned": last_report.filename if last_report else None
        },
        "by_resource_type": [
            {"type": t, "count": c, "monthly_cost": round(float(m or 0), 2)} for t, c, m in by_type
        ],
        "by_cloud_provider": [
            {"provider": p, "count": c, "monthly_cost": round(float(m or 0), 2)} for p, c, m in by_provider
        ],
        "by_region": [
            {"region": r, "count": c, "monthly_cost": round(float(m or 0), 2)} for r, c, m in by_region
        ],
        "by_risk_level": [
            {"risk": r, "count": c} for r, c in by_risk
        ]
    }
