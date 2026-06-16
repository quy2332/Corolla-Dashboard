import pygame


class GearDisplay:
    def __init__(self, height):
        self.font_gear = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.38)
        )

    def draw(self, screen, gear_value, center, height):
        gear = self.font_gear.render(str(gear_value), True, (255, 255, 255))
        screen.blit(gear, gear.get_rect(center=(center[0], height * 0.47)))
