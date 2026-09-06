from enum import Enum


class AnalystType(str, Enum):
    # Fixed-income analysts (primary track)
    MACRO_POLICY = "macro_policy"
    CURVE_TECHNICALS = "curve_technicals"
    FED_SPEAK = "fed_speak"
    MACRO_CALENDAR = "macro_calendar"

    # Equity analysts (dual-track)
    MARKET = "market"
    # Wire value stays "social" for saved-config and string-keyed-caller
    # back-compat; the user-facing label is "Sentiment Analyst".
    SOCIAL = "social"
    NEWS = "news"
    FUNDAMENTALS = "fundamentals"


class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
