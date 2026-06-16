import pygame


class RpmDisplay:
    def __init__(self, height):
        self.font_rpm_label = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.045)
        )
        self.font_rpm_value = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.06)
        )

    def draw(self, screen, rpm, anchor, height):
        rpm_label = self.font_rpm_label.render("rpm", True, (255, 255, 255))
        rpm_value = self.font_rpm_value.render(f"{rpm:0.0f}", True, (255, 255, 255))

        rpm_gap = height * 0.014

        rpm_value_rect = rpm_value.get_rect()
        rpm_label_rect = rpm_label.get_rect()

        total_height = rpm_value_rect.height + rpm_gap + rpm_label_rect.height

        rpm_value_rect.centerx = anchor[0]
        rpm_value_rect.top = anchor[1] - total_height / 2

        rpm_label_rect.centerx = anchor[0]
        rpm_label_rect.top = rpm_value_rect.bottom - rpm_gap

        screen.blit(rpm_value, rpm_value_rect)
        screen.blit(rpm_label, rpm_label_rect)
