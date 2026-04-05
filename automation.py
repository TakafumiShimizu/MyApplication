#!/usr/bin/env python3
"""実用向けのファイルバックアップ自動化ツール。

主な用途:
- 拡張子・除外パターンで対象を絞った定期バックアップ
- 実行前の dry-run 確認
- 古いバックアップの世代管理

使い方例:
  python automation.py --source ./data --dest ./backup --ext .txt .csv
  python automation.py --config backup_config.example.json --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

TIMESTAMP_FMT = "%Y%m%d_%H%M%S"


@dataclass
class Settings:
    """実行時に使う設定値。"""

    source: Path
    dest: Path
    ext: list[str]
    exclude: list[str]
    keep: int
    dry_run: bool


@dataclass
class BackupResult:
    """バックアップ実行結果。"""

    scanned: int = 0
    copied: int = 0
    skipped: int = 0


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
        help="対象拡張子（例: .txt .csv）。空にすると全ファイル対象",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="除外する glob パターン（例: '*.tmp' '.git/*'）",
    )
    parser.add_argument("--keep", type=int, default=7, help="保持するバックアップ世代数（既定: 7）")
    parser.add_argument("--config", type=Path, help="JSON設定ファイル")
    parser.add_argument("--dry-run", action="store_true", help="コピーはせず、予定だけ表示")
    return parser.parse_args()


def load_config(path: Path) -> dict:
    """JSON設定ファイルを読み込む。"""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    required = {"source", "dest"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"設定ファイルに不足項目があります: {', '.join(sorted(missing))}")
    return data


def normalize_extensions(ext_list: list[str]) -> list[str]:
    """拡張子を正規化（小文字 + 先頭ドット）する。"""
    normalized = []
    for ext in ext_list:
        fixed = ext if ext.startswith(".") else f".{ext}"
        normalized.append(fixed.lower())
    return normalized


def resolve_settings(args: argparse.Namespace) -> Settings:
    """引数または設定ファイルから最終設定を組み立てる。"""
    if args.config:
        cfg = load_config(args.config)
        source = Path(cfg["source"])
        dest = Path(cfg["dest"])
        ext = cfg.get("ext", args.ext)
        exclude = cfg.get("exclude", args.exclude)
        keep = int(cfg.get("keep", args.keep))
    else:
        if not args.source or not args.dest:
            raise ValueError("--source と --dest を指定するか、--config を使用してください")
        source = args.source
        dest = args.dest
        ext = args.ext
        exclude = args.exclude
        keep = args.keep

    if keep < 1:
        raise ValueError("--keep は 1 以上を指定してください")

    normalized_ext = normalize_extensions(ext) if ext else []
    return Settings(
        source=source,
        dest=dest,
        ext=normalized_ext,
        exclude=exclude,
        keep=keep,
        dry_run=args.dry_run,
    )


def should_exclude(relative_path: Path, patterns: list[str]) -> bool:
    """相対パスが除外パターンに一致するか判定する。"""
    path_text = relative_path.as_posix()
    return any(fnmatch.fnmatch(path_text, pat) for pat in patterns)


def collect_files(settings: Settings) -> list[Path]:
    """設定に合うファイルを再帰的に収集する。"""
    files: list[Path] = []
    for p in settings.source.rglob("*"):
        if not p.is_file():
            continue

        rel = p.relative_to(settings.source)
        if should_exclude(rel, settings.exclude):
            continue

        if settings.ext and p.suffix.lower() not in settings.ext:
            continue

        files.append(p)
    return files


def is_same_file(src: Path, dst: Path) -> bool:
    """サイズと更新時刻で同一ファイルか簡易判定する。"""
    if not dst.exists():
        return False
    src_stat = src.stat()
    dst_stat = dst.stat()
    return src_stat.st_size == dst_stat.st_size and int(src_stat.st_mtime) == int(dst_stat.st_mtime)


def backup_files(files: list[Path], settings: Settings) -> tuple[Path, BackupResult]:
    """ファイルをバックアップ先へコピーする。"""
    backup_root = settings.dest / dt.datetime.now().strftime(TIMESTAMP_FMT)
    result = BackupResult(scanned=len(files))

    for file in files:
        rel = file.relative_to(settings.source)
        target = backup_root / rel

        if is_same_file(file, target):
            print(f"[SKIP] 変更なし: {file}")
            result.skipped += 1
            continue

        print(f"[COPY] {file} -> {target}")
        if not settings.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)

        result.copied += 1

    if not settings.dry_run:
        print(f"保存先: {backup_root}")
    return backup_root, result


def apply_retention(dest: Path, keep: int, dry_run: bool) -> int:
    """古いバックアップ世代を削除して、keep件だけ残す。"""
    backup_dirs = [p for p in dest.iterdir() if p.is_dir()]

    # タイムスタンプ名のフォルダだけを対象にする
    valid_backups: list[Path] = []
    for p in backup_dirs:
        try:
            dt.datetime.strptime(p.name, TIMESTAMP_FMT)
        except ValueError:
            continue
        valid_backups.append(p)

    valid_backups.sort(key=lambda x: x.name, reverse=True)
    to_delete = valid_backups[keep:]

    for old in to_delete:
        print(f"[PRUNE] 古いバックアップを削除: {old}")
        if not dry_run:
            shutil.rmtree(old)

    return len(to_delete)


def print_summary(result: BackupResult, pruned: int, dry_run: bool) -> None:
    """実行結果を見やすく表示する。"""
    mode = "DRY-RUN" if dry_run else "EXECUTE"
    print("\n===== 結果サマリー =====")
    print(f"モード: {mode}")
    print(f"探索対象: {result.scanned} 件")
    print(f"コピー実行: {result.copied} 件")
    print(f"スキップ: {result.skipped} 件")
    print(f"世代削除: {pruned} 件")


def main() -> None:
    """メイン処理。"""
    args = parse_args()
    settings = resolve_settings(args)

    if not settings.source.exists() or not settings.source.is_dir():
        raise FileNotFoundError(f"source が存在しないか、フォルダではありません: {settings.source}")

    if not settings.dest.exists() and not settings.dry_run:
        settings.dest.mkdir(parents=True, exist_ok=True)

    files = collect_files(settings)
    if not files:
        print("対象ファイルが見つかりませんでした")
        return

    _, result = backup_files(files, settings)
    pruned = apply_retention(settings.dest, settings.keep, settings.dry_run) if settings.dest.exists() else 0
    print_summary(result, pruned, settings.dry_run)


if __name__ == "__main__":
    main()
