import pygame

from ui.screens.gauge_screen import GaugeScreen


class Dashboard:
    def __init__(self, width=800, height=480):
        pygame.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Corolla OS")

        self.current_screen = GaugeScreen(width, height)
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def render(self, state):
        self.handle_events()

        self.screen.fill((15, 15, 18))
        self.current_screen.draw(self.screen, state)

        pygame.display.flip()

    def close(self):
        pygame.quit()
