* # Code Review Agent

  ## 1. 核心能力 (Core Capabilities)

  该 Code Review Agent 应该具有以下能力：

  ### 1.1 代码质量与规范检查
  * **基础规范**：自动检查代码风格（如缩进、命名规范）、代码格式，确保团队代码风格统一。
  * **代码异味**：识别过长函数、过高的代码复杂度、重复代码、不当的注释等，提升代码的可读性和可维护性。
  * **最佳实践**：检查代码是否遵循了 SOLID 原则、设计模式是否被正确使用等。

  ### 1.2 安全漏洞扫描
  * **常见漏洞**：识别 SQL 注入、XSS 攻击、敏感信息（如 API 密钥）硬编码、权限控制不当等安全风险。
  * **依赖检查**：分析项目依赖，检查是否存在已知安全漏洞的第三方库。

  ### 1.3 性能与可靠性分析
  * **性能瓶颈**：发现潜在的性能问题，如 N+1 查询、不必要的循环、内存泄漏风险、不合理的缓存策略等。
  * **逻辑错误**：检查边界条件、空值处理、异常处理是否完善，避免程序在特定场景下崩溃。

  ### 1.4 业务逻辑与语义理解 (高级能力)
  这是区分优秀 Agent 与普通工具的关键。Agent 需要理解代码变更背后的业务意图。
  * **语义分析**：能够识别出那些“技术上正确，但业务上错误”的变更。例如，一个折扣规则的修改虽然通过了所有单元测试，但可能无意中移除了利润率保护机制。
  * **上下文感知**：结合整个项目的代码库和历史提交记录进行分析，而不是孤立地看待本次变更。这能帮助它发现跨模块的逻辑不一致问题。

  ### 1.5 核心能力与上下文增强 (Capabilities & Context Layer)
  * **多维规则检查**：涵盖基础代码规范统一、代码异味识别、SOLID 原则与最佳实践的落地。
  * **深层业务语义理解**：识别“技术正确但业务错误”的变更（例如误删利润保护机制），避免盲目重构。
  * **跨模块上下文感知**：结合整个代码库和 Git 历史提交记录进行宏观分析，防止孤立看待变更导致模块间逻辑断裂。
  * **RAG (检索增强生成) 支持**：连接企业内部知识库、历史 Issue、Confluence 文档和过往修复案例。遇到相似问题时，输出符合团队历史习惯的精准建议。

  ---

  ## 2. 交互入口层 (Interactive Entry Layer)

  提供多维度的接入方式，覆盖从本地开发到持续集成的全生命周期。

  * **CLI (命令行工具)**
    * **命令**：`guardian scan ./src --lang=ts`
    * **场景**：开发者在本地终端快速检查当前项目或单文件的代码异味。
  * **SDK (核心代码库)**
    * **功能**：`import { scanCode } from 'guardian-sdk'`
    * **场景**：无缝集成 CI/CD Pipeline (如 GitHub Actions/GitLab CI)。设置质量卡点，若综合评分低于 80 分则自动阻断构建。

  ---

  ## 3. 内部架构 (Internal Architecture)

  ### 🏗️ 核心架构：1+N 模式

在这个模式中，**1个主控Agent（Manager/Orchestrator）** 负责统筹和决策，**N个专项Agent（Subagents）** 负责具体的执行和深度分析。

#### 1. 主控 Agent (The Lead)

- **角色：** 审查指挥官、流程编排者。
- **职责：**
    - **接收请求：** 接收用户的审查请求（如一个PR链接）。
    - **任务拆解：** 分析代码变更的规模，决定需要调用哪些专项Agent（例如，涉及支付模块时，必须调用安全Agent）。
    - **信息聚合：** 收集所有专项Agent的报告，去重、合并冲突，生成最终的审查总结。
    - **决策：** 决定是“批准合并”、“请求变更”还是“需要人工介入”。

#### 2. 专项执行 Agent (The Specialists)

共配置 **5个专项Agent**，各司其职：

