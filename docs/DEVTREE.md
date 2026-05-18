# 开发树

## 分类图例

| 图标 | 类型 | 说明                       |
| ---- | ---- | -------------------------- |
| 🌱   | 初建 | 某功能域首次从零建立       |
| ✨   | 功能 | 扩展用户可感知的能力       |
| 🐛   | 修复 | 纠正缺陷或回归             |
| 🏗️   | 重构 | 内部结构改善，用户行为不变 |
| 📦   | 工程 | 打包/CI/分发/工具链        |
| 🔬   | 探索 | 调研，可能被搁置           |

## 可视化

```mermaid
%%{init: {'flowchart': {'rankSpacing': 30, 'nodeSpacing': 20}}}%%
graph TD
  classDef genesis  fill:#d4edda,stroke:#28a745,color:#155724,font-weight:bold
  classDef feature  fill:#cce5ff,stroke:#0d6efd,color:#003d8f,font-weight:bold
  classDef bugfix   fill:#f8d7da,stroke:#dc3545,color:#721c24,font-weight:bold
  classDef refactor fill:#fff3cd,stroke:#ffc107,color:#664d03,font-weight:bold
  classDef infra    fill:#e2d9f3,stroke:#6f42c1,color:#3d1a78,font-weight:bold
  classDef research fill:#e2e3e5,stroke:#6c757d,color:#383d41,font-weight:bold
  classDef epic     fill:#f8f9fa,stroke:#adb5bd,color:#495057,font-weight:bold,font-size:15px

  ROOT["tlou-dance"]:::epic
  ROOT --> ea["资产准备"]:::epic
  ea --> ea1

  subgraph ea1["🔄 角色模型提取与标准化"]
    direction TB
    N0["🔬 0 · 游戏人物模型提取调研"]:::research
    N2["🔬 2 · 贴图集成进 normalized FBX"]:::research
    N0 ~~~ N2
  end
```

## 节点索引

> 最后更新：2026-05-18 | 共 2 轮

| #   | 名称                      | 类型    | 所属 Epic            | 一句话描述                                                                       |
| --- | ------------------------- | ------- | -------------------- | -------------------------------------------------------------------------------- |
| 0   | 游戏人物模型提取调研      | 🔬 探索 | 角色模型提取与标准化 | 三人 fan-port 模型 + Mixamo 65-bone 标准骨架；灰模成品（无贴图）就绪             |
| 2   | 贴图集成进 normalized FBX | 🔬 探索 | 角色模型提取与标准化 | spike 失败：pipeline + 41 单测就位，Blender 4.5 不解 TLOU DDS 子格式，未交付贴图 |

## Epic 结构

### 资产准备

#### 角色模型提取与标准化

- 状态：进行中
- 轮次：0, 2

> round 0 spike 已交付灰模成品（mesh + Mixamo 65-bone 标准骨架）；round 2 尝试集成贴图未达成（Blender 4.5 不解 TLOU 的 DDS 子格式），spike 失败但 pipeline 代码与 41 个单测可复用，等 DDS 外部解码方案落地后重启。issue #3 保持 open。
