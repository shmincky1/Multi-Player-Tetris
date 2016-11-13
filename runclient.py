import game, block, pygame, sys, os

SCREEN_SIZE=(400,600)
PPI=87

pygame.init()
pygame.key.set_repeat(200,100)
screen=pygame.display.set_mode(SCREEN_SIZE)

isserver="server" in sys.argv

if isserver:
	server = game.Server(0.4, block.Theme("0", "0"), tickrate=1)

identifier="server" if isserver else "client"

client=game.Client(identifier, SCREEN_SIZE, PPI, ('127.0.0.1', 1244))
client.connect()

i=0

run=True
while run:
	for event in pygame.event.get():
		if event.type==pygame.QUIT:
			print("quit")
			run=False
		if event.type==pygame.KEYDOWN and isserver:
			if event.key==pygame.K_RETURN:
				server.start_game()
			client.handle_event(event)
	client.render(screen)
	pygame.display.flip()

os._exit(0)