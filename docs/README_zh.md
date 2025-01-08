# AI 生词本

AI 生词本（“AI Vocabulary Builder” 简称 aivoc）是一个利用了 AI 技术的智能英语生词本工具，它能帮你快速构建起自己的英语生词库，学习起来事半功倍。

核心功能：

- 独创的高效生词收集模式，例句、翻译、生词和释义一键完成
- 通过有趣的故事模式、测试模式助你掌握生词
- 支持超过 10 种目标语言，包括 OpenAI、Gemini、Anthropic 在内的多种 AI 后端

产品截图：

<div align="center">
  <table>
    <tr>
      <td align="center">
        <a href="https://github.com/user-attachments/assets/e89dd25b-b637-461e-9b89-fc9c2dc00c56" target="_blank">
          <img src="https://github.com/user-attachments/assets/e89dd25b-b637-461e-9b89-fc9c2dc00c56" style="max-height: 200px;">
        </a>
        <br>↑ 由 AI 智能提取生词
      </td>
      <td align="center">
        <a href="https://github.com/user-attachments/assets/52e4e594-80c0-4e55-99a8-14de51078d30" target="_blank">
          <img src="https://github.com/user-attachments/assets/52e4e594-80c0-4e55-99a8-14de51078d30" style="max-height: 200px;">
        </a>
        <br>↑ 测验模式，帮助记忆
      </td>
    </tr>
  </table>
</div>

## 快速开始

### 方法 1：直接安装

本工具基于 Python 开发，请使用 pip 来安装本工具：

```console
# 需要 Python 版本 3.9 及以上
pip install ai-vocabulary-builder
```

安装完成后，执行 `aivoc notebook`，在浏览器中打开应用。

### 方法 2：Docker 部署

也可以使用 docker-compose 来运行应用。首先，clone 项目至本地：

```bash
git clone https://github.com/your-repo/ai-vocabulary-builder.git
cd ai-vocabulary-builder
```

然后，运行以下命令：

```bash
docker-compose up
```

容器启动后，即可通过 `http://127.0.0.1:16093` 访问应用。

## 常用功能

绝大多数常用功能都可以在 notebook 中找到，下面是一些更高级的功能：

- 和 [PopClip](https://www.popclip.app/) 集成实现划词添加生词功能。 [操作指引](docs/integrations.md)

## 常用配置

本工具的主要配置项可通过 Web 页面来管理，此处仅列举其他由环境变量配置项。

### AIVOC_DATA_DIR

指定生词本储存数据文件的路径, 默认路径为当前登录用户的 home 目录: `~/`

示例：

```
export AIVOC_DATA_DIR="$HOME/Documents"
```

## 为什么开发这个工具？

学习英语，生词本是一个非常重要的工具。一个优秀的生词本，至少需要包含：**生词、释义、例句、例句释义**这些内容。但是，手动维护这些内容非常繁琐，因此，大部分人学习英语多年，都没有自己的生词本。阅读时，常常是碰见生词，查过词典，20 秒钟后就忘调。

“AI 生词本”尝试着使用 AI 的能力，把构建生词本的过程变得轻松有趣，让每人都可拥有自己的生词本，快速拓展词汇量。
