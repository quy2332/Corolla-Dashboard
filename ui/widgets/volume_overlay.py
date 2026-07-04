import time
import pygame


class VolumeOverlay:
    def __init__(self, height):
        self.visible_until = 0

        self.label_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.032)
        )

    def show(self, duration=2.0):
        self.visible_until = time.time() + duration

    def is_visible(self):
        return time.time() < self.visible_until

    def draw(self, screen, volume_percent):
        if not self.is_visible():
            return

        w, h = screen.get_size()

        bar_w = w * 0.34
        bar_h = h * 0.018
        x = (w - bar_w) / 2
        y = h * 0.925

        fill_w = bar_w * (volume_percent / 100)

        label = self.label_font.render("VOL", True, (150, 150, 160))
        value = self.label_font.render("{}%".format(volume_percent), True, (180, 180, 190))

        screen.blit(label, label.get_rect(midright=(x - 12, y + bar_h / 2)))
        screen.blit(value, value.get_rect(midleft=(x + bar_w + 12, y + bar_h / 2)))

        pygame.draw.rect(screen, (60, 60, 70), pygame.Rect(x, y, bar_w, bar_h))
        pygame.draw.rect(screen, (230, 230, 240), pygame.Rect(x, y, fill_w, bar_h))
