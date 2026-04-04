"""
卡牌对战游戏 - Python Pygame版
玩家 vs AI，回合制卡牌战斗
"""

import pygame
import random
import math
import copy
import json
import os
import numpy as np
from dataclasses import dataclass
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

# 卡牌颜色（根据名称分配简单颜色）
CARD_COLORS = [
    (255, 107, 107),   # 红色
    (78, 205, 196),    # 青色
    (168, 85, 247),    # 紫色
    (255, 215, 0),     # 金色
    (255, 100, 0),     # 橙色
    (100, 200, 100),   # 绿色
    (100, 150, 255),   # 蓝色
    (255, 150, 200),   # 粉色
]

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# 卡牌尺寸
CARD_WIDTH = 120
CARD_HEIGHT = 170

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(" 卡牌对战")
clock = pygame.time.Clock()

# 字体设置
# 尝试多个可能的中文字体名称
font_names = ["SimHei", "Microsoft YaHei", "SimSun", "FangSong", "KaiTi", "Arial"]
chinese_font_name = None

for font_name in font_names:
    try:
        test_font = pygame.font.SysFont(font_name, 48)
        test_surface = test_font.render("测试", True, (255, 255, 255))
        if test_surface.get_width() > 20:
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

# emoji字体 - Windows 10/11 自带 Segoe UI Emoji
emoji_font_path = "C:/Windows/Fonts/seguiemj.ttf"
if os.path.exists(emoji_font_path):
    emoji_font_large = pygame.font.Font(emoji_font_path, 48)
    emoji_font_medium = pygame.font.Font(emoji_font_path, 32)
    emoji_font_small = pygame.font.Font(emoji_font_path, 24)
    emoji_font_tiny = pygame.font.Font(emoji_font_path, 18)
else:
    emoji_font_large = emoji_font_medium = emoji_font_small = emoji_font_tiny = None

# emoji字符检测（简化的emoji集合）
def is_emoji(char):
    """检测字符是否为emoji"""
    code = ord(char) if char else 0
    # 常见emoji Unicode范围
    return (0x2600 <= code <= 0x26FF or  # 杂项符号
            0x2700 <= code <= 0x27BF or  # 装饰符号
            0x1F300 <= code <= 0x1F9FF or  # 表情符号
            0x1F600 <= code <= 0x1F64F or  # 表情
            0x1F680 <= code <= 0x1F6FF or  # 交通和地图符号
            0x1F900 <= code <= 0x1F9FF)    # 补充表情符号

def get_emoji_font(font):
    """根据普通字体获取对应的emoji字体"""
    if font == font_large:
        return emoji_font_large
    elif font == font_medium:
        return emoji_font_medium
    elif font == font_small:
        return emoji_font_small
    elif font == font_tiny:
        return emoji_font_tiny
    return emoji_font_small

def blit_text(surface, text, pos, font, color):
    """智能文本渲染，分离中文和emoji"""
    if emoji_font_small is None:
        # 没有emoji字体，直接渲染
        text_surf = font.render(text, True, color)
        if isinstance(pos, tuple):
            rect = text_surf.get_rect(center=pos)
        else:
            rect = text_surf.get_rect(topleft=pos)
        surface.blit(text_surf, rect)
        return rect
    
    # 分离并分别渲染中文和emoji
    x, y = pos if isinstance(pos, tuple) else (pos[0], pos[1])
    
    # 尝试直接渲染，如果成功（没有方块）就用它
    text_surf = font.render(text, True, color)
    # 检测是否有方块（渲染结果宽度为0或异常小）
    if text_surf.get_width() > 5:
        if isinstance(pos, tuple):
            rect = text_surf.get_rect(center=pos)
        else:
            rect = text_surf.get_rect(topleft=pos)
        surface.blit(text_surf, rect)
        return rect
    
    # 如果直接渲染失败（可能有emoji），分段渲染
    emoji_font = get_emoji_font(font)
    if emoji_font is None:
        emoji_font = emoji_font_small
    
    current_text = ""
    i = 0
    while i < len(text):
        char = text[i]
        if is_emoji(char):
            # 先渲染累积的非emoji文本
            if current_text:
                chunk_surf = font.render(current_text, True, color)
                surface.blit(chunk_surf, (x, y))
                x += chunk_surf.get_width()
                current_text = ""
            # 渲染emoji
            emoji_surf = emoji_font.render(char, True, color)
            surface.blit(emoji_surf, (x, y))
            x += emoji_surf.get_width()
        else:
            current_text += char
        i += 1
    
    # 渲染剩余的文本
    if current_text:
        chunk_surf = font.render(current_text, True, color)
        surface.blit(chunk_surf, (x, y))
        x += chunk_surf.get_width()
    
    # 返回一个估算的矩形
    height = font.get_height()
    width = x - (pos[0] if isinstance(pos, tuple) else pos[0])
    return pygame.Rect(pos[0] if isinstance(pos, tuple) else pos[0], 
                      pos[1] if isinstance(pos, tuple) else pos[1], width, height)


@dataclass
class Card:
    """卡牌数据结构"""
    name: str
    icon: str
    card_type: str = ""  # 保留字段但不再使用
    attack: int = 0
    defense: int = 0
    energy: int = 1  # 能量消耗
    
    def get_color(self) -> tuple:
        """获取卡牌颜色 - 根据名称分配"""
        return CARD_COLORS[hash(self.name) % len(CARD_COLORS)]


# 卡牌库（能量消耗：攻击20+ = 3能量，15-19 = 2能量，≤14 = 1能量）
CARD_LIBRARY = [
    Card('战士', '', 'attack', 15, 5, energy=2),      # 2能量
    Card('骑士', '', 'defense', 5, 20, energy=1),    # 1能量
    Card('法师', '🧙', 'magic', 18, 3, energy=2),      # 2能量
    Card('猎人', '🏹', 'attack', 14, 8, energy=1),     # 1能量
    Card('精灵', '🧝', 'magic', 12, 12, energy=1),     # 1能量
    Card('死灵', '💀', 'special', 20, 0, energy=3),    # 3能量
    Card('巨龙', '🐉', 'special', 25, 10, energy=3),  # 3能量
    Card('狐妖', '🦊', 'magic', 10, 15, energy=1),     # 1能量
    Card('刺客', '🗡️', 'attack', 22, 2, energy=3),     # 3能量
    Card('圣骑士', '🪖', 'defense', 8, 18, energy=1),  # 1能量
    Card('巫师', '', 'magic', 16, 6, energy=2),      # 2能量
    Card('狮王', '🦁', 'special', 19, 8, energy=2),    # 2能量
]


# 关卡配置
LEVELS = [
    {'name': '第1关', 'ai_health': 100, 'ai_bonus': 0, 'desc': '入门', 'color': (100, 200, 100)},
    {'name': '第2关', 'ai_health': 105, 'ai_bonus': 5, 'desc': '初级', 'color': (150, 200, 100)},
    {'name': '第3关', 'ai_health': 110, 'ai_bonus': 10, 'desc': '中级', 'color': (200, 180, 100)},
    {'name': '第4关', 'ai_health': 120, 'ai_bonus': 20, 'desc': '高级', 'color': (200, 150, 100)},
    {'name': '第5关', 'ai_health': 130, 'ai_bonus': 30, 'desc': '专家', 'color': (200, 100, 100)},
]


class GameState:
    """游戏状态"""
    def __init__(self):
        self.unlocked_levels = 1  # 默认解锁第1关
        self.current_level = 0    # 当前选择的关卡
        self.in_main_menu = True   # 是否在主菜单
        self.selecting_level = False  # 正在选关
        self.in_settings = False     # 是否在设置界面
        self.reset()
    
    def reset(self, keep_stats=False):
        self.player_health = 100
        self.ai_health = 100
        self.max_health = 100
        self.player_hand: List[Card] = []
        self.ai_hand: List[Card] = []
        self.player_card: Optional[Card] = None
        self.ai_card: Optional[Card] = None
        self.round = 0
        self.is_player_turn = True
        self.game_started = False
        self.battle_result = ''  # '', 'win', 'lose', 'draw'
        self.game_over = False
        self.winner = None
        self.level_cleared = False
        
        # 多牌出牌系统
        self.player_played_cards = []  # 本回合玩家出的牌
        self.ai_played_cards = []  # 本回合AI出的牌
        self.turn_action_done = False  # 本回合是否已执行完成
        
        # 能量系统
        self.player_energy = 3
        self.ai_energy = 3
        self.max_energy = 5  # 能量上限5点
        
        # 统计（可选保留）
        if not keep_stats:
            self.wins = 0
            self.losses = 0
            self.draws = 0
        
        # 动画相关
        self.player_card_pos = None
        self.ai_card_pos = None
        self.player_damage = 0
        self.ai_damage = 0
        self.show_damage = False
        self.damage_timer = 0
        
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


