import block

import pygame, time
pygame.init()

screen = pygame.display.set_mode((1200,700))
blocktypes = block.load_blocktypes("blocks.json")
themes = []

for themenum, themeprefix in enumerate(list("012")):
	themes.append(block.Theme(themeprefix, themeprefix))
	for blocktype in blocktypes.values():
		blocktype.build_images_for_theme(themes[-1])

blocks = []

for theme in themes:
	for blocktype in blocktypes.values():
		blocks.append(block.Block(blocktype, theme, 1))

print(blocks[0].dump())

while pygame.QUIT not in [e.type for e in pygame.event.get()]:
	for block in blocks: block.next_rot()
	screen.fill((0,0,0))

	for idx, block in enumerate(blocks):
		screen.blit(block.image, ((idx%7)*30, (idx//7)*30))

	pygame.display.flip()
	time.sleep(0.2)