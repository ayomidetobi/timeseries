"""Constants and enums for lookup tables and financial data generation."""
from enum import Enum


class AssetClassEnum(str, Enum):
    """Enum for asset classes."""
    COMMODITY = "Commodity"
    CREDIT = "Credit"
    FX = "FX"


class SubAssetClassEnum(str, Enum):
    """Enum for sub-asset classes."""
    BASE_METALS = "Base Metals"
    ENERGY = "Energy"
    PRECIOUS_METALS = "Precious Metals"
    OAS = "OAS"
    EM_LATAM = "EM LATAM"
    EM_CEEMEA = "EM CEEMEA"
    EM_APAC = "EM APAC"
    G10 = "G10"


class ProductTypeEnum(str, Enum):
    """Enum for product types."""
    SPOT = "Spot"
    INDEX = "Index"


class StructureTypeEnum(str, Enum):
    """Enum for structure types."""
    OUTRIGHT = "Outright"


class MarketSegmentEnum(str, Enum):
    """Enum for market segments."""
    GLOBAL = "Global"
    DM = "DM"
    EM = "EM"


class DataTypeEnum(str, Enum):
    """Enum for data types."""
    PRICE = "Price"
    OPEN_INTEREST = "Open Interest"
    PRICE_SPREAD = "Price Spread"


class FieldTypeEnum(str, Enum):
    """Enum for field types (FLDS)."""
    PX_LAST = "PX_LAST"
    OPEN_INT = "OPEN_INT"
    PX_OPEN = "PX_OPEN"
    PX_HIGH = "PX_HIGH"
    PX_LOW = "PX_LOW"
    PX_VOLUME = "PX_VOLUME"


# Ticker suffix mapping based on asset class and product type
TICKER_SUFFIX_MAP = {
    (AssetClassEnum.COMMODITY, ProductTypeEnum.SPOT): "Comdty",
    (AssetClassEnum.FX, ProductTypeEnum.SPOT): "Curncy",
    (AssetClassEnum.CREDIT, ProductTypeEnum.INDEX): "Index",
    (AssetClassEnum.COMMODITY, ProductTypeEnum.INDEX): "Index",
    (AssetClassEnum.FX, ProductTypeEnum.INDEX): "Index",
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
    SubAssetClassEnum.BASE_METALS: ["Copper", "Aluminum", "Zinc", "Nickel"],
    SubAssetClassEnum.ENERGY: ["Oil, WTI", "Oil, Brent", "Natural Gas"],
    SubAssetClassEnum.PRECIOUS_METALS: ["Gold", "Silver", "Platinum"],
}

# Market segment to sub-asset class mapping for FX
FX_MARKET_SUB_ASSET_MAP = {
    MarketSegmentEnum.GLOBAL: [SubAssetClassEnum.G10],
    MarketSegmentEnum.DM: [SubAssetClassEnum.G10],
    MarketSegmentEnum.EM: [
        SubAssetClassEnum.EM_LATAM,
        SubAssetClassEnum.EM_CEEMEA,
        SubAssetClassEnum.EM_APAC,
    ],
}

# Asset class to sub-asset class mapping
ASSET_CLASS_SUB_ASSET_MAP = {
    AssetClassEnum.COMMODITY: [
        SubAssetClassEnum.BASE_METALS,
        SubAssetClassEnum.ENERGY,
        SubAssetClassEnum.PRECIOUS_METALS,
    ],
    AssetClassEnum.CREDIT: [SubAssetClassEnum.OAS],
    AssetClassEnum.FX: [
        SubAssetClassEnum.EM_LATAM,
        SubAssetClassEnum.EM_CEEMEA,
        SubAssetClassEnum.EM_APAC,
        SubAssetClassEnum.G10,
    ],
}

