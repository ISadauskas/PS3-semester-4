import random
import sys
import socket

HEADER = 2048
PORT = 8080
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def send(conn, msg):
    conn.send(msg.encode(FORMAT))

def receive(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg

def drawBoard(board, conn):
    # This function prints out the board that it was passed. returns None
    item = ""
    
    HLINE = '  +---+---+---+---+---+---+---+---+'
    VLINE = '  |   |   |   |   |   |   |   |   |'

    item += "\n" + '    1   2   3   4   5   6   7   8' + "\n"
    item += HLINE + "\n"

    for y in range(8):
        item += VLINE + "\n"
        item += " " + str(y + 1)
        for x in range(8):
            item += '|  ' + str(board[x][y])
        item += '|' + "\n"
        item += VLINE + "\n"
        item += HLINE + "\n"

    send(conn, item)

def resetBoard(board):
    # Blanks out the board if it is passed, except for the original starting position
    for x in range(8):
        for y in range(8):
            board[x][y] = ' '

    # Starting pieces:
    board[3][3] = 'X'
    board[3][4] = 'O'
    board[4][3] = 'O'
    board[4][4] = 'X'

def getNewBoard():
    # Creates a brand new, blank board data structure
    board = []
    for i in range(8):
        board.append([' '] * 8)
    
    return board

def isValidMove(board, tile, xstart, ystart):
    # Returns False if the player's move on space xstart, ystart is invalid
    # If it is a valid move returns a list of spaces-
    # -that would become the player's if they made a move here

    if board[xstart][ystart] != ' ' or not isOnBoard(xstart, ystart):
        return False
    board[xstart][ystart] = tile # temporarily set the tile on the board
    if tile == 'X':
        otherTile = 'O'
    else:
        otherTile = 'X'

    tilesToFlip = []
    for xdirection, ydirection in [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]:
        x, y = xstart, ystart
        x += xdirection # First step in the direction
        y += ydirection # first step in the direction

        if isOnBoard(x, y) and board[x][y] == otherTile:
            # There is a piece belonging to the other player next to our piece
            x += xdirection
            y += ydirection
            if not isOnBoard(x, y):
                continue
            
            while board[x][y] == otherTile:
                x += xdirection
                y += ydirection
                if not isOnBoard(x, y): # break out of while loop, then continue in for loop
                    break
            if not isOnBoard(x, y):
                continue
            if board[x][y] == tile:
                while True:
                    x -= xdirection
                    y -= ydirection
                    if x == xstart and y == ystart:
                        break
                    tilesToFlip.append([x, y])

    board[xstart][ystart] = ' ' # restore the empty space
    if len(tilesToFlip) == 0:
        return False
    return tilesToFlip

def isOnBoard(x, y):
    # Returns True if the coordinates are laocated on the board
    return x >= 0 and x <= 7 and y >= 0 and y <=7

def getBoardWithValidMoves(board, tile):
    # Returns a new board with . marking the valid moves the given player can make
    dupeBoard = getBoardCopy(board)

    for x, y in getValidMoves(dupeBoard, tile):
        dupeBoard[x][y] = '.'
    return dupeBoard

def getValidMoves(board, tile):
    # Returns a list of [x, y] lists of valid moves for the given player on the given board
    validMoves = []

    for x in range(8):
        for y in range(8):
            if isValidMove(board, tile, x, y) != False:
                validMoves.append([x, y])
    return validMoves

def getScoreOfBoard(board):
    # Determine the score by counting the tiles. Returns a dictionary with keys 'X' and 'O'.
    xscore = 0
    oscore = 0
    for x in range(8):
         for y in range(8):
             if board[x][y] == 'X':
                 xscore += 1

             if board[x][y] == 'O':
                 oscore += 1

    return {'X':xscore, 'O':oscore}

def enterPlayerTile(conn):
# Lets the player type which tile they want to be.
# Returns a list with the player's tile as the first item, and the computer's tile as the second.
    tile = ''
    while not (tile == 'X' or tile == 'O'):
        send(conn, 'Do you want to be X or O?')
        tile = receive(conn)
    
    if tile == 'X':
        return ['X', 'O']
    else:
        return ['O', 'X']

def whoGoesFirst():
    # Randomly choose the player who goes first
    if random.randint(0, 1) == 0:
        return 'computer'
    else:
        return 'player'

def playAgain():
    # This function return True if the player wants to play again, otherwise it returns False
    print('Do you want to play again? (yes or no)')
    return input().lower().startswith('y')

def makeMove(board, tile, xstart, ystart):
    # Place the tile on the board at xstart, ystart, and flip any of the opponent's pieces.
    # Returns False if this is an invalid move, True if it is valid.
    tilesToFlip = isValidMove(board, tile, xstart, ystart)
    if tilesToFlip == False:
        return False
    
    board[xstart][ystart] = tile
    for x, y in tilesToFlip:
        board[x][y] = tile
    return True

def getBoardCopy(board):
    # Make a duplicate of the board list and return the duplicate.

    dupeBoard = getNewBoard()
    for x in range(8):
        for y in range(8):
            dupeBoard[x][y] = board[x][y]
    return dupeBoard

def isOnCorner(x, y):
    return (x == 0 and y == 0) or (x == 7 and y == 0) or (x == 0 and y == 7) or (x == 7 and y == 7)

def getPlayerMove(board, playerTile, conn):
    # Let the player type in their move.
    # Returns the move as [x, y] (or returns the strings 'hints' or 'quit')
    DIGITS1TO8 = '1 2 3 4 5 6 7 8'.split()
    while True:
        send(conn, 'Enter your move')
        move = receive(conn)
        if move == 'quit':
            return 'quit'
        if move == 'hints':
            return 'hints'
        
        
        if len(move) == 2 and move[0] in DIGITS1TO8 and move[1] in DIGITS1TO8:
            x = int(move[0]) - 1
            y = int(move[1]) - 1
            if isValidMove(board, playerTile, x, y) == False:
                continue
            else:
                break
        else:
            send(conn, '')
            send(conn, '')
    return [x, y]

def getComputerMove(board, computerTile):
    possibleMoves = getValidMoves(board, computerTile)

    # randomize the order of the possible moves
    random.shuffle(possibleMoves)

    # always go for a corner if available.
    for x, y in possibleMoves:
        if isOnCorner(x, y):
            return [x, y]

    # Go through all the possible moves and remember the best scoring move
    bestScore = -1
    for x, y in possibleMoves:
        dupeBoard = getBoardCopy(board)
        makeMove(dupeBoard, computerTile, x, y)
        score = getScoreOfBoard(dupeBoard)[computerTile]
        if score > bestScore:
            bestMove = [x, y]
            bestScore = score
    return bestMove

# def showPoints(playerTile, computerTile):
#     # Prints out the current score.
#     scores = getScoreOfBoard(mainBoard)
#     print('You have %s points. The computer has %s points.' % (scores[playerTile], scores[computerTile]))


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()

        send(conn, "Welcome to Reversi!")
        while True:
            # Reset the board and game.
            mainBoard = getNewBoard()
            resetBoard(mainBoard)
            playerTile, computerTile = enterPlayerTile(conn)
            showHints = False
            turn = whoGoesFirst()
            send(conn, 'The ' + turn + ' will go first.')

            while True:
                if turn == 'player':
                    # Player's turn.
                    if showHints:
                        validMovesBoard = getBoardWithValidMoves(mainBoard, playerTile)
                        drawBoard(validMovesBoard, conn)
                    else:
                        drawBoard(mainBoard, conn)
                    #showPoints(playerTile, computerTile)
                    move = getPlayerMove(mainBoard, playerTile, conn)
                    if move == 'quit':
                        print('Thanks for playing!')
                        sys.exit() # terminate the program
                    elif move == 'hints':
                        showHints = not showHints
                        continue
                    else:
                        makeMove(mainBoard, playerTile, move[0], move[1])

                    if getValidMoves(mainBoard, computerTile) == []:
                        break
                    else:
                        turn = 'computer'
                else:
                    # Computer's turn.
                    drawBoard(mainBoard, conn)
                    #showPoints(playerTile, computerTile)
                    send(conn, 'Press Enter to see the computer\'s move.')
                    receive(conn)
                    x, y = getComputerMove(mainBoard, computerTile)
                    makeMove(mainBoard, computerTile, x, y)

                    if getValidMoves(mainBoard, playerTile) == []:
                        break
                    else:
                        turn = 'player'

            # Display the final score.
            drawBoard(mainBoard)
            scores = getScoreOfBoard(mainBoard)
            print('X scored %s points. O scored %s points.' % (scores['X'], scores['O']))
            if scores[playerTile] > scores[computerTile]:
                print('You beat the computer by %s points! Congratulations!' % (scores[playerTile] - scores[computerTile]))
            elif scores[playerTile] < scores[computerTile]:
                    print('You lost. The computer beat you by %s points.' % (scores[computerTile] - scores[playerTile]))
            else:
                print('The game was a tie!')

            if not playAgain():
                 break


print("[STARTING] server is starting...")
start()
