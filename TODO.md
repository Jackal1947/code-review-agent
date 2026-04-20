# Code Review Agent 改进计划

## 一、完整项目架构理解

### 问题
当前只审查 diff 片段，缺乏项目级上下文，无法判断模块边界、依赖关系。

### 方案：预处理分层 + 项目知识库

**预处理分层**：
- 硬编码层：DiffParser、FileClassifier、StructureScanner
- 智能层（子Agent）：ProjectArchitect 理解模块关系、业务含义

**项目知识库结构**：
```
project_context/
├── structure.json      # 项目文件树结构
├── dependencies.json   # 模块依赖关系
├── api_contracts.json  # 接口定义
└── architecture.md     # 架构说明文档
```

### TODO
- [ ] 新增 `StructureScanner` 硬编码模块，扫描项目结构
- [ ] 新增 `ProjectArchitect` 子 Agent，理解模块关系
- [ ] 修改预处理节点，注入项目上下文

---

## 二、团队自定义代码规范

### 问题
无法自定义团队代码规范，如命名规则、禁止使用的 API 等。

### 方案：规则配置中心

**规则配置结构**：
```
config/
└── code_rules/
    ├── _default.yaml      # 默认规则
    └── {team_name}.yaml   # 团队自定义规则
```

**规则格式示例**：
```yaml
rules:
  - id: "java-001"
    severity: "high"
    pattern: "System\\.out\\.print"
    message: "禁止使用 System.out.print，应使用日志框架"
```

**协作方式**：
- Pattern 预检：硬编码快速匹配
- Prompt 注入：随系统提示词传给 Agent

### TODO
- [ ] 设计规则配置格式（YAML/JSON）
- [ ] 新增 `RuleEngine` 加载和匹配模块
- [ ] 实现 Prompt 注入机制
- [ ] 支持 `.reviewrc.yaml` 项目级配置

---

## 三、易错文档 + 历史学习

### 问题
同一团队反复出现的问题未被记住，无法从历史人工 Review 中学习。

### 方案：知识沉淀系统

**知识库结构**：
```
knowledge_base/
├── common_mistakes/        # 易错文档
│   ├── java.md
│   ├── python.md
│   └── security.md
├── human_reviews/         # 历史人工 Review
│   └── {year}-{month}/
│       └── pr_{number}_{type}.md
└── learned_patterns.json  # AI 学习总结
```

**实施阶段**：
- 阶段1：简单文件存储（按时间/文件类型过滤）
- 阶段2：关键词/元数据检索
- 阶段3：轻量级向量检索（Chroma/Milvus）
- 阶段4：完整 RAG 架构

**知识提取流程**：
```
人工 Review 完成 → KnowledgeExtractor → 更新易错文档 + 存入历史库
                                              ↓
                            下次审查时加载相关历史作为上下文
```

### TODO
- [ ] 新增 `KnowledgeExtractor` 节点
- [ ] 新增 `KnowledgeBase` 管理模块
- [ ] 设计知识提取 Prompt 模板
- [ ] 阶段1：简单文件存储实现
- [ ] 阶段2：关键词检索实现
- [ ] 阶段3：向量检索实现（如需要）

---

## 实施顺序

| 顺序 | 改进点 | 理由 |
|------|--------|------|
| 1 | 团队自定义代码规范 | 改动最小，立即可用 |
| 2 | 完整项目架构理解 | 为后续提供上下文基础 |
| 3 | 易错文档 + 历史学习 | 依赖前两者，跑起来后迭代 |
