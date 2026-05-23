import unittest

from jose import JWTError

from app.security.token import JWTUtils


class JWTUtilsTestCase(unittest.TestCase):
    def test_round_trips_payload_with_explicit_secret(self) -> None:
        payload = {"sub": "user-1", "role": "MEMBER"}

        token = JWTUtils.encode(payload, secret="test-secret")

        self.assertEqual(
            JWTUtils.decode(token, secret="test-secret"),
            payload,
        )

    def test_rejects_token_signed_with_another_secret(self) -> None:
        token = JWTUtils.encode({"sub": "user-1"}, secret="first-secret")

        with self.assertRaises(JWTError):
            JWTUtils.decode(token, secret="second-secret")


if __name__ == "__main__":
    unittest.main()
