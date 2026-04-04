"""
卡牌对战游戏 v2.0 - 增强版
玩家 vs AI，回合制卡牌战斗
新增：真实伤害、反伤、护盾、吸血等机制
"""

import pygame
import random
import math
import copy
import json
import os
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

# 初始化Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 80, 80)
GREEN = (80, 200, 100)
BLUE = (100, 150, 255)
ORANGE = (255, 150, 50)
PURPLE = (180, 100, 255)
YELLOW = (255, 215, 0)

# 卡牌颜色
CARD_COLORS = [
    (255, 107, 107),   # 红色 - 物理
    (78, 205, 196),    # 青色 - 魔法
    (168, 85, 247),    # 紫色 - 功能
    (255, 215, 0),     # 金色 - 稀有
    (255, 100, 0),     # 橙色 - 爆发
    (100, 200, 100),   # 绿色 - 治疗
    (100, 150, 255),   # 蓝色 - 防守
    (255, 150, 200),   # 粉色 - 特殊
]

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# 卡牌尺寸
CARD_WIDTH = 120
CARD_HEIGHT = 170

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("卡牌对战 v2.0")
clock = pygame.time.Clock()

# 字体设置 - 优先使用常见中文字体
chinese_font_name = None
for font_name in ["Microsoft YaHei", "SimHei", "SimSun", "KaiTi"]:
    try:
        test_surface = pygame.font.SysFont(font_name, 24).render("测", True, (255,255,255))
        if test_surface.get_width() > 10:
            chinese_font_name = font_name
            break
    except:
        continue

if chinese_font_name:
    font_large = pygame.font.SysFont(chinese_font_name, 48)
    font_medium = pygame.font.SysFont(chinese_font_name, 32)
    font_small = pygame.font.SysFont(chinese_font_name, 24)
    font_tiny = pygame.font.SysFont(chinese_font_name, 18)
else:
    font_large = pygame.font.Font(None, 72)
    font_medium = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)
    font_tiny = pygame.font.Font(None, 24)


@dataclass
class Card:
    """增强版卡牌数据结构"""
    name: str
    icon: str = ""

    # 基础属性
    attack: int = 0           # 物理攻击
    defense: int = 0          # 物理防御
    magic_attack: int = 0     # 魔法攻击
    magic_defense: int = 0    # 魔法防御
    health: int = 0           # 生命值（某些卡有）
    energy: int = 1           # 能量消耗

    # 特殊属性
    real_damage: int = 0      # 真实伤害（无视防御）
    reflect_damage: int = 0   # 反伤比例(%)
    shield: int = 0           # 护盾值
    heal: int = 0             # 治疗量
    lifesteal: int = 0        # 吸血比例(%)
    vulnerability: int = 0    # 易伤比例(%)，正数=受伤增加
    armor: int = 0            # 护甲值（独立减伤）

    # 卡牌类型
    card_type: str = "normal"  # normal/rare/legendary

    def get_color(self) -> tuple:
        """获取卡牌颜色"""
        if self.card_type == "legendary":
            return CARD_COLORS[3]  # 金色
        elif self.card_type == "rare":
            return CARD_COLORS[4]  # 橙色
        return CARD_COLORS[hash(self.name) % 7]

    def get_total_attack(self) -> int:
        """获取总攻击力（物理+魔法+真实）"""
        return self.attack + self.magic_attack

    def get_desc(self) -> str:
        """获取卡牌描述"""
        effects = []
        if self.real_damage > 0:
            effects.append(f"⚔️真实伤害+{self.real_damage}")
        if self.reflect_damage > 0:
            effects.append(f"🛡️反伤{self.reflect_damage}%")
        if self.shield > 0:
            effects.append(f"🔰护盾+{self.shield}")
        if self.heal > 0:
            effects.append(f"💚治疗{self.heal}")
        if self.lifesteal > 0:
            effects.append(f"🩸吸血{self.lifesteal}%")
        if self.vulnerability > 0:
            effects.append(f"💔易伤+{self.vulnerability}%")
        if self.armor > 0:
            effects.append(f"🛡护甲+{self.armor}")
        return " ".join(effects) if effects else ""


# ==================== 玩家卡池（20张） ====================
PLAYER_CARD_LIBRARY = [
    # === 物理攻击系（5张）===
    Card('战士', '⚔️', attack=15, defense=5, energy=2),
    Card('刺客', '🗡️', attack=22, defense=2, energy=3, real_damage=8),
    Card('狂战士', '💢', attack=20, defense=3, energy=3, vulnerability=30),
    Card('剑圣', '🏋️', attack=18, defense=8, energy=4, real_damage=5),
    Card('盾战士', '🛡️', attack=8, defense=15, energy=2, armor=10),

    # === 魔法攻击系（5张）===
    Card('法师', '🔮', magic_attack=16, magic_defense=3, energy=2, real_damage=3),
    Card('火球术', '🔥', magic_attack=14, magic_defense=2, energy=3, real_damage=8),
    Card('冰霜新星', '❄️', magic_attack=10, magic_defense=8, energy=3, vulnerability=25),
    Card('奥术飞弹', '✨', magic_attack=8, magic_defense=4, energy=2, heal=4),
    Card('大法师', '🧙', magic_attack=22, magic_defense=6, energy=4, shield=15),

    # === 防御/生存系（5张）===
    Card('圣骑士', '⚜️', attack=5, defense=18, energy=2, shield=12),
    Card('生命汲取', '💉', attack=3, defense=6, energy=2, heal=12, lifesteal=20),
    Card('守护天使', '👼', defense=12, energy=3, shield=25),
    Card('荆棘光环', '🌹', attack=6, defense=10, energy=2, reflect_damage=25),
    Card('治疗结界', '💖', defense=8, energy=3, heal=18),

    # === 特殊/功能性（5张）===
    Card('暗影突袭', '💀', attack=18, defense=0, energy=3, lifesteal=30, real_damage=5),
    Card('龙息', '🐉', attack=15, defense=5, energy=4, real_damage=12, card_type="rare"),
    Card('战吼', '📢', attack=4, defense=4, energy=1, real_damage=6),
    Card('铁壁', '🧱', defense=16, energy=2, armor=15),
    Card('复仇之魂', '👻', attack=12, defense=12, energy=3, reflect_damage=20, heal=8),
]


# ==================== AI敌人卡池（每关不同） ====================

# 关卡1：新手教程 - 哥布林
GOBLIN_CARDS = [
    Card('哥布林战士', '👺', attack=8, defense=3, energy=1),
    Card('哥布林弓手', '🏹', attack=10, defense=1, energy=1),
    Card('哥布林萨满', '🧙', magic_attack=6, magic_defense=5, energy=2, heal=4),
]

# 关卡2：黑暗森林 - 狼群
WOLF_CARDS = [
    Card('野狼', '🐺', attack=12, defense=2, energy=1, real_damage=2),
    Card('狼王', '🐺', attack=15, defense=4, energy=2, lifesteal=15),
    Card('暗夜猎手', '🌙', attack=10, defense=6, energy=2, real_damage=4),
]

# 关卡3：亡灵墓地 - 不死族
UNDEAD_CARDS = [
    Card('骷髅战士', '💀', attack=8, defense=8, energy=1, reflect_damage=15),
    Card('僵尸', '🧟', attack=6, defense=10, energy=1, heal=6),
    Card('亡灵骑士', '⚔️', attack=14, defense=12, energy=3, reflect_damage=20, armor=8),
    Card('死亡骑士', '💀', attack=18, defense=8, energy=3, real_damage=5, lifesteal=20, card_type="rare"),
]

# 关卡4：火焰地狱 - 炎魔军团
FIRE_CARDS = [
    Card('火焰精灵', '🔥', magic_attack=14, magic_defense=3, energy=1, real_damage=3),
    Card('岩浆巨人', '🌋', attack=16, defense=10, energy=3, real_damage=8),
    Card('地狱火', '😈', magic_attack=20, magic_defense=6, attack=10, energy=3),
    Card('炎魔领主', '👹', magic_attack=22, magic_defense=8, attack=12, energy=4, real_damage=10, card_type="rare"),
]

