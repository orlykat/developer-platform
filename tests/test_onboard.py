from argparse import Namespace

import pytest
import yaml

from tools import onboard


@pytest.fixture
def valid_args():
    return Namespace(
        name="inventory",
        image="nginx",
        tag="1.28-alpine",
        port=80,
        replicas=2,
        health_path="/",
        dry_run=False,
    )


@pytest.mark.parametrize(
    "name",
    ["inventory", "payment-api", "app123", "a"]
)
def test_valid_names(name):
    onboard.validate_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "Inventory",
        "payment_api",
        "-inventory",
        "inventory-",
        "../inventory",
        "123app",
        "a" * 54,
    ]
)
def test_invalid_names(name):
    with pytest.raises(ValueError):
        onboard.validate_name(name)


@pytest.mark.parametrize(
    "field,value",
    [
        ("port", 0),
        ("port", 65536),
        ("replicas", 0),
        ("replicas", 11),
        ("tag", "latest"),
        ("tag", ""),
        ("image", ""),
        ("health_path", "health"),
    ]
)
def test_invalid_config(valid_args, field, value):
    setattr(valid_args, field, value)

    with pytest.raises(ValueError):
        onboard.validate_config(valid_args)


def test_generate_values(valid_args):
    values = onboard.generate_values(valid_args)

    assert values["replicaCount"] == 2
    assert values["image"]["repository"] == "nginx"
    assert values["image"]["tag"] == "1.28-alpine"
    assert values["containerPort"] == 80
    assert values["probes"]["readiness"]["enabled"] is True
    assert values["probes"]["readiness"]["path"] == "/"
    assert values["probes"]["liveness"]["enabled"] is True
    assert values["probes"]["liveness"]["path"] == "/"


def test_onboard_creates_file(
    valid_args, tmp_path, monkeypatch
):
    monkeypatch.setattr(onboard, "APPS_DIR", tmp_path)

    onboard.onboard(valid_args)

    values_file = tmp_path / "inventory" / "values.yaml"

    assert values_file.exists()

    values = yaml.safe_load(values_file.read_text())

    assert values == onboard.generate_values(valid_args)


def test_dry_run(
    valid_args, tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(onboard, "APPS_DIR", tmp_path)
    valid_args.dry_run = True

    onboard.onboard(valid_args)

    assert not (tmp_path / "inventory").exists()

    output = yaml.safe_load(capsys.readouterr().out)
    assert output == onboard.generate_values(valid_args)


def test_prevent_overwrite(
    valid_args, tmp_path, monkeypatch
):
    monkeypatch.setattr(onboard, "APPS_DIR", tmp_path)

    onboard.onboard(valid_args)

    values_file = tmp_path / "inventory" / "values.yaml"
    original = values_file.read_text()

    valid_args.replicas = 5

    with pytest.raises(FileExistsError):
        onboard.onboard(valid_args)

    assert values_file.read_text() == original