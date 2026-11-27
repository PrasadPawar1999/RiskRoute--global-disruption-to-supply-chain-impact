"""
Phase 2, step 2: generate the SIMULATED Warsaw electronics manufacturer.

Run from the project root:
    python src/generate_company_data.py            # write CSVs + load into MySQL
    python src/generate_company_data.py --csv-only # only write CSVs

The company: "Vistula Controls Sp. z o.o." (fictional), Warsaw, Poland.
It assembles industrial control units (~250 per day) from parts bought in
Asia and Europe. Every company record produced here is SIMULATED.

Places on the map (ports, chokepoints, rail hubs) are real, so that real
risk events in Phase 3 can be matched to them.

A fixed random seed means everyone who runs this gets identical data.
"""
import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
SNAPSHOT_DATE = date(2026, 11, 27)      # "today" in the simulated world
DAILY_PRODUCTION = 250                  # control units built per day
HISTORY_DAYS = 180                      # how far back purchase orders go

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "simulated"

random.seed(SEED)


# =====================================================================
# 1. NODES — real places goods pass through
# =====================================================================
NODES = [
    # node_id, name, type, country_code, lat, lon
    ("FAC_WAW", "Vistula Controls factory, Warsaw", "factory", "POL", 52.22970, 21.01220),
    # Asian ports
    ("PORT_SHA", "Port of Shanghai", "port", "CHN", 31.23040, 121.47370),
    ("PORT_SZX", "Port of Shenzhen (Yantian)", "port", "CHN", 22.57000, 114.27000),
    ("PORT_KHH", "Port of Kaohsiung", "port", "TWN", 22.61000, 120.28000),
    ("PORT_PEN", "Port of Penang", "port", "MYS", 5.41000, 100.34000),
    ("PORT_BUS", "Port of Busan", "port", "KOR", 35.10000, 129.04000),
    # Other origin ports
    ("PORT_IST", "Port of Istanbul (Ambarli)", "port", "TUR", 40.97000, 28.69000),
    ("PORT_ALT", "Port of Altamira", "port", "MEX", 22.48000, -97.87000),
    # European ports
    ("PORT_GDN", "Port of Gdansk", "port", "POL", 54.40000, 18.67000),
    ("PORT_HAM", "Port of Hamburg", "port", "DEU", 53.54000, 9.97000),
    ("PORT_RTM", "Port of Rotterdam", "port", "NLD", 51.95000, 4.14000),
    # Maritime chokepoints
    ("CP_TAIWAN", "Taiwan Strait", "chokepoint", None, 24.00000, 119.50000),
    ("CP_MALACCA", "Strait of Malacca", "chokepoint", None, 2.50000, 101.00000),
    ("CP_BAB", "Bab-el-Mandeb Strait", "chokepoint", None, 12.60000, 43.30000),
    ("CP_SUEZ", "Suez Canal", "chokepoint", "EGY", 30.60000, 32.30000),
    ("CP_GIB", "Strait of Gibraltar", "chokepoint", None, 35.95000, -5.60000),
    ("CP_CAPE", "Cape of Good Hope", "chokepoint", "ZAF", -34.36000, 18.47000),
    ("CP_DOVER", "Dover Strait", "chokepoint", None, 51.00000, 1.50000),
    ("CP_DANISH", "Danish Straits", "chokepoint", "DNK", 55.70000, 12.70000),
    ("CP_DARDANELLES", "Dardanelles", "chokepoint", "TUR", 40.20000, 26.40000),
    # China–Europe rail corridor
    ("RAIL_XIAN", "Xi'an rail hub", "rail_hub", "CHN", 34.34000, 108.94000),
    ("BORDER_DOSTYK", "Alashankou–Dostyk border crossing", "border", "KAZ", 45.20000, 82.50000),
    ("RAIL_MOSCOW", "Moscow rail transit", "rail_hub", "RUS", 55.75000, 37.62000),
    ("BORDER_BREST", "Brest–Malaszewicze border crossing", "border", "BLR", 52.08000, 23.65000),
    # European road origin hubs
    ("HUB_DEU", "Southern Germany supplier region", "rail_hub", "DEU", 48.78000, 9.18000),
    ("HUB_CZE", "Czech supplier region", "rail_hub", "CZE", 49.82000, 18.26000),
    ("HUB_ITA", "Northern Italy supplier region", "rail_hub", "ITA", 45.46000, 9.19000),
    ("HUB_POL", "Domestic Polish supplier region", "rail_hub", "POL", 52.41000, 16.93000),
]


