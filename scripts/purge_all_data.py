#!/usr/bin/env python3
"""
全データ削除（ストレージ初期化）スクリプト
- SQLite, ChromaDB, NetworkXグラフ等の物理ファイルを削除
- サーバ停止中に実行すること
- 実行後は必要に応じてbulk_store_memories.py等で再投入
"""
import os
import shutil

# 設定: ストレージファイル/ディレクトリのパス
SQLITE_PATH = "data/metadata.db"
CHROMA_PATH = "data/chroma/"
GRAPH_PATH = "data/graph_store/"


def remove_path(path):
    if os.path.isfile(path):
        print(f"削除: {path}")
        os.remove(path)
    elif os.path.isdir(path):
        print(f"ディレクトリ削除: {path}")
        shutil.rmtree(path)
    else:
        print(f"存在しない: {path}")


def main():
    print("=== MCP全データ削除スクリプト ===")
    remove_path(SQLITE_PATH)
    remove_path(CHROMA_PATH)
    remove_path(GRAPH_PATH)
    print("--- 完了 ---")
    print("※サーバ再起動後、必要に応じてデータ再投入してください")

if __name__ == "__main__":
    main()
