import game, block, pygame, sys

pygame.init()
screen=pygame.display.set_mode((400,500))

if "server" in sys.argv: server = game.Server((1,1), block.Theme("0", "0"))

game.Client("louis" + "server" if "server" in sys.argv else "", ('127.0.0.1', 1244))