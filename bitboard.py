from typing import List, Tuple

class BitBoard:
    # ------------------------------------------------------------
    # 盤面を左右上下斜め８方向にビットシフトするときに使う定数マスク
    #   方向ごとに行をまたいでしまうシフトを防ぐためのマスクを予め定義しておく。
    # ------------------------------------------------------------
    # A列 (ビット0,8,...,56) が 1 のビットマスク
    MASK_FILE_A = 0x0101010101010101
    # H列 (ビット7,15,...,63) が 1 のビットマスク
    MASK_FILE_H = 0x8080808080808080
    # AB列 (ビット0,1,8,9,...,56,57) が 1 のビットマスク
    MASK_FILE_AB = 0x0303030303030303
    # GH列 (ビット6,7,14,15,...,62,63) が 1 のビットマスク
    MASK_FILE_GH = 0xC0C0C0C0C0C0C0C0

    # ------------------------------------------------------------
    # 初期化 (スタートポジションをセット)
    # ------------------------------------------------------------
    def __init__(self):
        # 黒石の初期配置： D4(27), E5(36)
        self.black = (1 << 27) | (1 << 36)
        # 白石の初期配置： D5(35), E4(28)
        self.white = (1 << 35) | (1 << 28)
        # 手番: 'B' が黒、'W' が白
        self.current_player = 'B'

    # ------------------------------------------------------------
    # ユーティリティ: 現在の手番の石ビットボードと相手の石ビットボードを返す
    # ------------------------------------------------------------
    def _get_player_bitboards(self) -> Tuple[int, int]:
        if self.current_player == 'B':
            return self.black, self.white
        else:
            return self.white, self.black

    # ------------------------------------------------------------
    # ユーティリティ: 位置文字列 (例: 'D3') をビットインデックス (0～63) に変換
    #  - 列: 'A'〜'H' → 0〜7, 行: '1'〜'8' → 0〜7
    # ------------------------------------------------------------
    @staticmethod
    def square_to_index(square: str) -> int:
        """
        square: 例えば "D3" のように、列(A~H)+行(1~8) の２文字
        戻り値: ビットインデックス 0~63
        """
        col = ord(square[0].upper()) - ord('A')  # 0〜7
        row = int(square[1]) - 1                # 0〜7
        return row * 8 + col

    # ------------------------------------------------------------
    # ビットインデックス (0~63) を位置文字列 (例: 'D3') に変換
    # ------------------------------------------------------------
    @staticmethod
    def index_to_square(index: int) -> str:
        """
        index: 0〜63
        戻り値: 文字列 "A1"〜"H8"
        """
        row = index // 8     # 0〜7
        col = index % 8      # 0〜7
        return f"{chr(col + ord('A'))}{row + 1}"

    # ------------------------------------------------------------
    # 盤面をASCII表示 (人間が見やすい形で出力)
    # ------------------------------------------------------------
    def print_board(self):
        black, white = self._get_player_bitboards() if self.current_player == 'B' else (self.white, self.black)
        # ただし、表示上は常に上が8行目、下が1行目。
        print("  A B C D E F G H")
        for row in range(7, -1, -1):
            line = f"{row+1} "
            for col in range(8):
                idx = row * 8 + col
                mask = 1 << idx
                if (self.black >> idx) & 1:
                    line += "● "  # 黒石
                elif (self.white >> idx) & 1:
                    line += "○ "  # 白石
                else:
                    line += "- "  # 空きマス
            print(line + f"{row+1}")
        print("  A B C D E F G H\n")

    # ------------------------------------------------------------
    # 現在の手番プレイヤー（player）の合法手ビットボードを計算する
    # ------------------------------------------------------------
    def get_legal_moves(self) -> int:
        """
        返却値: ビットボード (64ビット整数) で、合法手になり得るマスが 1 になっている。
        見方: たとえば (moves >> i) & 1 == 1 なら、ビット i（マス i）は合法手。
        """
        player, opponent = self._get_player_bitboards()
        empty = ~(player | opponent) & 0xFFFFFFFFFFFFFFFF  # 盤外ビットを消す

        legal_moves = 0
        # 8方向それぞれについて、一度に“はさみ”を検出する
        # 1) 隣接マスが opponent の石であるものを見つける
        # 2) 連続して相手の石が続くもの全体を追尾
        # 3) その先にプレイヤーの石があれば、その隣接空きマスを“合法手”に加える

        # --- 東 (East) 方向 ---
        mask = opponent & ~self.MASK_FILE_H  # H列へはみ出すもの除去
        flip_candidates = mask & (player << 1)
        # 周辺の相手石をすべて取り込みつつ、
        while flip_candidates:
            legal_moves |= (legal_moves | (empty & (flip_candidates << 1)))
            flip_candidates = mask & (flip_candidates << 1)

        # --- 西 (West) 方向 ---
        mask = opponent & ~self.MASK_FILE_A
        flip_candidates = mask & (player >> 1)
        while flip_candidates:
            legal_moves |= (legal_moves | (empty & (flip_candidates >> 1)))
            flip_candidates = mask & (flip_candidates >> 1)

        # --- 北 (North) 方向 ---
        mask = opponent
        flip_candidates = mask & (player << 8)
        while flip_candidates:
            legal_moves |= (legal_moves | (empty & (flip_candidates << 8)))
            flip_candidates = mask & (flip_candidates << 8)

        # --- 南 (South) 方向 ---
        mask = opponent
        flip_candidates = mask & (player >> 8)
        while flip_candidates:
            legal_moves |= (legal_moves | (empty & (flip_candidates >> 8)))
            flip_candidates = mask & (flip_candidates >> 8)

        # --- 北東 (NorthEast) 方向 ---
        mask = opponent & ~self.MASK_FILE_H
        flip_candidates = mask & (player << 9)
        while flip_candidates:
            legal_moves |= (legal_moves | (empty & (flip_candidates << 9)))
            flip_candidates = mask & (flip_candidates << 9)

        # --- 北西 (NorthWest) 方向 ---
        mask = opponent & ~self.MASK_FILE_A
        flip_candidates = mask & (player << 7)
        while flip_candidates:
            legal_moves |= (legal_moves | (empty & (flip_candidates << 7)))
            flip_candidates = mask & (flip_candidates << 7)

        # --- 南東 (SouthEast) 方向 ---
        mask = opponent & ~self.MASK_FILE_H
        flip_candidates = mask & (player >> 7)
        while flip_candidates:
            # flip_candidates = mask & (flip_candidates >> 7)
            legal_moves |= (legal_moves | (empty & (flip_candidates >> 7)))
            flip_candidates = mask & (flip_candidates >> 7)

        # --- 南西 (SouthWest) 方向 ---
        mask = opponent & ~self.MASK_FILE_A
        flip_candidates = mask & (player >> 9)
        while flip_candidates:
            # flip_candidates = mask & (flip_candidates >> 9)
            legal_moves |= (legal_moves | (empty & (flip_candidates >> 9)))
            flip_candidates = mask & (flip_candidates >> 9)

        return legal_moves & 0xFFFFFFFFFFFFFFFF  # 余分な上位ビットを消しておく

    # ------------------------------------------------------------
    # 着手してビットをひっくり返す (move: 0～63 のインデックス or 1ビット)
    # ------------------------------------------------------------
    def make_move(self, move: int) -> bool:
        # move がインデックスの場合はビットに変換
        if move.bit_length() <= 6:
            idx = move
            move_bb = 1 << idx
        else:
            move_bb = move

        legal = self.get_legal_moves()
        if (move_bb & legal) == 0:
            return False  # 合法手ではない

        player, opponent = self._get_player_bitboards()
        total_flips = 0

        # 各方向で反転対象を集める
        # 東
        mask = opponent & ~self.MASK_FILE_H
        flips = 0
        cand = mask & (move_bb << 1)
        while cand:
            flips |= cand
            tcand = mask & (cand << 1)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand << 1) & player:
            total_flips |= flips

        # 西
        mask = opponent & ~self.MASK_FILE_A
        flips = 0
        cand = mask & (move_bb >> 1)
        while cand:
            flips |= cand
            tcand = mask & (cand << 1)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand >> 1) & player:
            total_flips |= flips

        # 北
        mask = opponent
        flips = 0
        cand = mask & (move_bb << 8)
        while cand:
            flips |= cand
            tcand = mask & (cand << 8)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand << 8) & player:
            total_flips |= flips

        # 南
        mask = opponent
        flips = 0
        cand = mask & (move_bb >> 8)
        while cand:
            flips |= cand
            tcand = mask & (cand >> 8)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand >> 8) & player:
            total_flips |= flips

        # 北東
        mask = opponent & ~self.MASK_FILE_H
        flips = 0
        cand = mask & (move_bb << 9)
        while cand:
            flips |= cand
            tcand = mask & (cand << 9)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand << 9) & player:
            total_flips |= flips
        # 北西
        mask = opponent & ~self.MASK_FILE_A
        flips = 0
        cand = mask & (move_bb << 7)
        while cand:
            flips |= cand
            tcand = mask & (cand << 7)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand << 7) & player:
            total_flips |= flips
        # 南東
        mask = opponent & ~self.MASK_FILE_H
        flips = 0
        cand = mask & (move_bb >> 7)
        while cand:
            flips |= cand
            tcand = mask & (cand >> 7)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand >> 7) & player:
            total_flips |= flips
        # 南西
        mask = opponent & ~self.MASK_FILE_A
        flips = 0
        cand = mask & (move_bb >> 9)
        while cand:
            flips |= cand
            tcand = mask & (cand >> 9)
            if tcand == 0:
                break
            else:
                cand = tcand
        if (cand >> 9) & player:
            total_flips |= flips

        # 実際にビットを反転・追加
        if self.current_player == 'B':
            self.black ^= (move_bb | total_flips)
            self.white ^= total_flips
            self.black |= move_bb
        else:
            self.white ^= (move_bb | total_flips)
            self.black ^= total_flips
            self.white |= move_bb

        # 手番交代
        self.current_player = 'W' if self.current_player == 'B' else 'B'
        return True

    # ------------------------------------------------------------
    # パス可能判定 (合法手がひとつもない)
    # ------------------------------------------------------------
    def can_pass(self) -> bool:
        return self.get_legal_moves() == 0

    # ------------------------------------------------------------
    # ゲーム終了判定 (両者とも合法手なし)
    # ------------------------------------------------------------
    def is_game_over(self) -> bool:
        if self.get_legal_moves() != 0:
            return False
        # 一度手番を入れ替えて相手の合法手を確認
        print(self.get_legal_moves())
        self.current_player = 'W' if self.current_player == 'B' else 'B'
        has_moves = (self.get_legal_moves() != 0)
        # 手番を戻す
        self.current_player = 'W' if self.current_player == 'B' else 'B'
        return not has_moves

    # ------------------------------------------------------------
    # 現在スコア（黒, 白 の石数）を返す
    # ------------------------------------------------------------
    def get_score(self) -> Tuple[int, int]:
        b_count = bin(self.black).count("1")
        w_count = bin(self.white).count("1")
        return b_count, w_count

    # ------------------------------------------------------------
    # 合法手を ["D3","C4",...] のように文字列リストで取得
    # ------------------------------------------------------------
    def list_legal_moves(self) -> List[str]:
        legal_bb = self.get_legal_moves()
        moves = []
        for i in range(64):
            if (legal_bb >> i) & 1:
                moves.append(self.index_to_square(i))
        return moves

