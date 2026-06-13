import pandas as pd
import json
from typing import List, Dict, Any

ORPHAN_RULES = {
    "unattached_disk": {
        "types": ["disk", "volume", "ebs"],
        "condition": lambda r: r.get("status", "").lower() in ["unattached", "available", "orphaned"],
        "risk": "HIGH"
    },
    "idle_vm": {
        "types": ["vm", "instance", "ec2"],
        "condition": lambda r: r.get("status", "").lower() in ["stopped", "idle", "deallocated"],
        "risk": "HIGH"
    },
    "unused_ip": {
        "types": ["ip", "elastic_ip", "public_ip"],
        "condition": lambda r: r.get("status", "").lower() in ["unassociated", "unattached", "idle"],
        "risk": "MEDIUM"
    },
    "old_snapshot": {
        "types": ["snapshot"],
        "condition": lambda r: r.get("status", "").lower() in ["orphaned", "unused", "old"],
        "risk": "LOW"
    },
    "unused_lb": {
        "types": ["load_balancer", "lb", "alb", "elb"],
        "condition": lambda r: r.get("status", "").lower() in ["idle", "empty", "unused"],
        "risk": "HIGH"
    }
}

CLI_TEMPLATES = {
    "AWS": {
        "disk": "aws ec2 delete-volume --volume-id {resource_id} --region {region}",
        "volume": "aws ec2 delete-volume --volume-id {resource_id} --region {region}",
        "ebs": "aws ec2 delete-volume --volume-id {resource_id} --region {region}",
        "vm": "aws ec2 terminate-instances --instance-ids {resource_id} --region {region}",
        "instance": "aws ec2 terminate-instances --instance-ids {resource_id} --region {region}",
        "ec2": "aws ec2 terminate-instances --instance-ids {resource_id} --region {region}",
        "ip": "aws ec2 release-address --allocation-id {resource_id} --region {region}",
        "elastic_ip": "aws ec2 release-address --allocation-id {resource_id} --region {region}",
        "snapshot": "aws ec2 delete-snapshot --snapshot-id {resource_id} --region {region}",
        "load_balancer": "aws elbv2 delete-load-balancer --load-balancer-arn {resource_id} --region {region}",
        "alb": "aws elbv2 delete-load-balancer --load-balancer-arn {resource_id} --region {region}",
    },
    "Azure": {
        "disk": "az disk delete --ids {resource_id} --yes",
        "volume": "az disk delete --ids {resource_id} --yes",
        "vm": "az vm delete --ids {resource_id} --yes",
        "instance": "az vm delete --ids {resource_id} --yes",
        "ip": "az network public-ip delete --ids {resource_id}",
        "public_ip": "az network public-ip delete --ids {resource_id}",
        "snapshot": "az snapshot delete --ids {resource_id}",
        "load_balancer": "az network lb delete --ids {resource_id}",
        "lb": "az network lb delete --ids {resource_id}",
    }
}

def detect_orphans(records: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
    orphans = []
    for record in records:
        resource_type = record.get("resource_type", "").lower()
        for rule_name, rule in ORPHAN_RULES.items():
            if any(t in resource_type for t in rule["types"]):
                if rule["condition"](record):
                    record["orphan_reason"] = rule_name
                    record["risk_level"] = rule["risk"]
                    orphans.append(record)
                    break
    return orphans

def generate_cli_command(resource: Dict) -> str:
    provider = resource.get("cloud_provider", "AWS")
    rtype = resource.get("resource_type", "").lower()
    rid = resource.get("resource_id", "RESOURCE_ID")
    region = resource.get("region", "us-east-1")

    provider_cmds = CLI_TEMPLATES.get(provider, CLI_TEMPLATES["AWS"])
    for key in provider_cmds:
        if key in rtype:
            return provider_cmds[key].format(resource_id=rid, region=region)

    return f"# Manual review required for {provider} resource: {rid}"

def parse_billing_file(content: bytes, filename: str) -> List[Dict]:
    records = []
    try:
        if filename.endswith(".json"):
            data = json.loads(content)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = data.get("resources", data.get("items", [data]))
        elif filename.endswith(".csv"):
            import io
            df = pd.read_csv(io.BytesIO(content))
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            records = df.to_dict(orient="records")
    except Exception as e:
        raise ValueError(f"Failed to parse file: {str(e)}")
    return records

def calculate_savings(orphans: List[Dict]) -> Dict:
    total_monthly = sum(float(r.get("monthly_cost", 0)) for r in orphans)
    return {
        "monthly_savings": round(total_monthly, 2),
        "annual_savings": round(total_monthly * 12, 2),
        "orphan_count": len(orphans)
    }
