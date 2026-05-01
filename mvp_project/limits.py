"""
ドメイン上の共通上限（単一ソース）。

選出 required_count と課題の required_participants は同一のキャップとして扱う。
この値を変えるときは Selection の validators・課題 API・frontend の入力上限をまとめて更新する。
（匿名名の件数とは独立に上限を定められる。）
"""

MAX_SELECTION_PARTICIPANTS = 700
