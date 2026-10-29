import json
import os
import csv
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_01_tnau_stcr_rules_file_exists_and_valid():
    rules_path = os.path.join(HERE, "data", "agronomy", "tnau_stcr_rules.json")
    assert os.path.exists(rules_path), "tnau_stcr_rules.json missing"
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)
    assert isinstance(rules, list), "Rules JSON should contain a list of rules"
    assert len(rules) > 0
    for r in rules:
        assert "rule_id" in r
        assert "crop" in r
        assert "verification_status" in r
        assert r["verification_status"] in ("VERIFIED", "PROVISIONAL", "PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION", "SOURCE_NOT_VERIFIED", "UNSUPPORTED", "DEPRECATED")


def test_02_source_registry_csv_valid():
    source_path = os.path.join(HERE, "data", "agronomy", "source_registry.csv")
    assert os.path.exists(source_path), "source_registry.csv missing"
    with open(source_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) > 0
    headers = reader.fieldnames
    assert "source_id" in headers or "rule_id" in headers
    assert "source_title" in headers or "official_source_title" in headers


def test_03_env_example_exists():
    env_path = os.path.join(HERE, ".env.example")
    assert os.path.exists(env_path), ".env.example file missing"
