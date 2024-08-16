import os
import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault("CONFIG_PATH", ".env.test")

from db.init_db import Checkout, Tariff
from utils.utils import generate_pricing


class GeneratePricingTests(unittest.TestCase):
    def test_pricing_has_currency(self):
        for tariff, expected_currency in [
            (a_tariff(currency="USD"), "USD"),
            (a_tariff(currency="EUR"), "EUR"),
            (a_tariff(currency="CAD"), "CAD"),
            (a_tariff(currency="GBP"), "GBP"),
        ]:
            with self.subTest(expected_currency=expected_currency):
                checkout = a_checkout(tariff_id=tariff.id)

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.currency, expected_currency)

    def test_pricing_has_tax_rate(self):
        for tariff, expected_tax_rate in [  # TODO: fix type mismatch
            (a_tariff(tax_rate=1), 1),
            (a_tariff(tax_rate=2), 2),
            (a_tariff(tax_rate=5), 5),
            (a_tariff(tax_rate=23), 23),
        ]:
            with self.subTest(expected_tax_rate=expected_tax_rate):
                checkout = a_checkout(tariff_id=tariff.id)

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.tax_rate, expected_tax_rate)

    def test_pricing_has_payment_fee(self):
        for tariff, expected_payment_fee in [  # TODO: fix type mismatch
            (a_tariff(payment_fee=1), 1),
            (a_tariff(payment_fee=2), 2),
            (a_tariff(payment_fee=5), 5),
            (a_tariff(payment_fee=23), 23),
        ]:
            with self.subTest(expected_payment_fee=expected_payment_fee):
                checkout = a_checkout(tariff_id=tariff.id)

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.payment_fee, expected_payment_fee)

    def test_pricing_has_energy_consumption_kwh(self):
        tariff = a_tariff()
        for checkout, expected_energy_consumption in [
            (a_checkout(tariff_id=tariff.id, transaction_kwh=0), 0),
            (a_checkout(tariff_id=tariff.id, transaction_kwh=0.01), 0.01),
            (a_checkout(tariff_id=tariff.id, transaction_kwh=0.00001), 0.00001),
            (a_checkout(tariff_id=tariff.id, transaction_kwh=0.99999), 0.99999),
            (a_checkout(tariff_id=tariff.id, transaction_kwh=1), 1),
            (a_checkout(tariff_id=tariff.id, transaction_kwh=10.23), 10.23),
            (a_checkout(tariff_id=tariff.id, transaction_kwh=39.99), 39.99),
        ]:
            with self.subTest(
                transaction_kwh=checkout.transaction_kwh,
                expected_energy_consumption=expected_energy_consumption,
            ):
                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(
                        pricing.energy_consumption_kwh, expected_energy_consumption
                    )

    def test_pricing_has_energy_costs(self):
        for price_kwh, kwh, expected_energy_costs in [
            (0.09, 20, 180),  # 1.80
            (0.14, 20, 280),  # 2.80
            (0.23, 20, 460),  # 4.60
            (0.25, 20, 500),  # 5.00
            (0.47, 20, 940),  # 9.40
            (0.61, 20, 1220),  # 12.20
            (0.69, 20, 1380),  # 13.80
            (0.09, 23.54, 211),  # 2.1186
            (0.14, 23.54, 329),  # 3.2956
            (0.23, 23.54, 541),  # 5.4142
            (0.25, 23.54, 588),  # 5.885
            (0.47, 23.54, 1106),  # 11.0638
            (0.61, 23.54, 1435),  # 14.3594
            (0.69, 23.54, 1624),  # 16.2426
            (0.09, 39.99, 359),  # 3.5991
            (0.14, 39.99, 559),  # 5.5986
            (0.23, 39.99, 919),  # 9.1977
            (0.25, 39.99, 999),  # 9.9975
            (0.47, 39.99, 1879),  # 18.7953
            (0.61, 39.99, 2439),  # 24.3939
            (0.69, 39.99, 2759),  # 27.5931
            (0.092, 41.784, 384),  # 3.844128
            (0.145, 41.784, 605),  # 6.05868
            (0.231, 41.784, 965),  # 9.652104
            (0.254, 41.784, 1061),  # 10.613136
            (0.479, 41.784, 2001),  # 20.014536
            (0.617, 41.784, 2578),  # 25.780728
            (0.699, 41.784, 2920),  # 29.207016
            (1, 9.512, 951),  # 9.512
            (1, 12.421, 1242),  # 12.421
            (1, 16.765, 1676),  # 16.765
            (1, 21.517, 2151),  # 21.517
            (1, 26.214, 2621),  # 26.214
            (1, 31.431, 3143),  # 31.431
            (1, 43.589, 4358),  # 43.589
        ]:
            with self.subTest(
                price_kwh=price_kwh,
                kwh=kwh,
                expected_energy_costs=expected_energy_costs,
            ):
                tariff = a_tariff(price_kwh=price_kwh)
                checkout = a_checkout(tariff_id=tariff.id, transaction_kwh=kwh)

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.energy_costs, expected_energy_costs)

    def test_pricing_has_no_energy_costs_when_missing_transaction_kwh(self):
        tariff = a_tariff(price_kwh=0.43)
        checkout = a_checkout(tariff_id=tariff.id, transaction_kwh=None)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertIsNone(pricing.energy_costs)

    def test_pricing_has_no_energy_costs_when_missing_price_kwh(self):
        tariff = a_tariff(price_kwh=None)
        checkout = a_checkout(tariff_id=tariff.id, transaction_kwh=39.99)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertIsNone(pricing.energy_costs)

    def test_pricing_has_no_energy_costs_when_missing_transaction_kwh_and_price_kwh(
        self,
    ):
        tariff = a_tariff(price_kwh=None)
        checkout = a_checkout(tariff_id=tariff.id, transaction_kwh=None)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertIsNone(pricing.energy_costs)

    def test_pricing_has_time_costs(self):
        for price_minute, start_time, end_time, expected_time_costs in [
            (
                0.09,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                180,
            ),  # 1.80
            (
                0.14,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                280,
            ),  # 2.80
            (
                0.23,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                460,
            ),  # 4.60
            (
                0.25,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                500,
            ),  # 5.00
            (
                0.47,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                940,
            ),  # 9.40
            (
                0.61,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                1220,
            ),  # 12.20
            (
                0.69,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                1380,
            ),  # 13.80
            (
                0.09,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                539,
            ),  # 5.3985
            (
                0.14,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                839,
            ),  # 8.397666666666666666666666666666
            (
                0.23,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1379,
            ),  # 13.79616666666666666666666666666
            (
                0.25,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1499,
            ),  # 14.995833333333333333333333333333
            (
                0.47,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                2819,
            ),  # 28.19216666666666666666666666666
            (
                0.61,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                3658,
            ),  # 36.589833333333333333333333333333
            (
                0.69,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                4138,
            ),  # 41.3885
            (
                0.09,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                266,
            ),  # 2.6625
            (
                0.14,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                414,
            ),  # 4.14166666666666666666666666666
            (
                0.23,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                680,
            ),  # 6.8041666666666666666666666666667
            (
                0.25,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                739,
            ),  # 7.395833333333333333333333333333
            (
                0.47,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                1390,
            ),  # 13.90416666666666666666666666666
            (
                0.61,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                1804,
            ),  # 18.04583333333333333333333333333
            (
                0.69,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                2041,
            ),  # 20.4125
        ]:
            with self.subTest(
                price_minute=price_minute,
                start_time=start_time,
                end_time=end_time,
                expected_time_costs=expected_time_costs,
            ):
                tariff = a_tariff(price_minute=price_minute)
                checkout = a_checkout(
                    tariff_id=tariff.id,
                    transaction_start_time=start_time,
                    transaction_end_time=end_time,
                )

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.time_costs, expected_time_costs)

    def test_pricing_has_zero_time_costs_when_missing_transaction_start_time(self):
        tariff = a_tariff(price_minute=0.09)
        checkout = a_checkout(tariff_id=tariff.id, transaction_start_time=None)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertEqual(pricing.time_costs, 0)

    def test_pricing_has_no_time_costs_when_missing_price_minute(self):
        tariff = a_tariff(price_minute=None)
        checkout = a_checkout(
            tariff_id=tariff.id, transaction_start_time=datetime(2024, 8, 15, 10, 0, 0)
        )

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertIsNone(pricing.time_costs)

    def test_pricing_has_no_time_costs_when_missing_transaction_start_time_and_price_minute(
        self,
    ):
        tariff = a_tariff(price_minute=None)
        checkout = a_checkout(tariff_id=tariff.id, transaction_start_time=None)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertIsNone(pricing.time_costs)

    def test_pricing_has_one_session_consumption(self):
        tariff = a_tariff()
        checkout = a_checkout(tariff_id=tariff.id)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertEqual(pricing.session_consumption, 1)

    def test_pricing_has_session_costs(self):
        for tariff, expected_session_costs in [
            (a_tariff(price_session=0), 0),
            (a_tariff(price_session=0.99), 99),
            (a_tariff(price_session=1.99), 199),
            (a_tariff(price_session=5.01), 501),
        ]:
            with self.subTest(
                price_session=tariff.price_session,
                expected_session_costs=expected_session_costs,
            ):
                checkout = a_checkout(tariff_id=tariff.id)

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.session_costs, expected_session_costs)

    def test_pricing_has_no_session_costs_when_missing_price_session(self):
        tariff = a_tariff(price_session=None)
        checkout = a_checkout(tariff_id=tariff.id)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertIsNone(pricing.session_costs)

    def test_pricing_has_total_costs_net(self):
        for (
            price_kwh,
            price_minute,
            price_session,
            kwh,
            start_time,
            end_time,
            expected_total_costs_net,
        ) in [
            (
                0.09,
                0.00,
                0.00,
                0,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                0,
            ),
            (
                0.00,
                0.23,
                0.00,
                0,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                460,
            ),
            (
                0.09,
                0.00,
                3.99,
                0,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                399,
            ),
            (
                0.00,
                0.00,
                0.00,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                0,
            ),
            (0.09, 0.23, 0.00, 20, None, None, 180),
            (0.09, 0.23, 3.99, 20, None, None, 579),
            (
                0.09,
                0.09,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                759,
            ),
            (
                0.14,
                0.14,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                959,
            ),
            (
                0.23,
                0.23,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                1319,
            ),
            (
                0.25,
                0.25,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                1399,
            ),
            (
                0.47,
                0.47,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                2279,
            ),
            (
                0.61,
                0.61,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                2839,
            ),
            (
                0.69,
                0.69,
                3.99,
                20,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 20, 0),
                3159,
            ),
            (
                0.09,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1098,
            ),  # 10.9876
            (
                0.14,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1298,
            ),  # 12.9871
            (
                0.23,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1658,
            ),  # 16.5862
            (
                0.25,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1738,
            ),  # 17.386
            (
                0.47,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                2618,
            ),  # 26.1838
            (
                0.61,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                3178,
            ),  # 31.7824
            (
                0.69,
                0.09,
                1.99,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                3498,
            ),  # 34.9816
            (
                0.145,
                0.09,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                1071,
            ),  # 10.71118
            (
                0.145,
                0.14,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                1219,
            ),  # 12.190346666666666
            (
                0.145,
                0.23,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                1485,
            ),  # 14.85284666666666666666666666666
            (
                0.145,
                0.25,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                1544,
            ),  # 15.44451333333333333333333
            (
                0.145,
                0.47,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                2195,
            ),  # 21.9528466666666666666
            (
                0.145,
                0.61,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                2609,
            ),  # 26.0945133333333333333333
            (
                0.145,
                0.69,
                1.99,
                41.784,
                datetime(2024, 8, 15, 23, 50, 59),
                datetime(2024, 8, 16, 0, 20, 34),
                2846,
            ),  # 28.46118
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
                tariff = a_tariff(
                    price_kwh=price_kwh,
                    price_minute=price_minute,
                    price_session=price_session,
                )
                checkout = a_checkout(
                    tariff_id=tariff.id,
                    transaction_kwh=kwh,
                    transaction_start_time=start_time,
                    transaction_end_time=end_time,
                )

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.total_costs_net, expected_total_costs_net)

    def test_pricing_has_tax_costs(self):
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
                0,
            ),
            (
                0.14,
                0.09,
                1.99,
                1,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                12,
            ),  # 0.129871
            (
                0.14,
                0.09,
                1.99,
                3,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                38,
            ),  # 0.389613
            (
                0.14,
                0.09,
                1.99,
                8,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                103,
            ),  # 1.038968
            (
                0.14,
                0.09,
                1.99,
                12,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                155,
            ),  # 1.558452
            (
                0.14,
                0.09,
                1.99,
                19,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                246,
            ),  # 2.467549
            (
                0.14,
                0.09,
                1.99,
                23,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                298,
            ),  # 2.987033
            (
                0.14,
                0.09,
                1.99,
                32,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                415,
            ),  # 4.155872
            (
                0.14,
                0.09,
                1.99,
                50,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                649,
            ),  # 6.49355
            (
                0.14,
                0.09,
                1.99,
                100,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1298,
            ),  # 12.9871
            (
                0.14,
                0.09,
                1.99,
                200,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                2597,
            ),  # 25.9742
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
                tariff = a_tariff(
                    price_kwh=price_kwh,
                    price_minute=price_minute,
                    price_session=price_session,
                    tax_rate=tax_rate,
                )
                checkout = a_checkout(
                    tariff_id=tariff.id,
                    transaction_kwh=kwh,
                    transaction_start_time=start_time,
                    transaction_end_time=end_time,
                )

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(pricing.tax_costs, expected_tax_costs)

    def test_pricing_has_total_costs_gross(self):
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
                1298,
            ),  # 12.9871
            (
                0.14,
                0.09,
                1.99,
                1,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1311,
            ),  # 13.116971
            (
                0.14,
                0.09,
                1.99,
                3,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1337,
            ),  # 13.376713
            (
                0.14,
                0.09,
                1.99,
                8,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1402,
            ),  # 14.026068
            (
                0.14,
                0.09,
                1.99,
                12,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1454,
            ),  # 14.545552
            (
                0.14,
                0.09,
                1.99,
                19,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1545,
            ),  # 15.454649
            (
                0.14,
                0.09,
                1.99,
                23,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1597,
            ),  # 15.974133
            (
                0.14,
                0.09,
                1.99,
                32,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1714,
            ),  # 17.142972
            (
                0.14,
                0.09,
                1.99,
                50,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                1948,
            ),  # 19.48065
            (
                0.14,
                0.09,
                1.99,
                100,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                2597,
            ),  # 25.9742
            (
                0.14,
                0.09,
                1.99,
                200,
                39.99,
                datetime(2024, 8, 15, 10, 0, 0),
                datetime(2024, 8, 15, 10, 59, 59),
                3896,
            ),  # 38.9613
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
                tariff = a_tariff(
                    price_kwh=price_kwh,
                    price_minute=price_minute,
                    price_session=price_session,
                    tax_rate=tax_rate,
                )
                checkout = a_checkout(
                    tariff_id=tariff.id,
                    transaction_kwh=kwh,
                    transaction_start_time=start_time,
                    transaction_end_time=end_time,
                )

                with model_data({Checkout: checkout, Tariff: tariff}):
                    pricing = generate_pricing(checkout.id)
                    self.assertEqual(
                        pricing.total_costs_gross, expected_total_costs_gross
                    )

    def test_payment_costs_tax_rate_is_zero(self):
        tariff = a_tariff()
        checkout = a_checkout(tariff_id=tariff.id)

        with model_data({Checkout: checkout, Tariff: tariff}):
            pricing = generate_pricing(checkout.id)
            self.assertEqual(pricing.payment_costs_tax_rate, 0)


