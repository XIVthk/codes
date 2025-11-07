import pygame
import json
import time
import sys

# 初始化Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Game")
clock = pygame.time.Clock()

# ===== 颜色配置 =====
COLORS = {
    "background": (20, 25, 35),
    "dialog_bg": (40, 45, 60, 220),
    "name_text": (255, 220, 100),
    "dialog_text": (240, 240, 240),
    "option_bg": (65, 70, 85),
    "option_hover": (90, 95, 110),
    "option_border": (170, 170, 190)
}

# ===== 字体加载 =====
try:
    font = pygame.font.Font("fonts/5i1tf1.ttf", 24)
    option_font = pygame.font.Font("fonts/5i1tf1.ttf", 22)
except Exception as e:
    print("字体加载失败:", e)
    pygame.quit()
    sys.exit()

# ===== 加载对话数据 =====
try:
    with open('data/story.json', 'r', encoding='utf-8') as f:
        story = json.load(f)
    assert "start" in story
except Exception as e:
    print("对话加载失败:", e)
    pygame.quit()
    sys.exit()

# ===== 游戏状态 =====
current_node = "start"
display_text = ""
typing = True  # 初始为打字状态
last_char_time = time.time()
typing_speed = 0.05
show_options = False  # 新增：控制选项显示的状态


# ===== 核心函数优化 =====
def handle_events():
    global typing, current_node, display_text, show_options
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            handle_space_press()
        if event.type == pygame.MOUSEBUTTONDOWN and show_options:  # 仅在显示选项时检测点击
            check_option_click()
    return True


def handle_space_press():
    global typing, display_text, show_options
    if typing:
        # 立即完成当前文本显示
        typing = False
        display_text = story[current_node]["text"]  # 确保文本完整
        show_options = True  # 立即显示选项
    else:
        # 只有非打字状态才推进对话
        advance_dialog()

def update_text():
    global display_text, typing, last_char_time, show_options
    if typing:
        current_time = time.time()
        if current_time - last_char_time > typing_speed:
            target_text = story[current_node]["text"]
            if len(display_text) < len(target_text):
                display_text += target_text[len(display_text)]
                last_char_time = current_time
            else:
                # 自然完成打字时也显示选项
                typing = False
                show_options = True


def advance_dialog():
    global current_node, display_text, typing, show_options
    if "ending" in story[current_node]:
        current_node = "start"
        display_text = ""
        typing = True
        show_options = False


def check_option_click():
    global current_node, display_text, typing, show_options
    mouse_pos = pygame.mouse.get_pos()
    options = story[current_node].get("options", [])
    
    dialog_top = 380
    base_y = dialog_top - 5
    
    for i, option in enumerate(options):
        option_rect = pygame.Rect(
            520,
            base_y - (len(options) - i) * 48,
            220,
            36
        )
        if option_rect.collidepoint(mouse_pos):
            show_options = False  # 选择后隐藏选项直到新文本完成
            transition_to_next(option["next"])


def transition_to_next(next_node):
    global current_node, display_text, typing, show_options
    current_node = next_node
    display_text = ""
    typing = True
    show_options = False  # 切换到新节点时重置显示状态


def draw_dialog():
    # 绘制主对话框
    dialog_rect = pygame.Rect(50, 380, 700, 200)
    pygame.draw.rect(screen, COLORS["dialog_bg"], dialog_rect, border_radius=12)
    
    # 绘制角色名
    current_data = story[current_node]
    if current_data.get("name"):
        name_surf = font.render(current_data["name"], True, COLORS["name_text"])
        screen.blit(name_surf, (dialog_rect.x + 30, dialog_rect.y + 15))
    
    # 绘制对话文本
    text_x, text_y = dialog_rect.x + 30, dialog_rect.y + (60 if current_data.get("name") else 30)
    lines = []
    current_line = ""
    for word in display_text.split(' '):
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] < 640:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    for idx, line in enumerate(lines):
        text_surf = font.render(line, True, COLORS["dialog_text"])
        screen.blit(text_surf, (text_x, text_y + idx * 32))
    
    # === 条件渲染选项 ===
    if show_options and not typing:  # 仅在非打字状态显示选项
        options = current_data.get("options", [])
        dialog_top = 380
        base_y = dialog_top - 5
        
        for i, option in enumerate(options):
            option_rect = pygame.Rect(
                520,
                base_y - (len(options) - i) * 48,
                220,
                36
            )
            
            is_hover = option_rect.collidepoint(pygame.mouse.get_pos())
            base_color = COLORS["option_hover"] if is_hover else COLORS["option_bg"]
            
            pygame.draw.rect(screen, base_color, option_rect, border_radius=6)
            pygame.draw.rect(screen, COLORS["option_border"], option_rect, width=2, border_radius=6)
            
            text_surf = option_font.render(option["text"], True, (30, 30, 30))
            screen.blit(text_surf, (option_rect.x + 8, option_rect.y + 6))
            text_surf = option_font.render(option["text"], True, COLORS["dialog_text"])
            screen.blit(text_surf, (option_rect.x + 6, option_rect.y + 4))


# ===== 主循环 =====
running = True
while running:
    running = handle_events()
    update_text()
    screen.fill(COLORS["background"])
    draw_dialog()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()