# =====================================================================
# 2. ROUTES — each one as an ordered list of (from, to, days) legs
# =====================================================================
ROUTES = {
    # route_id: (name, mode, [(from_node, to_node, days), ...])
    "R_SHA_GDN_SUEZ": ("Shanghai → Gdansk via Suez", "sea", [
        ("PORT_SHA", "CP_TAIWAN", 2), ("CP_TAIWAN", "CP_MALACCA", 6),
        ("CP_MALACCA", "CP_BAB", 9), ("CP_BAB", "CP_SUEZ", 3),
        ("CP_SUEZ", "CP_GIB", 4), ("CP_GIB", "CP_DOVER", 4),
        ("CP_DOVER", "CP_DANISH", 2), ("CP_DANISH", "PORT_GDN", 1),
        ("PORT_GDN", "FAC_WAW", 2)]),
    "R_SHA_GDN_CAPE": ("Shanghai → Gdansk via Cape of Good Hope", "sea", [
        ("PORT_SHA", "CP_TAIWAN", 2), ("CP_TAIWAN", "CP_MALACCA", 6),
        ("CP_MALACCA", "CP_CAPE", 15), ("CP_CAPE", "CP_DOVER", 16),
        ("CP_DOVER", "CP_DANISH", 2), ("CP_DANISH", "PORT_GDN", 1),
        ("PORT_GDN", "FAC_WAW", 2)]),
    "R_SZX_RTM_SUEZ": ("Shenzhen → Rotterdam via Suez", "sea", [
        ("PORT_SZX", "CP_MALACCA", 5), ("CP_MALACCA", "CP_BAB", 9),
        ("CP_BAB", "CP_SUEZ", 3), ("CP_SUEZ", "CP_GIB", 4),
        ("CP_GIB", "PORT_RTM", 5), ("PORT_RTM", "FAC_WAW", 3)]),
    "R_KHH_HAM_SUEZ": ("Kaohsiung → Hamburg via Suez", "sea", [
        ("PORT_KHH", "CP_MALACCA", 5), ("CP_MALACCA", "CP_BAB", 9),
        ("CP_BAB", "CP_SUEZ", 3), ("CP_SUEZ", "CP_GIB", 4),
        ("CP_GIB", "CP_DOVER", 4), ("CP_DOVER", "PORT_HAM", 1),
        ("PORT_HAM", "FAC_WAW", 2)]),
    "R_PEN_GDN_SUEZ": ("Penang → Gdansk via Suez", "sea", [
        ("PORT_PEN", "CP_MALACCA", 1), ("CP_MALACCA", "CP_BAB", 8),
        ("CP_BAB", "CP_SUEZ", 3), ("CP_SUEZ", "CP_GIB", 4),
        ("CP_GIB", "CP_DOVER", 4), ("CP_DOVER", "CP_DANISH", 2),
        ("CP_DANISH", "PORT_GDN", 1), ("PORT_GDN", "FAC_WAW", 2)]),
    "R_BUS_HAM_SUEZ": ("Busan → Hamburg via Suez", "sea", [
        ("PORT_BUS", "CP_TAIWAN", 3), ("CP_TAIWAN", "CP_MALACCA", 5),
        ("CP_MALACCA", "CP_BAB", 9), ("CP_BAB", "CP_SUEZ", 3),
        ("CP_SUEZ", "CP_GIB", 4), ("CP_GIB", "CP_DOVER", 4),
        ("CP_DOVER", "PORT_HAM", 1), ("PORT_HAM", "FAC_WAW", 2)]),
    "R_IST_GDN": ("Istanbul → Gdansk via Gibraltar", "sea", [
        ("PORT_IST", "CP_DARDANELLES", 1), ("CP_DARDANELLES", "CP_GIB", 5),
        ("CP_GIB", "CP_DOVER", 4), ("CP_DOVER", "CP_DANISH", 2),
        ("CP_DANISH", "PORT_GDN", 1), ("PORT_GDN", "FAC_WAW", 2)]),
    "R_ALT_HAM": ("Altamira → Hamburg (Atlantic)", "sea", [
        ("PORT_ALT", "CP_DOVER", 15), ("CP_DOVER", "PORT_HAM", 1),
        ("PORT_HAM", "FAC_WAW", 2)]),
    "R_XIAN_WAW_RAIL": ("Xi'an → Warsaw rail via Kazakhstan, Russia, Belarus", "rail", [
        ("RAIL_XIAN", "BORDER_DOSTYK", 3), ("BORDER_DOSTYK", "RAIL_MOSCOW", 7),
        ("RAIL_MOSCOW", "BORDER_BREST", 3), ("BORDER_BREST", "FAC_WAW", 2)]),
    "R_DEU_WAW_ROAD": ("Southern Germany → Warsaw road", "road", [("HUB_DEU", "FAC_WAW", 2)]),
    "R_CZE_WAW_ROAD": ("Czechia → Warsaw road", "road", [("HUB_CZE", "FAC_WAW", 1)]),
    "R_ITA_WAW_ROAD": ("Northern Italy → Warsaw road", "road", [("HUB_ITA", "FAC_WAW", 3)]),
    "R_POL_WAW_ROAD": ("Domestic Poland → Warsaw road", "road", [("HUB_POL", "FAC_WAW", 1)]),
}


