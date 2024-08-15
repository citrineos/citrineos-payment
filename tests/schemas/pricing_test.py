import unittest

from schemas.checkouts import Pricing


class PricingTests(unittest.TestCase):  # TODO: negative costs scenarios?

    def test_total_costs_net(self):
        for pricing, expected_total_costs_net in [
            (a_pricing(energy_costs=0, time_costs=0, session_costs=0), 0),

            (a_pricing(energy_costs=1494, time_costs=0, session_costs=0), 1494),
            (a_pricing(energy_costs=0, time_costs=891, session_costs=0), 891),
            (a_pricing(energy_costs=0, time_costs=0, session_costs=100), 100),

            (a_pricing(energy_costs=1494, time_costs=891, session_costs=0), 2385),
            (a_pricing(energy_costs=1494, time_costs=0, session_costs=299), 1793),
            (a_pricing(energy_costs=0, time_costs=891, session_costs=299), 1190),

            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100), 2485),
            (a_pricing(energy_costs=2999, time_costs=1264, session_costs=299), 4562),
            (a_pricing(energy_costs=10341, time_costs=11841, session_costs=987), 23169),
        ]:
            with self.subTest(
                    energy_costs=pricing.energy_costs, time_costs=pricing.time_costs,
                    session_costs=pricing.session_costs, expected_total_costs_net=expected_total_costs_net):
                self.assertEqual(pricing.total_costs_net, expected_total_costs_net)

    def test_tax_costs(self):
        for pricing, expected_tax_costs in [
            (a_pricing(energy_costs=0, time_costs=0, session_costs=0, tax_rate=23), 0),  # 0

            (a_pricing(energy_costs=1494, time_costs=0, session_costs=0, tax_rate=23), 343),  # 3.4362
            (a_pricing(energy_costs=0, time_costs=891, session_costs=0, tax_rate=23), 204),  # 2.0493
            (a_pricing(energy_costs=0, time_costs=0, session_costs=100, tax_rate=23), 23),  # 0.23

            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=0), 0),  # 0
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=8), 198),  # 1.988
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=23), 571),  # 5.7155
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=50), 1242),  # 12.425
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=100), 2485),  # 24.85
        ]:
            with self.subTest(
                    energy_costs=pricing.energy_costs, time_costs=pricing.time_costs,
                    session_costs=pricing.session_costs, tax_rate=pricing.tax_rate, expected_tax_costs=expected_tax_costs):
                self.assertEqual(pricing.tax_costs, expected_tax_costs)

    def test_total_costs_gross(self):
        for pricing, expected_total_costs_gross in [
            (a_pricing(energy_costs=0, time_costs=0, session_costs=0, tax_rate=23), 0),  # 0

            (a_pricing(energy_costs=1494, time_costs=0, session_costs=0, tax_rate=23), 1837),  # 18.3762
            (a_pricing(energy_costs=0, time_costs=891, session_costs=0, tax_rate=23), 1095),  # 10.9593
            (a_pricing(energy_costs=0, time_costs=0, session_costs=100, tax_rate=23), 123),  # 1.23

            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=0), 2485),  # 24.85
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=8), 2683),  # 26.838
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=23), 3056),  # 30.5655
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=50), 3727),  # 37.275
            (a_pricing(energy_costs=1494, time_costs=891, session_costs=100, tax_rate=100), 4970),  # 49.70
        ]:
            with self.subTest(
                    energy_costs=pricing.energy_costs, time_costs=pricing.time_costs,
                    session_costs=pricing.session_costs, tax_rate=pricing.tax_rate, expected_total_costs_gross=expected_total_costs_gross):
                self.assertEqual(pricing.total_costs_gross, expected_total_costs_gross)


def a_pricing(**overrides) -> Pricing:
    defaults = {
        'currency': "USD",
        'tax_rate': 23,
        'payment_fee': 50,
        'energy_consumption_kwh': 39.99,
        'energy_costs': 2658,
        'time_consumption_min': 32.46,
        'time_costs': 1351,
        'session_consumption': 1,
        'session_costs': 500,
        'payment_costs_tax_rate': 0,
    }

    defaults.update(overrides)

    return Pricing(**defaults)


if __name__ == '__main__':
    unittest.main()
