from voc_builder.builder import VocBuilderCSVFile


class TestVocBuilderCSVFile:
    def test_read_all_with_meta(self, tmp_path):
        file_path = tmp_path / 'foo.csv'
        with open(file_path, 'w') as fp:
            fp.write(
                """\
添加时间,单词,读音,释义,例句/翻译
2023-03-06 16:07,iconoclasm,/aɪˈkɑːnəˌklæzəm/,[noun] 反传统做法,"What started as lighthearted iconoclasm, poking at the bear of SOLID, has developed into something more concrete and tangible. / 由轻松挑战传统做法逐渐转化为更具体且实际的事物。" # noqa: E501
2023-03-06 16:07,preamble,/ˈpræmbəl/,序言，前言,Preamble: a long time ago… / 前言：很久很久以前...
2023-03-06 16:07,culprit,['kʌlprɪt],罪犯；犯罪者,"I quickly found the culprit, which was a simple logic error, made a change, built the code, and tested it. / 我很快就找到了罪犯，发现只是一个简单的逻辑错误，我进行了更改，构建了代码并进行了测试。" # noqa: E501
"""
            )
        builder = VocBuilderCSVFile(file_path)
        words = list(builder.read_all_with_meta())
        assert len(words) == 3