# =====================================================================
# 3. SUPPLIERS — fictional companies in real cities
# =====================================================================
SUPPLIERS = [
    # name, country, code, city, lat, lon, usual route, categories they sell
    ("Shenzhen Lianfeng Electronics", "China", "CHN", "Shenzhen", 22.54, 114.06, "R_SZX_RTM_SUEZ", ["Passive components", "Connectors"]),
    ("Shenzhen Brightpath PCB", "China", "CHN", "Shenzhen", 22.55, 114.10, "R_SZX_RTM_SUEZ", ["PCBs"]),
    ("Dongguan Precision Cable", "China", "CHN", "Dongguan", 23.02, 113.75, "R_SZX_RTM_SUEZ", ["Cables & harnesses", "Connectors"]),
    ("Shanghai Yuanda Semiconductor", "China", "CHN", "Shanghai", 31.23, 121.47, "R_SHA_GDN_SUEZ", ["Power semiconductors", "Sensors"]),
    ("Suzhou Kaiyue Display Tech", "China", "CHN", "Suzhou", 31.30, 120.58, "R_SHA_GDN_SUEZ", ["Displays"]),
    ("Ningbo Everpower Battery", "China", "CHN", "Ningbo", 29.87, 121.54, "R_SHA_GDN_SUEZ", ["Batteries"]),
    ("Xi'an Silkline Components", "China", "CHN", "Xi'an", 34.34, 108.94, "R_XIAN_WAW_RAIL", ["Passive components", "Sensors"]),
    ("Chengdu Western Microsystems", "China", "CHN", "Chengdu", 30.57, 104.07, "R_XIAN_WAW_RAIL", ["Memory", "Microcontrollers"]),
    ("Hsinchu Formosa Microchip", "Taiwan", "TWN", "Hsinchu", 24.80, 120.97, "R_KHH_HAM_SUEZ", ["Microcontrollers", "Memory"]),
    ("Taichung Jade Semiconductor", "Taiwan", "TWN", "Taichung", 24.15, 120.67, "R_KHH_HAM_SUEZ", ["Power semiconductors"]),
    ("Taoyuan Pacific Circuits", "Taiwan", "TWN", "Taoyuan", 24.99, 121.30, "R_KHH_HAM_SUEZ", ["PCBs"]),
    ("Kaohsiung Harbor Electronics", "Taiwan", "TWN", "Kaohsiung", 22.63, 120.30, "R_KHH_HAM_SUEZ", ["Sensors", "Passive components"]),
    ("Penang Straits Semiconductor", "Malaysia", "MYS", "Penang", 5.41, 100.33, "R_PEN_GDN_SUEZ", ["Microcontrollers", "Power semiconductors"]),
    ("Kulim Tropic Electronics", "Malaysia", "MYS", "Kulim", 5.37, 100.56, "R_PEN_GDN_SUEZ", ["Memory", "Passive components"]),
    ("Busan Hanbit Display", "South Korea", "KOR", "Busan", 35.18, 129.08, "R_BUS_HAM_SUEZ", ["Displays", "Batteries"]),
    ("Gumi Saebyeok Memory", "South Korea", "KOR", "Gumi", 36.12, 128.34, "R_BUS_HAM_SUEZ", ["Memory"]),
    ("Bursa Marmara Kablo", "Turkey", "TUR", "Bursa", 40.19, 29.06, "R_IST_GDN", ["Cables & harnesses"]),
    ("Istanbul Bosphorus Metal", "Turkey", "TUR", "Istanbul", 41.01, 28.98, "R_IST_GDN", ["Metal enclosures"]),
    ("Monterrey Norte Harness", "Mexico", "MEX", "Monterrey", 25.69, -100.32, "R_ALT_HAM", ["Cables & harnesses", "Connectors"]),
    ("Stuttgart Neckar Steckverbinder", "Germany", "DEU", "Stuttgart", 48.78, 9.18, "R_DEU_WAW_ROAD", ["Connectors", "Fasteners"]),
    ("Nuremberg Franken Sensorik", "Germany", "DEU", "Nuremberg", 49.45, 11.08, "R_DEU_WAW_ROAD", ["Sensors"]),
    ("Dresden Elbe Halbleiter", "Germany", "DEU", "Dresden", 51.05, 13.74, "R_DEU_WAW_ROAD", ["Power semiconductors", "Microcontrollers"]),
    ("Ostrava Silesian Steel Works", "Czechia", "CZE", "Ostrava", 49.82, 18.26, "R_CZE_WAW_ROAD", ["Metal enclosures", "Fasteners"]),
    ("Brno Moravia Plastics", "Czechia", "CZE", "Brno", 49.20, 16.61, "R_CZE_WAW_ROAD", ["Plastic housings"]),
    ("Plzen Bohemia Harness", "Czechia", "CZE", "Plzen", 49.74, 13.38, "R_CZE_WAW_ROAD", ["Cables & harnesses"]),
    ("Milan Lombardia Polimeri", "Italy", "ITA", "Milan", 45.46, 9.19, "R_ITA_WAW_ROAD", ["Plastic housings", "Fasteners"]),
    ("Bologna Emilia Precision", "Italy", "ITA", "Bologna", 44.49, 11.34, "R_ITA_WAW_ROAD", ["Metal enclosures"]),
    ("Poznan Wielkopolska Packaging", "Poland", "POL", "Poznan", 52.41, 16.93, "R_POL_WAW_ROAD", ["Packaging"]),
    ("Lodz Central Cable", "Poland", "POL", "Lodz", 51.76, 19.46, "R_POL_WAW_ROAD", ["Cables & harnesses", "Packaging"]),
    ("Wroclaw Odra Electronics", "Poland", "POL", "Wroclaw", 51.11, 17.03, "R_POL_WAW_ROAD", ["Passive components", "PCBs"]),
]


