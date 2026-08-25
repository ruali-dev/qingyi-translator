# 论文划词翻译器

一个面向 Windows 和 Zotero 10 的轻量划词翻译工具。翻译请求走你自己的 OpenAI 兼容 LLM 接口。

## 能做什么

- 安装附带的 Zotero 连接器后，在 Zotero PDF 中选中文字，右键点击“翻译选中文字”。
- 在其他 PDF 阅读器中仍可选中文字后按备用快捷键 `Ctrl+Shift+T`。
- 点击翻译后立即显示动态加载卡片；接口错误会原位切换为红色错误提示。
- API Key 使用 Windows DPAPI 加密后保存在当前用户目录，不会写入项目或日志。
- 支持 OpenAI、DeepSeek、Moonshot、通义兼容模式、Ollama 等提供 `/chat/completions` 的接口。

> 桌面程序本身不能修改 Zotero 内部菜单，因此附带一个极薄的 Zotero 连接器。连接器使用官方 Reader 事件缓存当前选区，并通过 `createViewContextMenu` 把翻译命令加入原生右键菜单。

## 快速开始

### 1. 运行桌面程序

如果使用已打包版本，双击 `PaperTranslator.exe`。

从源码运行：

```powershell
py -3 -m pip install -r requirements.txt
py -3 app.py
```

首次启动填写：

- API 地址：例如 `https://api.openai.com/v1`
- API Key
- 模型：例如 `gpt-4.1-mini`
- 目标语言：默认 `简体中文`

点击“保存并隐藏”。程序会留在系统托盘。

### 2. 安装 Zotero 10 连接器

1. 先运行桌面程序。
2. Zotero 中打开“工具 → 插件”。
3. 点击齿轮 → “Install Plugin From File…”。
4. 选择 `dist/paper-translator-zotero.xpi`。
5. 在 PDF 中划词，右键点击“翻译选中文字”。

### 3. 其他 PDF 阅读器

选中文字后按 `Ctrl+Shift+T`。程序会模拟一次 `Ctrl+C` 获取选区，并在鼠标附近弹出翻译。

## 常见接口配置

| 提供方 | API 地址示例 | 模型示例 |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4.1-mini` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Ollama | `http://127.0.0.1:11434/v1` | 本地已安装模型名 |

程序会自动在 API 地址后补 `/chat/completions`。也可以直接填写完整地址。

## 构建

```powershell
py -3 scripts/build.py
```

产物：

- `dist/PaperTranslator.exe`
- `dist/paper-translator-zotero.xpi`

## 本地数据

配置保存在 `%APPDATA%\PaperTranslator\config.json`。API Key 只允许当前 Windows 用户解密。

本地连接器监听 `127.0.0.1:8765`，只接受最大 64 KiB 的 JSON 请求。它不会监听局域网地址。
