import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import socket
import threading
import random
import math

# === 參數設定 ===
BOARD_SIZE = 15
CELL_SIZE = 40
OFFSET = 30
TIME_LIMIT = 30  # 每回合秒數

class GomokuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("五子棋終極版 (Gomoku Ultimate)")
        self.root.geometry("950x700") 

        # === 遊戲狀態 ===
        self.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history = []
        self.current_player = 1 # 1:黑, 2:白
        self.my_color = 1       # 單機預設為黑
        self.player_name = "玩家" # 預設暱稱
        self.game_over = False
        self.mode = "PVE"       
        self.difficulty = "Normal"
        self.timer_seconds = TIME_LIMIT
        self.socket = None
        self.effect_running = False # 控制特效開關
        
        # === 建立三個主要介面 ===
        self.create_main_menu()       
        self.create_difficulty_menu() 
        self.create_game_ui()         
        
        self.show_frame("MENU")

    # ================= 介面建立區 =================

    def create_main_menu(self):
        self.menu_frame = tk.Frame(self.root, bg="#222222")
        title = tk.Label(self.menu_frame, text="五 子 棋 大 戰", font=("微軟正黑體", 40, "bold"), fg="#00FF7F", bg="#222222")
        title.pack(pady=80)
        
        btn_style = {"font": ("微軟正黑體", 18), "width": 20, "pady": 10, "bd": 0}
        
        tk.Button(self.menu_frame, text="單機挑戰 (PVE)", command=self.go_to_difficulty_select, **btn_style, bg="#444444", fg="white").pack(pady=10)
        tk.Button(self.menu_frame, text="線上對戰 (Online)", command=self.setup_online, **btn_style, bg="#444444", fg="white").pack(pady=10)
        tk.Button(self.menu_frame, text="離開遊戲", command=self.root.quit, **btn_style, bg="#cc0000", fg="white").pack(pady=10)

    def create_difficulty_menu(self):
        self.diff_frame = tk.Frame(self.root, bg="#222222")
        title = tk.Label(self.diff_frame, text="請 選 擇 難 度", font=("微軟正黑體", 30, "bold"), fg="#FFD700", bg="#222222")
        title.pack(pady=60)
        
        btn_style = {"font": ("微軟正黑體", 16), "width": 20, "pady": 8, "bd": 0}
        tk.Button(self.diff_frame, text="簡單 (Easy)", command=lambda: self.start_pve("Easy"), **btn_style, bg="#90EE90").pack(pady=10)
        tk.Button(self.diff_frame, text="普通 (Normal)", command=lambda: self.start_pve("Normal"), **btn_style, bg="#87CEFA").pack(pady=10)
        tk.Button(self.diff_frame, text="困難 (Hard)", command=lambda: self.start_pve("Hard"), **btn_style, bg="#FF6347").pack(pady=10)
        tk.Button(self.diff_frame, text="返回", command=lambda: self.show_frame("MENU"), **btn_style, bg="#aaaaaa").pack(pady=30)

    def create_game_ui(self):
        self.game_frame = tk.Frame(self.root)
        
        # 左側：棋盤
        self.canvas = tk.Canvas(self.game_frame, width=650, height=650, bg="#F5DEB3")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", self.on_resize)
        
        # 右側：面板
        self.info_panel = tk.Frame(self.game_frame, width=300, bg="#dddddd")
        self.info_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lbl_status = tk.Label(self.info_panel, text="準備開始", font=("微軟正黑體", 16), bg="#dddddd")
        self.lbl_status.pack(pady=20)
        
        self.lbl_timer = tk.Label(self.info_panel, text=f"時間: {TIME_LIMIT}", font=("Arial", 20, "bold"), fg="red", bg="#dddddd")
        self.lbl_timer.pack(pady=10)
        
        self.lbl_diff_display = tk.Label(self.info_panel, text="", font=("微軟正黑體", 12), fg="blue", bg="#dddddd")
        self.lbl_diff_display.pack(pady=5)
        
        tk.Button(self.info_panel, text="悔棋 (Undo)", command=self.undo_move).pack(fill=tk.X, padx=10, pady=5)
        tk.Button(self.info_panel, text="回到主選單", command=self.back_to_menu).pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.info_panel, text="--- 聊天室 ---", bg="#dddddd").pack(pady=(20, 5))
        self.chat_area = scrolledtext.ScrolledText(self.info_panel, height=15, width=25, state='disabled')
        self.chat_area.pack(padx=5)
        
        self.entry_msg = tk.Entry(self.info_panel)
        self.entry_msg.pack(fill=tk.X, padx=5, pady=5)
        self.entry_msg.bind("<Return>", self.send_chat)
        tk.Button(self.info_panel, text="發送訊息", command=self.send_chat).pack(pady=5)

    def show_frame(self, frame_name):
        self.menu_frame.pack_forget()
        self.diff_frame.pack_forget()
        self.game_frame.pack_forget()
        
        if frame_name == "MENU":
            self.menu_frame.pack(fill="both", expand=True)
        elif frame_name == "DIFFICULTY":
            self.diff_frame.pack(fill="both", expand=True)
        elif frame_name == "GAME":
            self.game_frame.pack(fill="both", expand=True)
            self.reset_game()
            self.draw_board()

    # ================= 特效系統 (新功能) =================

    def start_fireworks(self):
        """ 勝利煙火特效 """
        if not self.game_over: return
        self.effect_running = True
        
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF']
        
        def create_explosion():
            if not self.effect_running: return
            # 隨機中心點
            cx = random.randint(50, 600)
            cy = random.randint(50, 600)
            color = random.choice(colors)
            
            # 產生多個粒子
            for _ in range(20):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 6)
                dx = math.cos(angle) * speed
                dy = math.sin(angle) * speed
                self.animate_particle(cx, cy, dx, dy, color, 20)
            
            # 隨機時間後產生下一個煙火
            self.root.after(random.randint(300, 800), create_explosion)

        create_explosion()

    def animate_particle(self, x, y, dx, dy, color, life):
        """ 移動單個煙火粒子 """
        if life <= 0 or not self.effect_running: return
        
        # 畫粒子
        item = self.canvas.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color, tags="effect")
        
        # 下一幀的位置
        new_x = x + dx
        new_y = y + dy + 0.1 # 加一點重力
        
        # 50ms 後更新
        self.root.after(50, lambda: self.update_particle(item, new_x, new_y, dx, dy, color, life-1))

    def update_particle(self, item, x, y, dx, dy, color, life):
        self.canvas.delete(item) # 清除上一幀
        self.animate_particle(x, y, dx, dy, color, life)

    def start_rain(self):
        """ 失敗下雨特效 """
        if not self.game_over: return
        self.effect_running = True
        
        def create_rain():
            if not self.effect_running: return
            
            # 產生雨滴
            x = random.randint(0, 650)
            y = -10
            length = random.randint(10, 20)
            speed = random.randint(10, 20)
            
            self.animate_raindrop(x, y, length, speed)
            
            # 密集產生
            self.root.after(20, create_rain)
            
        create_rain()

    def animate_raindrop(self, x, y, length, speed):
        if y > 700 or not self.effect_running: return # 超出畫面就停止
        
        item = self.canvas.create_line(x, y, x, y+length, fill="#708090", width=1, tags="effect")
        
        self.root.after(30, lambda: self.update_raindrop(item, x, y+speed, length, speed))

    def update_raindrop(self, item, x, y, length, speed):
        self.canvas.delete(item)
        self.animate_raindrop(x, y, length, speed)

    def clear_effects(self):
        """ 清除所有特效 """
        self.effect_running = False
        self.canvas.delete("effect") # 刪除所有標籤為 effect 的圖形

    # ================= 遊戲邏輯 =================

    def ask_nickname(self):
        """ 詢問暱稱 """
        name = simpledialog.askstring("輸入暱稱", "請輸入你的大名：", parent=self.root)
        if name:
            self.player_name = name
        else:
            self.player_name = "玩家"
        return self.player_name

    def go_to_difficulty_select(self):
        self.ask_nickname() # 先問名字
        self.show_frame("DIFFICULTY")

    def start_pve(self, level):
        self.mode = "PVE"
        self.difficulty = level
        self.lbl_diff_display.config(text=f"玩家: {self.player_name} | 難度: {level}")
        self.show_frame("GAME")
        self.start_timer()

    def setup_online(self):
        self.ask_nickname() # 先問名字
        ip = simpledialog.askstring("連線", "輸入伺服器 IP (本機測試輸入 127.0.0.1):", initialvalue="127.0.0.1")
        if not ip: return
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, 5555))
            self.mode = "PVP"
            self.difficulty = "PVP"
            self.lbl_diff_display.config(text=f"玩家: {self.player_name} (連線中)")
            t = threading.Thread(target=self.receive_data, daemon=True)
            t.start()
            self.show_frame("GAME")
            self.lbl_status.config(text="連線中...等待對手")
        except Exception as e:
            messagebox.showerror("錯誤", f"無法連線: {e}")

    def reset_game(self):
        self.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.history = []
        self.current_player = 1
        self.game_over = False
        self.timer_seconds = TIME_LIMIT
        self.chat_area.config(state='normal')
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state='disabled')
        self.clear_effects() # 重置時清除特效

    def back_to_menu(self):
        if self.socket:
            self.socket.close()
            self.socket = None
        self.clear_effects()
        self.show_frame("MENU")

    def start_timer(self):
        if self.game_over: return
        if self.mode == "PVE" and self.current_player == 2: return 
        self.lbl_timer.config(text=f"時間: {self.timer_seconds}")
        if self.timer_seconds <= 0:
            self.handle_timeout()
            return
        self.timer_seconds -= 1
        self.root.after(1000, self.start_timer)

    def handle_timeout(self):
        if self.game_over: return
        self.game_over = True
        winner = "白棋" if self.current_player == 1 else "黑棋"
        messagebox.showinfo("時間到", f"時間到！{winner} 獲勝！")
        # 觸發特效 (時間到判負)
        if self.current_player == 1: self.start_rain() # 玩家輸
        else: self.start_fireworks() # 玩家贏

    def make_move(self, r, c):
        self.board[r][c] = self.current_player
        self.history.append((r, c))
        self.draw_board()
        
        win_info = self.check_win(r, c, self.current_player)
        if win_info:
            self.game_over = True
            self.draw_win_line(win_info)
            
            # === 判斷要放煙火還是下雨 ===
            is_player_win = False
            if self.mode == "PVE":
                if self.current_player == 1: is_player_win = True
            elif self.mode == "PVP":
                if self.current_player == self.my_color: is_player_win = True
            
            if is_player_win:
                self.lbl_status.config(text=f"恭喜 {self.player_name} 獲勝！")
                self.start_fireworks()
                messagebox.showinfo("遊戲結束", "恭喜獲勝！")
            else:
                self.lbl_status.config(text="遺憾落敗...")
                self.start_rain()
                messagebox.showinfo("遊戲結束", "你輸了...")
        else:
            self.current_player = 3 - self.current_player
            self.timer_seconds = TIME_LIMIT 
            self.update_status()
            if not (self.mode == "PVE" and self.current_player == 2):
                self.start_timer()

    def update_status(self):
        turn_text = "黑棋回合" if self.current_player == 1 else "白棋回合"
        if self.mode == "PVP":
            who = "(你)" if self.current_player == self.my_color else "(對手)"
            turn_text += who
        self.lbl_status.config(text=turn_text)

    # ... (其餘繪圖、連線、AI 邏輯與之前相同，為節省篇幅省略重複部分，但請保留原本的邏輯) ...
    # 請確保以下函式存在：check_win, computer_move, evaluate, check_line_strength, undo_move, send_chat, receive_data, log_chat
    # 這裡我將必要的 check_win 和 computer_move 補上確保完整性
    
    def on_click(self, event):
        if self.game_over: return
        if self.mode == "PVE" and self.current_player != 1: return
        if self.mode == "PVP" and self.current_player != self.my_color: return

        c = int((event.x - OFFSET + CELL_SIZE / 2) // CELL_SIZE)
        r = int((event.y - OFFSET + CELL_SIZE / 2) // CELL_SIZE)

        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == 0:
            self.make_move(r, c)
            if self.mode == "PVP" and self.socket:
                self.socket.send(f"MOVE:{r},{c}".encode('utf-8'))
            if not self.game_over and self.mode == "PVE":
                self.root.after(500, self.computer_move)

    def draw_board(self):
        if self.effect_running: return # 特效運作時不重畫背景，以免閃爍
        self.canvas.delete("all")
        for i in range(BOARD_SIZE):
            self.canvas.create_line(OFFSET, OFFSET + i * CELL_SIZE, OFFSET + (BOARD_SIZE-1)*CELL_SIZE, OFFSET + i * CELL_SIZE)
            self.canvas.create_line(OFFSET + i * CELL_SIZE, OFFSET, OFFSET + i * CELL_SIZE, OFFSET + (BOARD_SIZE-1)*CELL_SIZE)
        star_points = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
        for sr, sc in star_points:
             sx, sy = OFFSET + sc * CELL_SIZE, OFFSET + sr * CELL_SIZE
             self.canvas.create_oval(sx-3, sy-3, sx+3, sy+3, fill="black")
        stone_r = CELL_SIZE // 2 - 4
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != 0:
                    cx, cy = OFFSET + c * CELL_SIZE, OFFSET + r * CELL_SIZE
                    color = "black" if self.board[r][c] == 1 else "white"
                    self.canvas.create_oval(cx - stone_r, cy - stone_r, cx + stone_r, cy + stone_r, fill=color)
                    if self.history and (r, c) == self.history[-1]:
                         self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="red", outline="red")
                         
    def draw_win_line(self, win_info):
        r1, c1, r2, c2 = win_info
        x1 = OFFSET + c1 * CELL_SIZE
        y1 = OFFSET + r1 * CELL_SIZE
        x2 = OFFSET + c2 * CELL_SIZE
        y2 = OFFSET + r2 * CELL_SIZE
        self.canvas.create_line(x1, y1, x2, y2, fill="red", width=5, tags="effect")

    def undo_move(self):
        if self.mode == "PVP":
            messagebox.showwarning("提示", "線上對戰禁止悔棋！")
            return
        if len(self.history) < 2: return
        for _ in range(2):
            r, c = self.history.pop()
            self.board[r][c] = 0
        self.draw_board()

    def send_chat(self, event=None):
        if self.mode == "PVE":
            self.log_chat("系統", "跟電腦講話，它不會理你喔...")
            self.entry_msg.delete(0, tk.END)
            return
        msg = self.entry_msg.get()
        if msg and self.socket:
            self.socket.send(f"CHAT:{msg}".encode('utf-8'))
            self.log_chat(self.player_name, msg)
            self.entry_msg.delete(0, tk.END)

    def log_chat(self, sender, msg):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{sender}: {msg}\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def receive_data(self):
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data: break
                if data.startswith("COLOR:"):
                    color = data.split(":")[1]
                    self.my_color = 1 if color == "BLACK" else 2
                    self.root.title(f"五子棋 (線上: {'黑棋' if self.my_color==1 else '白棋'})")
                elif data.startswith("MOVE:"):
                    _, coords = data.split(":")
                    r, c = map(int, coords.split(","))
                    self.make_move(r, c)
                elif data.startswith("CHAT:"):
                    msg = data.split(":", 1)[1]
                    self.log_chat("對手", msg)
            except: break

    def computer_move(self):
        if self.game_over: return
        best_score = -99999
        best_move = (7, 7)
        if self.difficulty == "Easy" and random.random() < 0.3:
            empty = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board[r][c] == 0]
            if empty: self.make_move(*random.choice(empty))
            return
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 0:
                    score = self.evaluate(r, c)
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
        self.make_move(*best_move)

    def evaluate(self, r, c):
        defense_weight = 1.0
        if self.difficulty == "Easy": defense_weight = 0.5
        elif self.difficulty == "Normal": defense_weight = 1.2
        elif self.difficulty == "Hard": defense_weight = 2.0
        atk = self.check_line_strength(r, c, 2)
        dfs = self.check_line_strength(r, c, 1)
        return atk + dfs * defense_weight 

    def check_line_strength(self, r, c, player):
        score = 0
        dirs = [(0,1), (1,0), (1,1), (1,-1)]
        for dr, dc in dirs:
            count = 1
            for step in range(1, 5): 
                nr, nc = r+dr*step, c+dc*step
                if 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and self.board[nr][nc] == player: count+=1
                else: break
            for step in range(1, 5): 
                nr, nc = r-dr*step, c-dc*step
                if 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and self.board[nr][nc] == player: count+=1
                else: break
            if count >= 5: score += 10000
            elif count == 4: score += 1000
            elif count == 3: score += 100
            elif count == 2: score += 10
        return score

    def check_win(self, r, c, player):
        dirs = [(0,1), (1,0), (1,1), (1,-1)]
        for dr, dc in dirs:
            start_r, start_c = r, c
            while 0 <= start_r-dr < BOARD_SIZE and 0 <= start_c-dc < BOARD_SIZE and self.board[start_r-dr][start_c-dc] == player:
                start_r -= dr
                start_c -= dc
            end_r, end_c = r, c
            while 0 <= end_r+dr < BOARD_SIZE and 0 <= end_c+dc < BOARD_SIZE and self.board[end_r+dr][end_c+dc] == player:
                end_r += dr
                end_c += dc
            dist = max(abs(end_r - start_r), abs(end_c - start_c))
            if dist >= 4:
                return (start_r, start_c, end_r, end_c)
        return None
    
    def on_resize(self, event):
        self.draw_board()

if __name__ == "__main__":
    root = tk.Tk()
    app = GomokuApp(root)
    root.mainloop()