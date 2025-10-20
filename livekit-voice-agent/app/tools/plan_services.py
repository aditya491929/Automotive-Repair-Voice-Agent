import json
from typing import List
from ..dispatcher import PlanIn, PlanOut

with open("app/config/pricing_catalog.json") as f:
    CFG = json.load(f)

def _match_symptoms(issues: List[str]) -> List[str]:
    issues_text = " ".join([i.lower() for i in issues])
    services = set()
    for m in CFG["symptom_map"]:
        if all(tok in issues_text for tok in m["phrase"].split()):
            services.update(m["services"])
    return list(services)

async def plan_services(inp: PlanIn) -> dict:
    services = _match_symptoms(inp.issues)
    # Basic upsell rule
    if inp.vehicle.mileage and inp.vehicle.mileage > 5000:
        for rule in CFG.get("upsell_rules", []):
            if inp.vehicle.mileage > rule.get("if_mileage_over", 999999):
                services.append(rule["add"])
    if not services:
        services = ["suspension_inspection"]  # safe default
    return PlanOut(services=list(dict.fromkeys(services))).model_dump()
