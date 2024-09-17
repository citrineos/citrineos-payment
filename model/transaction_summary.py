from moneyed import Money
from datetime import datetime, timezone
from decimal import Decimal


ZERO = Decimal("0")
HUNDRED = Decimal("100")
SECONDS_IN_MINUTE = Decimal("60")


class TransactionSummary:
    def __init__(
        self,
        kwh: float,
        start_time: datetime,
        end_time: datetime,
        currency: str,
        tax_rate: float,
        payment_fee: float,
        price_kwh: float,
        price_minute: float,
        price_session: float,
    ):
        self.kwh = kwh
        self.start_time = start_time
        self.end_time = end_time

        self.currency = currency
        self.tax_rate = tax_rate
        self.payment_fee = payment_fee

        self.price_kwh = price_kwh
        self.price_minute = price_minute
        self.price_session = price_session

    @property
    def energy_costs(self) -> Money | None:
        if self.kwh is not None and self.price_kwh is not None:
            return Money(amount=self.price_kwh, currency=self.currency) * self.kwh
        else:
            return None

    @property
    def time_consumption_min(self) -> Decimal:
        if self.start_time is None:
            return ZERO

        session_end_time = (
            self.end_time if self.end_time is not None else datetime.now(timezone.utc)
        )
        return (
            Decimal.from_float((session_end_time - self.start_time).total_seconds())
            / SECONDS_IN_MINUTE
        )

    @property
    def time_costs(self) -> Money | None:
        if self.time_consumption_min is not None and self.price_minute is not None:
            return (
                Money(amount=self.price_minute, currency=self.currency)
                * self.time_consumption_min
            )
        else:
            return None

    @property
    def session_consumption(self) -> int:
        return 1

    @property
    def session_costs(self) -> Money | None:
        if self.price_session is not None:
            return Money(amount=self.price_session, currency=self.currency)
        else:
            return None

    @property
    def payment_costs_tax_rate(self) -> int:
        return 0  # currently 0. needed for reverse charge scenarios

    @property
    def total_costs_net(self) -> Money:
        result = Money(amount="0", currency=self.currency)
        if self.energy_costs is not None:
            result += self.energy_costs
        if self.time_costs is not None:
            result += self.time_costs
        if self.session_costs is not None:
            result += self.session_costs
        return result

    @property
    def tax_costs(self) -> Money:
        return self.total_costs_net * self.tax_rate / HUNDRED

    @property
    def total_costs_gross(self) -> Money:
        return self.total_costs_net + self.tax_costs

    @property
    def payment_costs_gross(self) -> Money:
        return (
            self.total_costs_net
            * (1 + self.payment_costs_tax_rate / HUNDRED)
            * self.payment_fee
            / HUNDRED
        )

    @property
    def payment_costs_net(self) -> Money:
        return self.total_costs_net * self.payment_fee / HUNDRED
