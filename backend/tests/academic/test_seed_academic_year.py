# File Name: test_seed_academic_year.py
# Description: Check academic seed year boundaries without loading database or environment configuration.
# Created At: 2026-10-29
# Created By: AI Agent
# Updated At: 2026-10-29
# Updated By: AI Agent

import ast
from datetime import date
from pathlib import Path
import unittest


class AcademicSeedYearTests(unittest.TestCase):
    def test_school_year_rollover(self):
        """Match the frontend's August rollover without importing seed side effects."""
        path = Path(__file__).resolve().parents[2] / "app/scripts/seed_academic_data.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == "seed_academic_sample_data")
        statements = next(node for node in function.body if isinstance(node, ast.Try)).body
        names = {"today", "start_year", "academic_year", "classes_data"}
        assignments = [node for node in statements if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id in names
                               for target in node.targets)]
        code = compile(ast.Module(body=assignments, type_ignores=[]), str(path), "exec")
        for today, expected in [(date(2026, 7, 31), "2025-2026"),
                                (date(2026, 8, 1), "2026-2027"),
                                (date(2027, 1, 1), "2026-2027")]:
            with self.subTest(today=today):
                class Clock:
                    @staticmethod
                    def today():
                        return today

                scope = {"date": Clock}
                exec(code, scope)
                self.assertEqual(scope["academic_year"], expected)
                self.assertEqual(len(scope["classes_data"]), 3)
                self.assertTrue(all(item["school_year"] == expected
                                    for item in scope["classes_data"]))


if __name__ == "__main__":
    unittest.main()
