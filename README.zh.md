# HKBS 中文圣经抽取工具

[English](README.md) | 中文

本仓库包含一个针对 HKBS 在线圣经网页的小型抽取工具，以及静态阅读器所使用的按章节切分的 JSON 数据。

新标点和合本有两个路径：

```text
https://rcuv.hkbs.org.hk/CUNP1/GEN/1/
https://rcuv.hkbs.org.hk/CUNP1s/GEN/1/
```

`CUNP1` 为繁体中文，`CUNP1s` 为简体中文。

和合本2010（和修）（神版）有两个路径：

```text
https://rcuv.hkbs.org.hk/RCUV1/GEN/1/
https://rcuv.hkbs.org.hk/RCUV1s/GEN/1/
```

`RCUV1` 为繁体中文，`RCUV1s` 为简体中文。两条路径对应的是「和合本2010（和修）（神版）」的文本，相关的 `RCUV2` 路径为「上帝版」，未包含在本数据集中。

## 数据状态

截至 2026-05-17 的当前部署状态：

- 静态网页阅读器中已支持 CUNP 与 RCUV 神版作为可切换的译本。
- RCUV 神版创世记 28 章的段落标题已修正：`以扫另娶一妻` 归属于创世记 28:6，与 HKBS 源页一致。
- 抽取器通过 `verse_end` 字段保留源端的合并经节范围。
- 抽取器通过 `sequence` 字段保留源端的重复经节编号。
- 不会把 HKBS 中出现在经节中段的标题提升进 `section_headings`。例如 CUNP 哥林多前书 12:31 之后出现的源标题 `爱` 不会渲染在 12:31 之前，经文文本保持完整。
- 通过 `--cache-source` 和 `--from-cache` 支持源 HTML 缓存，本地调整解析器后无需重新从 HKBS 下载即可重跑。
- 静态网页阅读器支持键盘切章：← 上一章，→ 下一章，可跨书自动衔接。
- 本仓库提供英文 README（`README.md`）与中文 README（`README.zh.md`）两份文档，文件顶部互相链接。修改项目文档时请同步更新两份文件。

`data/cunp` 目录包含两种字体的完整逐章抽取：

- `traditional`：1189 个章节 JSON 文件
- `simplified`：1189 个章节 JSON 文件
- 合计：2378 个章节 JSON 文件

2026-05-17 的校验结果：无缺失章节、无非法 JSON 文件、无空经节数组、无元数据不一致、首节解析起点均为第 1 节。CUNP 数据已用当前解析器从 HKBS 源页重新同步，修正了章节标题，并恢复了旧抽取流程漏掉的合并经节范围。

`data/rcuv-shen` 目录包含「和合本2010（和修）（神版）」两种字体的完整逐章抽取：

- `traditional`：1189 个章节 JSON 文件
- `simplified`：1189 个章节 JSON 文件
- 合计：2378 个章节 JSON 文件

2026-05-17 的校验结果：无缺失章节、无非法 JSON 文件、无空经节数组、无元数据不一致、首节解析起点均为第 1 节。

修改抽取器逻辑或 `data/` 下的文件后，运行校验器：

```bash
python3 scripts/verify_bible_data.py data/cunp data/rcuv-shen
```

校验器会检查章节覆盖度、JSON 合法性、路径与元数据一致性、经节数组非空、经节排序、合并经节范围，以及源端跳过或重复的经节编号。

## JSON 结构

每个章节 JSON 文件的顶层结构如下：

```json
{
  "translation": "cunp",
  "version": "CUNP1s",
  "version_name": "新标点和合本",
  "script": "simplified",
  "book_code": "GEN",
  "book_name": "创世记",
  "chapter": 1,
  "heading": "神的创造",
  "source_url": "https://rcuv.hkbs.org.hk/CUNP1s/GEN/1/",
  "verses": []
}
```

HKBS 源端的合并经节范围用范围首节上的 `verse_end` 表示：

```json
{
  "verse": 1,
  "verse_end": 2,
  "text": "...",
  "notes": []
}
```

单节经文省略 `verse_end`。源同步后仍未出现 `verse_end` 的编号空缺，属于源端被省略的经节编号，并非推断出来的范围。