# =====================================================================
# 4. MATERIALS — by category
# category: (criticality, unit cost range €, qty used per unit built,
#            production days at supplier, [material names])
# =====================================================================
CATEGORIES = {
    "Microcontrollers": ("A", (1.5, 12.0), (1, 1), (28, 56), [
        "MCU 32-bit Cortex-M4 (LQFP64)", "MCU 32-bit Cortex-M0+ (QFN32)",
        "MCU 32-bit Cortex-M7 (LQFP144)", "MCU 8-bit (TQFP32)", "Wireless SoC BLE 5.3"]),
    "Power semiconductors": ("A", (0.8, 45.0), (1, 4), (21, 49), [
        "IGBT module 1200V 100A", "MOSFET 650V 30A", "Gate driver IC",
        "DC-DC converter module 24V", "LDO voltage regulator 3.3V"]),
    "Memory": ("A", (0.4, 6.0), (1, 2), (28, 56), [
        "NOR Flash 128Mbit", "DDR4 SDRAM 8Gbit", "EEPROM 256Kbit"]),
    "Sensors": ("B", (0.3, 18.0), (1, 3), (14, 35), [
        "NTC temperature sensor", "Hall current sensor 50A", "Pressure sensor 10 bar",
        "Digital humidity sensor", "3-axis accelerometer"]),
    "PCBs": ("A", (2.0, 25.0), (1, 1), (14, 28), [
        "Main control board PCB 6-layer", "Power board PCB 4-layer",
        "I/O expansion PCB 2-layer", "Display interface PCB 4-layer"]),
    "Passive components": ("C", (0.002, 0.40), (10, 120), (7, 21), [
        "MLCC capacitor 10uF 0805", "Resistor 10k 0603", "Electrolytic capacitor 470uF",
        "Power inductor 22uH", "Crystal oscillator 16MHz", "TVS diode array"]),
    "Connectors": ("B", (0.15, 6.0), (2, 6), (10, 28), [
        "Terminal block 5.08mm 4-pin", "M12 circular connector 8-pin",
        "RJ45 industrial jack", "Board-to-board connector 40-pin", "USB-C receptacle"]),
    "Cables & harnesses": ("B", (1.5, 22.0), (1, 3), (10, 21), [
        "Main wiring harness assembly", "Power cable 3x2.5mm2",
        "Shielded Ethernet cable Cat6", "M12 sensor cable 5m"]),
    "Displays": ("B", (6.0, 55.0), (1, 1), (21, 42), [
        "TFT LCD 7-inch touch", "TFT LCD 4.3-inch", "OLED 1.3-inch module"]),
    "Batteries": ("B", (0.3, 4.5), (1, 2), (14, 35), [
        "Li-ion cell 18650", "Backup coin cell CR2032"]),
    "Metal enclosures": ("B", (4.0, 60.0), (1, 1), (10, 28), [
        "Aluminium enclosure 300x200", "Steel DIN-rail cabinet", "Extruded aluminium heat sink"]),
    "Plastic housings": ("C", (0.2, 8.0), (1, 2), (7, 21), [
        "ABS front panel housing", "Polycarbonate transparent cover", "Cable gland M20"]),
    "Fasteners": ("C", (0.01, 0.6), (8, 24), (5, 14), [
        "M4 stainless screw set", "DIN rail clip", "Thermal pad 1mm"]),
    "Packaging": ("C", (0.05, 2.5), (1, 3), (3, 10), [
        "Corrugated shipping box", "Anti-static bag 200x300", "Foam insert set"]),
}