def draw_card_character(surface: pygame.Surface, card: Card, x: int, y: int, width: int, height: int):
    """绘制卡牌角色图案"""
    cx, cy = x + width // 2, y + 55
    
    # 根据卡牌名称绘制不同角色
    name = card.name
    
    if '战士' in name:
        # 战士 - 剑
        pygame.draw.line(surface, (255, 255, 200), (cx - 25, cy + 20), (cx + 25, cy - 20), 6)
        pygame.draw.line(surface, (200, 150, 100), (cx - 25, cy + 20), (cx - 35, cy + 30), 6)
        pygame.draw.rect(surface, (150, 100, 50), (cx - 8, cy + 15, 16, 20), border_radius=3)
    elif '骑士' in name:
        # 骑士 - 盾牌
        pygame.draw.ellipse(surface, (100, 150, 255), (cx - 25, cy - 15, 50, 50))
        pygame.draw.ellipse(surface, (150, 200, 255), (cx - 18, cy - 8, 36, 36))
        pygame.draw.line(surface, (200, 220, 255), (cx, cy - 10), (cx, cy + 18), 3)
        pygame.draw.line(surface, (200, 220, 255), (cx - 12, cy + 4), (cx + 12, cy + 4), 3)
    elif '法师' in name:
        # 法师 - 星星魔法
        for i in range(5):
            angle = i * 72 - 90
            r = 15
            px = cx + r * math.cos(math.radians(angle))
            py = cy + r * math.sin(math.radians(angle))
            pygame.draw.circle(surface, (255, 255, 100), (int(px), int(py)), 5)
        pygame.draw.circle(surface, (255, 255, 200), (int(cx), int(cy)), 8)
    elif '猎人' in name:
        # 猎人 - 弓箭
        pygame.draw.arc(surface, (150, 100, 50), (cx - 20, cy - 20, 40, 40), -45, 45, 4)
        pygame.draw.line(surface, (200, 150, 100), (cx - 10, cy + 10), (cx + 20, cy - 20), 3)
        pygame.draw.polygon(surface, (180, 180, 180), [(cx + 20, cy - 20), (cx + 15, cy - 15), (cx + 25, cy - 15)])
    elif '精灵' in name:
        # 精灵 - 叶子
        points = [(cx, cy - 20), (cx + 20, cy + 15), (cx, cy + 5), (cx - 20, cy + 15)]
        pygame.draw.polygon(surface, (100, 200, 100), points)
        pygame.draw.line(surface, (50, 150, 50), (cx, cy - 15), (cx, cy + 10), 2)
    elif '死灵' in name:
        # 死灵 - 骷髅
        pygame.draw.circle(surface, (220, 220, 220), (int(cx), int(cy - 5)), 15)
        pygame.draw.circle(surface, (0, 0, 0), (int(cx - 5), int(cy - 8)), 4)
        pygame.draw.circle(surface, (0, 0, 0), (int(cx + 5), int(cy - 8)), 4)
        pygame.draw.line(surface, (100, 100, 100), (cx - 5, cy + 2), (cx + 5, cy + 2), 2)
        pygame.draw.line(surface, (180, 180, 180), (cx, cy + 10), (cx, cy + 25), 3)
    elif '巨龙' in name:
        # 巨龙 - 龙头
        pygame.draw.circle(surface, (255, 150, 0), (int(cx), int(cy)), 20)
        pygame.draw.polygon(surface, (255, 200, 0), [(cx - 20, cy - 15), (cx - 30, cy - 30), (cx - 10, cy - 20)])
        pygame.draw.polygon(surface, (255, 200, 0), [(cx + 20, cy - 15), (cx + 30, cy - 30), (cx + 10, cy - 20)])
        pygame.draw.circle(surface, (255, 0, 0), (int(cx - 7), int(cy - 3)), 4)
        pygame.draw.circle(surface, (255, 0, 0), (int(cx + 7), int(cy - 3)), 4)
        # 火焰
        for i in range(3):
            pygame.draw.circle(surface, (255, 100, 0), (int(cx), int(cy + 25 + i * 5)), 4 - i)
    elif '狐妖' in name:
        # 狐妖 - 狐狸脸
        pygame.draw.ellipse(surface, (255, 150, 100), (cx - 18, cy - 12, 36, 30))
        pygame.draw.polygon(surface, (255, 150, 100), [(cx - 18, cy - 5), (cx - 25, cy - 25), (cx - 8, cy - 5)])
        pygame.draw.polygon(surface, (255, 150, 100), [(cx + 18, cy - 5), (cx + 25, cy - 25), (cx + 8, cy - 5)])
        pygame.draw.circle(surface, (50, 50, 50), (int(cx - 6), int(cy - 2)), 3)
        pygame.draw.circle(surface, (50, 50, 50), (int(cx + 6), int(cy - 2)), 3)
        pygame.draw.ellipse(surface, (255, 100, 150), (cx - 3, cy + 5, 6, 4))
    elif '刺客' in name:
        # 刺客 - 匕首
        pygame.draw.line(surface, (180, 180, 190), (cx - 20, cy + 20), (cx + 15, cy - 15), 4)
        pygame.draw.polygon(surface, (180, 180, 190), [(cx + 15, cy - 15), (cx + 25, cy - 25), (cx + 20, cy - 10)])
        pygame.draw.rect(surface, (80, 50, 30), (cx - 25, cy + 15, 12, 15), border_radius=2)
    elif '圣骑士' in name:
        # 圣骑士 - 十字
        pygame.draw.rect(surface, (200, 200, 100), (cx - 5, cy - 22, 10, 44))
        pygame.draw.rect(surface, (200, 200, 100), (cx - 18, cy - 8, 36, 10))
        pygame.draw.circle(surface, (255, 220, 100), (int(cx), int(cy)), 25, 3)
    elif '巫师' in name:
        # 巫师 - 水晶球
        pygame.draw.circle(surface, (100, 50, 150), (int(cx), int(cy)), 18)
        pygame.draw.circle(surface, (150, 100, 200), (int(cx - 5), int(cy - 5)), 6)
        pygame.draw.circle(surface, (255, 255, 255), (int(cx + 5), int(cy + 5)), 3)
        # 光芒
        for i in range(6):
            angle = i * 60
            lx = cx + 22 * math.cos(math.radians(angle))
            ly = cy + 22 * math.sin(math.radians(angle))
            pygame.draw.line(surface, (200, 150, 255), (int(cx + 18 * math.cos(math.radians(angle))), 
                            int(cy + 18 * math.sin(math.radians(angle)))), (int(lx), int(ly)), 2)
    elif '狮王' in name:
        # 狮王 - 狮子头
        pygame.draw.circle(surface, (220, 180, 80), (int(cx), int(cy)), 18)
        # 鬃毛
        for i in range(8):
            angle = i * 45
            lx = cx + 22 * math.cos(math.radians(angle))
            ly = cy + 22 * math.sin(math.radians(angle))
            pygame.draw.circle(surface, (180, 120, 50), (int(lx), int(ly)), 6)
        pygame.draw.circle(surface, (50, 30, 0), (int(cx - 6), int(cy - 3)), 3)
        pygame.draw.circle(surface, (50, 30, 0), (int(cx + 6), int(cy - 3)), 3)
        pygame.draw.polygon(surface, (200, 100, 50), [(cx - 5, cy + 5), (cx, cy + 12), (cx + 5, cy + 5)])


