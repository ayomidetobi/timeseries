"""Constants and enums for lookup tables and financial data generation."""
from enum import Enum


class assetClassEnum(str, Enum):
    """Enum for asset classes."""
    COMMODITY = "Commodity"
    CREDIT = "Credit"
    FX = "FX"


class subAssetClassEnum(str, Enum):
    """Enum for sub-asset classes."""
    BASE_METALS = "Base Metals"
    ENERGY = "Energy"
    PRECIOUS_METALS = "Precious Metals"
    OAS = "OAS"
    EM_LATAM = "EM LATAM"
    EM_CEEMEA = "EM CEEMEA"
    EM_APAC = "EM APAC"
    G10 = "G10"


class productTypeEnum(str, Enum):
    """Enum for product types."""
    SPOT = "Spot"
    INDEX = "Index"


class structureTypeEnum(str, Enum):
    """Enum for structure types."""
    OUTRIGHT = "Outright"


class marketSegmentEnum(str, Enum):
    """Enum for market segments."""
    GLOBAL = "Global"
    DM = "DM"
    EM = "EM"


class dataTypeEnum(str, Enum):
    """Enum for data types."""
    PRICE = "Price"
    OPEN_INTEREST = "Open Interest"
    PRICE_SPREAD = "Price Spread"


class fieldTypeEnum(str, Enum):
    """Enum for field types (FLDS)."""
    PX_LAST = "PX_LAST"
    OPEN_INT = "OPEN_INT"
    PX_OPEN = "PX_OPEN"
    PX_HIGH = "PX_HIGH"
    PX_LOW = "PX_LOW"
    PX_VOLUME = "PX_VOLUME"


# Ticker suffix mapping based on asset class and product type
TICKER_SUFFIX_MAP = {
    (assetClassEnum.COMMODITY, productTypeEnum.SPOT): "Comdty",
    (assetClassEnum.FX, productTypeEnum.SPOT): "Curncy",
    (assetClassEnum.CREDIT, productTypeEnum.INDEX): "Index",
    (assetClassEnum.COMMODITY, productTypeEnum.INDEX): "Index",
    (assetClassEnum.FX, productTypeEnum.INDEX): "Index",
}

# Limited commodity names (about 10)
COMMODITY_NAMES = [
    "Copper",
    "Gold",
    "Silver",
    "Platinum",
    "Oil, WTI",
    "Oil, Brent",
    "Natural Gas",
    "Aluminum",
    "Zinc",
    "Nickel",
]

# Sub-asset class to commodity mapping
COMMODITY_SUB_ASSET_MAP = {
    subAssetClassEnum.BASE_METALS: ["Copper", "Aluminum", "Zinc", "Nickel"],
    subAssetClassEnum.ENERGY: ["Oil, WTI", "Oil, Brent", "Natural Gas"],
    subAssetClassEnum.PRECIOUS_METALS: ["Gold", "Silver", "Platinum"],
}

# Market segment to sub-asset class mapping for FX
FX_MARKET_SUB_ASSET_MAP = {
    marketSegmentEnum.GLOBAL: [subAssetClassEnum.G10],
    marketSegmentEnum.DM: [subAssetClassEnum.G10],
    marketSegmentEnum.EM: [
        subAssetClassEnum.EM_LATAM,
        subAssetClassEnum.EM_CEEMEA,
        subAssetClassEnum.EM_APAC,
    ],
}

# Asset class to sub-asset class mapping
ASSET_CLASS_SUB_ASSET_MAP = {
    assetClassEnum.COMMODITY: [
        subAssetClassEnum.BASE_METALS,
        subAssetClassEnum.ENERGY,
        subAssetClassEnum.PRECIOUS_METALS,
    ],
    assetClassEnum.CREDIT: [subAssetClassEnum.OAS],
    assetClassEnum.FX: [
        subAssetClassEnum.EM_LATAM,
        subAssetClassEnum.EM_CEEMEA,
        subAssetClassEnum.EM_APAC,
        subAssetClassEnum.G10,
    ],
}

