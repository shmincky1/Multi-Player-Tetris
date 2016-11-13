import struct, block, pygame, socket, json, threading, enum, random

RECV_BUF_SIZE=1024

class _SliceView:
	def __init__(self, list, offset):
		self.offset=offset
		self.list=list
	def __getitem__(self, idx):
		return self.list[self.offset+idx]
	def __setitem__(self, idx, val):
		self.list[self.offset+idx]=val

class Game:
	def __init__(self):
		self.blocks={}
		self.game_state=GameStates.joining

	def init_board(self, size):
		print("initing board")
		self.placed_blocks=[] #array of rows
		for i in range(size[1]):
			self.placed_blocks.extend([-1]*size[0]) #1d array for speed... i think
		self.size=size
		self._format_string = "!" + ("b"*size[0]*size[1])

	def __getitem__(self, idx):
		return _SliceView(self.placed_blocks, idx*self.size[0])

	def dump(self):
		return struct.pack(self._format_string, *self.placed_blocks)

	def load(self, data):
		self.placed_blocks=struct.unpack(self._format_string, data)

	def handle_loop(self):
		while True:
			try:
				data, addr = self.sock.recvfrom(RECV_BUF_SIZE)
				if data[0]==ord("j"):
					self.handlej(json.loads(data.decode("utf-8")[1:]), addr)
				else:
					self.handle(data, addr)
			except socket.error as e:
				print(e)

class ClientView:
	def __init__(self, server, addr, identifier, window_size, ppi):
		self.server=server
		self.addr=addr
		self.identifier=identifier
		self.game_state=GameStates.joining
		self.view_offset=[0,0]
		self.view_size=[1,1]
		self.window_size=window_size
		self.ppi=ppi
		self.inch_width=(window_size[0]/ppi, window_size[1]/ppi)

	def send(self, data):
		self.server.sock.sendto(data.encode("utf-8"), self.addr)

	def sendb(self, data):
		self.server.sock.sendto(data, self.addr)

	def sendj(self, data):
		self.send("j"+json.dumps(data))

	def get_blocks_at_size(self, ipb):
		return (int(self.inch_width[0]//ipb), int(self.inch_width[1]//ipb))

	def get_block_size_in_pixels(self, ipb):
		return min(self.window_size[0]//self.get_blocks_at_size(ipb)[0],
			self.window_size[1]//self.get_blocks_at_size(ipb)[1])

	def get_world_scale(self, ipb):
		return self.get_block_size_in_pixels(ipb)/block.GRID_BASE_SIZE

class GameStates(enum.Enum):
	joining=0
	arranging=1
	playing=2

class Server(Game):
	def __init__(self, inches_per_block, theme, tickrate=4, server_address=('',1244)):
		self.theme=theme
		self.inches_per_block=inches_per_block
		self.server_address=server_address
		self.tickrate=tickrate
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(server_address)
		self.clients=[]
		Game.__init__(self)
		self.handle_thread=threading.Thread(target=self.handle_loop)
		self.handle_thread.start()
		self.tick_thread=threading.Thread(target=self.update_loop)
		self.tick_thread.start()

	def recalculate_size(self):
		self.init_board((sum([c.get_blocks_at_size(self.inches_per_block)[0] for c in self.clients]),
			min([c.get_blocks_at_size(self.inches_per_block)[1] for c in self.clients])))
		print("Server recalculated size... "+str(self.size))

	def handle_join_loop(self, client):
		while client.game_state==GameStates.joining:
			client.sendj({
				"action":"accept",
				"themename":self.theme.name,
				"themeprefix":self.theme.prefix,
				"inches_per_block":self.inches_per_block
			})

	def handle_join(self, dgram, addr):
		if self.client_by_addr(addr):return
		print("`"+dgram["username"] + "` Connecting..")
		client=ClientView(self, addr, dgram["username"], dgram["screensize"], dgram["ppi"])
		self.clients.append(client)
		threading.Thread(target=self.handle_join_loop, args=(client,)).start()
		self.recalculate_size()

	def handlej(self, dgram, addr):
		if dgram["action"]=="join":
			self.handle_join(dgram, addr)
		if dgram["action"]=="join_OK":
			self.client_by_addr(addr).game_state=GameStates.arranging
			self.game_state=GameStates.arranging

	def handle(self, dgram, addr):
		print(dgram, addr, "!?")

	def client_by_addr(self, addr):
		l=[c for c in self.clients if c.addr==addr]
		return l[0] if l else None

	def update_loop(self):
		clock=pygame.time.Clock()
		while True:
			clock.tick(self.tickrate)
			if self.game_state==GameStates.arranging:
				data=self.dump()
				[client.sendb(data) for client in self.clients]
				[client.sendj({
					"action":"arrange_update",
					"size":self.size
				}) for client in self.clients]

class Client(Game):
	def __init__(self, identifier, size, ppi, address):
		Game.__init__(self)
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.address=address
		self.identifier=identifier
		self.view=ClientView(None, None, self.identifier, size, ppi)

		self.block=None

		# self.connect()

	def send(self, data):
		self.sock.sendto(data.encode("utf-8"), self.address)

	def sendj(self, data):
		self.send("j"+json.dumps(data))

	def connect(self):
		self.handle_thread=threading.Thread(target=self.handle_loop)
		self.handle_thread.start()
		while self.game_state==GameStates.joining:
			self.sendj({
				"action":"join",
				"username":self.identifier,
				"screensize":self.view.window_size,
				"ppi":self.view.ppi
			})

	def handlej(self, data, addr):
		if data["action"]=="accept":
			self.theme=block.Theme(data["themename"], data["themeprefix"])
			self.inches_per_block=data["inches_per_block"]
			self.sendj({"action":"join_OK"})

		if data["action"]=="arrange_update":
			if self.game_state==GameStates.joining:
				self.init_board(data["size"])
				self.game_state=GameStates.arranging
			else:
				if self.size!=data["size"]:
					self.init_board(data["size"])

	def handle(self, dgram, addr):
		if self.game_state==GameStates.arranging:
			try:
				self.load(dgram)
			except struct.error:
				print("(server changed size, struct error)")

	def get_scale(self):
		return self.view.get_world_scale(self.inches_per_block)

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

	def render(self, screen):
		print(self.get_scale())
		screen.fill((0,0,0))
		surf=self.draw_placed_blocks()
		size=surf.get_rect().size
		newsize=int(size[0]*self.get_scale()), int(size[1]*self.get_scale())
		screen.blit(pygame.transform.scale(surf, newsize), (-self.view.get_block_size_in_pixels(self.inches_per_block)*self.view.view_offset[0],0))