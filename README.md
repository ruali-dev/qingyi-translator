<p align="center">
  <img src="assets/readme/hero.svg" alt="轻译：为 Zotero 论文阅读设计的轻量划词翻译工具" width="100%">
</p>

<p align="center">
  <strong>选中，右键，读懂。</strong><br>
  一个面向 Windows 与 Zotero 10 的轻量 LLM 划词翻译工具。
</p>

<p align="center">
  简体中文 · <a href="README.en.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/ruali-dev/qingyi-translator/actions/workflows/ci.yml"><img src="https://github.com/ruali-dev/qingyi-translator/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-5965E8" alt="Apache-2.0 License"></a>
  <a href="https://github.com/ruali-dev/qingyi-translator/releases"><img src="https://img.shields.io/github/v/release/ruali-dev/qingyi-translator?display_name=tag&sort=semver" alt="GitHub Release"></a>
</p>

# 轻译（Qingyi）

轻译把论文翻译放回最自然的阅读动作里：在 Zotero PDF 中选中文字，右键点击“翻译选中文字”，结果卡片会立刻出现。等待期间显示加载动效，接口异常则原位显示红色错误提示，不再让人猜程序是不是卡住了。

翻译请求发送到你配置的 OpenAI 兼容接口；桌面端与 Zotero 连接器都很小，不需要常驻浏览器或完整 Web 框架。

它来自一个很直接的需求：想要词典式的划词体验，又不想为了翻译论文安装一套臃肿的完整词典；同时，希望模型和服务商始终由自己选择。

> 兼容性：Windows · Zotero 10.0.x

## 实机效果

下面是轻译在 Zotero 10 阅读器中的实际运行过程，不是概念图。

**1 — 选中论文内容，在原生右键菜单中点击“翻译选中文字”**

<p align="center">
  <img src="assets/readme/screenshots/context-menu.png" alt="在 Zotero 10 PDF 阅读器中选中文字，并从原生右键菜单启动轻译" width="100%">
</p>

**2 — 翻译窗口立即出现，并明确显示处理状态**

<p align="center">
  <img src="assets/readme/screenshots/translating.png" alt="轻译窗口显示正在翻译和学术术语对齐状态" width="100%">
</p>

**3 — 翻译完成，直接复制结果或继续阅读**

<p align="center">
  <img src="assets/readme/screenshots/translated-paragraph.png" alt="轻译在 Zotero 论文旁显示完整中文翻译结果" width="100%">
</p>

## 亮点

- **原生右键入口**：Zotero PDF 划词后直接在上下文菜单中翻译。
- **即时反馈**：先弹出轻量卡片和加载动效，再异步填入结果。
- **错误可见**：超时、鉴权和网络错误会显示为红色提示气泡。
- **自带接口选择权**：支持 OpenAI、DeepSeek、Moonshot、通义兼容模式、Ollama 等 `/chat/completions` 接口。
- **本地安全存储**：API Key 经 Windows DPAPI 加密，只能由当前 Windows 用户解密。
- **低常驻开销**：Python/Tk 桌面端、Win32 托盘和一个极薄的 Zotero 连接器。
- **备用快捷键**：其他阅读器中可使用 `Ctrl+Shift+T` 翻译当前选区。

## 使用方式

### 1. 运行桌面端

从 [GitHub Releases](https://github.com/ruali-dev/qingyi-translator/releases/latest) 下载并运行 `Qingyi.exe`。首次启动时填写：

- API 地址，例如 `https://api.openai.com/v1`
- API Key
- 模型，例如 `gpt-4.1-mini`
- 目标语言，默认 `简体中文`

点击“保存并隐藏”后，轻译会留在系统托盘。

<p align="center">
  <img src="assets/readme/screenshots/settings.png" alt="轻译模型设置页，API Key 已遮蔽，可测试连接并保存到后台" width="614">
</p>

### 2. 安装 Zotero 连接器

1. 在 Zotero 中打开“工具 → 插件”。
2. 点击齿轮，选择“Install Plugin From File…”。
3. 选择 Release 中的 `qingyi-zotero.xpi`。
4. 打开 PDF，划词并右键点击“翻译选中文字”。

桌面端需要保持运行。若连接器找不到桌面端，Zotero 会给出明确提示。

<p align="center">
  <img src="assets/readme/screenshots/install-connector.png" alt="在 Zotero 10 插件管理器中选择 Install Plugin From File" width="100%">
</p>

安装后确认“轻译 · Qingyi 连接器”处于启用状态：

<p align="center">
  <img src="assets/readme/screenshots/connector-enabled.png" alt="Zotero 10 中已经安装并启用轻译连接器" width="716">
</p>

### 3. 配置兼容接口

| 提供方 | API 地址示例 | 模型示例 |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4.1-mini` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Ollama | `http://127.0.0.1:11434/v1` | 本地已安装的模型名 |

轻译会自动在 API 地址后补上 `/chat/completions`；也可以直接填写完整地址。

## 从源码运行

要求：Windows、Python 3.11+、Zotero 10.0.x。

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3 -m pip install -r requirements-dev.txt
py -3 app.py
```

运行测试与构建：

```powershell
py -3 -m pytest
py -3 scripts/build.py
```

构建产物位于 `dist/`：

- `Qingyi.exe`
- `qingyi-zotero.xpi`

## 项目结构

```text
paper_translator/   Windows 桌面端、翻译客户端、本地服务和 UI
zotero-connector/   Zotero 10 原生右键菜单连接器
scripts/            一键构建脚本
tests/              配置、接口、本地服务和 XPI 元数据测试
assets/icon/         可编辑的品牌图标、PNG 与多尺寸 Windows ICO
assets/readme/      GitHub README 品牌视觉与实机截图
docs/               发布与维护文档
```

Zotero 连接器通过 Reader 事件缓存当前选区，再把文字发送给监听在 `127.0.0.1:8765` 的桌面端。桌面端负责显示状态卡片并调用 LLM，API Key 不会经过连接器。

## 隐私与安全

- 只有选中的文字会发送到你配置的 LLM 服务商。
- API Key 使用 Windows DPAPI 加密，配置保存在 `%APPDATA%\PaperTranslator\config.json`。该旧目录名为兼容已有用户暂时保留。
- 本地服务只监听 `127.0.0.1`，不暴露到局域网；单次 JSON 请求上限为 64 KiB。
- 请在处理敏感或未公开论文前确认所选服务商的数据政策。

## 已知限制

- 目前只支持 Windows。
- Zotero 原生右键连接器目前锁定 Zotero 10.0.x。
- 其他 PDF 阅读器只能使用备用快捷键，无法由独立桌面程序注入原生右键菜单。
- PDF 扫描件需要先完成 OCR，才能获得可翻译的文字选区。

## 参与贡献

欢迎提交问题、交互建议和兼容接口适配。开始修改前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，版本变化记录在 [CHANGELOG.md](CHANGELOG.md)。

如果轻译让你读论文顺手了一点，欢迎给这个仓库点一个 Star。

## 许可证

轻译采用 [Apache License 2.0](LICENSE) 开源。你可以在许可证条款范围内使用、修改和分发本项目。
