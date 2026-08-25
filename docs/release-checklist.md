# GitHub 首次发布清单

建议仓库名：`qingyi-translator`。

## 公开仓库前

- [x] 选择 Apache-2.0 开源许可证并添加 `LICENSE`。
- [x] 把 Zotero 连接器的 `update_url` 替换为仓库中的真实 `updates.json` 地址。
- [x] 在 README 中补充真实的 GitHub Releases 链接和仓库徽章。
- [ ] 检查 Git 历史中没有 API Key、论文原文和个人配置。
- [ ] 确认项目名称、简介与 Topics：`zotero`、`translation`、`llm`、`pdf`、`windows`。

## 创建 Release

- [ ] 更新 `paper_translator/__init__.py`、`pyproject.toml` 与 Zotero manifest 中的版本号。
- [ ] 更新 `CHANGELOG.md`，把 Unreleased 内容归入新版本。
- [ ] 运行 `py -3 -m pytest`。
- [ ] 运行 `py -3 scripts/build.py`。
- [ ] 在一台没有开发环境的 Windows 机器或虚拟机中试运行 `Qingyi.exe`。
- [ ] 在 Zotero 10.0.x 中重新安装并验证 `qingyi-zotero.xpi`。
- [ ] 上传两个构建产物，并附上 SHA-256 校验值。

## 发布后

- [ ] 验证 README 的下载链接。
- [ ] 验证全新安装、首次配置、加载状态、成功状态与错误状态。
- [ ] 记录已知限制，不承诺尚未验证的 Zotero 或 Windows 版本。