若源端某章存在重复的经节编号，重复项会保留原始 `verse` 数值，并通过从 1 开始的 `sequence` 区分。这样既能保留源引用，又能通过 `book_code/chapter/verse/sequence` 实现唯一定位：

```json
{
  "verse": 9,
  "sequence": 1,
  "section_headings": ["．有些古卷有下列结语．", "短结语："],
  "text": "...",
  "notes": []
}
```

`section_headings` 保留紧贴某节经文之前出现的源标题，例如 RCUV 神版马可福音 16 章的短结语与长结语。出现在经文已经开始之后的标题被视为下一段落的标题，不挂在当前节上。

## 使用方法

抓取一节 CUNP：

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1
```

默认会同时抓取繁体与简体。如需只抓其中一种：

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1 --script traditional
python3 scripts/extract_hkbs_cunp.py --book GEN --chapter 1 --script simplified
```

抓取一章 RCUV 神版：

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --book GEN --chapter 1
```

把一整卷 CUNP 抓为按章 JSON 文件：

```bash
python3 scripts/extract_hkbs_cunp.py --book GEN --output-dir data/cunp
```

抓取一整卷 RCUV 神版：

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --book GEN --output-dir data/rcuv-shen
```

输出按字体分目录存放：

```text
data/cunp/traditional/GEN/001.json
data/cunp/simplified/GEN/001.json
data/rcuv-shen/traditional/GEN/001.json
data/rcuv-shen/simplified/GEN/001.json
```

抓取全本 CUNP：

```bash
python3 scripts/extract_hkbs_cunp.py --all --output-dir data/cunp --delay 1.5
```

抓取全本 RCUV 神版：

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --all --output-dir data/rcuv-shen --workers 12 --delay 0.05
```

抓取时同步保存源 HTML：

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --all --output-dir data/rcuv-shen --workers 12 --delay 0.05 --force --cache-source
```

当源 HTML 已经缓存在 `.cache/hkbs-source` 下后，调整解析器后可以本地重跑而无需再次访问 HKBS：

```bash
python3 scripts/extract_hkbs_cunp.py --translation rcuv-shen --all --output-dir data/rcuv-shen --workers 12 --force --from-cache
```

源缓存仅在本地，不会被 git 跟踪。只有在需要刷新 HKBS 源页面时才使用 `--cache-source`。

如需输出 JSON Lines 而非按章嵌套 JSON：

```bash
python3 scripts/extract_hkbs_cunp.py --book PHP --chapter 1 --format jsonl
```

## 静态网页阅读器

本仓库在 `web/` 下包含一个静态圣经阅读 / 查询工具。

线上地址：

```text
https://zhuguangjun2002.github.io/hkbs-openai/
```

功能特性：

- 按书卷与章号阅读
- 在 CUNP 与 RCUV 神版之间切换译本
- 简繁体切换
- 浏览器端数据来源于 `data/cunp` 与 `data/rcuv-shen` 的打包
- 简体 / 繁体全文客户端检索
- 跨字体高亮，例如阅读简体时检索 `亞歷山大`
- 检索范围：全本、旧约、新约或当前书卷
- 引用直跳，例如 `约3:16`、`約3:16`、`约3:16-18`、`JHN3:16`
- 进入检索结果后高亮检索关键词
- 键盘导航：← 上一章，→ 下一章
- 亮色 / 暗色主题

修改 `data/cunp` 或 `data/rcuv-shen` 下的文件后，重建浏览器数据包：

```bash
python3 scripts/build_web_data.py
```

本地预览：

```bash
python3 -m http.server 8000
```

然后打开：

```text
http://localhost:8000/web/
```

站点由 `.github/workflows/pages.yml` 通过 GitHub Pages 部署。工作流直接发布 `web/` 目录，不需要 npm 安装或构建步骤。

下一步推荐的网页任务：把译本、字体、经文位置和检索状态加到 URL 上，让分享出去的链接能直接重现阅读器的状态。

## 版权

在大规模下载、存储或再分发文本之前，请确认 HKBS 的授权与使用条款。本脚本仅作为抽取工具供经授权或个人研究使用，本身不包含圣经文本。