# 关卡5：最终决战 - 魔王
DEMON_LORD_CARDS = [
    Card('魔将', '👿', attack=14, defense=10, energy=2, shield=15),
    Card('暗影刺客', '🗡️', attack=16, defense=4, energy=2, real_damage=8),
    Card('堕落天使', '😇', magic_attack=18, magic_defense=10, energy=3, heal=12),
    Card('魔王', '👑', attack=20, defense=12, magic_attack=12, magic_defense=12, energy=4,
         real_damage=6, reflect_damage=15, card_type="legendary"),
]

# 关卡敌人卡池映射
ENEMY_CARD_POOLS = {
    0: GOBLIN_CARDS,
    1: WOLF_CARDS,
    2: UNDEAD_CARDS,
    3: FIRE_CARDS,
    4: DEMON_LORD_CARDS,
}

# 关卡配置
LEVELS = [
    {'name': '第1关', 'ai_health': 80, 'ai_bonus': 0, 'desc': '哥布林小队',
     'color': (100, 200, 100), 'enemy_name': '哥布林营地'},
    {'name': '第2关', 'ai_health': 90, 'ai_bonus': 5, 'desc': '黑暗森林',
     'color': (150, 200, 100), 'enemy_name': '狼群巢穴'},
    {'name': '第3关', 'ai_health': 100, 'ai_bonus': 10, 'desc': '亡灵墓地',
     'color': (180, 180, 200), 'enemy_name': '不死军团'},
    {'name': '第4关', 'ai_health': 110, 'ai_bonus': 20, 'desc': '火焰地狱',
     'color': (200, 150, 100), 'enemy_name': '炎魔军团'},
    {'name': '第5关', 'ai_health': 130, 'ai_bonus': 30, 'desc': '最终决战',
     'color': (200, 100, 100), 'enemy_name': '魔王城'},
]


class GameState:
    """游戏状态"""
    def __init__(self):
        self.unlocked_levels = 1
        self.current_level = 0
        self.in_main_menu = True
        self.selecting_level = False
        self.in_settings = False
        self.reset()

    def reset(self, keep_stats=False):
        # 基础状态
        self.player_health = 100
        self.ai_health = 100
        self.max_health = 100

        # 护盾系统
        self.player_shield = 0
        self.ai_shield = 0

        # 手牌
        self.player_hand: List[Card] = []
        self.ai_hand: List[Card] = []
        self.player_card: Optional[Card] = None
        self.ai_card: Optional[Card] = None

        # 回合状态
        self.round = 0
        self.is_player_turn = True
        self.game_started = False
        self.battle_result = ''
        self.game_over = False
        self.winner = None
        self.level_cleared = False

        # 多牌出牌系统
        self.player_played_cards = []
        self.ai_played_cards = []
        self.turn_action_done = False

        # 能量系统（优化：每回合+2，上限7）
        self.player_energy = 3
        self.ai_energy = 3
        self.max_energy = 7

        # 状态效果
        self.player_vulnerability = 0   # 玩家当前易伤%
        self.ai_vulnerability = 0       # AI当前易伤%
        self.player_reflect = 0         # 玩家当前反伤%
        self.ai_reflect = 0             # AI当前反伤%

        # 统计
        if not keep_stats:
            self.wins = 0
            self.losses = 0
            self.draws = 0

        # 动画相关
        self.show_damage = False
        self.damage_timer = 0
        self.player_damage = 0
        self.ai_damage = 0
        self.player_heal = 0
        self.ai_heal = 0
        self.show_heal = False

        # 日志
        self.logs: List[str] = []

    def add_log(self, message: str):
        """添加日志"""
        self.logs.insert(0, message)
        if len(self.logs) > 20:
            self.logs.pop()

    def unlock_next_level(self):
        """解锁下一关"""
        if self.current_level + 1 < len(LEVELS):
            self.unlocked_levels = max(self.unlocked_levels, self.current_level + 2)


