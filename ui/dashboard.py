import os
import time
import subprocess
import pygame

from system.state_manager import (
    save_state,
    load_state,
)
from ui.screens.gauge_screen import GaugeScreen
from ui.screens.info_screen import InfoScreen
from ui.screens.gps_screen import GpsScreen
from ui.screens.music_screen import MusicScreen
from ui.screens.main_menu_screen import MainMenuScreen

from ui.widgets.status_bar import StatusBar
from ui.widgets.volume_overlay import VolumeOverlay

from music.player import MUSIC_ENDED

from system.map_projection import MapProjection

class Dashboard:
    def __init__(self, width=1024, height=600, fullscreen=True):
        # Under Xorg, a borderless 1024x600 window behaves like
        # fullscreen without SDL exclusively owning input.
        if fullscreen:
            os.environ[
                "SDL_VIDEO_WINDOW_POS"
            ] = "0,0"

        pygame.init()
        pygame.mouse.set_visible(False)

        flags = (
            pygame.NOFRAME
            if fullscreen
            else 0
        )

        self.display_flags = flags 

        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Corolla OS")

        self.width, self.height = self.screen.get_size()
        self.sidebar_gradient = self.create_sidebar_gradient()

        self.main_menu = MainMenuScreen(self.width, self.height)
        self.status_bar = StatusBar(self.height)
        self.volume_overlay = VolumeOverlay(self.height)

        self.debug_overlay_enabled = True
        self.debug_font = pygame.font.Font(
            "assets/fonts/roboto.ttf",
            int(self.height * 0.024)
        )
        self.debug_last_update = 0.0
        self.debug_fps_text = "FPS: 0.0"
        self.debug_surface = None


        self.sidebar_icon_size = int(self.height * 0.22)

        self.sidebar_icons = {}

        self.sidebar_scaled_icons = {}

        self.sidebar_visual_index = 0.0
        self.sidebar_anim_progress = 0.0
        self.sidebar_anim_speed = 0.8

        self.sidebar_icon_variant_cache = {}

        sidebar_icon_files = {
            "gauge": "assets/images/gauge.png",
            "system": "assets/images/system.png",
            "gps": "assets/images/gps.png",
            "music": "assets/images/music.png",
        }

        self.sidebar_gradient = self.create_sidebar_gradient()

        self.render_call_count = 0
        self.render_count_started = time.perf_counter()

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
        self.restore_saved_state()

        self.main_menu.set_music_screen(
            self.screens["music"]
        )
        self.restore_saved_state()

        self.current_screen_name = "main_menu"

        self.split_mode = False
        self.left_screen_name = "gauge"
        self.right_screen_name = "main_menu"
        self.focus_side = "right"

        self.sidebar_open = False
        self.sidebar_selected_index = 0
        self.sidebar_options = ["gauge", "system", "gps", "music"]

        self.left_hold_start = None
        self.left_hold_seconds = 3.0
        self.left_hold_consumed = False

        self.right_hold_start = None
        self.right_hold_seconds = 3.0
        self.right_hold_consumed = False

        self.shutdown_confirm_open = False
        self.shutdown_confirm_selected = 0

        # Global ENTER hold for safe system shutdown.
        self.power_hold_start = None
        self.power_hold_seconds = 5.0
        self.power_hold_consumed = False
        self.shutdown_in_progress = False

        self.map_projection = MapProjection()
        self.projection_mode = False

        self.running = True


    def start_map_projection(self):
        if self.map_projection.is_active():
            return True

        pygame.event.set_grab(False)
        pygame.mouse.set_visible(False)
        pygame.event.clear()

        # Keep Pygame, its display, and the music mixer alive.
        self.projection_mode = True

        started = self.map_projection.start()

        if not started:
            self.projection_mode = False

        return started   

    def restore_dashboard_display(self):
        if not pygame.display.get_init():
            pygame.display.init()

        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            self.display_flags,
        )

        pygame.display.set_caption(
            "Corolla OS"
        )

        pygame.event.set_grab(False)
        pygame.mouse.set_visible(False)
        pygame.event.clear()

    def service_map_projection(self):
        if not self.projection_mode:
            return False

        self.map_projection.update()

        if self.map_projection.is_active():
            return True

        self.map_projection.consume_return_request()

        self.projection_mode = False

        self.current_screen_name = "main_menu"
        self.split_mode = False
        self.sidebar_open = False

        pygame.event.clear()
        pygame.mouse.set_visible(False)

        return False



    def get_music_screen(self):
        return self.screens.get("music")

    def is_music_drawer_open(self):
        music_screen = self.get_music_screen()

        return (
            self.current_screen_name == "music"
            and not self.split_mode
            and music_screen is not None
            and getattr(music_screen, "drawer_open", False)
        )

    def can_open_music_drawer(self):
        music_screen = self.get_music_screen()

        return (
            self.current_screen_name == "music"
            and not self.split_mode
            and music_screen is not None
            and music_screen.mode == "now_playing"
            and not music_screen.drawer_open
        )

    def can_open_sidebar(self):
        return (
            self.current_screen_name != "main_menu"
            and not self.split_mode
            and not self.sidebar_open
            and not self.is_music_drawer_open()
        ) 

    def select_main_menu_option(self):
        selected = self.main_menu.get_selected_screen()

        if self.split_mode:
            self.right_screen_name = selected
            self.focus_side = "right"
        else:
            self.current_screen_name = selected

            if selected == "gps":
                self.start_map_projection()


    def exit_split_mode(self):
        self.current_screen_name = self.left_screen_name
        self.split_mode = False

    def maximize_focused_panel(self):
        if self.focus_side == "left":
            selected = self.left_screen_name
        else:
            selected = self.right_screen_name

        self.current_screen_name = selected
        self.split_mode = False

        if selected == "gps":
            self.start_map_projection()


    def open_sidebar_split(self):
        selected = self.sidebar_options[self.sidebar_selected_index]

        self.left_screen_name = self.current_screen_name
        self.right_screen_name = selected
        self.focus_side = "right"

        self.split_mode = True
        self.sidebar_open = False

    def create_sidebar_gradient(self):
        gradient_w = int(self.width * 0.35)

        # No SRCALPHA: regular RGB surface.
        gradient = pygame.Surface(
            (gradient_w, self.height)
        ).convert()

        for x in range(gradient_w):
            progress = x / max(1, gradient_w - 1)

            # 255 means unchanged.
            # Lower values darken the underlying pixels.
            multiplier = int(
                255 - 185 * (progress ** 1.2)
            )

            pygame.draw.line(
                gradient,
                (multiplier, multiplier, multiplier),
                (x, 0),
                (x, self.height)
            )

        return gradient 
    
    def handle_left_tap(self):
        music_screen = self.get_music_screen()

        if (
            self.current_screen_name == "music"
            and not self.split_mode
            and music_screen is not None
            and music_screen.mode == "now_playing"
        ):
            music_screen.handle_key(pygame.K_LEFT)

    def handle_right_tap(self):
        if (
            self.current_screen_name == "music"
            and not self.split_mode
            and hasattr(self.screens["music"], "handle_key")
        ):
            self.screens["music"].handle_key(pygame.K_RIGHT)

    def handle_enter_tap(self):
        # Sidebar owns ENTER while open.
        if self.sidebar_open:
            self.handle_sidebar_key(
                pygame.K_RETURN
            )
            return

        music_screen = self.get_music_screen()

        # Music drawer owns ENTER while open.
        if (
            music_screen is not None
            and music_screen.drawer_open
        ):
            music_screen.handle_key(
                pygame.K_RETURN
            )
            return

        # Give the active app first chance to use ENTER.
        if self.route_to_current_screen(
            pygame.K_RETURN
        ):
            return

        # Dashboard-level ENTER behavior.
        if self.split_mode:
            if (
                self.focus_side == "right"
                and self.right_screen_name
                == "main_menu"
            ):
                self.select_main_menu_option()
            else:
                self.maximize_focused_panel()

        elif self.current_screen_name == "main_menu":
            self.select_main_menu_option()

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
        if key == pygame.K_RETURN:
            if self.power_hold_start is not None:
                self.power_hold_start = None

                if not self.power_hold_consumed:
                    self.handle_enter_tap()

            self.power_hold_consumed = False
            return

        if key == pygame.K_RIGHT:
            if self.right_hold_consumed:
                self.right_hold_consumed = False
                self.right_hold_start = None
                return

            if self.right_hold_start is not None:
                held_time = time.time() - self.right_hold_start
                self.right_hold_start = None

                if held_time < self.right_hold_seconds:
                    self.handle_right_tap()

            return

        if key == pygame.K_LEFT:
            if self.left_hold_consumed:
                self.left_hold_consumed = False
                self.left_hold_start = None
                return

            if self.left_hold_start is not None:
                held_time = time.time() - self.left_hold_start
                self.left_hold_start = None

                if held_time < self.left_hold_seconds:
                    self.handle_left_tap() 


    def handle_keydown(self, key):
        if self.shutdown_confirm_open:
            self.handle_shutdown_confirm_key(key)
            return

        # ENTER is special:
        # tap = normal ENTER action
        # 5-second hold = safe shutdown
        if key == pygame.K_RETURN:
            if self.power_hold_start is None:
                self.power_hold_start = time.time()
                self.power_hold_consumed = False

            return

        if self.sidebar_open:
            self.handle_sidebar_key(key)
            return

        music_screen = self.get_music_screen()

        if music_screen and music_screen.drawer_open:
            # The Music drawer owns all navigation while open.
            self.left_hold_start = None
            self.right_hold_start = None

            music_screen.handle_key(key)
            return 

        if music_screen and key == pygame.K_w:
            music_screen.player.increase_volume()
            self.volume_overlay.show()
            return

        if music_screen and key == pygame.K_s:
            music_screen.player.decrease_volume()
            self.volume_overlay.show()
            return

        if key == pygame.K_F3:
            self.debug_overlay_enabled = not self.debug_overlay_enabled
            return
        

        # RIGHT is special because tap = app action, hold = sidebar.
        # So we do not route RIGHT on keydown.
        is_music_left_hold = (
            key == pygame.K_LEFT
            and self.can_open_music_drawer()
        )

        if key != pygame.K_RIGHT and not is_music_left_hold:
            if self.route_to_current_screen(key):
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
            if self.can_open_music_drawer():
                if self.left_hold_start is None:
                    self.left_hold_start = time.time()
                    self.left_hold_consumed = False

            elif self.current_screen_name == "main_menu" and not self.split_mode:
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

       
           

    def handle_options_key(self, key):
        if key == pygame.K_ESCAPE:
            self.options_open = False
            return True

        if key == pygame.K_RETURN:
            selected = self.options_items[self.options_selected_index]

            if selected == "close":
                self.options_open = False
            else:
                self.options_open = False

            return True

        if key == pygame.K_UP:
            self.options_selected_index = (
                self.options_selected_index - 1
            ) % len(self.options_items)
            return True

        if key == pygame.K_DOWN:
            self.options_selected_index = (
                self.options_selected_index + 1
            ) % len(self.options_items)
            return True

        if key == pygame.K_LEFT:
            self.change_selected_option(-1)
            return True

        if key == pygame.K_RIGHT:
            self.change_selected_option(1)
            return True

        return False


    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == MUSIC_ENDED:
                music_screen = self.get_music_screen()

                if music_screen and hasattr(music_screen, "handle_song_finished"):
                    music_screen.handle_song_finished()

                continue

            elif event.type == pygame.KEYUP:
                self.handle_keyup(event.key)

            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)


    def handle_shutdown_confirm_key(self, key):
        if key == pygame.K_ESCAPE:
            self.shutdown_confirm_open = False
            return True

        if key == pygame.K_LEFT:
            self.shutdown_confirm_selected = 0
            return True

        if key == pygame.K_RIGHT:
            self.shutdown_confirm_selected = 1
            return True

        if key == pygame.K_RETURN:
            if self.shutdown_confirm_selected == 0:
                self.shutdown_confirm_open = False
            else:
                self.shutdown_confirm_open = False
                self.shutdown_corolla_os()

            return True

        return True


    def update_long_press(self):
        keys = pygame.key.get_pressed()
        # ---------------------------------------------------------
        # ENTER hold: safe Corolla OS shutdown
        # ---------------------------------------------------------
        if not keys[pygame.K_RETURN]:
            self.power_hold_start = None

        elif (
            self.power_hold_start is not None
            and not self.power_hold_consumed
            and not self.shutdown_in_progress
        ):
            held_time = (
                time.time()
                - self.power_hold_start
            )

            if held_time >= self.power_hold_seconds:
                self.power_hold_consumed = True

                # Cancel other long-press actions.
                self.left_hold_start = None
                self.right_hold_start = None

                self.shutdown_confirm_open = True
                self.shutdown_confirm_selected = 1
                self.power_hold_start = None
        # ---------------------------------------------------------
        # LEFT hold: open the Music options drawer
        # ---------------------------------------------------------
        if not keys[pygame.K_LEFT]:
            self.left_hold_start = None

        elif self.can_open_music_drawer():
            if self.left_hold_start is None:
                self.left_hold_start = time.time()
                self.left_hold_consumed = False

            held_time = time.time() - self.left_hold_start

            if held_time >= self.left_hold_seconds:
                music_screen = self.get_music_screen()

                if music_screen is not None:
                    music_screen.drawer_open = True
                    music_screen.drawer_icon_index = 0

                self.left_hold_consumed = True
                self.left_hold_start = None

                # Cancel any simultaneous right-sidebar attempt.
                self.right_hold_start = None
                self.right_hold_consumed = False

        else:
            self.left_hold_start = None

        # ---------------------------------------------------------
        # RIGHT hold: open the Dashboard split-screen sidebar
        # ---------------------------------------------------------
        if not keys[pygame.K_RIGHT]:
            self.right_hold_start = None
            return

        if not self.can_open_sidebar():
            self.right_hold_start = None
            self.right_hold_consumed = False
            return

        if self.right_hold_start is None:
            self.right_hold_start = time.time()
            self.right_hold_consumed = False

        held_time = time.time() - self.right_hold_start

        if held_time >= self.right_hold_seconds:
            self.sidebar_open = True
            self.sidebar_anim_progress = 0.0
            self.right_hold_consumed = True
            self.right_hold_start = None 

    def restore_saved_state(self):
        state = load_state()

        if not isinstance(
            state,
            dict
        ):
            return

        music_state = state.get(
            "music",
            {}
        )

        music_screen = (
            self.get_music_screen()
        )

        if music_screen is not None:
            music_screen.restore_save_state(
                music_state
            )


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

        if self.map_projection.consume_return_request():
            self.restore_dashboard_display()

            self.current_screen_name = "main_menu"
            self.split_mode = False
            self.sidebar_open = False

        self.update_long_press()

        if self.sidebar_open:
            self.sidebar_anim_progress = min(
                1.0,
                self.sidebar_anim_progress + self.sidebar_anim_speed
            )
            self.update_sidebar_animation()
        screen = self.screens.get(self.current_screen_name)

        if screen and hasattr(screen, "update"):
            screen.update()



    def draw_screen_by_name(
        self,
        target_surface,
        screen_name,
        telemetry_state,
        navigation_state=None,
        slot="fullscreen"
    ):
        if screen_name == "main_menu":
            self.main_menu.draw(
                target_surface,
                telemetry_state
            )

        elif screen_name == "gauge":
            self.screens[screen_name].draw(
                target_surface,
                telemetry_state,
                slot=slot
            )

        elif screen_name == "gps":
            self.screens[screen_name].draw(
                target_surface,
                navigation_state
            )

        else:
            self.screens[screen_name].draw(
                target_surface,
                telemetry_state
            ) 


    def render_active_screen(
        self,
        telemetry_state,
        navigation_state=None
    ):
        if self.split_mode:
            self.render_split(
                telemetry_state,
                navigation_state
            )
        else:
            self.draw_screen_by_name(
                self.screen,
                self.current_screen_name,
                telemetry_state,
                navigation_state
            )

    def render_shutdown_confirm(self):
        if not self.shutdown_confirm_open:
            return

        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))

        self.screen.blit(
            overlay,
            (0, 0)
        )

        popup_w = int(self.width * 0.52)
        popup_h = int(self.height * 0.30)

        popup_rect = pygame.Rect(
            0,
            0,
            popup_w,
            popup_h
        )

        popup_rect.center = (
            self.width // 2,
            self.height // 2
        )

        pygame.draw.rect(
            self.screen,
            (24, 24, 30),
            popup_rect,
            border_radius=18
        )

        pygame.draw.rect(
            self.screen,
            (85, 85, 95),
            popup_rect,
            2,
            border_radius=18
        )

        title_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(self.height * 0.045)
        )

        button_font = pygame.font.Font(
            "assets/fonts/Manrope-Bold.ttf",
            int(self.height * 0.030)
        )

        title_surface = title_font.render(
            "Shut down Corolla OS?",
            True,
            (245, 245, 250)
        )

        self.screen.blit(
            title_surface,
            title_surface.get_rect(
                center=(
                    popup_rect.centerx,
                    popup_rect.top + int(popup_h * 0.32)
                )
            )
        )

        cancel_rect = pygame.Rect(
            0,
            0,
            int(popup_w * 0.28),
            int(popup_h * 0.22)
        )

        shutdown_rect = cancel_rect.copy()

        cancel_rect.center = (
            popup_rect.centerx - int(popup_w * 0.18),
            popup_rect.top + int(popup_h * 0.70)
        )

        shutdown_rect.center = (
            popup_rect.centerx + int(popup_w * 0.18),
            popup_rect.top + int(popup_h * 0.70)
        )

        buttons = [
            (
                cancel_rect,
                "CANCEL"
            ),
            (
                shutdown_rect,
                "SHUT DOWN"
            )
        ]

        for index, (rect, label) in enumerate(buttons):
            selected = (
                index
                == self.shutdown_confirm_selected
            )

            pygame.draw.rect(
                self.screen,
                (52, 52, 62)
                if selected
                else (32, 32, 38),
                rect,
                border_radius=10
            )

            pygame.draw.rect(
                self.screen,
                (235, 235, 245)
                if selected
                else (80, 80, 90),
                rect,
                2 if selected else 1,
                border_radius=10
            )

            text = button_font.render(
                label,
                True,
                (250, 250, 250)
                if selected
                else (160, 160, 170)
            )

            self.screen.blit(
                text,
                text.get_rect(
                    center=rect.center
                )
            )

    def render_split(
        self,
        telemetry_state,
        navigation_state=None
    ):
        left_rect = pygame.Rect(
            0,
            0,
            self.width // 2,
            self.height
        )

        right_rect = pygame.Rect(
            self.width // 2,
            0,
            self.width // 2,
            self.height
        )

        self.screen.fill(
            (15, 15, 18),
            left_rect
        )

        self.screen.fill(
            (15, 15, 18),
            right_rect
        )

        left_surface = self.screen.subsurface(
            left_rect
        )

        right_surface = self.screen.subsurface(
            right_rect
        )

        if self.left_screen_name == "gauge":
            self.screen.set_clip(
                left_rect
            )

            self.draw_screen_by_name(
                self.screen,
                self.left_screen_name,
                telemetry_state,
                navigation_state,
                slot="left"
            )

            self.screen.set_clip(
                None
            )
        else:
            self.draw_screen_by_name(
                left_surface,
                self.left_screen_name,
                telemetry_state,
                navigation_state
            )

        if self.right_screen_name == "gauge":
            self.screen.set_clip(
                right_rect
            )

            self.draw_screen_by_name(
                self.screen,
                self.right_screen_name,
                telemetry_state,
                navigation_state,
                slot="right"
            )

            self.screen.set_clip(
                None
            )
        else:
            self.draw_screen_by_name(
                right_surface,
                self.right_screen_name,
                telemetry_state,
                navigation_state
            )

        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (
                self.width // 2,
                0
            ),
            (
                self.width // 2,
                self.height
            ),
            2
        )

        if self.focus_side == "left":
            pygame.draw.rect(
                self.screen,
                (255, 255, 255),
                left_rect,
                3
            )
        else:
            pygame.draw.rect(
                self.screen,
                (255, 255, 255),
                right_rect,
                3
            )

    def render_sidebar(self):
        sidebar_w = int(self.width * 0.18)
        x = self.width - sidebar_w

        t = self.sidebar_anim_progress
        ease = 1 - (1 - t) * (1 - t)
        slide_offset = int(sidebar_w * (1.0 - ease))
        x += slide_offset

        gradient_x = self.width - self.sidebar_gradient.get_width()
        self.screen.blit(
            self.sidebar_gradient,
            (gradient_x, 0),
            special_flags=pygame.BLEND_RGB_MULT
        )


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

            icon_size = int(
                self.sidebar_icon_size * scale
            )

            icon = self.get_sidebar_icon_variant(
                screen_name,
                icon_size,
                alpha
            )

            icon_rect = icon.get_rect(
                center=(center_x, y)
            )

            self.screen.blit(icon, icon_rect) 


    def render_long_press_progress(self):
        bar_w = self.width * 0.18
        bar_h = max(4, int(self.height * 0.012))
        y = self.height * 0.88

        background_color = (60, 60, 70)
        fill_color = (235, 235, 245)

        # LEFT hold: Music drawer.
        if self.left_hold_start is not None:
            left_progress = min(
                1.0,
                (time.time() - self.left_hold_start)
                / self.left_hold_seconds
            )

            left_x = self.width * 0.04
            left_fill_w = bar_w * left_progress

            pygame.draw.rect(
                self.screen,
                background_color,
                pygame.Rect(
                    left_x,
                    y,
                    bar_w,
                    bar_h
                )
            )

            pygame.draw.rect(
                self.screen,
                fill_color,
                pygame.Rect(
                    left_x,
                    y,
                    left_fill_w,
                    bar_h
                )
            )

        # RIGHT hold: Split-screen sidebar.
        if self.right_hold_start is not None:
            right_progress = min(
                1.0,
                (time.time() - self.right_hold_start)
                / self.right_hold_seconds
            )

            right_x = (
                self.width
                - bar_w
                - self.width * 0.04
            )

            right_fill_w = bar_w * right_progress

            pygame.draw.rect(
                self.screen,
                background_color,
                pygame.Rect(
                    right_x,
                    y,
                    bar_w,
                    bar_h
                )
            )

            pygame.draw.rect(
                self.screen,
                fill_color,
                pygame.Rect(
                    right_x,
                    y,
                    right_fill_w,
                    bar_h
                )
            )
        
        

    def render_debug_overlay(self):
        if not self.debug_overlay_enabled:
            return

        now = time.perf_counter()

        if (
            self.debug_surface is None
            or now - self.debug_last_update >= 0.5
        ):
            fps = self.clock.get_fps()
            frame_ms = 1000.0 / fps if fps > 0 else 0.0

            self.debug_fps_text = (
                "FPS: {:.1f}   FRAME: {:.1f} ms   SCREEN: {}"
            ).format(
                fps,
                frame_ms,
                self.current_screen_name
            )

            self.debug_surface = self.debug_font.render(
                self.debug_fps_text,
                True,
                (255, 255, 255)
            )

            self.debug_last_update = now

        padding = 8

        background = pygame.Rect(
            8,
            self.height - self.debug_surface.get_height() - padding * 2 - 8,
            self.debug_surface.get_width() + padding * 2,
            self.debug_surface.get_height() + padding * 2
        )

        pygame.draw.rect(self.screen, (0, 0, 0), background)

        self.screen.blit(
            self.debug_surface,
            (
                background.left + padding,
                background.top + padding
            )
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

        self.render_shutdown_confirm()
        self.render_debug_overlay()


    def render(
        self,
        telemetry_state,
        navigation_state=None
    ):
        projection_active = (
            self.service_map_projection()
        )

        # Keep processing music completion, keyboard, and system
        # events even while scrcpy is above Corolla OS.
        self.handle_events()

        # A key event may have started or stopped projection.
        projection_active = (
            self.service_map_projection()
        )

        if projection_active:
            # Pygame and pygame.mixer remain alive underneath
            # scrcpy, but we avoid wasting resources rendering
            # a dashboard that is presently covered.
            self.clock.tick(20)
            return

        self.screen.fill(
            (15, 15, 18)
        )

        self.update()

        self.render_active_screen(
            telemetry_state,
            navigation_state
        )

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

    def get_sidebar_icon_variant(
        self,
        screen_name,
        icon_size,
        alpha
    ):
        # Quantize values so animation does not create unlimited cache entries.
        icon_size = max(1, int(round(icon_size / 4.0) * 4))
        alpha = max(0, min(255, int(round(alpha / 16.0) * 16)))

        key = (
            screen_name,
            icon_size,
            alpha
        )

        if key not in self.sidebar_icon_variant_cache:
            icon = self.get_sidebar_icon(
                screen_name,
                icon_size
            ).copy()

            icon.set_alpha(alpha)

            self.sidebar_icon_variant_cache[key] = icon

        return self.sidebar_icon_variant_cache[key] 


    def route_to_current_screen(self, key):
        screen = self.screens.get(self.current_screen_name)

        if screen and hasattr(screen, "handle_key"):
            return screen.handle_key(key)

        return False

    def shutdown_corolla_os(self):
        if self.shutdown_in_progress:
            return

        self.shutdown_in_progress = True
        
        self.map_projection.stop(
            request_return=False
        )

        music_screen = self.get_music_screen()

        state = {
            "current_screen": self.current_screen_name,
            "split_mode": self.split_mode,
            "music": (
                music_screen.get_save_state()
                if music_screen is not None
                else {}
            ),
        }

        try:
            save_state(state)

            subprocess.run(
                ["sync"],
                check=False
            )

            pygame.event.clear()

            subprocess.Popen(
                [
                    "sudo",
                    "shutdown",
                    "-h",
                    "now"
                ]
            )

        except Exception as error:
            print(
                "Shutdown error: {}".format(
                    error
                )
            )

            self.shutdown_in_progress = False
            self.power_hold_consumed = False

    
    def close(self):
        self.map_projection.close()
        pygame.quit()
