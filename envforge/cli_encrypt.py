"""CLI subcommands for encryption key management and snapshot encryption."""

import argparse
import sys

from envforge.encrypt import (
    generate_key,
    get_key_from_env,
    encrypt_values,
    decrypt_values,
    is_encrypted,
    ENVFORGE_KEY_ENV,
)
from envforge.cli import get_store


def cmd_keygen(args: argparse.Namespace) -> None:
    """Generate and print a new encryption key."""
    key = generate_key()
    print(f"Generated key (set as {ENVFORGE_KEY_ENV}):\n{key}")


def cmd_encrypt_snapshot(args: argparse.Namespace) -> None:
    """Encrypt the values of an existing snapshot in-place."""
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    if is_encrypted(snap.variables):
        print(f"Snapshot '{args.name}' is already encrypted.")
        return

    key = get_key_from_env()
    snap.variables = encrypt_values(snap.variables, key)
    store.save(snap)
    print(f"Snapshot '{args.name}' encrypted successfully.")


def cmd_decrypt_snapshot(args: argparse.Namespace) -> None:
    """Decrypt the values of an existing snapshot in-place."""
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)

    if not is_encrypted(snap.variables):
        print(f"Snapshot '{args.name}' does not appear to be encrypted.")
        return

    key = get_key_from_env()
    snap.variables = decrypt_values(snap.variables, key)
    store.save(snap)
    print(f"Snapshot '{args.name}' decrypted successfully.")


def register_encrypt_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register encryption-related subcommands onto an existing subparsers object."""
    p_keygen = subparsers.add_parser("keygen", help="Generate a new encryption key")
    p_keygen.set_defaults(func=cmd_keygen)

    p_enc = subparsers.add_parser("encrypt", help="Encrypt an existing snapshot's values")
    p_enc.add_argument("name", help="Snapshot name to encrypt")
    p_enc.set_defaults(func=cmd_encrypt_snapshot)

    p_dec = subparsers.add_parser("decrypt", help="Decrypt an existing snapshot's values")
    p_dec.add_argument("name", help="Snapshot name to decrypt")
    p_dec.set_defaults(func=cmd_decrypt_snapshot)
