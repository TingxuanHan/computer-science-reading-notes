# GitHub 公式渲染检查

本检查覆盖《具体数学》和《计算机程序设计艺术》的全部 Markdown 文件。各书的代码与数学实例验证仍由各自的 `verification/verify_all.py` 运行。

## 运行

需要 Python 3.10+、Node.js 22.12+ 和已经登录的 GitHub CLI。首次运行在仓库根目录安装验证依赖：

```sh
npm ci --prefix verification --ignore-scripts
python verification/verify_markdown_math.py --github
```

不带 `--github` 时只在本地检查 TeX 语法和已知禁用命令。带该选项会通过 `gh api markdown` 渲染完整文档，并逐条核对公式数量、顺序及传给公式渲染器的 TeX。该接口不创建文章、提交或其他远端内容；缓存保存在 Git 忽略的 `.math-cache/` 中。需要重新向 GitHub 请求时，移除这个缓存目录后重跑。

结果写入 `math-report.json`。报告含每篇文件的 SHA-256，以便确认检查针对的正文版本。

## 本次修复

2026-10-28 的检查发现两类平台兼容问题：

- 21 篇中有 88 处 `\operatorname`，GitHub 当前会拒绝这个命令。改用 `\mathop{\mathrm{名称}}\nolimits`，保留正体字与算子间距。
- 部分公式紧贴中文时没有被识别，或者 `\{`、`\,`、`\\` 等被 Markdown 提前解释。受影响的行内公式改用带反引号的数学定界符，受影响的独立公式改用 `math` 围栏。

格式修复涉及 100 篇、1,076 处原有公式；示例 Python 代码保持一致。此外，TAOCP §2.5 补明伙伴地址公式的层级范围，以及整池块没有同池伙伴的边界。

## 检查边界与维护

GitHub 于此次检查时加载 MathJax 3.2.0，因此依赖固定到这个版本，并按其页面渲染器配置排除部分扩展。页面样式和平台配置可能变化，本地检查不能取代对实际网页的抽查。公式语法正确也不意味着所有数学证明已经重新审定。

新公式应优先采用 [GitHub 官方说明](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions)中的保护语法。`github_compatible_math` 可用于导入笔记时转换定界符；它只处理数学片段，保留代码和其他正文。
