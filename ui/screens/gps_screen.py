import pygame


class GpsScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.title_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.08)
        )

    def draw(self, screen, state=None):
        w, h = screen.get_size()

        title = self.title_font.render("GPS", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(w * 0.5, h * 0.45)))

        subtitle = self.title_font.render("COMING SOON", True, (120, 120, 120))
        screen.blit(subtitle, subtitle.get_rect(center=(w * 0.5, h * 0.58)))
