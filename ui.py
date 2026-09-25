"""
UI描画コンポーネント（サイドパネル、スコア、難易度切替、リザルト画面等）
"""
import pygame
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_BG, COLOR_PANEL_BG, COLOR_PANEL_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, PLAYER_COLORS,
    DIFFICULTY_PRESETS
)


class Button:
    def __init__(self, rect, text, callback, active=False, bg_color=None, active_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.active = active
        self.bg_color = bg_color or (51, 65, 85)
        self.active_color = active_color or (14, 165, 233)
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface, font):
        color = self.active_color if self.active else (
            (71, 85, 105) if self.hovered else self.bg_color
        )
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        if self.active or self.hovered:
            pygame.draw.rect(surface, (255, 255, 255), self.rect, width=1, border_radius=6)
        else:
            pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, width=1, border_radius=6)

        txt_color = (255, 255, 255) if (self.active or self.hovered) else COLOR_TEXT
        txt_surf = font.render(self.text, True, txt_color)
        t_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, t_rect)


class UI:
    def __init__(self, on_change_difficulty, on_toggle_rule, on_restart):
        self.on_change_difficulty = on_change_difficulty
        self.on_toggle_rule = on_toggle_rule
        self.on_restart = on_restart

        self.font_title = None
        self.font_bold = None
        self.font_regular = None
        self.font_small = None

        self.buttons = []
        self._setup_buttons()

    def _init_fonts(self):
        if self.font_title is None:
            font_family = "meiryo,msgothic,yugothic,segoeui,sans-serif"
            self.font_title = pygame.font.SysFont(font_family, 22, bold=True)
            self.font_bold = pygame.font.SysFont(font_family, 15, bold=True)
            self.font_regular = pygame.font.SysFont(font_family, 13)
            self.font_small = pygame.font.SysFont(font_family, 11)

    def _setup_buttons(self):
        # 難易度ボタン (Easy, Normal, Hard)
        btn_y = 490
        btn_w = 90
        btn_h = 32

        self.diff_buttons = {
            "easy": Button((705, btn_y, btn_w, btn_h), "Easy", lambda: self.on_change_difficulty("easy")),
            "normal": Button((805, btn_y, btn_w, btn_h), "Normal", lambda: self.on_change_difficulty("normal")),
            "hard": Button((905, btn_y, btn_w, btn_h), "Hard", lambda: self.on_change_difficulty("hard")),
        }

        # ルール切替ボタン（隣接のみ / 自由）
        self.rule_btn = Button((705, 536, 290, 32), "開放ルール: 隣接マスのみ", self.on_toggle_rule)

        # リセットボタン
        self.restart_btn = Button((705, 580, 290, 38), "新規ゲーム開始 (R)", self.on_restart,
                                  bg_color=(30, 58, 138), active_color=(37, 99, 235))

    def handle_event(self, event):
        for btn in self.diff_buttons.values():
            if btn.handle_event(event):
                return True
        if self.rule_btn.handle_event(event):
            return True
        if self.restart_btn.handle_event(event):
            return True
        return False

    def draw_side_panel(self, surface, board, players, current_difficulty, elapsed_time):
        self._init_fonts()

        panel_x = 690
        panel_y = 20
        panel_w = 320
        panel_h = 680

        # パネル背景
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, COLOR_PANEL_BG, panel_rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, panel_rect, width=2, border_radius=10)

        # タイトル
        title_surf = self.font_title.render("MINESWEEPER WARS", True, (56, 189, 248))
        surface.blit(title_surf, (panel_x + 20, panel_y + 15))

        sub_surf = self.font_small.render("リアルタイム陣取り合戦", True, COLOR_TEXT_MUTED)
        surface.blit(sub_surf, (panel_x + 22, panel_y + 45))

        # スコア集計
        scores = board.get_scores()
        total_cells = board.cols * board.rows

        # プレイヤーカード (4名分)
        card_y = panel_y + 75
        card_h = 60
        card_gap = 8

        # 順位付け用ソート
        ranked_pids = sorted([1, 2, 3, 4], key=lambda pid: scores[pid], reverse=True)

        for rank, pid in enumerate(ranked_pids, start=1):
            p = players[pid]
            p_color = PLAYER_COLORS[pid]
            count = scores[pid]
            share = (count / total_cells) * 100.0 if total_cells > 0 else 0

            card_rect = pygame.Rect(panel_x + 15, card_y, panel_w - 30, card_h)

            # 背景（スタン時は赤みがかった警告色）
            if p.is_stunned:
                bg_col = (79, 25, 25)
                border_col = (239, 68, 68)
            else:
                bg_col = (20, 28, 45)
                border_col = p_color["main"] if pid == 1 else (40, 50, 70)

            pygame.draw.rect(surface, bg_col, card_rect, border_radius=6)
            pygame.draw.rect(surface, border_col, card_rect, width=1, border_radius=6)

            # 順位バッジ
            badge_text = f"#{rank}"
            b_surf = self.font_bold.render(badge_text, True, (250, 204, 21) if rank == 1 else COLOR_TEXT_MUTED)
            surface.blit(b_surf, (card_rect.x + 8, card_rect.y + 8))

            # プレイヤー名
            name_surf = self.font_bold.render(p.name, True, p_color["bright"])
            surface.blit(name_surf, (card_rect.x + 36, card_rect.y + 8))

            # スコア & シェア
            score_text = f"{count}マス ({share:.1f}%)"
            s_surf = self.font_bold.render(score_text, True, COLOR_TEXT)
            s_rect = s_surf.get_rect(right=card_rect.right - 10, top=card_rect.y + 8)
            surface.blit(s_surf, s_rect)

            # 下部ステータス（スタン表示 or 孤立ブレイクアウト or 通常状態）
            if p.is_stunned:
                stun_text = f"⚠️ スタン中! ({p.stun_timer:.1f}s)"
                st_surf = self.font_bold.render(stun_text, True, (248, 113, 113))
                surface.blit(st_surf, (card_rect.x + 36, card_rect.y + 32))

                # スタン進行バー
                bar_x = card_rect.right - 90
                bar_y = card_rect.y + 36
                bar_w = 80
                bar_h = 8
                pygame.draw.rect(surface, (50, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                ratio = p.stun_timer / 5.0
                pygame.draw.rect(surface, (239, 68, 68), (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=4)
            elif board.only_adjacent_rule and board.is_player_isolated(pid):
                iso_text = "★ 包囲脱出! どこでも開拓可"
                iso_surf = self.font_bold.render(iso_text, True, (250, 204, 21))
                surface.blit(iso_surf, (card_rect.x + 36, card_rect.y + 32))
            else:
                info_text = f"地雷被弾: {p.mines_triggered}回"
                inf_surf = self.font_small.render(info_text, True, COLOR_TEXT_MUTED)
                surface.blit(inf_surf, (card_rect.x + 36, card_rect.y + 34))

            card_y += card_h + card_gap

        # 領地シェアのマルチカラープログレスバー
        bar_x = panel_x + 15
        bar_y = card_y + 8
        bar_w = panel_w - 30
        bar_h = 16
        pygame.draw.rect(surface, (40, 50, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=8)

        current_x = bar_x
        for pid in (1, 2, 3, 4):
            cnt = scores[pid]
            w = int(bar_w * (cnt / total_cells))
            if w > 0:
                seg_rect = pygame.Rect(current_x, bar_y, w, bar_h)
                pygame.draw.rect(surface, PLAYER_COLORS[pid]["main"], seg_rect)
                current_x += w

        # 全体インフォメーション
        info_y = bar_y + 26
        unrev = scores["unrevealed"]
        mines_found = scores["mine"]
        time_str = f"経過時間: {int(elapsed_time)}s"
        cells_str = f"未開放: {unrev}マス / 爆破地雷: {mines_found}"

        surface.blit(self.font_regular.render(time_str, True, COLOR_TEXT), (panel_x + 18, info_y))
        surface.blit(self.font_small.render(cells_str, True, COLOR_TEXT_MUTED), (panel_x + 18, info_y + 22))

        # 難易度ラベル & ボタン
        diff_label_y = info_y + 50
        surface.blit(self.font_bold.render("難易度プリセット:", True, COLOR_TEXT), (panel_x + 18, diff_label_y))

        for k, btn in self.diff_buttons.items():
            btn.active = (k == current_difficulty)
            btn.draw(surface, self.font_bold)

        # ルールボタン描画
        self.rule_btn.text = f"開放ルール: {'隣接マスのみ' if board.only_adjacent_rule else 'どこでも自由'}"
        self.rule_btn.draw(surface, self.font_regular)

        # リスタートボタン描画
        self.restart_btn.draw(surface, self.font_bold)

        # 操作ヒントテキスト
        help_y = self.restart_btn.rect.bottom + 8
        hint1 = "◆ 右クリック: 旗を設置 (誤爆防止)"
        hint2 = "★ 数字Wクリック: 周囲マス一括開放"
        surface.blit(self.font_small.render(hint1, True, (251, 191, 36)), (panel_x + 18, help_y))
        surface.blit(self.font_small.render(hint2, True, (56, 189, 248)), (panel_x + 18, help_y + 16))

    def draw_game_over_modal(self, surface, board, players):
        """ゲーム終了時のリザルトモーダル描画"""
        self._init_fonts()

        # 暗転オーバーレイ
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # モーダルウィンドウ
        mw = 480
        mh = 360
        mx = (WINDOW_WIDTH - mw) // 2
        my = (WINDOW_HEIGHT - mh) // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)

        pygame.draw.rect(surface, (20, 28, 48), modal_rect, border_radius=12)
        pygame.draw.rect(surface, (56, 189, 248), modal_rect, width=2, border_radius=12)

        # 順位判定
        scores = board.get_scores()
        ranked_pids = sorted([1, 2, 3, 4], key=lambda pid: scores[pid], reverse=True)
        winner_id = ranked_pids[0]
        winner = players[winner_id]

        if winner_id == 1:
            res_title = "VICTORY! あなたの勝利!"
            title_col = (74, 222, 128)
        else:
            res_title = f"{winner.name} の勝利!"
            title_col = (248, 113, 113)

        t_surf = self.font_title.render(res_title, True, title_col)
        surface.blit(t_surf, t_surf.get_rect(center=(WINDOW_WIDTH // 2, my + 35)))

        sub_surf = self.font_regular.render("全マスの開放または進行が終了しました", True, COLOR_TEXT_MUTED)
        surface.blit(sub_surf, sub_surf.get_rect(center=(WINDOW_WIDTH // 2, my + 68)))

        # 順位一覧表示
        list_y = my + 100
        total_cells = board.cols * board.rows
        for rank, pid in enumerate(ranked_pids, start=1):
            p = players[pid]
            p_color = PLAYER_COLORS[pid]
            cnt = scores[pid]
            share = (cnt / total_cells) * 100.0 if total_cells > 0 else 0

            row_text = f"第{rank}位:  {p.name}  -  {cnt}マス ({share:.1f}%)"
            color = p_color["bright"] if pid == 1 else COLOR_TEXT
            r_surf = self.font_bold.render(row_text, True, color)
            surface.blit(r_surf, (mx + 60, list_y))
            list_y += 36

        # 再開ヒント
        hint_surf = self.font_regular.render("Spaceキー または「新規ゲーム開始」で再挑戦", True, (250, 204, 21))
        surface.blit(hint_surf, hint_surf.get_rect(center=(WINDOW_WIDTH // 2, my + mh - 40)))
