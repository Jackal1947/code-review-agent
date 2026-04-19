# Code Review Agent 项目设计文档（基于 LangGraph + GitHub Action）

## 一、项目目标

构建一个基于 LLM 的自动化 Code Review Agent，实现以下能力：

* 在 GitHub PR 创建/更新时自动触发
* 对 PR diff 进行分析并生成 review 建议
* 提供：

  * 高质量 summary（整体评价）
  * 精准 inline comments（逐行评论）
* 具备多角色（Multi-Agent）协作能力
* 控制噪音（减少无效评论）

---

## 二、整体架构

```text
                ┌──────────────┐
                │   PR Diff     │
                └──────┬───────┘
                       ↓
            ┌──────────────────┐
            │   Preprocess     │
            │  - diff切分       │
            │  - 文件分类       │
            └──────┬──────────┘
                   ↓
        ┌──────────────────────┐
        │   Multi Reviewers     │
        │ Bug / Quality / Sec   │
        └──────┬──────────────┘
               ↓
        ┌──────────────────────┐
        │   Cross-check (可选)  │
        └──────┬──────────────┘
               ↓
        ┌──────────────────────┐
        │ Aggregator / Referee │
        └──────┬──────────────┘
               ↓
        ┌──────────────────────┐
        │   Output Formatter    │
        │ summary + inline     │
        └──────────────────────┘
```

---

## 三、核心模块设计

---

### 1. PR Diff 获取

#### 输入来源：

* GitHub Action 触发（pull_request event）

#### 获取方式：

* 使用 GitHub API 获取 PR diff：

```bash
GET /repos/{owner}/{repo}/pulls/{pull_number}
```

#### 输出格式：

```json
{
  "files": [
    {
      "filename": "xxx.ts",
      "patch": "...diff内容..."
    }
  ]
}
```

---

### 2. Preprocess 模块

#### 2.1 Diff 切分

目标：控制单次 LLM 输入大小

规则：

* 按文件拆分
* 每个文件按 hunk 拆分
* 每块建议 ≤ 300 行

输出：

```json
[
  {
    "file": "user.ts",
    "chunk_id": 1,
    "code": "..."
  }
]
```

---

#### 2.2 文件分类

简单规则：

| 类型       | 判断              |
| -------- | --------------- |
| backend  | .ts / .py / .go |
| frontend | .tsx / .jsx     |
| test     | test / spec     |
| config   | json / yaml     |

输出：

```json
{
  "file": "user.ts",
  "type": "backend"
}
```

---

### 3. Multi Reviewers（LangGraph 核心）

采用 LangGraph 构建 DAG：

```text
          ┌──────────────┐
          │  Bug Agent   │
          └──────┬───────┘
                 ↓
          ┌──────────────┐
          │ Quality Agent│
          └──────┬───────┘
                 ↓
          ┌──────────────┐
          │ Security     │
          └──────────────┘
```

---

#### 3.1 Bug Hunter Agent

职责：

* null / undefined
* 边界条件
* 异常处理
* 并发问题

Prompt 要求：

* 只关注 bug
* 忽略 style

---

#### 3.2 Code Quality Agent

职责：

* 可读性
* 重复代码
* 设计问题

---

#### 3.3 Security Agent

职责：

* SQL 注入
* 权限校验
* 敏感数据泄露

---

#### 3.4 输出格式（统一）

所有 agent 必须输出：

```json
{
  "issues": [
    {
      "type": "bug | quality | security",
      "severity": "high | medium | low",
      "confidence": 0-100,
      "file": "user.ts",
      "line": 42,
      "description": "...",
      "suggestion": "..."
    }
  ]
}
```

---

### 4. Cross-check 模块（可选）

#### 目的：

降低误报

#### 实现：

* 将 Agent A 的 issue 发送给 Agent B
* 判断是否同意

输入：

```json
{
  "issue": {...}
}
```

输出：

```json
{
  "agree": true,
  "confidence": 80
}
```

#### 规则：

```text
如果 ≥2 agent 同意 → 保留
否则 → 降权或删除
```

---

### 5. Aggregator / Referee 模块

核心模块，必须实现。

---

#### 5.1 去重

方法：

* 简单：文本相似度
* 推荐：embedding 相似度

---

#### 5.2 合并 Issue

多个 agent 提到同一问题 → 合并

---

#### 5.3 排序

优先级计算：

```text
priority = 
  severity权重
+ confidence
+ agent投票数
```

---

#### 5.4 Summary 生成

输出：

```text
## Summary
- 1 high issue
- 2 medium issues

## Key Issues
- xxx
- xxx
```

---

### 6. Output Formatter

#### 6.1 PR Summary Comment

格式：

```markdown
## 🤖 AI Code Review Summary

### Overview
- 1 high risk issue
- 2 medium issues

### Key Findings
1. ...
2. ...
```

---

#### 6.2 Inline Comments

规则：

* 只输出：

  * high
  * medium
* low 不输出（减少噪音）

---

## 四、LangGraph 实现建议

---

### 状态定义（State）

```python
class ReviewState(TypedDict):
    diff_chunks: List
    issues: List
    final_issues: List
```

---

### 节点定义

* preprocess_node
* bug_agent_node
* quality_agent_node
* security_agent_node
* cross_check_node（可选）
* aggregator_node
* formatter_node

---

### DAG 流程

```text
preprocess
   ↓
multi agents（并行）
   ↓
cross-check（可选）
   ↓
aggregator
   ↓
formatter
```

---

## 五、GitHub Action 集成

---

### 1. 触发条件

```yaml
on:
  pull_request:
    types: [opened, synchronize]
```

---

### 2. 执行流程

1. 获取 PR diff
2. 调用 LangGraph pipeline
3. 获取 review 结果
4. 调用 GitHub API 发布评论

---

### 3. 评论方式

#### Summary Comment

```bash
POST /repos/{owner}/{repo}/issues/{issue_number}/comments
```

---

#### Inline Comment

```bash
POST /repos/{owner}/{repo}/pulls/{pull_number}/comments
```

---

## 六、优化建议（后续迭代）

---

### 1. 成本优化

* 小 PR → 单 agent
* 大 PR → 多 agent

---

### 2. 上下文增强（Retrieval）

* 引入 embedding
* 查找相关代码

---

### 3. 历史学习

* 记录：

  * 被采纳的评论
  * 被忽略的评论

---

### 4. 自动修复建议

* 输出 patch / code snippet

---

## 七、开发优先级

---

### Phase 1（MVP）

* 单 agent（Bug）
* 输出 summary

---

### Phase 2

* 多 agent
* aggregation

---

### Phase 3

* cross-check
* retrieval

---

## 八、核心设计原则

---

### 1. 少而精

* 控制评论数量
* 提高命中率

---

### 2. 强约束输出

* 必须 JSON
* 不允许自由文本

---

### 3. 可扩展

* agent 可插拔
* DAG 可扩展

---

## 九、最终目标

构建一个：

> **低成本、高信噪比、接近真实工程师的 Code Review Agent**