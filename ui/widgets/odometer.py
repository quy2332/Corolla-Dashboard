import pygame

class Odometer:
    def __init__(self, height):
        self.font_value = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.035)
        )

        self.font_unit =  pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.022)
        )

    def draw(self, screen, miles, center,height):
        value = self.font_value.render(
            f"{miles:06.0f}",
            True,
            (255,255,255)
        )

        unit = self.font_unit.render(
            "mi",
            True,
            (255,255,255)
        )
    
        gap = int(height * 0.008)
        padding_x = int(height * 0.018)
        padding_y = int(height * 0.005)

        total_width = value.get_width() + gap + unit.get_width()

        total_height = max(value.get_height(), unit.get_height())

        odometer_center = (
            center[0],
            int(height * 0.67)
        )

        background = pygame.Rect(
            odometer_center[0] - total_width / 2 - padding_x,
            odometer_center[1] - total_height / 2 - padding_y,
            total_width + padding_x * 2,
            total_height + padding_y * 2
        )

        pygame.draw.rect(
            screen,
            (55, 55, 55),
            background,
            border_radius=int(height * 0.012)
        )

        value_rect = value.get_rect(
            midleft=(
                background.left + padding_x,
                odometer_center[1]
            )
        )

        unit_rect = unit.get_rect(
            midleft=(
                value_rect.right + gap,
                odometer_center[1]
            )
        )

        screen.blit(value, value_rect)
        screen.blit(unit, unit_rect)