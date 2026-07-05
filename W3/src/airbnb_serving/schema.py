from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ListingFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_type: str
    property_type: str
    neighbourhood_name: str
    accommodates: int
    bedrooms: Optional[float] = None
    beds: Optional[float] = None
    bathrooms: Optional[float] = None
    listing_price: float
    minimum_nights: int
    maximum_nights: int
    instant_bookable: bool
    is_superhost: bool
    host_listing_count: float
    total_reviews_before_cutoff: float
    unique_reviewers_before_cutoff: float
    avg_comment_len_before_cutoff: Optional[float] = None
    max_comment_len_before_cutoff: Optional[float] = None
    days_since_last_review: Optional[float] = None
    available_days_last_90d: float
    available_rate_last_90d: float
    avg_minimum_nights_calendar_last_90d: Optional[float] = None
    avg_maximum_nights_calendar_last_90d: Optional[float] = None
    available_days_last_30d: float
    available_rate_last_30d: float
    avg_minimum_nights_calendar_last_30d: Optional[float] = None
    avg_maximum_nights_calendar_last_30d: Optional[float] = None


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listing_id: int | None = None
    prediction: int = Field(..., ge=0, le=1)
    probability_high_demand: float = Field(..., ge=0.0, le=1.0)
    model_run_id: str
