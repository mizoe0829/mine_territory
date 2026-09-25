import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pygame
import time
from main import MinesweeperWarsGame

def test_run():
    game = MinesweeperWarsGame()
    print("MinesweeperWarsGame initialized successfully!")
    
    # 60フレーム回して描画・CPU動作をテスト
    for frame in range(60):
        dt = game.clock.tick(60) / 1000.0
        game.elapsed_time += dt
        game.players[1].update(dt)
        game.update_cpus(dt)
        
        # 画面描画
        game.screen.fill((15, 23, 42))
        game.board.draw(game.screen, hover_cell=(0, 0), active_player_id=1, show_valid_targets=True)
        game.ui.draw_side_panel(game.screen, game.board, game.players, game.current_difficulty, game.elapsed_time)
        pygame.display.flip()

    print("60 frames rendered and simulated without any exceptions!")
    pygame.quit()

if __name__ == "__main__":
    test_run()
