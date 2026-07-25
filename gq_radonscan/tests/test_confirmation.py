import unittest

from radonscan3.web import _destructive_confirmation_ok, _normalise_confirmation


class ConfirmationTests(unittest.TestCase):
    def test_accepts_supported_tokens(self):
        for value in ("LÖSCHEN", "Loeschen", "DELETE", "PURGE", " Prurge ", "Pruge"):
            self.assertTrue(_destructive_confirmation_ok({"confirmation": value}), value)

    def test_accepts_decomposed_umlaut_and_confirmed_flag(self):
        self.assertEqual(_normalise_confirmation("LO\u0308SCHEN"), "LÖSCHEN")
        self.assertTrue(_destructive_confirmation_ok({"confirmation": "LO\u0308SCHEN"}))
        self.assertTrue(_destructive_confirmation_ok({"confirmed": True}))

    def test_rejects_unconfirmed_request(self):
        self.assertFalse(_destructive_confirmation_ok({"confirmation": ""}))
        self.assertFalse(_destructive_confirmation_ok({"confirmation": "YES"}))


    def test_accepts_header_and_string_boolean(self):
        self.assertTrue(_destructive_confirmation_ok({}, "LÖSCHEN"))
        self.assertTrue(_destructive_confirmation_ok({"confirmed": "true"}))
        self.assertTrue(_destructive_confirmation_ok({"confirmation_text": "PURGE"}))

if __name__ == "__main__":
    unittest.main()
