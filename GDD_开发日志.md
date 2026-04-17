# 《至正铁匠》开发日志
最新内容见workbuddy工作日志

> 记录学习过程和功能迭代

---

## 📅 2026-04-16 物品系统 + 快捷栏 UI

### 🎮 完成功能

| 功能 | 脚本/文件 | 说明 |
|------|-----------|------|
| 物品数据基类 | `ItemSO.cs` | ScriptableObject，字段：itemName/description/icon/stackable/maxStack |
| 快捷栏 UI | `InventorySlot.cs` | 7格底部快捷栏，显示图标和堆叠数量 |
| 背包管理器 | `InventoryManger.cs` | 单例模式，AddItem 核心逻辑：可堆叠优先叠加，找空格子放新物品 |
| 物品拾取 | `Loot.cs` | OnTriggerEnter2D 检测 Player，调用 AddItem，播放动画后销毁 |
| 物品创建 | Meat Resource, Wood Resource | 右键 → Create → Item → New Item |

### 📁 新增文件
```
Assets/Scripts/
├─ Items/
│   └─ ItemSO.cs              # 物品 ScriptableObject 基类
├─ Inventory & Shop/
│   ├─ InventorySlot.cs      # 快捷栏格子组件
│   └─ InventoryManger.cs    # 背包管理器（单例）
```

### 🔧 踩坑记录
1. **Animator Controller Invalid**：动画状态名写错或Controller未正确创建，重新创建Controller解决
2. **"背包已满"误报**：Slots数组的 Icon Image 和 Count Text 未在 Inspector 中关联
3. **数量文字不显示**：countText.enabled 在物体未激活时无效，改用 SetActive(true)

### 📚 学习内容
- ScriptableObject 数据容器
- UI 父子 Canvas 结构
- 单例模式管理器
- Collider2D 触发检测

### ⏭️ 下一步
- [ ] 商店 NPC 功能
- [ ] 物品使用/消耗逻辑
- [ ] 更多物品类型

---

## 📅 2026-04-15 战斗系统完善 + 数值管理 + UI

### 🎮 完成功能

| 功能 | 脚本/文件 | 说明 |
|------|-----------|------|
| 击退眩晕系统 | `PlayerHealth.cs`, `NPCWarriorAI.cs` | 击退力度=5，眩晕0.2秒 |
| 眩晕禁止移动 | `Palyermovement.cs` | 读取 `isKnockedBack`，眩晕时禁止移动 |
| 数值管理器 | `StatsManager.cs` | 单例模式，集中管理所有数值 |
| 血条 UI | `PlayerHealth.cs` | Image + 锚点方案，根据血量百分比缩放 |
| 属性面板 UI | `StatsUI.cs`, `StatsCanvasController.cs` | 4属性显示：Health/Strength/Speed/Knockback |
| 暂停菜单 | `StatsCanvasController.cs` | P键打开/关闭，ESC关闭，TimeScale暂停 |
| Strength 属性 | `StatsManager.cs` | Attack1=Strength×1, Attack2=Strength×1.5 |
| 场景切换 | SceneManager | 学会基础场景加载 |

### 📁 新增文件
```
Assets/Scripts/
├─ StatsManager.cs           # 数值管理器（单例）
├─ Player/
│   ├─ StatsUI.cs            # 属性面板显示
│   └─ StatsCanvasController.cs  # 暂停菜单控制
└─ Shared/
    └─ StatsManager.cs        # （路径可能调整）
```

### 📊 StatsManager 属性列表
| 分类 | 属性 | 默认值 |
|------|------|--------|
| Player-Combat | playerAttack1Damage | Strength×1 |
| Player-Combat | playerAttack2Damage | Strength×1.5 |
| Player-Combat | playerKnockbackForce | 5 |
| Player-Combat | playerKnockbackStunTime | 0.2 |
| Player-Movement | playerMoveSpeed | 5 |
| Player-Health | playerMaxHealth | 100 |
| Player-Health | playerDefenseReduction | 10 |
| NPC-Warrior | npcMaxHealth | 100 |
| NPC-Warrior | npcAttackDamage | 10 |
| NPC-Warrior | npcMoveSpeed | 2 |
| NPC-Warrior | npcDetectionRadius | 3 |
| NPC-Warrior | npcAttackInterval | 2 |
| NPC-Warrior | npcAttackChance | 0.6 |
| NPC-Warrior | npcDefenseChance | 0.4 |

### 🔧 踩坑记录
1. **Unity 6 触发器失效**: CircleCollider2D + OnTriggerEnter2D 检测不到Player，改用 `Physics2D.OverlapCircleAll`
2. **isKnockedBack 警告**: 变量声明但未使用 → 在 Update() 添加 `if (isDead || isKnockedBack) return;`
3. **Awake 单例模式**: 确保全局只有一个 StatsManager 实例

### 📚 学习内容
- 单例模式（Singleton）
- Canvas Group 控制 UI 显示
- Time.timeScale 控制游戏暂停
- SceneManager.LoadScene 场景切换
- AI 素材生成工具（Leonardo.ai）

### ⏭️ 下一步
- [ ] 卡牌系统接入
- [ ] 技能树/升级系统
- [ ] 其他职业（弓箭手、法师）
- [ ] 商店场景
- [ ] 素材准备（AI生成/自画）

---

## 📅 2026-04-14（晚）战斗系统 v2.0 - 伤害与死亡

### 🎮 完成功能

| 功能 | 脚本 | 说明 |
|------|------|------|
| Player 伤害系统 | `PlayerHealth.cs` | 新增，maxHealth=100，防御减10伤害 |
| Player 防御 | `PlayerDefense.cs` | 按住K防御，isDefending标志位控制 |
| NPC 伤害系统 | `NPCWarriorAI.cs` | maxHealth=100，死亡后Destroy |
| NPC→Player 攻击 | `NPCWarriorAI.OnAttackHit()` | 通过GetComponent查找PlayerHealth |
| NPC→NPC 互殴 | `NPCWarriorAI.OnAttackHit()` | 同时处理两种目标类型 |
| 重复触发保护 | lastHitTime | 0.05秒时间窗口防止多次扣血 |

### 🔧 防御逻辑
- **Player**: 按住K → `isDefending=true` → `TakeDamage()` 伤害-10
- **NPC**: 被攻击时40%概率防御 → 伤害-10

### ⚠️ 踩坑记录
1. **状态名检查不稳定**: Animator状态名可能变化，改用 `isAttacking` + `lastHitTime` 双保险
2. **GetComponent返回null**: Player必须挂载PlayerHealth组件
3. **动画事件多次触发**: 用 `Time.time - lastHitTime < 0.05f` 保护

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
