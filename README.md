# Multiplayer-Tetris
## System Requirements
* Python 3.5
* PyGame
* Fast local network
## To Run
1. Set environment variable "PPI" to [horizontal res of screen]/[diagonal measurement of screen]
  a. Linux command: 'PPI=[ppi value]'
  b. Windows command: '$env:PPI=[ppi value]'
2. Run server/client combo, this should be the far left computer
  a. run command in Multiplayer-Tetris directory: '[your python command such as 'python' or 'python3'] runclent.py server bpi=[how many blocks per inch you want, .5 is usually good for 15" screens, the bigger the screen the higher this value should be]'
    A. eg. python3 runclient.py server bpi=.5
3. Run clients from left to right starting with the second one (waiting until the grid shows up to start the next one) with the command: [python] runclient.py client [server's local ip]
4. Wait until all clients are connected and displaying the grid then press enter on the server