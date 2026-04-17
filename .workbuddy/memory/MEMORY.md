# MEMORY.md - 洪武铁匠开发记忆

## 用户信息
- 学生，正在用 Unity 开发卡牌 RPG《至正铁匠》
- 项目路径：D:\GAMETRY\Unity\Gametry
- 说话风格：轻松口语化，常自称"兄弟"
- 偏好：先聊宽泛思路再深入技术细节

## 游戏设定
- **至正铁匠**：元末至正年间（1341-1370）的铁匠
- **核心立意**：主角行为是"至正"的 —— 为了结束战争而创造战争兵器
- **哲学核心**：通往正义的路，沾满鲜血

## Unity 版本
- **Unity 6**（2026-04-15 升级自 2022.3 LTS）
- VS: Community 2026 (18.5.0)
- Input System 包已安装，Active Input Handling = Both
- 提示：Input.GetKey() 过时警告不影响运行，可无视

## 项目现状

### 代码结构
```
Assets/Scripts/
├─ Player/
│   ├─ Palyermovement.cs     # WASD/方向键移动 + 朝向翻转
│   ├─ PlayerAttack.cs       # J 键连击攻击
│   ├─ PlayerDefense.cs       # K 键防御（按住）
│   └─ PlayerHealth.cs        # 玩家血量、防御减伤、死亡
├─ NPC/
│   └─ NPCWarriorAI.cs        # AI：追击、攻击、防御、伤害系统
└─ Shared/
    ├─ FactionSelector.cs     # 阵营选择
    ├─ Faction.cs             # 阵营枚举
    └─ AttackHitbox.cs        # 攻击碰撞检测
```

### 战斗系统（已完成）
| 功能 | 状态 |
|------|------|
| Player 攻击 | J 连击，Attack1=10伤害，Attack2=15伤害 |
| Player 防御 | K 按住防御，伤害-10 |
| NPC 追击 | 按阵营敌对关系追击 |
| NPC 攻击 | 攻击概率60%，防御概率40% |
| NPC 互殴 | 伤害-10 |
| 死亡处理 | Player SetActive(false)，NPC Destroy |
| 击退眩晕 | knockbackForce=5, stunTime=0.2 |

### 血条UI（2026-04-15）
- Image + Canvas Group 方案
- 血条宽度随血量百分比缩放（Pivot X=0，从左边锚点）
- 锚点预设选择 left+top 等位置

### 属性面板UI（2026-04-15）
- `StatsUI.cs` 显示4个属性：Health/Strength/Speed/Knockback
- `StatsCanvasController.cs` 控制开关
- P键打开/关闭，ESC关闭
- 打开时 Time.timeScale=0 暂停游戏

### Strength属性（2026-04-15）
- Attack1 = Strength × 1
- Attack2 = Strength × 1.5
- Strength 默认值 = 10

### 伤害保护机制
- `isAttacking` + `lastHitTime`(0.05秒) 双保险防止重复触发
- `Physics2D.OverlapCircleAll` 检测范围内敌人

### 击退系统（2026-04-15）
- PlayerAttack 和 NPCWarriorAI 各有 knockbackForce=5, knockbackStunTime=0.2
- `isKnockedBack` 变量控制眩晕状态，眩晕时禁止移动
- PlayerMovement 和 NPCWarriorAI Update() 中检查 isKnockedBack

### 数值管理系统（2026-04-15）
- 创建 `StatsManager.cs` 单例模式，集中管理所有游戏数值
- 路径：`Assets/Scripts/Shared/StatsManager.cs`
- Hierarchy 需要创建 StatsManager 空对象并挂载脚本
- 包含 Player 和 NPC 所有属性（血量、伤害、速度、感知范围、行为概率等）
- 使用 `StatsManager.Instance.属性名` 访问

### 感知系统（2026-04-15）
- **触发器方案失败**：CircleCollider2D + OnTriggerEnter2D 在 Unity 6 中无法检测 Player（能检测到地图物体 Confiner，但检测不到近距离的 Player）
- **最终方案**：改用 `Physics2D.OverlapCircleAll` 每帧手动检测，不依赖触发器事件
- **简化方案**：用 `detectionRadius` 数值字段代替 CircleCollider2D 引用，直接设置数值即可
- 目标超出感知范围会丢失，冷却时间 = attackInterval（2秒）
- Scene视图黄色圆圈可视化（Gizmos）

### 已知问题
- UnityConnectWebRequestException: 许可证验证失败，Clash切全局+重启Unity可解决

### 物品系统（2026-04-16, 2026-04-17大更新）
- 路径：`Assets/Scripts/Inventory & Shop/`
- **ItemSO.cs**：ScriptableObject基类，字段：itemName/itemDescription/icon/isGold/isUsable/healAmount/speedBuffAmount/speedBuffDuration/currentHealth/maxHealth/speed/damage/duration/isStackable/maxStack/pickupQuantity
- **InventoryManger.cs**：单例管理器 + InventorySlot内部类；热键1-7选格子（放大1.2x）；E使用物品；Q长按机制：<1秒松手丢1个，>1秒进入长按模式（每帧丢1个），松手停止；长按丢全部=格子总数量；每帧生成1个 loot Prefab；lootPrefab字段拖入 Prefab；生成时+随机横向偏移
- **Loot.cs**：Awake+RefreshVisuals运行时设置图标；pickupCooldown=2秒防止瞬捡；OnTriggerEnter2D按pickupQuantity捡起后Destroy；Loot.quantity保存掉落物数量（目前搁置备用）
- **InventorySlotUI.cs**：每个格子挂载，通过GetComponentInChildren<Button>()响应点击并调用SelectSlot
- **踩坑**：UpdateUI()中countText.enabled=false后没有在非null分支重置为true，导致捡起堆叠物品后数量文字不显示
- 右键 → Create → Item → New Item 创建物品数据文件（ItemSOs/文件夹下）

### 踩坑记录
- Animator Controller Invalid：动画状态名写错或Controller未正确创建，重新创建Controller解决

## 待实现
- [x] 血条/伤害数值 UI 显示
- [ ] 死亡和重生逻辑
- [ ] 其他职业（弓箭手、法师等）
- [ ] 卡牌战斗 UI
- [ ] 技能树/升级系统
- [x] 商店场景（进行中）
- [x] 素材准备（Aseprite已编译）

## GitHub
- 仓库：q1262437767-dotcom/Gametry1
- 分支：Unity（旧，已废弃，内容在main）
- 备份：D:\GAMETRY\ 全项目
