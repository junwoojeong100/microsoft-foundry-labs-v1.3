import json
import unittest

from tools import TOOL_SCHEMA, ToolInputError, estimate_trip_cost, execute_tool


class ToolTests(unittest.TestCase):
    def test_seoul_two_nights_exact_values(self):
        result = estimate_trip_cost("서울", 2)
        self.assertEqual(result["days"], 3)
        self.assertEqual(result["lodging"], 300000)
        self.assertEqual(result["meals"], 90000)
        self.assertEqual(result["total"], 390000)
        self.assertEqual(result["policy_id"], "TRAVEL-2026")
        self.assertEqual(result["currency"], "KRW")
        self.assertEqual(result["status"], "estimate_only")
        self.assertIs(result["approval_required"], True)

    def test_all_cities_and_boundary_nights(self):
        for city, rate in (("서울", 150000), ("부산", 120000), ("기타", 100000)):
            for nights in range(1, 7):
                with self.subTest(city=city, nights=nights):
                    self.assertEqual(
                        estimate_trip_cost(city, nights)["total"],
                        rate * nights + 30000 * (nights + 1),
                    )
        self.assertEqual(estimate_trip_cost("부산", 2)["total"], 330000)

    def test_invalid_nights_never_become_zero_estimates(self):
        for value in (0, -1, 7, True, False, 2.0, "2", "2박", None, []):
            with self.subTest(value=value), self.assertRaises(ToolInputError):
                estimate_trip_cost("서울", value)

    def test_invalid_city_and_argument_shapes(self):
        for city in ("도쿄", "", "seoul", None, []):
            with self.subTest(city=city), self.assertRaises(ToolInputError):
                estimate_trip_cost(city, 2)
        for arguments in (
            "not json",
            "[]",
            "null",
            '{"city":"서울"}',
            '{"city":"서울","nights":2,"approve":true}',
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ToolInputError):
                execute_tool("estimate_trip_cost", arguments)

    def test_no_dynamic_function_dispatch(self):
        with self.assertRaises(ToolInputError):
            execute_tool("approve_payment", '{"city":"서울","nights":2}')
        self.assertEqual(
            execute_tool(
                "estimate_trip_cost", json.dumps({"city": "서울", "nights": 2})
            )["total"],
            390000,
        )

    def test_schema_matches_runtime_contract(self):
        schema = TOOL_SCHEMA["parameters"]
        self.assertEqual(set(schema["required"]), {"city", "nights"})
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["properties"]["city"]["enum"]), {"서울", "부산", "기타"}
        )
        self.assertTrue(TOOL_SCHEMA["strict"])
