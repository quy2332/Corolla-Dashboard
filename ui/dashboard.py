import pygame

from ui.screens.gauge_screen import GaugeScreen
from ui.screens.info_screen import InfoScreen
from ui.screens.main_menu_screen import MainMenuScreen


class Dashboard:
    def __init__(self, width=800, height=480, fullscreen=True):
        pygame.init()

        flags = pygame.FULLSCREEN if fullscreen else 0

        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Corolla OS")

        self.width, self.height = self.screen.get_size()

        self.main_menu = MainMenuScreen(self.width, self.height)

        self.screens = {
            "gauge": GaugeScreen(self.width, self.height),
            "system": InfoScreen(self.width, self.height),
        }

        self.current_screen_name = "main_menu"

        self.split_mode = False
        self.left_screen_name = "gauge"
        self.right_screen_name = "main_menu"
        self.focus_side = "right"

        self.running = True

    def enter_split_mode(self):
        if self.current_screen_name != "main_menu":
            self.left_screen_name = self.current_screen_name
        else:
            self.left_screen_name = "gauge"

        self.right_screen_name = "main_menu"
        self.focus_side = "right"
        self.split_mode = True

    def exit_split_mode(self):
        self.current_screen_name = self.left_screen_name
        self.split_mode = False

    def select_main_menu_option(self):
        selected = self.main_menu.get_selected_screen()

        if self.split_mode:
            self.right_screen_name = selected
            self.focus_side = "right"
        else:
            self.current_screen_name = selected

    def maximize_focused_panel(self):
        if self.focus_side == "left":
            self.current_screen_name = self.left_screen_name
        else:
            self.current_screen_name = self.right_screen_name

        self.split_mode = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                if self.split_mode:
                    self.exit_split_mode()
                elif self.current_screen_name == "main_menu":
                    self.running = False
                else:
                    self.current_screen_name = "main_menu"

            elif event.key == pygame.K_RIGHT:
                if self.current_screen_name == "main_menu" and not self.split_mode:
                    return

                if not self.split_mode:
                    self.enter_split_mode()
                else:
                    self.focus_side = "right"

            elif event.key == pygame.K_LEFT:
                if self.split_mode:
                    self.focus_side = "left"

            elif event.key == pygame.K_UP:
                if self.current_screen_name == "main_menu":
                    self.main_menu.move_up()
                elif self.split_mode and self.right_screen_name == "main_menu" and self.focus_side == "right":
                    self.main_menu.move_up()

            elif event.key == pygame.K_DOWN:
                if self.current_screen_name == "main_menu":
                    self.main_menu.move_down()
                elif self.split_mode and self.right_screen_name == "main_menu" and self.focus_side == "right":
                    self.main_menu.move_down()

            elif event.key == pygame.K_RETURN:
                if self.split_mode:
                    if self.focus_side == "right" and self.right_screen_name == "main_menu":
                        self.select_main_menu_option()
                    else:
                        self.maximize_focused_panel()
                elif self.current_screen_name == "main_menu":
                    self.select_main_menu_option()
    
    def draw_screen_by_name(self, target_surface, screen_name, state, slot="fullscreen"):
        if screen_name == "main_menu":
            self.main_menu.draw(target_surface, state)
        elif screen_name == "gauge":
            self.screens[screen_name].draw(target_surface, state, slot=slot)
        else:
            self.screens[screen_name].draw(target_surface, state)

    def render_split(self, state):
        left_rect = pygame.Rect(0, 0, self.width // 2, self.height)
        right_rect = pygame.Rect(self.width // 2, 0, self.width // 2, self.height)

        self.screen.fill((15, 15, 18), left_rect)
        self.screen.fill((15, 15, 18), right_rect)

        left_surface = self.screen.subsurface(left_rect)
        right_surface = self.screen.subsurface(right_rect)

        # Left panel
        if self.left_screen_name == "gauge":
            self.screen.set_clip(left_rect)
            self.draw_screen_by_name(self.screen, self.left_screen_name, state, slot="left")
            self.screen.set_clip(None)
        else:
            self.draw_screen_by_name(left_surface, self.left_screen_name, state)

        # Right panel
        if self.right_screen_name == "gauge":
            self.screen.set_clip(right_rect)
            self.draw_screen_by_name(self.screen, self.right_screen_name, state, slot="right")
            self.screen.set_clip(None)
        else:
            self.draw_screen_by_name(right_surface, self.right_screen_name, state)

        # Divider
        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (self.width // 2, 0),
            (self.width // 2, self.height),
            2
        )

        # Focus border
        if self.focus_side == "left":
            pygame.draw.rect(self.screen, (255, 255, 255), left_rect, 3)
        else:
            pygame.draw.rect(self.screen, (255, 255, 255), right_rect, 3)

    def render(self, state):

        self.handle_events()

        self.screen.fill((15, 15, 18))

        if self.split_mode:
            self.render_split(state)
        else:
            self.draw_screen_by_name(self.screen, self.current_screen_name, state)

        pygame.display.flip()

    def close(self):
        pygame.quit()
