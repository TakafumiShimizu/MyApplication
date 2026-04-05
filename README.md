# 自動化プログラム（ファイルバックアップ）

指定ディレクトリ内のファイルを拡張子でフィルタし、日時付きフォルダへ自動コピーする Python スクリプトです。

## 使い方

```bash
python automation.py --source ./data --dest ./backup --ext .txt .csv .log
```

ドライラン（実際にはコピーしない）:

```bash
python automation.py --source ./data --dest ./backup --dry-run
```

設定ファイルを使う場合:

```bash
python automation.py --config backup_config.example.json
```

## 主な機能

- 拡張子指定で対象ファイルを選択
- サブディレクトリを含めて再帰的に探索
- バックアップ先に `YYYYMMDD_HHMMSS` のフォルダを自動作成
- `--dry-run` で事前確認可能
