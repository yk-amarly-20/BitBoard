from flask import Flask, session, redirect, url_for, render_template_string, request
from typing import Tuple

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# ----- BitBoard クラス（省略可：実際は別ファイルに分けてもOK） -----
class BitBoard:
    MASK_FILE_A = 0x0101010101010101
    MASK_FILE_H = 0x8080808080808080
    MASK_FILE_AB = 0x0303030303030303
    MASK_FILE_GH = 0xC0C0C0C0C0C0C0C0

    def __init__(self):
        self.black = (1 << 27) | (1 << 36)
        self.white = (1 << 35) | (1 << 28)
        self.current_player = 'B'

    def _get_player_bitboards(self) -> Tuple[int, int]:
        return (self.black, self.white) if self.current_player == 'B' else (self.white, self.black)

    @staticmethod
    def square_to_index(square: str) -> int:
        col = ord(square[0].upper()) - ord('A')
        row = int(square[1]) - 1
        return row * 8 + col

    @staticmethod
    def index_to_square(index: int) -> str:
        row, col = divmod(index, 8)
        return f"{chr(col + ord('A'))}{row + 1}"

    def get_legal_moves(self) -> int:
        player, opponent = self._get_player_bitboards()
        empty = ~(player | opponent) & 0xFFFFFFFFFFFFFFFF
        legal = 0
        directions = [(1, self.MASK_FILE_H), (-1, self.MASK_FILE_A), (8, 0), (-8, 0), (9, self.MASK_FILE_H), (7, self.MASK_FILE_A), (-7, self.MASK_FILE_H), (-9, self.MASK_FILE_A)]
        for shift, mask_file in directions:
            mask = opponent & ~mask_file
            move_mask = (player << shift) if shift > 0 else (player >> -shift)
            cand = mask & move_mask
            while cand:
                cand_shifted = (cand << shift) if shift > 0 else (cand >> -shift)
                legal |= empty & cand_shifted
                cand = mask & cand_shifted
        return legal

    def make_move(self, square: str) -> bool:
        idx = self.square_to_index(square)
        move_bb = 1 << idx
        legal = self.get_legal_moves()
        if not (move_bb & legal): return False
        player, opponent = self._get_player_bitboards()
        flips = 0
        directions = [(1, self.MASK_FILE_H), (-1, self.MASK_FILE_A), (8, 0), (-8, 0), (9, self.MASK_FILE_H), (7, self.MASK_FILE_A), (-7, self.MASK_FILE_H), (-9, self.MASK_FILE_A)]
        for shift, mask_file in directions:
            mask = opponent & ~mask_file
            line_flips = 0
            cand = mask & (move_bb << shift if shift > 0 else move_bb >> -shift)
            while cand:
                line_flips |= cand
                next_cand = mask & (cand << shift if shift > 0 else cand >> -shift)
                if not next_cand:
                    break
                cand = next_cand
            end_bit = (cand << shift) if shift > 0 else (cand >> -shift)
            if end_bit & player:
                flips |= line_flips
        if self.current_player == 'B':
            self.black ^= flips | move_bb
            self.white ^= flips
        else:
            self.white ^= flips | move_bb
            self.black ^= flips
        self.current_player = 'W' if self.current_player == 'B' else 'B'
        return True

    def list_board(self) -> list:
        grid = []
        for r in range(7, -1, -1):
            row = []
            for c in range(8):
                idx = r * 8 + c
                bit = 1 << idx
                if self.black & bit:
                    row.append('B')
                elif self.white & bit:
                    row.append('W')
                else:
                    row.append('')
            grid.append(row)
        return grid

    def list_legal(self) -> list:
        moves = self.get_legal_moves()
        return [self.index_to_square(i) for i in range(64) if (moves >> i) & 1]

# ----- セッションから BitBoard の取得・保存 -----
def get_game():
    if 'game' not in session:
        session['game'] = BitBoard().__dict__
    board = BitBoard()
    board.__dict__.update(session['game'])
    return board

def save_game(board):
    session['game'] = board.__dict__

# ----- テンプレート定義 -----
TEMPLATE = '''
<!doctype html>
<html>
<head><title>Flask Othello</title><style>
table{border-collapse:collapse;}td{width:40px;height:40px;text-align:center;border:1px solid #000;}a{display:block;width:100%;height:100%;text-decoration:none;color:#000;}
</style></head>
<body>
  <h1>Flask Othello</h1>
  <p>Current: {{ player }}</p>
  <table>
    {% for i in range(board|length) %}
      <tr>
        {% for j in range(board[0]|length) %}
          <td>
            {% set cell = board[i][j] %}
            {% set sq = cols[j] ~ rows[i] %}
            {% if cell %}
              {{ '●' if cell == 'B' else '○' }}
            {% elif sq in legal %}
              <a href="{{ url_for('move', square=sq) }}"></a>
            {% endif %}
          </td>
        {% endfor %}
      </tr>
    {% endfor %}
  </table>
  <p><a href="{{ url_for('reset') }}">Reset Game</a></p>
</body>
</html>
'''

# ----- ルート定義 -----
@app.route('/')
def index():
    game = get_game()
    board = game.list_board()
    legal = game.list_legal()
    player = 'Black' if game.current_player == 'B' else 'White'
    cols = ['A','B','C','D','E','F','G','H']
    rows = ['8','7','6','5','4','3','2','1']
    return render_template_string(TEMPLATE, board=board, legal=legal, player=player, cols=cols, rows=rows)

@app.route('/move')
def move():
    square = request.args.get('square')
    game = get_game()
    game.make_move(square)
    save_game(game)
    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    session.pop('game', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
