"""Explicit research universe and conservative country-name resolution."""

import re
import unicodedata

import pandas as pd
import pycountry

# UN member-state roster, checked against https://www.un.org/en/about-us/member-states.
UN_MEMBERS = """
AF AL DZ AD AO AG AR AM AU AT AZ BS BH BD BB BY BE BZ BJ BT BO BA BW BR BN BG BF BI
CV KH CM CA CF TD CL CN CO KM CG CD CR CI HR CU CY CZ DK DJ DM DO EC EG SV GQ ER EE
SZ ET FJ FI FR GA GM GE DE GH GR GD GT GN GW GY HT HN HU IS IN ID IR IQ IE IL IT JM
JP JO KZ KE KI KP KR KW KG LA LV LB LS LR LY LI LT LU MG MW MY MV ML MT MH MR MU
MX FM MD MC MN ME MA MZ MM NA NR NP NL NZ NI NE NG MK NO OM PK PW PA PG PY PE PH PL
PT QA RO RU RW KN LC VC WS SM ST SA SN RS SC SL SG SK SI SB SO ZA SS ES LK SD SR SE
CH SY TJ TZ TH TL TG TO TT TN TR TM TV UG UA AE GB US UY UZ VU VE VN YE ZM ZW
""".split()
EXTRAS = {
    "VA": "UN observer",
    "PS": "UN observer",
    "TW": "Additional entity",
    "XK": "Additional entity",
}
NAMES = {
    "BOL": "Bolivia",
    "BRN": "Brunei",
    "COD": "DR Congo",
    "COG": "Republic of the Congo",
    "CZE": "Czechia",
    "IRN": "Iran",
    "KOR": "South Korea",
    "PRK": "North Korea",
    "LAO": "Laos",
    "MDA": "Moldova",
    "PSE": "Palestine",
    "RUS": "Russia",
    "SYR": "Syria",
    "TWN": "Taiwan",
    "TZA": "Tanzania",
    "TUR": "Türkiye",
    "USA": "United States",
    "GBR": "United Kingdom",
    "VAT": "Holy See",
    "VEN": "Venezuela",
    "VNM": "Vietnam",
    "XKX": "Kosovo",
}
ALIASES = {
    "turkey": "TUR",
    "czech republic": "CZE",
    "ivory coast": "CIV",
    "swaziland": "SWZ",
    "east timor": "TLS",
    "cape verde": "CPV",
    "burma": "MMR",
    "uk": "GBR",
    "united states of america": "USA",
    "vatican city": "VAT",
    "west bank and gaza": "PSE",
    "democratic republic of the congo": "COD",
    "congo kinshasa": "COD",
    "congo brazzaville": "COG",
    "republic of korea": "KOR",
    "democratic people's republic of korea": "PRK",
}


def country_universe() -> pd.DataFrame:
    rows = []
    for code in UN_MEMBERS + list(EXTRAS):
        c = pycountry.countries.get(alpha_2=code) if code != "XK" else None
        iso3 = c.alpha_3 if c else "XKX"
        rows.append(
            {
                "iso2": code,
                "iso3": iso3,
                "country": NAMES.get(iso3, c.name if c else "Kosovo"),
                "membership": EXTRAS.get(code, "UN member"),
                "core_un_member": code in UN_MEMBERS,
                "iso_status": "User-assigned XK/XKX" if code == "XK" else "ISO 3166-1",
            }
        )
    frame = pd.DataFrame(rows).sort_values("country").reset_index(drop=True)
    if len(UN_MEMBERS) != 193 or frame.iso3.nunique() != 197:
        raise ValueError(
            "Country universe must contain 193 UN members and four additional entities"
        )
    return frame


def _key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.casefold().strip())
    return re.sub(
        r"[^a-z0-9]+", " ", "".join(c for c in text if not unicodedata.combining(c))
    ).strip()


def resolve_country(value: str) -> str:
    """Return an in-universe alpha-3 code; never fuzzy-match ambiguous names."""
    if _key(value) in {"congo", "korea", "virgin islands"}:
        raise ValueError(f"Ambiguous country name: {value!r}; use an ISO code")
    lookup = {_key(k): v for k, v in ALIASES.items()}
    for row in country_universe().itertuples():
        for name in [row.country, row.iso2, row.iso3]:
            lookup[_key(name)] = row.iso3
        c = pycountry.countries.get(alpha_3=row.iso3)
        if c:
            for attr in ["name", "official_name", "common_name"]:
                if hasattr(c, attr) and _key(getattr(c, attr)) not in {"congo", "korea"}:
                    lookup[_key(getattr(c, attr))] = row.iso3
    try:
        return lookup[_key(value)]
    except KeyError:
        raise ValueError(f"Unknown or out-of-scope country: {value!r}") from None
