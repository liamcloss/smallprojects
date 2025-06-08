import importlib
import sys
import os

import pytest


def import_password_gen(monkeypatch, initial='6'):
    """Import passwordGen while providing a default input to avoid hanging."""
    monkeypatch.setattr('builtins.input', lambda _='': initial)
    # Ensure repository root is on the module search path
    repo_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_root)
    if 'passwordGen' in sys.modules:
        del sys.modules['passwordGen']
    mod = importlib.import_module('passwordGen')
    sys.path.remove(repo_root)
    return mod


def test_get_length_valid(monkeypatch):
    mod = import_password_gen(monkeypatch)
    monkeypatch.setattr('builtins.input', lambda _='': '8')
    assert mod.getLength() == 8


def test_get_length_invalid_then_valid(monkeypatch):
    mod = import_password_gen(monkeypatch)
    responses = iter(['abc', '5', '9'])
    monkeypatch.setattr('builtins.input', lambda _='': next(responses))
    assert mod.getLength() == 9
