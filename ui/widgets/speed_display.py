import pygame


class SpeedDisplay:
    def __init__(self, height):
        self.font_speed = pygame.font.Font(
            "assets/fonts/Untitled1.ttf",
            int(height * 0.12)
        )
        self.font_unit = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.04)
        )

    def draw(self, screen, speed_mph, center, height):
        speed = self.font_speed.render(f"{speed_mph:0.0f}", True, (255, 255, 255))
        mph = self.font_unit.render("mp/h", True, (255, 255, 255))

        screen.blit(speed, speed.get_rect(center=(center[0], height * 0.22)))
        screen.blit(mph, mph.get_rect(center=(center[0], height * 0.29)))
