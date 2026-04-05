# 自動化プログラム（ファイルバックアップ）

このプログラムは、指定したフォルダ内のファイルを
**拡張子で絞り込んで**、**日時付きフォルダ**に自動コピーします。

## できること

- `.txt` や `.csv` など、対象拡張子を指定できる
- サブフォルダも含めてまとめて探索する
- バックアップ先を `YYYYMMDD_HHMMSS` で分けて保存する
- `--dry-run` で「実際にはコピーせず確認だけ」できる

## 実行例

### 1) 引数で直接指定する

```bash
python automation.py --source ./data --dest ./backup --ext .txt .csv .log
```

### 2) ドライラン（コピーしない）

```bash
python automation.py --source ./data --dest ./backup --dry-run
```

### 3) 設定ファイルを使う

```bash
python automation.py --config backup_config.example.json
```
