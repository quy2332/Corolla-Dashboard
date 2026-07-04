import pygame

from ui.widgets.status_bar import StatusBar

class MainMenuScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.status_bar = StatusBar(height)

        self.options = [
            ("GAUGE", "gauge", "assets/images/gauge.png"),
            ("SYSTEM", "system", "assets/images/system.png"),
            ("GPS", "gps", "assets/images/gps.png"),
            ("MUSIC", "music", "assets/images/music.png"),
        ]

        self.selected_index = 0

        self.title_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.09)
        )
        self.label_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.034)
        )
        self.hint_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.030)
        )

        self.icon_size = int(height * 0.24)
        self.highlight_size = int(self.icon_size * 1.08)

        self.icons = {}

        for _, screen_name, filename in self.options:
            image = pygame.image.load(filename).convert_alpha()
            image = pygame.transform.smoothscale(
                image,
                (self.icon_size, self.icon_size)
            )
            self.icons[screen_name] = image

        self.highlight = pygame.image.load(
            "assets/images/highlight.png"
        ).convert_alpha()
        self.highlight = pygame.transform.smoothscale(
            self.highlight,
            (self.highlight_size, self.highlight_size)
        )

    def move_up(self):
        self.move_left()

    def move_down(self):
        self.move_right()

    def move_left(self):
        self.selected_index = (self.selected_index - 1) % len(self.options)

    def move_right(self):
        self.selected_index = (self.selected_index + 1) % len(self.options)

    def get_selected_screen(self):
        return self.options[self.selected_index][1]

    def draw(self, screen, state=None):
        self.status_bar.draw(screen)

        w, h = screen.get_size()

        #title = self.title_font.render("COROLLA OS", True, (245, 245, 245))
        #screen.blit(title, title.get_rect(center=(w * 0.5, h * 0.16)))

        tile_count = len(self.options)
        icon_size = self.icon_size
        gap = w * 0.045

        total_width = tile_count * icon_size + (tile_count - 1) * gap
        start_x = (w - total_width) / 2
        icon_y = h * 0.60

        icon_rects = []

        for i, (_, screen_name, _) in enumerate(self.options):
            x = start_x + i * (icon_size + gap)
            rect = pygame.Rect(x, icon_y, icon_size, icon_size)
            icon_rects.append(rect)

        # Draw icons and labels first
        for i, (label, screen_name, _) in enumerate(self.options):
            rect = icon_rects[i]

            icon = self.icons[screen_name]
            screen.blit(icon, icon.get_rect(center=rect.center))

            is_selected = i == self.selected_index
            label_color = (255, 255, 255) if is_selected else (150, 150, 160)

            label_surface = self.label_font.render(label, True, label_color)
            label_y = rect.bottom + h * 0.045
            screen.blit(
                label_surface,
                label_surface.get_rect(center=(rect.centerx, label_y))
            )

        # Draw highlight on top of selected icon
        selected_rect = icon_rects[self.selected_index]
        highlight_rect = self.highlight.get_rect(center=selected_rect.center)
        screen.blit(self.highlight, highlight_rect)

        hint = self.hint_font.render(
            "LEFT/RIGHT SELECT   ENTER OPEN   ESC BACK",
            True,
            (120, 120, 120)
        )
        screen.blit(hint, hint.get_rect(center=(w * 0.5, h * 0.95)))
