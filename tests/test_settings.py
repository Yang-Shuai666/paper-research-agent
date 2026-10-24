from app.config import PROJECT_ROOT, Settings


def test_settings_defaults_to_deepseek_flash(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.deepseek_model == "deepseek-flash"


def test_settings_reads_embedding_path_from_environment(monkeypatch, tmp_path) -> None:
    model_path = tmp_path / "custom-embedding"
    monkeypatch.setenv("EMBEDDING_MODEL_PATH", str(model_path))

    settings = Settings(_env_file=None)

    assert settings.embedding_model_path == model_path


def test_settings_resolves_relative_embedding_path(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL_PATH", "models/custom-embedding")

    settings = Settings(_env_file=None)

    assert settings.embedding_model_path == PROJECT_ROOT / "models" / "custom-embedding"


def test_settings_rejects_invalid_gpu_fraction(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_GPU_MEMORY_FRACTION", "1.5")

    try:
        Settings(_env_file=None)
    except ValueError as error:
        assert "embedding_gpu_memory_fraction" in str(error)
    else:
        raise AssertionError("Expected validation error for GPU memory fraction")
