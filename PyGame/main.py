import re
import pygame
import json
import time
import sys
import os
import math
from datetime import datetime

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("GameName")
clock = pygame.time.Clock()

SCREEN_START = 0
SCREEN_LOADING = 1
SCREEN_GAME = 2
SCREEN_SETTINGS = 3
SCREEN_SAVE = 4
SCREEN_LOAD = 5
SCREEN_CONFIRM_EXIT = 6
SCREEN_CONFIRM_OVERWRITE = 7
SCREEN_HISTORY = 8
SCREEN_ENDING = 9

DISPLAY_DIALOG = 0
DISPLAY_FULLSCREEN = 1

COLORS = {
    "background": (5, 10, 15), 
    "dialog_bg": (15, 20, 30, 220), 
    "name_text": (180, 200, 220), 
    "dialog_text": (200, 210, 220), 
    "option_bg": (25, 35, 45), 
    "option_hover": (40, 60, 80), 
    "option_border": (70, 90, 110), 
    "title": (230, 230, 230), 
    "button": (30, 50, 70), 
    "button_hover": (50, 80, 100),  
    "button_disabled": (15, 25, 35),
    "slider": (80, 110, 130), 
    "confirm_bg": (10, 20, 30, 240), 
    "empty_slot": (20, 30, 40), 
    "save_slot": (35, 55, 75), 
    "save_hover": (55, 85, 105), 
    "save_text": (180, 195, 210), 
    "fullscreen_bg": (0, 5, 10), 
    "fullscreen_text": (200, 220, 230), 
    "history_bg": (12, 22, 32, 240), 
    "history_text": (190, 205, 215), 
    "history_option": (120, 160, 190), 
    "ending_title": (140, 180, 210)   
}

df = "fonts/SourceHanSerifCN-Bold.otf"

try:
    title_font = pygame.font.Font(df, 48)
    button_font = pygame.font.Font(df, 32)
    dialog_font = pygame.font.Font(df, 24)
    name_font = pygame.font.Font(df, 26)
    option_font = pygame.font.Font(df, 22)
    small_font = pygame.font.Font(df, 18)
    fullscreen_font = pygame.font.Font(df, 28)
    history_font = pygame.font.Font(df, 20)
    ending_font = pygame.font.Font(df, 36)
except Exception as e:
    title_font = pygame.font.SysFont(None, 48)
    button_font = pygame.font.SysFont(None, 32)
    dialog_font = pygame.font.SysFont(None, 24)
    name_font = pygame.font.SysFont(None, 26)
    option_font = pygame.font.SysFont(None, 22)
    small_font = pygame.font.SysFont(None, 18)
    fullscreen_font = pygame.font.SysFont(None, 32)
    history_font = pygame.font.SysFont(None, 20)
    ending_font = pygame.font.SysFont(None, 36)

try:
    start_bg = pygame.image.load("images/start_bg.jpg").convert()
    start_bg = pygame.transform.scale(start_bg, (800, 600))
except:
    start_bg = pygame.Surface((800, 600))
    start_bg.fill((0, 12, 19))

current_screen = SCREEN_START
loading_progress = 0
current_node = "start"
display_text = ""
typing = True
last_char_time = time.time()
typing_speed = 0.05
show_options = False
game_data = {}
volume = 0.5
dialog_alpha = 200
sounds = {}
current_sound = None
story = {}
characters = {}
current_character = None
character_sprites = {}
type_sounds = {}
last_type_sound_time = 0
type_sound_delay = 0.1

current_display_mode = DISPLAY_DIALOG
fullscreen_bg_color = COLORS["fullscreen_bg"]
fullscreen_text_color = COLORS["fullscreen_text"]

save_slots = [None] * 10
current_save_slot = 0
slot_to_overwrite = -1

auto_save_enabled = True
auto_save_interval = 5
last_auto_save_time = time.time()

character_position = "left"

STYLE_TAGS = {
    'm': {'italic': True, 'color': (160, 160, 255)},
    'y': {'color': (255, 255, 0)},
    'r': {'color': (255, 100, 100)},
    'g': {'color': (100, 255, 100)},
    'b': {'color': (100, 150, 255)},
    'i': {'italic': True},
    'gy': {'color': (120, 120, 120)}
}

background_images = {}
current_background = None

character_expressions = {}

text_history = []
history_scroll_offset = 0

ending_name = ""
ending_timer = 0
ending_duration = 3

game_values = {}

INFO_PANEL_VISIBLE = False
info_messages = []
max_info_messages = 10
info_panel_height = 200

option_typing = False
option_display_texts = []
option_typing_index = 0
option_last_char_time = time.time()
option_typing_speed = 0.02  # 选项打字速度可以比对话稍快


def add_info_message(message, message_type="info"):
    global info_messages
    
    colors = {
        "info": (200, 200, 200),
        "success": (100, 255, 100),
        "warning": (255, 255, 100),
        "error": (255, 100, 100),
        "save": (100, 200, 255),
        "load": (255, 200, 100)
    }
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    info_messages.append({
        "text": formatted_message,
        "type": message_type,
        "color": colors.get(message_type, (200, 200, 200)),
        "time": time.time()
    })
    
    if len(info_messages) > max_info_messages:
        info_messages.pop(0)


