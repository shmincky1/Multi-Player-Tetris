import game, block, pygame, sys, os

SCREEN_SIZE=(1366,768)
PPI=87

pygame.init()
pygame.key.set_repeat(200,100)
screen=pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)

isserver="server" in sys.argv[1]

if isserver:
	server = game.Server(0.4, block.Theme("0", "0"), tickrate=1)

identifier=sys.argv[1]

client=game.Client(identifier, SCREEN_SIZE, PPI, (sys.argv[2], 1244))
client.connect()

i=0

run=True
while run:
	for event in pygame.event.get():
		if event.type==pygame.QUIT:
			print("quit")
			run=False
		if event.type==pygame.KEYDOWN:
			if event.key==pygame.K_RETURN and isserver:
				server.start_game()
			elif event.key==pygame.K_q:
				run=False
			client.handle_event(event)
	client.render(screen)
	pygame.display.flip()

os._exit(0)