# Some products use a part, some don't: share of daily production using it
MIX_RANGE = (0.3, 1.0)

# Deliberate weak spots for the risk engine to find (see docs later).
# material name: (forced supplier names, forced stock coverage in days)
PLANTED_WEAK_SPOTS = {
    # Single source, Taiwan, ships via Bab-el-Mandeb & Suez, low stock
    "MCU 32-bit Cortex-M4 (LQFP64)": (["Hsinchu Formosa Microchip"], 22),
    # Single source, China, via Suez, low stock
    "IGBT module 1200V 100A": (["Shanghai Yuanda Semiconductor"], 19),
    # Single source on the China–Europe rail route through Russia & Belarus
    "DDR4 SDRAM 8Gbit": (["Chengdu Western Microsystems"], 25),
    # Single source, Shenzhen, via Suez
    "Main control board PCB 6-layer": (["Shenzhen Brightpath PCB"], 24),
    # "Dual-sourced" — but BOTH suppliers ship through Suez (hidden concentration)
    "TFT LCD 7-inch touch": (["Busan Hanbit Display", "Suzhou Kaiyue Display Tech"], 30),
}


def route_transit_days(route_id: str) -> int:
    return sum(days for _, _, days in ROUTES[route_id][2])


def round_up(qty: float, step: int = 100) -> int:
    return max(step, int(-(-qty // step) * step))


# =====================================================================
# Build the tables
# =====================================================================
def build_nodes() -> pd.DataFrame:
    return pd.DataFrame(NODES, columns=[
        "node_id", "node_name", "node_type", "country_code", "latitude", "longitude"])


def build_routes() -> tuple[pd.DataFrame, pd.DataFrame]:
    routes, legs = [], []
    for route_id, (name, mode, route_legs) in ROUTES.items():
        routes.append({
            "route_id": route_id, "route_name": name, "transport_mode": mode,
            "origin_node_id": route_legs[0][0],
            "destination_node_id": route_legs[-1][1],
            "typical_transit_days": route_transit_days(route_id),
        })
        for seq, (frm, to, days) in enumerate(route_legs, start=1):
            legs.append({"route_id": route_id, "leg_seq": seq,
                         "from_node_id": frm, "to_node_id": to, "transit_days": days})
    return pd.DataFrame(routes), pd.DataFrame(legs)


def build_suppliers() -> tuple[pd.DataFrame, dict]:
    rows, info = [], {}
    for i, (name, country, code, city, lat, lon, route, cats) in enumerate(SUPPLIERS, start=1):
        sid = f"SUP{i:03d}"
        rows.append({
            "supplier_id": sid, "supplier_name": name, "country": country,
            "country_code": code, "city": city, "latitude": lat, "longitude": lon,
            "reliability_score": round(random.uniform(0.78, 0.98), 2),
        })
        info[sid] = {"name": name, "route": route, "categories": cats}
    return pd.DataFrame(rows), info


def build_materials(supplier_info: dict):
    materials, sup_mat, inventory = [], [], []
    name_to_sid = {v["name"]: k for k, v in supplier_info.items()}
    mat_no = 0

    for category, (crit, cost_rng, qty_rng, prod_rng, names) in CATEGORIES.items():
        candidates = [sid for sid, s in supplier_info.items() if category in s["categories"]]

        for name in names:
            mat_no += 1
            mid = f"MAT{mat_no:03d}"
            unit_cost = round(random.uniform(*cost_rng), 3 if cost_rng[1] < 1 else 2)
            # Passive parts use many pieces per unit; others few
            qty_per_unit = random.randint(*qty_rng)
            mix = random.uniform(*MIX_RANGE)
            daily = max(1, round(DAILY_PRODUCTION * qty_per_unit * mix))

            materials.append({
                "material_id": mid, "material_name": name, "category": category,
                "criticality": crit, "unit": "pcs", "unit_cost_eur": unit_cost,
            })

            # --- which suppliers sell it -------------------------------
            if name in PLANTED_WEAK_SPOTS:
                chosen = [name_to_sid[n] for n in PLANTED_WEAK_SPOTS[name][0]]
            else:
                chosen = [random.choice(candidates)]
                others = [c for c in candidates if c not in chosen]
                backup_chance = 0.7 if crit == "A" else 0.5  # critical parts more often dual-sourced
                if others and random.random() < backup_chance:
                    chosen.append(random.choice(others))

            for rank, sid in enumerate(chosen):
                route = supplier_info[sid]["route"]
                lead = route_transit_days(route) + random.randint(*prod_rng)
                price = unit_cost if rank == 0 else unit_cost * random.uniform(1.05, 1.25)
                sup_mat.append({
                    "supplier_id": sid, "material_id": mid, "is_primary": rank == 0,
                    "lead_time_days": lead,
                    "price_eur": round(price, 3 if price < 1 else 2),
                })

            # --- inventory --------------------------------------------
            if name in PLANTED_WEAK_SPOTS:
                coverage = PLANTED_WEAK_SPOTS[name][1]
            elif crit == "C":
                coverage = random.randint(35, 90)
            else:
                coverage = random.randint(30, 70)
            safety_days = 14 if crit == "A" else 10 if crit == "B" else 7
            inventory.append({
                "material_id": mid, "snapshot_date": SNAPSHOT_DATE,
                "on_hand_qty": int(daily * coverage),
                "safety_stock_qty": int(daily * safety_days),
                "avg_daily_consumption": float(daily),
            })

    return pd.DataFrame(materials), pd.DataFrame(sup_mat), pd.DataFrame(inventory)


def current_leg(route_id: str, departure: date) -> int:
    """Which leg a shipment is on today, based on days since departure."""
    elapsed = (SNAPSHOT_DATE - departure).days
    cumulative = 0
    for seq, (_, _, days) in enumerate(ROUTES[route_id][2], start=1):
        cumulative += days
        if elapsed < cumulative:
            return seq
    return len(ROUTES[route_id][2])


def build_orders(sup_mat: pd.DataFrame, inventory: pd.DataFrame, supplier_info: dict):
    pos, shipments = [], []
    daily_use = inventory.set_index("material_id")["avg_daily_consumption"].to_dict()
    po_no = 0

    for row in sup_mat.itertuples():
        route = supplier_info[row.supplier_id]["route"]
        transit = route_transit_days(route)
        daily = daily_use[row.material_id]

        # Primary suppliers get an order roughly every 30 days.
        # Backup suppliers get 1–2 occasional orders in the history.
        if row.is_primary:
            order_dates, d = [], SNAPSHOT_DATE - timedelta(days=HISTORY_DAYS)
            while d <= SNAPSHOT_DATE:
                order_dates.append(d)
                d += timedelta(days=random.randint(25, 35))
        else:
            order_dates = sorted(
                SNAPSHOT_DATE - timedelta(days=random.randint(90, HISTORY_DAYS))
                for _ in range(random.randint(1, 2)))

        for od in order_dates:
            po_no += 1
            po_id, shp_id = f"PO{po_no:06d}", f"SHP{po_no:06d}"
            cover_days = 30 if row.is_primary else random.randint(10, 20)
            qty = round_up(daily * cover_days)
            expected = od + timedelta(days=int(row.lead_time_days))
            departure = expected - timedelta(days=transit)

            # Status depends on where "today" falls
            if expected <= SNAPSHOT_DATE:
                po_status, shp_status, eta, leg = "delivered", "arrived", expected, None
            elif departure <= SNAPSHOT_DATE:
                po_status, shp_status, eta = "in_transit", "in_transit", expected
                leg = current_leg(route, departure)
                if random.random() < 0.08:        # a few are already running late
                    shp_status = "delayed"
                    eta = expected + timedelta(days=random.randint(3, 10))
            else:
                po_status, shp_status, eta, leg = "open", "planned", expected, None

            pos.append({
                "po_id": po_id, "supplier_id": row.supplier_id,
                "material_id": row.material_id, "order_date": od, "quantity": qty,
                "unit_price_eur": row.price_eur, "expected_delivery_date": expected,
                "status": po_status,
            })
            shipments.append({
                "shipment_id": shp_id, "po_id": po_id, "route_id": route,
                "departure_date": departure, "eta_date": eta,
                "current_leg_seq": leg, "status": shp_status,
            })

    shipments = pd.DataFrame(shipments)
    shipments["current_leg_seq"] = shipments["current_leg_seq"].astype("Int64")
    return pd.DataFrame(pos), shipments


# =====================================================================
# Save + load
# =====================================================================
LOAD_ORDER = ["suppliers", "materials", "supplier_materials", "nodes", "routes",
              "route_legs", "inventory", "purchase_orders", "shipments"]


def save_csvs(tables: dict):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in LOAD_ORDER:
        tables[name].to_csv(OUT_DIR / f"{name}.csv", index=False)
    print(f"✅ CSVs written to {OUT_DIR}")


def load_into_mysql(tables: dict):
    from sqlalchemy import text

    from db import get_engine

    engine = get_engine()

    with engine.begin() as conn:
        # Clear company tables (risk tables are left alone)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for name in reversed(LOAD_ORDER):
            conn.execute(text(f"DELETE FROM {name}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        for name in LOAD_ORDER:
            tables[name].to_sql(name, conn, if_exists="append", index=False)
    print("✅ Data loaded into MySQL")


def print_summary(tables: dict):
    m, sm, inv = tables["materials"], tables["supplier_materials"], tables["inventory"]
    shp = tables["shipments"]
    print("\n📊 Simulated company: Vistula Controls Sp. z o.o. (Warsaw)")
    for name in LOAD_ORDER:
        print(f"   {name:<20} {len(tables[name]):>5} rows")

    n_sources = sm.groupby("material_id").size()
    single_a = m[(m["criticality"] == "A") & m["material_id"].map(n_sources).eq(1)]
    inv = inv.assign(coverage=inv["on_hand_qty"] / inv["avg_daily_consumption"])
    low = inv[inv["coverage"] < 30].merge(m, on="material_id")

    print(f"\n⚠️  Critical (A) materials with a single supplier: {len(single_a)}")
    print(f"⚠️  Materials with under 30 days of stock: {len(low)}")
    for r in low.itertuples():
        print(f"     {r.material_id}  {r.material_name:<35} {r.coverage:5.1f} days")
    print(f"🚢 Shipments currently in transit or delayed: "
          f"{shp['status'].isin(['in_transit', 'delayed']).sum()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-only", action="store_true", help="don't load into MySQL")
    args = parser.parse_args()

    nodes = build_nodes()
    routes, legs = build_routes()
    suppliers, supplier_info = build_suppliers()
    materials, sup_mat, inventory = build_materials(supplier_info)
    pos, shipments = build_orders(sup_mat, inventory, supplier_info)

    tables = {
        "suppliers": suppliers, "materials": materials, "supplier_materials": sup_mat,
        "nodes": nodes, "routes": routes, "route_legs": legs, "inventory": inventory,
        "purchase_orders": pos, "shipments": shipments,
    }
    save_csvs(tables)
    if not args.csv_only:
        load_into_mysql(tables)
    print_summary(tables)


if __name__ == "__main__":
    main()