| Agent 角色 | 核心职责 | 何时调用 |
| :--- | :--- | :--- |
| **🕵️ 上下文探索者**<br>(Investigator) | 扫描代码库，分析受影响的模块依赖和调用链路，为其他 Agent 提供上下文 | 始终调用 |
| **🛡️ 安全审计员**<br>(Security Auditor) | 深度安全扫描：SQL注入、XSS、权限漏洞、敏感信息泄露、依赖漏洞 | 始终调用 |
| **📝 质量审查员**<br>(Quality Engineer) | 代码规范、复杂度、SOLID原则、代码异味、逻辑错误 | 始终调用 |
| **⚡ 性能审查员**<br>(Performance Engineer) | N+1查询、内存泄漏、并发问题、缓存策略、不合理算法 | 按需调用（涉及数据处理/IO时） |
| **🔧 修复工程师**<br>(Fixer) | 接收其他 Agent 发现的问题，生成具体的修复代码示例 | 发现问题时调用 |

---

### 3.1 Agent 协作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                         Manager (主控)                          │
│  1. 接收 PR Diff，分析变更范围                                    │
│  2. 决定调用哪些 Specialist                                      │
│  3. 汇总结果，生成最终报告                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     共享上下文 (Context)                         │
│  • PR 元信息（标题、描述、变更文件列表）                          │
│  • 代码 Diff 内容                                                │
│  • Investigator 生成的依赖图和影响分析                            │
│  • 历史审查记录（相似问题参考）                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
      ┌───────────┐ ┌───────────┐ ┌───────────┐
      │ Security  │ │ Quality   │ │Performance│
      │ Auditor   │ │ Engineer  │ │ Engineer  │
      └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
            │            │            │
            └────────────┼────────────┘
                         │ 并行执行
                         ▼
              ┌───────────────────────┐
              │    Fixer (按需)        │
              │  生成修复代码示例       │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Manager 汇总报告    │
              │   评分 + 合并建议      │
              └───────────────────────┘