@contextmanager
def model_data(data):
    with patch(
        "utils.utils.get_db",
        return_value=iter(
            [
                Mock(
                    query=Mock(
                        side_effect=lambda model: MagicMock(
                            filter=lambda expr: MagicMock(
                                first=lambda: data.get(model)
                                if data.get(model)
                                and expr.right.value == data[model].id
                                else None
                            )
                        )
                    )
                )
            ]
        ),
    ):
        yield


def a_checkout(**overrides) -> Checkout:
    defaults = {
        "id": 1,
        "payment_intent_id": 99,
        "authorization_amount": 0.99,
        "connector_id": 1,
        "tariff_id": 3,
        "qr_code_message_id": 5,
        "remote_request_status": "ACCEPTED",
        "remote_request_transaction_id": "7c4af61c-0f2d-4c90-8396-e479acc0beca",
        "transaction_start_time": datetime(2023, 8, 14, 10, 00, 00),
        "transaction_end_time": datetime(2023, 8, 14, 10, 30, 59),
        "transaction_last_meter_reading": 31.74,
        "transaction_kwh": 31.74,
        "power_active_import": 31.74,
        "transaction_soc": 15,
    }
    defaults.update(overrides)

    return Checkout(**defaults)


def a_tariff(**overrides) -> Tariff:
    defaults = {
        "id": 3,
        "price_kwh": 0.30,
        "price_minute": 0.05,
        "price_session": 3.00,
        "currency": "USD",
        "tax_rate": 23,
        "authorization_amount": 10.00,
        "payment_fee": 1,
        "stripe_price_id": "price_b30e584f5822",
    }
    defaults.update(overrides)

    return Tariff(**defaults)


if __name__ == "__main__":
    unittest.main()
