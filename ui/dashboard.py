import time
import pygame

from ui.screens.gauge_screen import GaugeScreen
from ui.screens.info_screen import InfoScreen
from ui.screens.gps_screen import GpsScreen
from ui.screens.music_screen import MusicScreen
from ui.screens.main_menu_screen import MainMenuScreen

from ui.widgets.status_bar import StatusBar
from ui.widgets.volume_overlay import VolumeOverlay


class Dashboard:
    def __init__(self, width=1024, height=600, fullscreen=True):
        pygame.init()

        flags = pygame.FULLSCREEN if fullscreen else 0

        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Corolla OS")

        self.width, self.height = self.screen.get_size()

        self.main_menu = MainMenuScreen(self.width, self.height)
        self.status_bar = StatusBar(self.height)
        self.volume_overlay = VolumeOverlay(self.height)


        self.sidebar_icon_size = int(self.height * 0.22)

        self.sidebar_icons = {}

        self.sidebar_scaled_icons = {}

        self.sidebar_visual_index = 0.0
        self.sidebar_anim_progress = 0.0
        self.sidebar_anim_speed = 0.8

        sidebar_icon_files = {
            "gauge": "assets/images/gauge.png",
            "system": "assets/images/system.png",
            "gps": "assets/images/gps.png",
            "music": "assets/images/music.png",
        }

        for name, filename in sidebar_icon_files.items():
            image = pygame.image.load(filename).convert_alpha()
            image = pygame.transform.smoothscale(
                image,
                (self.sidebar_icon_size, self.sidebar_icon_size)
            )
            self.sidebar_icons[name] = image

        self.screens = {
            "gauge": GaugeScreen(self.width, self.height),
            "system": InfoScreen(self.width, self.height),
            "gps": GpsScreen(self.width, self.height),
            "music": MusicScreen(self.width, self.height),
        }

        self.current_screen_name = "main_menu"

        self.split_mode = False
        self.left_screen_name = "gauge"
        self.right_screen_name = "main_menu"
        self.focus_side = "right"

        self.sidebar_open = False
        self.sidebar_selected_index = 0
        self.sidebar_options = ["gauge", "system", "gps", "music"]

        self.right_hold_start = None
        self.right_hold_seconds = 3.0
        self.right_hold_consumed = False

        self.running = True

    def get_music_screen(self):
        return self.screens.get("music")

    def can_open_sidebar(self):
        return (
            self.current_screen_name != "main_menu"
            and not self.split_mode
            and not self.sidebar_open
        )

    def select_main_menu_option(self):
        selected = self.main_menu.get_selected_screen()

        if self.split_mode:
            self.right_screen_name = selected
            self.focus_side = "right"
        else:
            self.current_screen_name = selected

    def exit_split_mode(self):
        self.current_screen_name = self.left_screen_name
        self.split_mode = False

    def maximize_focused_panel(self):
        if self.focus_side == "left":
            self.current_screen_name = self.left_screen_name
        else:
            self.current_screen_name = self.right_screen_name

        self.split_mode = False

    def open_sidebar_split(self):
        selected = self.sidebar_options[self.sidebar_selected_index]

        self.left_screen_name = self.current_screen_name
        self.right_screen_name = selected
        self.focus_side = "right"

        self.split_mode = True
        self.sidebar_open = False

    def handle_right_tap(self):
        if (
            self.current_screen_name == "music"
            and not self.split_mode
            and hasattr(self.screens["music"], "handle_key")
        ):
            self.screens["music"].handle_key(pygame.K_RIGHT)

    def handle_sidebar_key(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_LEFT:
            self.sidebar_open = False
            return True

        if key == pygame.K_UP:
            self.sidebar_selected_index = (
                self.sidebar_selected_index - 1
            ) % len(self.sidebar_options)
            return True

        if key == pygame.K_DOWN:
            self.sidebar_selected_index = (
                self.sidebar_selected_index + 1
            ) % len(self.sidebar_options)
            return True

        if key == pygame.K_RETURN:
            self.open_sidebar_split()
            return True

        return False

    def handle_keyup(self, key):
        if key != pygame.K_RIGHT:
            return

        if self.right_hold_consumed:
            self.right_hold_consumed = False
            self.right_hold_start = None
            return

        if self.right_hold_start is not None:
            held_time = time.time() - self.right_hold_start
            self.right_hold_start = None

            if held_time < self.right_hold_seconds:
                self.handle_right_tap()

    def handle_keydown(self, key):
        if self.sidebar_open:
            self.handle_sidebar_key(key)
            return

        music_screen = self.get_music_screen()

        if music_screen and key == pygame.K_w:
            music_screen.player.increase_volume()
            self.volume_overlay.show()
            return

        if music_screen and key == pygame.K_s:
            music_screen.player.decrease_volume()
            self.volume_overlay.show()
            return

        if (
            self.current_screen_name == "music"
            and not self.split_mode
            and hasattr(self.screens["music"], "handle_key")
        ):
            if key in (pygame.K_SPACE, pygame.K_LEFT):
                self.screens["music"].handle_key(key)
                return

        if key == pygame.K_ESCAPE:
            if self.split_mode:
                self.exit_split_mode()
            elif self.current_screen_name == "main_menu":
                self.running = False
            else:
                self.current_screen_name = "main_menu"

        elif key == pygame.K_RIGHT:
            if self.current_screen_name == "main_menu" and not self.split_mode:
                self.main_menu.move_right()

            elif self.split_mode:
                self.focus_side = "right"

            elif self.can_open_sidebar():
                if self.right_hold_start is None:
                    self.right_hold_start = time.time()
                    self.right_hold_consumed = False

        elif key == pygame.K_LEFT:
            if self.current_screen_name == "main_menu" and not self.split_mode:
                self.main_menu.move_left()
            elif self.split_mode:
                self.focus_side = "left"

        elif key == pygame.K_UP:
            if self.current_screen_name == "main_menu":
                self.main_menu.move_up()
            elif (
                self.split_mode
                and self.right_screen_name == "main_menu"
                and self.focus_side == "right"
            ):
                self.main_menu.move_up()

        elif key == pygame.K_DOWN:
            if self.current_screen_name == "main_menu":
                self.main_menu.move_down()
            elif (
                self.split_mode
                and self.right_screen_name == "main_menu"
                and self.focus_side == "right"
            ):
                self.main_menu.move_down()

        elif key == pygame.K_RETURN:
            if self.split_mode:
                if (
                    self.focus_side == "right"
                    and self.right_screen_name == "main_menu"
                ):
                    self.select_main_menu_option()
                else:
                    self.maximize_focused_panel()
            elif self.current_screen_name == "main_menu":
                self.select_main_menu_option()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYUP:
                self.handle_keyup(event.key)

            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)

    def update_long_press(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_RIGHT] and self.can_open_sidebar():
            if self.right_hold_start is None:
                self.right_hold_start = time.time()
                self.right_hold_consumed = False

            held_time = time.time() - self.right_hold_start

            if held_time >= self.right_hold_seconds:
                self.sidebar_open = True
                self.sidebar_anim_progress = 0.0
                self.right_hold_consumed = True
                self.right_hold_start = None
        else:
            if not keys[pygame.K_RIGHT]:
                self.right_hold_start = None

    def update_sidebar_animation(self):
        target = float(self.sidebar_selected_index)
        total = len(self.sidebar_options)

        diff = target - self.sidebar_visual_index

        if diff > total / 2:
            diff -= total
        elif diff < -total / 2:
            diff += total

        self.sidebar_visual_index += diff * self.sidebar_anim_speed

        if self.sidebar_visual_index < 0:
            self.sidebar_visual_index += total
        elif self.sidebar_visual_index >= total:
            self.sidebar_visual_index -= total

    def update(self):
        self.update_long_press()

        if self.sidebar_open:
            self.sidebar_anim_progress = min(
                1.0,
                self.sidebar_anim_progress + self.sidebar_anim_speed
            )
            self.update_sidebar_animation()


    def draw_screen_by_name(self, target_surface, screen_name, state, slot="fullscreen"):
        if screen_name == "main_menu":
            self.main_menu.draw(target_surface, state)
        elif screen_name == "gauge":
            self.screens[screen_name].draw(target_surface, state, slot=slot)
        else:
            self.screens[screen_name].draw(target_surface, state)

    def render_active_screen(self, state):
        if self.split_mode:
            self.render_split(state)
        else:
            self.draw_screen_by_name(
                self.screen,
                self.current_screen_name,
                state
            )

    def render_split(self, state):
        left_rect = pygame.Rect(0, 0, self.width // 2, self.height)
        right_rect = pygame.Rect(self.width // 2, 0, self.width // 2, self.height)

        self.screen.fill((15, 15, 18), left_rect)
        self.screen.fill((15, 15, 18), right_rect)

        left_surface = self.screen.subsurface(left_rect)
        right_surface = self.screen.subsurface(right_rect)

        if self.left_screen_name == "gauge":
            self.screen.set_clip(left_rect)
            self.draw_screen_by_name(
                self.screen,
                self.left_screen_name,
                state,
                slot="left"
            )
            self.screen.set_clip(None)
        else:
            self.draw_screen_by_name(left_surface, self.left_screen_name, state)

        if self.right_screen_name == "gauge":
            self.screen.set_clip(right_rect)
            self.draw_screen_by_name(
                self.screen,
                self.right_screen_name,
                state,
                slot="right"
            )
            self.screen.set_clip(None)
        else:
            self.draw_screen_by_name(right_surface, self.right_screen_name, state)

        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (self.width // 2, 0),
            (self.width // 2, self.height),
            2
        )

        if self.focus_side == "left":
            pygame.draw.rect(self.screen, (255, 255, 255), left_rect, 3)
        else:
            pygame.draw.rect(self.screen, (255, 255, 255), right_rect, 3)

    def render_sidebar(self):
        sidebar_w = int(self.width * 0.18)
        x = self.width - sidebar_w

        t = self.sidebar_anim_progress
        ease = 1 - (1 - t) * (1 - t)
        slide_offset = int(sidebar_w * (1.0 - ease))
        x += slide_offset

        gradient_w = int(self.width * 0.35)
        gradient_x = self.width - gradient_w

        gradient = pygame.Surface((gradient_w, self.height), pygame.SRCALPHA)

        for i in range(gradient_w):
            t = i / gradient_w
            alpha = int(185 * (t ** 1.2))

            pygame.draw.line(
                gradient,
                (0, 0, 0, alpha),
                (i, 0),
                (i, self.height)
            )

        self.screen.blit(gradient, (gradient_x, 0))

        center_x = x + sidebar_w * 0.5
        center_y = self.height * 0.50
        gap = self.height * 0.22
        total = len(self.sidebar_options)

        for i, screen_name in enumerate(self.sidebar_options):
            distance = i - self.sidebar_visual_index

            if distance > total / 2:
                distance -= total
            elif distance < -total / 2:
                distance += total

            if abs(distance) > 1.25:
                continue

            y = center_y + distance * gap

            closeness = max(0.0, 1.0 - abs(distance))

            scale = 0.70 + 0.30 * closeness
            alpha = int(120 + 135 * closeness)

            base_icon = self.sidebar_icons[screen_name]
            icon_size = int(self.sidebar_icon_size * scale)

            icon = self.get_sidebar_icon(screen_name, icon_size).copy()
            icon.set_alpha(alpha)

            icon_rect = icon.get_rect(center=(center_x, y))

            self.screen.blit(icon, icon_rect) 


    def render_long_press_progress(self):
        if self.right_hold_start is None:
            return

        progress = min(
            1.0,
            (time.time() - self.right_hold_start) / self.right_hold_seconds
        )

        bar_w = self.width * 0.18
        bar_h = self.height * 0.012
        x = self.width - bar_w - self.width * 0.04
        y = self.height * 0.88

        fill_w = bar_w * progress

        pygame.draw.rect(
            self.screen,
            (60, 60, 70),
            pygame.Rect(x, y, bar_w, bar_h)
        )
        pygame.draw.rect(
            self.screen,
            (235, 235, 245),
            pygame.Rect(x, y, fill_w, bar_h)
        )

    def render_overlays(self):
        if self.sidebar_open:
            self.render_sidebar()

        self.render_long_press_progress()
        self.status_bar.draw(self.screen)

        music_screen = self.get_music_screen()
        if music_screen:
            self.volume_overlay.draw(
                self.screen,
                music_screen.player.get_volume_percent()
            )

    def render(self, state):
        self.handle_events()
        self.update()

        self.screen.fill((15, 15, 18))

        self.render_active_screen(state)
        self.render_overlays()


        pygame.display.flip()
        self.clock.tick(30)

    def get_sidebar_icon(self, screen_name, icon_size):
        key = (screen_name, icon_size)

        if key not in self.sidebar_scaled_icons:
            self.sidebar_scaled_icons[key] = pygame.transform.smoothscale(
                self.sidebar_icons[screen_name],
                (icon_size, icon_size)
            )

        return self.sidebar_scaled_icons[key]

    def close(self):
        pygame.quit()
