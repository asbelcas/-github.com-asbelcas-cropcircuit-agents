import unittest

from tools.communication_pace_linter import evaluate


BASE = {
    "message": "Hi Alex, the revised brief is ready. No action is needed unless you spot an issue.",
    "purpose": "Deliver the revised brief.",
    "attention_reason": "The promised deliverable is ready.",
    "context_read": True,
    "next_step_count": 0,
    "urgent": False,
    "responding_to_inbound": False,
    "material_update": True,
    "hours_since_last_outbound": 3,
}


class CommunicationPaceLinterTests(unittest.TestCase):
    def test_material_update_can_pass_same_day(self):
        result = evaluate(dict(BASE))
        self.assertEqual(result["decision"], "PASS")

    def test_nonurgent_same_day_stack_holds(self):
        case = dict(BASE)
        case.update({
            "material_update": False,
            "message": "Hi Alex, I had another thought about the project.",
            "purpose": "Share an additional thought.",
            "attention_reason": "New thought.",
            "hours_since_last_outbound": 2,
        })
        result = evaluate(case)
        self.assertEqual(result["decision"], "HOLD")
        self.assertTrue(any("last outbound" in x for x in result["hard_holds"]))

    def test_low_value_checkin_holds(self):
        case = dict(BASE)
        case.update({
            "material_update": False,
            "hours_since_last_outbound": 72,
            "message": "Hi Alex, just checking in to see if you saw my last email.",
            "purpose": "Ask whether the prior email was seen.",
            "attention_reason": "Follow up.",
        })
        result = evaluate(case)
        self.assertEqual(result["decision"], "HOLD")
        self.assertTrue(any("Low-value follow-up" in x for x in result["hard_holds"]))

    def test_inbound_reply_relaxes_timing(self):
        case = dict(BASE)
        case.update({
            "material_update": False,
            "responding_to_inbound": True,
            "hours_since_last_outbound": 1,
            "message": "Yes — Tuesday works. I’ll send the file beforehand.",
            "purpose": "Answer the customer's scheduling question.",
            "attention_reason": "",
        })
        result = evaluate(case)
        self.assertEqual(result["decision"], "PASS")

    def test_multiple_asks_requires_review(self):
        case = dict(BASE)
        case.update({
            "hours_since_last_outbound": 48,
            "material_update": False,
            "next_step_count": 3,
            "message": "Could you confirm the date? Who owns the data? Can you send the file?",
            "purpose": "Resolve project setup.",
            "attention_reason": "The project cannot start without setup details.",
        })
        result = evaluate(case)
        self.assertEqual(result["decision"], "REVIEW")

    def test_missing_context_is_hard_hold(self):
        case = dict(BASE)
        case["context_read"] = False
        result = evaluate(case)
        self.assertEqual(result["decision"], "HOLD")
        self.assertTrue(any("Context" in x for x in result["hard_holds"]))


if __name__ == "__main__":
    unittest.main()
