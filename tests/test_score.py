"""Unit tests for the pure functions of score.py.

No network and no file is read except ville.json (loaded by score.py at import). Every fixture is built inline;
expected values are worked out by hand in the comments.
Run from the repository root: python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import score  # noqa: E402  (needs the repository root on sys.path)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class SunTest(unittest.TestCase):
    # Grenoble: latitude 45.21°. At solar noon the elevation is 90 - lat + declination:
    # June solstice (declination +23.44°) -> about 68.2°, December solstice (-23.44°) -> about 21.3°.
    # 12:00 UTC is within half an hour of Grenoble's solar noon (about 11:37 UTC), so allow 1 degree.

    def test_elevation_at_summer_noon(self):
        self.assertAlmostEqual(score.sun_elevation(utc(2025, 6, 21, 12, 0)), 68.2, delta=1.0)

    def test_elevation_at_winter_noon(self):
        self.assertAlmostEqual(score.sun_elevation(utc(2025, 12, 21, 12, 0)), 21.3, delta=1.0)

    def test_elevation_at_midnight_is_negative(self):
        # Solar midnight in June: lat + declination - 90 = 45.21 + 23.44 - 90 = -21.35°
        self.assertAlmostEqual(score.sun_elevation(utc(2025, 6, 21, 0, 0)), -21.35, delta=1.0)

    def test_elevation_is_a_valid_angle(self):
        for hour in range(24):
            e = score.sun_elevation(utc(2025, 3, 20, hour, 0))
            self.assertTrue(-90 <= e <= 90)

    def test_clear_sky_is_zero_at_night(self):
        for t in (utc(2025, 6, 21, 0, 0), utc(2025, 12, 21, 2, 0), utc(2025, 12, 21, 22, 0)):
            irradiance, elevation = score.clear_sky(t)
            self.assertEqual(irradiance, 0)
            self.assertLess(elevation, 0)

    def test_clear_sky_noon_summer_is_higher_than_noon_winter(self):
        summer, summer_elev = score.clear_sky(utc(2025, 6, 21, 12, 0))
        winter, winter_elev = score.clear_sky(utc(2025, 12, 21, 12, 0))
        self.assertGreater(summer, winter)
        self.assertGreater(summer_elev, winter_elev)

    def test_clear_sky_noon_values_are_plausible(self):
        # Haurwitz never exceeds its 1098 W/m² constant; a high summer sun gives most of it, a low winter sun much less.
        summer, _ = score.clear_sky(utc(2025, 6, 21, 12, 0))
        winter, _ = score.clear_sky(utc(2025, 12, 21, 12, 0))
        self.assertTrue(800 < summer < 1098)
        self.assertTrue(200 < winter < 450)

    def test_clear_sky_returns_elevation_at_mid_hour(self):
        t = utc(2025, 6, 21, 12, 0)
        _, elevation = score.clear_sky(t)
        self.assertAlmostEqual(elevation, score.sun_elevation(t - timedelta(minutes=30)))


class CategoryTest(unittest.TestCase):
    # Thresholds: rain from `rain_thr` mm up; sun from ratio 0.75; mixed from ratio 0.4; below is overcast.
    # Codes: 0 sun, 1 mixed, 2 overcast, 3 rain.

    def test_dry_sun(self):
        self.assertEqual(score.category(0, 1.0, score.RAIN_HOUR), 0)

    def test_dry_mixed(self):
        self.assertEqual(score.category(0, 0.5, score.RAIN_HOUR), 1)

    def test_dry_overcast(self):
        self.assertEqual(score.category(0, 0.1, score.RAIN_HOUR), 2)

    def test_rain_at_threshold_counts_as_rain(self):
        self.assertEqual(score.category(score.RAIN_HOUR, 1.0, score.RAIN_HOUR), 3)

    def test_rain_just_below_threshold_is_dry(self):
        self.assertEqual(score.category(score.RAIN_HOUR - 0.01, 1.0, score.RAIN_HOUR), 0)

    def test_threshold_depends_on_the_scale(self):
        # 0.3 mm is rain for an hour (0.2) but dry for a half-day block (0.5)
        self.assertEqual(score.category(0.3, 1.0, score.RAIN_HOUR), 3)
        self.assertEqual(score.category(0.3, 1.0, score.RAIN_BLOCK), 0)

    def test_rain_wins_over_sun(self):
        self.assertEqual(score.category(5, 1.0, score.RAIN_HOUR), 3)
        self.assertEqual(score.category(5, 0.0, score.RAIN_HOUR), 3)

    def test_sun_edge(self):
        self.assertEqual(score.category(0, score.SUN, score.RAIN_HOUR), 0)
        self.assertEqual(score.category(0, score.SUN - 0.001, score.RAIN_HOUR), 1)

    def test_mixed_edge(self):
        self.assertEqual(score.category(0, score.MIXED, score.RAIN_HOUR), 1)
        self.assertEqual(score.category(0, score.MIXED - 0.001, score.RAIN_HOUR), 2)

    def test_missing_sunlight_means_not_scored(self):
        self.assertIsNone(score.category(0, None, score.RAIN_HOUR))
        self.assertIsNone(score.category(5, None, score.RAIN_HOUR))  # rain is not scored at night either

    def test_missing_rain_means_not_scored(self):
        self.assertIsNone(score.category(None, 1.0, score.RAIN_HOUR))


class CloudRatioTest(unittest.TestCase):
    # ratio = 1 - 0.75 * (cc/100) ** 3.4

    def test_clear_sky(self):
        self.assertEqual(score.cloud_ratio(0), 1.0)

    def test_full_overcast_keeps_a_quarter_of_the_sunlight(self):
        self.assertAlmostEqual(score.cloud_ratio(100), 0.25)

    def test_half_cover(self):
        self.assertAlmostEqual(score.cloud_ratio(50), 1 - 0.75 * 0.5 ** 3.4)

    def test_missing_value(self):
        self.assertIsNone(score.cloud_ratio(None))

    def test_more_cloud_means_less_sunlight(self):
        values = [score.cloud_ratio(cc) for cc in range(0, 101, 10)]
        self.assertEqual(values, sorted(values, reverse=True))


class ToSlotsTest(unittest.TestCase):
    def test_hourly_amount_is_spread_over_three_slots(self):
        # 6 mm in the hour ending 10:00 -> 0.1 mm/min -> 2 mm in each of the slots 09:00, 09:20 and 09:40
        slots = score.to_slots({utc(2025, 1, 1, 10, 0): 6.0}, 60)
        self.assertEqual(set(slots), {utc(2025, 1, 1, 9, 0), utc(2025, 1, 1, 9, 20), utc(2025, 1, 1, 9, 40)})
        for value in slots.values():
            self.assertAlmostEqual(value, 2.0)

    def test_quarter_hour_amount_stays_in_one_slot(self):
        # 3 mm in the quarter hour ending 10:15 covers 10:00-10:14, entirely inside the slot 10:00
        slots = score.to_slots({utc(2025, 1, 1, 10, 15): 3.0}, 15)
        self.assertEqual(list(slots), [utc(2025, 1, 1, 10, 0)])
        self.assertAlmostEqual(slots[utc(2025, 1, 1, 10, 0)], 3.0)

    def test_quarter_hour_straddling_two_slots(self):
        # The quarter hour ending 10:25 covers 10:10-10:24: 10 minutes in slot 10:00, 5 in slot 10:20
        slots = score.to_slots({utc(2025, 1, 1, 10, 25): 3.0}, 15)
        self.assertAlmostEqual(slots[utc(2025, 1, 1, 10, 0)], 2.0)
        self.assertAlmostEqual(slots[utc(2025, 1, 1, 10, 20)], 1.0)

    def test_amounts_add_up_in_a_shared_slot(self):
        slots = score.to_slots({utc(2025, 1, 1, 10, 15): 3.0, utc(2025, 1, 1, 10, 20): 1.0}, 15)
        # second interval covers 10:05-10:19, also entirely inside slot 10:00
        self.assertAlmostEqual(slots[utc(2025, 1, 1, 10, 0)], 4.0)

    def test_total_rain_is_conserved(self):
        amounts = {utc(2025, 1, 1, 10, 0): 1.2, utc(2025, 1, 1, 11, 0): 0.0, utc(2025, 1, 1, 12, 0): 4.5}
        self.assertAlmostEqual(sum(score.to_slots(amounts, 60).values()), 5.7)

    def test_missing_amounts_are_skipped(self):
        self.assertEqual(score.to_slots({utc(2025, 1, 1, 10, 0): None}, 60), {})

    def test_empty_input(self):
        self.assertEqual(score.to_slots({}, 60), {})


def hour(temp=10.0, rain=0.0, ratio=1.0, gust=5.0, direction=180.0, wind=2.0, humidity=50.0, pressure=1015.0, cat=None):
    return {'temperature': temp, 'humidite': humidity, 'vent': wind, 'rafales': gust, 'direction': direction,
            'pression': pressure, 'pluie_mm': rain, 'ratio': ratio, 'cat': cat}


class ToBlocksTest(unittest.TestCase):
    # Europe/Paris is UTC+1 in January. Hour keys are the END of the hour: the morning block holds the hours ending
    # 7:00-12:00 local (06-11 UTC), the afternoon block the hours ending 13:00-18:00 local (12-17 UTC).
    DAY = (2025, 1, 15)

    def hours(self, utc_hours, **kw):
        return {utc(*self.DAY, h): hour(**kw) for h in utc_hours}

    def test_full_day_gives_two_blocks(self):
        blocks = score.to_blocks(self.hours(range(0, 24)))
        local_day = datetime(*self.DAY).date()
        self.assertEqual(set(blocks), {(local_day, 'matin'), (local_day, 'aprem')})

    def test_hours_outside_the_blocks_are_ignored(self):
        # Local 06:00 (05 UTC) and 19:00 (18 UTC) belong to no block: a complete morning stays alone and unchanged
        day = datetime(*self.DAY).date()
        blocks = score.to_blocks(self.hours([5, 6, 7, 8, 9, 10, 11, 18], temp=10.0))
        self.assertEqual(set(blocks), {(day, 'matin')})
        self.assertAlmostEqual(blocks[(day, 'matin')]['temperature'], 10.0)

    def test_incomplete_block_is_dropped(self):
        h = self.hours(range(6, 12))
        del h[utc(*self.DAY, 9)]
        self.assertEqual(score.to_blocks(h), {})

    def test_block_aggregation(self):
        day = datetime(*self.DAY).date()
        hs = {}
        for i, h in enumerate(range(6, 12)):  # morning, i = 0..5
            hs[utc(*self.DAY, h)] = hour(temp=10 + i, rain=0.1, ratio=0.8, gust=5 + i, direction=100 + i * 10,
                                         wind=2 + i, humidity=40 + i, pressure=1010 + i)
        b = score.to_blocks(hs)[(day, 'matin')]
        self.assertAlmostEqual(b['temperature'], 12.5)   # mean of 10..15
        self.assertAlmostEqual(b['humidite'], 42.5)      # mean of 40..45
        self.assertAlmostEqual(b['vent'], 4.5)           # mean of 2..7
        self.assertAlmostEqual(b['pression'], 1012.5)    # mean of 1010..1015
        self.assertAlmostEqual(b['pluie_mm'], 0.6)       # rain is summed: 6 x 0.1
        self.assertEqual(b['rafales'], 10)               # gusts: the maximum of 5..10
        self.assertEqual(b['direction'], 130)            # direction: the 4th hour (index 3) = 100 + 30
        self.assertAlmostEqual(b['ratio'], 0.8)
        self.assertEqual(b['cat'], 3)                    # 0.6 mm >= 0.5 mm block threshold: rain

    def test_rain_block_threshold_edge(self):
        day = datetime(*self.DAY).date()
        # 6 x 0.08 = 0.48 mm < 0.5 -> dry; with sun ratio 0.8 -> sun (0)
        dry = score.to_blocks(self.hours(range(6, 12), rain=0.08, ratio=0.8))[(day, 'matin')]
        self.assertAlmostEqual(dry['pluie_mm'], 0.48)
        self.assertEqual(dry['cat'], 0)
        # 6 x 0.1 = 0.6 mm >= 0.5 -> rain (3)
        wet = score.to_blocks(self.hours(range(6, 12), rain=0.1, ratio=0.8))[(day, 'matin')]
        self.assertEqual(wet['cat'], 3)

    def test_afternoon_block(self):
        day = datetime(*self.DAY).date()
        b = score.to_blocks(self.hours(range(12, 18), temp=20.0))
        self.assertEqual(set(b), {(day, 'aprem')})
        self.assertAlmostEqual(b[(day, 'aprem')]['temperature'], 20.0)

    def test_summer_time_shifts_the_blocks(self):
        # In July Paris is UTC+2: the morning hours ending 7-12 local are 05-10 UTC
        day = datetime(2025, 7, 15).date()
        hs = {utc(2025, 7, 15, h): hour() for h in range(5, 11)}
        self.assertEqual(set(score.to_blocks(hs)), {(day, 'matin')})
        # The same UTC hours in January would be local 6-11: the 6:00 hour is outside, so incomplete
        hs_winter = {utc(2025, 1, 15, h): hour() for h in range(5, 11)}
        self.assertEqual(score.to_blocks(hs_winter), {})

    def test_missing_value_makes_that_parameter_missing(self):
        day = datetime(*self.DAY).date()
        hs = self.hours(range(6, 12))
        hs[utc(*self.DAY, 8)]['temperature'] = None
        hs[utc(*self.DAY, 8)]['rafales'] = None
        b = score.to_blocks(hs)[(day, 'matin')]
        self.assertIsNone(b['temperature'])
        self.assertIsNone(b['rafales'])
        self.assertIsNotNone(b['vent'])

    def test_missing_rain_makes_rain_and_category_missing(self):
        day = datetime(*self.DAY).date()
        hs = self.hours(range(6, 12))
        hs[utc(*self.DAY, 8)]['pluie_mm'] = None
        b = score.to_blocks(hs)[(day, 'matin')]
        self.assertIsNone(b['pluie_mm'])
        self.assertIsNone(b['cat'])

    def test_ratio_needs_at_least_two_hours(self):
        day = datetime(*self.DAY).date()
        hs = self.hours(range(6, 12), ratio=None)
        hs[utc(*self.DAY, 8)]['ratio'] = 0.9
        b = score.to_blocks(hs)[(day, 'matin')]
        self.assertIsNone(b['ratio'])
        self.assertIsNone(b['cat'])  # no ratio, no condition
        hs[utc(*self.DAY, 9)]['ratio'] = 0.5
        b = score.to_blocks(hs)[(day, 'matin')]
        self.assertAlmostEqual(b['ratio'], 0.7)  # mean of the two known ratios


class CompareTest(unittest.TestCase):
    # compare() needs more than 50 values for a parameter and more than 100 scored conditions to report them,
    # so the fixtures hold 120 hours.
    N = 120
    TOL = {'temperature': 3, 'pluie_mm': 2, 'direction': 90}

    def series(self, **kw):
        start = utc(2025, 1, 1, 0, 0)
        return {start + timedelta(hours=i): dict(kw) for i in range(self.N)}

    def test_error_within_tolerance(self):
        # Constant error 1 against tolerance 3: 100 * (1 - 1/3) = 66.67
        s, mae, conf, n = score.compare(self.series(temperature=11.0), self.series(temperature=10.0), self.TOL)
        self.assertAlmostEqual(s['temperature'], 100 * (1 - 1 / 3))
        self.assertAlmostEqual(mae['temperature'], 1.0)

    def test_perfect_forecast_scores_100(self):
        s, mae, _, _ = score.compare(self.series(temperature=10.0), self.series(temperature=10.0), self.TOL)
        self.assertEqual(s['temperature'], 100)
        self.assertEqual(mae['temperature'], 0)

    def test_error_at_tolerance_scores_zero(self):
        s, _, _, _ = score.compare(self.series(temperature=13.0), self.series(temperature=10.0), self.TOL)
        self.assertAlmostEqual(s['temperature'], 0)

    def test_error_outside_tolerance_is_floored_at_zero(self):
        # Error 6 against tolerance 3 would be -100: the score is clamped to 0, the raw error is kept in mae
        s, mae, _, _ = score.compare(self.series(temperature=16.0), self.series(temperature=10.0), self.TOL)
        self.assertEqual(s['temperature'], 0)
        self.assertAlmostEqual(mae['temperature'], 6.0)

    def test_error_is_absolute(self):
        s, _, _, _ = score.compare(self.series(temperature=9.0), self.series(temperature=10.0), self.TOL)
        self.assertAlmostEqual(s['temperature'], 100 * (1 - 1 / 3))

    def test_missing_forecast_values_are_skipped(self):
        # 40 of the 120 hours have no forecast: 80 comparisons remain (> 50), still scored
        fc = self.series(temperature=11.0)
        for t in list(fc)[:40]:
            fc[t]['temperature'] = None
        s, mae, _, _ = score.compare(fc, self.series(temperature=10.0), self.TOL)
        self.assertAlmostEqual(mae['temperature'], 1.0)
        self.assertIn('temperature', s)

    def test_too_few_values_means_no_score(self):
        # Only 50 usable hours: the rule is strictly more than 50, so the parameter is left out
        fc = self.series(temperature=11.0)
        for t in list(fc)[:self.N - 50]:
            fc[t]['temperature'] = None
        s, mae, _, _ = score.compare(fc, self.series(temperature=10.0), self.TOL)
        self.assertNotIn('temperature', s)
        self.assertNotIn('temperature', mae)

    def test_missing_observed_values_are_skipped(self):
        obs = self.series(temperature=10.0)
        for t in obs:
            obs[t]['temperature'] = None
        s, _, _, _ = score.compare(self.series(temperature=11.0), obs, self.TOL)
        self.assertNotIn('temperature', s)

    def test_hours_without_forecast_are_skipped(self):
        # Forecast only covers 40 of the 120 observed hours: too few for a score
        fc = {t: v for t, v in list(self.series(temperature=11.0).items())[:40]}
        s, _, _, _ = score.compare(fc, self.series(temperature=10.0), self.TOL)
        self.assertEqual(s, {})

    def test_direction_wraps_around_north(self):
        # 350° vs 10° is 20° apart, not 340°: 100 * (1 - 20/90) = 77.78
        s, mae, _, _ = score.compare(self.series(direction=350.0, vent=3.0), self.series(direction=10.0, vent=3.0),
                                     self.TOL)
        self.assertAlmostEqual(mae['direction'], 20.0)
        self.assertAlmostEqual(s['direction'], 100 * (1 - 20 / 90))

    def test_direction_ignored_in_calm_air(self):
        s, _, _, _ = score.compare(self.series(direction=350.0), self.series(direction=10.0, vent=1.0), self.TOL)
        self.assertNotIn('direction', s)
        s, _, _, _ = score.compare(self.series(direction=350.0), self.series(direction=10.0), self.TOL)  # no wind at all
        self.assertNotIn('direction', s)

    def test_rain_error_only_counts_where_it_rained(self):
        # 60 dry hours (forecast and observed < 0.1 mm) are ignored; 60 rainy hours with a 1 mm error count
        fc, obs = {}, {}
        start = utc(2025, 1, 1)
        for i in range(120):
            t = start + timedelta(hours=i)
            if i < 60:
                fc[t], obs[t] = {'pluie_mm': 0.0}, {'pluie_mm': 0.0}
            else:
                fc[t], obs[t] = {'pluie_mm': 2.0}, {'pluie_mm': 1.0}
        s, mae, _, _ = score.compare(fc, obs, self.TOL)
        self.assertAlmostEqual(mae['pluie_mm'], 1.0)
        self.assertAlmostEqual(s['pluie_mm'], 100 * (1 - 1 / 2))

    def test_rain_forecast_but_not_observed_counts(self):
        # A false alarm (forecast 1 mm, observed 0) is an error of 1 mm
        s, mae, _, _ = score.compare(self.series(pluie_mm=1.0), self.series(pluie_mm=0.0), self.TOL)
        self.assertAlmostEqual(mae['pluie_mm'], 1.0)

    def test_rain_dry_both_sides_has_no_score(self):
        s, _, _, _ = score.compare(self.series(pluie_mm=0.0), self.series(pluie_mm=0.05), self.TOL)
        self.assertNotIn('pluie_mm', s)

    def test_only_parameters_in_tol_are_scored(self):
        s, _, _, _ = score.compare(self.series(temperature=11.0, vent=5.0), self.series(temperature=10.0, vent=1.0),
                                   {'temperature': 3})
        self.assertEqual(set(s), {'temperature'})

    def test_condition_exact_match_scores_full_credit(self):
        s, _, conf, n = score.compare(self.series(cat=0), self.series(cat=0), self.TOL)
        self.assertEqual(s['condition'], 100)
        self.assertEqual(conf, {(0, 0): self.N})
        self.assertEqual(n, self.N)

    def test_condition_neighbour_gets_partial_credit(self):
        # forecast mixed (1), observed sun (0): CREDIT[(1, 0)] = 0.5
        s, _, conf, _ = score.compare(self.series(cat=1), self.series(cat=0), self.TOL)
        self.assertAlmostEqual(s['condition'], 50.0)
        self.assertEqual(conf, {(1, 0): self.N})

    def test_condition_overcast_vs_rain_credit(self):
        # forecast overcast (2), observed rain (3): CREDIT[(2, 3)] = 0.3
        s, _, _, _ = score.compare(self.series(cat=2), self.series(cat=3), self.TOL)
        self.assertAlmostEqual(s['condition'], 30.0)

    def test_condition_far_apart_gets_nothing(self):
        # forecast sun (0), observed rain (3): no credit
        s, _, conf, _ = score.compare(self.series(cat=0), self.series(cat=3), self.TOL)
        self.assertEqual(s['condition'], 0)
        self.assertEqual(conf, {(0, 3): self.N})

    def test_condition_mixed_half_and_half(self):
        # 60 exact (1 point) + 60 neighbours (0.5 point) -> (60 + 30) / 120 = 75
        fc, obs = {}, {}
        start = utc(2025, 1, 1)
        for i in range(120):
            t = start + timedelta(hours=i)
            fc[t], obs[t] = {'cat': 0}, {'cat': 0 if i < 60 else 1}
        s, _, conf, n = score.compare(fc, obs, self.TOL)
        self.assertAlmostEqual(s['condition'], 75.0)
        self.assertEqual(conf, {(0, 0): 60, (0, 1): 60})
        self.assertEqual(n, 120)

    def test_condition_needs_more_than_100_cases(self):
        fc, obs = self.series(cat=0), self.series(cat=0)
        for t in list(fc)[:self.N - 100]:  # leaves exactly 100
            fc[t]['cat'] = None
        s, _, conf, n = score.compare(fc, obs, self.TOL)
        self.assertNotIn('condition', s)
        self.assertEqual(n, 100)
        self.assertEqual(conf, {(0, 0): 100})

    def test_missing_condition_on_either_side_is_skipped(self):
        fc, obs = self.series(cat=0), self.series(cat=0)
        for t in list(obs)[:30]:
            obs[t]['cat'] = None
        _, _, conf, n = score.compare(fc, obs, self.TOL)
        self.assertEqual(n, self.N - 30)
        self.assertEqual(conf, {(0, 0): self.N - 30})

    def test_empty_inputs(self):
        self.assertEqual(score.compare({}, {}, self.TOL), ({}, {}, {}, 0))


class ExactRatesTest(unittest.TestCase):
    # conf maps (forecast, observed) to a count; 20 cases:
    #   exact: (0,0)=6 + (2,2)=3 + (3,3)=2 = 11 -> 55 %
    #   observed sun (0): (0,0)=6 + (1,0)=2 = 8 -> 6/8 = 75 %
    #   observed overcast (2): (2,2)=3 + (3,2)=1 = 4 -> 3/4 = 75 %
    #   observed rain (3): (3,3)=2 + (2,3)=2 = 4 -> 2/4 = 50 %
    CONF = {(0, 0): 6, (1, 0): 2, (0, 1): 4, (2, 2): 3, (3, 2): 1, (3, 3): 2, (2, 3): 2}

    def test_rates(self):
        ex, sun, overcast, rain = score.exact_rates(self.CONF)
        self.assertAlmostEqual(ex, 55.0)
        self.assertAlmostEqual(sun, 75.0)
        self.assertAlmostEqual(overcast, 75.0)
        self.assertAlmostEqual(rain, 50.0)

    def test_perfect_forecast(self):
        self.assertEqual(score.exact_rates({(0, 0): 5, (1, 1): 5, (2, 2): 5, (3, 3): 5}), (100, 100, 100, 100))

    def test_all_wrong(self):
        self.assertEqual(score.exact_rates({(0, 2): 5, (2, 0): 5, (3, 2): 5}), (0, 0, 0, 0))

    def test_condition_never_observed_gives_zero_rate_not_an_error(self):
        # No rain observed at all: the rain hit rate is 0, not a division by zero
        ex, sun, overcast, rain = score.exact_rates({(0, 0): 4, (3, 0): 1})
        self.assertAlmostEqual(ex, 80.0)
        self.assertAlmostEqual(sun, 80.0)
        self.assertEqual(overcast, 0)
        self.assertEqual(rain, 0)

    def test_mixed_is_counted_in_exact_but_has_no_own_rate(self):
        ex, sun, overcast, rain = score.exact_rates({(1, 1): 10})
        self.assertEqual(ex, 100)
        self.assertEqual((sun, overcast, rain), (0, 0, 0))


class TotalTest(unittest.TestCase):
    def test_weights_sum_to_100(self):
        self.assertEqual(sum(score.WEIGHTS.values()), 100)

    def test_no_condition_means_no_total(self):
        self.assertIsNone(score.total({'temperature': 80}))
        self.assertIsNone(score.total({}))

    def test_condition_alone_is_its_own_total(self):
        self.assertAlmostEqual(score.total({'condition': 80}), 80.0)

    def test_weights_are_renormalised_over_present_components(self):
        # condition weight 60, temperature 7: (80 * 60 + 50 * 7) / 67 = 5150 / 67
        self.assertAlmostEqual(score.total({'condition': 80, 'temperature': 50}), 5150 / 67)

    def test_all_components_perfect(self):
        s = {k: 100 for k in score.WEIGHTS}
        self.assertAlmostEqual(score.total(s), 100.0)

    def test_all_components_at_zero(self):
        s = {k: 0 for k in score.WEIGHTS}
        self.assertEqual(score.total(s), 0)

    def test_full_weighted_sum(self):
        # condition 100 (60) + everything else 0 -> 60 out of 100
        s = {k: 0 for k in score.WEIGHTS}
        s['condition'] = 100
        self.assertAlmostEqual(score.total(s), 60.0)

    def test_keys_without_a_weight_are_ignored(self):
        # The nowcast scale stores '_csi' next to the scores; it must not enter the weighted mean
        self.assertAlmostEqual(score.total({'condition': 70, '_csi': 5}), 70.0)

    def test_condition_dominates(self):
        good_condition = score.total({'condition': 90, 'temperature': 10})
        good_temperature = score.total({'condition': 10, 'temperature': 90})
        self.assertGreater(good_condition, good_temperature)


if __name__ == '__main__':
    unittest.main()
