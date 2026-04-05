#!/usr/bin/env python3
"""フォルダ内ファイルを自動バックアップするスクリプト。

使い方:
  python automation.py --source ./data --dest ./backup --ext .txt .csv
  python automation.py --config backup_config.example.json --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を受け取る。"""
    parser = argparse.ArgumentParser(
        description="指定フォルダを、日時付きフォルダに自動バックアップするツール"
    )
    parser.add_argument("--source", type=Path, help="バックアップ元フォルダ")
    parser.add_argument("--dest", type=Path, help="バックアップ先フォルダ")
    parser.add_argument(
        "--ext",
        nargs="*",
        default=[".txt", ".csv"],
        help="対象拡張子（例: .txt .csv）",
    )
    parser.add_argument("--config", type=Path, help="JSON設定ファイル（source / dest / ext）")
    parser.add_argument("--dry-run", action="store_true", help="コピーはせず、予定だけ表示")
    return parser.parse_args()


def load_config(path: Path) -> dict:
    """JSON設定ファイルを読み込む。"""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 最低限必要なキーがあるか確認
    required = {"source", "dest"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"設定ファイルに不足項目があります: {', '.join(sorted(missing))}")
    return data


def resolve_settings(args: argparse.Namespace) -> tuple[Path, Path, list[str]]:
    """引数または設定ファイルから実行設定を決定する。"""
    if args.config:
        cfg = load_config(args.config)
        source = Path(cfg["source"])
        dest = Path(cfg["dest"])
        ext = cfg.get("ext", args.ext)
    else:
        if not args.source or not args.dest:
            raise ValueError("--source と --dest を指定するか、--config を使用してください")
        source = args.source
        dest = args.dest
        ext = args.ext

    # txt のようにドットなし指定でも .txt に補正する
    ext = [e if e.startswith(".") else f".{e}" for e in ext]
    return source, dest, ext


def collect_files(source: Path, extensions: list[str]) -> list[Path]:
    """対象拡張子のファイルを再帰的に集める。"""
    return [p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in extensions]


def backup_files(files: list[Path], source: Path, dest: Path, dry_run: bool) -> int:
    """ファイルをバックアップ先へコピーする。"""
    # 実行ごとに保存先が分かるよう、日時付きフォルダを作る
    backup_root = dest / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    copied = 0

    for file in files:
        # 元フォルダからの相対パスを維持して保存
        relative = file.relative_to(source)
        target = backup_root / relative
        print(f"[COPY] {file} -> {target}")

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
        copied += 1

    print(f"\n完了: {copied} 件 {'(dry-run)' if dry_run else ''}")
    if not dry_run:
        print(f"保存先: {backup_root}")
    return copied


def main() -> None:
    """メイン処理。"""
    args = parse_args()
    source, dest, ext = resolve_settings(args)

    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"source が存在しないか、フォルダではありません: {source}")

    files = collect_files(source, [e.lower() for e in ext])
    if not files:
        print("対象ファイルが見つかりませんでした")
        return

    backup_files(files, source, dest, args.dry_run)


if __name__ == "__main__":
    main()
