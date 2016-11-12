import struct, block, pygame, socket

class _SliceView:
	def __init__(self, list, offset):
		self.offset=offset
		self.list=list
	def __getitem__(self, idx):
		return self.list[self.offset+idx]
	def __setitem__(self, idx, val):
		self.list[self.offset+idx]=val

class Game:
	def __init__(self, size, theme):
		self.blocks={}
		self.placed_blocks=[] #array of rows
		for i in range(size[1]):
			self.placed_blocks.extend([-1]*size[0]) #1d array for speed... i think
		self.size=size
		self.theme=theme
		self._format_string = "!" + ("b"*size[0]*size[1])

	def __getitem__(self, idx):
		return _SliceView(self.placed_blocks, idx*self.size[0])

	def dump(self):
		return struct.pack(self._format_string, *self.placed_blocks)

	def load(self, data):
		self.placed_blocks=struct.unpack(self._format_string, data)

	def draw_placed_blocks(self):
		surf=pygame.Surface((block.GRID_BASE_SIZE*self.size[0], block.GRID_BASE_SIZE*self.size[1]))
		row=0
		col=0
		for blk in self.placed_blocks:
			if blk!=-1:
				pos = (block.GRID_BASE_SIZE*col, block.GRID_BASE_SIZE*row)
				surf.blit(self.theme.get_image(block.Styles(blk)), pos)
			col+=1
			if col>=self.size[0]:
				col=0
				row+=1
		return surf

class Server(Game):
	def __init__(self, size, theme, bind='0.0.0.0', port=737815):
		self.size=size
		self.theme=theme
		self.bind=bind
		self.port=port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(server_address)