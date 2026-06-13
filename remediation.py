from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, RemediationCommand

router = APIRouter()

@router.get("/commands")
def get_remediation_commands(db: Session = Depends(get_db)):
    """Get all generated CLI remediation commands."""
    commands = db.query(RemediationCommand).all()
    return [
        {
            "resource_id": c.resource_id,
            "command_type": c.command_type,
            "command": c.command,
            "risk_level": c.risk_level,
            "executed": c.executed
        }
        for c in commands
    ]

@router.get("/commands/{risk_level}")
def get_commands_by_risk(risk_level: str, db: Session = Depends(get_db)):
    """Filter remediation commands by risk level (LOW, MEDIUM, HIGH)."""
    commands = db.query(RemediationCommand).filter(
        RemediationCommand.risk_level == risk_level.upper()
    ).all()
    return [{"resource_id": c.resource_id, "command": c.command, "risk_level": c.risk_level} for c in commands]

@router.get("/export")
def export_commands(db: Session = Depends(get_db)):
    """Export all CLI commands as a shell script."""
    commands = db.query(RemediationCommand).all()
    lines = ["#!/bin/bash", "# Cloud Cost Optimizer - Remediation Script", "# REVIEW BEFORE EXECUTING\n"]
    for c in commands:
        lines.append(f"# Risk: {c.risk_level} | Resource: {c.resource_id}")
        lines.append(c.command)
        lines.append("")
    return {"script": "\n".join(lines), "command_count": len(commands)}
