"""Additional Garmin windows, schema and partial-collection regressions."""

from copy import deepcopy
from unittest.mock import patch
import unittest

from tools.health_sync.garmin import parse_api, categorical_inventory, GarminParseError
from tools.health_sync import garmin_client
from tools.health_sync.api import APIError
from tools.tests.test_garmin_sync import DAY, payload, morning, by_metric
from tools.tests import test_garmin_client as client_fixtures


def activity(ident=1, day=DAY, **kwargs):
    return {"activityId": ident, "startTimeLocal": day + " 12:00:00", **kwargs}


class GarminExtraParserTests(unittest.TestCase):
    def test_sleep_coach_compares_same_date_main_sleep_not_next_night_or_naps(self):
        raw = {"dailySleepDTO": {"calendarDate": DAY, "sleepTimeSeconds": 6*3600,
               "napTimeSeconds": 3600, "sleepNeed": {"calendarDate": DAY, "actual": 450},
               "nextSleepNeed": {"calendarDate": "2026-09-17", "actual": 500},
               "avgHeartRate": 63, "avgSleepStress": 21, "awakeCount": 0},
               "restlessMomentsCount": 22, "avgSkinTempDeviationC": -0.8,
               "avgSkinTempDeviationF": -1.5}
        values = by_metric(parse_api(payload("sleep", raw)))
        expected = {"Sleep Coach Recommendation": 7.5, "Sleep Coach Shortfall": 1.5,
                    "Average Sleeping HR": 63, "Average Sleeping Stress": 21,
                    "Awakening Count": 0, "Restless Moments": 22,
                    "Skin Temperature Deviation": -0.8}
        for name, value in expected.items():
            self.assertAlmostEqual(values[name + " (Garmin)"]["value"], value)
        self.assertEqual(values["Skin Temperature Deviation (Garmin)"]["unit"], "°C")
        for wrong in (None, "2026-09-17"):
            raw["dailySleepDTO"]["sleepNeed"]["calendarDate"] = wrong
            values = by_metric(parse_api(payload("sleep", raw)))
            self.assertNotIn("Sleep Coach Recommendation (Garmin)", values)
            self.assertNotIn("Sleep Coach Shortfall (Garmin)", values)

    def test_no_negative_shortfall_and_no_sleep_placeholders(self):
        raw = {"dailySleepDTO": {"sleepTimeSeconds": 8*3600,
               "sleepNeed": {"calendarDate": DAY, "actual": 420}}, "avgSkinTempDeviationC": 0}
        values = by_metric(parse_api(payload("sleep", raw)))
        self.assertEqual(values["Sleep Coach Shortfall (Garmin)"]["value"], 0)
        self.assertEqual(values["Skin Temperature Deviation (Garmin)"]["value"], 0)
        raw["dailySleepDTO"]["sleepTimeSeconds"] = 0
        self.assertEqual(parse_api(payload("sleep", raw)), [])

    def test_only_available_morning_contributors_not_onboarding_zero_or_exercise(self):
        raw = [morning(acuteLoad=387, acwrFactorPercent=91, acwrFactorFeedback="GOOD",
                       hrvFactorPercent=0, hrvFactorFeedback="NONE",
                       sleepHistoryFactorPercent=76, sleepHistoryFactorFeedback="GOOD"),
               morning(inputContext="AFTER_POST_EXERCISE_RESET", acuteLoad=999,
                       acwrFactorPercent=1, acwrFactorFeedback="POOR")]
        values = by_metric(parse_api(payload("training_readiness", raw)))
        self.assertEqual(values["Morning Acute Training Load (Garmin)"]["value"], 387)
        self.assertEqual(values["Morning Load Contributor (Garmin)"]["value"], 91)
        self.assertNotIn("Morning HRV Contributor (Garmin)", values)
        self.assertEqual(values["Morning Sleep History Contributor (Garmin)"]["value"], 76)

    def test_wakeup_body_battery_is_separate_from_daily_extrema(self):
        values = by_metric(parse_api(payload("daily_summary", {
            "bodyBatteryAtWakeTime": 64, "bodyBatteryHighestValue": 83,
            "bodyBatteryLowestValue": 12, "bodyBatteryChargedValue": 37})))
        self.assertEqual(values["Body Battery at Wakeup (Garmin)"]["value"], 64)
        self.assertEqual(values["Body Battery Highest (Garmin)"]["value"], 83)

    def test_vo2_uses_actual_dated_sport_measurements_and_preserves_precision(self):
        raw = [{"generic": {"calendarDate": DAY, "vo2MaxValue": 45, "vo2MaxPreciseValue": 45.3},
                "cycling": {"calendarDate": DAY, "vo2MaxValue": 48}}]
        values = by_metric(parse_api(payload("max_metrics", raw)))
        self.assertEqual(values["VO2 Max Running (Garmin)"]["value"], 45.3)
        self.assertEqual(values["VO2 Max Cycling (Garmin)"]["value"], 48)
        raw[0]["generic"]["calendarDate"] = "2026-09-15"
        del raw[0]["cycling"]["calendarDate"]
        self.assertEqual(parse_api(payload("max_metrics", raw)), [])

    def test_fitness_ages_keep_current_and_achievable_distinct(self):
        values = by_metric(parse_api(payload("fitness_age", {"calendarDate": DAY,
             "fitnessAge": 32.5, "achievableFitnessAge": 30, "chronologicalAge": 36})))
        self.assertEqual(len(values), 2)
        self.assertEqual(values["Fitness Age (Garmin)"]["value"], 32.5)
        for day in (None, "2026-09-15"):
            self.assertEqual(parse_api(payload("fitness_age", {"calendarDate": day, "fitnessAge": 30})), [])

    def test_live_fitness_age_last_updated_dates_snapshot_but_components_are_not_an_age(self):
        live = {"lastUpdated": DAY + "T00:00:00.0", "chronologicalAge": 35,
                "components": {"rhr": {"value": 63}, "vigorousDaysAvg": {"stale": True}}}
        self.assertEqual(parse_api(payload("fitness_age", live)), [])
        result = by_metric(parse_api(payload("fitness_age", {**live, "fitnessAge": 32.5})))
        self.assertEqual(result["Fitness Age (Garmin)"]["value"], 32.5)
        for stamp in ("2026-09-15T00:00:00.0", None):
            self.assertEqual(parse_api(payload("fitness_age", {**live, "lastUpdated": stamp,
                                                                   "fitnessAge": 32.5})), [])

    def test_performance_privacy_flags_are_not_silently_interpreted(self):
        for endpoint, doc in (("fitness_age", {"calendarDate": DAY, "fitnessAge": 32}),
                              ("max_metrics", {"generic": {"calendarDate": DAY, "vo2MaxValue": 45}}),
                              ("training_status", {}),
                              ("activities", activity())):
            with self.subTest(endpoint=endpoint), self.assertRaises(GarminParseError):
                parse_api(payload(endpoint, {**doc, "privacyProtected": True}))

    def test_training_status_uses_primary_same_day_device_and_text_not_numeric_codes(self):
        selected = {"primaryTrainingDevice": True, "calendarDate": DAY,
                    "trainingStatus": 7, "trainingStatusFeedbackPhrase": "PRODUCTIVE_3",
                    "acuteTrainingLoadDTO": {"dailyTrainingLoadAcute": 387,
                        "dailyTrainingLoadChronic": 350, "dailyAcuteChronicWorkloadRatio": 1.1,
                        "acwrStatus": "OPTIMAL"}}
        raw = {"mostRecentTrainingStatus": {"latestTrainingStatusData": {
            "1": selected, "2": {"calendarDate": DAY, "trainingStatus": 9}}}}
        values = by_metric(parse_api(payload("training_status", raw)))
        self.assertEqual(values["Acute Training Load (Garmin)"]["value"], 387)
        self.assertEqual(values["Acute/Chronic Training Load Ratio (Garmin)"]["value"], 1.1)
        self.assertEqual({r['value'] for r in categorical_inventory(payload("training_status", raw))},
                         {"PRODUCTIVE_3", "OPTIMAL"})
        selected['calendarDate'] = "2026-09-15"
        self.assertEqual(parse_api(payload("training_status", raw)), [])
        selected['calendarDate'] = DAY
        selected['primaryTrainingDevice'] = False
        self.assertEqual(parse_api(payload("training_status", raw)), [])

    def test_onboarding_training_feedback_is_not_a_health_classification(self):
        for feedback in ('NO_STATUS_1','NO_STATUS_2'):
            raw = {'mostRecentTrainingStatus': {'latestTrainingStatusData': {'1': {
                'calendarDate': DAY, 'primaryTrainingDevice': True,
                'trainingStatusFeedbackPhrase': feedback,
                'acuteTrainingLoadDTO': {'dailyTrainingLoadAcute': 387, 'acwrStatus': 'OPTIMAL'}}}}}
            source = deepcopy(raw)
            rows = categorical_inventory(payload('training_status',raw))
            self.assertEqual([(r['metric'],r['value']) for r in rows], [('Training Load Status (Garmin)','OPTIMAL')])
            self.assertEqual(parse_api(payload('training_status',raw))[0]['value'],387)
            self.assertEqual(raw,source)

    def test_explicit_hrv_onboarding_none_remains_raw_without_observation(self):
        raw = {'hrvSummary': {'calendarDate': DAY, 'status': 'NONE',
                             'feedbackPhrase': 'ONBOARDING_1', 'lastNightAvg': 30}}
        source = deepcopy(raw)
        self.assertEqual(categorical_inventory(payload('hrv',raw)),[])
        self.assertEqual(parse_api(payload('hrv',raw))[0]['value'],30)
        self.assertEqual(raw,source)
        del raw['hrvSummary']['feedbackPhrase']
        self.assertEqual(categorical_inventory(payload('hrv',raw))[0]['value'],'NONE')

    def test_workouts_deduplicate_ids_exclude_parent_overlap_and_preserve_distinct_events(self):
        first = activity(1, aerobicTrainingEffect=3.2, anaerobicTrainingEffect=0,
                         activityTrainingLoad=100, trainingEffectLabel="AEROBIC_BASE")
        raw = [first, deepcopy(first), activity(2, aerobicTrainingEffect=2.4),
               activity(3, parentId=1, aerobicTrainingEffect=4.8)]
        values = parse_api(payload("activities", raw))
        aerobic = [v for v in values if v['metric']=='Aerobic Training Effect per Workout (Garmin)']
        self.assertEqual([v['value'] for v in aerobic], [3.2, 2.4])
        self.assertEqual(len({v['id'] for v in aerobic}), 2)
        self.assertEqual(categorical_inventory(payload("activities", raw))[0]['value'], "AEROBIC_BASE")
        with self.assertRaises(GarminParseError):
            parse_api(payload("activities", [activity(1, aerobicTrainingEffect=5.1)]))

    def test_zone_seconds_sum_across_recorded_activities_and_duplicate_is_not_counted_twice(self):
        first = activity(1, zones=[{"zoneNumber": 2, "secsInZone": 120},
                                  {"zoneNumber": 5, "secsInZone": 0}])
        raw = [first, deepcopy(first), activity(2, zones=[{"zoneNumber": 2,"secsInZone": 300}])]
        values = by_metric(parse_api(payload("activity_hr_zones", raw)))
        record = values["Workout HR Zone 2 Duration (Garmin)"]
        self.assertEqual(record['value'], 7)
        self.assertEqual(record['source_count'], 2)
        self.assertEqual(record['source_record_ids'], ['1','2'])
        self.assertEqual(values["Workout HR Zone 5 Duration (Garmin)"]['value'], 0)


