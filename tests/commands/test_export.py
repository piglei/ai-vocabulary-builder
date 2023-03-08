from voc_builder.commands.export import handle_export
from voc_builder.store import get_word_store


def test_handle_export_ascii_file(tmp_path, w_sample_world):
    get_word_store().add(w_sample_world)
    file_path = tmp_path / 'foo.csv'
    handle_export('ascii', file_path)
    with open(file_path, 'r', encoding='utf-8') as fp:
        assert 'world' in fp.read()


def test_handle_export_csv_file(tmp_path, w_sample_world):
    get_word_store().add(w_sample_world)
    file_path = tmp_path / 'foo.csv'
    handle_export('csv', file_path)
    with open(file_path, 'r', encoding='utf-8') as fp:
        content = fp.read()
        assert content.startswith("#,单词,读音,释义,例句/翻译,添加时间\n")
        # The `date_added` field cannot be compared when the timezone is indeterminate.
        assert '1,world,wɔrld,世界,"Hello, world! / 你好，世界！",' in content
