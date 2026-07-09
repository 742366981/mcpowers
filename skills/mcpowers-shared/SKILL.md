---
name: mcpowers-shared
description: |
  **mcpowers 技术规范库入口**

  提供 21 个技术规范文件（API/数据库/缓存/Git/测试/部署等）。
  当需要参考具体技术规范时触发此 skill。

  **使用方式**：通过 mcpowers-spec-index 查表定位 → 按需 Read 规范文件
  **禁止**：一次性 Read 所有规范（会爆上下文）

  规范分类：
  - 通用规范（所有项目必须）：Git规范、代码规范、开发环境规范、设计规范、文档编写规范、细节记录规范
  - 技术锁规范（按需读取）：API规范、数据库规范、缓存规范、部署规范、测试规范、Flask后端规范、Vue前端规范、爬虫规范
---

# mcpowers-shared · 规范库入口

> 这是**入口 skill**，不是规范本体。规范本体在 `docs/技术规范/` 下。

## 使用方式（3 步）

### 1. 查表定位
Read `mcpowers-spec-index/SKILL.md`，根据"做什么 → 读哪个规范"查表。

### 2. 按需加载
根据查表结果，Read 对应的 `docs/技术规范/xxx规范.md`。

### 3. 引用而非复制
规范加载后，**只引用关键约束**到对话中，不要把整个规范内容粘贴出来。

## 规范清单（21 个）

详见 `mcpowers-spec-index/SKILL.md` 的"规范清单"段。

## 触发场景

- ✅ "写 API 接口前，先看下 API 规范"
- ✅ "这个 SQL 写法符合数据库规范吗"
- ✅ "Git commit 消息格式怎么写"
- ❌ "帮我写个登录功能"（应触发 `mcpowers-feat`，不是本 skill）