```

**执行规则：**
- Investigator **始终先执行**，为其他 Agent 提供上下文
- Security、Quality、Performance **并行执行**（互相独立）
- Fixer 在专项 Agent 完成后**按需调用**（只为严重/警告级别问题生成修复）
- Manager 收集所有结果，去重、排序、生成最终报告

  ### 3.2 动态提示词引擎 (Prompt Engine Layer)

  通过分层与缓存机制，在保证 AI 输出质量的同时控制 Token 成本。

  * **动态拼装策略**
    * **基础层 (Base)**：设定核心 Persona（资深全栈架构师，精通设计模式与 SOLID 原则）。
    * **语言层 (Language)**：根据文件后缀动态加载专属规范。例如 `.py` 加载 Python 最佳实践，`.ts` 加载 TypeScript 严格模式规范。
    * **场景层 (Scenario)**：根据意图加载策略。`scan` 模式加载“找茬与缺陷发现”提示词，`refactor` 模式加载“重构并保证逻辑等价性”提示词。
  * **缓存控制**
    * 将“基础层”和稳定的“语言层”系统提示词进行缓存，降低高频调用的延迟和 API 成本。

  ---

  ## 4. 输出规范 (Output Specification)

          # 📋 代码审查报告：[PR编号/功能名称]

        > **生成时间:** 202X-XX-XX HH:MM:SS
        > **审查 Agent:** CodeReview-Bot v2.0
        > **关联分支:** `feature/new-payment-gateway` -> `main`

        ---

        ## 1. 📊 审查摘要

        这里是给管理者或资深开发者看的“一眼概览”，不需要看细节就能知道这次提交的质量。

        - **总体评分:** **B+** (良好，但有少量建议)
        - **合并建议:** ✅ **建议合并** (或 🔴 阻断 / 🟡 需人工复核)
        - **关键统计:**
            - 变更文件数: 12
            - 代码行数变更: +450 / -120
            - 发现问题总数: 8 (🔴 严重: 0 | 🟡 警告: 3 | 🟢 建议: 5)

        ---

        ## 2. 🛡️ 安全与合规性审计

        由“安全审计员 Agent”生成的深度分析，通常放在最前面以示重视。

        ### 依赖检查
        - [x] 无已知漏洞的第三方库更新
        - [ ] **警告:** 引入了 `lib-xyz@1.0.2`，该版本存在 CVE-2023-XXXX 风险，建议升级至 1.0.3。

        ### 敏感信息扫描
        - **检测结果:** 未发现硬编码的 API Key 或密码。

        ### 权限与注入风险
        - **文件:** `src/auth/login.py`
        - **风险:** 潜在的 SQL 注入风险。
        - **详情:** 用户输入 `username` 未经过参数化处理直接拼接。

        ---

        ## 3. 🚀 性能与架构分析

        由“架构与探索者”及“性能官 Agent”生成的内容。

        ### 复杂度与性能瓶颈
        - **N+1 查询检测:** 在 `UserService.getUsers()` 循环中调用了 `OrderRepository.findById()`，建议在 Controller 层使用 `JOIN FETCH` 一次性获取。
        - **内存风险:** 检测到在 `DataProcessor` 中一次性加载了全量文件到内存，对于大文件可能导致 OOM。

        ### 架构一致性
        - **模块依赖:** 警告：`UI Layer` 直接引用了 `Database Layer`，违反了分层架构原则。

        ---

        ## 4. 🐞 逻辑错误与代码质量

        这是文档的主体部分，列出具体的代码问题。建议使用表格形式以便阅读。

        | 严重程度 | 文件路径 | 行号 | 问题描述 | 建议修复方案 |
        | :--- | :--- | :--- | :--- | :--- |
        | 🟡 警告 | `utils/date.py` | 45 | 未处理时区转换，可能导致跨天数据错误 | 使用 `ZonedDateTime` 替代 `Date` |
        | 🟢 建议 | `style.css` | 12 | 魔法数字 `100px`，建议提取为变量 | 定义 `--header-height: 100px` |
        | 🟡 警告 | `OrderService.java` | 88 | 事务注解 `@Transactional` 范围过大 | 缩小事务范围至数据库操作块 |

        ---

        ## 5. 🛠️ 自动化修复与补丁

        由”修复工程师 Agent”生成的内容。只为 **🔴 严重** 和 **🟡 警告** 级别的问题生成修复代码。

        ### 建议修复 1: SQL 注入漏洞
        **严重程度:** 🔴 严重
        **位置:** `src/auth/login.py:45`

        **原代码:**
        ```python
        query = f”SELECT * FROM users WHERE username = '{username}'”
        cursor.execute(query)
        ```

        **修复后:**
        ```python
        query = “SELECT * FROM users WHERE username = %s”
        cursor.execute(query, (username,))
        ```

        ---

        ### 建议修复 2: 空指针异常
        **严重程度:** 🟡 警告
        **位置:** `src/main/java/User.java:88`

        **原代码:**
        ```java
        return user.getAddress().getCity();
        ```

        **修复后:**
        ```java
        return Optional.ofNullable(user)
            .map(User::getAddress)
            .map(Address::getCity)
            .orElse(“Unknown”);
        ```

        ---

        ### 建议修复 3: N+1 查询
        **严重程度:** 🟡 警告
        **位置:** `src/service/OrderService.java:56-62`

        **原代码:**
        ```java
        for (User user : users) {
            List<Order> orders = orderRepository.findByUserId(user.getId());
            user.setOrders(orders);
        }
        ```

        **修复后:**
        ```java
        Set<Long> userIds = users.stream().map(User::getId).collect(Collectors.toSet());
        Map<Long, List<Order>> ordersMap = orderRepository.findByUserIds(userIds)
            .stream()
            .collect(Collectors.groupingBy(Order::getUserId));
        users.forEach(user -> user.setOrders(ordersMap.getOrDefault(user.getId(), Collections.emptyList())));
        ```

        ---

        ### 建议修复 4: 事务范围过大
        **严重程度:** 🟢 建议
        **位置:** `src/service/OrderService.java:88`

        **原代码:**
        ```java
        @Transactional
        public void processOrder(Order order) {
            validateOrder(order);        // ← 无需事务
            saveOrder(order);            // ← 需要事务
            sendNotification(order);     // ← 无需事务
        }
        ```

        **修复后:**
        ```java
        public void processOrder(Order order) {
            validateOrder(order);
            transactionTemplate.execute(status -> {
                saveOrder(order);
                return null;
            });
            sendNotification(order);
        }
        ```