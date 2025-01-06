# AI Voc Builder

> Available in other languages: [[中文]](docs/README_zh.md)

"AI Voc Builder" is a smart English vocabulary tool powered by AI technology. It helps you quickly build your own English vocabulary and learn more effectively.

Key Features:

- Unique, efficient vocabulary building: **One-click** saving of sample sentences, translations, new words, and definitions.
- Engaging **story and quiz modes** to help you master new words.
- Supports **over 10 target languages** with multiple AI backends, including OpenAI, Gemini, and Anthropic.

Product Screenshots:

<div align="center">
  <table>
    <tr>
      <td align="center">
        <a href="https://github.com/user-attachments/assets/5f45a172-bb01-4277-81e4-68e3381d2113" target="_blank">
          <img src="https://github.com/user-attachments/assets/5f45a172-bb01-4277-81e4-68e3381d2113" style="max-height: 200px;">
        </a>
        <br>↑ AI-Powered Smart Vocabulary Extraction
      </td>
      <td align="center">
        <a href="https://github.com/user-attachments/assets/bdfe9802-bccc-4d85-9fc5-09829a20bbcc" target="_blank">
          <img src="https://github.com/user-attachments/assets/bdfe9802-bccc-4d85-9fc5-09829a20bbcc" style="max-height: 200px;">
        </a>
        <br>↑ Test Mode for Enhanced Memorization
      </td>
    </tr>
  </table>
</div>

## Quick Start

This tool is developed using Python. Please use `pip` or other packaging tools to install it:

```bash
pip install ai-vocabulary-builder
```

[pipx](https://github.com/pypa/pipx)

```bash
pipx install ai-vocabulary-builder
```

[uv](https://github.com/astral-sh/uv)

```bash
uv pip install ai-vocabulary-builder
# or uvx to run the notebook directly
# uvx --from ai-vocabulary-builder aivoc notebook
```

> Requires Python version 3.9 or higher.

After installation, run `aivoc notebook` to open the application in your browser.

## Docker

For easier setup and a consistent environment, you can also use Docker. See the [CONTRIBUTING.md](CONTRIBUTING.md) file for instructions on building and running the Docker image.

## Features

The most commonly used features can be found inside the notebook app. Here are some more advanced features:

- Integration with [PopClip](https://www.popclip.app/) to add new words by highlighting. [Read Guide](docs/integrations.md)

## Configurations

The main configurations for this tool can be managed from the web page. Here are some additional configurations that are set through environment variables.

### AIVOC_DATA_DIR

Specifies the path where the vocabulary data files are stored. The default path is the current user's home directory: ~/.

Example:

```
export AIVOC_DATA_DIR="$HOME/Documents"
```

## Why Develop This Tool?

When learning English, a vocabulary builder is a very important tool. A good vocabulary builder should include at least the following: **new words, definitions, example sentences, and example sentence translations** . However, maintaining this information manually is very tedious. As a result, most people who have studied English for many years do not have their own vocabulary builder. They often encounter new words while reading, look them up in the dictionary, and then forget them 20 seconds later.

"AI Voc Builder" tries to use the power of AI to make the process of building a vocabulary builder easy and fun, so that everyone can have their own vocabulary builder and quickly expand their vocabulary.
