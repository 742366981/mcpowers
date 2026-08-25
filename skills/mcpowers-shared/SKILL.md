---
name: mcpowers-shared
description: "规范库入口 / 技术规范按需加载。覆盖 API、数据库、缓存、Git、测试、部署、Flask、FastAPI、Vue、爬虫等 33 个技术规范（含 v2.14.0 爬虫拆分 7 册、v2.31.0 Swagger 字段契约、v4.6.0 FastAPI 后端规范）；通过 mcpowers-spec-index 查表后定向 Read，避免一次加载全部规范。边界：写功能→mcpowers-feat；只查规范→本技能。"
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

## 规范清单（33 个，含 v2.14.0 爬虫拆分 7 册 + v4.6.0 FastAPI 后端规范）

详见 `mcpowers-spec-index/SKILL.md` 的"规范清单"段。

## 触发场景

- ✅ "写 API 接口前，先看下 API 规范"
- ✅ "这个 SQL 写法符合数据库规范吗"
- ✅ "Git commit 消息格式怎么写"
- ❌ "帮我写个登录功能"（应触发 `mcpowers-feat`，不是本 skill）
