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
	def __init__(self, size, theme):
		self.blocks={}
		self.placed_blocks=[] #array of rows
		for i in range(size[1]):
			self.placed_blocks.extend([-1]*size[0]) #1d array for speed... i think
		self.size=size
		self.theme=theme
		self._format_string = "!" + ("b"*size[0]*size[1])

		self.game_state=GameStates.joining

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

	def handle_loop(self):
		while True:
			try:
				data, addr = self.sock.recvfrom(RECV_BUF_SIZE)
				data=data.decode("utf-8")
				if data[0]=="j":
					self.handlej(json.loads(data[1:]), addr)
				else:
					self.handle(data, addr)
			except socket.error as e:
				print(e)

class ServerClient:
	def __init__(self, server, addr, identifier):
		self.server=server
		self.addr=addr
		self.identifier=identifier
		self.game_state=GameStates.joining

	def send(self, data):
		self.server.sock.sendto(data.encode("utf-8"), self.addr)

	def sendj(self, data):
		self.send("j"+json.dumps(data))

class GameStates(enum.Enum):
	joining=0
	arranging=1
	playing=2

class Server(Game):
	def __init__(self, size, theme, tickrate=4, server_address=('',1244)):
		self.size=size
		self.theme=theme
		self.server_address=server_address
		self.tickrate=tickrate
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(server_address)
		self.clients=[]
		Game.__init__(self, size, theme)
		self.handle_thread=threading.Thread(target=self.handle_loop)
		self.handle_thread.start()
		self.tick_thread=threading.Thread(target=self.update_loop)
		self.tick_thread.start()

	def handle_join_loop(self, client):
		while client.game_state==GameStates.joining:
			client.sendj({"action":"accept", "themename":self.theme.name, "themeprefix":self.theme.prefix})

	def handle_join(self, dgram, addr):
		if self.client_by_addr(addr):return
		client=ServerClient(self, addr, dgram["username"])
		self.clients.append(client)
		threading.Thread(target=self.handle_join_loop, args=(client,)).start()

	def handlej(self, dgram, addr):
		print(dgram)
		if dgram["action"]=="join":
			self.handle_join(dgram, addr)
		if dgram["action"]=="join_OK":
			self.client_by_addr(addr).game_state=GameStates.arranging

	def client_by_addr(self, addr):
		l=[c for c in self.clients if c.addr==addr]
		return l[0] if l else None

	def update_loop(self):
		clock=pygame.time.Clock()
		while True:
			clock.tick(self.tickrate)

class Client(Game):
	def __init__(self, identifier, address):
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.address=address
		self.identifier=identifier

		Game.__init__(self, (0,0), None)

		self.connect()

	def send(self, data):
		self.sock.sendto(data.encode("utf-8"), self.address)

	def sendj(self, data):
		self.send("j"+json.dumps(data))

	def connect(self):
		self.handle_thread=threading.Thread(target=self.handle_loop)
		self.handle_thread.start()
		while self.game_state==GameStates.joining:
			self.sendj({"action":"join", "username":self.identifier})

	def handlej(self, data, addr):
		if data["action"]=="accept":
			self.game_state=GameStates.arranging
			self.theme=block.Theme(data["themename"], data["themeprefix"])
			self.sendj({"action":"join_OK"})