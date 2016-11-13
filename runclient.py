import game, block, pygame, sys, os, ui


PPI=int(os.environ.get("PPI", 87))

pygame.init()
pygame.key.set_repeat(200,75)

dispinfo=pygame.display.Info()
SCREEN_SIZE=[dispinfo.current_w, dispinfo.current_h]
flags=pygame.FULLSCREEN

INCHES_PER_BLOCK=0.6
TICKRATE=1
for item in sys.argv:
	if item.startswith("ipb="): INCHES_PER_BLOCK=float(item.replace("ipb=",""))
	if item.startswith("tir="): TICKRATE=float(item.replace("tir=",""))
	if item.startswith("res="):
		SCREEN_SIZE=[int(i) for i in item.replace("res=","").split(",")]
		print(SCREEN_SIZE)
		flags=0

screen=pygame.display.set_mode(SCREEN_SIZE, flags)

font = ui.Font("img/alphanum/", 7, "-1234567890QWERTYUIOPASDFGHJKLZXCVBNM")

ui.disp_loading(screen, font, "Screen initilized.")

isserver="server" in sys.argv[1]

if isserver:
	ui.disp_loading(screen, font, "Starting Server...")
	server = game.Server(INCHES_PER_BLOCK, block.Theme("0","0"), tickrate=TICKRATE)

identifier=sys.argv[1]

ui.disp_loading(screen, font, "Constructing UI")

lgfont = ui.Font("img/alphanum/", 7, "-1234567890QWERTYUIOPASDFGHJKLZXCVBNM", 3)

ui_bar_offset=ui.UIBar.calculate_size(SCREEN_SIZE[0])[1]

ui.disp_loading(screen, font, "Starting Client...")

SCREEN_SIZE[1]-=ui_bar_offset
client=game.Client(identifier, SCREEN_SIZE, PPI, (sys.argv[2], 1244))
client.themes=[block.Theme(str(n), str(n)) for n in range(10)]

client.font=lgfont

ui.disp_loading(screen, font, "Starting Client... --**Connecting to %s--"%sys.argv[2])
client.connect()

ui.disp_loading(screen, font, "Constructing UIBar...")

uibar=ui.UIBar(client, font, lgfont, "img/board-background.png", SCREEN_SIZE[0])

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

	client.render(screen, ui_bar_offset)
	
	uibar.update()
	screen.blit(uibar.surf, (0,0))
	pygame.display.flip()

os._exit(0)