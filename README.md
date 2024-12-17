# AI 生词本

AI 生词本（“AI Vocabulary Builder” 简称 aivoc）是一个利用了 AI 技术的智能生词本工具，它能帮你快速构建起自己的生词库，学习起来事半功倍。

核心功能：

- 提供高质量的整句翻译能力
- 由 AI 智能提取生词及释义
- 独创的故事模式助记生词

产品截图：

![image](https://github.com/user-attachments/assets/e89dd25b-b637-461e-9b89-fc9c2dc00c56)

↑ 由 AI 智能提取生词

![image](https://github.com/user-attachments/assets/52e4e594-80c0-4e55-99a8-14de51078d30)
↑ 测验模式，帮助记忆

## 快速开始

本工具基于 Python 开发，请使用 pip 来安装本工具：

```console
# 需要 Python 版本 3.9 及以上
pip install ai-vocabulary-builder
```

安装完成后，执行 `aivoc notebook`，在浏览器中打开应用。

## 使用指南

执行 `aivoc notebook` 命令，使用可交互式 Web App。初次使用应用，需要在 Settings 页面中配置 AI 服务。

> 当前支持 OpenAI 和 Gemini。

## 常用配置

本工具的主要配置项可通过页面来管理，此处仅列举其他由环境变量配置项。

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
