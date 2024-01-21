import tkinter as tk
from tkinter import ttk
import numpy as np
from threading import Thread
from queue import Queue
from threading import Semaphore

semaphore = Semaphore(350)

disk_color = ['white', 'red', 'orange']
disks = list()

player_type = ['human']
for i in range(42):
    player_type.append('AI: alpha-beta level '+str(i+1))

def alpha_beta_decision(board, turn, ai_level, queue, max_player):
    moves = board.get_possible_moves()
    best_move = moves[0]
    best_score = np.NINF
    for move in moves:
        new_board = board.copy()
        new_board.add_disk(move, max_player, False)
        score = alpha_beta_min(new_board, turn + 1, ai_level - 1, np.NINF, np.inf, max_player)
        if score > best_score:
            best_score = score
            best_move = move
    queue.put(best_move)

def alpha_beta_min(board, turn, ai_level, alpha, beta, max_player):
    if board.check_victory():
        return 10000000
    elif turn >= 42:   
        return 0
    elif ai_level == 0:
        return board.eval(max_player)
    score = 2000000
    moves = board.get_possible_moves()
    for move in moves:
        new_board = board.copy()
        new_board.add_disk(move, max_player % 2 + 1, False)
        max_score = alpha_beta_max(new_board, turn + 1, ai_level - 1, alpha, beta, max_player)
        score = min(score, max_score)
        if score <= alpha:
            return score
        beta = min(beta, score)
    return score

def alpha_beta_max(board, turn, ai_level, alpha, beta, max_player):
    if board.check_victory():
        return -10000000
    elif turn >= 42:
        return 0
    elif ai_level == 0:
        return board.eval(max_player)
    score = -2000000
    moves = board.get_possible_moves()
    for move in moves:
        new_board = board.copy()
        new_board.add_disk(move, max_player, False)
        min_score = alpha_beta_min(new_board, turn + 1, ai_level - 1, alpha, beta, max_player)
        score = max(score, min_score)
        if score >= beta:
            return score
        alpha = max(alpha, score)
    return score

def alpha_beta_decision_thread(board, turn, ai_level, queue, max_player):
    moves = board.get_possible_moves()
    best_move = moves[0]
    best_score = float('-inf')
    threads  = []
    # Function to be executed by each thread
    def alpha_beta(move):
        nonlocal best_score, best_move
        #with semaphore:
        new_board = board.copy()
        new_board.add_disk(move, max_player, False)
        score = alpha_beta_min_thread(new_board, turn + 1, ai_level - 1, float('-inf'), float('inf'), max_player)
        if score > best_score:
            best_score = score
            best_move = move
    # Create a thread for each possible move
    for move in moves:
        threads.append(Thread(target=alpha_beta, args=(move,)))
        threads[-1].start()
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    queue.put(best_move)

def alpha_beta_min_thread(board, turn, ai_level, alpha, beta, max_player):
    if board.check_victory():
        return 10000000
    elif turn >= 42:   
        return 0
    elif ai_level == 0:
        return board.eval(max_player)
    score = 2000000
    moves = board.get_possible_moves()
    threads = []
    # Function to be executed by each thread
    def min_move(move):
        nonlocal score
        # Try to acquire the semaphore, if it fails, it means that the maximum number of threads is reached
        acquired = semaphore.acquire(timeout = 0.1)
        # If the semaphore is not acquired, call the function without creating a thread
        if not acquired:
            print("timeout")
            new_board = board.copy()
            new_board.add_disk(move, max_player % 2 + 1, False)
            max_score = alpha_beta_max(new_board, turn + 1, ai_level - 1, alpha, beta, max_player)
            score = min(score, max_score)
            return
        # If the semaphore is acquired, create a thread
        try:
            new_board = board.copy()
            new_board.add_disk(move, max_player % 2 + 1, False)
            max_score = alpha_beta_max_thread(new_board, turn + 1, ai_level - 1, alpha, beta, max_player)
            score = min(score, max_score)
        # after the thread is finished, release the semaphore
        finally:
            semaphore.release()
    # Create a thread for each possible move
    for move in moves:
        threads.append(Thread(target=min_move, args=(move,)))
        threads[-1].start()
    if score <= alpha:
        return score
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    beta = min(beta, score)
    return score