def draw_card(surface: pygame.Surface, card: Card, x: int, y: int, 
              selected=False, hover=False, small=False, face_down=False, disabled=False):
    """绘制卡牌"""
    width = CARD_WIDTH if not small else CARD_WIDTH - 20
    height = CARD_HEIGHT if not small else CARD_HEIGHT - 30
    
    # 阴影
    shadow_rect = pygame.Rect(x + 5, y + 5, width, height)
    pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=15)
    
    # 卡牌背景 - 渐变效果用多层矩形模拟
    card_rect = pygame.Rect(x, y, width, height)
    card_color = card.get_color()
    
    # 能量不足时显示灰色
    if disabled:
        card_color = (80, 80, 80)
    
    # 深色背景
    dark_color = tuple(max(0, c - 80) for c in card_color)
    pygame.draw.rect(surface, dark_color, card_rect, border_radius=15)
    
    # 内层背景
    inner_rect = pygame.Rect(x + 5, y + 5, width - 10, height - 10)
    pygame.draw.rect(surface, card_color, inner_rect, border_radius=12)
    
    # 边框 - 禁用时用灰色
    border_color = (120, 120, 120) if disabled else WHITE
    pygame.draw.rect(surface, border_color, card_rect, 3, border_radius=15)
    
    if face_down:
        # 背面样式 - 神秘图案
        for i in range(3):
            line_y = y + 25 + i * 35
            pygame.draw.rect(surface, (80, 80, 80), 
                          (x + 15, line_y, width - 30, 25), border_radius=5)
        return
    
    # 顶部装饰条
    top_rect = pygame.Rect(x + 8, y + 8, width - 16, 6)
    pygame.draw.rect(surface, WHITE, top_rect, border_radius=3)
    
    # 绘制角色图案
    draw_card_character(surface, card, x, y, width, height)
    
    # 名称背景
    name_bg_rect = pygame.Rect(x + 8, y + height - 65, width - 16, 22)
    pygame.draw.rect(surface, (0, 0, 0, 150), name_bg_rect, border_radius=5)
    
    # 名称
    name_font = font_tiny if not small else pygame.font.Font(None, 18)
    name_text = name_font.render(card.name, True, WHITE)
    name_rect = name_text.get_rect(center=(x + width // 2, y + height - 54))
    surface.blit(name_text, name_rect)
    
    # 属性背景
    stats_y = y + height - 40
    stats_bg = pygame.Rect(x + 8, stats_y, width - 16, 28)
    pygame.draw.rect(surface, (0, 0, 0, 150), stats_bg, border_radius=5)
    
    # 攻击力
    atk_text = font_small.render(f"{card.attack}", True, CARD_COLORS[0])
    surface.blit(atk_text, (x + 15, stats_y + 5))
    
    # 防御力
    def_text = font_small.render(f"{card.defense}", True, CARD_COLORS[1])
    surface.blit(def_text, (x + width - def_text.get_width() - 15, stats_y + 5))
    
    # 能量消耗（显示在右上角）
    energy_color = (255, 215, 0) if not disabled else (100, 100, 100)
    energy_bg_rect = pygame.Rect(x + width - 30, y + 8, 24, 24)
    pygame.draw.circle(surface, energy_color, (x + width - 18, y + 20), 12)
    pygame.draw.circle(surface, (0, 0, 0), (x + width - 18, y + 20), 9)
    energy_text = font_tiny.render(f"{card.energy}", True, energy_color)
    energy_rect = energy_text.get_rect(center=(x + width - 18, y + 20))
    surface.blit(energy_text, energy_rect)
    
    # 选中/悬停效果
    if selected:
        pygame.draw.rect(surface, (255, 215, 0), card_rect, 5, border_radius=15)
    elif hover:
        pygame.draw.rect(surface, (255, 255, 255, 100), card_rect, 3, border_radius=15)


def draw_health_bar(surface: pygame.Surface, x: int, y: int, width: int, height: int,
                    current: int, max_val: int, label: str, is_player: bool):
    """绘制血条"""
    # 背景
    pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height), border_radius=10)
    
    # 血量填充
    percent = max(0, current / max_val)
    fill_width = int(width * percent)
    
    if percent > 0.4:
        color = (0, 200, 100)
    elif percent > 0.2:
        color = (255, 150, 0)
    else:
        color = (255, 50, 50)
    
    if fill_width > 0:
        pygame.draw.rect(surface, color, (x, y, fill_width, height), border_radius=10)
    
    # 文字
    text = font_small.render(f"{label}: {current}/{max_val}", True, WHITE)
    text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text, text_rect)


def draw_button(surface: pygame.Surface, text: str, x: int, y: int, 
                width: int, height: int, color: tuple, hover_color: tuple = None,
                text_color: tuple = WHITE) -> bool:
    """绘制按钮，返回是否被点击"""
    mouse_pos = pygame.mouse.get_pos()
    rect = pygame.Rect(x, y, width, height)
    
    is_hover = rect.collidepoint(mouse_pos) if hover_color else False
    current_color = hover_color if is_hover else color
    
    pygame.draw.rect(surface, current_color, rect, border_radius=15)
    pygame.draw.rect(surface, WHITE, rect, 3, border_radius=15)
    
    text_surf = font_medium.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text_surf, text_rect)
    
    return is_hover


