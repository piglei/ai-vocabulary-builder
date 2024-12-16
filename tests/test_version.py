from voc_builder.version import JohnnyDist


def test__JohnnyDist():
    _ = JohnnyDist(
        "ai-vocabulary-builder", index_urls=["https://piglei.com/"]
    ).versions_available()