def draw_info_panel():
    if not INFO_PANEL_VISIBLE:
        return
    
    panel_rect = pygame.Rect(50, 50, 700, info_panel_height)
    panel_surface = pygame.Surface((700, info_panel_height), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, 200))
    screen.blit(panel_surface, (50, 50))
    
    pygame.draw.rect(screen, (100, 100, 150), panel_rect, 2, border_radius=5)
    
    title_surf = small_font.render("游戏信息", True, (255, 255, 255))
    screen.blit(title_surf, (panel_rect.x + 10, panel_rect.y + 10))
    
    close_rect = pygame.Rect(panel_rect.right - 30, panel_rect.y + 5, 25, 25)
    pygame.draw.rect(screen, (200, 100, 100), close_rect, border_radius=3)
    close_surf = small_font.render("X", True, (255, 255, 255))
    screen.blit(close_surf, (close_rect.centerx - close_surf.get_width() // 2,
                             close_rect.centery - close_surf.get_height() // 2))
    
    y_offset = panel_rect.y + 40
    for i, msg in enumerate(info_messages[-8:]):
        msg_surf = small_font.render(msg["text"], True, msg["color"])
        screen.blit(msg_surf, (panel_rect.x + 10, y_offset))
        y_offset += 20


def load_game_data():
    global story, sounds, characters, character_sprites, type_sounds, save_slots, background_images, character_expressions, game_values
    
    try:
        with open('data/story.json', 'r', encoding='utf-8') as f:
            story = json.load(f)
        
        with open('data/characters.json', 'r', encoding='utf-8') as f:
            characters = json.load(f)
        
        sounds.clear()
        for node in story.values():
            if "sound" in node:
                sound_path = f"sounds/{node['sound']}"
                if os.path.exists(sound_path):
                    sounds[node['sound']] = pygame.mixer.Sound(sound_path)
                else:
                    add_info_message(f"音效文件缺失: {sound_path}", "warning")
        
        background_images.clear()
        for node in story.values():
            if "background" in node:
                bg_path = f"backgrounds/{node['background']}"
                if bg_path not in background_images and os.path.exists(bg_path):
                    try:
                        bg_image = pygame.image.load(bg_path).convert()
                        bg_image = pygame.transform.scale(bg_image, (800, 600))
                        background_images[node['background']] = bg_image
                    except Exception as e:
                        add_info_message(f"加载背景图片失败: {bg_path} - {e}", "error")
        
        character_sprites.clear()
        character_expressions.clear()
        for char in characters:
            char_name = char["character"]
            character_expressions[char_name] = {}
            
            if "picture" in char:
                try:
                    sprite_path = f"sprites/{char['picture']}"
                    if os.path.exists(sprite_path):
                        sprite = pygame.image.load(sprite_path).convert_alpha()
                        sprite = pygame.transform.scale(sprite, (300, 400))
                        character_sprites[char_name] = sprite
                        character_expressions[char_name]["default"] = sprite
                    else:
                        add_info_message(f"立绘文件缺失: {sprite_path}", "warning")
                except Exception as e:
                    add_info_message(f"加载立绘失败: {char['picture']} - {e}", "error")
            
            if "expressions" in char:
                for expr_name, expr_file in char["expressions"].items():
                    try:
                        expr_path = f"sprites/{expr_file}"
                        if os.path.exists(expr_path):
                            expr_sprite = pygame.image.load(expr_path).convert_alpha()
                            expr_sprite = pygame.transform.scale(expr_sprite, (300, 400))
                            character_expressions[char_name][expr_name] = expr_sprite
                        else:
                            add_info_message(f"表情立绘文件缺失: {expr_path}", "warning")
                    except Exception as e:
                        add_info_message(f"加载表情立绘失败: {expr_file} - {e}", "error")
        
        type_sounds.clear()
        for char in characters:
            if "sound" in char:
                try:
                    sound_path = f"sounds/{char['sound']}"
                    if os.path.exists(sound_path):
                        type_sounds[char["character"]] = pygame.mixer.Sound(sound_path)
                    else:
                        add_info_message(f"打字音效文件缺失: {sound_path}", "warning")
                except Exception as e:
                    add_info_message(f"加载打字音效失败: {char['sound']} - {e}", "error")
        
        load_save_data()
        
        game_values = story.get("initial_values", {})
        add_info_message("游戏数据加载完成", "success")
    
    except Exception as e:
        add_info_message(f"游戏数据加载失败: {e}", "error")


def load_save_data():
    global save_slots, game_values
    try:
        if os.path.exists("saves/save_data.json"):
            with open("saves/save_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if isinstance(data, list):
                    save_slots = data
                    game_values = {}
                    add_info_message("检测到旧版存档格式，已自动转换", "warning")
                else:
                    save_slots = data.get("save_slots", [None] * 10)
                    game_values = data.get("game_values", {})
                
                while len(save_slots) < 10:
                    save_slots.append(None)
                
                add_info_message("存档数据加载完成", "success")
    except Exception as e:
        add_info_message(f"加载存档数据失败: {e}", "error")
        save_slots = [None] * 10
        game_values = {}


def save_game_data():
    try:
        if not os.path.exists("saves"):
            os.makedirs("saves")
        
        data = {
            "save_slots": save_slots,
            "game_values": game_values,
            "format_version": "2.0"
        }
        
        with open("saves/save_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        add_info_message("存档数据保存完成", "success")
    except Exception as e:
        add_info_message(f"保存存档数据失败: {e}", "error")


def save_game(slot_index):
    global save_slots
    
    save_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_node": current_node,
        "display_text": display_text,
        "typing": typing,
        "current_character": current_character,
        "display_mode": current_display_mode,
        "text_history": text_history,
        "game_values": game_values
    }
    
    save_slots[slot_index] = save_data
    save_game_data()
    
    add_info_message(f"游戏已保存到槽位 {slot_index + 1}", "save")


def load_game(slot_index):
    global current_node, display_text, typing, current_character, current_display_mode, text_history, game_values
    
    if save_slots[slot_index] is not None:
        save_data = save_slots[slot_index]
        current_node = save_data["current_node"]
        display_text = save_data["display_text"]
        typing = save_data["typing"]
        current_character = save_data["current_character"]
        current_display_mode = save_data.get("display_mode", DISPLAY_DIALOG)
        text_history = save_data.get("text_history", [])
        game_values = save_data.get("game_values", {})
        
        add_info_message(f"已从槽位 {slot_index + 1} 加载游戏", "load")
        return True
    else:
        add_info_message(f"槽位 {slot_index + 1} 没有存档", "warning")
        return False


def add_to_history(character, text, is_option=False):
    history_entry = {
        "character": character,
        "text": text,
        "is_option": is_option
    }
    text_history.append(history_entry)
    
    if len(text_history) > 100:
        text_history.pop(0)


def parse_styled_text(text, use_fullscreen=False, use_history=False):
    text = text.replace('\n', '[br]')
    
    segments = []
    pattern = re.compile(r'\[(\w+)\](.*?)\[\/\1\]', re.DOTALL)
    last_pos = 0
    
    if use_history:
        base_font = history_font
    elif use_fullscreen:
        base_font = fullscreen_font
    else:
        base_font = dialog_font
    
    for match in pattern.finditer(text):
        start, end = match.span()
        if last_pos < start:
            pre_text = text[last_pos:start]
            for part in pre_text.split('[br]'):
                if part:
                    segments.append({
                        'text': part,
                        'font': base_font,
                        'color': fullscreen_text_color if use_fullscreen else COLORS["dialog_text"]
                    })
                segments.append({'text': '\n', 'font': None, 'color': None})
            segments.pop()
        
        tag = match.group(1)
        content = match.group(2)
        style = STYLE_TAGS.get(tag, {})
        
        if 'italic' in style:
            try:
                if use_history:
                    font_size = 20
                elif use_fullscreen:
                    font_size = 27
                else:
                    font_size = 24
                font = pygame.font.Font(df, font_size)
                font.italic = True
                style['font'] = font
            except:
                style['font'] = pygame.font.SysFont(None, font_size)
                style['font'].italic = True
        else:
            style['font'] = base_font
        
        if 'color' not in style:
            if use_history:
                style['color'] = COLORS["history_text"]
            elif use_fullscreen:
                style['color'] = fullscreen_text_color
            else:
                style['color'] = COLORS["dialog_text"]
        
        for part in content.split('[br]'):
            if part:
                segments.append({
                    'text': part,
                    'font': style.get('font', base_font),
                    'color': style['color']
                })
            segments.append({'text': '\n', 'font': None, 'color': None})
        segments.pop()
        
        last_pos = end
    
    if last_pos < len(text):
        pre_text = text[last_pos:]
        for part in pre_text.split('[br]'):
            if part:
                segments.append({
                    'text': part,
                    'font': base_font,
                    'color': fullscreen_text_color if use_fullscreen else COLORS["dialog_text"]
                })
            segments.append({'text': '\n', 'font': None, 'color': None})
        segments.pop()
    
    return segments


def set_game_values(values_dict):
    global game_values
    for key, value in values_dict.items():
        game_values[key] = value


def change_game_values(changes_dict):
    global game_values
    for key, change in changes_dict.items():
        if key not in game_values:
            game_values[key] = 0
        
        if isinstance(change, dict):
            if 'add' in change:
                game_values[key] += change['add']
            elif 'sub' in change:
                game_values[key] -= change['sub']
            elif 'mul' in change:
                game_values[key] *= change['mul']
            elif 'div' in change:
                if change['div'] != 0:
                    game_values[key] /= change['div']
            elif 'set' in change:
                game_values[key] = change['set']
        else:
            game_values[key] = change


def check_conditions(conditions):
    if not conditions:
        return True
    
    for key, condition in conditions.items():
        if key not in game_values:
            return False
        
        current_value = game_values[key]
        
        if isinstance(condition, dict):
            if 'gt' in condition and not (current_value > condition['gt']):
                return False
            if 'gte' in condition and not (current_value >= condition['gte']):
                return False
            if 'lt' in condition and not (current_value < condition['lt']):
                return False
            if 'lte' in condition and not (current_value <= condition['lte']):
                return False
            if 'eq' in condition and not (current_value == condition['eq']):
                return False
            if 'ne' in condition and not (current_value != condition['ne']):
                return False
        else:
            if current_value != condition:
                return False
    
    return True


def get_filtered_options(options):
    filtered_options = []
    for option in options:
        conditions = option.get("conditions", {})
        if check_conditions(conditions):
            filtered_options.append(option)
    return filtered_options


def process_node_values(node_data):
    if "set_values" in node_data:
        set_game_values(node_data["set_values"])
    
    if "change_values" in node_data:
        change_game_values(node_data["change_values"])


def draw_start_screen():
    screen.blit(start_bg, (0, 0))
    
    title_surf = title_font.render("G/N", True, COLORS["title"])
    title_rect = title_surf.get_rect(center=(120, 100))
    screen.blit(title_surf, title_rect)
    
    buttons = [
        {"text": "新游戏", "y": 250, "enabled": True},
        {"text": "继续游戏", "y": 320, "enabled": any(save_slots)},
        {"text": "设置", "y": 390, "enabled": True},
        {"text": "退出游戏", "y": 460, "enabled": True}
    ]
    
    mouse_pos = pygame.mouse.get_pos()
    for btn in buttons:
        rect = pygame.Rect(60, btn["y"], 200, 50)
        color = COLORS["button_disabled"] if not btn["enabled"] else COLORS["button_hover"] if rect.collidepoint(
            mouse_pos) else COLORS["button"]
        pygame.draw.rect(screen, color, rect, border_radius=8)
        text_color = COLORS["dialog_text"] if btn["enabled"] else (150, 150, 150)
        text_surf = button_font.render(btn["text"], True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)


def handle_start_events(event):
    global current_screen
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = pygame.mouse.get_pos()
        
        buttons_y = [250, 320, 390, 460]
        for i, y in enumerate(buttons_y):
            rect = pygame.Rect(60, y, 200, 50)
            if rect.collidepoint(mouse_pos):
                if i == 0:
                    reset_game_state()
                    current_screen = SCREEN_LOADING
                elif i == 1:
                    current_screen = SCREEN_LOAD
                elif i == 2:
                    current_screen = SCREEN_SETTINGS
                elif i == 3:
                    pygame.quit()
                    sys.exit()


def reset_game_state():
    global current_node, display_text, typing, show_options, last_auto_save_time, current_display_mode, text_history, current_background, game_values
    current_node = "start"
    display_text = ""
    typing = True
    show_options = False
    last_auto_save_time = time.time()
    current_display_mode = DISPLAY_DIALOG
    text_history = []
    current_background = None
    game_values = story.get("initial_values", {})


def draw_loading_screen():
    screen.fill(COLORS["background"])
    
    text_surf = dialog_font.render("资源加载中...", True, COLORS["dialog_text"])
    screen.blit(text_surf, (350, 300))
    
    pygame.draw.rect(screen, COLORS["option_bg"], (200, 350, 400, 20), border_radius=10)
    
    progress_width = int(396 * loading_progress)
    pygame.draw.rect(screen, COLORS["name_text"], (202, 352, progress_width, 16), border_radius=8)
    
    percent_text = f"{int(loading_progress * 100)}%"
    percent_surf = dialog_font.render(percent_text, True, COLORS["dialog_text"])
    screen.blit(percent_surf, (380, 380))


def update_loading():
    global loading_progress, current_screen
    loading_progress += 0.02
    
    if loading_progress >= 1.0:
        load_game_data()
        current_screen = SCREEN_GAME


def draw_settings_screen():
    screen.fill(COLORS["background"])
    
    back_rect = pygame.Rect(20, 20, 100, 40)
    mouse_pos = pygame.mouse.get_pos()
    color = COLORS["button_hover"] if back_rect.collidepoint(mouse_pos) else COLORS["button"]
    pygame.draw.rect(screen, color, back_rect, border_radius=5)
    text_surf = option_font.render("返回", True, COLORS["dialog_text"])
    screen.blit(text_surf, (back_rect.x + 10, back_rect.y + 8))
    
    text_surf = dialog_font.render(f"音量: {int(volume * 100)}%", True, COLORS["dialog_text"])
    screen.blit(text_surf, (300, 200))
    pygame.draw.rect(screen, COLORS["slider"], (300, 250, 200, 10))
    pygame.draw.circle(screen, COLORS["button_hover"], (300 + int(200 * volume), 255), 8)
    
    text_surf = dialog_font.render(f"打字速度: {typing_speed:.2f}s/字", True, COLORS["dialog_text"])
    screen.blit(text_surf, (300, 300))
    pygame.draw.rect(screen, COLORS["slider"], (300, 350, 200, 10))
    speed_pos = 300 + int(200 * (typing_speed - 0.01) / 0.19)
    pygame.draw.circle(screen, COLORS["button_hover"], (speed_pos, 355), 8)
    
    text_surf = dialog_font.render(f"对话框透明度: {int(dialog_alpha / 255 * 100)}%", True, COLORS["dialog_text"])
    screen.blit(text_surf, (300, 400))
    pygame.draw.rect(screen, COLORS["slider"], (300, 450, 200, 10))
    alpha_pos = 300 + int(200 * dialog_alpha / 255)
    pygame.draw.circle(screen, COLORS["button_hover"], (alpha_pos, 455), 8)
    
    auto_save_text = "自动存档: 开启" if auto_save_enabled else "自动存档: 关闭"
    text_surf = dialog_font.render(auto_save_text, True, COLORS["dialog_text"])
    screen.blit(text_surf, (300, 500))
    auto_save_rect = pygame.Rect(500, 500, 60, 30)
    color = COLORS["button_hover"] if auto_save_rect.collidepoint(mouse_pos) else COLORS["button"]
    pygame.draw.rect(screen, color, auto_save_rect, border_radius=5)
    status_text = "开" if auto_save_enabled else "关"
    status_surf = option_font.render(status_text, True, COLORS["dialog_text"])
    screen.blit(status_surf, (auto_save_rect.centerx - status_surf.get_width() // 2,
                              auto_save_rect.centery - status_surf.get_height() // 2))
    
    pos_text = f"角色位置: {character_position}"
    text_surf = dialog_font.render(pos_text, True, COLORS["dialog_text"])
    screen.blit(text_surf, (300, 550))
    pos_rect = pygame.Rect(500, 550, 100, 30)
    color = COLORS["button_hover"] if pos_rect.collidepoint(mouse_pos) else COLORS["button"]
    pygame.draw.rect(screen, color, pos_rect, border_radius=5)
    pos_surf = option_font.render("切换", True, COLORS["dialog_text"])
    screen.blit(pos_surf, (pos_rect.centerx - pos_surf.get_width() // 2,
                           pos_rect.centery - pos_surf.get_height() // 2))
    
    title_surf = title_font.render("游戏设置", True, COLORS["title"])
    screen.blit(title_surf, (320, 50))


def handle_settings_events(event):
    global current_screen, volume, typing_speed, dialog_alpha, auto_save_enabled, character_position
    
    mouse_pos = pygame.mouse.get_pos()
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        if pygame.Rect(20, 20, 100, 40).collidepoint(mouse_pos):
            current_screen = SCREEN_START
        
        elif 300 <= mouse_pos[0] <= 500:
            if 240 <= mouse_pos[1] <= 260:
                volume = (mouse_pos[0] - 300) / 200
                volume = max(0.0, min(1.0, volume))
            
            elif 340 <= mouse_pos[1] <= 360:
                typing_speed = 0.01 + (mouse_pos[0] - 300) / 200 * 0.19
                typing_speed = max(0.01, min(0.2, typing_speed))
            
            elif 440 <= mouse_pos[1] <= 460:
                dialog_alpha = (mouse_pos[0] - 300) / 200 * 255
                dialog_alpha = max(0, min(255, int(dialog_alpha)))
                COLORS["dialog_bg"] = (40, 45, 60, int(dialog_alpha))
        
        elif pygame.Rect(500, 500, 60, 30).collidepoint(mouse_pos):
            auto_save_enabled = not auto_save_enabled
        
        elif pygame.Rect(500, 550, 100, 30).collidepoint(mouse_pos):
            if character_position == "left":
                character_position = "right"
            elif character_position == "right":
                character_position = "center"
            else:
                character_position = "left"


def draw_save_load_screen(is_save=True):
    screen.fill(COLORS["background"])
    
    title = "保存游戏" if is_save else "加载游戏"
    title_surf = title_font.render(title, True, COLORS["title"])
    screen.blit(title_surf, (320, 50))
    
    back_rect = pygame.Rect(20, 20, 100, 40)
    mouse_pos = pygame.mouse.get_pos()
    color = COLORS["button_hover"] if back_rect.collidepoint(mouse_pos) else COLORS["button"]
    pygame.draw.rect(screen, color, back_rect, border_radius=5)
    text_surf = option_font.render("返回", True, COLORS["dialog_text"])
    screen.blit(text_surf, (back_rect.x + 10, back_rect.y + 8))
    
    for i in range(10):
        row = i // 5
        col = i % 5
        x = 50 + col * 150
        y = 150 + row * 180
        
        slot_rect = pygame.Rect(x, y, 130, 150)
        is_hover = slot_rect.collidepoint(mouse_pos)
        
        if save_slots[i] is not None:
            color = COLORS["save_hover"] if is_hover else COLORS["save_slot"]
        else:
            color = COLORS["empty_slot"]
        
        pygame.draw.rect(screen, color, slot_rect, border_radius=8)
        pygame.draw.rect(screen, COLORS["option_border"], slot_rect, width=2, border_radius=8)
        
        if save_slots[i] is not None:
            save_data = save_slots[i]
            time_text = save_data["timestamp"]
            time_surf = small_font.render(time_text, True, COLORS["save_text"])
            screen.blit(time_surf, (x + 10, y + 15))
            
            node_text = f"节点: {save_data['current_node']}"
            node_surf = small_font.render(node_text, True, COLORS["save_text"])
            screen.blit(node_surf, (x + 10, y + 40))
            
            slot_text = f"存档位 {i + 1}"
            slot_surf = option_font.render(slot_text, True, COLORS["save_text"])
            screen.blit(slot_surf, (x + 10, y + 110))
        else:
            empty_text = "空存档位"
            empty_surf = option_font.render(empty_text, True, COLORS["dialog_text"])
            screen.blit(empty_surf, (x + 30, y + 60))
            
            slot_text = f"存档位 {i + 1}"
            slot_surf = small_font.render(slot_text, True, COLORS["dialog_text"])
            screen.blit(slot_surf, (x + 40, y + 110))


def handle_save_load_events(event, is_save=True):
    global current_screen, current_save_slot, slot_to_overwrite
    
    mouse_pos = pygame.mouse.get_pos()
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        if pygame.Rect(20, 20, 100, 40).collidepoint(mouse_pos):
            current_screen = SCREEN_GAME
            return
        
        for i in range(10):
            row = i // 5
            col = i % 5
            x = 50 + col * 150
            y = 150 + row * 180
            
            slot_rect = pygame.Rect(x, y, 130, 150)
            if slot_rect.collidepoint(mouse_pos):
                if is_save:
                    if save_slots[i] is not None:
                        slot_to_overwrite = i
                        current_screen = SCREEN_CONFIRM_OVERWRITE
                    else:
                        save_game(i)
                        current_screen = SCREEN_GAME
                else:
                    if load_game(i):
                        current_screen = SCREEN_GAME
                return


def draw_confirm_overwrite_screen():
    draw_save_load_screen(is_save=True)
    
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    dialog_rect = pygame.Rect(200, 200, 400, 200)
    pygame.draw.rect(screen, COLORS["confirm_bg"], dialog_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS["option_border"], dialog_rect, width=2, border_radius=10)
    
    warning_text = f"确定要覆盖存档位 {slot_to_overwrite + 1} 吗？"
    warning_surf = dialog_font.render(warning_text, True, COLORS["dialog_text"])
    screen.blit(warning_surf, (dialog_rect.centerx - warning_surf.get_width() // 2, dialog_rect.y + 60))
    
    buttons = [
        {"text": "确定", "rect": pygame.Rect(dialog_rect.x + 80, dialog_rect.y + 130, 100, 40)},
        {"text": "取消", "rect": pygame.Rect(dialog_rect.x + 220, dialog_rect.y + 130, 100, 40)}
    ]
    
    mouse_pos = pygame.mouse.get_pos()
    for btn in buttons:
        is_hover = btn["rect"].collidepoint(mouse_pos)
        color = COLORS["button_hover"] if is_hover else COLORS["button"]
        pygame.draw.rect(screen, color, btn["rect"], border_radius=5)
        text_surf = option_font.render(btn["text"], True, COLORS["dialog_text"])
        screen.blit(text_surf, (btn["rect"].centerx - text_surf.get_width() // 2,
                                btn["rect"].y + 10))


def handle_confirm_overwrite_events(event):
    global current_screen, slot_to_overwrite
    
    mouse_pos = pygame.mouse.get_pos()
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        if pygame.Rect(280, 330, 100, 40).collidepoint(mouse_pos):
            if slot_to_overwrite != -1:
                save_game(slot_to_overwrite)
                slot_to_overwrite = -1
            current_screen = SCREEN_GAME
        elif pygame.Rect(420, 330, 100, 40).collidepoint(mouse_pos):
            slot_to_overwrite = -1
            current_screen = SCREEN_SAVE


def draw_confirm_exit_screen():
    draw_game_screen()
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    dialog_rect = pygame.Rect(200, 200, 400, 200)
    pygame.draw.rect(screen, COLORS["confirm_bg"], dialog_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS["option_border"], dialog_rect, width=2, border_radius=10)
    
    warning_text = "是否确实要返回主界面？"
    warning_surf = dialog_font.render(warning_text, True, COLORS["dialog_text"])
    screen.blit(warning_surf, (dialog_rect.centerx - warning_surf.get_width() // 2, dialog_rect.y + 40))
    
    warning_text2 = "未保存的进度将会消失！"
    warning_surf2 = dialog_font.render(warning_text2, True, (255, 100, 100))
    screen.blit(warning_surf2, (dialog_rect.centerx - warning_surf2.get_width() // 2, dialog_rect.y + 80))
    
    buttons = [
        {"text": "确定", "rect": pygame.Rect(dialog_rect.x + 80, dialog_rect.y + 130, 100, 40)},
        {"text": "取消", "rect": pygame.Rect(dialog_rect.x + 220, dialog_rect.y + 130, 100, 40)}
    ]
    
    mouse_pos = pygame.mouse.get_pos()
    for btn in buttons:
        is_hover = btn["rect"].collidepoint(mouse_pos)
        color = COLORS["button_hover"] if is_hover else COLORS["button"]
        pygame.draw.rect(screen, color, btn["rect"], border_radius=5)
        text_surf = option_font.render(btn["text"], True, COLORS["dialog_text"])
        screen.blit(text_surf, (btn["rect"].centerx - text_surf.get_width() // 2,
                                btn["rect"].y + 10))


def handle_confirm_exit_events(event):
    global current_screen
    
    mouse_pos = pygame.mouse.get_pos()
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        if pygame.Rect(280, 330, 100, 40).collidepoint(mouse_pos):
            current_screen = SCREEN_START
        elif pygame.Rect(420, 330, 100, 40).collidepoint(mouse_pos):
            current_screen = SCREEN_GAME


def quick_save():
    empty_slot = next((i for i, slot in enumerate(save_slots) if slot is None), -1)
    if empty_slot != -1:
        save_game(empty_slot)
        add_info_message(f"快速存档到槽位 {empty_slot + 1}", "save")
    else:
        save_game(9)
        add_info_message("快速存档到槽位 10", "save")


def quick_load():
    latest_slot = -1
    latest_time = None
    
    for i, slot in enumerate(save_slots):
        if slot is not None:
            slot_time = datetime.strptime(slot["timestamp"], "%Y-%m-%d %H:%M:%S")
            if latest_time is None or slot_time > latest_time:
                latest_time = slot_time
                latest_slot = i
    
    if latest_slot != -1:
        load_game(latest_slot)
        add_info_message(f"从槽位 {latest_slot + 1} 快速读档", "load")
        return True
    else:
        add_info_message("没有找到存档", "warning")
        return False


def handle_game_events(event):
    global typing, current_node, display_text, show_options, current_screen, history_scroll_offset, INFO_PANEL_VISIBLE, option_typing
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            handle_space_press()
        elif event.key == pygame.K_ESCAPE:
            current_screen = SCREEN_CONFIRM_EXIT
        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            current_screen = SCREEN_SAVE
        elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
            current_screen = SCREEN_HISTORY
            history_scroll_offset = 0
        elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
            current_screen = SCREEN_LOAD
        elif event.key == pygame.K_F5:
            quick_save()
        elif event.key == pygame.K_F9:
            quick_load()
        elif event.key == pygame.K_F1:
            INFO_PANEL_VISIBLE = not INFO_PANEL_VISIBLE
    
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if INFO_PANEL_VISIBLE:
            panel_rect = pygame.Rect(50, 50, 700, info_panel_height)
            close_rect = pygame.Rect(panel_rect.right - 30, panel_rect.y + 5, 25, 25)
            if close_rect.collidepoint(event.pos):
                INFO_PANEL_VISIBLE = False
                return
        
        if show_options:
            if option_typing:
                # 如果选项正在打字，点击则立即完成所有选项的打字
                complete_option_typing()
            else:
                check_option_click()
        else:
            handle_space_press()
    
    elif event.type == pygame.MOUSEWHEEL:
        if current_screen == SCREEN_HISTORY:
            history_scroll_offset = max(0, history_scroll_offset - event.y * 30)


def handle_space_press():
    global typing, display_text, show_options, option_typing
    
    if typing:
        typing = False
        display_text = story[current_node]["text"]
        show_options = True
        # 开始选项打字
        start_option_typing()
    elif option_typing:
        # 如果选项正在打字，空格键也立即完成所有选项的打字
        complete_option_typing()
    else:
        advance_dialog()


def start_option_typing():
    global option_typing, option_display_texts, option_typing_index, option_last_char_time
    
    current_data = story.get(current_node, {})
    options = get_filtered_options(current_data.get("options", []))
    
    if options:
        option_typing = True
        option_display_texts = [""] * len(options)
        option_typing_index = 0
        option_last_char_time = time.time()


def complete_option_typing():
    global option_typing, option_display_texts
    
    current_data = story.get(current_node, {})
    options = get_filtered_options(current_data.get("options", []))
    
    if options:
        for i in range(len(options)):
            option_display_texts[i] = options[i]["text"]
        option_typing = False


def get_conditional_next(node_data):
    if "conditional_next" in node_data:
        for condition_data in node_data["conditional_next"]:
            if check_conditions(condition_data.get("conditions", {})):
                return condition_data["next"]
    return None


def advance_dialog():
    global current_node, display_text, typing, show_options, current_character, current_display_mode, fullscreen_bg_color, fullscreen_text_color, current_background, current_screen, ending_name, ending_timer, option_typing
    
    if not typing:
        current_data = story.get(current_node, {})
        if "ending" in current_data:
            ending_name = current_data["ending"]
            current_screen = SCREEN_ENDING
            ending_timer = time.time()
            return
        
        if "options" not in story[current_node]:
            add_to_history(current_character, story[current_node]["text"])
        
        next_node = get_conditional_next(current_data)
        if next_node:
            current_node = next_node
        elif "next" in story[current_node]:
            current_node = story[current_node]["next"]
        elif "options" not in story[current_node]:
            current_node = "start"
        
        display_text = ""
        typing = True
        show_options = False
        option_typing = False
        
        current_character = story[current_node].get("name")
        
        display_mode = story[current_node].get("display_mode", "dialog")
        current_display_mode = DISPLAY_FULLSCREEN if display_mode == "fullscreen" else DISPLAY_DIALOG
        
        if "bg_color" in story[current_node]:
            try:
                rgb = tuple(map(int, story[current_node]["bg_color"].split(',')))
                fullscreen_bg_color = rgb
            except:
                fullscreen_bg_color = COLORS["fullscreen_bg"]
        
        if "text_color" in story[current_node]:
            try:
                rgb = tuple(map(int, story[current_node]["text_color"].split(',')))
                fullscreen_text_color = rgb
            except:
                fullscreen_text_color = COLORS["fullscreen_text"]
        
        if "background" in story[current_node]:
            bg_name = story[current_node]["background"]
            if bg_name in background_images:
                current_background = background_images[bg_name]
            else:
                current_background = None
        else:
            current_background = None
        
        process_node_values(story[current_node])
        
        if "sound" in story[current_node]:
            play_sound(story[current_node]["sound"])


def play_sound(sound_name):
    global current_sound
    
    if sound_name in sounds:
        if current_sound:
            current_sound.stop()
        current_sound = sounds[sound_name]
        current_sound.set_volume(volume)
        current_sound.play()


def check_option_click():
    global current_node, display_text, typing, show_options, option_typing
    
    mouse_pos = pygame.mouse.get_pos()
    current_data = story.get(current_node, {})
    options = get_filtered_options(current_data.get("options", []))
    
    if option_typing:
        return
    
    if current_display_mode == DISPLAY_FULLSCREEN:
        base_y = 500
        option_width = 250
        start_x = (800 - option_width * len(options)) // 2 if len(options) > 0 else 275
        
        for i, option in enumerate(options):
            option_rect = pygame.Rect(start_x + i * (option_width + 20), base_y, option_width, 40)
            if option_rect.collidepoint(mouse_pos):
                add_to_history(None, option["text"], is_option=True)
                show_options = False
                option_typing = False
                transition_to_next(option["next"])
    else:
        dialog_top = 380
        base_y = dialog_top - 5
        
        for i, option in enumerate(options):
            option_rect = pygame.Rect(520, base_y - (len(options) - i) * 48, 220, 36)
            if option_rect.collidepoint(mouse_pos):
                add_to_history(None, option["text"], is_option=True)
                show_options = False
                option_typing = False
                transition_to_next(option["next"])


def transition_to_next(next_node):
    global current_node, display_text, typing, show_options, current_sound, current_character, current_display_mode, fullscreen_bg_color, fullscreen_text_color, current_background, option_typing
    
    if current_sound:
        current_sound.stop()
    
    current_node = next_node
    display_text = ""
    typing = True
    show_options = False
    option_typing = False
    
    current_character = story[current_node].get("name")
    
    display_mode = story[current_node].get("display_mode", "dialog")
    current_display_mode = DISPLAY_FULLSCREEN if display_mode == "fullscreen" else DISPLAY_DIALOG
    
    if "bg_color" in story[current_node]:
        try:
            rgb = tuple(map(int, story[current_node]["bg_color"].split(',')))
            fullscreen_bg_color = rgb
        except:
            fullscreen_bg_color = COLORS["fullscreen_bg"]
    
    if "text_color" in story[current_node]:
        try:
            rgb = tuple(map(int, story[current_node]["text_color"].split(',')))
            fullscreen_text_color = rgb
        except:
            fullscreen_text_color = COLORS["fullscreen_text"]
    
    if "background" in story[current_node]:
        bg_name = story[current_node]["background"]
        if bg_name in background_images:
            current_background = background_images[bg_name]
        else:
            current_background = None
    else:
        current_background = None
    
    process_node_values(story[current_node])
    
    if "sound" in story[current_node]:
        sound_name = story[current_node]["sound"]
        if sound_name in sounds:
            current_sound = sounds[sound_name]
            current_sound.play()


def update_text():
    global display_text, typing, last_char_time, show_options, last_type_sound_time, option_typing, option_display_texts, option_typing_index, option_last_char_time
    
    if typing:
        current_time = time.time()
        
        if current_time - last_char_time > typing_speed:
            target_text = story[current_node]["text"]
            if len(display_text) < len(target_text):
                display_text += target_text[len(display_text)]
                last_char_time = current_time
                
                if current_character and current_character in type_sounds:
                    if current_time - last_type_sound_time > type_sound_delay:
                        sound = type_sounds[current_character]
                        sound.set_volume(volume * 0.3)
                        sound.play()
                        last_type_sound_time = current_time
            else:
                typing = False
                show_options = True
                # 开始选项打字
                start_option_typing()
    
    # 更新选项打字
    if option_typing:
        current_time = time.time()
        current_data = story.get(current_node, {})
        options = get_filtered_options(current_data.get("options", []))
        
        if current_time - option_last_char_time > option_typing_speed:
            if option_typing_index < len(options):
                current_option_text = options[option_typing_index]["text"]
                if len(option_display_texts[option_typing_index]) < len(current_option_text):
                    option_display_texts[option_typing_index] += current_option_text[
                        len(option_display_texts[option_typing_index])]
                    option_last_char_time = current_time
                else:
                    option_typing_index += 1
                    if option_typing_index < len(options):
                        option_last_char_time = current_time
            else:
                option_typing = False


def check_auto_save():
    global last_auto_save_time
    
    if auto_save_enabled and current_screen == SCREEN_GAME:
        current_time = time.time()
        if current_time - last_auto_save_time > auto_save_interval * 60:
            empty_slot = next((i for i, slot in enumerate(save_slots) if slot is None), -1)
            if empty_slot != -1:
                save_game(empty_slot)
            else:
                save_game(9)
            
            last_auto_save_time = current_time
            add_info_message("已自动存档", "save")


def draw_game_screen():
    if current_display_mode == DISPLAY_FULLSCREEN:
        draw_fullscreen_mode()
    else:
        draw_dialog_mode()
    
    draw_info_panel()


def draw_dialog_mode():
    if current_background:
        screen.blit(current_background, (0, 0))
    else:
        screen.fill(COLORS["background"])
    
    if current_character and current_character in character_expressions:
        current_data = story.get(current_node, {})
        expression = current_data.get("expression", "default")
        
        if expression in character_expressions[current_character]:
            sprite = character_expressions[current_character][expression]
            
            # 缩放精灵图 - 保持宽高比
            scale_factor = 0.8
            new_width = int(sprite.get_width() * scale_factor)
            new_height = int(sprite.get_height() * scale_factor)
            sprite = pygame.transform.smoothscale(sprite, (new_width, new_height))
            
            # 根据位置绘制
            if character_position == "left":
                screen.blit(sprite, (50, 100))
            elif character_position == "right":
                screen.blit(sprite, (450, 100))
            else:
                screen.blit(sprite, (250, 100))
    
    # 绘制对话框
    dialog_rect = pygame.Rect(50, 380, 700, 200)
    dialog_surface = pygame.Surface((700, 200), pygame.SRCALPHA)
    dialog_surface.fill(COLORS["dialog_bg"])
    screen.blit(dialog_surface, (50, 380))
    
    current_data = story.get(current_node, {})
    
    character_name = current_data.get("name")
    if character_name:
        name_surf = name_font.render(character_name, True, COLORS["name_text"])
        screen.blit(name_surf, (dialog_rect.x + 30, dialog_rect.y + 10))
    
    text_segments = parse_styled_text(display_text)
    start_x = dialog_rect.x + 30
    start_y = dialog_rect.y + (60 if character_name else 30)
    current_x = start_x
    current_y = start_y
    line_height = dialog_font.get_linesize() + 5
    
    for segment in text_segments:
        if segment['text'] == '\n':
            current_x = start_x
            current_y += line_height
            continue
        
        words = segment['text'].split(' ')
        space_width = segment['font'].size(' ')[0]
        
        for word in words:
            if not word:
                continue
            
            word_surface = segment['font'].render(word, True, segment['color'])
            word_width, word_height = word_surface.get_size()
            
            if current_x + word_width > dialog_rect.right - 30:
                current_x = start_x
                current_y += line_height
            
            screen.blit(word_surface, (current_x, current_y))
            current_x += word_width + space_width
    
    if show_options and not typing:
        options = get_filtered_options(current_data.get("options", []))
        dialog_top = 380
        base_y = dialog_top - 5
        
        for i, option in enumerate(options):
            option_rect = pygame.Rect(520, base_y - (len(options) - i) * 48, 220, 36)
            is_hover = option_rect.collidepoint(pygame.mouse.get_pos())
            base_color = COLORS["option_hover"] if is_hover else COLORS["option_bg"]
            
            pygame.draw.rect(screen, base_color, option_rect, border_radius=6)
            pygame.draw.rect(screen, COLORS["option_border"], option_rect, width=2, border_radius=6)
            
            # 使用选项的显示文本（可能是部分文本，如果正在打字）
            option_text = option_display_texts[i] if i < len(option_display_texts) else option["text"]
            
            # 解析选项文本的样式
            option_segments = parse_styled_text(option_text)
            
            text_x = option_rect.x + 8
            text_y = option_rect.y + 6
            
            for segment in option_segments:
                if segment['text'] == '\n':
                    continue
                
                text_surf = segment['font'].render(segment['text'], True, (30, 30, 30))
                screen.blit(text_surf, (text_x, text_y))
                
                text_surf = segment['font'].render(segment['text'], True, segment['color'])
                screen.blit(text_surf, (text_x - 2, text_y - 2))
                
                text_x += text_surf.get_width()
    
    if not show_options and not typing and "options" not in current_data:
        prompt_surf = dialog_font.render("点击继续...", True, (200, 200, 200))
        screen.blit(prompt_surf, (dialog_rect.right - 120, dialog_rect.bottom - 30))
    
    current_time = datetime.now().strftime("%H:%M")
    time_surf = small_font.render(current_time, True, (200, 200, 200))
    screen.blit(time_surf, (730, 10))
    
    draw_bottom_hints()


def draw_fullscreen_mode():
    if current_background:
        screen.blit(current_background, (0, 0))
    else:
        screen.fill(fullscreen_bg_color)
    
    current_data = story.get(current_node, {})
    
    text_segments = parse_styled_text(display_text, use_fullscreen=True)
    
    max_width = 700
    line_height = fullscreen_font.get_linesize() + 10
    total_height = 0
    
    temp_lines = []
    for segment in text_segments:
        if segment['text'] == '\n':
            temp_lines.append(None)
            continue
        
        words = segment['text'].split(' ')
        current_line = []
        current_width = 0
        space_width = segment['font'].size(' ')[0]
        
        for word in words:
            if not word:
                continue
            
            word_width = segment['font'].size(word)[0]
            if current_line and current_width + space_width + word_width > max_width:
                temp_lines.append((current_line, segment))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += (space_width if current_line else 0) + word_width
        
        if current_line:
            temp_lines.append((current_line, segment))
    
    total_height = len(temp_lines) * line_height
    start_y = (600 - total_height) // 2
    current_y = start_y
    
    for item in temp_lines:
        if item is None:
            current_y += line_height
            continue
        
        words, segment = item
        if not words:
            continue
        
        line_text = ' '.join(words)
        text_surface = segment['font'].render(line_text, True, segment['color'])
        text_width = text_surface.get_width()
        
        current_x = (800 - text_width) // 2
        screen.blit(text_surface, (current_x, current_y))
        
        current_y += line_height
    
    if show_options and not typing:
        options = get_filtered_options(current_data.get("options", []))
        if options:
            base_y = 500
            option_width = 250
            start_x = (800 - option_width * len(options)) // 2 if len(options) > 0 else 275
            
            for i, option in enumerate(options):
                option_rect = pygame.Rect(start_x + i * (option_width + 20), base_y, option_width, 40)
                is_hover = option_rect.collidepoint(pygame.mouse.get_pos())
                base_color = COLORS["option_hover"] if is_hover else COLORS["option_bg"]
                
                pygame.draw.rect(screen, base_color, option_rect, border_radius=6)
                pygame.draw.rect(screen, COLORS["option_border"], option_rect, width=2, border_radius=6)
                
                # 使用选项的显示文本（可能是部分文本，如果正在打字）
                option_text = option_display_texts[i] if i < len(option_display_texts) else option["text"]
                
                # 解析选项文本的样式
                option_segments = parse_styled_text(option_text, use_fullscreen=True)
                
                text_x = option_rect.x + 10
                text_y = option_rect.y + 10
                
                for segment in option_segments:
                    if segment['text'] == '\n':
                        continue
                    
                    text_surf = segment['font'].render(segment['text'], True, segment['color'])
                    screen.blit(text_surf, (text_x, text_y))
                    text_x += text_surf.get_width()
    
    if not show_options and not typing and "options" not in current_data:
        prompt_surf = fullscreen_font.render("点击继续...", True, (200, 200, 200))
        screen.blit(prompt_surf, (400 - prompt_surf.get_width() // 2, 520))


def draw_bottom_hints():
    hint_rect = pygame.Rect(0, 580, 800, 20)
    hint_bg = pygame.Surface((800, 20), pygame.SRCALPHA)
    hint_bg.fill((0, 0, 0, 150))
    screen.blit(hint_bg, hint_rect)
    
    shortcut_hints = []
    shortcut_hints.append("F1: 信息面板")
    shortcut_hints.append("F5/F9: 快速存/读档")
    shortcut_hints.append("Ctrl+S/O: 存档/读档")
    shortcut_hints.append("ESC: 主菜单")
    
    x_pos = 10
    y_pos = 582
    
    for hint in shortcut_hints:
        color = (180, 180, 200)
        
        hint_surf = small_font.render(hint, True, color)
        
        if x_pos + hint_surf.get_width() < 790:
            screen.blit(hint_surf, (x_pos, y_pos))
            x_pos += hint_surf.get_width() + 20


def draw_history_screen():
    # 创建半透明覆盖层
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    
    # 绘制历史记录面板
    history_rect = pygame.Rect(50, 50, 700, 500)
    pygame.draw.rect(screen, COLORS["history_bg"], history_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS["option_border"], history_rect, width=2, border_radius=10)
    
    # 绘制标题
    title_surf = title_font.render("历史记录", True, COLORS["title"])
    screen.blit(title_surf, (history_rect.centerx - title_surf.get_width() // 2, history_rect.y + 20))
    
    # 绘制返回按钮
    back_rect = pygame.Rect(history_rect.right - 120, history_rect.y + 20, 100, 30)
    mouse_pos = pygame.mouse.get_pos()
    color = COLORS["button_hover"] if back_rect.collidepoint(mouse_pos) else COLORS["button"]
    pygame.draw.rect(screen, color, back_rect, border_radius=5)
    text_surf = option_font.render("返回", True, COLORS["dialog_text"])
    screen.blit(text_surf,
                (back_rect.centerx - text_surf.get_width() // 2, back_rect.centery - text_surf.get_height() // 2))
    
    # 绘制内容区域
    content_rect = pygame.Rect(
        history_rect.x + 20,
        history_rect.y + 70,
        history_rect.width - 40,
        history_rect.height - 90
    )
    pygame.draw.rect(screen, (20, 25, 35, 200), content_rect, border_radius=5)
    
    # 计算内容区域可以显示的最大行数
    line_height = 25
    max_lines = (content_rect.height - 20) // line_height
    
    # 从历史记录的末尾开始，计算要显示的消息范围
    # 确保只显示最后几条消息，不允许滚动
    start_index = max(0, len(text_history) - max_lines)
    visible_history = text_history[start_index:]
    
    # 从顶部开始绘制
    current_y = content_rect.y + 10
    
    for entry in visible_history:
        # 绘制角色名（如果有）
        if not entry["is_option"] and entry["character"]:
            char_surf = history_font.render(entry["character"] + "：", True, COLORS["name_text"])
            screen.blit(char_surf, (content_rect.x + 10, current_y))
            text_start_x = content_rect.x + 10 + char_surf.get_width()
        else:
            text_start_x = content_rect.x + 10
        
        # 绘制对话内容
        if entry["is_option"]:
            option_text = "【选项】" + entry["text"]
            text_surf = history_font.render(option_text, True, COLORS["history_option"])
            screen.blit(text_surf, (text_start_x, current_y))
            current_y += line_height
        else:
            # 处理多行文本
            text_segments = parse_styled_text(entry["text"], use_history=True)
            current_x = text_start_x
            
            for segment in text_segments:
                if segment['text'] == '\n':  # 处理换行
                    current_x = text_start_x
                    current_y += line_height
                    continue
                
                # 检查文本宽度，如果需要换行
                text_width = segment['font'].size(segment['text'])[0]
                if current_x + text_width > content_rect.right - 10:
                    current_x = text_start_x
                    current_y += line_height
                
                # 绘制文本片段
                text_surf = segment['font'].render(segment['text'], True, segment['color'])
                screen.blit(text_surf, (current_x, current_y))
                current_x += text_width
            
            # 每条消息后换行
            current_y += line_height
        
        # 检查是否超出内容区域
        if current_y > content_rect.bottom - 10:
            break
    
    # 如果历史记录为空，显示提示
    if len(text_history) == 0:
        empty_text = "历史记录为空"
        empty_surf = history_font.render(empty_text, True, COLORS["history_text"])
        screen.blit(empty_surf, (content_rect.centerx - empty_surf.get_width() // 2,
                                 content_rect.centery - empty_surf.get_height() // 2))


def handle_history_events(event):
    global current_screen
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = pygame.mouse.get_pos()
        
        # 返回按钮检测
        history_rect = pygame.Rect(50, 50, 700, 500)
        back_rect = pygame.Rect(history_rect.right - 120, history_rect.y + 20, 100, 30)
        
        if back_rect.collidepoint(mouse_pos):
            current_screen = SCREEN_GAME  # 返回游戏界面

def draw_ending_screen():
    screen.fill((0, 0, 0))
    
    ending_title = f"【{ending_name}结局】达成"
    title_surf = ending_font.render(ending_title, True, COLORS["ending_title"])
    screen.blit(title_surf, (400 - title_surf.get_width() // 2, 250))
    
    prompt_text = "返回主界面..."
    prompt_surf = dialog_font.render(prompt_text, True, (200, 200, 200))
    screen.blit(prompt_surf, (400 - prompt_surf.get_width() // 2, 320))


def handle_ending_events(event):
    global current_screen, ending_timer
    
    current_time = time.time()
    
    if event.type == pygame.MOUSEBUTTONDOWN or current_time - ending_timer > ending_duration:
        current_screen = SCREEN_START


load_game_data()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if current_screen == SCREEN_START:
            handle_start_events(event)
        elif current_screen == SCREEN_SETTINGS:
            handle_settings_events(event)
        elif current_screen == SCREEN_GAME:
            handle_game_events(event)
        elif current_screen == SCREEN_SAVE:
            handle_save_load_events(event, is_save=True)
        elif current_screen == SCREEN_LOAD:
            handle_save_load_events(event, is_save=False)
        elif current_screen == SCREEN_CONFIRM_EXIT:
            handle_confirm_exit_events(event)
        elif current_screen == SCREEN_CONFIRM_OVERWRITE:
            handle_confirm_overwrite_events(event)
        elif current_screen == SCREEN_HISTORY:
            handle_history_events(event)
        elif current_screen == SCREEN_ENDING:
            handle_ending_events(event)
    
    if current_screen == SCREEN_LOADING:
        update_loading()
    elif current_screen == SCREEN_GAME:
        update_text()
        check_auto_save()
    
    screen.fill(COLORS["background"])
    
    if current_screen == SCREEN_START:
        draw_start_screen()
    elif current_screen == SCREEN_LOADING:
        draw_loading_screen()
    elif current_screen == SCREEN_SETTINGS:
        draw_settings_screen()
    elif current_screen == SCREEN_GAME:
        draw_game_screen()
    elif current_screen == SCREEN_SAVE:
        draw_save_load_screen(is_save=True)
    elif current_screen == SCREEN_LOAD:
        draw_save_load_screen(is_save=False)
    elif current_screen == SCREEN_CONFIRM_EXIT:
        draw_game_screen()
        draw_confirm_exit_screen()
    elif current_screen == SCREEN_CONFIRM_OVERWRITE:
        draw_confirm_overwrite_screen()
    elif current_screen == SCREEN_HISTORY:
        draw_game_screen()
        draw_history_screen()
    elif current_screen == SCREEN_ENDING:
        draw_ending_screen()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()