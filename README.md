# AI 生词本

AI 生词本（“AI Vocabulary Builder” 简称 aivoc）是一个利用了 AI 技术的智能生词本工具，它能帮你快速构建起自己的生词库，学习起来事半功倍。

核心功能：

- 提供高质量的整句翻译能力
- 由 AI 自动提取生词及释义
- 独创的故事模式助记生词
- 支持 CSV 等格式导出生词本

工具截图：

<img width="742" alt="image" src="https://user-images.githubusercontent.com/731266/224582400-56e66b81-3368-42b6-885f-74a6be160edb.png">

↑ 交互式翻译，自动提取生词

<img width="742" alt="image" src="https://user-images.githubusercontent.com/731266/224582444-49555765-014c-457c-a83c-72c44e9fe3c5.png">

↑ 通过阅读故事，牢固掌握生词

## 快速开始

本工具基于 Python 开发，请使用 pip 来安装本工具：

```console
# 需要 Python 版本 3.7 及以上
pip install ai-vocabulary-builder
```

安装完成后，请在环境变量中设置你的 [OpenAI API key](https://platform.openai.com/account/api-keys)：

```console
# 使用你在 OpenAI 官网上申请到的 key 替换该内容
export OPENAI_API_KEY='your_api_key'
```

之后执行 `aivoc run` 启动工具，进入交互式命令行模式。

除环境变量外，你也可以通过 `--api-key` 参数完成设置：

```console
aivoc run --api-key "your_api_key"
```

## 使用指南

### 交互式命令行

执行 `aivoc run` 命令，会进入交互式命令行模式，在该模式下，你可以快速完成添加生词、阅读故事等操作。

#### 添加生词

默认情况下，命令行处于“添加生词”模式，此时你可以直接粘贴一小段英文：

```console
Enter text> It depicted simply an enormous face, more than a metre wide
```

按下回车后，工具会开始翻译工作。它首先会将你所输入内容的中文翻译打印到屏幕上。然后，它会从原文中提取出一个**你最有可能不认识的单词**，将其加入到生词本中。

```
                              Translation Result
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ Original Text │ It depicted simply an enormous face, more than a metre wide │
│ Translation   │ 它只是简单地描绘了一个巨大的面孔，超过一米宽。              │
└───────────────┴─────────────────────────────────────────────────────────────┘


⠴  Extracting word
> The new word AI has chosen is "depicted".

┏━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Word     ┃ Pronunciation ┃ Definition                 ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ depicted │ /dɪˈpɪkt/     │ 描述，描绘（原词：depict） │
└──────────┴───────────────┴────────────────────────────┘
"depicted" was added to your vocabulary book (78 in total), well done!
```

#### 重选生词

某些情况下，工具所挑选的生词可能并非你所想的那个。此时，通过输入 `no` 命令，你可以启动一次重选：

```
Enter text> no
```

上一次被添加到生词本的单词会被丢弃，工具将尝试重新返回 4 个新生词（可能包含刚被丢弃的词），如下所示：

```
"depicted" has been discarded from your vocabulary book.
⠋  Extracting multiple new words
? Choose the word(s) you don't know (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
 » ○ depicted / （原词：depict） / dɪˈpɪkt / 描绘，描述
   ○ metre / （原词：meter） / ˈmiːtə(r) / 米
   ○ simply / ˈsɪmpli / 简而言之，仅仅
   ○ enormous / ɪˈnɔːməs / 巨大的，庞大的
   ○ None of above, skip for now.
```

请按↑↓方向键移动游标，按空格选中你想要的词（支持多选），按下回车确认。选中的单词会被添加到你的生词本中。

```
? Choose the word(s) you don't know done (2 selections)
New word(s) added to your vocabulary book: "metre,enormous" (79 in total), well done!
```

假如你所想的单词仍然没有出现在选项中，请选择 `None of above, skip for now.`，跳过本次添加。

> 别气馁，祝你下次好运。😁

#### 查看生词

使用 `list` 命令可以查看生词本中最近添加的生词，默认展示 10 条：

```plain
Enter text> list
```

该命令接收一个可选参数：`limit`，用来指定生词的数量。常见用法：

```plain
# 查看最近 5 条
Enter text> list 5
# 查看所有生词
Enter text> list all
```

### 删除生词

使用 `remove` 命令可以进入“删除生词”模式。

<img width="709" alt="image" src="https://user-images.githubusercontent.com/731266/229272715-4e7ba4e2-6c2e-434f-8d84-ca0f2373de04.png">

在该模式下，你可以输入单词（按↑↓方向键选择自动补全），再按回车键将其从生词本中删除。除手动输入外，你还用可以用鼠标选择单词。

要退出“删除生词”模式，输入 q （或不输入任何内容）按下回车，工具将退回到“翻译模式”。

#### 阅读故事来助记生词

为了快速并牢固掌握生词本里的单词，本工具提供了一个创新的故事模式。在交互式命令行模式下，输入 `story` 开始故事模式：

```
Enter text> story
```

工具将从生词本里挑选出 6 个单词，请求 AI 用这些词写一个小故事。输入如下所示：

```
Words for generating story: prudent, extraneous, serendipitously, onus, aphorisms, cater
⠼  Querying OpenAI API to write the story...
╭─────────────────────────────────────────── Enjoy your reading ────────────────────────────────────────────╮
│ Once there was a prudent young girl named Alice who always carried a small notebook with her. She wrote   │
│ down aphorisms and wise sayings that she heard from her elders or from books. It was an extraneous task,  │
│ but Alice believed that it helped her to be wise and joyful.                                              │
│                                                                                                           │
│ One day, Alice went for a walk in the park and serendipitously met an old man. He was reading a book, and │
│ Alice noticed that he had marked some phrases with a pencil. She greeted him and asked about the book.    │
│ They started to chat about literature, and the man shared some of his favorite aphorisms.                 │
│                                                                                                           │
│ Alice was delighted, and she wrote down the new sayings in her notebook. After their conversation, the    │
│ man thanked Alice and said that he felt as if a heavy onus had been lifted from his chest. Alice smiled   │
│ and said that it was her pleasure to cater to his needs.                                                  │
│                                                                                                           │
│ From then on, Alice and the old man often met in the park to exchange knowledge and wisdom. They learned  │
│ that serendipity could bring unexpected blessings to life.                                                │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

阅读结束后，按下回车键，你可以继续查看在故事中出现的所有生词的详细信息。

### 其他功能

### 导出生词本

你可以使用 `export` 命令来导出你的生词本。以下是一些示例：

```
# 直接往屏幕输出文本格式
aivoc export
# 直接往屏幕输出 CSV 格式
aivoc export --format csv
# 往 ./voc.csv 写入 CSV 格式的生词本
aivoc export --format csv --file-path ./voc.csv
```

### 删除生词

如果你觉得你已经牢牢掌握了某个生词，你可以将它从生词本里删除。执行 `remove` 命令来完成这个任务：

```console
# enormous 和 depicted 为需要删除的单词，多个单词使用空格分隔
aivoc remove enormous depicted
```

## 常用配置

此处列举了本工具的所有**全局配置项**。目前仅支持通过环境变量来完成配置，未来将增加对配置文件的支持。

> 如果你想了解各子命令支持哪些个性化参数，比如“导出”支持哪些格式和参数，请使用 `--help` 参数，比如：`aivoc export --help`。

### OPENAI_API_KEY

工具调用 OpenAI 的 API 时所使用的 [API Key](https://platform.openai.com/account/api-keys)，必须设置。

示例：

```
export OPENAI_API_KEY='your_api_key'
```

### OPENAI_API_BASE

工具所使用的 OpenAI 的 API 地址，可选设置。仅当默认 API 地址（`https://api.openai.com/v1`）无法正常访问时指定。

示例：

```bash
# 将 www.example.com 替换为你的域名
export OPENAI_API_BASE="https://www.my-openai-proxy.com/v1"
```

💡 请关注地址配置中的 `/v1` 部分。是否添加它，取决于你的代理配置如何。不确定的话可以先写上，如果无法成功调用，再去掉 `/v1` 试试看。

### AIVOC_DATA_DIR

指定生词本储存数据文件的路径, 默认路径为当前登录用户的 home 目录: `~/`

示例：

```
export AIVOC_DATA_DIR="$HOME/Documents"
```

## 为什么开发这个工具？

学习一门语言，生词本是一个非常重要的工具。一个内容优秀的生词本，至少需要包含：**生词、释义、例句、例句释义**这些内容。但是，手动维护这些内容非常麻烦，因此大部分人都没有自己的生词本。阅读时碰见生词，常常查过词典，转头就忘。

“AI 生词本”尝试着使用 ChatGPT 的能力，将生词本的维护成本降到最低，让每人都可以拥有自己的生词本。

## TODO

- 支持 [bob-plugin-openai-translator](https://github.com/yetone/bob-plugin-openai-translator) 插件，实现划词自动扩充生词本。
