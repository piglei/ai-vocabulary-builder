# AI Vocabulary Builder

AI Vocabulary Builder（后简称“aivoc”）是一个利用了 AI 技术的智能生词本工具，可以帮你快速构建起自己的生词库，学习事半功倍。

学习一门语言，生词本是一个非常重要的工具。一个内容优秀的生词本，至少需要包含：**生词、释义、例句、例句释义**这些内容。但是，手动维护这些内容非常麻烦，所以大部分人都没有自己的生词本。阅读时碰见生词，常常查过词典，转头就忘。

aivoc 尝试着使用 ChatGPT 的能力，将维护生词本的成本降到最低，让每人都可以拥有自己的生词本。

使用 aivoc，每当你读到一句包含了生词的句子时，只要将其原样输入到 aivoc 工具中，便可以获得：

- 整句话的全文翻译
- 由 AI 提取出的生词及释义
- **一个免维护的全自动生词本表格**

## 快速开始

使用 pip 来安装本工具：

```console
# 需要 Python 版本 3.7 及以上
$ pip install ai-vocabulary-builder
```

完成后，在环境变量设置好你的 OPENAI API KEY：

```console
# 使用你在 OpenAI 官网上申请到的 key 替换该内容
$ export OPENAI_API_KEY='your_api_key'
```

一切就绪，之后执行 `aivoc` 启动工具，进入交互翻译模式。

执行 `aivoc --help` 查看更多帮助。

## TODO

- 支持 [bob-plugin-openai-translator](https://github.com/yetone/bob-plugin-openai-translator) 插件，实现划词自动扩充生词本。
