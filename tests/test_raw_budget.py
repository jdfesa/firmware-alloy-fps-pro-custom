import unittest
from test_firmware import module

budget = module("measure_raw_hid")


class RawBudgetTests(unittest.TestCase):
    def test_full_measurement(self):
        report = budget.overflow_from_log("ld:rules_memory.ld:314 cannot move location counter backwards (from 20000958 to 20000800)")
        self.assertEqual(report, {"ram_bytes": 2048, "linker_ram_location_bytes": 2392, "overflow_bytes": 344})

    def test_minimal_measurement(self):
        self.assertEqual(budget.overflow_from_log("cannot move location counter backwards (from 200008c0 to 20000800)")["overflow_bytes"], 192)

    def test_unrelated_failure_is_not_a_ram_result(self):
        for text in ("fatal error: missing.h", "cannot move location counter backwards (from 20000958 to 20001000)",
                     "cannot move location counter backwards (from 20000700 to 20000800)"):
            self.assertIsNone(budget.overflow_from_log(text))

    def test_measurement_preserves_stacks_and_minimizes_queues(self):
        for config in budget.CASES.values():
            self.assertNotIn("STACKSIZE", config)
            for queue in ("RAW_IN", "RAW_OUT", "KEYBOARD_IN"):
                self.assertIn("#define " + queue + "_CAPACITY 1", config)
        self.assertNotIn("NO_ACTION_TAPPING", budget.CASES["raw_budget_full"])
        self.assertIn("NO_ACTION_TAPPING", budget.CASES["raw_budget_minimal"])
