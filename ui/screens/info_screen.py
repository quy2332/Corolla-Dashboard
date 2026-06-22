import subprocess
import pygame


class InfoScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.title_font = pygame.font.Font(
            "assets/fonts/rajdhani-bold.ttf",
            int(height * 0.08)
        )
        self.value_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(height * 0.045)
        )

    def get_cpu_temp(self):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_c = int(f.read().strip()) / 1000
            return f"{temp_c:.1f}°C"
        except Exception:
            return "--.-°C"

    def get_core_voltage(self):
        try:
            result = subprocess.check_output(
                ["vcgencmd", "measure_volts"],
                text=True
            ).strip()
            return result.replace("volt=", "")
        except Exception:
            return "--.--V"

    def get_throttle_status(self):
        try:
            result = subprocess.check_output(
                ["vcgencmd", "get_throttled"],
                text=True
            ).strip()

            value = int(result.replace("throttled=", ""), 16)

            if value == 0:
                return "POWER OK"

            return "POWER WARNING"
        except Exception:
            return "UNKNOWN"

    def draw(self, screen, state=None):
        w, h = screen.get_size()

        title = self.title_font.render("SYSTEM INFO", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(w * 0.5, h * 0.15)))

        rows = [
            ("CPU TEMP", self.get_cpu_temp()),
            ("CORE VOLT", self.get_core_voltage()),
            ("POWER", self.get_throttle_status()),
            ("MODE", "REPLAY"),
        ]

        y = h * 0.32

        for label, value in rows:
            label_surface = self.value_font.render(label, True, (140, 140, 140))
            value_surface = self.value_font.render(value, True, (255, 255, 255))

            screen.blit(label_surface, label_surface.get_rect(midleft=(w * 0.12, y)))
            screen.blit(value_surface, value_surface.get_rect(midright=(w * 0.88, y)))

            y += h * 0.09
