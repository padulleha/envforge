"""Tests for envforge.encrypt module."""

import pytest

pytest.importorskip("cryptography", reason="cryptography package not installed")

from envforge.encrypt import (
    generate_key,
    encrypt_values,
    decrypt_values,
    is_encrypted,
)


SAMPLE = {"API_KEY": "secret123", "DB_PASS": "hunter2", "PORT": "8080"}


@pytest.fixture
def key() -> str:
    return generate_key()


def test_generate_key_is_string(key):
    assert isinstance(key, str)
    assert len(key) > 0


def test_generate_key_unique():
    assert generate_key() != generate_key()


def test_encrypt_values_prefixed(key):
    encrypted = encrypt_values(SAMPLE, key)
    for v in encrypted.values():
        assert v.startswith("enc:"), f"Expected 'enc:' prefix, got: {v}"


def test_encrypt_values_keys_preserved(key):
    encrypted = encrypt_values(SAMPLE, key)
    assert set(encrypted.keys()) == set(SAMPLE.keys())


def test_decrypt_roundtrip(key):
    encrypted = encrypt_values(SAMPLE, key)
    decrypted = decrypt_values(encrypted, key)
    assert decrypted == SAMPLE


def test_decrypt_ignores_plain_values(key):
    mixed = {"PLAIN": "hello", "ENC": "enc:" + "x" * 0}  # invalid enc token
    # Only plain values should pass through; enc: ones will fail
    plain_only = {"PLAIN": "hello"}
    result = decrypt_values(plain_only, key)
    assert result == plain_only


def test_is_encrypted_true(key):
    encrypted = encrypt_values(SAMPLE, key)
    assert is_encrypted(encrypted) is True


def test_is_encrypted_false():
    assert is_encrypted(SAMPLE) is False


def test_is_encrypted_partial(key):
    partial = {"A": "plain", "B": "enc:sometoken"}
    assert is_encrypted(partial) is True


def test_wrong_key_raises(key):
    other_key = generate_key()
    encrypted = encrypt_values(SAMPLE, key)
    with pytest.raises(ValueError, match="Failed to decrypt"):
        decrypt_values(encrypted, other_key)
