import game, block, pygame, sys, os

SCREEN_SIZE=(800,500)
PPI=87

pygame.init()
screen=pygame.display.set_mode(SCREEN_SIZE)

isserver="server" in sys.argv

if isserver:
	server = game.Server(0.5, block.Theme("0", "0"))

identifier="server" if isserver else "client"

client=game.Client(identifier, SCREEN_SIZE, PPI, ('127.0.0.1', 1244))
client.connect()

if not isserver:
	client.view.view_offset[0]=9

i=0

run=True
while run:
	for event in pygame.event.get():
		if event.type==pygame.QUIT:
			print("quit")
			run=False
		if event.type==pygame.KEYDOWN and isserver:
			i+=1
			server[0][i]=0
	client.render(screen)
	pygame.display.flip()

os._exit(0)