import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from model.transaction_summary import TransactionSummary
from moneyed import Money
from decimal import Decimal


class TransactionSummaryTests(unittest.TestCase):
    def test_energy_costs(self):
        currency = "USD"
        for price_kwh, kwh, expected_energy_costs in [
            (0.09, 20, Money(amount="1.80", currency=currency)),
            (0.14, 20, Money(amount="2.80", currency=currency)),
            (0.23, 20, Money(amount="4.60", currency=currency)),
            (0.25, 20, Money(amount="5.00", currency=currency)),
            (0.47, 20, Money(amount="9.40", currency=currency)),
            (0.61, 20, Money(amount="12.20", currency=currency)),
            (0.69, 20, Money(amount="13.80", currency=currency)),
            (0.09, 23.54, Money(amount="2.1186", currency=currency)),
            (0.14, 23.54, Money(amount="3.2956", currency=currency)),
            (0.23, 23.54, Money(amount="5.4142", currency=currency)),
            (0.25, 23.54, Money(amount="5.885", currency=currency)),
            (0.47, 23.54, Money(amount="11.0638", currency=currency)),
            (0.61, 23.54, Money(amount="14.3594", currency=currency)),
            (0.69, 23.54, Money(amount="16.2426", currency=currency)),
            (0.09, 39.99, Money(amount="3.5991", currency=currency)),
            (0.14, 39.99, Money(amount="5.5986", currency=currency)),
            (0.23, 39.99, Money(amount="9.1977", currency=currency)),
            (0.25, 39.99, Money(amount="9.9975", currency=currency)),
            (0.47, 39.99, Money(amount="18.7953", currency=currency)),
            (0.61, 39.99, Money(amount="24.3939", currency=currency)),
            (0.69, 39.99, Money(amount="27.5931", currency=currency)),
            (0.092, 41.784, Money(amount="3.844128", currency=currency)),
            (0.145, 41.784, Money(amount="6.05868", currency=currency)),
            (0.231, 41.784, Money(amount="9.652104", currency=currency)),
            (0.254, 41.784, Money(amount="10.613136", currency=currency)),
            (0.479, 41.784, Money(amount="20.014536", currency=currency)),
            (0.617, 41.784, Money(amount="25.780728", currency=currency)),
            (0.699, 41.784, Money(amount="29.207016", currency=currency)),
            (1, 9.512, Money(amount="9.512", currency=currency)),
            (1, 12.421, Money(amount="12.421", currency=currency)),
            (1, 16.765, Money(amount="16.765", currency=currency)),
            (1, 21.517, Money(amount="21.517", currency=currency)),
            (1, 26.214, Money(amount="26.214", currency=currency)),
            (1, 31.431, Money(amount="31.431", currency=currency)),
            (1, 43.589, Money(amount="43.589", currency=currency)),
        ]:
            with self.subTest(
                price_kwh=price_kwh,
                kwh=kwh,
                expected_energy_costs=expected_energy_costs,
            ):
                summary = a_transaction_summary(
                    kwh=kwh, currency=currency, price_kwh=price_kwh
                )
                self.assertEqual(summary.energy_costs, expected_energy_costs)

    def test_no_energy_costs_when_missing_transaction_kwh(self):
        summary = a_transaction_summary(kwh=None, price_kwh=0.43)
        self.assertIsNone(summary.energy_costs)

    def test_no_energy_costs_when_missing_price_kwh(self):
        summary = a_transaction_summary(kwh=39.99, price_kwh=None)
        self.assertIsNone(summary.energy_costs)

    def test_no_energy_costs_when_missing_transaction_kwh_and_price_kwh(self):
        summary = a_transaction_summary(kwh=None, price_kwh=None)
        self.assertIsNone(summary.energy_costs)

    def test_time_consumption_min(self):
        for start_time, end_time, expected_time_consumption_min in [
            (
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 0, 0),
                Decimal("0"),
            ),
            (
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 0, 1),
                Decimal("0.01666666666666666666666666667"),
            ),
            (
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 0, 59),
                Decimal("0.9833333333333333333333333333"),
            ),
            (
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 1, 0),
                Decimal("1"),
            ),
            (
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Decimal("20"),
            ),
            (
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Decimal("59.98333333333333333333333333"),
            ),
            (
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Decimal("29.58333333333333333333333333"),
            ),
            (
                datetime(2024, 8, 15, 23, 59, 59),
                datetime(2024, 8, 16, 0, 0, 0),
                Decimal("0.01666666666666666666666666667"),
            ),
            (
                datetime(2024, 8, 15, 0, 0, 0),
                datetime(2024, 8, 15, 23, 59, 59),
                Decimal("1439.983333333333333333333333"),
            ),
            (
                datetime(2024, 8, 15, 0, 0, 0),
                datetime(2024, 8, 16, 0, 0, 0),
                Decimal("1440"),
            ),
            (
                datetime(2024, 8, 15, 0, 0, 0),
                datetime(2024, 8, 18, 0, 0, 0),
                Decimal("4320"),
            ),
            (
                datetime(2024, 12, 31, 23, 59, 59),
                datetime(2025, 1, 1, 0, 0, 1),
                Decimal("0.03333333333333333333333333333"),
            ),
        ]:
            with self.subTest(
                start_time=start_time,
                end_time=end_time,
                expected_time_consumption_min=expected_time_consumption_min,
            ):
                summary = a_transaction_summary(
                    start_time=start_time, end_time=end_time
                )
                self.assertEqual(
                    summary.time_consumption_min, expected_time_consumption_min
                )

    def test_time_consumption_min_includes_microseconds(self):
        for start_time, end_time, expected_time_consumption_min in [
            (
                datetime(2024, 8, 15, 10, 0, 0, 0),
                datetime(2024, 8, 15, 10, 0, 0, 500_000),
                Decimal("0.008333333333333333333333333333"),
            ),
            (
                datetime(2024, 8, 15, 10, 0, 0, 499_999),
                datetime(2024, 8, 15, 10, 20, 0, 999_999),
                Decimal("20.00833333333333333333333333"),
            ),
        ]:
            with self.subTest(
                start_time=start_time,
                end_time=end_time,
                expected_time_consumption_min=expected_time_consumption_min,
            ):
                summary = a_transaction_summary(
                    start_time=start_time, end_time=end_time
                )
                self.assertEqual(
                    summary.time_consumption_min, expected_time_consumption_min
                )

    def test_time_consumption_min_when_missing_end_time(self):
        now = datetime(2024, 8, 15, 10, 59, 59)
        for start_time, expected_time_consumption_min in [
            (
                datetime(2024, 8, 15, 9, 59, 59),
                Decimal("60"),
            ),
            (
                datetime(2024, 8, 15, 10, 0, 0),
                Decimal("59.98333333333333333333333333"),
            ),
            (
                datetime(2024, 8, 15, 10, 30, 0),
                Decimal("29.98333333333333333333333333"),
            ),
            (
                datetime(2024, 8, 15, 10, 41, 56),
                Decimal("18.05"),
            ),
            (
                datetime(2024, 8, 15, 10, 59, 59),
                Decimal("0"),
            ),
        ]:
            with self.subTest(
                start_time=start_time,
                now=now,
                expected_time_consumption_min=expected_time_consumption_min,
            ):
                with patch("model.transaction_summary.datetime") as dt_mock:
                    dt_mock.now.return_value = now
                    summary = a_transaction_summary(
                        start_time=start_time, end_time=None
                    )
                    self.assertEqual(
                        summary.time_consumption_min, expected_time_consumption_min
                    )
                    dt_mock.now.assert_called_with(timezone.utc)

    def test_time_costs(self):
        currency = "USD"
        for (
            price_minute,
            start_time,
            end_time,
            expected_time_costs,
        ) in [  # TODO: issue with repeating decimals?
            (
                0.09,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="1.80", currency=currency),
            ),
            (
                0.14,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="2.80", currency=currency),
            ),
            (
                0.23,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="4.60", currency=currency),
            ),
            (
                0.25,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="5.00", currency=currency),
            ),
            (
                0.47,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="9.40", currency=currency),
            ),
            (
                0.61,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="12.20", currency=currency),
            ),
            (
                0.69,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="13.80", currency=currency),
            ),
            (
                0.09,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="5.3985", currency=currency),
            ),
            (
                0.14,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="8.397666666666666666666666666", currency=currency),
            ),
            (
                0.23,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="13.79616666666666666666666667", currency=currency),
            ),
            (
                0.25,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="14.99583333333333333333333333", currency=currency),
            ),
            (
                0.47,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="28.19216666666666666666666667", currency=currency),
            ),
            (
                0.61,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="36.58983333333333333333333333", currency=currency),
            ),
            (
                0.69,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="41.3885", currency=currency),
            ),
            (
                0.09,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="2.6625", currency=currency),
            ),
            (
                0.14,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="4.141666666666666666666666666", currency=currency),
            ),
            (
                0.23,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="6.804166666666666666666666666", currency=currency),
            ),
            (
                0.25,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="7.395833333333333333333333332", currency=currency),
            ),
            (
                0.47,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="13.90416666666666666666666667", currency=currency),
            ),
            (
                0.61,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="18.04583333333333333333333333", currency=currency),
            ),
            (
                0.69,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="20.4125", currency=currency),
            ),
        ]:
            with self.subTest(
                price_minute=price_minute,
                start_time=start_time,
                end_time=end_time,
                expected_time_costs=expected_time_costs,
            ):
                summary = a_transaction_summary(
                    start_time=start_time,
                    end_time=end_time,
                    currency=currency,
                    price_minute=price_minute,
                )
                self.assertEqual(summary.time_costs, expected_time_costs)

    def test_session_consumption_is_always_one(self):
        summary = a_transaction_summary()
        self.assertEqual(summary.session_consumption, 1)

    def test_session_costs(self):
        currency = "USD"
        for summary, expected_session_costs in [
            (
                a_transaction_summary(currency=currency, price_session=0),
                Money(amount="0", currency=currency),
            ),
            (
                a_transaction_summary(currency=currency, price_session=0.99),
                Money(amount="0.99", currency=currency),
            ),
            (
                a_transaction_summary(currency=currency, price_session=1.99),
                Money(amount="1.99", currency=currency),
            ),
            (
                a_transaction_summary(currency=currency, price_session=5.01),
                Money(amount="5.01", currency=currency),
            ),
        ]:
            with self.subTest(
                price_session=summary.price_session,
                expected_session_costs=expected_session_costs,
            ):
                self.assertEqual(summary.session_costs, expected_session_costs)

    def test_payment_costs_tax_rate_is_always_zero(self):
        summary = a_transaction_summary()
        self.assertEqual(summary.payment_costs_tax_rate, 0)

    def test_total_costs_net(self):
        currency = "USD"
        for (
            price_kwh,
            price_minute,
            price_session,
            kwh,
            start_time,
            end_time,
            expected_total_costs_net,
        ) in [  # TODO: issue with repeating decimals?
            (
                0.09,
                0.00,
                0.00,
                0,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="0", currency=currency),
            ),
            (
                0.00,
                0.23,
                0.00,
                0,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="4.60", currency=currency),
            ),
            (
                0.09,
                0.00,
                3.99,
                0,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="3.99", currency=currency),
            ),
            (
                0.00,
                0.00,
                0.00,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="0", currency=currency),
            ),
            (
                0.09,
                0.23,
                0.00,
                20,
                None,
                None,
                Money(amount="1.80", currency=currency),
            ),
            (
                0.09,
                0.23,
                3.99,
                20,
                None,
                None,
                Money(amount="5.79", currency=currency),
            ),
            (
                0.09,
                0.09,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="7.59", currency=currency),
            ),
            (
                0.14,
                0.14,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="9.59", currency=currency),
            ),
            (
                0.23,
                0.23,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="13.19", currency=currency),
            ),
            (
                0.25,
                0.25,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="13.99", currency=currency),
            ),
            (
                0.47,
                0.47,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="22.79", currency=currency),
            ),
            (
                0.61,
                0.61,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="28.39", currency=currency),
            ),
            (
                0.69,
                0.69,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                Money(amount="31.59", currency=currency),
            ),
            (
                0.09,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="10.9876", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="12.9871", currency=currency),
            ),
            (
                0.23,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="16.5862", currency=currency),
            ),
            (
                0.25,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="17.386", currency=currency),
            ),
            (
                0.47,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="26.1838", currency=currency),
            ),
            (
                0.61,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="31.7824", currency=currency),
            ),
            (
                0.69,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="34.9816", currency=currency),
            ),
            (
                0.145,
                0.09,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="10.71118", currency=currency),
            ),
            (
                0.145,
                0.14,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="12.19034666666666666666666667", currency=currency),
            ),
            (
                0.145,
                0.23,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="14.85284666666666666666666667", currency=currency),
            ),
            (
                0.145,
                0.25,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="15.44451333333333333333333333", currency=currency),
            ),
            (
                0.145,
                0.47,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="21.95284666666666666666666667", currency=currency),
            ),
            (
                0.145,
                0.61,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="26.09451333333333333333333333", currency=currency),
            ),
            (
                0.145,
                0.69,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                Money(amount="28.46118", currency=currency),
            ),
        ]:
            with self.subTest(
                price_kwh=price_kwh,
                price_minute=price_minute,
                price_session=price_session,
                kwh=kwh,
                start_time=start_time,
                end_time=end_time,
                expected_total_costs_net=expected_total_costs_net,
            ):
                summary = a_transaction_summary(
                    start_time=start_time,
                    end_time=end_time,
                    kwh=kwh,
                    currency=currency,
                    price_kwh=price_kwh,
                    price_minute=price_minute,
                    price_session=price_session,
                )
                self.assertEqual(summary.total_costs_net, expected_total_costs_net)

    def test_tax_costs(self):
        currency = "USD"
        for (
            price_kwh,
            price_minute,
            price_session,
            tax_rate,
            kwh,
            start_time,
            end_time,
            expected_tax_costs,
        ) in [
            (
                0.14,
                0.09,
                1.99,
                0,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="0", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                1,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="0.129871", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                3,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="0.389613", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                8,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="1.038968", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                12,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="1.558452", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                19,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="2.467549", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                23,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="2.987033", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                32,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="4.155872", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                50,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="6.49355", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                100,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="12.9871", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                200,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="25.9742", currency=currency),
            ),
        ]:
            with self.subTest(
                price_kwh=price_kwh,
                price_minute=price_minute,
                price_session=price_session,
                tax_rate=tax_rate,
                kwh=kwh,
                start_time=start_time,
                end_time=end_time,
                expected_tax_costs=expected_tax_costs,
            ):
                summary = a_transaction_summary(
                    start_time=start_time,
                    end_time=end_time,
                    kwh=kwh,
                    currency=currency,
                    price_kwh=price_kwh,
                    price_minute=price_minute,
                    price_session=price_session,
                    tax_rate=tax_rate,
                )
                self.assertEqual(summary.tax_costs, expected_tax_costs)

    def test_total_costs_gross(self):
        currency = "USD"
        for (
            price_kwh,
            price_minute,
            price_session,
            tax_rate,
            kwh,
            start_time,
            end_time,
            expected_total_costs_gross,
        ) in [
            (
                0.14,
                0.09,
                1.99,
                0,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="12.9871", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                1,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="13.116971", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                3,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="13.376713", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                8,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="14.026068", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                12,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="14.545552", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                19,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="15.454649", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                23,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="15.974133", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                32,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="17.142972", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                50,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="19.48065", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                100,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="25.9742", currency=currency),
            ),
            (
                0.14,
                0.09,
                1.99,
                200,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                Money(amount="38.9613", currency=currency),
            ),
        ]:
            with self.subTest(
                price_kwh=price_kwh,
                price_minute=price_minute,
                price_session=price_session,
                tax_rate=tax_rate,
                kwh=kwh,
                start_time=start_time,
                end_time=end_time,
                expected_total_costs_gross=expected_total_costs_gross,
            ):
                summary = a_transaction_summary(
                    start_time=start_time,
                    end_time=end_time,
                    kwh=kwh,
                    currency=currency,
                    price_kwh=price_kwh,
                    price_minute=price_minute,
                    price_session=price_session,
                    tax_rate=tax_rate,
                )
                self.assertEqual(summary.total_costs_gross, expected_total_costs_gross)


def a_transaction_summary(**overrides) -> TransactionSummary:
    defaults = {
        "start_time": datetime(2023, 8, 14, 10, 00, 00),
        "end_time": datetime(2023, 8, 14, 10, 30, 59),
        "kwh": 31.74,
        "currency": "USD",
        "price_minute": 0.05,
        "price_session": 3.00,
        "price_kwh": 0.30,
        "tax_rate": 23,
        "payment_fee": 1,
    }

    defaults.update(overrides)

    return TransactionSummary(**defaults)


if __name__ == "__main__":
    unittest.main()