class GarminExtraClientTests(unittest.TestCase):
    setUp = client_fixtures.GarminClientTests.setUp
    save = client_fixtures.GarminClientTests.save
    fetch = client_fixtures.GarminClientTests.fetch

    def test_performance_endpoints_are_fetchable_optional_collections(self):
        self.client.get_max_metrics.side_effect = client_fixtures.NotFoundError()
        result = self.fetch()
        self.assertEqual(result['_sync']['endpoint_status']['max_metrics']['status'], 'unavailable')
        self.assertEqual(result['_sync']['endpoint_status']['fitness_age']['status'], 'complete')

    def test_activity_child_404_preserves_entire_daily_zone_sum(self):
        day = self.first.isoformat()
        self.client.connectapi.return_value = [activity(1,day),activity(2,day)]
        self.client.get_activity_hr_in_timezones.side_effect = [[{'zoneNumber':2,'secsInZone':120}],client_fixtures.NotFoundError()]
        result = self.fetch()
        self.assertEqual(result['activity_hr_zones'], [])
        self.assertEqual(len(result['activities'][0]['data']),2)
        self.assertEqual(result['_sync']['endpoint_status']['activity_hr_zones']['unavailable_days'],[day])

    def test_activity_404_preserves_both_related_collections(self):
        self.client.connectapi.side_effect = client_fixtures.NotFoundError()
        result = self.fetch()
        self.assertEqual(result['_sync']['endpoint_status']['activities']['status'],'unavailable')
        self.assertEqual(result['_sync']['endpoint_status']['activity_hr_zones']['status'],'unavailable')
        self.client.get_activity_hr_in_timezones.assert_not_called()

    def test_activity_pagination_has_no_silent_truncation(self):
        self.client.connectapi.return_value = [activity(1,self.first.isoformat())]
        with patch.object(garmin_client,'ACTIVITY_PAGE_SIZE',1), patch.object(garmin_client,'MAX_ACTIVITY_PAGES',1):
            with self.assertRaisesRegex(APIError,'pagination limit'):
                self.fetch()
        self.client.get_activity_hr_in_timezones.assert_not_called()

    def test_repeated_activity_page_fails_before_zone_requests(self):
        self.client.connectapi.return_value = [activity(1,self.first.isoformat())]
        with patch.object(garmin_client,'ACTIVITY_PAGE_SIZE',1):
            with self.assertRaisesRegex(APIError,'repeated a page'):
                self.fetch()


if __name__ == '__main__':
    unittest.main()
