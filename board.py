"""
マインスイーパー陣取り合戦 盤面ロジック & 描画モジュール
"""
import random
from collections import deque
import pygame
from settings import (
    BOARD_X, BOARD_Y, BOARD_SIZE,
    COLOR_CELL_UNREVEALED, COLOR_CELL_BORDER, COLOR_CELL_HOVER,
    COLOR_CELL_VALID_TARGET, COLOR_MINE_BG, COLOR_MINE_ICON,
    PLAYER_COLORS, NUMBER_COLORS, COLOR_TEXT
)


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_mine = False
        self.adjacent_mines = 0
        self.is_revealed = False
        self.is_flagged = False  # フラグ（🚩）
        self.flag_owner = None   # 旗を立てたプレイヤーID (1~4)
        self.owner = None  # None: 未開放, 1~4: プレイヤーID, 0: 地雷マス（中立）
        self.reveal_anim = 0.0  # 開放アニメーション用 (0.0 -> 1.0)


class Board:
    def __init__(self, cols, rows, mine_ratio=0.15, only_adjacent_rule=True):
        self.cols = cols
        self.rows = rows
        self.mine_ratio = mine_ratio
        self.only_adjacent_rule = only_adjacent_rule

        # セルサイズの計算（盤面エリアに収まる最大正方形）
        self.cell_size = min(BOARD_SIZE // self.cols, BOARD_SIZE // self.rows)
        self.actual_width = self.cell_size * self.cols
        self.actual_height = self.cell_size * self.rows
        # センタリングオフセット
        self.offset_x = BOARD_X + (BOARD_SIZE - self.actual_width) // 2
        self.offset_y = BOARD_Y + (BOARD_SIZE - self.actual_height) // 2

        self.font = None
        self.mine_font = None
        self.cells = [[Cell(x, y) for x in range(self.cols)] for y in range(self.rows)]
        self.init_board()

    def _init_fonts(self):
        if self.font is None:
            font_size = max(14, int(self.cell_size * 0.65))
            mine_font_size = max(14, int(self.cell_size * 0.7))
            self.font = pygame.font.SysFont("meiryo,msgothic,yugothic,consolas", font_size, bold=True)
            self.banner_font = pygame.font.SysFont("meiryo,msgothic,yugothic,segoeui", 14, bold=True)
            self.mine_font = pygame.font.SysFont("Segoe UI Symbol,meiryo", mine_font_size, bold=True)

    def init_board(self):
        """盤面の再初期化・地雷配置・4隅のスタート地点割り当て"""
        self.cells = [[Cell(x, y) for x in range(self.cols)] for y in range(self.rows)]

        # 4隅のプレイヤー初期位置
        self.corners = {
            1: (0, 0),                          # P1: 左上
            2: (self.cols - 1, 0),              # CPU1: 右上
            3: (0, self.rows - 1),              # CPU2: 左下
            4: (self.cols - 1, self.rows - 1),  # CPU3: 右下
        }

        # 初期マスの周囲も含めて地雷除外エリア（安全地帯）を設定
        safe_zones = set()
        for pid, (cx, cy) in self.corners.items():
            safe_zones.add((cx, cy))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows:
                        safe_zones.add((nx, ny))

        # 地雷の配置
        all_coords = [
            (x, y) for y in range(self.rows) for x in range(self.cols)
            if (x, y) not in safe_zones
        ]
        total_cells = self.cols * self.rows
        mine_count = int(total_cells * self.mine_ratio)
        mine_coords = set(random.sample(all_coords, min(mine_count, len(all_coords))))

        for x, y in mine_coords:
            self.cells[y][x].is_mine = True

        # 各セルの隣接地雷数計算
        for y in range(self.rows):
            for x in range(self.cols):
                if not self.cells[y][x].is_mine:
                    count = 0
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                                if self.cells[ny][nx].is_mine:
                                    count += 1
                    self.cells[y][x].adjacent_mines = count

        # 4隅の初期マスを各陣営の領地としてオープン
        for pid, (cx, cy) in self.corners.items():
            cell = self.cells[cy][cx]
            cell.is_revealed = True
            cell.owner = pid
            cell.reveal_anim = 1.0

    def get_cell(self, x, y):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.cells[y][x]
        return None

    def set_flag(self, x, y, player_id=1, flagged=True):
        """指定マスにフラグを設置 / 解除"""
        cell = self.get_cell(x, y)
        if cell and not cell.is_revealed:
            cell.is_flagged = flagged
            cell.flag_owner = player_id if flagged else None
            return True
        return False

    def toggle_flag(self, x, y, player_id=1):
        """プレイヤーによるフラグ（旗）の付け外し"""
        cell = self.get_cell(x, y)
        if cell and not cell.is_revealed:
            cell.is_flagged = not cell.is_flagged
            cell.flag_owner = player_id if cell.is_flagged else None
            return True
        return False

    def get_adjacent_unrevealed_cells(self, player_id):
        """自陣地に隣接する開拓可能な未開放マスのリストを取得"""
        targets = set()
        for y in range(self.rows):
            for x in range(self.cols):
                if self.cells[y][x].is_revealed and self.cells[y][x].owner == player_id:
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            ncell = self.get_cell(nx, ny)
                            # フラグ（🚩）が立っているマスは地雷予測マスなので、プレイヤー・CPU問わず開拓不可
                            if ncell and not ncell.is_revealed and not ncell.is_flagged:
                                targets.add((nx, ny))
        return list(targets)

    def is_player_isolated(self, player_id):
        """プレイヤーが自陣地に隣接する開拓可能マスを失った（包囲・孤立）か判定"""
        scores = self.get_scores()
        if scores["unrevealed"] == 0:
            return False
        # 開拓可能な隣接未開放マスが0個なら孤立（包囲）
        return len(self.get_adjacent_unrevealed_cells(player_id)) == 0

    def can_reveal(self, player_id, x, y, ignore_flag=False):
        """指定プレイヤーがそのセルを開封可能か判定"""
        cell = self.get_cell(x, y)
        if not cell or cell.is_revealed:
            return False

        # フラグが立っているマスは誰であっても（プレイヤー・CPU問わず）直接開放不可！
        # （コード開放時のみignore_flag=Trueで開放）
        if cell.is_flagged and not ignore_flag:
            return False

        # 「どこでも自由」ルール、または「完全に包囲・孤立された場合」は盤面のどこでも開けられる（ブレイクアウト）
        if not self.only_adjacent_rule or self.is_player_isolated(player_id):
            return True

        # 隣接マスのみルール: 自陣隣接の未開放マスか
        return (x, y) in self.get_adjacent_unrevealed_cells(player_id)

    def get_openable_cells(self, player_id):
        """指定プレイヤーが開けられる未開放マス一覧を取得"""
        scores = self.get_scores()
        if scores["unrevealed"] == 0:
            return []

        # どこでもルール、または包囲・孤立時は、未開放かつフラグなしの全マスを開拓可能とする
        if not self.only_adjacent_rule or self.is_player_isolated(player_id):
            openable = []
            for y in range(self.rows):
                for x in range(self.cols):
                    cell = self.cells[y][x]
                    if not cell.is_revealed and not cell.is_flagged:
                        openable.append((x, y))
            return openable

        # 通常の隣接マスルール
        return self.get_adjacent_unrevealed_cells(player_id)

    def chord_reveal(self, player_id, x, y):
        """
        数字マスダブルクリックによるコード開放（Chording）
        周囲の「フラグ数 ＋ 爆破済み地雷数」が数字と一致している場合、周囲のフラグなし未開放マスを一括開放
        """
        center_cell = self.get_cell(x, y)
        if not center_cell or not center_cell.is_revealed or center_cell.adjacent_mines == 0:
            return None

        # 自分の領地マス（またはブレイクアウト時）のみコード可能
        if self.only_adjacent_rule and center_cell.owner != player_id and not self.is_player_isolated(player_id):
            return None

        # 周囲の「フラグマス」および「爆破済み地雷（owner == 0）」をカウント
        identified_mines = 0
        targets = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                ncell = self.get_cell(nx, ny)
                if not ncell:
                    continue

                if ncell.is_revealed:
                    # 爆破済みの地雷マス（owner == 0）を特定済み地雷としてカウント！
                    if ncell.owner == 0:
                        identified_mines += 1
                else:
                    # 未開放マスのうち、フラグが立っているものは特定済み地雷、立っていないものは開放対象
                    if ncell.is_flagged:
                        identified_mines += 1
                    else:
                        targets.append((nx, ny))

        # 特定済み地雷数（フラグ＋爆破済み地雷）とマスの数字が一致していれば一括開放
        if identified_mines == center_cell.adjacent_mines and targets:
            results = []
            for tx, ty in targets:
                res = self.reveal_cell(player_id, tx, ty, ignore_flag=True)
                results.append(res)
            return results

        return None

    def reveal_cell(self, player_id, x, y, ignore_flag=False):
        """セルを開放する（地雷判定、フラッドフィル連鎖開放）"""
        if not self.can_reveal(player_id, x, y, ignore_flag=ignore_flag):
            return {"status": "invalid"}

        target = self.cells[y][x]
        target.is_flagged = False  # 開いたマスはフラグ解除

        # 地雷を踏んだ場合
        if target.is_mine:
            target.is_revealed = True
            target.owner = 0  # 地雷は誰の陣地でもない（障害物）
            target.reveal_anim = 1.0
            return {
                "status": "mine",
                "coord": (x, y),
                "opened": [(x, y)]
            }

        # 安全マスを開放
        opened_cells = []
        queue = deque([(x, y)])
        visited = set([(x, y)])

        # 1回の連鎖開放の上限数（大味な一気染めを防ぎ、駆け引きを維持）
        MAX_CHAIN = 10

        while queue and len(opened_cells) < MAX_CHAIN:
            cx, cy = queue.popleft()
            cell = self.cells[cy][cx]
            cell.is_revealed = True
            cell.owner = player_id
            cell.is_flagged = False
            cell.reveal_anim = 1.0
            opened_cells.append((cx, cy))

            # 0マス（周囲に地雷なし）の場合、隣接する未開封マスを連鎖開放
            if cell.adjacent_mines == 0:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = cx + dx, cy + dy
                        ncell = self.get_cell(nx, ny)
                        if ncell and not ncell.is_revealed and not ncell.is_mine:
                            # 他プレイヤーの初期位置から距離3以内のエリアは連鎖侵入をブロック
                            too_close_to_enemy = False
                            for other_pid, (ocx, ocy) in self.corners.items():
                                if other_pid != player_id:
                                    dist = abs(nx - ocx) + abs(ny - ocy)
                                    if dist <= 3:
                                        too_close_to_enemy = True
                                        break

                            if not too_close_to_enemy and (nx, ny) not in visited:
                                visited.add((nx, ny))
                                queue.append((nx, ny))

        return {
            "status": "safe",
            "coord": (x, y),
            "opened": opened_cells,
            "count": len(opened_cells)
        }

    def get_cell_at_pos(self, mouse_pos):
        """スクリーン座標からグリッド座標(x, y)を取得"""
        mx, my = mouse_pos
        rel_x = mx - self.offset_x
        rel_y = my - self.offset_y
        if 0 <= rel_x < self.actual_width and 0 <= rel_y < self.actual_height:
            return rel_x // self.cell_size, rel_y // self.cell_size
        return None

    def get_scores(self):
        """各プレイヤーの獲得マス数および盤面集計"""
        scores = {1: 0, 2: 0, 3: 0, 4: 0, "mine": 0, "unrevealed": 0}
        for y in range(self.rows):
            for x in range(self.cols):
                c = self.cells[y][x]
                if not c.is_revealed:
                    scores["unrevealed"] += 1
                elif c.owner == 0:
                    scores["mine"] += 1
                elif c.owner in scores:
                    scores[c.owner] += 1
        return scores

    def is_game_finished(self):
        """全マスが開いた、または誰も開けられるマスがなくなったか判定"""
        scores = self.get_scores()
        if scores["unrevealed"] == 0:
            return True

        # いずれかのプレイヤーが開けられるマスが残っているか
        for pid in (1, 2, 3, 4):
            if len(self.get_openable_cells(pid)) > 0:
                return False
        return True

    def draw(self, surface, hover_cell=None, active_player_id=1, show_valid_targets=True):
        """盤面全体の描画"""
        self._init_fonts()

        # 盤面の外枠・土台
        bg_rect = pygame.Rect(self.offset_x - 4, self.offset_y - 4,
                              self.actual_width + 8, self.actual_height + 8)
        pygame.draw.rect(surface, (20, 27, 45), bg_rect, border_radius=6)
        pygame.draw.rect(surface, (51, 65, 85), bg_rect, width=2, border_radius=6)

        valid_targets = set()
        is_isolated = self.only_adjacent_rule and self.is_player_isolated(active_player_id)
        if show_valid_targets and active_player_id:
            valid_targets = set(self.get_openable_cells(active_player_id))

        # 孤立ブレイクアウト中のバナー表示
        if is_isolated and show_valid_targets:
            banner_rect = pygame.Rect(self.offset_x, max(6, self.offset_y - 28), self.actual_width, 24)
            pygame.draw.rect(surface, (234, 88, 12), banner_rect, border_radius=4)
            pygame.draw.rect(surface, (251, 191, 36), banner_rect, width=1, border_radius=4)
            banner_surf = self.banner_font.render("BREAKOUT! 包囲脱出: 盤面のどこでも開拓可能!", True, (255, 255, 255))
            surface.blit(banner_surf, banner_surf.get_rect(center=banner_rect.center))

        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.cells[y][x]
                px = self.offset_x + x * self.cell_size
                py = self.offset_y + y * self.cell_size
                rect = pygame.Rect(px, py, self.cell_size, self.cell_size)

                # 未開放マスの描画
                if not cell.is_revealed:
                    # ホバー判定
                    is_hovered = (hover_cell == (x, y))
                    color = COLOR_CELL_HOVER if is_hovered else COLOR_CELL_UNREVEALED
                    pygame.draw.rect(surface, color, rect)

                    # フラグ（🚩）の描画
                    if cell.is_flagged:
                        p_owner = cell.flag_owner or 1
                        flag_color = PLAYER_COLORS.get(p_owner, PLAYER_COLORS[1])["bright"]
                        flag_surf = self.mine_font.render("🚩", True, flag_color)
                        if flag_surf.get_width() <= 2:
                            flag_surf = self.font.render("P", True, flag_color)
                        f_rect = flag_surf.get_rect(center=rect.center)
                        surface.blit(flag_surf, f_rect)
                        pygame.draw.rect(surface, flag_color, rect, width=1)
                    # 開放可能マスのハイライト枠（フラグが立っていない場合）
                    elif (x, y) in valid_targets:
                        # プレイヤーのテーマ色で微かなドット/枠線を描画
                        pcolor = PLAYER_COLORS[active_player_id]["main"]
                        inner_rect = rect.inflate(-4, -4)
                        pygame.draw.rect(surface, pcolor, inner_rect, width=1)
                        if is_hovered:
                            pygame.draw.rect(surface, (255, 255, 255), rect, width=2)
                    else:
                        pygame.draw.rect(surface, COLOR_CELL_BORDER, rect, width=1)

                else:
                    # 開放済みマスの描画
                    if cell.owner == 0:
                        # 地雷マス
                        pygame.draw.rect(surface, COLOR_MINE_BG, rect)
                        pygame.draw.rect(surface, (185, 28, 28), rect, width=1)
                        # 地雷マーク（✕ または 💣）
                        mine_surf = self.mine_font.render("💣", True, COLOR_MINE_ICON)
                        # フォントが絵文字非対応の場合のフォールバック
                        if mine_surf.get_width() <= 2:
                            mine_surf = self.font.render("X", True, (255, 100, 100))
                        m_rect = mine_surf.get_rect(center=rect.center)
                        surface.blit(mine_surf, m_rect)
                    else:
                        # 領地マス
                        p_info = PLAYER_COLORS.get(cell.owner, PLAYER_COLORS[1])
                        # 領地背景色（プレイヤーカラーの濃淡）
                        base_col = p_info["dark"]
                        pygame.draw.rect(surface, base_col, rect)
                        # 内側に少し明るいボーダー
                        inner_rect = rect.inflate(-2, -2)
                        pygame.draw.rect(surface, p_info["main"], inner_rect, width=1)

                        # 数字ヒントの描画
                        if cell.adjacent_mines > 0:
                            num = cell.adjacent_mines
                            num_color = NUMBER_COLORS.get(num, COLOR_TEXT)
                            num_surf = self.font.render(str(num), True, num_color)
                            n_rect = num_surf.get_rect(center=rect.center)
                            surface.blit(num_surf, n_rect)
                        else:
                            # 0マスは小さめのドットで視認性を上げる
                            center_x, center_y = rect.center
                            pygame.draw.circle(surface, (p_info["main"][0]//2, p_info["main"][1]//2, p_info["main"][2]//2),
                                               (center_x, center_y), max(2, self.cell_size // 8))
