# Reference

`Reference` 是一个面向学术论文 Word 文档的 Codex Skill。上传正文 `.docx` 和期刊引用格式要求后，它可以：

- 提取放在相关句子后的完整文献信息；
- 按标题去重并批量匹配 Crossref；
- 将完整文献替换为指定格式的正文引用；
- 在文末生成参考文献；
- 使用 Word 书签和内部超链接，将正文引用链接到对应的文末条目；
- 仅在格式明确要求期刊名缩写时查询 ISSN LTWA；
- 保留无法唯一匹配的原始文献，避免猜测和误删。

## 使用方法

上传 Word 正文和引用格式要求，然后输入：

```text
使用 Reference 按指定格式处理这篇 Word 正文，生成相互链接的正文引用和文末参考文献。
```

默认只返回处理后的 `.docx` 和简短统计。需要 Excel 或元数据表时，请在请求中明确说明。

## GitHub 目录

```text
.
├── README.md
├── LICENSE
└── skills/
    └── reference/
        ├── SKILL.md
        ├── agents/
        ├── assets/
        ├── references/
        └── scripts/
```

在 GitHub 仓库中保留以上目录结构。安装时选择 `skills/reference` 目录。

## 匹配规则

- 每个去重后的标题只查询一次 Crossref。
- 仅接受唯一的规范化精确标题匹配。
- 不使用 DOI 页面、出版社网站、Google Scholar 或其他数据库进行二次验证。
- Crossref 无唯一匹配时保留原始内容并标记为未解决。

## License

MIT
