import game, block, pygame

pygame.init()
screen=pygame.display.set_mode((700,700))

client=game.Game((10,5), block.Theme("0","0"))
client[0][0]=0
client[0][1]=1
client[1][2]=2

while pygame.QUIT not in [e.type for e in pygame.event.get()]:
	screen.fill((0,0,0))
	screen.blit(client.draw_placed_blocks(), (0,0))
	pygame.display.flip()