def main():
    game = BitBoard()

    print("=== ビットボード版オセロ (CLI) ===")
    print("入力例: D3 のように列と行を組み合わせて入力してください。")
    print("合法手がない場合は “pass” と入力してください。\n")

    # ゲームループ
    while True:
        # 盤面とスコア、手番を表示
        game.print_board()
        black_score, white_score = game.get_score()
        print(f"現在のスコア → 黒: {black_score} 石、白: {white_score} 石")
        print(f"手番: {'黒 (●)' if game.current_player == 'B' else '白 (○)'}")

        # 終了判定
        if game.is_game_over():
            print("\nゲーム終了！")
            b_final, w_final = game.get_score()
            print(f"最終スコア → 黒: {b_final} 石、白: {w_final} 石")
            if b_final > w_final:
                print("勝者: 黒 (●)")
            elif w_final > b_final:
                print("勝者: 白 (○)")
            else:
                print("引き分けです。")
            break

        # 合法手表示
        legal_moves = game.list_legal_moves()
        if legal_moves:
            print("合法手:", " ".join(legal_moves))
        else:
            print("合法手なし → pass")

        # プレイヤー入力
        user_input = input("着手 (例 D3 or pass): ").strip().upper()

        # pass の場合
        if user_input == "PASS":
            if game.can_pass():
                game.current_player = 'W' if game.current_player == 'B' else 'B'
                print("パスしました。\n")
                continue
            else:
                print("まだ合法手があります。パスできません。\n")
                continue

        # 位置入力 (例: D3)
        if len(user_input) == 2 and user_input[0] in "ABCDEFGH" and user_input[1] in "12345678":
            try:
                idx = BitBoard.square_to_index(user_input)
            except Exception:
                print("入力が不正です。もう一度入力してください。\n")
                continue

            if not game.make_move(idx):
                print("その位置は合法手ではありません。もう一度入力してください。\n")
                continue
            else:
                # 着手成功
                print(f"{user_input} に着手しました。\n")
                continue
        else:
            print("入力形式が正しくありません（例: D3 または pass）。\n")
            continue

if __name__ == "__main__":
    main()
