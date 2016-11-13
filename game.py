import struct, block, pygame, socket, json, threading, enum, random

class _SliceView:
	def __init__(self, list, offset):
		self.offset=offset
		self.list=list
	def __getitem__(self, idx):
		try:
			return self.list[self.offset+idx]
		except IndexError:
			return -1
	def __setitem__(self, idx, val):
		self.list[self.offset+idx]=val

class Game:
	def __init__(self):
		self.blocks={}
		self.game_state=GameStates.joining
		self.recv_buf_size=1024
		self.blocktypes=block.load_blocktypes('blocks.json')
		self.cleared=0
		self.score=0
		self.level=0

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
				data, addr = self.sock.recvfrom(self.recv_buf_size)
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
		self.view_offset=0
		self.window_size=window_size
		self.ppi=ppi
		self.inch_width=(window_size[0]/ppi, window_size[1]/ppi)
		self.owned_block=None
		self.next_block=None

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
		self.tickrate=self.initial_tickrate=tickrate
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(server_address)
		self.clients=[]
		Game.__init__(self)
		self.handle_thread=threading.Thread(target=self.handle_loop, name="Server_handle")
		self.handle_thread.start()
		self.tick_thread=threading.Thread(target=self.update_loop, name="Server_tick")
		self.tick_thread.start()
		self.current_blockid=0

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
				"inches_per_block":self.inches_per_block,
				"xoffset":self.size[0]-client.get_blocks_at_size(self.inches_per_block)[0]
			})

	def handle_join(self, dgram, addr):
		if self.client_by_addr(addr):return
		print("`"+dgram["username"] + "` Connecting..")
		client=ClientView(self, addr, dgram["username"], dgram["screensize"], dgram["ppi"])
		self.clients.append(client)

		self.recalculate_size()

		client.view_width=client.get_blocks_at_size(self.inches_per_block)[0]
		client.view_offset=self.size[0]-client.view_width

		
		threading.Thread(
			target=self.handle_join_loop,
			args=(client,),
			name="Server_handlejoin_"+client.identifier
		).start()

	def handlej(self, dgram, addr):
		if dgram["action"]=="join":
			self.handle_join(dgram, addr)
		else:
			client=self.client_by_addr(addr)
			if dgram["action"]=="join_OK":
				client.game_state=GameStates.arranging
				self.game_state=GameStates.arranging
			if dgram["action"]=="start_OK":
				client.game_state=GameStates.playing
				self.create_user_blocks()

			if client.owned_block is None:
				return

			initial=client.owned_block.x
			initial_rot=client.owned_block.rotation
			if dgram["action"]=="move_left":
				print("Moving left")
				client.owned_block.x-=1
				if client.owned_block.x+client.owned_block.get_leftmost()<=-1:
					client.owned_block.x=self.size[0]-client.owned_block.get_rightmost()-1
			elif dgram["action"]=="move_right":
				client.owned_block.x+=1
				if client.owned_block.x+client.owned_block.get_rightmost()>=self.size[0]:
					client.owned_block.x=-client.owned_block.get_leftmost()
			elif dgram["action"]=="rotate_cw":
				client.owned_block.next_rot()
			elif dgram["action"]=="rotate_ccw":
				client.owned_block.prev_rot()

			if self.get_collisions(predict=0):
				client.owned_block.x=initial
				client.owned_block.rotation=initial_rot

			if dgram["action"]=="move_down":
				client.owned_block.y+=1

			if dgram["action"] in ["move_left", "move_right", "move_down", "rotate_cw", "rotate_ccw"]:
				if self.check_collisions():
					self.send_blocks_update()
				self.send_update()

	def handle(self, dgram, addr):
		print(dgram, addr, "!?")

	def client_by_addr(self, addr):
		l=[c for c in self.clients if c.addr==addr]
		return l[0] if l else None

	def get_blocks_message(self):
		msg=b"b"+struct.pack('!b', len(self.blocks))
		for block in self.blocks.values():
			msg+=block.dump()
		return msg

	def send_update(self):
		msg=self.get_blocks_message()
		[client.sendb(msg) for client in self.clients]

	def send_blocks_update(self):
		data=self.dump()
		[client.sendb(data) for client in self.clients]

	def update_loop(self):
		clock=pygame.time.Clock()
		while True:
			clock.tick(self.tickrate)
			if self.game_state==GameStates.arranging:
				[client.sendj({
					"action":"arrange_update",
					"size":self.size
				}) for client in self.clients]
			if self.game_state==GameStates.playing:
				
				for block in self.blocks.values():
					block.y+=1

				done=False
				updated=0
				while not done:
					done=True
					for row in range(self.size[1]):
						if all([blk!=-1 for blk in\
						 self.placed_blocks[self.size[0]*row:self.size[0]*(row+1)]]):
							for row_to_move in reversed(range(row)):
								for col in range(self.size[0]):
									self[row_to_move+1][col]=self[row_to_move][col]
							for col in range(self.size[0]):
								self[0][col]=-1
							done=False
							updated+=1
							self.cleared+=1
							
				if updated:
					self.score+=[0, 40, 100, 300, 1200][updated]*(self.level+1)
					self.level=self.cleared//10
					self.tickrate=self.initial_tickrate*(0.75**self.level)
					[client.sendj({
						"action":"update_cleared",
						"cleared":self.cleared,
						"score":self.score,
						"level":self.level
					}) for client in self.clients]

				if self.check_collisions() or updated:
					self.send_blocks_update()

				self.send_update()

	def get_collisions(self, predict=1):
		colliding=[]
		for blockid, block in self.blocks.items():
			destroy_block=False
			for row_idx, row in enumerate(block.grid):
				for col_idx, val in enumerate(row):
					if val:
						if block.y+row_idx+predict==self.size[1] or \
						   self[block.y+row_idx+predict][block.x+col_idx]!=-1:
							destroy_block=True
			if destroy_block:
				colliding.append(blockid)
		return colliding
			

	def check_collisions(self):
		collisions=self.get_collisions()
		for key in collisions:
			block=self.blocks[key]
			for row_idx, row in enumerate(block.grid):
				for col_idx, val in enumerate(row):
					if val:
						self[block.y+row_idx][block.x+col_idx]=block.blocktype.style.value

			for client in self.clients:
				if client.owned_block==self.blocks[key]:
					client.owned_block=None
			del self.blocks[key]

		self.create_user_blocks()
		return len(collisions)
	
	def create_user_blocks(self):
		for client in self.clients:
			if client.next_block is None:
				client.next_block=random.choice(list(self.blocktypes.values()))
			if client.owned_block is None:
				# print(client.view_offset+2-(client.view_width//2))
				client.owned_block=self.create_block(
					client.next_block,
					client.view_offset+(client.view_width//2)-2,
					-2
				)
				client.next_block=random.choice(list(self.blocktypes.values()))
				client.sendj({"action":"notify_next_block", "block":chr(client.next_block.typeid)})

	def create_block(self, blocktype, x, y):
		self.current_blockid+=1
		self.blocks[self.current_blockid]=block.Block(blocktype, self.theme, self.current_blockid, [x,y])
		return self.blocks[self.current_blockid]

	def start_game(self):
		while not all([c.game_state==GameStates.playing for c in self.clients]):
			for client in self.clients:
				print("starting...")
				client.sendj({"action":"start"})
		self.game_state=GameStates.playing

class Client(Game):
	def __init__(self, identifier, size, ppi, address):
		Game.__init__(self)
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.address=address
		self.identifier=identifier
		self.view=ClientView(None, None, self.identifier, size, ppi)
		self.styles_cache={}

		self.block=None
		self.next_block=None

		self._surf=pygame.Surface(size)

		# self.connect()

	def send(self, data):
		self.sock.sendto(data.encode("utf-8"), self.address)

	def sendj(self, data):
		self.send("j"+json.dumps(data))

	def connect(self):
		self.handle_thread=threading.Thread(target=self.handle_loop, name="Client_handle")
		self.handle_thread.start()
		while self.game_state==GameStates.joining:
			self.sendj({
				"action":"join",
				"username":self.identifier,
				"screensize":self.view.window_size,
				"ppi":self.view.ppi
			})

	def handlej(self, data, addr):
		print(data)
		if data["action"]=="accept":
			self.theme=block.Theme(data["themename"], data["themeprefix"])
			self.inches_per_block=data["inches_per_block"]
			self.view.view_offset=data["xoffset"]
			self.view.view_width=self.view.get_blocks_at_size(self.inches_per_block)[0]
			self.sendj({"action":"join_OK"})

		if data["action"]=="arrange_update":
			if self.game_state==GameStates.joining:
				self.init_board(data["size"])
				self.game_state=GameStates.arranging
			else:
				if self.size!=data["size"]:
					self.init_board(data["size"])
					self.styles_cache={}

			self.recv_buf_size=self.size[0]*self.size[1]+10

		if data["action"]=="start":
			self.game_state=GameStates.playing
			self.sendj({"action":"start_OK"})

		if data["action"]=="update_cleared":
			self.cleared=data["cleared"]
			self.score=data["score"]
			self.level=data["level"]

		if data["action"]=="notify_next_block":
			self.next_block=self.blocktypes[data["block"]]

	def handle(self, dgram, addr):
		if dgram[0]==ord('b'):
			if self.game_state==GameStates.playing:
				count=dgram[1]
				idx=2
				structsz=struct.calcsize(block.Block._format_string)
				mine=list(self.blocks.keys())
				thiers=[]
				for _ in range(count):
					blockid, typeid, x, y, rot = \
					 struct.unpack(block.Block._format_string, dgram[idx:idx+structsz])
					print(blockid, typeid, x, y, rot)
					if blockid in self.blocks:
						self.blocks[blockid].load(rot, x, y)
					else:
						self.blocks[blockid]=block.Block(
							self.blocktypes[chr(typeid)],
							self.theme,
							blockid=blockid,
							position=[x,y],
							rotation=rot
						)
					thiers.append(blockid)
					idx+=structsz

				for bid in mine:
					if bid not in thiers:
						del self.blocks[bid]
		else:
			if self.game_state!=GameStates.joining:
				try:
					self.load(dgram)
				except struct.error as e:
					print("(server changed size, struct error)")

	def get_scale(self):
		return self.view.get_world_scale(self.inches_per_block)

	def compute_offset(self, x, y):
		blocksize=self.view.get_block_size_in_pixels(self.inches_per_block)
		return ((x-self.view.view_offset)*blocksize, y*blocksize)

	def drawworldblock(self, screen, x, y, style):
		blocksize=self.view.get_block_size_in_pixels(self.inches_per_block)
		if style in self.styles_cache:
			img=self.styles_cache[style]
		else:
			img=pygame.transform.scale(self.theme.get_image(style), (blocksize, blocksize))
			self.styles_cache[style]=img

		pos=self.compute_offset(x,y)
		# if pos[0]<0 or pos[0]>self.view.window_size[0]+20:
		# 	return

		screen.blit(img, pos)

	def draw_placed_blocks(self, screen):
		row=0
		col=0
		for blk in self.placed_blocks:
			if blk!=-1:
				self.drawworldblock(screen, col, row, block.Styles(blk))
			col+=1
			if col>=self.size[0]:
				col=0
				row+=1

	def render(self, screen, y_offset):
		# print(self.get_scale())
		self._surf.fill((0,0,0))
		if self.game_state==GameStates.playing:
			self.draw_placed_blocks(self._surf)
			for name, block in self.blocks.items():
				block.draw_to(self._surf, self, block.x, block.y)
		else:
			for x in range(self.view.view_offset-1, self.view.view_offset+self.view.view_width+2):
				for y in range(self.view.get_blocks_at_size(self.inches_per_block)[1]+1):
					self._surf.blit(
						pygame.font.SysFont("monospace",10).render("%i,%i"%(x,y), 0, (255,255,255)),
						self.compute_offset(x,y)
					)
					pygame.draw.rect(
						self._surf,
						(255,0,0),
						pygame.Rect(
							self.compute_offset(x,y),
							[self.view.get_block_size_in_pixels(self.inches_per_block)]*2
						),
						1
					)
		screen.blit(self._surf, (0,y_offset))

	def handle_event(self, event):
		if event.key==pygame.K_LEFT:
			print("Sending move left")
			self.sendj({"action":"move_left"})
		elif event.key==pygame.K_RIGHT:
			self.sendj({"action":"move_right"})
		elif event.key==pygame.K_DOWN:
			self.sendj({"action":"move_down"})
		elif event.key==pygame.K_a:
			self.sendj({"action":"rotate_ccw"})
		elif event.key in [pygame.K_UP, pygame.K_d]:
			self.sendj({"action":"rotate_cw"})
