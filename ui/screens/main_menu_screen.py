import pygame


class MainMenuScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.options = [
            ("Gauge", "gauge"),
            ("System Info", "system"),
        ]

        self.selected_index = 0

        self.title_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.09)
        )
        self.option_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.055)
        )
        self.hint_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.032)
        )

    def move_up(self):
        self.selected_index = (self.selected_index - 1) % len(self.options)

    def move_down(self):
        self.selected_index = (self.selected_index + 1) % len(self.options)

    def get_selected_screen(self):
        return self.options[self.selected_index][1]

    def draw(self, screen, state=None):
        w, h = screen.get_size()

        title = self.title_font.render("COROLLA OS", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(w * 0.5, h * 0.15)))

        start_y = h * 0.34
        box_w = w * 0.72
        box_h = h * 0.11
        gap = h * 0.04

        for i, (label, _) in enumerate(self.options):
            x = (w - box_w) / 2
            y = start_y + i * (box_h + gap)

            is_selected = i == self.selected_index

            bg_color = (255, 255, 255) if is_selected else (35, 35, 42)
            text_color = (15, 15, 18) if is_selected else (220, 220, 220)

            rect = pygame.Rect(x, y, box_w, box_h)
            pygame.draw.rect(screen, bg_color, rect)

            text = self.option_font.render(label, True, text_color)
            screen.blit(text, text.get_rect(center=rect.center))

        hint = self.hint_font.render("UP/DOWN SELECT   ENTER OPEN   ESC BACK", True, (120, 120, 120))
        screen.blit(hint, hint.get_rect(center=(w * 0.5, h * 0.90)))
