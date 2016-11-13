import pygame, block

def calc_scale(ix,iy,bx,by):
	if ix > iy:
		# fit to width
		scale_factor = bx/float(ix)
		sy = scale_factor * iy
		if sy > by:
			scale_factor = by/float(iy)
			sx = scale_factor * ix
			sy = by
		else:
			sx = bx
	else:
		# fit to height
		scale_factor = by/float(iy)
		sx = scale_factor * ix
		if sx > bx:
			scale_factor = bx/float(ix)
			sx = bx
			sy = scale_factor * iy
		else:
			sy = by
	return int(sx),int(sy)

def aspect_scale(img,sz):
	""" Scales 'img' to fit into box bx/by.
	 This method will retain the original image's aspect ratio """
	bx,by=sz
	ix,iy = img.get_size()
	sx,sy=calc_scale(ix,iy,bx,by)

	return pygame.transform.scale(img, (int(sx),int(sy)))

def color_replace(surface, find_color, replace_color):
	for x in range(surface.get_size()[0]):
		for y in range(surface.get_size()[1]):
			print(surface.get_at([x, y]))
			if surface.get_at([x, y]) == find_color:
				surface.set_at([x, y], replace_color)
	return surface

class Font:
	def __init__(self, basepath, size, characters, scale=2, padding=1):
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
		space=pygame.Surface([self.size]*2).convert()
		space.fill((255,255,255))
		space.set_colorkey((255,255,255))
		self.cache[' ']=space
		for char in self.characters:
			img=pygame.image.load(self.basepath+"%s.png"%char).convert()
			img.set_colorkey((255,255,255))
			self.cache[char]=pygame.transform.scale(img, [self.scaledsize]*2)

	def render(self, text, color=(255,255,255)):
		surf=pygame.Surface((len(text)*(self.scaledsize+self.padding), self.scaledsize))
		surf.set_colorkey((69,69,69))
		surf.fill((69,69,69))
		for idx, char in enumerate(text.upper()):
			if char not in self.characters+" ":
				print("***ERROR*** %s not in font"%char)
			else:
				surf.blit(self.cache[char], (idx*(self.scaledsize+self.padding), 0))
		pa=pygame.PixelArray(surf)
		pa.replace((0,0,0), color)
		return pa.surface

class UIBar:
	def __init__(self, client, font, lgfont, path, width):
		self.client=client
		self.base_surf=pygame.image.load(path).convert()
		self.surf=self.base_surf.copy()
		self.font=font
		self.lgfont=lgfont
		self.width=width
		self.finalsize=self.calculate_size(width)
		self._redraw()

	def _redraw(self):
		self.surf=self.base_surf.copy()
		self.surf.blit(self.font.render("%04i"%self.client.cleared), (227,25))
		if self.client.next_block:
			self.surf.blit(self.client.next_block.render_mini(self.client.theme), (23,10))
		self.surf.blit(self.lgfont.render("%03i"%self.client.level), (535,20))
		self.surf.blit(self.font.render("%09i"%self.client.score), (800,25))
		self.surf=pygame.transform.scale(self.surf, self.finalsize)
		self.prev_cleared=self.client.cleared
		self.prev_next=self.client.next_block

	def update(self):
		if self.prev_cleared!=self.client.cleared or\
		   self.prev_next!=self.client.next_block:
			self._redraw()

	@classmethod
	def calculate_size(self, width):
		return calc_scale(1000, 64, width, 9999)

def disp_loading(screen, font, text):
	screen.fill((0,0,0))
	screen.blit(font.render(text), (0,0))
	pygame.display.flip()