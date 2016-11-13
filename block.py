from enum import Enum
import pygame, os, json, struct

RESOURCES_FOLDER="img"
GRID_BASE_SIZE=7

class Styles(Enum):
	DARK=0
	HOLLOW=1
	LIGHT=2

	@classmethod
	def from_string(cls, string):
		return {
			"dark":cls.DARK,
			"hollow":cls.HOLLOW,
			"light":cls.LIGHT
		}[string]

class Theme:
	def __init__(self, name, prefix):
		self.name=name
		self.prefix=prefix
		self.load_images()

	def load_images(self):
		self.images={}
		for style in Styles:
			self.images[style.value]=pygame.image.load(
				os.path.join(RESOURCES_FOLDER,self.prefix+"-"+style.name.lower()+".png")
			)

	def get_image(self, style):
		return self.images[style.value]

class BlockType:
	def __init__(self, grids, style, typeid):
		self.style=style
		self.images={} #Mapping of Theme -> [0 deg rotated image, 90 deg rotated image, 180 deg rotated image, 170 deg rotated image]
		self.grids=grids #array of 4x4 rows, cols array of booleans
		self.typeid=typeid

	def build_images_for_theme(self, theme):
		if theme in self.images: return
		self.images[theme]=[]
		for rot_idx in range(len(self.grids)):
			grid=self.grids[rot_idx]
			surf=pygame.Surface((4*GRID_BASE_SIZE, 4*GRID_BASE_SIZE))
			for row_idx, row in enumerate(grid):
				for col_idx, value in enumerate(row):
					if value:
						surf.blit(theme.get_image(self.style), (col_idx*GRID_BASE_SIZE, row_idx*GRID_BASE_SIZE))
			self.images[theme].append(surf)

class Block:
	_format_string="!HBHHB"
	def __init__(self, blocktype, theme, blockid=None, position=None, rotation=0):
		self.worldpos=position if position else [0,0]
		self.blockid=blockid
		self.blocktype=blocktype
		self.images=blocktype.images[theme]
		self.grids=blocktype.grids
		self.rotation=rotation

	def next_rot(self):
		self.rotation+=1
		if self.rotation==len(self.grids):
			self.rotation=0

	def prev_rot(self):
		self.rotation-=1
		if self.rotation==-1:
			self.rotation=len(self.grids)[-1]

	def dump(self):
		return struct.pack(self._format_string, self.blockid, self.blocktype.typeid, self.x, self.y, self.rotation)

	def load(self, rot, x, y):
		self.rotation=rot
		self.x, self.y=x,y

	@property
	def image(self):
		return self.images[self.rotation]

	@property
	def grid(self):
		return self.grids[self.rotation]

	@property
	def x(self): return self.worldpos[0]

	@x.setter
	def x(self, v): self.worldpos[0]=v

	@property
	def y(self): return self.worldpos[1]

	@y.setter
	def y(self, v): self.worldpos[1]=v

def load_blocktypes(path):
	blocktypes={}
	with open(path) as fd:
		data=json.load(fd)
		idx=0
		for name, data in data["blocks"].items():
			blocktypes[name]=BlockType(data["grids"], Styles.from_string(data["style"]), ord(name))
	return blocktypes

def build_images_for_theme(blocktypes, theme):
	[blocktype.build_images_for_theme(theme) for blocktype in blocktypes]