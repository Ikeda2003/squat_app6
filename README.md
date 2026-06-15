# スクワット姿勢解析アプリ

MediaPipe と Streamlit を用いて，横向きで撮影したスクワット動画から姿勢を解析するアプリです．  
動画内の人物の関節位置を推定し，スクワット回数，ひざスコア，腰スコア，総合スコアを表示します．
- アプリ：https://huggingface.co/spaces/tuuree123/squat-evaluator
- 動作確認用パスワード：squat60410745
- デモ動画URL：https://drive.google.com/file/d/1YdVaNKiwSYCSeOLI1cCJ5TgvJ1EPI-hu/view?usp=sharing)(github : https://github.com/Ikeda2003/squat_app6
## 概要

本アプリは，アップロードした動画に対して姿勢推定を行い，スクワット動作を解析することを目的としています．  
MediaPipeにより身体のランドマークを取得し，肩・腰・ひざ・足首の位置から関節角度を計算します．  
その結果をもとに，スクワットの回数とフォーム評価を行います．

## 主な機能

- 動画ファイルのアップロード
- パスワード認証
- 動画の回転補正
- 開始秒数・終了秒数の指定
- スクワット回数のカウント
- ひざ角度・腰角度の可視化
- 平均ひざスコア，平均腰スコア，平均総合スコアの表示
- MediaPipe による骨格描画

## 動作環境

- Python 3.9 以上推奨
- Streamlit
- OpenCV
- NumPy
- MediaPipe
- ffmpeg-python

## インストール

必要なライブラリをインストール

```bash
pip install streamlit opencv-python numpy mediapipe ffmpeg-python
