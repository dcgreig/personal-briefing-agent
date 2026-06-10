import json
import unittest
from pathlib import Path

from briefing_agent.llm_contract import validate_llm_classifier_output


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class LlmClassifierContractTests(unittest.TestCase):
    def test_sample_input_fixture_has_contract_fields(self):
        sample_input = _load_fixture("sample_llm_classifier_input.json")

        self.assertEqual(sample_input["item"]["item_id"], "email-002")
        self.assertIn("waiting_on_me", sample_input["allowed_classifications"])
        self.assertTrue(sample_input["safety"]["dry_run_only"])
        self.assertTrue(sample_input["safety"]["no_external_actions"])

    def test_valid_llm_classifier_output_fixture_passes_validation(self):
        sample_output = _load_fixture("sample_valid_llm_classifier_output.json")

        validate_llm_classifier_output(sample_output)

    def test_invalid_llm_classifier_output_fixture_is_rejected(self):
        sample_output = _load_fixture("sample_invalid_llm_classifier_output.json")

        with self.assertRaises(ValueError):
            validate_llm_classifier_output(sample_output)


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
