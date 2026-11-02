from prumo.core.security import hash_password, hash_token, new_token, verify_password


def test_password_hash_roundtrip() -> None:
    password_hash = hash_password("senha-segura-123")
    assert password_hash.startswith("$argon2")
    assert verify_password(password_hash, "senha-segura-123")
    assert not verify_password(password_hash, "outra-senha")
    assert not verify_password("not-a-hash", "senha-segura-123")


def test_tokens_are_random_and_only_their_digest_is_kept() -> None:
    first, second = new_token(), new_token()
    assert first != second
    assert len(first) >= 43
    assert len(hash_token(first)) == 32
    assert hash_token(first) == hash_token(first)
    assert hash_token(first) != hash_token(second)
