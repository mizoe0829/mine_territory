"""
マインスイーパー風リアルタイム陣取り合戦ゲーム (Minesweeper Wars)
メインエントリーポイント
"""
import sys
import math
import random
import pygame

from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    COLOR_BG, DIFFICULTY_PRESETS
)
from board import Board
from player import HumanPlayer, CPUPlayer
from ui import UI


class Particle:
    def __init__(self, x, y, color, count=12, speed_range=(2.0, 6.0), lifespan=0.6):
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2.0, 5.0)
            self.particles.append({
                "x": x, "y": y,
                "vx": vx, "vy": vy,
                "size": size,
                "color": color,
                "life": lifespan,
                "max_life": lifespan
            })

    def update(self, dt):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= dt
            p["size"] = max(0.5, p["size"] * 0.96)
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surface):
        for p in self.particles:
            alpha = int(255 * (p["life"] / p["max_life"]))
            color = p["color"]
            # 半透明描画
            s = pygame.Surface((int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color[:3], alpha), (int(p["size"]), int(p["size"])), int(p["size"]))
            surface.blit(s, (int(p["x"] - p["size"]), int(p["y"] - p["size"])))

    @property
    def is_dead(self):
        return len(self.particles) == 0


class MinesweeperWarsGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Minesweeper Wars - マインスイーパー陣取り合戦")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.current_difficulty = "normal"
        self.only_adjacent_rule = True
        self.elapsed_time = 0.0
        self.game_over = False
        self.particles = []

        self.ui = UI(
            on_change_difficulty=self.change_difficulty,
            on_toggle_rule=self.toggle_rule,
            on_restart=self.start_new_game
        )

        self.board = None
        self.players = {}
        self.last_click_time = 0
        self.last_click_cell = None
        self.start_new_game()

    def start_new_game(self):
        preset = DIFFICULTY_PRESETS[self.current_difficulty]
        self.board = Board(
            cols=preset["cols"],
            rows=preset["rows"],
            mine_ratio=preset["mine_ratio"],
            only_adjacent_rule=self.only_adjacent_rule
        )

        # プレイヤー初期化
        self.players = {
            1: HumanPlayer(1, "Player (You)"),
            2: CPUPlayer(2, difficulty=self.current_difficulty, speed_frames=preset["cpu_speed"]),
            3: CPUPlayer(3, difficulty=self.current_difficulty, speed_frames=preset["cpu_speed"]),
            4: CPUPlayer(4, difficulty=self.current_difficulty, speed_frames=preset["cpu_speed"]),
        }

        self.elapsed_time = 0.0
        self.game_over = False
        self.particles.clear()

    def change_difficulty(self, diff_key):
        if diff_key in DIFFICULTY_PRESETS:
            self.current_difficulty = diff_key
            self.start_new_game()

    def toggle_rule(self):
        self.only_adjacent_rule = not self.only_adjacent_rule
        self.board.only_adjacent_rule = self.only_adjacent_rule

    def spawn_mine_effect(self, grid_x, grid_y):
        """地雷被弾時の爆発パーティクル"""
        px = self.board.offset_x + grid_x * self.board.cell_size + self.board.cell_size // 2
        py = self.board.offset_y + grid_y * self.board.cell_size + self.board.cell_size // 2
        self.particles.append(Particle(px, py, (248, 113, 113), count=25, speed_range=(3.0, 8.0), lifespan=0.8))
        self.particles.append(Particle(px, py, (251, 191, 36), count=15, speed_range=(2.0, 5.0), lifespan=0.5))

    def spawn_claim_effect(self, opened_coords, player_id):
        """領地獲得時のきらめきパーティクル"""
        pcolor = self.players[player_id].color_info["bright"]
        for (gx, gy) in opened_coords[:5]:  # 大量連鎖時は代表数箇所
            px = self.board.offset_x + gx * self.board.cell_size + self.board.cell_size // 2
            py = self.board.offset_y + gy * self.board.cell_size + self.board.cell_size // 2
            self.particles.append(Particle(px, py, pcolor, count=6, speed_range=(1.0, 3.0), lifespan=0.4))

    def handle_player_click(self, mouse_pos):
        if self.game_over:
            return

        human = self.players[1]
        if human.is_stunned:
            return  # スタン中は操作不能

        cell_coord = self.board.get_cell_at_pos(mouse_pos)
        if not cell_coord:
            return

        x, y = cell_coord
        cell = self.board.get_cell(x, y)
        if not cell:
            return

        # 未開放マスを開く
        if not cell.is_revealed:
            if not self.board.can_reveal(1, x, y):
                return

            result = self.board.reveal_cell(1, x, y)
            if result["status"] == "mine":
                human.trigger_stun()
                self.spawn_mine_effect(x, y)
            elif result["status"] == "safe":
                self.spawn_claim_effect(result["opened"], 1)

            self.check_game_over()

    def handle_player_right_click(self, mouse_pos):
        """右クリックでフラグ（🚩）を立てる / 解除する"""
        if self.game_over:
            return

        human = self.players[1]
        if human.is_stunned:
            return

        cell_coord = self.board.get_cell_at_pos(mouse_pos)
        if not cell_coord:
            return

        x, y = cell_coord
        self.board.toggle_flag(x, y)

    def handle_player_double_click(self, cell_coord):
        """ダブルクリックによるコード開放（Chording）またはマス開放"""
        if self.game_over:
            return

        human = self.players[1]
        if human.is_stunned:
            return

        x, y = cell_coord
        cell = self.board.get_cell(x, y)
        if not cell:
            return

        # 開放済み数字マスの場合: コード開放（周囲のフラグ数と一致していれば周囲の安全マスを一括開放）
        if cell.is_revealed:
            results = self.board.chord_reveal(1, x, y)
            if results:
                hit_mine = False
                all_opened = []
                for res in results:
                    if res["status"] == "mine":
                        hit_mine = True
                        mx, my = res["coord"]
                        self.spawn_mine_effect(mx, my)
                    elif res["status"] == "safe":
                        all_opened.extend(res["opened"])

                if hit_mine:
                    human.trigger_stun()
                if all_opened:
                    self.spawn_claim_effect(all_opened, 1)

                self.check_game_over()
        else:
            # 未開放マスの場合は通常の開放を試みる
            self.handle_player_click(
                (self.board.offset_x + x * self.board.cell_size + 2,
                 self.board.offset_y + y * self.board.cell_size + 2)
            )

    def update_cpus(self, dt):
        if self.game_over:
            return

        for pid in (2, 3, 4):
            cpu = self.players[pid]
            action_cell = cpu.update(dt, self.board)
            if action_cell:
                ax, ay = action_cell
                res = self.board.reveal_cell(pid, ax, ay)
                if res["status"] == "mine":
                    cpu.trigger_stun()
                    self.spawn_mine_effect(ax, ay)
                elif res["status"] == "safe":
                    self.spawn_claim_effect(res["opened"], pid)

        self.check_game_over()

    def check_game_over(self):
        if not self.game_over and self.board.is_game_finished():
            self.game_over = True

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # 秒単位
            if not self.game_over:
                self.elapsed_time += dt

            # プレイヤー（Human）のスタン更新
            self.players[1].update(dt)

            # CPUの思考・更新
            self.update_cpus(dt)

            # パーティクル更新
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if not p.is_dead]

            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.start_new_game()
                    elif event.key == pygame.K_SPACE and self.game_over:
                        self.start_new_game()
                    elif event.key == pygame.K_1:
                        self.change_difficulty("easy")
                    elif event.key == pygame.K_2:
                        self.change_difficulty("normal")
                    elif event.key == pygame.K_3:
                        self.change_difficulty("hard")

                # UIイベント処理
                ui_handled = self.ui.handle_event(event)
                if not ui_handled and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # 左クリック（シングル / ダブルクリック判定）
                        now = pygame.time.get_ticks()
                        cell_coord = self.board.get_cell_at_pos(event.pos)
                        if cell_coord:
                            if cell_coord == self.last_click_cell and (now - self.last_click_time) < 400:
                                # ダブルクリック発動
                                self.handle_player_double_click(cell_coord)
                                self.last_click_time = 0
                                self.last_click_cell = None
                            else:
                                self.last_click_time = now
                                self.last_click_cell = cell_coord
                                self.handle_player_click(event.pos)
                        else:
                            self.last_click_time = 0
                            self.last_click_cell = None

                    elif event.button == 3:
                        # 右クリック（フラグの設置/解除）
                        self.handle_player_right_click(event.pos)

                    elif event.button == 2:
                        # 中クリック（ホイールクリック）でもコード開放
                        cell_coord = self.board.get_cell_at_pos(event.pos)
                        if cell_coord:
                            self.handle_player_double_click(cell_coord)

            # 描画
            self.screen.fill(COLOR_BG)

            # マウス位置のセル
            mpos = pygame.mouse.get_pos()
            hover_cell = self.board.get_cell_at_pos(mpos)

            # 盤面描画
            self.board.draw(
                self.screen,
                hover_cell=hover_cell,
                active_player_id=1,
                show_valid_targets=(not self.players[1].is_stunned and not self.game_over)
            )

            # パーティクル描画
            for p in self.particles:
                p.draw(self.screen)

            # サイドパネル描画
            self.ui.draw_side_panel(
                self.screen,
                self.board,
                self.players,
                self.current_difficulty,
                self.elapsed_time
            )

            # リザルトモーダル
            if self.game_over:
                self.ui.draw_game_over_modal(self.screen, self.board, self.players)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = MinesweeperWarsGame()
    game.run()
