import json
from sqlmodel import select
from ..dispatcher import EstimateIn, EstimateOut
from ..db.session import get_session
from ..db.models import Pricing

# Load pricing catalog
with open("app/config/pricing_catalog.json") as f:
    CFG = json.load(f)

def _map_service_name_to_code(service_name: str) -> str:
    """Map service names to service codes"""
    service_lower = service_name.lower()
    
    # Direct mappings for common service name variations
    mappings = {
        "check engine light diagnosis": "diagnostic_basic",
        "check engine light": "diagnostic_basic",
        "diagnostic": "diagnostic_basic",
        "air filter replacement": "air_filter_replacement",
        "air filter": "air_filter_replacement",
        "spark plug replacement": "spark_plug_replacement",
        "spark plugs": "spark_plug_replacement",
        "spark plug": "spark_plug_replacement",
        "oil change": "oil_change",
        "engine oil": "oil_change",
        "battery replacement": "battery_replacement",
        "battery": "battery_replacement",
        "brake inspection": "brake_inspection",
        "brake service": "brake_service",
        "tire rotation": "tire_rotation",
        "suspension inspection": "suspension_inspection",
        "transmission service": "transmission_service",
    }
    
    # Check direct mappings first
    if service_lower in mappings:
        return mappings[service_lower]
    
    # Check if it's already a valid code
    for service in CFG["services"]:
        if service["code"] == service_name:
            return service_name
    
    # Try partial matching on service names
    for service in CFG["services"]:
        service_name_lower = service["name"].lower()
        if any(word in service_name_lower for word in service_lower.split()):
            return service["code"]
    
    # Default fallback
    return service_name

async def estimate(inp: EstimateIn) -> dict:
    with get_session() as s:
        pricing = s.exec(select(Pricing)).first()
        labor_rate = pricing.labor_rate_per_hour
        shop_fee = pricing.shop_fee_flat
        tax_rate = pricing.tax_rate

        labor_hours = 0.0
        parts = 0.0
        
        print(f"💰 Input services: {inp.services}")
        
        # Map service names to codes and look up in pricing catalog
        for service_input in inp.services:
            service_code = _map_service_name_to_code(service_input)
            print(f"💰 Mapped '{service_input}' -> '{service_code}'")
            
            found = False
            for service in CFG["services"]:
                if service["code"] == service_code:
                    labor_hours += service["labor_hours"]
                    parts += service["base_parts_cost"]
                    print(f"💰 Found service {service_code}: {service['labor_hours']}h, ${service['base_parts_cost']}")
                    found = True
                    break
            
            if not found:
                print(f"⚠️ Service '{service_input}' (mapped to '{service_code}') not found in pricing catalog")

        print(f"💰 Labor hours: {labor_hours}")
        print(f"💰 Parts: {parts}")
        print(f"💰 Shop fee: {shop_fee}")
        print(f"💰 Labor rate: {labor_rate}")

        base = labor_hours * labor_rate + parts + shop_fee
        print(f"💰 Base: {base}")
        low, high = base * 0.9, base * 1.2
        duration = int(labor_hours * 60) or 60
        out = EstimateOut(price_low=round(low,2), price_high=round(high,2), duration_minutes=duration)
        return out.model_dump()
