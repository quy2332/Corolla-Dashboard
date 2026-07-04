from datetime import datetime
import pygame


class StatusBar:
    def __init__(self, height):
        self.date_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.045)
        )

        self.time_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.10)
        )

        self.ampm_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.032)
        )

        self.status_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.040)
        )

    def draw(self, screen):
        w, h = screen.get_size()
        now = datetime.now()

        date_text = now.strftime("%a %d %b").upper()
        time_text = now.strftime("%I:%M").lstrip("0")
        ampm_text = now.strftime("%p")
        phone_text = "Phone Is Not Connected"

        y = h * 0.095

        date_surface = self.date_font.render(
            date_text,
            True,
            (255, 255, 255)
        )

        time_surface = self.time_font.render(
            time_text,
            True,
            (255, 255, 255)
        )

        ampm_surface = self.ampm_font.render(
            ampm_text,
            True,
            (255, 255, 255)
        )

        phone_surface = self.status_font.render(
            phone_text,
            True,
            (180, 180, 180)
        )

        screen.blit(
            date_surface,
            date_surface.get_rect(midleft=(w * 0.04, y))
        )

        time_rect = time_surface.get_rect(center=(w * 0.5, y))
        screen.blit(time_surface, time_rect)

        ampm_rect = ampm_surface.get_rect(
            midleft=(time_rect.right + 8, time_rect.centery + 2)
        )
        screen.blit(ampm_surface, ampm_rect)

        screen.blit(
            phone_surface,
            phone_surface.get_rect(midright=(w * 0.96, y))
        )
