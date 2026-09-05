"""Currency-agnostic configuration models for rates analysis.

Populated for USD/Fed only in this task. The abstraction is designed so
JPY/BOJ, GBP/BOE, CNY/PBOC are future config entries, not a rewrite.
"""
from pydantic import BaseModel, Field


class Curve(BaseModel):
    """Configuration for a sovereign yield curve."""
    currency: str = Field(description="ISO currency code, e.g. 'USD'")
    curve_type: str = Field(description="Curve identifier, e.g. 'UST', 'JGB'")
    tenors: list[str] = Field(description="Tenor labels, e.g. ['2Y', '5Y', '10Y', '30Y']")
    tenor_series: dict[str, str] = Field(
        description="Mapping of tenor label → data series ID (e.g. FRED series)"
    )


class CentralBank(BaseModel):
    """Configuration for a central bank's data sources."""
    currency: str = Field(description="ISO currency code")
    name: str = Field(description="Central bank name, e.g. 'Fed'")
    policy_rate_series: str = Field(description="Series ID for policy rate")
    funding_rate_series: str = Field(description="Series ID for overnight funding rate")
    meeting_calendar_source: str = Field(
        description="Source identifier for meeting calendar data"
    )
    speech_source: str = Field(
        description="Source identifier for speech/communication data"
    )
