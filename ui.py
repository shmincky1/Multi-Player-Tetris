import pygame

def color_replace(surface, find_color, replace_color):
    for x in range(surface.get_size()[0]):
        for y in range(surface.get_size()[1]):
            if surface.get_at([x, y]) == find_color:
                surface.set_at([x, y], replace_color)
    return surface

class Font:
	def __init__(self, basepath, size, characters, scale=4, padding=1):
		self.basepath=basepath
		self.size=size
		self.characters=characters
		self.imagecache={}
		self.scale=scale
		self.padding=padding
		self.scaledsize=int(self.size*self.scale)
		self.init_cache()

	def init_cache(self):
		self.cache={}
		for char in self.characters:
			img=pygame.image.load(self.basepath+"%s.png"%char).convert_alpha()
			img.set_colorkey((255,255,255))
			self.cache[char]=pygame.transform.scale(img, [self.scaledsize]*2)

	def render(self, text, color=(255,255,255)):
		surf=pygame.Surface((len(text)*(self.scaledsize+self.padding), self.scaledsize), pygame.SRCALPHA)
		# surf.fill((0,255,0,0))
		for idx, char in enumerate(text.upper()):
			if char not in self.characters:
				print("***ERROR*** %s not in font"%char)
			else:
				surf.blit(self.cache[char], (idx*(self.scaledsize+self.padding), 0))
		color_replace(surf, (0,0,0), color)
		return surf