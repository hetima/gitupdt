# gitupdt

Gitリポジトリを簡単に更新するためのPythonツールです。リモートリポジトリの更新を確認し、インタラクティブなメニューからブランチのプルやタグへの切り替えを行えます。

**このツールはソフトウェアとして利用する目的などでクローンし、編集は行わない実行環境用リポジトリで使用することを想定しています。開発用のリポジトリで使用することはお勧めしません。**


## 機能

- **リモート更新の確認**: リモートリポジトリに更新があるかどうかをチェック
- **インタラクティブな選択メニュー**: questionaryによる対話的なCLI
- **ブランチのプル**: 現在のブランチを最新の状態に更新
- **タグへのチェックアウト**: 指定したバージョンタグに切り替え
- **リセットモード**: `--reset` オプションで `git reset --hard` を使用して更新
- **requirements.txtの変更表示とインストール**: 依存関係ファイルの変更差分を表示し、自動インストールをサポート
- **pyproject.tomlの変更表示とuv sync**: uvがインストールされている場合、pyproject.tomlのdependenciesセクションの変更を検出してuv syncを実行
- **仮想環境の自動検出**: `.venv` または `venv` フォルダを自動的に検出し、適切なPythonインタープリタを選択肢に表示
- **リポジトリメンテナンス**: 更新後に自動で `git gc --auto` を実行

## インストール

```bash
pip install gitupdt
```

## 使用方法

### カレントディレクトリのリポジトリを更新

```bash
gitupdt
```

### 指定したパスのリポジトリを更新

```bash
gitupdt /path/to/repo
```

### リセットモードで更新

`--reset` オプションを指定すると、`git checkout` や `git pull` の代わりに `git reset --hard` を使用して更新します。これはローカルのファイルが壊れている場合に、リモートの状態で強制的に上書きするのに便利です。

```bash
gitupdt --reset
```

```bash
gitupdt /path/to/repo --reset
```

## 選択可能なアクション

ツールを実行すると、以下のアクションから選択できます：

1. **Checkout and Pull latest remote**: リモートのデフォルトブランチをチェックアウトしてプル
2. **Pull**: 現在のブランチを最新の状態に更新（リモートより遅れている場合）
3. **タグのチェックアウト**: 指定したバージョンタグに切り替え（最新タグや過去のタグから選択）

### requirements.txtの変更時の自動インストール

`requirements.txt` に変更がある場合、以下の処理が行われます：

1. 変更差分がunified diff形式で表示されます
2. 更新された `requirements.txt` をインストールするかどうか確認されます
3. 適切なインストールコマンドを選択できます：
   - uvがインストールされている場合：`uv pip install` または `uv add`（pyproject.tomlが存在する場合のみ）
   - 現在実行中のPython
   - 検出された仮想環境（`.venv` または `venv`）のPython
4. 選択したコマンドでインストールが実行されます
5. キャンセルして後から手動でインストールすることを選ぶこともできます

### pyproject.tomlの変更時のuv sync

uvがインストールされており、`pyproject.toml` が存在する場合、以下の処理が行われます：

1. `pyproject.toml` の `dependencies` セクションの変更差分がunified diff形式で表示されます
2. `uv sync` を実行して依存関係を更新するかどうか確認されます
3. `uv sync` を選択すると依存関係が更新されます
4. キャンセルして後から手動で更新することを選ぶこともできます

※ `pyproject.toml` に変更があった場合は、`requirements.txt` の変更確認は行われません。

## 更新履歴

### 1.1.0
- uvのパッケージインストール対応を追加
  - uvがインストールされている場合、`uv pip install`と`uv add`のオプションが利用可能になりました
- pyproject.tomlの変更検出とuv syncを追加
  - `pyproject.toml`の`dependencies`セクションの変更を検出するようになりました
  - 変更が検出された場合、自動的に`uv sync`の実行を促します
- 最小Pythonバージョンを3.9から3.11に変更（tomllib使用のため）

## 依存関係

- GitPython
- questionary
- packaging

## Pythonバージョン

Python 3.11 以上が必要です。

## ライセンス

MIT License
