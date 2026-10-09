"""YNAB metrics."""

import asyncio
import datetime
from typing import TYPE_CHECKING

import polars as pl
import ynab

from pysomebar.config import CONFIG

from .module import NeedsInternetModule

if TYPE_CHECKING:
    from pysomebar.util import ColoriserProtocol


def get_transactions() -> pl.DataFrame:
    """Retrieve transactions for the past two weeks from the YNAB API."""
    access_token = CONFIG.ynab.access_token
    if access_token is None or access_token == "":
        msg = "YNAB access token not provided."
        raise ValueError(msg)

    plan_id = CONFIG.ynab.plan_id
    if plan_id is None or plan_id == "":
        msg = "YNAB plan ID not provided."
        raise ValueError(msg)

    today = datetime.datetime.now().astimezone().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    since_date = start_of_week - datetime.timedelta(weeks=1)

    config = ynab.Configuration(access_token=access_token)

    with ynab.ApiClient(config) as api_client:
        api_instance = ynab.TransactionsApi(api_client)
        response = api_instance.get_transactions(plan_id, since_date=since_date)
        transactions = response.data.transactions

        if not transactions:
            return pl.DataFrame(
                schema={
                    "id": pl.String,
                    "var_date": pl.Date,
                    "cleared": pl.String,
                    "approved": pl.Boolean,
                    "account_id": pl.String,
                    "payee_name": pl.String,
                    "category_name": pl.String,
                    "deleted": pl.Boolean,
                    "amount_currency": pl.Int64,
                },
            )

        df = pl.concat(
            [pl.json_normalize(t.model_dump()) for t in transactions],
            how="vertical_relaxed",
        )

    return df.select(
        "id",
        "var_date",
        "cleared",
        "approved",
        "account_id",
        "payee_name",
        "category_name",
        "deleted",
        "amount_currency",
    ).filter(~pl.col("deleted"))


def get_period_total(
    df: pl.DataFrame,
    weeks_ago: int = 0,
    date_col: str = "var_date",
    amount_col: str = "amount_currency",
) -> float:
    """Get sum of transactions from the start of the week to equivalent day this week."""
    today = datetime.datetime.now().astimezone().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    start = start_of_week - datetime.timedelta(weeks=weeks_ago)
    end = start + datetime.timedelta(days=(today - start_of_week).days + 1)

    amount = df.filter(pl.col(date_col).is_between(start, end, closed="left"))[amount_col].sum()

    return round(float(amount) or 0.0, 2)


def format_output(df: pl.DataFrame) -> str:
    """Format amounts and percent change since last week."""
    past_week = get_period_total(df)
    week_before = get_period_total(df, weeks_ago=1)

    if week_before == 0:
        change = "N/A"
    else:
        percent_change = round((abs(past_week) / abs(week_before) - 1) * 100)
        sign = "+" if percent_change > 0 else ""
        change = f"{sign}{percent_change}%"

    return f"Week: £{-past_week:.2f} ({change})"


class YNABModule(NeedsInternetModule):
    """YNAB module displaying spend this week compared to last week."""

    name = "ynab"

    def __init__(self, coloriser: ColoriserProtocol | None) -> None:  # noqa: D107
        super().__init__(coloriser=coloriser, name=self.name, interval=CONFIG.ynab.interval)

        self.refresh_signal = 1
        self.raw_output = self.output

        if CONFIG.ynab.access_token is None or CONFIG.ynab.access_token == "":
            msg = "YNAB access token not provided."
            raise ValueError(msg)

        if CONFIG.ynab.plan_id is None or CONFIG.ynab.plan_id == "":
            msg = "YNAB plan ID not provided."
            raise ValueError(msg)

    async def update(self) -> None:  # noqa: D102
        for _ in range(self.connect_retries):
            if await self.is_internet_available():
                await self.make_output()
                return

            await asyncio.sleep(self.retry_interval)

            self.output = "No network!"
            self.raw_output = "No network!"

    async def get_weekly_total(self) -> str | None:
        """Get weekly totals from YNAB API and format as string."""
        try:
            df = await asyncio.to_thread(get_transactions)
        except:  # noqa: E722
            return None

        return format_output(df)

    async def make_output(self) -> None:  # noqa: D102
        self.output = "Updating..."
        await self.request_redraw()

        result = await self.get_weekly_total()

        if result is None:
            self.output = "No network!"
        else:
            self.output = result
            self.raw_output = self.output

        await self.request_redraw()
