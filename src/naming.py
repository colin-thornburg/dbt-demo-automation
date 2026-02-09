"""
Naming utilities for the demo automation tool.

Handles:
- Company name aliasing (privacy-safe alternatives for well-known companies)
- Unique project / repository name generation
- Primary key and foreign key identification for seed data integrity
"""

import re
import random
from datetime import datetime
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Company name aliasing
# ---------------------------------------------------------------------------

# Map of well-known companies to plausible but fictional alias names.
# The alias should *feel* similar (same industry, similar vibe) without
# being the real name, so demos never expose confidential prospect info.
_ALIAS_MAP: Dict[str, str] = {
    # Tech / Cloud
    "amazon": "Pinnacle Commerce",
    "apple": "Orchard Devices",
    "google": "Beacon Search",
    "microsoft": "Stratus Software",
    "meta": "Horizon Social",
    "facebook": "Horizon Social",
    "netflix": "StreamWave",
    "uber": "SwiftRide",
    "lyft": "UrbanGlide",
    "airbnb": "Roamly Stays",
    "spotify": "TuneVault",
    "twitter": "Chirp Networks",
    "x": "Chirp Networks",
    "salesforce": "CloudPeak CRM",
    "oracle": "Atlas Data Systems",
    "ibm": "Cobalt Computing",
    "intel": "Quantum Chips",
    "nvidia": "LuminAI Silicon",
    "amd": "CoreForge Processors",
    "adobe": "Prism Creative",
    "slack": "Relay Messaging",
    "zoom": "ClearBridge Video",
    "shopify": "Storefront Labs",
    "stripe": "Conduit Payments",
    "square": "Mosaic Payments",
    "paypal": "VaultPay",
    "twilio": "SignalPath",
    "snowflake": "CrystalVault Data",
    "databricks": "SparkForge Analytics",
    "palantir": "Sentinel Analytics",
    "datadog": "Watchpost Monitoring",
    "splunk": "Logstream Insights",
    "confluent": "FlowBridge Streaming",
    "mongodb": "NovaStore",
    "elastic": "PulseSearch",
    "hashicorp": "Keystone Infra",
    "github": "CodeNexus",
    "gitlab": "DevForge",
    "atlassian": "TaskBridge",
    "servicenow": "WorkflowEdge",
    "crowdstrike": "SentryShield Cyber",

    # Finance
    "jpmorgan": "Summit National Bank",
    "goldman sachs": "Meridian Capital",
    "morgan stanley": "Westfield Securities",
    "bank of america": "Continental Trust",
    "wells fargo": "Prairie Federal",
    "citigroup": "Coastal Finance Group",
    "visa": "SwiftLink Payments",
    "mastercard": "GlobalArc Payments",
    "american express": "Premier Card Co",
    "fidelity": "Crestline Investments",
    "charles schwab": "Ridgeway Brokerage",
    "robinhood": "FairTrade Markets",
    "coinbase": "DigitalVault Exchange",
    "blackrock": "GranitePeak Asset Mgmt",
    "vanguard": "Steadfast Funds",

    # Retail / E-commerce
    "walmart": "Evergreen Retail",
    "target": "Bullseye Stores",
    "costco": "Valor Wholesale",
    "home depot": "Craftsman Supply",
    "lowes": "Homestead Hardware",
    "kroger": "Harvest Market",
    "nike": "Velocity Athletic",
    "adidas": "Stride Sportswear",
    "starbucks": "Roasted Bean Co",
    "mcdonalds": "Golden Arch Eats",
    "coca cola": "Refresh Beverages",
    "pepsi": "Sparkling Springs",
    "procter gamble": "Horizon Consumer Brands",
    "unilever": "Compass Consumer Goods",

    # Healthcare / Pharma
    "unitedhealth": "Pinnacle Health Group",
    "cvs health": "CarePoint Pharmacy",
    "pfizer": "Apex Therapeutics",
    "johnson johnson": "MeridianMed",
    "abbvie": "NovaPharm",
    "merck": "Crest Biosciences",
    "anthem": "Keystone Health Plans",
    "humana": "Compass Care Insurance",

    # Auto / Transport / Energy
    "tesla": "Voltstream Motors",
    "ford": "Crestline Auto",
    "toyota": "Zenith Motors",
    "general motors": "Liberty Automotive",
    "boeing": "Skyward Aerospace",
    "lockheed martin": "Sentinel Defense",
    "exxon": "Ridgeline Energy",
    "chevron": "Crestfield Petroleum",

    # Telecom / Media
    "att": "NexusComm",
    "verizon": "Broadpath Telecom",
    "t-mobile": "WaveLink Mobile",
    "comcast": "Keystone Media",
    "disney": "Wonderland Entertainment",
    "warner bros": "Silvercrest Studios",

    # Consulting / Services
    "deloitte": "Ridgepoint Advisory",
    "mckinsey": "Pinnacle Strategy",
    "accenture": "Apex Consulting",
    "kpmg": "Crestview Audit Group",
    "pwc": "Meridian Assurance",
    "ey": "Summit Advisory",
    "bain": "Keystone Strategy Group",
    "bcg": "Vantage Consulting",
}

