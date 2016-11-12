import game, block, pygame

pygame.init()
screen=pygame.display.set_mode((700,700))

server = game.Server((1,1), block.Theme("0", "0"))

game.Client("louis", server.server_address)