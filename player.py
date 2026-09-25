"""
プレイヤーおよびCPUのロジックモジュール
"""
import random
from settings import (
    STUN_PENALTY_SECONDS, PLAYER_COLORS
)


class PlayerBase:
    def __init__(self, player_id, name=None):
        self.player_id = player_id
        self.color_info = PLAYER_COLORS[player_id]
        self.name = name or self.color_info["name"]
        self.stun_timer = 0.0  # スタン残り秒数
        self.score = 1         # 初期マス1つ
        self.mines_triggered = 0

    @property
    def is_stunned(self):
        return self.stun_timer > 0.0

    def trigger_stun(self, penalty=STUN_PENALTY_SECONDS):
        self.stun_timer = penalty
        self.mines_triggered += 1

    def update(self, dt):
        """dt: 経過秒数"""
        if self.stun_timer > 0.0:
            self.stun_timer = max(0.0, self.stun_timer - dt)


class HumanPlayer(PlayerBase):
    def __init__(self, player_id=1, name="Player (You)"):
        super().__init__(player_id, name)


class CPUPlayer(PlayerBase):
    def __init__(self, player_id, difficulty="normal", speed_frames=25):
        super().__init__(player_id)
        self.difficulty = difficulty
        self.base_cooldown = speed_frames / 60.0  # 秒数に変換
        # 少しランダムな揺らぎ（人間らしさ）を持たせる
        self.cooldown_timer = random.uniform(0.1, self.base_cooldown)

    def set_difficulty(self, difficulty, speed_frames):
        self.difficulty = difficulty
        self.base_cooldown = speed_frames / 60.0

    def update(self, dt, board=None):
        super().update(dt)

        if self.is_stunned or board is None:
            return None

        # Normal / HardのCPUは周囲の確定地雷を論理推論してフラグ（🚩）を立てる
        if self.difficulty in ("normal", "hard"):
            self._deduce_and_flag_mines(board)

        self.cooldown_timer -= dt
        if self.cooldown_timer <= 0.0:
            # 行動を実行
            target_cell = self.choose_action(board)

            # 次のクールダウン時間を設定
            if self.difficulty == "easy":
                # Easy: のんびり思考（たまに長考してプレイヤーに余裕を与える）
                hesitation = random.uniform(1.0, 2.0) if random.random() < 0.25 else 0.0
                jitter = random.uniform(0.9, 1.4)
                self.cooldown_timer = (self.base_cooldown * jitter) + hesitation
            else:
                jitter = random.uniform(0.8, 1.2)
                self.cooldown_timer = self.base_cooldown * jitter

            return target_cell

        return None

    def _deduce_and_flag_mines(self, board):
        """自陣地の数字ヒントから確定地雷を推論し、自陣カラーのフラグ（🚩）を立てる"""
        for y in range(board.rows):
            for x in range(board.cols):
                cell = board.cells[y][x]
                # 自陣地（自分が領有するマス）の数字ヒントのみから推論！他陣地に勝手に旗を立てない
                if cell.is_revealed and cell.owner == self.player_id and cell.adjacent_mines > 0:
                    hint = cell.adjacent_mines
                    flagged_mines = 0
                    unrevealed_unknowns = []

                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            ncell = board.get_cell(nx, ny)
                            if not ncell:
                                continue
                            if ncell.is_revealed:
                                if ncell.owner == 0:
                                    flagged_mines += 1
                            else:
                                if ncell.is_flagged:
                                    flagged_mines += 1
                                else:
                                    unrevealed_unknowns.append((nx, ny))

                    # 残り地雷数と未開放マス数が一致していれば、すべて100%確定地雷！
                    remaining = hint - flagged_mines
                    if remaining > 0 and remaining == len(unrevealed_unknowns):
                        for (ux, uy) in unrevealed_unknowns:
                            board.set_flag(ux, uy, player_id=self.player_id, flagged=True)

    def choose_action(self, board):
        """難易度に応じたマス選択ロジック"""
        openable = board.get_openable_cells(self.player_id)
        if not openable:
            return None

        # フラグ（🚩）が立っているマスは完全に除外。候補がなければ待機（自爆特攻は絶対にしない）
        valid_candidates = [c for c in openable if not board.get_cell(c[0], c[1]).is_flagged]
        if not valid_candidates:
            return None

        candidates = valid_candidates

        if self.difficulty == "easy":
            # Easy: フラグマス以外の候補からランダム選択
            return random.choice(candidates)

        # Normal / Hard: 数字ヒントを考慮した確率的思考
        cell_scores = []
        for (cx, cy) in candidates:
            danger = self._calculate_cell_danger(board, cx, cy)
            cell_scores.append(((cx, cy), danger))

        # 危険度でソート（危険度が低いものが安全）
        cell_scores.sort(key=lambda x: x[1])

        # 【超重要】最も安全なマスでも「確定地雷（danger >= 0.99）」の場合！
        # 終盤に全員で確定地雷に順々に自爆特攻するのを防ぎ、フラグを立てて平和に待機する
        min_danger = cell_scores[0][1]
        if min_danger >= 0.99:
            for (cx, cy), d in cell_scores:
                if d >= 0.99:
                    board.set_flag(cx, cy, player_id=self.player_id, flagged=True)
            return None

        # 安全なマスのみに絞る（確定地雷は除外）
        safe_scores = [item for item in cell_scores if item[1] < 0.99]
        if not safe_scores:
            return None

        if self.difficulty == "normal":
            # 安全度トップグループからランダムに選ぶ
            min_d = safe_scores[0][1]
            best_group = [c for c, d in safe_scores if d <= min_d + 0.15]
            return random.choice(best_group)

        elif self.difficulty == "hard":
            # Hard: 完全に最も安全なマス、同率なら中央に近いマスを選ぶ
            min_d = safe_scores[0][1]
            best_candidates = [c for c, d in safe_scores if abs(d - min_d) < 0.001]

            # 盤面中央 (center_x, center_y) に近いマスを優先（領地を積極的に中央へ広げる）
            center_x = board.cols / 2.0
            center_y = board.rows / 2.0

            best_candidates.sort(
                key=lambda pos: (pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2
            )
            return best_candidates[0]

        return random.choice([c for c, d in safe_scores])

    def _calculate_cell_danger(self, board, x, y):
        """
        対象マス(x, y)の周囲の開放済みマスの数字ヒントから
        地雷である推定確率（危険度スコア 0.0〜1.0）を算出する
        """
        cell = board.get_cell(x, y)
        if cell and cell.is_flagged:
            return 1.0  # フラグマス自体の危険度は最大

        estimates = []

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                neighbor = board.get_cell(nx, ny)
                if neighbor and neighbor.is_revealed and neighbor.owner != 0:
                    # 開放済みかつ数字のあるマス
                    hint_mines = neighbor.adjacent_mines
                    # この周囲の「既知の地雷（爆破済み＋フラグ）」と「未知の未開放マス」をカウント
                    flagged_mines = 0
                    unrevealed_neighbors = 0

                    for ndx in (-1, 0, 1):
                        for ndy in (-1, 0, 1):
                            if ndx == 0 and ndy == 0:
                                continue
                            nnx, nny = nx + ndx, ny + ndy
                            nn_cell = board.get_cell(nnx, nny)
                            if nn_cell:
                                if nn_cell.is_revealed and nn_cell.owner == 0:
                                    flagged_mines += 1
                                elif not nn_cell.is_revealed:
                                    if nn_cell.is_flagged:
                                        flagged_mines += 1  # プレイヤーの立てたフラグも特定地雷として認識
                                    else:
                                        unrevealed_neighbors += 1

                    remaining_mines = max(0, hint_mines - flagged_mines)
                    if unrevealed_neighbors > 0:
                        prob = remaining_mines / unrevealed_neighbors
                        estimates.append(prob)

        if not estimates:
            # 周囲に数字ヒントがない未開拓地の場合は、全体地雷率を基準にする
            return board.mine_ratio

        # 最悪ケース（隣接ヒントの中で最大の地雷推定確率）をそのマスの危険度とする
        return max(estimates)
