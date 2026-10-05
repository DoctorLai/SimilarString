import importlib.util
import logging
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from flask import Flask
from gunicorn.app.base import BaseApplication


@pytest.fixture
def load_server(monkeypatch, tmp_path):
    transformers = MagicMock()
    transformers.util.pytorch_cos_sim.return_value.item.return_value = 0.75
    transformers.SentenceTransformer.return_value.encode.side_effect = (
        lambda sentence, *, convert_to_tensor: MagicMock()
    )
    torch = MagicMock()
    monkeypatch.setitem(sys.modules, "sentence_transformers", transformers)
    monkeypatch.setitem(sys.modules, "torch", torch)
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(tmp_path)

    def load(overrides=None, *, cuda_available=False):
        torch.cuda.is_available.return_value = cuda_available
        if overrides is None:
            monkeypatch.delenv("SIMILARSTRING_CONFIG", raising=False)
        else:
            config_path = tmp_path / "config.yaml"
            config_path.write_text(yaml.safe_dump(overrides), encoding="utf-8")
            monkeypatch.setenv("SIMILARSTRING_CONFIG", str(config_path))
        spec = importlib.util.spec_from_file_location("server", root / "server.py")
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, "server", module)
        spec.loader.exec_module(module)
        module.app.config["TESTING"] = True
        return module

    return load


@pytest.fixture
def server(load_server):
    return load_server()


@pytest.mark.parametrize("method", ["get", "post"])
def test_similarity_preserves_response(server, method):
    client = server.app.test_client()
    response = getattr(client, method)(
        "/", json={"s1": " A laptop ", "s2": "A computer"}
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "success",
        "s1": " A laptop ",
        "s2": "A computer",
        "score": 0.75,
    }
    assert [call.args[0] for call in server.model.encode.call_args_list] == [
        "a laptop",
        "a computer",
    ]


@pytest.mark.parametrize("method", ["get", "post"])
def test_score_override_skips_inference(server, method):
    response = getattr(server.app.test_client(), method)(
        "/", json={"s1": "first", "s2": "second", "test": 0.42}
    )

    assert response.status_code == 200
    assert response.get_json()["score"] == 0.42
    server.model.encode.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        [],
        ["s1", "s2"],
        "text",
        12,
        {},
        {"s1": "first"},
        {"s2": "second"},
        {"s1": None, "s2": "second"},
        {"s1": "first", "s2": 12},
        {"s1": ["first"], "s2": "second"},
        {"s1": "", "s2": "second"},
        {"s1": "first", "s2": " \n "},
    ],
)
def test_invalid_payload_returns_json_error(server, payload):
    response = server.app.test_client().post("/", json=payload)

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
    server.model.encode.assert_not_called()


@pytest.mark.parametrize("body", ["", "null", "{"])
def test_invalid_json_returns_json_error(server, body):
    response = server.app.test_client().post(
        "/", data=body, content_type="application/json"
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
    server.model.encode.assert_not_called()


def test_legacy_get_accepts_json_without_content_type(server):
    response = server.app.test_client().get("/", data='{"s1": "first", "s2": "second"}')

    assert response.status_code == 200
    assert response.get_json()["score"] == 0.75


def test_health_does_not_run_inference(server):
    response = server.app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "version": server.VERSION,
        "model": server.model_name,
        "device": "cpu",
    }
    server.model.encode.assert_not_called()


def test_request_limit_returns_json_error(server):
    server.app.config["MAX_CONTENT_LENGTH"] = 32
    response = server.app.test_client().post(
        "/", json={"s1": "first" * 10, "s2": "second"}
    )

    assert response.status_code == 413
    assert response.get_json()["status"] == "error"
    server.model.encode.assert_not_called()


def test_requests_do_not_log_submitted_text(server, caplog):
    with caplog.at_level(logging.INFO):
        response = server.app.test_client().post(
            "/", json={"s1": "private sentence one", "s2": "private sentence two"}
        )

    assert response.status_code == 200
    assert "Similarity request completed" in caplog.text
    assert "private sentence" not in caplog.text


def test_cache_disabled_recomputes_embeddings(server):
    server.get_embedding("same")
    server.get_embedding("same")

    assert server.cache is None
    assert server.model.encode.call_count == 2


def test_cache_normalizes_and_evicts_least_recently_used(load_server):
    server = load_server({"cache": {"enabled": True, "max_size": 2}})
    first = server.get_embedding(" First ")
    server.get_embedding("second")
    assert server.get_embedding("FIRST") is first
    server.get_embedding("third")

    assert list(server.cache) == ["first", "third"]
    assert server.model.encode.call_count == 3
    server.get_embedding("second")
    assert list(server.cache) == ["third", "second"]
    assert server.model.encode.call_count == 4


@pytest.mark.parametrize("size", [0, -1, "unlimited", True, False, 1.5, None])
def test_invalid_cache_limit_is_rejected(load_server, size):
    with pytest.raises(ValueError, match="cache.max_size"):
        load_server({"cache": {"enabled": True, "max_size": size}})


@pytest.mark.parametrize("available, expected", [(False, "cpu"), (True, "cuda")])
def test_auto_device_selection(load_server, available, expected):
    server = load_server({}, cuda_available=available)

    assert server.device == expected
    server.SentenceTransformer.assert_called_once_with(
        "all-MiniLM-L6-v2", device=expected
    )


def test_explicit_device_selection(load_server):
    server = load_server({"model": {"device": "cuda:1"}})

    assert server.device == "cuda:1"
    server.torch.cuda.is_available.assert_not_called()


@pytest.mark.parametrize(
    "precision, method", [("float16", "half"), ("float32", "float")]
)
def test_model_precision_is_applied_at_initialization(load_server, precision, method):
    server = load_server({"model": {"precision": precision}})

    getattr(server.model, method).assert_called_once_with()
    server.get_embedding("text")
    server.model.encode.assert_called_once_with("text", convert_to_tensor=True)


def test_invalid_precision_is_rejected(load_server):
    with pytest.raises(ValueError, match="model.precision"):
        load_server({"model": {"precision": "int8"}})


def test_non_mapping_configuration_is_rejected(load_server):
    with pytest.raises(ValueError, match="YAML mapping"):
        load_server(["model"])


def test_development_startup_uses_config(server, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    run = MagicMock()
    monkeypatch.setattr(server.app, "run", run)
    server.config["server"] = {"host": "127.0.0.1", "port": 8080, "debug": True}

    server.main()

    run.assert_called_once_with(host="127.0.0.1", port=8080, debug=True)


def test_script_entrypoint_starts_development_server(server, monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    run = MagicMock()
    monkeypatch.setattr(Flask, "run", run)

    runpy.run_path(server.__file__, run_name="__main__")

    run.assert_called_once_with(host="0.0.0.0", port=5000, debug=False)


def test_production_startup_uses_gunicorn(server, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    applications = []
    monkeypatch.setattr(
        BaseApplication, "run", lambda application: applications.append(application)
    )
    server.config["server"] = {"host": "127.0.0.1", "port": 8080, "workers": 3}

    server.main()

    application = applications[0]
    assert application.load() is server.app
    assert application.cfg.bind == ["127.0.0.1:8080"]
    assert application.cfg.workers == 3
    filtered = type(application)(server.app, {"workers": None, "unknown": "ignored"})
    assert filtered.cfg.workers == 1
