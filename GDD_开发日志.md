# 《洪武铁匠》开发日志

> 记录学习过程和功能迭代

---

## 📅 2026-04-14（下午）战斗系统 v1.0

### 🎮 完成功能

| 功能 | 脚本 | 说明 |
|------|------|------|
| J 连击攻击 | `PlayerAttack.cs` | Attack1→Attack2→Attack1 循环 |
| K 防御 | `PlayerDefense.cs` | 按住防御，松手恢复 |
| NPC 追击 | `NPCWarriorAI.cs` | 警戒范围外 Idle，进入后追击 |
| NPC 攻击 | `NPCWarriorAI.cs` | 攻击概率 60% |
| NPC 随机防御 | `NPCWarriorAI.cs` | 战斗中随机防御 40% |
| NPC 被攻击防御 | `NPCWarriorAI.cs` | 被攻击时 40% 概率防御 |
| 阵营系统 | `FactionSelector.cs` | 7 个阵营：Red/Blue/Yellow/Black/Purple/Animal/Monster |
| 攻击碰撞检测 | `AttackHitbox.cs` | NPC 攻击玩家用 |

### 🎮 控制方式
- **J** - 攻击（连击）
- **K** - 防御（按住）
- **WASD/方向键** - 移动

### 📁 文件结构
```
Assets/Scripts/
├─ Player/
│   ├─ Palyermovement.cs     # WASD/方向键移动 + 朝向翻转
│   ├─ PlayerAttack.cs       # J 键连击攻击
│   ├─ PlayerDefense.cs     # K 键防御（按住）
│   └─ AttackHitbox.cs      # 攻击碰撞检测
├─ NPC/
│   └─ NPCWarriorAI.cs      # AI：追击、攻击、防御（概率）
└─ Elevation/
    ├─ ElevationEntry.cs     # 高度进入触发器
    └─ ElevationExit.cs      # 高度退出触发器
├─ FactionSelector.cs       # 阵营系统
```

### 🔧 学会的 Unity 技能
- Animator 状态机 + Parameters（Trigger/Bool）
- 动画连线条件设置
- Rigidbody2D 类型（Dynamic vs Kinematic）
- Collider2D + Trigger 检测
- Tag 和 Layer 的区别和用法
- 协程实现 AI 行为
- 代码控制动画触发

### ⏭️ 下一步
- [ ] 血条/伤害数值系统
- [ ] 死亡和重生逻辑
- [ ] 其他职业（弓箭手、法师等）
- [ ] 攻击伤害判定

---

## 📅 2026-04-14（上午）Unity 入门

### ✅ 学会的基础
- 场景搭建（Canvas、GameObject）
- 基础移动（Input.GetAxis + Rigidbody2D）
- Animator 状态机设置
- 碰撞体/触发器
- Trigger 参数控制动画切换
- Gizmos 可视化调试

### 📁 早期文件
- `Palyermovement.cs` - 移动脚本
- `ElevationEntry.cs` / `ElevationExit.cs` - 高度系统

---

## 📅 2026-04-10 卡牌游戏原型

### ✅ 完成
- Python 卡牌战斗原型 v1
- GDD 卡牌战斗系统设计 v2

### 📁 文件
- `card_battle.py` - 卡牌战斗逻辑
- `GDD_CARD_BATTLE_v2.md` - 通用卡牌战斗系统设计

### ⏭️ 下一步
- [ ] Unity 实现卡牌战斗核心
- [ ] UI 卡牌界面

---

## 📅 更早

### 2026-04-09 游戏设计
- 完成《洪武铁匠》完整 GDD
- 确定核心玩法：铁匠 + 卡牌 + 阵营

### 📁 文件
- `洪武铁匠_游戏设计文档.md` - 完整游戏设计文档
