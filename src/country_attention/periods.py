"""Fixed, complete calendar-month research windows."""

from dataclasses import dataclass
from datetime import date
from zoneinfo import ZoneInfo

import pandas as pd


@dataclass(frozen=True)
class StudyWindow:
    start: str
    end: str

    def __post_init__(self):
        start, end = pd.Timestamp(self.start), pd.Timestamp(self.end)
        if start.day != 1 or end != end + pd.offsets.MonthEnd(0):
            raise ValueError("Use complete calendar months")
        if len(pd.period_range(start, end, freq="M")) != 12:
            raise ValueError("Study window must contain exactly 12 complete months")

    @property
    def months(self) -> list[str]:
        return pd.period_range(self.start, self.end, freq="M").astype(str).tolist()

    @classmethod
    def trailing(cls, as_of: str | None = None):
        stamp = pd.Timestamp(as_of or pd.Timestamp.now(ZoneInfo("Europe/Prague")).date())
        end = stamp.replace(day=1) - pd.Timedelta(days=1)
        start = (end.to_period("M") - 11).start_time
        return cls(start.date().isoformat(), end.date().isoformat())

    def validate_as_of(self, as_of: str):
        if pd.Timestamp(self.end).date() >= date.fromisoformat(as_of):
            raise ValueError("Search window must end before the collection date")