class SoundManager:
    """音效管理器"""
    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.3
        self.sfx_volume = 0.5
        self.enabled = True
        self.music_enabled = True
        self.sfx_enabled = True  # 音效开关
        
        # 加载保存的设置
        self.load_settings()
        
        self._generate_sounds()
        self._generate_bgm()
        
        # 如果音乐关闭则不播放
        if not self.music_enabled and hasattr(self, 'bgm'):
            self.bgm.stop()
    
    def load_settings(self):
        """加载保存的设置"""
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
            pass  # 如果加载失败，使用默认设置
    
    def save_settings(self):
        """保存设置到文件"""
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
            pass  # 保存失败不影响游戏
    
    def _generate_bgm(self):
        """生成背景音乐 - 轻快的战斗旋律"""
        try:
            sample_rate = 44100
            duration = 8  # 8秒循环
            
            # 轻快的战斗音乐旋律
            # 音符频率 (C4=262, D4=294, E4=330, F4=349, G4=392, A4=440, B4=494, C5=523)
            melody = [
                (262, 0.25), (330, 0.25), (392, 0.25), (330, 0.25),  # C E G E
                (294, 0.25), (370, 0.25), (440, 0.25), (370, 0.25),  # D F# A F#
                (262, 0.25), (330, 0.25), (392, 0.5),                # C E G
                (440, 0.25), (392, 0.25), (330, 0.25), (262, 0.5),   # A G E C
                
                (294, 0.25), (349, 0.25), (440, 0.25), (349, 0.25),  # D F A F
                (330, 0.25), (392, 0.25), (523, 0.25), (392, 0.25),  # E G C5 G
                (262, 0.25), (330, 0.25), (392, 0.5),                # C E G
                (523, 0.25), (440, 0.25), (392, 0.25), (330, 0.75),  # C5 A G E
            ]
            
            wave = np.array([], dtype=np.float32)
            
            for freq, note_duration in melody:
                t = np.linspace(0, note_duration, int(sample_rate * note_duration), dtype=np.float32)
                
                # 主旋律 - 正弦波
                melody_wave = np.sin(2 * np.pi * freq * t)
                
                # 和弦 - 低八度
                bass_wave = np.sin(2 * np.pi * (freq / 2) * t) * 0.3
                
                # 高音泛音
                high_wave = np.sin(2 * np.pi * freq * 2 * t) * 0.1
                
                # 包络
                envelope = np.ones_like(t)
                attack = int(sample_rate * 0.02)
                release = int(sample_rate * 0.1)
                envelope[:attack] = np.linspace(0, 1, attack)
                envelope[-release:] = np.linspace(1, 0.3, release)
                
                # 组合
                note = (melody_wave + bass_wave + high_wave) * envelope * 0.4
                
                # 节奏感 - 添加鼓点
                beat_freq = 4  # 每秒4个八分音符
                beat = np.sin(2 * np.pi * 60 * t) * (np.sin(2 * np.pi * beat_freq * t) > 0.8).astype(float) * 0.15
                note += beat
                
                wave = np.concatenate([wave, note])
            
            # 添加淡入淡出
            fade_len = int(sample_rate * 0.5)
            fade_in = np.linspace(0, 1, fade_len)
            fade_out = np.linspace(1, 0.5, fade_len)
            wave[:fade_len] *= fade_in
            wave[-fade_len:] *= fade_out
            
            # 转换为16位立体声
            wave = (wave * 32767 * 0.5).astype(np.int16)
            stereo = np.column_stack((wave, wave))
            
            # 保存为音乐
            self.bgm = pygame.mixer.Sound(array=stereo)
            self.bgm.set_volume(self.music_volume)
            self.bgm_length = len(wave) / sample_rate
            
            print("完成 背景音乐加载成功")
        except Exception as e:
            print(f"警告 背景音乐生成失败: {e}")
            self.music_enabled = False
    
    def play_bgm(self):
        """播放背景音乐"""
        if self.music_enabled and hasattr(self, 'bgm'):
            self.bgm.stop()  # 先停止之前的BGM
            self.bgm.set_volume(self.music_volume)  # 确保音量正确
            self.bgm.play(-1)  # -1 表示循环播放
    
    def stop_bgm(self):
        """停止背景音乐"""
        if hasattr(self, 'bgm'):
            self.bgm.stop()
    
    def set_bgm_volume(self, volume):
        """设置背景音乐音量"""
        self.music_volume = max(0, min(1, volume))
        if hasattr(self, 'bgm'):
            self.bgm.set_volume(self.music_volume)
    
    def _generate_sounds(self):
        """生成音效"""
        try:
            # 出牌音效 - 清脆的"嗖"声
            self.sounds['play_card'] = self._create_beep_sound(800, 0.1, 0.3)
            
            # 攻击音效 - 有力的打击声
            self.sounds['attack'] = self._create_attack_sound()
            
            # 胜利音效 - 欢快的旋律
            self.sounds['victory'] = self._create_victory_sound()
            
            # 失败音效 - 低沉的音符
            self.sounds['defeat'] = self._create_defeat_sound()
            
            # 点击音效
            self.sounds['click'] = self._create_beep_sound(600, 0.05, 0.2)
            
            # 抽牌音效
            self.sounds['draw'] = self._create_beep_sound(1000, 0.08, 0.25)
            
            # 平局音效
            self.sounds['draw'] = self._create_beep_sound(500, 0.15, 0.3)
            
            print("完成 音效加载成功")
        except Exception as e:
            print(f"警告 音效生成失败: {e}")
            self.enabled = False
    
    def _create_beep_sound(self, freq, duration, volume):
        """创建简单的蜂鸣声"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        
        t = np.linspace(0, duration, samples, dtype=np.float32)
        
        # 频率随时间变化
        freq_envelope = freq * (1 + 0.1 * np.sin(2 * np.pi * 10 * t))
        
        # 生成声波
        wave = np.sin(2 * np.pi * freq_envelope * t)
        
        # 添加衰减
        envelope = np.exp(-3 * t / duration)
        wave = wave * envelope * volume
        
        # 转换为16位整数
        wave = (wave * 32767 * 0.3).astype(np.int16)
        
        # 立体声
        stereo = np.column_stack((wave, wave))
        
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound
    
    def _create_attack_sound(self):
        """创建攻击音效"""
        sample_rate = 44100
        duration = 0.2
        samples = int(sample_rate * duration)
        
        t = np.linspace(0, duration, samples, dtype=np.float32)
        
        # 低频冲击
        bass = np.sin(2 * np.pi * 80 * t) * np.exp(-10 * t)
        
        # 高频撕裂
        treble = np.sin(2 * np.pi * 400 * t) * np.exp(-15 * t) * 0.5
        
        # 混合
        wave = bass + treble
        wave = wave * 0.6
        
        wave = (wave * 32767 * 0.4).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        sound = pygame.mixer.Sound(array=stereo)
        sound.set_volume(self.sfx_volume)
        return sound
    
    def _create_victory_sound(self):
        """创建胜利音效 - 上升的旋律"""
        sample_rate = 44100
        
        notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
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
        """创建失败音效 - 下降的旋律"""
        sample_rate = 44100
        
        notes = [392, 330, 262, 196]  # G4, E4, C4, G3
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
        """播放音效"""
        if self.enabled and self.sfx_enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass
    
    def set_volume(self, volume):
        """设置音量"""
        self.sfx_volume = max(0, min(1, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)


class CardBattleGame:
    """卡牌对战游戏主类"""
    def __init__(self):
        self.state = GameState()
        self.hovered_card = None
        self.animation_queue = []
        self.sound = SoundManager()
    
    def draw(self):
        """绘制游戏界面"""
        # 背景
        screen.fill((26, 26, 46))
        
        # 标题
        title = font_large.render(" 卡牌对战", True, (255, 215, 0))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title, title_rect)
        
        # 根据状态绘制不同界面
        if self.state.in_main_menu:
            self.draw_main_menu()
        elif self.state.selecting_level:
            self.draw_level_select()
        else:
            # 战斗界面
            self.draw_battle()
        
        # 设置按钮（所有界面都显示，除了设置界面本身和主菜单）
        if not self.state.in_settings and not self.state.in_main_menu:
            # 放在右上角
            self.settings_btn_rect = pygame.Rect(SCREEN_WIDTH - 90, 5, 80, 25)
            is_hovered = self.settings_btn_rect.collidepoint(pygame.mouse.get_pos())
            btn_color = (80, 80, 100) if is_hovered else (60, 60, 80)
            pygame.draw.rect(screen, btn_color, self.settings_btn_rect, border_radius=6)
            settings_text = font_tiny.render("设置", True, WHITE)
            settings_rect = settings_text.get_rect(center=self.settings_btn_rect.center)
            screen.blit(settings_text, settings_rect)
        
        # 设置界面（覆盖在其他界面上）
        if self.state.in_settings:
            self.draw_settings()
    
    def draw_main_menu(self):
        """绘制主菜单"""
        # 绘制装饰背景
        pygame.draw.rect(screen, (30, 30, 60), (100, 150, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 300), border_radius=20)
        
        # 游戏标题（大号）
        game_title = font_large.render("卡牌对战", True, (255, 215, 0))
        game_title_rect = game_title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(game_title, game_title_rect)
        
        # 副标题
        subtitle = font_small.render("Card Battle", True, LIGHT_GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 250))
        screen.blit(subtitle, subtitle_rect)
        
        # 菜单按钮
        center_x = SCREEN_WIDTH // 2
        btn_width = 200
        btn_height = 50
        btn_spacing = 70
        
        # 新游戏按钮
        self.new_game_btn_rect = pygame.Rect(center_x - btn_width // 2, 320, btn_width, btn_height)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.new_game_btn_rect.collidepoint(mouse_pos)
        btn_color = (60, 180, 80) if is_hover else (50, 150, 60)
        pygame.draw.rect(screen, btn_color, self.new_game_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.new_game_btn_rect, 2, border_radius=12)
        new_game_text = font_medium.render("新游戏", True, WHITE)
        new_game_rect = new_game_text.get_rect(center=self.new_game_btn_rect.center)
        screen.blit(new_game_text, new_game_rect)
        
        # 继续游戏按钮
        self.continue_btn_rect = pygame.Rect(center_x - btn_width // 2, 320 + btn_spacing, btn_width, btn_height)
        is_hover = self.continue_btn_rect.collidepoint(mouse_pos)
        btn_color = (100, 150, 220) if is_hover else (70, 120, 180)
        pygame.draw.rect(screen, btn_color, self.continue_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.continue_btn_rect, 2, border_radius=12)
        continue_text = font_medium.render("继续游戏", True, WHITE)
        continue_rect = continue_text.get_rect(center=self.continue_btn_rect.center)
        screen.blit(continue_text, continue_rect)
        
        # 设置按钮
        self.menu_settings_btn_rect = pygame.Rect(center_x - btn_width // 2, 320 + btn_spacing * 2, btn_width, btn_height)
        is_hover = self.menu_settings_btn_rect.collidepoint(mouse_pos)
        btn_color = (150, 130, 80) if is_hover else (120, 100, 60)
        pygame.draw.rect(screen, btn_color, self.menu_settings_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.menu_settings_btn_rect, 2, border_radius=12)
        settings_text = font_medium.render("设置", True, WHITE)
        settings_rect = settings_text.get_rect(center=self.menu_settings_btn_rect.center)
        screen.blit(settings_text, settings_rect)
        
        # 退出按钮
        self.exit_btn_rect = pygame.Rect(center_x - btn_width // 2, 320 + btn_spacing * 3, btn_width, btn_height)
        is_hover = self.exit_btn_rect.collidepoint(mouse_pos)
        btn_color = (180, 80, 80) if is_hover else (150, 60, 60)
        pygame.draw.rect(screen, btn_color, self.exit_btn_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.exit_btn_rect, 2, border_radius=12)
        exit_text = font_medium.render("退出", True, WHITE)
        exit_rect = exit_text.get_rect(center=self.exit_btn_rect.center)
        screen.blit(exit_text, exit_rect)
        
        # 底部版本信息
        version_text = font_tiny.render("v1.0", True, GRAY)
        version_rect = version_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        screen.blit(version_text, version_rect)
    
    def draw_level_select(self):
        """绘制选关界面"""
        # 副标题
        subtitle = font_medium.render("请选择关卡", True, LIGHT_GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(subtitle, subtitle_rect)
        
        # 关卡按钮
        self.level_buttons = []
        start_y = 200
        spacing = 90
        
        for i, level in enumerate(LEVELS):
            y = start_y + i * spacing
            locked = i >= self.state.unlocked_levels
            
            # 按钮位置
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, y, 400, 70)
            self.level_buttons.append(btn_rect)
            
            if locked:
                # 锁定状态
                pygame.draw.rect(screen, DARK_GRAY, btn_rect, border_radius=15)
                lock_text = font_medium.render(f"锁定 {level['name']} - {level['desc']} (需通关前一关)", True, GRAY)
            else:
                # 可选状态
                is_hovered = btn_rect.collidepoint(pygame.mouse.get_pos())
                btn_color = tuple(min(255, c + 30) for c in level['color']) if is_hovered else level['color']
                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=15)
                pygame.draw.rect(screen, WHITE, btn_rect, 2, border_radius=15)
                
                level_text = f"{level['name']} - {level['desc']}"
                if i < len(LEVELS) - 1:
                    level_text += f" (AI血量: {level['ai_health']})"
                lock_text = font_medium.render(level_text, True, WHITE)
                
                # 已通关标记
                if i < self.state.unlocked_levels - 1 or (i == self.state.unlocked_levels - 1 and self.state.unlocked_levels > 1):
                    check_text = font_small.render("完成", True, WHITE)
                    screen.blit(check_text, (btn_rect.right - 50, btn_rect.centery - 12))
            
            lock_rect = lock_text.get_rect(center=(btn_rect.centerx, btn_rect.centery))
            screen.blit(lock_text, lock_rect)
        
        # 统计信息
        stats_text = font_small.render(f"胜 胜利:{self.state.wins}  负 失败:{self.state.losses}  平 平局:{self.state.draws}", 
                                       True, LIGHT_GRAY)
        stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(stats_text, stats_rect)
    
    def draw_settings(self):
        """绘制设置界面"""
        # 半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # 设置面板
        panel_width, panel_height = 500, 400
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 40, 60), panel_rect, border_radius=20)
        pygame.draw.rect(screen, (255, 215, 0), panel_rect, 3, border_radius=20)
        
        # 标题
        title = font_large.render("设置 设置", True, (255, 215, 0))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 50))
        screen.blit(title, title_rect)
        
        # 音乐开关
        music_y = panel_y + 120
        music_label = font_medium.render("音乐 音乐", True, WHITE)
        screen.blit(music_label, (panel_x + 60, music_y))
        
        # 音乐开关按钮
        self.music_toggle_rect = pygame.Rect(panel_x + 350, music_y, 80, 40)
        music_state = "开启" if self.sound.music_enabled else "关闭"
        music_color = (100, 200, 100) if self.sound.music_enabled else (200, 100, 100)
        pygame.draw.rect(screen, music_color, self.music_toggle_rect, border_radius=10)
        music_text = font_small.render(music_state, True, WHITE)
        music_text_rect = music_text.get_rect(center=self.music_toggle_rect.center)
        screen.blit(music_text, music_text_rect)
        
        # 音乐音量滑块
        volume_y = music_y + 60
        volume_label = font_small.render(f"音量: {int(self.sound.music_volume * 100)}%", True, LIGHT_GRAY)
        screen.blit(volume_label, (panel_x + 60, volume_y))
        
        # 音量滑块
        self.volume_slider_rect = pygame.Rect(panel_x + 150, volume_y + 5, 250, 20)
        pygame.draw.rect(screen, DARK_GRAY, self.volume_slider_rect, border_radius=10)
        
        # 滑块填充
        fill_width = int(self.sound.music_volume * 250)
        fill_rect = pygame.Rect(panel_x + 150, volume_y + 5, fill_width, 20)
        pygame.draw.rect(screen, (100, 200, 100), fill_rect, border_radius=10)
        
        # 滑块把手
        handle_x = panel_x + 150 + fill_width
        pygame.draw.circle(screen, WHITE, (handle_x, volume_y + 15), 12)
        
        # 音效开关
        sfx_y = volume_y + 60
        sfx_label = font_medium.render("音效 音效", True, WHITE)
        screen.blit(sfx_label, (panel_x + 60, sfx_y))
        
        # 音效开关按钮
        self.sfx_toggle_rect = pygame.Rect(panel_x + 350, sfx_y, 80, 40)
        sfx_state = "开启" if self.sound.sfx_enabled else "关闭"
        sfx_color = (100, 200, 100) if self.sound.sfx_enabled else (200, 100, 100)
        pygame.draw.rect(screen, sfx_color, self.sfx_toggle_rect, border_radius=10)
        sfx_text = font_small.render(sfx_state, True, WHITE)
        sfx_text_rect = sfx_text.get_rect(center=self.sfx_toggle_rect.center)
        screen.blit(sfx_text, sfx_text_rect)
        
        # 音效音量滑块
        sfx_volume_y = sfx_y + 60
        sfx_volume_label = font_small.render(f"音量: {int(self.sound.sfx_volume * 100)}%", True, LIGHT_GRAY)
        screen.blit(sfx_volume_label, (panel_x + 60, sfx_volume_y))
        
        # 音效音量滑块
        self.sfx_volume_slider_rect = pygame.Rect(panel_x + 150, sfx_volume_y + 5, 250, 20)
        pygame.draw.rect(screen, DARK_GRAY, self.sfx_volume_slider_rect, border_radius=10)
        
        # 滑块填充
        sfx_fill_width = int(self.sound.sfx_volume * 250)
        sfx_fill_rect = pygame.Rect(panel_x + 150, sfx_volume_y + 5, sfx_fill_width, 20)
        pygame.draw.rect(screen, (100, 200, 100), sfx_fill_rect, border_radius=10)
        
        # 滑块把手
        sfx_handle_x = panel_x + 150 + sfx_fill_width
        pygame.draw.circle(screen, WHITE, (sfx_handle_x, sfx_volume_y + 15), 12)
        
        # 返回按钮
        self.settings_back_rect = pygame.Rect(panel_x + 30, panel_y + panel_height - 70, 130, 50)
        pygame.draw.rect(screen, (100, 150, 255), self.settings_back_rect, border_radius=12)
        back_text = font_medium.render("返回", True, WHITE)
        back_rect = back_text.get_rect(center=self.settings_back_rect.center)
        screen.blit(back_text, back_rect)
        
        # 返回主页按钮
        self.settings_home_rect = pygame.Rect(panel_x + 340, panel_y + panel_height - 70, 130, 50)
        pygame.draw.rect(screen, (150, 100, 100), self.settings_home_rect, border_radius=12)
        home_text = font_medium.render("返回主页", True, WHITE)
        home_rect = home_text.get_rect(center=self.settings_home_rect.center)
        screen.blit(home_text, home_rect)
    
    def draw_battle(self):
        """绘制战斗界面"""
        # 显示当前关卡
        level_info = LEVELS[self.state.current_level]
        level_text = font_small.render(f"{level_info['name']} - {level_info['desc']}", True, level_info['color'])
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 90))
        screen.blit(level_text, level_rect)
        
        # 玩家血条
        draw_health_bar(screen, 50, 30, 250, 30, 
                       self.state.player_health, self.state.max_health, "玩家", True)
        
        # 玩家能量显示
        energy_text = font_small.render(f"能量:  {self.state.player_energy}/{self.state.max_energy}", True, (255, 215, 0))
        screen.blit(energy_text, (50, 65))
        
        # AI血条
        draw_health_bar(screen, SCREEN_WIDTH - 300, 30, 250, 30,
                       self.state.ai_health, self.state.ai_health if self.state.ai_health > 100 else 100, "AI", False)
        
        # AI能量显示
        ai_energy_text = font_small.render(f"能量:  {self.state.ai_energy}/{self.state.max_energy}", True, (255, 215, 0))
        screen.blit(ai_energy_text, (SCREEN_WIDTH - 150, 65))
        
        # 回合指示器
        turn_text = " 你的回合" if self.state.is_player_turn else "AI AI回合"
        turn_color = (100, 150, 255) if self.state.is_player_turn else (255, 100, 100)
        turn_surf = font_medium.render(turn_text, True, turn_color)
        turn_rect = turn_surf.get_rect(center=(SCREEN_WIDTH // 2, 130))
        pygame.draw.rect(screen, DARK_GRAY, turn_rect.inflate(40, 20), border_radius=15)
        screen.blit(turn_surf, turn_rect)
        
        # 战场区域
        pygame.draw.rect(screen, (30, 30, 60), (100, 170, SCREEN_WIDTH - 200, 200), border_radius=20)
        
        # 玩家准备出牌区（显示已选的牌）
        player_label = font_small.render("你的出牌", True, LIGHT_GRAY)
        screen.blit(player_label, (150, 180))
        
        # 玩家剩余手牌数量
        player_hand_count = font_small.render(f"剩余: {len(self.state.player_hand)}", True, (100, 200, 255))
        screen.blit(player_hand_count, (150, 380))
        
        # 显示玩家已选准备打出的牌
        if self.state.player_played_cards:
            card_spacing = 130
            total_width = len(self.state.player_played_cards) * card_spacing
            start_x = (SCREEN_WIDTH // 2 - 200 - total_width) // 2
            for i, card in enumerate(self.state.player_played_cards):
                x = start_x + i * card_spacing
                # 显示可撤回效果
                draw_card(screen, card, x, 200)
                # 添加撤回标记
                pygame.draw.circle(screen, (255, 100, 100), (x + 12, 187), 12)
                撤回_text = font_tiny.render("×", True, WHITE)
                撤回_text_rect = 撤回_text.get_rect(center=(x + 12, 187))
                screen.blit(撤回_text, 撤回_text_rect)
        
        # VS
        vs_text = font_large.render("VS", True, (255, 215, 0))
        vs_rect = vs_text.get_rect(center=(SCREEN_WIDTH // 2, 270))
        pygame.draw.circle(screen, (255, 100, 50), vs_rect.center, 40)
        screen.blit(vs_text, vs_rect)
        
        # AI出牌区
        ai_label = font_small.render("AI出牌", True, LIGHT_GRAY)
        screen.blit(ai_label, (SCREEN_WIDTH - 250, 180))
        
        # 显示AI已出的牌
        if self.state.ai_played_cards:
            card_spacing = 130
            total_width = len(self.state.ai_played_cards) * card_spacing
            start_x = SCREEN_WIDTH // 2 + 80
            for i, card in enumerate(self.state.ai_played_cards):
                x = start_x + i * card_spacing
                draw_card(screen, card, x, 200)
        
        # AI剩余手牌数量
        ai_hand_count = font_small.render(f"剩余: {len(self.state.ai_hand)}", True, (255, 200, 100))
        screen.blit(ai_hand_count, (SCREEN_WIDTH - 150, 380))
        
        # 伤害数字动画
        if self.state.show_damage:
            if self.state.player_damage > 0:
                dmg_text = font_large.render(f"-{self.state.player_damage}", True, CARD_COLORS[0])
                screen.blit(dmg_text, (SCREEN_WIDTH // 2 - 100, 400))
            if self.state.ai_damage > 0:
                dmg_text = font_large.render(f"-{self.state.ai_damage}", True, CARD_COLORS[0])
                screen.blit(dmg_text, (SCREEN_WIDTH // 2 + 100, 400))
        
        # 本轮结果
        if self.state.battle_result:
            result_texts = {
                'win': ('胜 本轮胜利！', (100, 255, 150)),
                'lose': ('负 本轮失败！', (255, 100, 100)),
                'draw': ('平 本轮平局！', (255, 215, 0))
            }
            text, color = result_texts[self.state.battle_result]
            result_surf = font_medium.render(text, True, color)
            result_rect = result_surf.get_rect(center=(SCREEN_WIDTH // 2, 500))
            screen.blit(result_surf, result_rect)
        
        # 先绘制日志（在手牌后面）
        self.draw_log()
        
        # 玩家手牌
        hand_label = font_small.render("手牌 你的手牌（点击出牌）", True, LIGHT_GRAY)
        hand_label_rect = hand_label.get_rect(center=(SCREEN_WIDTH // 2, 540))
        screen.blit(hand_label, hand_label_rect)
        
        # 绘制手牌
        hand_y = 570
        card_spacing = 130
        total_width = len(self.state.player_hand) * card_spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        self.hovered_card = None
        
        for i, card in enumerate(self.state.player_hand):
            x = start_x + i * card_spacing
            can_play = (self.state.is_player_turn and self.state.game_started 
                       and self.state.player_energy >= card.energy)
            
            if can_play:
                mouse_pos = pygame.mouse.get_pos()
                card_rect = pygame.Rect(x, hand_y, CARD_WIDTH, CARD_HEIGHT)
                if card_rect.collidepoint(mouse_pos):
                    draw_card(screen, card, x, hand_y - 20, hover=True)
                    self.hovered_card = i
                else:
                    draw_card(screen, card, x, hand_y)
            else:
                # 能量不足时显示灰色
                draw_card(screen, card, x, hand_y, disabled=not can_play)
        
        # 结束回合按钮（圆形，在右下角）
        if self.state.is_player_turn and self.state.game_started and not self.state.turn_action_done:
            self.end_turn_btn_rect = pygame.Rect(SCREEN_WIDTH - 90, SCREEN_HEIGHT - 90, 70, 70)
            mouse_pos = pygame.mouse.get_pos()
            btn_hovered = self.end_turn_btn_rect.collidepoint(mouse_pos)
            btn_color = (100, 200, 100) if btn_hovered else (60, 140, 60)
            # 绘制圆形按钮
            pygame.draw.circle(screen, btn_color, (SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55), 35)
            pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH - 55, SCREEN_HEIGHT - 55), 35, 3)
            end_text = font_small.render("结束", True, WHITE)
            end_rect = end_text.get_rect(center=(SCREEN_WIDTH - 55, SCREEN_HEIGHT - 60))
            screen.blit(end_text, end_rect)
            end_text2 = font_small.render("回合", True, WHITE)
            end_rect2 = end_text2.get_rect(center=(SCREEN_WIDTH - 55, SCREEN_HEIGHT - 40))
            screen.blit(end_text2, end_rect2)
    
    def draw_log(self):
        """绘制日志区域 - 左下角，在手牌后面"""
        log_rect = pygame.Rect(50, SCREEN_HEIGHT - 180, 350, 160)
        pygame.draw.rect(screen, (20, 20, 30), log_rect, border_radius=10)
        
        log_title = font_tiny.render("日志 战斗日志", True, (255, 215, 0))
        screen.blit(log_title, (60, SCREEN_HEIGHT - 170))
        
        for i, log in enumerate(self.state.logs[:8]):
            log_text = font_tiny.render(log[:40], True, LIGHT_GRAY)
            screen.blit(log_text, (60, SCREEN_HEIGHT - 145 + i * 18))
        
        # 游戏结束遮罩
        if self.state.game_over:
            # 半透明遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            if self.state.winner == 'player':
                game_over_text = font_large.render("胜 胜利！", True, (255, 215, 0))
            else:
                game_over_text = font_large.render("负 失败", True, (255, 100, 100))
            
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
            screen.blit(game_over_text, text_rect)
            
            stats = font_small.render(
                f"胜利:{self.state.wins}  失败:{self.state.losses}  平局:{self.state.draws}  回合:{self.state.round}",
                True, WHITE)
            stats_rect = stats.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70))
            screen.blit(stats, stats_rect)
            
            center_x = SCREEN_WIDTH // 2
            center_y = SCREEN_HEIGHT // 2
            
            # 按钮高度位置
            btn_y1 = center_y - 20   # 下一关
            btn_y2 = center_y + 40  # 再来一次
            btn_y3 = center_y + 100 # 返回首页
            
            # 下一关按钮（只有胜利时才显示）
            if self.state.winner == 'player' and self.state.current_level < len(LEVELS) - 1:
                self.next_level_btn_rect = pygame.Rect(center_x - 80, btn_y1, 160, 45)
                mouse_pos = pygame.mouse.get_pos()
                hover = self.next_level_btn_rect.collidepoint(mouse_pos)
                btn_color = (100, 200, 100) if hover else (60, 150, 60)
                pygame.draw.rect(screen, btn_color, self.next_level_btn_rect, border_radius=10)
                next_text = font_medium.render("下一关", True, WHITE)
                next_rect = next_text.get_rect(center=self.next_level_btn_rect.center)
                screen.blit(next_text, next_rect)
            
            # 再来一次按钮
            self.restart_btn_rect = pygame.Rect(center_x - 80, btn_y2, 160, 45)
            mouse_pos = pygame.mouse.get_pos()
            hover = self.restart_btn_rect.collidepoint(mouse_pos)
            btn_color = (100, 150, 255) if hover else (60, 100, 200)
            pygame.draw.rect(screen, btn_color, self.restart_btn_rect, border_radius=10)
            restart_text = font_medium.render("再来一次", True, WHITE)
            restart_rect = restart_text.get_rect(center=self.restart_btn_rect.center)
            screen.blit(restart_text, restart_rect)
            
            # 返回首页按钮
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
        
        # 能量系统（初始3点，上限5点，每回合回复3点）
        self.state.player_energy = 3
        self.state.ai_energy = 3
        
        # 根据关卡设置AI血量
        level_info = LEVELS[self.state.current_level]
        self.state.ai_health = level_info['ai_health']
        
        self.state.player_hand = self.draw_cards(6)
        self.state.ai_hand = self.draw_cards(6)
        
        # 重置多牌系统
        self.state.player_played_cards = []
        self.state.ai_played_cards = []
        self.state.turn_action_done = False
        
        self.state.add_log(f" {level_info['name']} 开始！")
        self.state.add_log(f"每回合 {self.state.max_energy} 点能量")
        self.state.add_log("能量:  点击卡牌出牌，点击结束回合")
    
    def draw_cards(self, count: int) -> List[Card]:
        """抽牌"""
        return [copy.copy(random.choice(CARD_LIBRARY)) for _ in range(count)]
    

    
    def player_play_card(self, index: int):
        """玩家出牌"""
        if not self.state.is_player_turn or not self.state.game_started:
            return
        if self.state.turn_action_done:  # 回合行动已完成
            return
        
        card = self.state.player_hand[index]
        
        # 检查能量是否足够
        if self.state.player_energy < card.energy:
            self.state.add_log(f"警告 {card.name} 需要{card.energy}能量")
            self.state.add_log(f"你只有{self.state.player_energy}点能量！")
            self.sound.play('error')
            return
        
        # 消耗能量
        self.state.player_energy -= card.energy
        
        # 从手牌移除卡牌（用完就丢弃），记录到已出牌列表
        card = self.state.player_hand.pop(index)
        self.state.player_played_cards.append(card)
        self.sound.play('play_card')
        
        self.state.add_log(f"你出牌：{card.name} 能量: {card.energy}")
        self.state.add_log(f"剩余能量：{self.state.player_energy}点")
    
    def ai_play_card(self):
        """AI出牌 - 可以出多张牌"""
        if not self.state.ai_hand:
            self.state.turn_action_done = True
            pygame.time.set_timer(pygame.USEREVENT + 2, 500)
            return
        
        # AI 可以出多张牌，循环选择能量足够的牌
        while self.state.ai_energy > 0 and self.state.ai_hand:
            # 找出能量足够的牌
            affordable_cards = [i for i, card in enumerate(self.state.ai_hand) 
                              if card.energy <= self.state.ai_energy]
            
            if not affordable_cards:
                break  # 没有足够能量的牌了
            
            # AI策略：优先选择高攻击/防御的牌
            best_index = affordable_cards[0]
            best_score = -float('inf')
            
            for i in affordable_cards:
                card = self.state.ai_hand[i]
                score = card.attack + card.defense
                
                if score > best_score:
                    best_score = score
                    best_index = i
            
            # 消耗能量并出牌
            card = self.state.ai_hand[best_index]
            self.state.ai_energy -= card.energy
            
            # 从手牌移除（用完就丢弃），记录到已出牌列表
            card = self.state.ai_hand.pop(best_index)
            self.state.ai_played_cards.append(card)
            self.sound.play('play_card')
            
            self.state.add_log(f"AI出牌：{card.name} 能量: {card.energy}")
        
        # 标记回合行动完成
        self.state.turn_action_done = True
        
        # 延迟计算战斗
        pygame.time.set_timer(pygame.USEREVENT + 2, 500)
    
    def end_turn(self):
        """玩家主动结束回合"""
        if not self.state.is_player_turn or not self.state.game_started:
            return
        if self.state.turn_action_done:
            return
        
        self.state.turn_action_done = True
        self.sound.play('click')
        
        # 如果玩家还没出牌，清空已出牌列表
        if not self.state.player_played_cards:
            self.state.player_played_cards = []
        
        # 玩家结束回合后，AI出牌
        pygame.time.set_timer(pygame.USEREVENT + 1, 800)
    
    def calculate_battle(self):
        """计算战斗结果"""
        player_cards = self.state.player_played_cards
        ai_cards = self.state.ai_played_cards
        
        # 即使没有出牌也要结算（视为0攻击0防御）
        self.state.round += 1
        
        # 计算伤害 - 取最高值（不出牌时为0）
        player_attack = max((card.attack for card in player_cards), default=0)
        player_defense = max((card.defense for card in player_cards), default=0)
        ai_attack = max((card.attack for card in ai_cards), default=0)
        ai_defense = max((card.defense for card in ai_cards), default=0)
        
        # 计算伤害（玩家攻击 - AI防御，AI攻击 - 玩家防御）
        player_damage = max(0, player_attack - ai_defense)
        ai_damage = max(0, ai_attack - player_defense)
        
        # 记录伤害用于动画
        self.state.player_damage = player_damage
        self.state.ai_damage = ai_damage
        self.state.show_damage = True
        
        # 应用伤害
        self.state.ai_health = max(0, self.state.ai_health - player_damage)
        self.state.player_health = max(0, self.state.player_health - ai_damage)
        
        # 日志 - 显示本回合出牌
        self.state.add_log(f"--- 第 {self.state.round} 回合 ---")
        
        if player_cards:
            card_names = "、".join([c.name for c in player_cards])
            self.state.add_log(f"你出牌：{card_names}")
            self.state.add_log(f"你的攻击:{player_attack} 防御:{player_defense}")
        else:
            self.state.add_log("你选择不出牌（0攻击0防御）")
        
        if ai_cards:
            ai_card_names = "、".join([c.name for c in ai_cards])
            self.state.add_log(f"AI出牌：{ai_card_names}")
            self.state.add_log(f"AI攻击:{ai_attack} 防御:{ai_defense}")
        else:
            self.state.add_log("AI选择不出牌（0攻击0防御）")
        
        if player_damage > 0:
            self.state.add_log(f"你对AI造成 {player_damage} 点伤害！")
        else:
            self.state.add_log("你的攻击被AI完全抵挡！")
        
        if ai_damage > 0:
            self.state.add_log(f"AI对你造成 {ai_damage} 点伤害！")
        else:
            self.state.add_log("AI的攻击被你完全抵挡！")
        
        # 判断本轮结果
        if player_damage > ai_damage:
            self.state.battle_result = 'win'
        elif player_damage < ai_damage:
            self.state.battle_result = 'lose'
        else:
            self.state.battle_result = 'draw'
        
        self.sound.play('attack')
        
        # 延迟结束回合
        pygame.time.set_timer(pygame.USEREVENT + 3, 1500)
    
    def end_round(self):
        """结束回合"""
        # 补充手牌（每回合抽2张，上限6张）
        if len(self.state.player_hand) < 6:
            draw_count = min(2, 6 - len(self.state.player_hand))
            for _ in range(draw_count):
                self.state.player_hand.append(self.draw_cards(1)[0])
                self.sound.play('draw')
        if len(self.state.ai_hand) < 6:
            draw_count = min(2, 6 - len(self.state.ai_hand))
            for _ in range(draw_count):
                self.state.ai_hand.append(self.draw_cards(1)[0])
        
        # 重置能量（每回合回复3点，上限5点）
        self.state.player_energy = min(self.state.max_energy, self.state.player_energy + 3)
        self.state.ai_energy = min(self.state.max_energy, self.state.ai_energy + 3)
        
        # 清空本回合已出牌
        self.state.player_played_cards = []
        self.state.ai_played_cards = []
        self.state.battle_result = ''
        self.state.show_damage = False
        self.state.turn_action_done = False
        
        # 检查游戏结束
        if self.state.player_health <= 0:
            self.state.game_over = True
            self.state.winner = 'ai'
            self.state.losses += 1
            self.state.add_log("😢 很遗憾，你输了...")
            self.sound.play('defeat')
            return
        
        if self.state.ai_health <= 0:
            self.state.game_over = True
            self.state.winner = 'player'
            self.state.wins += 1
            self.state.level_cleared = True
            
            # 解锁下一关
            self.state.unlock_next_level()
            
            level_name = LEVELS[self.state.current_level]['name']
            self.state.add_log(f" {level_name} 通关！")
            if self.state.current_level + 1 < len(LEVELS):
                self.state.add_log(f"解锁 解锁了 {LEVELS[self.state.current_level + 1]['name']}！")
            else:
                self.state.add_log("胜 你已通关所有关卡！")
            self.sound.play('victory')
            return
        
        # 下一回合
        self.state.is_player_turn = True
        self.state.add_log(f"能量:  第 {self.state.round + 1} 回合开始")
        self.state.add_log(f"能量:  能量重置为 {self.state.max_energy} 点")
    
    def get_card_at_mouse(self) -> Optional[int]:
        """获取鼠标位置下的手牌索引"""
        if not self.state.is_player_turn or not self.state.game_started or self.state.turn_action_done:
            return None
        
        mouse_pos = pygame.mouse.get_pos()
        hand_y = 570  # 与 draw_battle 中的 hand_y 保持一致
        card_spacing = 130
        total_width = len(self.state.player_hand) * card_spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        for i, card in enumerate(self.state.player_hand):
            x = start_x + i * card_spacing
            card_rect = pygame.Rect(x, hand_y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(mouse_pos):
                return i
        return None
    
    def get_recallable_card_at_mouse(self) -> Optional[int]:
        """获取鼠标位置下的可撤回卡牌索引"""
        if not self.state.is_player_turn or not self.state.game_started or self.state.turn_action_done:
            return None
        if not self.state.player_played_cards:
            return None
        
        mouse_pos = pygame.mouse.get_pos()
        card_spacing = 130
        total_width = len(self.state.player_played_cards) * card_spacing
        start_x = (SCREEN_WIDTH // 2 - 200 - total_width) // 2
        
        for i, card in enumerate(self.state.player_played_cards):
            x = start_x + i * card_spacing
            card_rect = pygame.Rect(x, 200, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(mouse_pos):
                return i
        return None
    
    def recall_card(self, index: int):
        """撤回已出牌"""
        if index is None or index >= len(self.state.player_played_cards):
            return
        
        card = self.state.player_played_cards.pop(index)
        # 返还能量
        self.state.player_energy += card.energy
        # 放回手牌
        self.state.player_hand.append(card)
        self.sound.play('click')
        self.state.add_log(f"撤回：{card.name}（返还{card.energy}能量）")
    
    def get_button_at_mouse(self) -> Optional[str]:
        """检测鼠标下的按钮"""
        mouse_pos = pygame.mouse.get_pos()
        
        # 主菜单按钮
        if self.state.in_main_menu:
            if hasattr(self, 'new_game_btn_rect') and self.new_game_btn_rect.collidepoint(mouse_pos):
                return 'new_game'
            if hasattr(self, 'continue_btn_rect') and self.continue_btn_rect.collidepoint(mouse_pos):
                return 'continue_game'
            if hasattr(self, 'menu_settings_btn_rect') and self.menu_settings_btn_rect.collidepoint(mouse_pos):
                return 'menu_settings'
            if hasattr(self, 'exit_btn_rect') and self.exit_btn_rect.collidepoint(mouse_pos):
                return 'exit'
            return None
        
        # 设置按钮 - 所有界面都可以点击
        if not self.state.in_settings and hasattr(self, 'settings_btn_rect'):
            if self.settings_btn_rect.collidepoint(mouse_pos):
                return 'settings'
        
        # 选关界面 - 点击关卡
        if self.state.selecting_level and hasattr(self, 'level_buttons'):
            for i, btn_rect in enumerate(self.level_buttons):
                if i < self.state.unlocked_levels and btn_rect.collidepoint(mouse_pos):
                    return f'level_{i}'
        
        # 游戏结束按钮
        if self.state.game_over:
            # 下一关按钮
            if hasattr(self, 'next_level_btn_rect') and self.next_level_btn_rect.collidepoint(mouse_pos):
                return 'next_level'
            # 再来一次按钮
            if hasattr(self, 'restart_btn_rect') and self.restart_btn_rect.collidepoint(mouse_pos):
                return 'restart'
            # 返回首页按钮
            if hasattr(self, 'home_btn_rect') and self.home_btn_rect.collidepoint(mouse_pos):
                return 'home'
        
        return None
    
    def handle_settings_event(self, event):
        """处理设置界面的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                mouse_pos = pygame.mouse.get_pos()
                
                # 音乐开关
                if hasattr(self, 'music_toggle_rect') and self.music_toggle_rect.collidepoint(mouse_pos):
                    self.sound.music_enabled = not self.sound.music_enabled
                    if self.sound.music_enabled:
                        self.sound.play_bgm()
                    else:
                        self.sound.stop_bgm()
                    self.sound.play('click')
                    self.sound.save_settings()  # 保存设置
                    return
                
                # 音效开关
                if hasattr(self, 'sfx_toggle_rect') and self.sfx_toggle_rect.collidepoint(mouse_pos):
                    self.sound.sfx_enabled = not self.sound.sfx_enabled
                    if self.sound.sfx_enabled:
                        self.sound.play('click')
                    self.sound.save_settings()  # 保存设置
                    return
                
                # 返回按钮
                if hasattr(self, 'settings_back_rect') and self.settings_back_rect.collidepoint(mouse_pos):
                    self.state.in_settings = False
                    self.sound.play('click')
                    self.sound.save_settings()  # 保存设置
                    return
                
                # 返回主页按钮
                if hasattr(self, 'settings_home_rect') and self.settings_home_rect.collidepoint(mouse_pos):
                    self.state.in_settings = False
                    self.state.reset(keep_stats=True)
                    self.state.in_main_menu = True  # 返回主菜单
                    self.sound.play('click')
                    self.sound.save_settings()
                    return
        
        elif event.type == pygame.MOUSEMOTION:
            # 拖动滑块
            mouse_pos = pygame.mouse.get_pos()
            buttons = pygame.mouse.get_pressed()
            
            if buttons[0]:  # 左键按住
                panel_width, panel_height = 500, 400
                panel_x = (SCREEN_WIDTH - panel_width) // 2
                panel_y = (SCREEN_HEIGHT - panel_height) // 2
                
                # 音乐音量滑块
                if hasattr(self, 'volume_slider_rect'):
                    slider = self.volume_slider_rect
                    if slider.collidepoint(mouse_pos):
                        # 计算新的音量值
                        rel_x = mouse_pos[0] - slider.x
                        new_volume = max(0, min(1, rel_x / slider.width))
                        self.sound.music_volume = new_volume
                        if hasattr(self.sound, 'bgm'):
                            self.sound.bgm.set_volume(new_volume)
                        self.sound.save_settings()  # 保存设置
                
                # 音效音量滑块
                if hasattr(self, 'sfx_volume_slider_rect'):
                    slider = self.sfx_volume_slider_rect
                    if slider.collidepoint(mouse_pos):
                        # 计算新的音量值
                        rel_x = mouse_pos[0] - slider.x
                        new_volume = max(0, min(1, rel_x / slider.width))
                        self.sound.sfx_volume = new_volume
                        self.sound.save_settings()  # 保存设置
    
    def handle_event(self, event: pygame.event):
        """处理事件"""
        # 设置界面事件优先处理
        if self.state.in_settings:
            self.handle_settings_event(event)
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                mouse_pos = event.pos
                
                # 点击设置按钮
                btn = self.get_button_at_mouse()
                
                # 主菜单按钮处理
                if self.state.in_main_menu:
                    if btn == 'new_game':
                        self.state.selecting_level = True
                        self.state.in_main_menu = False
                        self.sound.play('click')
                        return
                    elif btn == 'continue_game':
                        self.state.in_main_menu = False
                        self.sound.play('click')
                        return
                    elif btn == 'menu_settings':
                        self.state.in_settings = True
                        self.sound.play('click')
                        return
                    elif btn == 'exit':
                        self.sound.play('click')
                        pygame.quit()
                        import sys
                        sys.exit()
                    return
                
                if btn == 'settings':
                    self.state.in_settings = True
                    self.sound.play('click')
                    return
                elif btn == 'restart':
                    self.state.reset(keep_stats=True)
                    self.state.selecting_level = False
                    return
                elif btn == 'next_level':
                    # 进入下一关
                    if self.state.current_level < len(LEVELS) - 1:
                        self.state.current_level += 1
                    self.state.reset(keep_stats=True)
                    self.state.selecting_level = False
                    return
                elif btn == 'home':
                    # 返回首页
                    self.state.reset(keep_stats=True)
                    self.state.in_main_menu = True  # 返回主菜单
                    return
                elif btn and btn.startswith('level_'):
                    # 选择关卡并直接开始游戏
                    level_index = int(btn.split('_')[1])
                    if level_index < self.state.unlocked_levels:
                        self.state.current_level = level_index
                        self.start_game()  # 直接开始游戏
                    return
                
                # 点击手牌
                card_index = self.get_card_at_mouse()
                if card_index is not None:
                    self.player_play_card(card_index)
                    return
                
                # 点击已出牌（撤回）
                recall_index = self.get_recallable_card_at_mouse()
                if recall_index is not None:
                    self.recall_card(recall_index)
                    return
                
                # 点击结束回合按钮
                if self.state.is_player_turn and self.state.game_started and not self.state.turn_action_done:
                    if hasattr(self, 'end_turn_btn_rect') and self.end_turn_btn_rect.collidepoint(mouse_pos):
                        self.end_turn()
                        return
        
        elif event.type == pygame.USEREVENT + 1:
            # AI出牌
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)
            self.ai_play_card()
        
        elif event.type == pygame.USEREVENT + 2:
            # 计算战斗
            pygame.time.set_timer(pygame.USEREVENT + 2, 0)
            self.calculate_battle()
        
        elif event.type == pygame.USEREVENT + 3:
            # 结束回合
            pygame.time.set_timer(pygame.USEREVENT + 3, 0)
            self.end_round()
    
    def run(self):
        """游戏主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)
        
        pygame.quit()


# 运行游戏
if __name__ == "__main__":
    game = CardBattleGame()
    game.run()
