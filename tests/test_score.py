"""Unit tests for the pure functions of score.py (no network, no data files).

Run from the repository root:  python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import score  # importing only reads ville.json, it downloads nothing

UTC = timezone.utc
PARIS = ZoneInfo('Europe/Paris')
GRENOBLE = {'LAT': 45.2115, 'LON': 5.682833}  # same values as ville.json, pinned so the tests ignore $VILLE


def at(y, m, d, h=0, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=UTC)


class SunTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.multiple(score, PARIS=PARIS, **GRENOBLE)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_elevation_at_midnight_is_below_horizon(self):
        self.assertLess(score.sun_elevation(at(2025, 6, 21, 0)), 0)
        self.assertLess(score.sun_elevation(at(2025, 12, 21, 0)), 0)

    def test_elevation_at_noon_matches_geometry(self):
        # Solar noon elevation = 90 - latitude + declination (about +-23.44 at the solstices):
        # 90 - 45.21 + 23.44 = 68.2 in June, 90 - 45.21 - 23.44 = 21.3 in December. Solar noon in
        # Grenoble (5.68 E) is close to 12:00 UTC (about 11:37 + equation of time), hence a 2 degree margin.
        self.assertAlmostEqual(score.sun_elevation(at(2025, 6, 21, 12)), 68.2, delta=2)
        self.assertAlmostEqual(score.sun_elevation(at(2025, 12, 21, 12)), 21.3, delta=2)

    def test_summer_noon_is_higher_than_winter_noon(self):
        self.assertGreater(score.sun_elevation(at(2025, 6, 21, 12)), score.sun_elevation(at(2025, 12, 21, 12)))

    def test_clear_sky_is_zero_at_night(self):
        for t in (at(2025, 6, 21, 0), at(2025, 12, 21, 0), at(2025, 12, 21, 18)):
            power, elevation = score.clear_sky(t)
            self.assertEqual(power, 0)
            self.assertLess(elevation, 0)

    def test_clear_sky_summer_noon_is_higher_than_winter_noon(self):
        summer, summer_elev = score.clear_sky(at(2025, 6, 21, 12))
        winter, winter_elev = score.clear_sky(at(2025, 12, 21, 12))
        self.assertGreater(summer, winter)
        self.assertGreater(summer_elev, winter_elev)
        # Haurwitz at 68 degrees is about 950 W/m2, at 21 degrees about 340 W/m2
        self.assertTrue(900 < summer < 1000, summer)
        self.assertTrue(300 < winter < 380, winter)

    def test_clear_sky_elevation_is_taken_at_mid_hour(self):
        # the hour "ending at t" is centred on t - 30 min
        _, elevation = score.clear_sky(at(2025, 6, 21, 12))
        self.assertEqual(elevation, score.sun_elevation(at(2025, 6, 21, 11, 30)))


class CategoryTests(unittest.TestCase):
    # codes: 0 sun, 1 mixed, 2 overcast, 3 rain (see score.CATS)
    def test_rain_threshold_edges(self):
        thr = score.RAIN_HOUR  # 0.2 mm
        self.assertEqual(score.category(thr, 1.0, thr), 3)        # at the threshold: rain
        self.assertEqual(score.category(thr - 0.01, 1.0, thr), 0)  # just under: dry, sunny
        self.assertEqual(score.category(0, 1.0, thr), 0)

    def test_rain_wins_over_sun(self):
        self.assertEqual(score.category(5, 1.0, score.RAIN_HOUR), 3)

    def test_sun_threshold_edges(self):
        self.assertEqual(score.category(0, score.SUN, 0.2), 0)        # 0.75: sun
        self.assertEqual(score.category(0, score.SUN - 0.01, 0.2), 1)  # just under: mixed

    def test_mixed_threshold_edges(self):
        self.assertEqual(score.category(0, score.MIXED, 0.2), 1)         # 0.4: mixed
        self.assertEqual(score.category(0, score.MIXED - 0.01, 0.2), 2)  # just under: overcast
        self.assertEqual(score.category(0, 0, 0.2), 2)

    def test_threshold_is_a_parameter(self):
        # 0.3 mm is rain for an hourly threshold of 0.2 but dry for a half-day threshold of 0.5
        self.assertEqual(score.category(0.3, 1.0, score.RAIN_HOUR), 3)
        self.assertEqual(score.category(0.3, 1.0, score.RAIN_BLOCK), 0)

    def test_missing_values_are_not_scored(self):
        self.assertIsNone(score.category(0, None, 0.2))     # night: no sunlight value
        self.assertIsNone(score.category(None, 1.0, 0.2))   # no rain value
        self.assertIsNone(score.category(None, None, 0.2))


class CloudRatioTests(unittest.TestCase):
    def test_none_stays_none(self):
        self.assertIsNone(score.cloud_ratio(None))

    def test_clear_sky(self):
        self.assertEqual(score.cloud_ratio(0), 1)  # 1 - 0.75 * 0 = 1

    def test_full_overcast(self):
        self.assertAlmostEqual(score.cloud_ratio(100), 0.25)  # 1 - 0.75 * 1 = 0.25

    def test_half_cover(self):
        # 1 - 0.75 * 0.5 ** 3.4 = 1 - 0.75 * 0.0947 = 0.929
        self.assertAlmostEqual(score.cloud_ratio(50), 0.929, places=3)

    def test_decreases_with_cloud_cover(self):
        values = [score.cloud_ratio(c) for c in range(0, 101, 10)]
        self.assertEqual(values, sorted(values, reverse=True))


class ToSlotsTests(unittest.TestCase):
    def test_hour_is_spread_over_three_slots(self):
        # 6 mm in the hour ending 10:00 = 0.1 mm/min = 2 mm per 20-min slot (9:00, 9:20, 9:40)
        slots = score.to_slots({at(2025, 1, 1, 10): 6.0}, 60)
        self.assertEqual(set(slots), {at(2025, 1, 1, 9), at(2025, 1, 1, 9, 20), at(2025, 1, 1, 9, 40)})
        for value in slots.values():
            self.assertAlmostEqual(value, 2.0)

    def test_total_is_conserved(self):
        slots = score.to_slots({at(2025, 1, 1, 10): 1.5, at(2025, 1, 1, 11): 0.3}, 60)
        self.assertAlmostEqual(sum(slots.values()), 1.8)

    def test_short_interval_lands_in_one_slot(self):
        # the 10 minutes ending 10:10 are 10:00..10:09, all in the 10:00 slot
        slots = score.to_slots({at(2025, 1, 1, 10, 10): 1.0}, 10)
        self.assertEqual(list(slots), [at(2025, 1, 1, 10)])
        self.assertAlmostEqual(slots[at(2025, 1, 1, 10)], 1.0)

    def test_interval_straddling_two_slots(self):
        # the 10 minutes ending 10:25 are 10:15..10:24: 5 minutes in slot 10:00, 5 in slot 10:20
        slots = score.to_slots({at(2025, 1, 1, 10, 25): 1.0}, 10)
        self.assertAlmostEqual(slots[at(2025, 1, 1, 10)], 0.5)
        self.assertAlmostEqual(slots[at(2025, 1, 1, 10, 20)], 0.5)

    def test_overlapping_amounts_add_up(self):
        slots = score.to_slots({at(2025, 1, 1, 10, 10): 1.0, at(2025, 1, 1, 10, 20): 2.0}, 10)
        self.assertAlmostEqual(slots[at(2025, 1, 1, 10)], 3.0)

    def test_none_is_skipped_and_empty_gives_empty(self):
        self.assertEqual(score.to_slots({at(2025, 1, 1, 10): None}, 60), {})
        self.assertEqual(score.to_slots({}, 60), {})


def hour(**kw):
    base = {'temperature': 10.0, 'humidite': 50.0, 'vent': 2.0, 'rafales': 5.0, 'direction': 180.0,
            'pression': 1015.0, 'pluie_mm': 0.0, 'ratio': 0.8, 'cat': 0}
    base.update(kw)
    return base


def local_hours(day, first, last, **kw):
    """Hours ending at local 'first'..'last' on a Paris date, keyed by UTC time like the forecasts."""
    out = {}
    for h in range(first, last + 1):
        t = datetime(day.year, day.month, day.day, h, tzinfo=PARIS).astimezone(UTC)
        out[t] = hour(**kw)
    return out


class ToBlocksTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(score, 'PARIS', PARIS)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.day = datetime(2025, 1, 15).date()

    def test_morning_and_afternoon_blocks(self):
        hours = {**local_hours(self.day, 7, 12), **local_hours(self.day, 13, 18)}
        blocks = score.to_blocks(hours)
        self.assertEqual(set(blocks), {(self.day, 'matin'), (self.day, 'aprem')})

    def test_hours_outside_blocks_are_ignored(self):
        # 19h..23h belong to no block; 7-12 only has 6 hours so it still makes a block
        hours = {**local_hours(self.day, 7, 12), **local_hours(self.day, 19, 23)}
        self.assertEqual(set(score.to_blocks(hours)), {(self.day, 'matin')})

    def test_summer_time_is_taken_into_account(self):
        # in July Paris is UTC+2: local 7h is 5h UTC. Blocks follow local time, not UTC.
        day = datetime(2025, 7, 15).date()
        blocks = score.to_blocks(local_hours(day, 7, 12))
        self.assertEqual(set(blocks), {(day, 'matin')})

    def test_incomplete_block_is_dropped(self):
        hours = local_hours(self.day, 7, 11)  # 5 hours only
        self.assertEqual(score.to_blocks(hours), {})

    def test_means_sum_and_max(self):
        hours = local_hours(self.day, 7, 12)
        keys = sorted(hours)
        for i, t in enumerate(keys):
            # temperatures 10..15 (mean 12.5), 0.1 mm each (sum 0.6), gusts 5..10 (max 10), wind 1..6 (mean 3.5)
            hours[t] = hour(temperature=10.0 + i, pluie_mm=0.1, rafales=5.0 + i, vent=1.0 + i,
                            direction=float(100 + i), ratio=0.5)
        b = score.to_blocks(hours)[(self.day, 'matin')]
        self.assertAlmostEqual(b['temperature'], 12.5)
        self.assertAlmostEqual(b['pluie_mm'], 0.6)
        self.assertEqual(b['rafales'], 10.0)
        self.assertAlmostEqual(b['vent'], 3.5)
        self.assertEqual(b['direction'], 103.0)  # the 4th hour (index 3) is used as is
        self.assertAlmostEqual(b['ratio'], 0.5)
        # 0.6 mm >= RAIN_BLOCK (0.5): rain
        self.assertEqual(b['cat'], 3)

    def test_dry_block_category_uses_ratio(self):
        b = score.to_blocks(local_hours(self.day, 7, 12, ratio=0.9))[(self.day, 'matin')]
        self.assertEqual(b['cat'], 0)

    def test_block_rain_threshold_differs_from_hourly(self):
        # 6 x 0.06 mm = 0.36 mm: each hour is dry-ish, the block is below RAIN_BLOCK (0.5) so not rain
        b = score.to_blocks(local_hours(self.day, 7, 12, pluie_mm=0.06))[(self.day, 'matin')]
        self.assertAlmostEqual(b['pluie_mm'], 0.36)
        self.assertNotEqual(b['cat'], 3)

    def test_missing_value_makes_that_component_none(self):
        hours = local_hours(self.day, 7, 12)
        first = sorted(hours)[0]
        hours[first] = hour(temperature=None, pluie_mm=None, rafales=None)
        b = score.to_blocks(hours)[(self.day, 'matin')]
        self.assertIsNone(b['temperature'])
        self.assertIsNone(b['pluie_mm'])
        self.assertIsNone(b['rafales'])
        self.assertIsNone(b['cat'])  # no rain total: condition not scored

    def test_ratio_needs_two_values(self):
        hours = local_hours(self.day, 7, 12, ratio=None)
        for t in sorted(hours)[:1]:
            hours[t] = hour(ratio=0.8)
        self.assertIsNone(score.to_blocks(hours)[(self.day, 'matin')]['ratio'])  # only one hour has a ratio
        for t in sorted(hours)[:2]:
            hours[t] = hour(ratio=0.8)
        self.assertAlmostEqual(score.to_blocks(hours)[(self.day, 'matin')]['ratio'], 0.8)


def series(n, forecast, observed):
    """n hourly entries starting 2025-01-01 00:00 UTC, as (forecast dict, observation dict)."""
    t0 = at(2025, 1, 1)
    fc = {t0 + timedelta(hours=i): dict(forecast) for i in range(n)}
    obs = {t0 + timedelta(hours=i): dict(observed) for i in range(n)}
    return fc, obs


class CompareTests(unittest.TestCase):
    # compare() only scores a parameter with more than 50 pairs, and the condition with more than 100
    N = 120

    def test_perfect_forecast_scores_100(self):
        fc, obs = series(self.N, hour(), hour())
        s, mae, conf, n = score.compare(fc, obs, score.TOL_HOUR)
        self.assertEqual(s['condition'], 100)
        self.assertEqual(s['temperature'], 100)
        self.assertEqual(mae['temperature'], 0)
        self.assertEqual(conf, {(0, 0): self.N})
        self.assertEqual(n, self.N)

    def test_error_within_tolerance_gives_partial_score(self):
        # temperature error 1.5 for a tolerance of 3: 100 * (1 - 1.5 / 3) = 50
        fc, obs = series(self.N, hour(temperature=11.5), hour(temperature=10.0))
        s, mae, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertAlmostEqual(s['temperature'], 50)
        self.assertAlmostEqual(mae['temperature'], 1.5)

    def test_error_outside_tolerance_is_floored_at_zero(self):
        fc, obs = series(self.N, hour(temperature=20.0), hour(temperature=10.0))  # error 10 > 3
        s, mae, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertEqual(s['temperature'], 0)
        self.assertAlmostEqual(mae['temperature'], 10)  # the raw error is kept

    def test_missing_values_are_skipped(self):
        fc, obs = series(self.N, hour(), hour())
        for t in list(fc)[:80]:
            fc[t]['temperature'] = None  # leaves 40 pairs: not enough to score
        s, mae, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertNotIn('temperature', s)
        self.assertNotIn('temperature', mae)
        self.assertIn('humidite', s)  # other parameters are unaffected

    def test_missing_forecast_time_is_skipped(self):
        fc, obs = series(self.N, hour(), hour())
        for t in list(fc)[:self.N - 40]:
            del fc[t]  # 40 observations without any forecast
        s, _, conf, n = score.compare(fc, obs, score.TOL_HOUR)
        self.assertEqual(n, 40)
        self.assertEqual(sum(conf.values()), 40)
        self.assertEqual(s, {})  # too few pairs for anything

    def test_not_enough_pairs_for_condition(self):
        fc, obs = series(100, hour(), hour())  # needs strictly more than 100
        s, _, _, n = score.compare(fc, obs, score.TOL_HOUR)
        self.assertNotIn('condition', s)
        self.assertEqual(n, 100)
        self.assertIn('temperature', s)  # 100 > 50

    def test_missing_category_is_not_counted(self):
        fc, obs = series(self.N, hour(cat=None), hour())
        s, _, conf, n = score.compare(fc, obs, score.TOL_HOUR)
        self.assertEqual((n, conf), (0, {}))
        self.assertNotIn('condition', s)

    def test_condition_partial_credit(self):
        # forecast sun (0), observed mixed (1): CREDIT[(0, 1)] = 0.5
        fc, obs = series(self.N, hour(cat=0), hour(cat=1))
        s, _, conf, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertEqual(s['condition'], 50)
        self.assertEqual(conf, {(0, 1): self.N})

    def test_condition_no_credit_when_far_apart(self):
        # forecast sun (0), observed rain (3): not in CREDIT
        fc, obs = series(self.N, hour(cat=0), hour(cat=3))
        s, _, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertEqual(s['condition'], 0)

    def test_direction_wraps_around_north(self):
        # 350 vs 10 degrees is a 20 degree error, not 340: 100 * (1 - 20 / 90)
        fc, obs = series(self.N, hour(direction=350.0), hour(direction=10.0))
        s, mae, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertAlmostEqual(mae['direction'], 20)
        self.assertAlmostEqual(s['direction'], 100 * (1 - 20 / 90))

    def test_direction_ignored_in_calm_air(self):
        fc, obs = series(self.N, hour(direction=0.0), hour(direction=180.0, vent=1.0))  # observed wind < 2
        s, _, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertNotIn('direction', s)

    def test_rain_amount_only_scored_when_it_rained(self):
        # first 60 hours dry on both sides (ignored); the next 60: forecast 1.0 mm, observed 0.0 mm
        fc, obs = series(self.N, hour(pluie_mm=0.0), hour(pluie_mm=0.0))
        for t in list(fc)[60:]:
            fc[t]['pluie_mm'] = 1.0
        s, mae, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertAlmostEqual(mae['pluie_mm'], 1.0)  # mean over the 60 forecast-rain hours only
        self.assertAlmostEqual(s['pluie_mm'], 100 * (1 - 1.0 / 2))  # tolerance 2 mm

    def test_dry_everywhere_gives_no_rain_score(self):
        fc, obs = series(self.N, hour(pluie_mm=0.05), hour(pluie_mm=0.0))  # both below 0.1 mm
        s, _, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        self.assertNotIn('pluie_mm', s)

    def test_block_tolerance_for_rain_is_larger(self):
        fc, obs = series(self.N, hour(pluie_mm=2.0), hour(pluie_mm=0.0))
        hourly, _, _, _ = score.compare(fc, obs, score.TOL_HOUR)
        block, _, _, _ = score.compare(fc, obs, score.TOL_BLOCK)
        self.assertEqual(hourly['pluie_mm'], 0)                 # error 2 = tolerance 2
        self.assertAlmostEqual(block['pluie_mm'], 60)           # 100 * (1 - 2 / 5)


class TotalTests(unittest.TestCase):
    def test_all_components_equal(self):
        s = {k: 80.0 for k in score.WEIGHTS}
        self.assertAlmostEqual(score.total(s), 80.0)

    def test_weighted_average(self):
        # condition 60 + temperature 7: (100 * 60 + 0 * 7) / 67
        self.assertAlmostEqual(score.total({'condition': 100, 'temperature': 0}), 6000 / 67)

    def test_missing_components_renormalise_weights(self):
        self.assertAlmostEqual(score.total({'condition': 70}), 70.0)

    def test_without_condition_there_is_no_total(self):
        self.assertIsNone(score.total({'temperature': 90, 'vent': 90}))
        self.assertIsNone(score.total({}))

    def test_unknown_components_are_ignored(self):
        self.assertAlmostEqual(score.total({'condition': 50, 'bogus': 0}), 50.0)

    def test_weights_sum_to_100(self):
        self.assertEqual(sum(score.WEIGHTS.values()), 100)


class ExactRatesTests(unittest.TestCase):
    def test_perfect(self):
        exact, sun, overcast, rain = score.exact_rates({(0, 0): 4, (2, 2): 3, (3, 3): 3})
        self.assertEqual((exact, sun, overcast, rain), (100, 100, 100, 100))

    def test_mixed_confusion(self):
        # keys are (forecast, observed). 10 cases, 6 exact (60 %).
        # observed sun: 5 (3 right) = 60 %, observed overcast: 3 (2 right) = 66.7 %, observed rain: 2 (1 right) = 50 %
        conf = {(0, 0): 3, (1, 0): 2, (2, 2): 2, (0, 2): 1, (3, 3): 1, (2, 3): 1}
        exact, sun, overcast, rain = score.exact_rates(conf)
        self.assertAlmostEqual(exact, 60.0)  # exact: (0,0) 3 + (2,2) 2 + (3,3) 1 = 6 out of 10
        self.assertAlmostEqual(sun, 60.0)
        self.assertAlmostEqual(overcast, 2 / 3 * 100)
        self.assertAlmostEqual(rain, 50.0)

    def test_category_never_observed_scores_zero(self):
        exact, sun, overcast, rain = score.exact_rates({(0, 0): 5})
        self.assertEqual((exact, sun, overcast, rain), (100, 100, 0, 0))

    def test_mixed_category_does_not_count_in_hit_rates(self):
        # only sun, overcast and rain have their own rate; mixed (1) counts in the exact rate only
        exact, sun, overcast, rain = score.exact_rates({(1, 1): 2, (0, 0): 2})
        self.assertEqual(exact, 100)
        self.assertEqual((sun, overcast, rain), (100, 0, 0))


if __name__ == '__main__':
    unittest.main()
