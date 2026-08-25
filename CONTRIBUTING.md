# 为轻译贡献代码

感谢你愿意改进轻译。提交改动前，请先在 Issue 中说明用户场景，尤其是涉及 Zotero 版本兼容、接口协议或交互方式的变更。

## 本地开发

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3 -m pip install -r requirements-dev.txt
py -3 -m pytest
```

## 提交建议

- 一次提交只解决一个明确问题。
- 新行为应补充测试，界面改动应附截图或短录屏。
- 不要提交 API Key、论文原文、`dist/`、`.codex-tmp/` 或本地配置。
- 保持 Zotero 连接器轻量，LLM 请求和密钥处理应留在桌面端。
- 用户可见文案发生变化时，同步更新中英文 README。

## 报告问题

请包含 Windows 版本、Zotero 版本、轻译版本、复现步骤和经过脱敏的错误信息。不要粘贴 API Key 或未公开论文内容。

