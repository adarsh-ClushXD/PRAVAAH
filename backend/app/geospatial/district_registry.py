"""
West Bengal District Registry.

Single source of truth for all 23 districts of West Bengal.
Contains precise coordinates (district headquarters), flood risk
topographical factors, major rivers, and administrative metadata.

Each district entry includes:
  - lat/lon: District headquarters coordinates (WGS84)
  - elevation_m: Average elevation in meters
  - base_flood_risk: Topographical risk multiplier (1.0–2.0)
  - major_rivers: Rivers flowing through or adjacent to the district
  - population_density: Approx. people per km² (Census 2011)
  - area_km2: District area in square kilometers
"""
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class DistrictInfo:
    """Immutable metadata record for a single West Bengal district."""
    id: str
    name: str
    lat: float
    lon: float
    elevation_m: float
    base_flood_risk: float          # Topographical multiplier: 1.0 (low) – 2.0 (high)
    major_rivers: list[str]
    population_density: int          # persons per km²
    area_km2: float
    division: str                    # Administrative division


class DistrictRegistry:
    """
    Immutable registry of all 23 West Bengal districts.

    Access districts by ID using get_district() or iterate all using
    get_all_districts(). This registry is the authoritative source
    used by all data fetchers and the AI pipeline.
    """

    _DISTRICTS: ClassVar[list[DistrictInfo]] = [
        # ── North Bengal ─────────────────────────────────────────────────────
        DistrictInfo(
            id="darjeeling",
            name="Darjeeling",
            lat=27.0360, lon=88.2627,
            elevation_m=2042.0,
            base_flood_risk=1.3,
            major_rivers=["Teesta", "Balason", "Mahananda"],
            population_density=482,
            area_km2=3149.0,
            division="Jalpaiguri",
        ),
        DistrictInfo(
            id="kalimpong",
            name="Kalimpong",
            lat=27.0590, lon=88.4748,
            elevation_m=1247.0,
            base_flood_risk=1.4,
            major_rivers=["Teesta", "Relli"],
            population_density=160,
            area_km2=1344.0,
            division="Jalpaiguri",
        ),
        DistrictInfo(
            id="jalpaiguri",
            name="Jalpaiguri",
            lat=26.5454, lon=88.7182,
            elevation_m=76.0,
            base_flood_risk=1.8,
            major_rivers=["Teesta", "Jaldhaka", "Torsha", "Mansai"],
            population_density=621,
            area_km2=6227.0,
            division="Jalpaiguri",
        ),
        DistrictInfo(
            id="alipurduar",
            name="Alipurduar",
            lat=26.4839, lon=89.5271,
            elevation_m=56.0,
            base_flood_risk=1.9,
            major_rivers=["Torsha", "Sankosh", "Kaljani", "Raidak"],
            population_density=383,
            area_km2=3383.0,
            division="Jalpaiguri",
        ),
        DistrictInfo(
            id="cooch_behar",
            name="Cooch Behar",
            lat=26.3452, lon=89.4439,
            elevation_m=43.0,
            base_flood_risk=2.0,
            major_rivers=["Torsha", "Kaljani", "Sankosh", "Raidak"],
            population_density=1041,
            area_km2=3387.0,
            division="Jalpaiguri",
        ),
        DistrictInfo(
            id="uttar_dinajpur",
            name="Uttar Dinajpur",
            lat=25.6139, lon=88.1406,
            elevation_m=35.0,
            base_flood_risk=1.7,
            major_rivers=["Mahananda", "Nagar", "Kulik"],
            population_density=1074,
            area_km2=3140.0,
            division="Jalpaiguri",
        ),
        DistrictInfo(
            id="dakshin_dinajpur",
            name="Dakshin Dinajpur",
            lat=25.1783, lon=88.4836,
            elevation_m=28.0,
            base_flood_risk=1.5,
            major_rivers=["Atrai", "Punarbhaba", "Tangon"],
            population_density=893,
            area_km2=2219.0,
            division="Jalpaiguri",
        ),
        DistrictInfo(
            id="malda",
            name="Malda",
            lat=25.0108, lon=88.1415,
            elevation_m=23.0,
            base_flood_risk=1.8,
            major_rivers=["Ganga", "Mahananda", "Kalindri", "Fulhar"],
            population_density=1073,
            area_km2=3733.0,
            division="Malda",
        ),

        # ── South Bengal ──────────────────────────────────────────────────────
        DistrictInfo(
            id="murshidabad",
            name="Murshidabad",
            lat=24.1819, lon=88.2692,
            elevation_m=16.0,
            base_flood_risk=1.9,
            major_rivers=["Bhagirathi", "Ganga", "Jalangi", "Mayurakshi"],
            population_density=1334,
            area_km2=5341.0,
            division="Murshidabad",
        ),
        DistrictInfo(
            id="birbhum",
            name="Birbhum",
            lat=23.9490, lon=87.5356,
            elevation_m=56.0,
            base_flood_risk=1.5,
            major_rivers=["Mayurakshi", "Brahmani", "Kopai", "Ajay"],
            population_density=771,
            area_km2=4545.0,
            division="Burdwan",
        ),
        DistrictInfo(
            id="nadia",
            name="Nadia",
            lat=23.4675, lon=88.5572,
            elevation_m=9.0,
            base_flood_risk=1.7,
            major_rivers=["Bhagirathi", "Churni", "Ichamati", "Jalangi"],
            population_density=1316,
            area_km2=3927.0,
            division="Presidency",
        ),
        DistrictInfo(
            id="north_24_parganas",
            name="North 24 Parganas",
            lat=22.8455, lon=88.3952,
            elevation_m=6.0,
            base_flood_risk=1.8,
            major_rivers=["Ichamati", "Bidyadhari", "Haldi"],
            population_density=2444,
            area_km2=4094.0,
            division="Presidency",
        ),
        DistrictInfo(
            id="south_24_parganas",
            name="South 24 Parganas",
            lat=22.0460, lon=88.5671,
            elevation_m=3.0,
            base_flood_risk=2.0,
            major_rivers=["Muriganga", "Saptamukhi", "Thakuran", "Matla"],
            population_density=818,
            area_km2=9960.0,
            division="Presidency",
        ),
        DistrictInfo(
            id="kolkata",
            name="Kolkata",
            lat=22.5726, lon=88.3639,
            elevation_m=6.0,
            base_flood_risk=1.6,
            major_rivers=["Hooghly"],
            population_density=24252,
            area_km2=185.0,
            division="Presidency",
        ),
        DistrictInfo(
            id="howrah",
            name="Howrah",
            lat=22.5958, lon=88.2636,
            elevation_m=12.0,
            base_flood_risk=1.8,
            major_rivers=["Hooghly", "Damodar"],
            population_density=3300,
            area_km2=1467.0,
            division="Presidency",
        ),
        DistrictInfo(
            id="hooghly",
            name="Hooghly",
            lat=22.9025, lon=88.3967,
            elevation_m=15.0,
            base_flood_risk=1.6,
            major_rivers=["Hooghly", "Damodar", "Mundeswari"],
            population_density=1799,
            area_km2=3149.0,
            division="Burdwan",
        ),
        DistrictInfo(
            id="paschim_bardhaman",
            name="Paschim Bardhaman",
            lat=23.2324, lon=87.0797,
            elevation_m=62.0,
            base_flood_risk=1.4,
            major_rivers=["Damodar", "Ajay"],
            population_density=989,
            area_km2=1603.0,
            division="Burdwan",
        ),
        DistrictInfo(
            id="purba_bardhaman",
            name="Purba Bardhaman",
            lat=23.2324, lon=87.8616,
            elevation_m=29.0,
            base_flood_risk=1.7,
            major_rivers=["Damodar", "Bhagirathi", "Kunur"],
            population_density=1201,
            area_km2=7024.0,
            division="Burdwan",
        ),
        DistrictInfo(
            id="bankura",
            name="Bankura",
            lat=23.2300, lon=87.0731,
            elevation_m=95.0,
            base_flood_risk=1.3,
            major_rivers=["Damodar", "Dwarakeswar", "Gangani", "Shilabati"],
            population_density=523,
            area_km2=6882.0,
            division="Burdwan",
        ),
        DistrictInfo(
            id="purulia",
            name="Purulia",
            lat=23.3319, lon=86.3647,
            elevation_m=217.0,
            base_flood_risk=1.2,
            major_rivers=["Damodar", "Kangsabati", "Subarnarekha"],
            population_density=468,
            area_km2=6259.0,
            division="Burdwan",
        ),
        DistrictInfo(
            id="paschim_medinipur",
            name="Paschim Medinipur",
            lat=22.4215, lon=87.3195,
            elevation_m=42.0,
            base_flood_risk=1.5,
            major_rivers=["Subarnarekha", "Kangsabati", "Silabati", "Rupnarayan"],
            population_density=658,
            area_km2=9345.0,
            division="Medinipur",
        ),
        DistrictInfo(
            id="purba_medinipur",
            name="Purba Medinipur",
            lat=22.2157, lon=87.9180,
            elevation_m=5.0,
            base_flood_risk=1.9,
            major_rivers=["Rupnarayan", "Rasulpur", "Haldi"],
            population_density=1076,
            area_km2=4736.0,
            division="Medinipur",
        ),
        DistrictInfo(
            id="jhargram",
            name="Jhargram",
            lat=22.4473, lon=86.9890,
            elevation_m=78.0,
            base_flood_risk=1.2,
            major_rivers=["Subarnarekha", "Dulung", "Tarafeni"],
            population_density=282,
            area_km2=3037.0,
            division="Medinipur",
        ),
    ]

    _INDEX: ClassVar[dict[str, DistrictInfo]] = {d.id: d for d in _DISTRICTS}

    @classmethod
    def get_district(cls, district_id: str) -> DistrictInfo:
        """
        Retrieve a district by its unique ID.

        Args:
            district_id: Snake_case district identifier (e.g., 'murshidabad').

        Returns:
            The DistrictInfo for that district.

        Raises:
            KeyError: If the district ID does not exist in the registry.
        """
        if district_id not in cls._INDEX:
            raise KeyError(
                f"District '{district_id}' not found. "
                f"Valid IDs: {list(cls._INDEX.keys())}"
            )
        return cls._INDEX[district_id]

    @classmethod
    def get_all_districts(cls) -> list[DistrictInfo]:
        """Return all 23 West Bengal districts."""
        return list(cls._DISTRICTS)

    @classmethod
    def get_all_ids(cls) -> list[str]:
        """Return all district IDs."""
        return list(cls._INDEX.keys())

    @classmethod
    def count(cls) -> int:
        """Return the total number of registered districts."""
        return len(cls._DISTRICTS)
