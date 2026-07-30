import pygame

pygame.init()

screen = pygame.display.set_mode((1024, 600))
clock = pygame.time.Clock()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((20, 20, 20))
    pygame.display.flip()

    print(clock.get_fps())
    clock.tick(30)

pygame.quit()
