"""步骤十六部署配置测试。"""

from config.settings import Settings


def test_cors_origins_are_parsed_and_trimmed() -> None:
    settings = Settings(cors_origins=" https://app.example.com,https://preview.example.com ")

    assert settings.cors_origin_list == [
        "https://app.example.com",
        "https://preview.example.com",
    ]


def test_default_cors_origins_cover_local_frontend() -> None:
    settings = Settings(_env_file=None)

    assert settings.cors_origin_list == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