def draw_card(surface: pygame.Surface, card: Card, x: int, y: int,
              selected=False, hover=False, small=False, face_down=False, disabled=False):
    """绘制卡牌"""
    width = CARD_WIDTH if not small else CARD_WIDTH - 20
    height = CARD_HEIGHT if not small else CARD_HEIGHT - 30

    # 阴影
    shadow_rect = pygame.Rect(x + 5, y + 5, width, height)
    pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=15)

    card_rect = pygame.Rect(x, y, width, height)
    card_color = card.get_color()

    if disabled:
        card_color = (80, 80, 80)

    # 背景
    dark_color = tuple(max(0, c - 80) for c in card_color)
    pygame.draw.rect(surface, dark_color, card_rect, border_radius=15)

    inner_rect = pygame.Rect(x + 5, y + 5, width - 10, height - 10)
    pygame.draw.rect(surface, card_color, inner_rect, border_radius=12)

    border_color = (120, 120, 120) if disabled else WHITE
    pygame.draw.rect(surface, border_color, card_rect, 3, border_radius=15)

    if face_down:
        for i in range(3):
            line_y = y + 25 + i * 35
            pygame.draw.rect(surface, (80, 80, 80),
                             (x + 15, line_y, width - 30, 25), border_radius=5)
        return

    # 顶部装饰条
    top_rect = pygame.Rect(x + 8, y + 8, width - 16, 6)
    pygame.draw.rect(surface, WHITE, top_rect, border_radius=3)

    # 图标
    if card.icon:
        icon_font = font_medium
        icon_text = icon_font.render(card.icon, True, WHITE)
        icon_rect = icon_text.get_rect(center=(x + width // 2, y + 30))
        surface.blit(icon_text, icon_rect)

    # 名称背景
    name_bg_rect = pygame.Rect(x + 8, y + height - 70, width - 16, 22)
    pygame.draw.rect(surface, (0, 0, 0, 150), name_bg_rect, border_radius=5)

    name_font = font_tiny if not small else pygame.font.Font(None, 18)
    name_text = name_font.render(card.name, True, WHITE)
    name_rect = name_text.get_rect(center=(x + width // 2, y + height - 59))
    surface.blit(name_text, name_rect)

    # 属性显示（紧凑布局）
    stats_y = y + height - 45

    # 左上：物理攻击
    if card.attack > 0:
        atk_text = font_small.render(f"⚔{card.attack}", True, RED)
        surface.blit(atk_text, (x + 8, stats_y))

    # 右上：物理防御
    if card.defense > 0:
        def_text = font_small.render(f"🛡{card.defense}", True, BLUE)
        surface.blit(def_text, (x + width - 45, stats_y))

    # 第二行：魔法攻击/防御
    stats_y2 = y + height - 25
    if card.magic_attack > 0:
        matk_text = font_tiny.render(f"🔮{card.magic_attack}", True, PURPLE)
        surface.blit(matk_text, (x + 8, stats_y2))
    if card.magic_defense > 0:
        mdef_text = font_tiny.render(f"✨{card.magic_defense}", True, PURPLE)
        surface.blit(mdef_text, (x + 50, stats_y2))

    # 能量消耗
    energy_color = YELLOW if not disabled else (100, 100, 100)
    energy_bg_rect = pygame.Rect(x + width - 30, y + 8, 24, 24)
    pygame.draw.circle(surface, energy_color, (x + width - 18, y + 20), 12)
    pygame.draw.circle(surface, (0, 0, 0), (x + width - 18, y + 20), 9)
    energy_text = font_tiny.render(f"{card.energy}", True, energy_color)
    energy_rect = energy_text.get_rect(center=(x + width - 18, y + 20))
    surface.blit(energy_text, energy_rect)

    # 稀有度标记
    if card.card_type == "legendary":
        pygame.draw.rect(surface, YELLOW, (x + 5, y + 5, 15, 15), border_radius=3)
    elif card.card_type == "rare":
        pygame.draw.rect(surface, ORANGE, (x + 5, y + 5, 15, 15), border_radius=3)

    # 选中/悬停效果
    if selected:
        pygame.draw.rect(surface, YELLOW, card_rect, 5, border_radius=15)
    elif hover:
        pygame.draw.rect(surface, (255, 255, 255, 100), card_rect, 3, border_radius=15)


def draw_card_detail(surface: pygame.Surface, card: Card, x: int, y: int):
    """绘制卡牌详细信息面板"""
    panel_width = 300
    panel_height = 200

    # 背景
    pygame.draw.rect(surface, (30, 30, 50), (x, y, panel_width, panel_height), border_radius=10)
    pygame.draw.rect(surface, card.get_color(), (x, y, panel_width, panel_height), 2, border_radius=10)

    # 标题
    title = font_medium.render(f"{card.icon} {card.name}", True, WHITE)
    surface.blit(title, (x + 15, y + 15))

    # 基础属性
    attrs = []
    if card.attack > 0:
        attrs.append(f"⚔️ 物理攻击: {card.attack}")
    if card.defense > 0:
        attrs.append(f"🛡️ 物理防御: {card.defense}")
    if card.magic_attack > 0:
        attrs.append(f"🔮 魔法攻击: {card.magic_attack}")
    if card.magic_defense > 0:
        attrs.append(f"✨ 魔法防御: {card.magic_defense}")
    if card.armor > 0:
        attrs.append(f"🛡 护甲: +{card.armor}")
    if card.energy > 0:
        attrs.append(f"⚡ 能量: {card.energy}")

    y_offset = y + 55
    for attr in attrs[:4]:
        text = font_small.render(attr, True, LIGHT_GRAY)
        surface.blit(text, (x + 15, y_offset))
        y_offset += 25

    # 特殊效果
    effects = []
    if card.real_damage > 0:
        effects.append(f"⚔️ 真实伤害 +{card.real_damage}")
    if card.reflect_damage > 0:
        effects.append(f"🛡️ 反伤 {card.reflect_damage}%")
    if card.shield > 0:
        effects.append(f"🔰 护盾 +{card.shield}")
    if card.heal > 0:
        effects.append(f"💚 治疗 +{card.heal}")
    if card.lifesteal > 0:
        effects.append(f"🩸 吸血 {card.lifesteal}%")
    if card.vulnerability > 0:
        effects.append(f"💔 易伤 +{card.vulnerability}%")

    for effect in effects:
        text = font_small.render(effect, True, ORANGE)
        surface.blit(text, (x + 15, y_offset))
        y_offset += 22


def draw_health_bar(surface: pygame.Surface, x: int, y: int, width: int, height: int,
                    current: int, max_val: int, label: str, shield: int = 0):
    """绘制血条（带护盾）"""
    # 背景
    pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height), border_radius=10)

    # 护盾条（如果存在）
    if shield > 0:
        shield_height = height // 3
        shield_percent = min(1.0, shield / 50)  # 假设50点护盾=满
        shield_fill = int((width - 4) * shield_percent)
        pygame.draw.rect(surface, (100, 150, 255), (x + 2, y + 2, shield_fill, shield_height), border_radius=8)
        shield_label = font_tiny.render(f"🔰{shield}", True, WHITE)
        surface.blit(shield_label, (x + 5, y + 2))

    # 血量填充
    percent = max(0, current / max_val)
    fill_width = int(width * percent)

    if percent > 0.4:
        color = GREEN
    elif percent > 0.2:
        color = ORANGE
    else:
        color = RED

    if fill_width > 0:
        pygame.draw.rect(surface, color, (x, y + height // 3, fill_width, height * 2 // 3), border_radius=10)

    # 文字
    text = font_small.render(f"{label}: {current}/{max_val}", True, WHITE)
    text_rect = text.get_rect(center=(x + width // 2, y + height // 2 + 5))
    surface.blit(text, text_rect)


class SoundManager:
    """音效管理器"""
    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.3
        self.sfx_volume = 0.5
        self.enabled = True
        self.music_enabled = True
        self.sfx_enabled = True

        self.load_settings()
        self._generate_sounds()
        self._generate_bgm()

        if not self.music_enabled and hasattr(self, 'bgm'):
            self.bgm.stop()

    def load_settings(self):
        try:
            settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    self.music_enabled = settings.get('music_enabled', True)
                    self.music_volume = settings.get('music_volume', 0.3)
                    self.sfx_enabled = settings.get('sfx_enabled', True)
                    self.sfx_volume = settings.get('sfx_volume', 0.5)
        except:
            pass

    def save_settings(self):
        try:
            settings = {
                'music_enabled': self.music_enabled,
                'music_volume': self.music_volume,
                'sfx_enabled': self.sfx_enabled,
                'sfx_volume': self.sfx_volume
            }
            settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
            with open(settings_path, 'w') as f:
                json.dump(settings, f)
        except:
            pass

    def _generate_bgm(self):
        """生成柔和的背景音乐"""
        try:
            sample_rate = 22050
            duration = 4  # 4秒循环
            beat_duration = 0.5

            # 和弦进行 (C-G-Am-F 柔和的进行)
            chord_prog = [
                (262, 330, 392),  # C
                (196, 247, 392),  # G
                (220, 262, 330),  # Am
                (175, 220, 262),  # F
            ]

            wave = np.array([], dtype=np.float32)

            for chord in chord_prog:
                for note_dur in [beat_duration, beat_duration, beat_duration, beat_duration]:
                    samples = int(sample_rate * note_dur)
                    t = np.linspace(0, note_dur, samples, dtype=np.float32)
                    chord_wave = np.zeros(samples)
                    for freq in chord:
                        # 使用更柔和的正弦波
                        note_wave = np.sin(2 * np.pi * freq * t)
                        # 添加轻微颤音
                        vibrato = 1 + 0.02 * np.sin(2 * np.pi * 5 * t)
                        chord_wave += note_wave * vibrato * 0.15
                    # 包络
                    envelope = np.ones(samples)
                    attack = int(samples * 0.05)
                    release = int(samples * 0.3)
                    envelope[:attack] = np.linspace(0, 1, attack)
                    envelope[-release:] = np.linspace(1, 0.5, release)
                    chord_wave *= envelope
                    wave = np.concatenate([wave, chord_wave])

            # 轻柔淡入淡出
            fade_len = min(1000, len(wave) // 8)
            wave[:fade_len] *= np.linspace(0, 1, fade_len)
            wave[-fade_len:] *= np.linspace(1, 0, fade_len)

            wave = (wave * 32767 * 0.4).astype(np.int16)
            stereo = np.column_stack((wave, wave))

            self.bgm = pygame.mixer.Sound(array=stereo)
            self.bgm.set_volume(self.music_volume)
            self.bgm_length = len(wave) / sample_rate
        except Exception as e:
            print(f"警告 背景音乐生成失败: {e}")
            self.music_enabled = False

    def play_bgm(self):
        if self.music_enabled and hasattr(self, 'bgm'):
            self.bgm.stop()
            self.bgm.set_volume(self.music_volume)
            self.bgm.play(-1)

    def stop_bgm(self):
        if hasattr(self, 'bgm'):
            self.bgm.stop()

    def _generate_sounds(self):
        try:
            self.sounds['play_card'] = self._create_beep_sound(800, 0.1, 0.3)
            self.sounds['attack'] = self._create_attack_sound()
            self.sounds['victory'] = self._create_victory_sound()
            self.sounds['defeat'] = self._create_defeat_sound()
            self.sounds['click'] = self._create_beep_sound(600, 0.05, 0.2)
            self.sounds['draw'] = self._create_beep_sound(1000, 0.08, 0.25)
            self.sounds['heal'] = self._create_heal_sound()
            self.sounds['shield'] = self._create_shield_sound()
        except Exception as e:
            print(f"警告 音效生成失败: {e}")
            self.enabled = False

    def _create_beep_sound(self, freq, duration, volume):
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, dtype=np.float32)
        freq_envelope = freq * (1 + 0.1 * np.sin(2 * np.pi * 10 * t))
        wave = np.sin(2 * np.pi * freq_envelope * t)
        envelope = np.exp(-3 * t / duration)
        wave = wave * envelope * volume
        wave = (wave * 32767 * 0.3).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound

    def _create_attack_sound(self):
        sample_rate = 44100
        duration = 0.2
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, dtype=np.float32)
        bass = np.sin(2 * np.pi * 80 * t) * np.exp(-10 * t)
        treble = np.sin(2 * np.pi * 400 * t) * np.exp(-15 * t) * 0.5
        wave = bass + treble
        wave = wave * 0.6
        wave = (wave * 32767 * 0.4).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound

    def _create_heal_sound(self):
        sample_rate = 44100
        notes = [523, 659, 784]
        wave = np.array([], dtype=np.int16)
        for freq in notes:
            duration = 0.12
            t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
            note_wave = np.sin(2 * np.pi * freq * t) * np.exp(-2 * t)
            note_wave = (note_wave * 32767 * 0.25).astype(np.int16)
            wave = np.concatenate([wave, note_wave])
        stereo = np.column_stack((wave, wave))
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound

    def _create_shield_sound(self):
        sample_rate = 44100
        notes = [400, 500, 600]
        wave = np.array([], dtype=np.int16)
        for freq in notes:
            duration = 0.1
            t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
            note_wave = np.sin(2 * np.pi * freq * t) * np.exp(-3 * t)
            note_wave = (note_wave * 32767 * 0.2).astype(np.int16)
            wave = np.concatenate([wave, note_wave])
        stereo = np.column_stack((wave, wave))
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound

    def _create_victory_sound(self):
        sample_rate = 44100
        notes = [523, 659, 784, 1047]
        wave = np.array([], dtype=np.int16)
        for freq in notes:
            duration = 0.15
            t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
            note_wave = np.sin(2 * np.pi * freq * t) * np.exp(-2 * t)
            note_wave = (note_wave * 32767 * 0.3).astype(np.int16)
            wave = np.concatenate([wave, note_wave])
        stereo = np.column_stack((wave, wave))
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound

    def _create_defeat_sound(self):
        sample_rate = 44100
        notes = [392, 330, 262, 196]
        wave = np.array([], dtype=np.int16)
        for freq in notes:
            duration = 0.25
            t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
            note_wave = np.sin(2 * np.pi * freq * t) * np.exp(-2 * t)
            note_wave = (note_wave * 32767 * 0.3).astype(np.int16)
            wave = np.concatenate([wave, note_wave])
        stereo = np.column_stack((wave, wave))
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound

    def play(self, sound_name):
        if self.enabled and self.sfx_enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass

    def set_volume(self, volume):
        self.sfx_volume = max(0, min(1, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)


class CardBattleGame:
    """卡牌对战游戏主类"""
    def __init__(self):
        self.state = GameState()
        self.hovered_card = None
        self.sound = SoundManager()
        self.show_card_detail = False
        self.detail_card = None

    def draw(self):
        """绘制游戏界面"""
        screen.fill((26, 26, 46))

        # 标题
        title = font_large.render("卡牌对战 v2.0", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title, title_rect)

        if self.state.in_main_menu:
            self.draw_main_menu()
        elif self.state.selecting_level:
            self.draw_level_select()
        else:
            self.draw_battle()

        # 设置按钮
        if not self.state.in_settings and not self.state.in_main_menu:
            self.settings_btn_rect = pygame.Rect(SCREEN_WIDTH - 90, 5, 80, 25)
            is_hovered = self.settings_btn_rect.collidepoint(pygame.mouse.get_pos())
            btn_color = (80, 80, 100) if is_hovered else (60, 60, 80)
            pygame.draw.rect(screen, btn_color, self.settings_btn_rect, border_radius=6)
            settings_text = font_tiny.render("设置", True, WHITE)
            settings_rect = settings_text.get_rect(center=self.settings_btn_rect.center)
            screen.blit(settings_text, settings_rect)

        if self.state.in_settings:
            self.draw_settings()

    def draw_main_menu(self):
        """绘制主菜单"""
        pygame.draw.rect(screen, (30, 30, 60), (100, 150, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 300), border_radius=20)

        game_title = font_large.render("卡牌对战 v2.0", True, YELLOW)
        game_title_rect = game_title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(game_title, game_title_rect)

        # 新增特性提示
        features = font_small.render("⚔️ 真实伤害 | 🛡️ 反伤护盾 | 🩸 吸血治疗", True, ORANGE)
        features_rect = features.get_rect(center=(SCREEN_WIDTH // 2, 250))
        screen.blit(features, features_rect)

        center_x = SCREEN_WIDTH // 2
        btn_width = 200
        btn_height = 50
        btn_spacing = 70

        # 按钮
        mouse_pos = pygame.mouse.get_pos()

        self.new_game_btn_rect = pygame.Rect(center_x - btn_width // 2, 320, btn_width, btn_height)
        is_hover = self.new_game_btn_rect.collidepoint(mouse_pos)
        btn_color = (60, 180, 80) if is_hover else (50, 150, 60)
        pygame.draw.rect(screen, btn_color, self.new_game_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.new_game_btn_rect, 2, border_radius=12)
        new_game_text = font_medium.render("新游戏", True, WHITE)
        new_game_rect = new_game_text.get_rect(center=self.new_game_btn_rect.center)
        screen.blit(new_game_text, new_game_rect)

        self.continue_btn_rect = pygame.Rect(center_x - btn_width // 2, 320 + btn_spacing, btn_width, btn_height)
        is_hover = self.continue_btn_rect.collidepoint(mouse_pos)
        btn_color = (100, 150, 220) if is_hover else (70, 120, 180)
        pygame.draw.rect(screen, btn_color, self.continue_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.continue_btn_rect, 2, border_radius=12)
        continue_text = font_medium.render("继续游戏", True, WHITE)
        continue_rect = continue_text.get_rect(center=self.continue_btn_rect.center)
        screen.blit(continue_text, continue_rect)

        self.menu_settings_btn_rect = pygame.Rect(center_x - btn_width // 2, 320 + btn_spacing * 2, btn_width, btn_height)
        is_hover = self.menu_settings_btn_rect.collidepoint(mouse_pos)
        btn_color = (150, 130, 80) if is_hover else (120, 100, 60)
        pygame.draw.rect(screen, btn_color, self.menu_settings_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.menu_settings_btn_rect, 2, border_radius=12)
        settings_text = font_medium.render("设置", True, WHITE)
        settings_rect = settings_text.get_rect(center=self.menu_settings_btn_rect.center)
        screen.blit(settings_text, settings_rect)

        self.exit_btn_rect = pygame.Rect(center_x - btn_width // 2, 320 + btn_spacing * 3, btn_width, btn_height)
        is_hover = self.exit_btn_rect.collidepoint(mouse_pos)
        btn_color = (180, 80, 80) if is_hover else (150, 60, 60)
        pygame.draw.rect(screen, btn_color, self.exit_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.exit_btn_rect, 2, border_radius=12)
        exit_text = font_medium.render("退出", True, WHITE)
        exit_rect = exit_text.get_rect(center=self.exit_btn_rect.center)
        screen.blit(exit_text, exit_rect)

        version_text = font_tiny.render("v2.0 - 真实伤害/反伤/护盾/吸血", True, GRAY)
        version_rect = version_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        screen.blit(version_text, version_rect)

    def draw_level_select(self):
        """绘制选关界面"""
        subtitle = font_medium.render("选择关卡", True, LIGHT_GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(subtitle, subtitle_rect)

        self.level_buttons = []
        start_y = 200
        spacing = 90

        for i, level in enumerate(LEVELS):
            y = start_y + i * spacing
            locked = i >= self.state.unlocked_levels

            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, y, 400, 70)
            self.level_buttons.append(btn_rect)

            if locked:
                pygame.draw.rect(screen, DARK_GRAY, btn_rect, border_radius=15)
                lock_text = font_medium.render(f"锁定 {level['name']}", True, GRAY)
            else:
                is_hovered = btn_rect.collidepoint(pygame.mouse.get_pos())
                btn_color = tuple(min(255, c + 30) for c in level['color']) if is_hovered else level['color']
                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=15)
                pygame.draw.rect(screen, WHITE, btn_rect, 2, border_radius=15)

                level_text = f"{level['name']} - {level['enemy_name']}"
                lock_text = font_medium.render(level_text, True, WHITE)

            lock_rect = lock_text.get_rect(center=(btn_rect.centerx, btn_rect.centery))
            screen.blit(lock_text, lock_rect)

        stats_text = font_small.render(f"胜利: {self.state.wins}  失败: {self.state.losses}", True, LIGHT_GRAY)
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(stats_text, stats_rect)

    def draw_settings(self):
        """绘制设置界面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        panel_width, panel_height = 500, 400
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 40, 60), panel_rect, border_radius=20)
        pygame.draw.rect(screen, YELLOW, panel_rect, 3, border_radius=20)

        title = font_large.render("设置", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 50))
        screen.blit(title, title_rect)

        # 音乐开关
        music_y = panel_y + 120
        music_label = font_medium.render("音乐", True, WHITE)
        screen.blit(music_label, (panel_x + 60, music_y))

        self.music_toggle_rect = pygame.Rect(panel_x + 350, music_y, 80, 40)
        music_state = "开启" if self.sound.music_enabled else "关闭"
        music_color = (100, 200, 100) if self.sound.music_enabled else (200, 100, 100)
        pygame.draw.rect(screen, music_color, self.music_toggle_rect, border_radius=10)
        music_text = font_small.render(music_state, True, WHITE)
        music_text_rect = music_text.get_rect(center=self.music_toggle_rect.center)
        screen.blit(music_text, music_text_rect)

        # 音量滑块
        volume_y = music_y + 60
        volume_label = font_small.render(f"音量: {int(self.sound.music_volume * 100)}%", True, LIGHT_GRAY)
        screen.blit(volume_label, (panel_x + 60, volume_y))

        self.volume_slider_rect = pygame.Rect(panel_x + 150, volume_y + 5, 250, 20)
        pygame.draw.rect(screen, DARK_GRAY, self.volume_slider_rect, border_radius=10)

        fill_width = int(self.sound.music_volume * 250)
        fill_rect = pygame.Rect(panel_x + 150, volume_y + 5, fill_width, 20)
        pygame.draw.rect(screen, (100, 200, 100), fill_rect, border_radius=10)

        handle_x = panel_x + 150 + fill_width
        pygame.draw.circle(screen, WHITE, (handle_x, volume_y + 15), 12)

        # 音效开关
        sfx_y = volume_y + 60
        sfx_label = font_medium.render("音效", True, WHITE)
        screen.blit(sfx_label, (panel_x + 60, sfx_y))

        self.sfx_toggle_rect = pygame.Rect(panel_x + 350, sfx_y, 80, 40)
        sfx_state = "开启" if self.sound.sfx_enabled else "关闭"
        sfx_color = (100, 200, 100) if self.sound.sfx_enabled else (200, 100, 100)
        pygame.draw.rect(screen, sfx_color, self.sfx_toggle_rect, border_radius=10)
        sfx_text = font_small.render(sfx_state, True, WHITE)
        sfx_text_rect = sfx_text.get_rect(center=self.sfx_toggle_rect.center)
        screen.blit(sfx_text, sfx_text_rect)

        # 返回按钮
        self.settings_back_rect = pygame.Rect(panel_x + 30, panel_y + panel_height - 70, 130, 50)
        pygame.draw.rect(screen, (100, 150, 255), self.settings_back_rect, border_radius=12)
        back_text = font_medium.render("返回", True, WHITE)
        back_rect = back_text.get_rect(center=self.settings_back_rect.center)
        screen.blit(back_text, back_rect)

        self.settings_home_rect = pygame.Rect(panel_x + 340, panel_y + panel_height - 70, 130, 50)
        pygame.draw.rect(screen, (150, 100, 100), self.settings_home_rect, border_radius=12)
        home_text = font_medium.render("返回主页", True, WHITE)
        home_rect = home_text.get_rect(center=self.settings_home_rect.center)
        screen.blit(home_text, home_rect)

    def draw_battle(self):
        """绘制战斗界面"""
        level_info = LEVELS[self.state.current_level]

        # 敌人信息
        enemy_name = font_medium.render(f"敌人: {level_info['enemy_name']}", True, level_info['color'])
        enemy_rect = enemy_name.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(enemy_name, enemy_rect)

        # 玩家血条+护盾
        draw_health_bar(screen, 50, 30, 250, 35,
                       self.state.player_health, self.state.max_health, "玩家", self.state.player_shield)

        # 玩家能量
        energy_text = font_small.render(f"⚡能量: {self.state.player_energy}/{self.state.max_energy}", True, YELLOW)
        screen.blit(energy_text, (50, 70))

        # AI血条+护盾
        draw_health_bar(screen, SCREEN_WIDTH - 300, 30, 250, 35,
                       self.state.ai_health, self.state.ai_health if self.state.ai_health > 100 else 100, "AI", self.state.ai_shield)

        # AI能量
        ai_energy_text = font_small.render(f"⚡能量: {self.state.ai_energy}/{self.state.max_energy}", True, YELLOW)
        screen.blit(ai_energy_text, (SCREEN_WIDTH - 150, 70))

        # 回合指示器
        turn_text = "你的回合" if self.state.is_player_turn else "AI回合"
        turn_color = (100, 150, 255) if self.state.is_player_turn else (255, 100, 100)
        turn_surf = font_medium.render(turn_text, True, turn_color)
        turn_rect = turn_surf.get_rect(center=(SCREEN_WIDTH // 2, 115))
        pygame.draw.rect(screen, DARK_GRAY, turn_rect.inflate(40, 20), border_radius=15)
        screen.blit(turn_surf, turn_rect)

        # 战场区域
        pygame.draw.rect(screen, (30, 30, 60), (100, 160, SCREEN_WIDTH - 200, 180), border_radius=20)

        # 玩家出牌区
        player_label = font_small.render("你的出牌", True, LIGHT_GRAY)
        screen.blit(player_label, (150, 170))

        if self.state.player_played_cards:
            card_spacing = 130
            total_width = len(self.state.player_played_cards) * card_spacing
            start_x = (SCREEN_WIDTH // 2 - 200 - total_width) // 2
            for i, card in enumerate(self.state.player_played_cards):
                x = start_x + i * card_spacing
                draw_card(screen, card, x, 190)
                pygame.draw.circle(screen, RED, (x + 12, 177), 12)
                撤回_text = font_tiny.render("×", True, WHITE)
                撤回_text_rect = 撤回_text.get_rect(center=(x + 12, 177))
                screen.blit(撤回_text, 撤回_text_rect)

        # VS
        vs_text = font_large.render("VS", True, YELLOW)
        vs_rect = vs_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        pygame.draw.circle(screen, (255, 100, 50), vs_rect.center, 40)
        screen.blit(vs_text, vs_rect)

        # AI出牌区
        ai_label = font_small.render("AI出牌", True, LIGHT_GRAY)
        screen.blit(ai_label, (SCREEN_WIDTH - 250, 170))

        if self.state.ai_played_cards:
            card_spacing = 130
            total_width = len(self.state.ai_played_cards) * card_spacing
            start_x = SCREEN_WIDTH // 2 + 80
            for i, card in enumerate(self.state.ai_played_cards):
                x = start_x + i * card_spacing
                draw_card(screen, card, x, 190)

        # 伤害/治疗显示
        if self.state.show_damage:
            if self.state.player_damage > 0:
                dmg_text = font_large.render(f"-{self.state.player_damage}", True, RED)
                screen.blit(dmg_text, (SCREEN_WIDTH // 2 - 100, 380))
            if self.state.ai_damage > 0:
                dmg_text = font_large.render(f"-{self.state.ai_damage}", True, RED)
                screen.blit(dmg_text, (SCREEN_WIDTH // 2 + 100, 380))

        if self.state.show_heal:
            if self.state.player_heal > 0:
                heal_text = font_medium.render(f"+{self.state.player_heal}", True, GREEN)
                screen.blit(heal_text, (SCREEN_WIDTH // 2 - 150, 380))
            if self.state.ai_heal > 0:
                heal_text = font_medium.render(f"+{self.state.ai_heal}", True, GREEN)
                screen.blit(heal_text, (SCREEN_WIDTH // 2 + 150, 380))

        # 本轮结果
        if self.state.battle_result:
            result_texts = {
                'win': ('胜 本轮胜利！', GREEN),
                'lose': ('负 本轮失败！', RED),
                'draw': ('平 本轮平局！', YELLOW)
            }
            text, color = result_texts[self.state.battle_result]
            result_surf = font_medium.render(text, True, color)
            result_rect = result_surf.get_rect(center=(SCREEN_WIDTH // 2, 420))
            screen.blit(result_surf, result_rect)

        # 手牌剩余
        player_hand_count = font_small.render(f"剩余: {len(self.state.player_hand)}", True, (100, 200, 255))
        screen.blit(player_hand_count, (50, 355))
        ai_hand_count = font_small.render(f"剩余: {len(self.state.ai_hand)}", True, (255, 200, 100))
        screen.blit(ai_hand_count, (SCREEN_WIDTH - 100, 355))

        # 日志
        self.draw_log()

        # 手牌区
        hand_label = font_small.render("你的手牌（点击出牌，Hover查看详情）", True, LIGHT_GRAY)
        hand_label_rect = hand_label.get_rect(center=(SCREEN_WIDTH // 2, 450))
        screen.blit(hand_label, hand_label_rect)

        hand_y = 480
        card_spacing = 130
        total_width = len(self.state.player_hand) * card_spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        self.hovered_card = None

        for i, card in enumerate(self.state.player_hand):
            x = start_x + i * card_spacing
            can_play = (self.state.is_player_turn and self.state.game_started
                       and self.state.player_energy >= card.energy)

            mouse_pos = pygame.mouse.get_pos()
            card_rect = pygame.Rect(x, hand_y, CARD_WIDTH, CARD_HEIGHT)

            if can_play:
                if card_rect.collidepoint(mouse_pos):
                    draw_card(screen, card, x, hand_y - 20, hover=True)
                    self.hovered_card = i
                    # 显示详情
                    self.show_card_detail = True
                    self.detail_card = card
                else:
                    draw_card(screen, card, x, hand_y)
            else:
                draw_card(screen, card, x, hand_y, disabled=True)

        # 结束回合按钮
        if self.state.is_player_turn and self.state.game_started and not self.state.turn_action_done:
            self.end_turn_btn_rect = pygame.Rect(SCREEN_WIDTH - 90, SCREEN_HEIGHT - 90, 70, 70)
            mouse_pos = pygame.mouse.get_pos()
            btn_hovered = self.end_turn_btn_rect.collidepoint(mouse_pos)
            btn_color = (100, 200, 100) if btn_hovered else (60, 140, 60)
            pygame.draw.circle(screen, btn_color, (SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55), 35)
            pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55), 35, 3)
            end_text = font_small.render("结束", True, WHITE)
            end_rect = end_text.get_rect(center=(SCREEN_WIDTH - 55, SCREEN_HEIGHT - 60))
            screen.blit(end_text, end_rect)
            end_text2 = font_small.render("回合", True, WHITE)
            end_rect2 = end_text2.get_rect(center=(SCREEN_WIDTH - 55, SCREEN_HEIGHT - 40))
            screen.blit(end_text2, end_rect2)

        # 显示卡牌详情
        if self.show_card_detail and self.detail_card and self.hovered_card is not None:
            mouse_pos = pygame.mouse.get_pos()
            detail_x = mouse_pos[0] + 20
            detail_y = mouse_pos[1] - 100
            # 确保不超出屏幕
            if detail_x + 300 > SCREEN_WIDTH:
                detail_x = mouse_pos[0] - 320
            if detail_y < 10:
                detail_y = 10
            if detail_y + 200 > SCREEN_HEIGHT - 100:
                detail_y = SCREEN_HEIGHT - 210
            draw_card_detail(screen, self.detail_card, detail_x, detail_y)

    def draw_log(self):
        """绘制日志区域"""
        log_rect = pygame.Rect(50, SCREEN_HEIGHT - 180, 350, 160)
        pygame.draw.rect(screen, (20, 20, 30), log_rect, border_radius=10)

        log_title = font_tiny.render("战斗日志", True, YELLOW)
        screen.blit(log_title, (60, SCREEN_HEIGHT - 170))

        for i, log in enumerate(self.state.logs[:8]):
            log_text = font_tiny.render(log[:45], True, LIGHT_GRAY)
            screen.blit(log_text, (60, SCREEN_HEIGHT - 145 + i * 18))

        # 游戏结束遮罩
        if self.state.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            if self.state.winner == 'player':
                game_over_text = font_large.render("胜利！", True, YELLOW)
            else:
                game_over_text = font_large.render("失败", True, RED)

            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
            screen.blit(game_over_text, text_rect)

            stats = font_small.render(
                f"胜利: {self.state.wins}  失败: {self.state.losses}  回合: {self.state.round}",
                True, WHITE)
            stats_rect = stats.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70))
            screen.blit(stats, stats_rect)

            center_x = SCREEN_WIDTH // 2
            center_y = SCREEN_HEIGHT // 2

            btn_y1 = center_y - 20
            btn_y2 = center_y + 40
            btn_y3 = center_y + 100

            if self.state.winner == 'player' and self.state.current_level < len(LEVELS) - 1:
                self.next_level_btn_rect = pygame.Rect(center_x - 80, btn_y1, 160, 45)
                mouse_pos = pygame.mouse.get_pos()
                hover = self.next_level_btn_rect.collidepoint(mouse_pos)
                btn_color = (100, 200, 100) if hover else (60, 150, 60)
                pygame.draw.rect(screen, btn_color, self.next_level_btn_rect, border_radius=10)
                next_text = font_medium.render("下一关", True, WHITE)
                next_rect = next_text.get_rect(center=self.next_level_btn_rect.center)
                screen.blit(next_text, next_rect)

            self.restart_btn_rect = pygame.Rect(center_x - 80, btn_y2, 160, 45)
            mouse_pos = pygame.mouse.get_pos()
            hover = self.restart_btn_rect.collidepoint(mouse_pos)
            btn_color = (100, 150, 255) if hover else (60, 100, 200)
            pygame.draw.rect(screen, btn_color, self.restart_btn_rect, border_radius=10)
            restart_text = font_medium.render("再来一次", True, WHITE)
            restart_rect = restart_text.get_rect(center=self.restart_btn_rect.center)
            screen.blit(restart_text, restart_rect)

            self.home_btn_rect = pygame.Rect(center_x - 80, btn_y3, 160, 45)
            hover = self.home_btn_rect.collidepoint(mouse_pos)
            btn_color = (150, 150, 150) if hover else (100, 100, 100)
            pygame.draw.rect(screen, btn_color, self.home_btn_rect, border_radius=10)
            home_text = font_medium.render("返回首页", True, WHITE)
            home_rect = home_text.get_rect(center=self.home_btn_rect.center)
            screen.blit(home_text, home_rect)

    def start_game(self):
        """开始游戏"""
        self.sound.play('click')
        self.sound.play_bgm()
        self.state.reset(keep_stats=True)
        self.state.game_started = True
        self.state.selecting_level = False
        self.state.level_cleared = False
        self.state.round = 0
        self.state.player_health = 100
        self.state.max_health = 100
        self.state.player_shield = 0
        self.state.ai_shield = 0

        # 能量系统（每回合+2，上限7）
        self.state.player_energy = 3
        self.state.ai_energy = 3

        # 根据关卡设置AI血量
        level_info = LEVELS[self.state.current_level]
        self.state.ai_health = level_info['ai_health']

        # 获取当前关卡的敌人卡池
        enemy_pool = ENEMY_CARD_POOLS.get(self.state.current_level, GOBLIN_CARDS)
        self.enemy_card_pool = enemy_pool

        self.state.player_hand = self.draw_cards(6, use_player_pool=True)
        self.state.ai_hand = self.draw_cards(6, use_player_pool=False)

        self.state.player_played_cards = []
        self.state.ai_played_cards = []
        self.state.turn_action_done = False

        self.state.add_log(f"{level_info['name']} 开始！")
        self.state.add_log(f"敌人: {level_info['enemy_name']}")
        self.state.add_log("能量: 点击卡牌出牌")

    def draw_cards(self, count: int, use_player_pool: bool = True) -> List[Card]:
        """抽牌"""
        pool = PLAYER_CARD_LIBRARY if use_player_pool else getattr(self, 'enemy_card_pool', GOBLIN_CARDS)
        return [copy.copy(random.choice(pool)) for _ in range(count)]

    def player_play_card(self, index: int):
        """玩家出牌"""
        if not self.state.is_player_turn or not self.state.game_started:
            return
        if self.state.turn_action_done:
            return

        card = self.state.player_hand[index]

        if self.state.player_energy < card.energy:
            self.state.add_log(f"能量不足！需要{card.energy}点")
            return

        # 消耗能量
        self.state.player_energy -= card.energy

        # 从手牌移除，加入出牌区
        card = self.state.player_hand.pop(index)
        self.state.player_played_cards.append(card)
        self.sound.play('play_card')

        self.state.add_log(f"出牌: {card.name}")
        # 效果将在回合结束时统一结算

    def ai_play_card(self):
        """AI出牌"""
        if not self.state.ai_hand:
            self.state.turn_action_done = True
            pygame.time.set_timer(pygame.USEREVENT + 2, 500)
            return

        # AI策略：优先出高分卡牌
        while self.state.ai_energy > 0 and self.state.ai_hand:
            affordable_cards = [i for i, card in enumerate(self.state.ai_hand)
                              if card.energy <= self.state.ai_energy]

            if not affordable_cards:
                break

            best_index = affordable_cards[0]
            best_score = -float('inf')

            for i in affordable_cards:
                card = self.state.ai_hand[i]
                score = card.attack + card.magic_attack + card.real_damage * 2 + card.defense

                # AI优先使用能造成伤害的牌
                if card.attack + card.magic_attack + card.real_damage > 15:
                    score += 10

                if score > best_score:
                    best_score = score
                    best_index = i

            card = self.state.ai_hand[best_index]

            self.state.ai_energy -= card.energy
            card = self.state.ai_hand.pop(best_index)
            self.state.ai_played_cards.append(card)
            self.sound.play('play_card')
            self.state.add_log(f"AI出牌: {card.name}")
            # AI效果将在回合结束时统一结算

        self.state.turn_action_done = True
        pygame.time.set_timer(pygame.USEREVENT + 2, 500)

    def end_turn(self):
        """玩家主动结束回合"""
        if not self.state.is_player_turn or not self.state.game_started:
            return
        if self.state.turn_action_done:
            return

        self.state.turn_action_done = True
        self.sound.play('click')

        if not self.state.player_played_cards:
            self.state.player_played_cards = []

        pygame.time.set_timer(pygame.USEREVENT + 1, 800)

    def calculate_battle(self):
        """计算战斗结果（增强版）"""
        player_cards = self.state.player_played_cards
        ai_cards = self.state.ai_played_cards

        self.state.round += 1

        # ========== 回合计时生效的效果 ==========
        # 玩家出牌区的即时效果（护盾+治疗）
        for card in player_cards:
            if card.shield > 0:
                self.state.player_shield += card.shield
                self.state.add_log(f"{card.name} 提供 {card.shield} 护盾！")
                self.sound.play('shield')
            if card.heal > 0:
                heal_amount = min(card.heal, self.state.max_health - self.state.player_health)
                if heal_amount > 0:
                    self.state.player_health += heal_amount
                    self.state.player_heal = heal_amount
                    self.state.show_heal = True
                    self.state.add_log(f"{card.name} 治疗 {heal_amount} 点生命！")
                    self.sound.play('heal')

        # AI出牌区的即时效果
        for card in ai_cards:
            if card.shield > 0:
                self.state.ai_shield += card.shield
                self.state.add_log(f"{card.name} AI获得 {card.shield} 护盾")
            if card.heal > 0:
                heal_amount = min(card.heal, self.state.max_health - self.state.ai_health)
                if heal_amount > 0:
                    self.state.ai_health += heal_amount
                    self.state.ai_heal = heal_amount
                    self.state.add_log(f"{card.name} AI治疗 {heal_amount} 点")
        # =========================================

        # 计算玩家总输出
        player_phys_atk = sum(card.attack for card in player_cards)
        player_magic_atk = sum(card.magic_attack for card in player_cards)
        player_real_dmg = sum(card.real_damage for card in player_cards)
        player_armor = sum(card.armor for card in player_cards)
        player_lifesteal = max((card.lifesteal for card in player_cards), default=0)
        player_reflect = max((card.reflect_damage for card in player_cards), default=0)

        # 计算AI总输出
        ai_phys_atk = sum(card.attack for card in ai_cards)
        ai_magic_atk = sum(card.magic_attack for card in ai_cards)
        ai_real_dmg = sum(card.real_damage for card in ai_cards)
        ai_armor = sum(card.armor for card in ai_cards)
        ai_lifesteal = max((card.lifesteal for card in ai_cards), default=0)
        ai_reflect = max((card.reflect_damage for card in ai_cards), default=0)

        # 伤害计算
        # 玩家对AI的伤害
        phys_dmg_to_ai = max(0, player_phys_atk - ai_armor)
        magic_dmg_to_ai = max(0, player_magic_atk - sum(c.magic_defense for c in ai_cards))
        total_dmg_to_ai = phys_dmg_to_ai + magic_dmg_to_ai + player_real_dmg

        # AI对玩家的伤害
        phys_dmg_to_player = max(0, ai_phys_atk - player_armor)
        magic_dmg_to_player = max(0, ai_magic_atk - sum(c.magic_defense for c in player_cards))
        total_dmg_to_player = phys_dmg_to_player + magic_dmg_to_player + ai_real_dmg

        # 应用护盾
        if self.state.ai_shield > 0:
            shield_damage = min(self.state.ai_shield, total_dmg_to_ai)
            self.state.ai_shield -= shield_damage
            total_dmg_to_ai -= shield_damage
            if shield_damage > 0:
                self.state.add_log(f"AI护盾吸收 {shield_damage} 伤害")

        if self.state.player_shield > 0:
            shield_damage = min(self.state.player_shield, total_dmg_to_player)
            self.state.player_shield -= shield_damage
            total_dmg_to_player -= shield_damage
            if shield_damage > 0:
                self.state.add_log(f"你的护盾吸收 {shield_damage} 伤害")

        # 反伤处理
        player_takes_reflect = 0
        ai_takes_reflect = 0

        if player_reflect > 0 and total_dmg_to_player > 0:
            player_takes_reflect = int(total_dmg_to_player * player_reflect / 100)
            total_dmg_to_ai += player_takes_reflect

        if ai_reflect > 0 and total_dmg_to_ai > 0:
            ai_takes_reflect = int(total_dmg_to_ai * ai_reflect / 100)
            total_dmg_to_player += ai_takes_reflect

        # 吸血处理
        if player_lifesteal > 0 and total_dmg_to_ai > 0:
            lifesteal_heal = int(total_dmg_to_ai * player_lifesteal / 100)
            actual_heal = min(lifesteal_heal, self.state.max_health - self.state.player_health)
            if actual_heal > 0:
                self.state.player_health += actual_heal
                self.state.player_heal = actual_heal
                self.state.show_heal = True
                self.state.add_log(f"吸血回复 {actual_heal} 点")

        if ai_lifesteal > 0 and total_dmg_to_player > 0:
            lifesteal_heal = int(total_dmg_to_player * ai_lifesteal / 100)
            if lifesteal_heal > 0:
                self.state.ai_health = min(self.state.ai_health + lifesteal_heal, self.state.ai_health + 50)
                self.state.ai_heal = lifesteal_heal

        # 应用最终伤害
        self.state.ai_health = max(0, self.state.ai_health - total_dmg_to_ai)
        self.state.player_health = max(0, self.state.player_health - total_dmg_to_player)

        # 显示动画
        self.state.player_damage = total_dmg_to_player
        self.state.ai_damage = total_dmg_to_ai
        self.state.show_damage = True

        # 日志
        self.state.add_log(f"--- 第 {self.state.round} 回合 ---")

        if player_cards:
            card_names = "、".join([c.name for c in player_cards])
            self.state.add_log(f"你出牌: {card_names}")
            self.state.add_log(f"总攻击: ⚔️{player_phys_atk} 🔮{player_magic_atk} ⚔️{player_real_dmg}真实")
        else:
            self.state.add_log("你选择不出牌")

        if ai_cards:
            ai_card_names = "、".join([c.name for c in ai_cards])
            self.state.add_log(f"AI出牌: {ai_card_names}")
            self.state.add_log(f"AI攻击: ⚔️{ai_phys_atk} 🔮{ai_magic_atk} ⚔️{ai_real_dmg}真实")

        if total_dmg_to_ai > 0:
            self.state.add_log(f"你对AI造成 {total_dmg_to_ai} 伤害！")
        if total_dmg_to_player > 0:
            self.state.add_log(f"AI对你造成 {total_dmg_to_player} 伤害！")
        if player_takes_reflect > 0:
            self.state.add_log(f"反伤！你受到 {player_takes_reflect} 反射伤害！")
        if ai_takes_reflect > 0:
            self.state.add_log(f"AI反伤！受到 {ai_takes_reflect} 反射伤害！")

        # 本轮结果
        if total_dmg_to_ai > total_dmg_to_player:
            self.state.battle_result = 'win'
        elif total_dmg_to_ai < total_dmg_to_player:
            self.state.battle_result = 'lose'
        else:
            self.state.battle_result = 'draw'

        self.sound.play('attack')
        pygame.time.set_timer(pygame.USEREVENT + 3, 1500)

    def end_round(self):
        """结束回合"""
        # 抽牌（每回合1张，上限6张）
        if len(self.state.player_hand) < 6:
            self.state.player_hand.append(self.draw_cards(1, use_player_pool=True)[0])
            self.sound.play('draw')
        if len(self.state.ai_hand) < 6:
            self.state.ai_hand.append(self.draw_cards(1, use_player_pool=False)[0])

        # 能量回复（+2点，上限7点）
        self.state.player_energy = min(self.state.max_energy, self.state.player_energy + 2)
        self.state.ai_energy = min(self.state.max_energy, self.state.ai_energy + 2)

        # 清空状态
        self.state.player_played_cards = []
        self.state.ai_played_cards = []
        self.state.battle_result = ''
        self.state.show_damage = False
        self.state.show_heal = False
        self.state.turn_action_done = False

        # 检查游戏结束
        if self.state.player_health <= 0:
            self.state.game_over = True
            self.state.winner = 'ai'
            self.state.losses += 1
            self.state.add_log("很遗憾，你输了...")
            self.sound.play('defeat')
            return

        if self.state.ai_health <= 0:
            self.state.game_over = True
            self.state.winner = 'player'
            self.state.wins += 1
            self.state.level_cleared = True
            self.state.unlock_next_level()

            level_name = LEVELS[self.state.current_level]['name']
            self.state.add_log(f"{level_name} 通关！")
            if self.state.current_level + 1 < len(LEVELS):
                self.state.add_log(f"解锁了 {LEVELS[self.state.current_level + 1]['name']}！")
            else:
                self.state.add_log("你已通关所有关卡！")
            self.sound.play('victory')
            return

        self.state.is_player_turn = True
        self.state.add_log(f"第 {self.state.round + 1} 回合开始")
        self.state.add_log(f"能量回复: {self.state.player_energy}/{self.state.max_energy}")

    def get_card_at_mouse(self) -> Optional[int]:
        """获取鼠标位置下的手牌索引"""
        if not self.state.is_player_turn or not self.state.game_started or self.state.turn_action_done or self.state.game_over:
            return None

        mouse_pos = pygame.mouse.get_pos()
        hand_y = 480
        card_spacing = 130
        total_width = len(self.state.player_hand) * card_spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, card in enumerate(self.state.player_hand):
            x = start_x + i * card_spacing
            card_rect = pygame.Rect(x, hand_y - 20, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(mouse_pos):
                return i
        return None

    def get_recallable_card_at_mouse(self) -> Optional[int]:
        """获取可撤回卡牌"""
        if not self.state.is_player_turn or not self.state.game_started or self.state.turn_action_done or self.state.game_over:
            return None
        if not self.state.player_played_cards:
            return None

        mouse_pos = pygame.mouse.get_pos()
        card_spacing = 130
        total_width = len(self.state.player_played_cards) * card_spacing
        start_x = (SCREEN_WIDTH // 2 - 200 - total_width) // 2

        for i, card in enumerate(self.state.player_played_cards):
            x = start_x + i * card_spacing
            card_rect = pygame.Rect(x, 190, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(mouse_pos):
                return i
        return None

    def recall_card(self, index: int):
        """撤回已出牌"""
        if index is None or index >= len(self.state.player_played_cards):
            return

        card = self.state.player_played_cards.pop(index)
        self.state.player_energy += card.energy
        self.state.player_hand.append(card)
        self.sound.play('click')
        self.state.add_log(f"撤回: {card.name}（返还{card.energy}能量）")

    def handle_event(self, event: pygame.event):
        """处理事件"""
        if event.type == pygame.QUIT:
            pygame.quit()
            import sys
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos

                # 悬停检测重置
                self.show_card_detail = False
                self.detail_card = None

                # 主菜单
                if self.state.in_main_menu:
                    if hasattr(self, 'new_game_btn_rect') and self.new_game_btn_rect.collidepoint(mouse_pos):
                        self.state.selecting_level = True
                        self.state.in_main_menu = False
                        self.sound.play('click')
                        return
                    elif hasattr(self, 'continue_btn_rect') and self.continue_btn_rect.collidepoint(mouse_pos):
                        self.state.in_main_menu = False
                        self.sound.play('click')
                        return
                    elif hasattr(self, 'menu_settings_btn_rect') and self.menu_settings_btn_rect.collidepoint(mouse_pos):
                        self.state.in_settings = True
                        self.state.in_main_menu = False  # 关闭主页模式
                        self.sound.play('click')
                        return
                    elif hasattr(self, 'exit_btn_rect') and self.exit_btn_rect.collidepoint(mouse_pos):
                        self.sound.play('click')
                        pygame.quit()
                        import sys
                        sys.exit()
                    return

                # 设置按钮
                if not self.state.in_settings and hasattr(self, 'settings_btn_rect'):
                    if self.settings_btn_rect.collidepoint(mouse_pos):
                        self.state.in_settings = True
                        self.sound.play('click')
                        return

                # 设置界面
                if self.state.in_settings:
                    if hasattr(self, 'music_toggle_rect') and self.music_toggle_rect.collidepoint(mouse_pos):
                        self.sound.music_enabled = not self.sound.music_enabled
                        if self.sound.music_enabled:
                            self.sound.play_bgm()
                        else:
                            self.sound.stop_bgm()
                        self.sound.play('click')
                        self.sound.save_settings()
                        return

                    if hasattr(self, 'sfx_toggle_rect') and self.sfx_toggle_rect.collidepoint(mouse_pos):
                        self.sound.sfx_enabled = not self.sound.sfx_enabled
                        if self.sound.sfx_enabled:
                            self.sound.play('click')
                        self.sound.save_settings()
                        return

                    if hasattr(self, 'settings_back_rect') and self.settings_back_rect.collidepoint(mouse_pos):
                        self.state.in_settings = False
                        self.sound.play('click')
                        self.sound.save_settings()
                        return

                    if hasattr(self, 'settings_home_rect') and self.settings_home_rect.collidepoint(mouse_pos):
                        self.state.in_settings = False
                        self.state.reset(keep_stats=True)
                        self.state.in_main_menu = True
                        self.sound.play('click')
                        self.sound.save_settings()
                        return
                    return

                # 选关界面
                if self.state.selecting_level and hasattr(self, 'level_buttons'):
                    for i, btn_rect in enumerate(self.level_buttons):
                        if i < self.state.unlocked_levels and btn_rect.collidepoint(mouse_pos):
                            self.state.current_level = i
                            self.start_game()
                            return

                # 游戏结束按钮
                if self.state.game_over:
                    if hasattr(self, 'next_level_btn_rect') and self.next_level_btn_rect.collidepoint(mouse_pos):
                        if self.state.current_level < len(LEVELS) - 1:
                            self.state.current_level += 1
                        self.start_game()  # 必须调用start_game来初始化关卡
                        return
                    if hasattr(self, 'restart_btn_rect') and self.restart_btn_rect.collidepoint(mouse_pos):
                        self.start_game()  # 必须调用start_game来初始化关卡
                        return
                    if hasattr(self, 'home_btn_rect') and self.home_btn_rect.collidepoint(mouse_pos):
                        self.state.reset(keep_stats=True)
                        self.state.in_main_menu = True
                        return

                # 点击手牌
                card_index = self.get_card_at_mouse()
                if card_index is not None:
                    self.player_play_card(card_index)
                    return

                # 撤回
                recall_index = self.get_recallable_card_at_mouse()
                if recall_index is not None:
                    self.recall_card(recall_index)
                    return

                # 结束回合
                if self.state.is_player_turn and self.state.game_started and not self.state.turn_action_done:
                    if hasattr(self, 'end_turn_btn_rect') and self.end_turn_btn_rect.collidepoint(mouse_pos):
                        self.end_turn()
                        return

        # 悬停效果检测
        if event.type == pygame.MOUSEMOTION:
            if not self.state.in_main_menu and not self.state.in_settings and self.state.game_started:
                card_index = self.get_card_at_mouse()
                if card_index is not None:
                    self.show_card_detail = True
                    self.detail_card = self.state.player_hand[card_index]
                    self.hovered_card = card_index
                else:
                    self.show_card_detail = False
                    self.detail_card = None
                    self.hovered_card = None

        # 计时器事件
        if event.type == pygame.USEREVENT + 1:
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)
            self.ai_play_card()

        elif event.type == pygame.USEREVENT + 2:
            pygame.time.set_timer(pygame.USEREVENT + 2, 0)
            self.calculate_battle()

        elif event.type == pygame.USEREVENT + 3:
            pygame.time.set_timer(pygame.USEREVENT + 3, 0)
            self.end_round()

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.draw()
            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()


# 运行游戏
if __name__ == "__main__":
    game = CardBattleGame()
    game.run()