def alpha_beta_max_thread(board, turn, ai_level, alpha, beta, max_player):
    if board.check_victory():
        return -10000000
    elif turn >= 42:
        return 0
    elif ai_level == 0:
        return board.eval(max_player)
    score = -2000000
    moves = board.get_possible_moves()
    threads = []
    # Function to be executed by each thread
    def max_move(move):
        nonlocal score
        # Try to acquire the semaphore, if it fails, it means that the maximum number of threads is reached
        acquired = semaphore.acquire(timeout = 0.1)
        # If the semaphore is not acquired, call the function without creating a thread
        if not acquired:
            print("timeout")
            new_board = board.copy()
            new_board.add_disk(move, max_player, False)
            min_score = alpha_beta_min(new_board, turn + 1, ai_level - 1, alpha, beta, max_player)
            score = max(score, min_score)
            return
        # If the semaphore is acquired, create a thread
        try:
            new_board = board.copy()
            new_board.add_disk(move, max_player, False)
            min_score = alpha_beta_min_thread(new_board, turn + 1, ai_level - 1, alpha, beta, max_player)
            score = max(score, min_score)
        # after the thread is finished, release the semaphore
        finally:
            semaphore.release()
    # Create a thread for each possible move
    for move in moves:
        threads.append(Thread(target=max_move, args=(move,)))
        threads[-1].start()
    if score >= beta:
        return score
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    alpha = max(alpha, score)
    return score

