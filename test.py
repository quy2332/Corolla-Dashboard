import pygame

pygame.init()

screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("Corolla OS")

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((20, 20, 20))

    pygame.display.flip()

pygame.quit()