# Adjective + noun parts for generating random aliases when no match exists.
_ALIAS_ADJECTIVES = [
    "Apex", "Summit", "Pinnacle", "Crestline", "Meridian",
    "Vantage", "Keystone", "Beacon", "Horizon", "Compass",
    "Ridgeline", "Stellar", "Northstar", "Evergreen", "Brightpath",
    "Ironwood", "Silveroak", "Granite", "Blueridge", "Clearwater",
]

_ALIAS_NOUNS = [
    "Industries", "Holdings", "Group", "Enterprises", "Corp",
    "Solutions", "Partners", "Global", "Collective", "Ventures",
    "Labs", "Systems", "Networks", "Co", "Works",
]


def generate_company_alias(company_name: str) -> str:
    """
    Return a privacy-safe alias for *company_name*.

    If the company is in our known-alias map, return the mapped alias.
    Otherwise, generate a deterministic but generic alias so the same
    input always produces the same output within a session.

    Args:
        company_name: The real company name from the user.

    Returns:
        A plausible fictional company name.
    """
    if not company_name or not company_name.strip():
        return "Demo Company"

    # Normalize for lookup: lowercase, strip common suffixes
    key = company_name.strip().lower()
    for suffix in (" inc", " inc.", " llc", " ltd", " corp", " corporation",
                   " co", " company", " group", " holdings"):
        if key.endswith(suffix):
            key = key[: -len(suffix)].strip()

    # Direct match
    if key in _ALIAS_MAP:
        return _ALIAS_MAP[key]

    # Partial match (e.g. "Amazon Web Services" → "amazon")
    for known, alias in _ALIAS_MAP.items():
        if known in key or key in known:
            return alias

    # No match — generate a deterministic alias from the input.
    # Use the hash of the company name as a seed so the same company
    # always gets the same alias within a process, but it's not the
    # real name.
    rng = random.Random(key)
    adj = rng.choice(_ALIAS_ADJECTIVES)
    noun = rng.choice(_ALIAS_NOUNS)
    return f"{adj} {noun}"


# ---------------------------------------------------------------------------
# Unique name generation
# ---------------------------------------------------------------------------

def make_unique_project_name(company_name: str) -> str:
    """
    Generate a unique, privacy-safe dbt project name.

    Uses the company alias (not the real name) and appends a timestamp
    so every generation is unique.

    dbt project names must start with a letter and contain only
    [a-z0-9_].
    """
    alias = generate_company_alias(company_name)
    base = re.sub(r'[^a-z0-9]+', '_', alias.lower()).strip('_')
    if not base or not base[0].isalpha():
        base = 'demo_' + base
    base = base[:60]
    suffix = datetime.now().strftime('%Y%m%d_%H%M')
    return f"{base}_{suffix}"


def make_unique_repo_name(company_name: str) -> str:
    """
    Generate a unique, privacy-safe GitHub repository name.

    Uses the company alias (not the real name) and appends a timestamp.
    """
    alias = generate_company_alias(company_name)
    slug = re.sub(r'[^a-z0-9]+', '-', alias.lower()).strip('-')
    slug = re.sub(r'-{2,}', '-', slug)[:80].strip('-')
    if not slug:
        slug = "demo-project"
    suffix = datetime.now().strftime('%Y%m%d-%H%M')
    return f"dbt-demo-{slug}-{suffix}"


# ---------------------------------------------------------------------------
# Primary / foreign key identification (shared by seed & schema generators)
# ---------------------------------------------------------------------------

def identify_primary_key(columns: List[str], table_name: str) -> str:
    """
    Identify the primary key column for a table.

    Heuristic order:
    1. Column named exactly 'id'
    2. Column named '{table_singular}_id'
    3. First column ending with '_id'
    4. First column in the list (fallback)
    """
    col_lower_map = {c.lower(): c for c in columns}

    if 'id' in col_lower_map:
        return col_lower_map['id']

    table_base = table_name.split('.')[-1].lower()
    for prefix in ('raw_', 'src_', 'source_', 'stg_'):
        if table_base.startswith(prefix):
            table_base = table_base[len(prefix):]
    table_singular = table_base.rstrip('s') if table_base.endswith('s') and len(table_base) > 2 else table_base
    pk_candidate = f"{table_singular}_id"
    if pk_candidate in col_lower_map:
        return col_lower_map[pk_candidate]

    for col in columns:
        if col.lower().endswith('_id'):
            return col

    return columns[0] if columns else 'id'


def identify_foreign_keys(
    columns: List[str],
    pk_column: str,
    all_table_names: List[str],
) -> Dict[str, str]:
    """
    Identify foreign key columns and their referenced table names.

    Returns ``{column_name: referenced_table_full_name}``.
    """
    fk_map: Dict[str, str] = {}
    table_bases: Dict[str, str] = {}
    for tn in all_table_names:
        base = tn.split('.')[-1].lower()
        for prefix in ('raw_', 'src_', 'source_', 'stg_'):
            if base.startswith(prefix):
                base = base[len(prefix):]
        table_bases[base] = tn
        singular = base.rstrip('s') if base.endswith('s') and len(base) > 2 else base
        if singular != base:
            table_bases[singular] = tn

    for col in columns:
        if col == pk_column:
            continue
        col_lower = col.lower()
        if not col_lower.endswith('_id'):
            continue
        entity = col_lower[:-3]
        if entity in table_bases:
            fk_map[col] = table_bases[entity]

    return fk_map
