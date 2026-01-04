トイレ探索アプリ 開発環境起動手順書

このドキュメントは、ローカル環境で「バックエンド（API）」と「フロントエンド（画面）」を起動するための手順をまとめたものです。

📁 フォルダ構成の前提

ターミナルで作業する際は、ルートフォルダ（toilet_finder_api）にいることを前提としています。

1. バックエンド (Python/FastAPI) の起動

APIサーバー（api.py）を起動します。これがないと地図にピンが表示されません。

手順

ターミナルを開き、プロジェクトフォルダに移動します。

以下のコマンドを順番に実行します。

Windows (PowerShell) の場合:

# 1. 仮想環境を有効化 (行頭に (venv) が表示されればOK)
.\venv\Scripts\activate

# 2. サーバーを起動
python api.py



Mac / Linux の場合:

source venv/bin/activate
python api.py



成功確認

ターミナルに Application startup complete. と表示されれば成功です。

ブラウザで http://127.0.0.1:8000 にアクセスし、{"message": "Toilet Finder API is running!"} と表示されるか確認してください。

2. フロントエンド (Next.js) の起動

アプリの画面を起動します。バックエンドとは別の新しいターミナルを開いて実行してください。

手順

新しいターミナルを開き、プロジェクトフォルダに移動します。

以下のコマンドを実行します。

yarn dev



成功確認

ターミナルに ready - started server on 0.0.0.0:3000 と表示されれば成功です。

ブラウザで http://localhost:3000 を開くとアプリが表示されます。

🛠 初回セットアップ（環境を作り直す場合）

久しぶりに開発する場合や、別のパソコンで動かす場合は、以下の手順で環境を構築してください。

1. バックエンドの準備

# 1. 仮想環境の作成 (Python 3.12を指定)
py -3.12 -m venv venv

# 2. 仮想環境の有効化
.\venv\Scripts\activate

# 3. ライブラリの一括インストール
pip install -r requirements.txt



2. フロントエンドの準備

# パッケージのインストール
yarn install



⚠️ よくあるトラブルと解決策

Q. api.py を実行したら ModuleNotFoundError が出る

A. 仮想環境が有効になっていません。
.\venv\Scripts\activate を実行して、ターミナルの左端に (venv) が出ている状態で実行してください。

Q. yarn dev でエラーが出る

A. 必要なパッケージが足りていない可能性があります。
一度 yarn install を実行してから、再度 yarn dev を試してください。

Q. アプリで「検索エラー」や「404」が出る

A. バックエンド（API）が起動していないか、エラーで止まっている可能性があります。
バックエンド側のターミナルを確認し、止まっていれば python api.py で再起動してください。