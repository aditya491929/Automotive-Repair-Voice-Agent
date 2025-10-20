import json, os
from .session import get_session, init_db
from .models import Service, Pricing

def run_seed():
    init_db()
    with get_session() as s:
        # pricing
        s.add(Pricing(labor_rate_per_hour=float(os.getenv("LABOR_RATE", 120)),
                      shop_fee_flat=float(os.getenv("SHOP_FEE", 12)),
                      tax_rate=float(os.getenv("TAX_RATE", 0.08875))))
        # services
        cfg = json.load(open("app/config/pricing_catalog.json"))
        for svc in cfg["services"]:
            s.add(Service(code=svc["code"], name=svc["name"],
                          labor_hours=svc["labor_hours"], base_parts_cost=svc["base_parts_cost"]))
        s.commit()

if __name__ == "__main__":
    run_seed()
