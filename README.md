# 自動化プログラム（実用版バックアップ）

このツールは、指定フォルダを **実運用しやすい形で** バックアップするための CLI です。

## 実用向けに強化したポイント

- 拡張子フィルタ（`--ext`）
- 除外パターン（`--exclude`）
- ドライラン（`--dry-run`）
- 古い世代の自動削除（`--keep`）
- 実行結果サマリー表示（探索/コピー/スキップ/削除件数）

## 基本コマンド

```bash
python automation.py --source ./data --dest ./backup --ext .txt .csv --exclude '*.tmp' --keep 14
```

## まずは安全確認（ドライラン）

```bash
python automation.py --source ./data --dest ./backup --dry-run
```

## 設定ファイルで実行

```bash
python automation.py --config backup_config.example.json
```

## 設定ファイル例

`backup_config.example.json`:

```json
{
  "source": "./data",
  "dest": "./backup",
  "ext": [".txt", ".csv", ".log"],
  "exclude": ["*.tmp", "cache/*"],
  "keep": 7
}
```

## 運用のコツ

- まず `--dry-run` で対象確認
- 問題なければ cron / タスクスケジューラで定期実行
- `--keep` を小さくしすぎると復元候補が減るため注意