class Board:
    grid = np.array([[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])

    # return the score of the board for the player
    def eval(self, max_player):
        score = 0

        score += self.alignement(max_player)
        score -= 2 * self.alignement(max_player % 2 + 1)
        score += self.centered(max_player)

        return score
    
    # add the value of the sequence for each possible sequence of 4 disks
    def alignement(self, player):
        score = 0
        
        # Horizontal sequence
        for line in range(6):
            for horizontal_shift in range(4):
                score += self.eval_sequence([self.grid[horizontal_shift][line], self.grid[horizontal_shift + 1][line], 
                                             self.grid[horizontal_shift + 2][line], self.grid[horizontal_shift + 3][line]], player)
                
        # Vertical sequence
        for column in range(7):
            for vertical_shift in range(3):
                score += self.eval_sequence([self.grid[column][vertical_shift], self.grid[column][vertical_shift + 1], 
                                             self.grid[column][vertical_shift + 2], self.grid[column][vertical_shift + 3]], player)
                
        # Diagonal sequence
        for horizontal_shift in range(4):
            for vertical_shift in range(3):
                score += self.eval_sequence([self.grid[horizontal_shift][vertical_shift], self.grid[horizontal_shift + 1][vertical_shift + 1], 
                                             self.grid[horizontal_shift + 2][vertical_shift + 2], self.grid[horizontal_shift + 3][vertical_shift + 3]], player)
                score += self.eval_sequence([self.grid[horizontal_shift][5 - vertical_shift], self.grid[horizontal_shift + 1][4 - vertical_shift], 
                                             self.grid[horizontal_shift + 2][3 - vertical_shift], self.grid[horizontal_shift + 3][2 - vertical_shift]], player)
                
        return score
    

    # return the score of the sequence
    def eval_sequence(self, sequence, player):
        score = 0

        if sequence.count(player) == 3 and sequence.count(0) == 1:
            score += 100
        elif sequence.count(player) == 2 and sequence.count(0) == 2:
            score += 10
        elif sequence.count(player) == 1 and sequence.count(0) == 3:
            score += 1

        return score
    
    def centered(self, player):
        score = 0
        for column in range(7):
            for line in range(6):
                if self.grid[column][line] == player:
                    # The more centered the disk is, the higher the score
                    score += 3 - abs(3 - column)
        return score

    def copy(self):
        new_board = Board()
        new_board.grid = np.array(self.grid, copy=True)
        return new_board

    def reinit(self):
        self.grid.fill(0)
        for i in range(7):
            for j in range(6):
                canvas1.itemconfig(disks[i][j], fill=disk_color[0])

    def get_possible_moves(self):
        possible_moves = list()
        if self.grid[3][5] == 0:
            possible_moves.append(3)
        for shift_from_center in range(1, 4):
            if self.grid[3 + shift_from_center][5] == 0:
                possible_moves.append(3 + shift_from_center)
            if self.grid[3 - shift_from_center][5] == 0:
                possible_moves.append(3 - shift_from_center)
        return possible_moves

    def add_disk(self, column, player, update_display=True):
        for j in range(6):
            if self.grid[column][j] == 0:
                break
        self.grid[column][j] = player
        if update_display:
            canvas1.itemconfig(disks[column][j], fill=disk_color[player])

    def column_filled(self, column):
        return self.grid[column][5] != 0

    def check_victory(self):
        # Horizontal alignment check
        for line in range(6):
            for horizontal_shift in range(4):
                if self.grid[horizontal_shift][line] == self.grid[horizontal_shift + 1][line] == self.grid[horizontal_shift + 2][line] == self.grid[horizontal_shift + 3][line] != 0:
                    return True
        # Vertical alignment check
        for column in range(7):
            for vertical_shift in range(3):
                if self.grid[column][vertical_shift] == self.grid[column][vertical_shift + 1] == \
                        self.grid[column][vertical_shift + 2] == self.grid[column][vertical_shift + 3] != 0:
                    return True
        # Diagonal alignment check
        for horizontal_shift in range(4):
            for vertical_shift in range(3):
                if self.grid[horizontal_shift][vertical_shift] == self.grid[horizontal_shift + 1][vertical_shift + 1] ==\
                        self.grid[horizontal_shift + 2][vertical_shift + 2] == self.grid[horizontal_shift + 3][vertical_shift + 3] != 0:
                    return True
                elif self.grid[horizontal_shift][5 - vertical_shift] == self.grid[horizontal_shift + 1][4 - vertical_shift] ==\
                        self.grid[horizontal_shift + 2][3 - vertical_shift] == self.grid[horizontal_shift + 3][2 - vertical_shift] != 0:
                    return True
        return False


class Connect4:

    def __init__(self):
        self.board = Board()
        self.human_turn = False
        self.turn = 1
        self.players = (0, 0)
        self.ai_move = Queue()

    def current_player(self):
        return 2 - (self.turn % 2)

    def launch(self):
        self.board.reinit()
        self.turn = 0
        information['fg'] = 'black'
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(
            self.current_player()) + " is playing"
        self.human_turn = False
        self.players = (combobox_player1.current(), combobox_player2.current())
        self.handle_turn()

    def move(self, column):
        if not self.board.column_filled(column):
            self.board.add_disk(column, self.current_player())
            self.handle_turn()

    def click(self, event):
        if self.human_turn:
            column = event.x // row_width
            self.move(column)

    def ai_turn(self, ai_level):
        Thread(target=alpha_beta_decision, args=(self.board, self.turn, ai_level, self.ai_move, self.current_player(),)).start()
        self.ai_wait_for_move()

    def ai_wait_for_move(self):
        if not self.ai_move.empty():
            self.move(self.ai_move.get())
        else:
            window.after(100, self.ai_wait_for_move)

    def handle_turn(self):
        self.human_turn = False
        if self.board.check_victory():
            information['fg'] = 'red'
            information['text'] = "Player " + str(self.current_player()) + " wins !"
            return
        elif self.turn >= 42:
            information['fg'] = 'red'
            information['text'] = "This a draw !"
            return
        self.turn = self.turn + 1
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(
            self.current_player()) + " is playing"
        if self.players[self.current_player() - 1] != 0:
            self.human_turn = False
            self.ai_turn(self.players[self.current_player() - 1])
        else:
            self.human_turn = True


game = Connect4()

# Graphical settings
width = 700
row_width = width // 7
row_height = row_width
height = row_width * 6
row_margin = row_height // 10

window = tk.Tk()
window.title("Connect 4")
canvas1 = tk.Canvas(window, bg="blue", width=width, height=height)

# Drawing the grid
for i in range(7):
    disks.append(list())
    for j in range(5, -1, -1):
        disks[i].append(canvas1.create_oval(row_margin + i * row_width, row_margin + j * row_height, (i + 1) * row_width - row_margin,
                            (j + 1) * row_height - row_margin, fill='white'))


canvas1.grid(row=0, column=0, columnspan=2)

information = tk.Label(window, text="")
information.grid(row=1, column=0, columnspan=2)

label_player1 = tk.Label(window, text="Player 1: ")
label_player1.grid(row=2, column=0)
combobox_player1 = ttk.Combobox(window, state='readonly')
combobox_player1.grid(row=2, column=1)

label_player2 = tk.Label(window, text="Player 2: ")
label_player2.grid(row=3, column=0)
combobox_player2 = ttk.Combobox(window, state='readonly')
combobox_player2.grid(row=3, column=1)

combobox_player1['values'] = player_type
combobox_player1.current(0)
combobox_player2['values'] = player_type
combobox_player2.current(6)

button2 = tk.Button(window, text='New game', command=game.launch)
button2.grid(row=4, column=0)

button = tk.Button(window, text='Quit', command=window.destroy)
button.grid(row=4, column=1)

# Mouse handling
canvas1.bind('<Button-1>', game.click)

window.mainloop()
