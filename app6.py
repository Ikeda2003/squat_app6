import streamlit as st
import cv2
import numpy as np
import math
import mediapipe as mp
import tempfile
import os
import ffmpeg

# パスワード設定
PASSWORD = "squat65738998"  # 任意のパスワードに変更

# MediaPipeのモデルを初期化
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# パスワード入力欄
st.title("🏋️ スクワット姿勢解析アプリ（MediaPipe）")

password = st.text_input("パスワードを入力してください:", type="password")

if password == PASSWORD:
    # パスワードが正しい場合、スクワット姿勢解析のアプリを表示
    st.markdown("**📸 アップロード前にご確認ください：**")
    st.info("動画は **身体が真横から撮影されている** 状態でご使用ください。正しい姿勢評価のために必要です。")

    # MediaPipeのクレジット表記
    st.markdown("**クレジット**")
    st.markdown("This app uses **[MediaPipe](https://mediapipe.dev/)** for pose estimation.")

    uploaded_file = st.file_uploader("動画ファイルをアップロード", type=["mp4", "mov", "avi"])

    # 回転角度の選択肢を追加
    rotation_angle = st.selectbox("動画の左向き回転角度を選択", [0, 90, 180, 270])

    # 開始秒数と終了秒数の入力欄
    start_time = st.number_input("開始秒数", min_value=0.0, step=0.1, format="%.1f")
    end_time = st.number_input("終了秒数 (省略すると最後まで)", min_value=0.0, step=0.1, format="%.1f", value=0.0)

    def calculate_angle(a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)

    def rotate_frame(frame, angle):
        """指定された角度でフレームを回転し、条件に応じて反転"""
        if angle == 90:
            frame = cv2.transpose(frame)  # 90度回転
            return cv2.flip(frame, 0)  # 上下反転
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)  # 180度回転（反転なし）
        elif angle == 270:
            frame = cv2.transpose(cv2.rotate(frame, cv2.ROTATE_180))  # 270度回転
            return cv2.flip(frame, 0)  # 上下反転
        else:
            return frame  # 0度回転（反転なし）

    if uploaded_file:
        # 一時ファイルを作成
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())

        cap = cv2.VideoCapture(tfile.name)

        fps = cap.get(cv2.CAP_PROP_FPS)  # フレームレートを取得
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 総フレーム数を取得
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps) if end_time > 0 else total_frames

        squat_count = 0
        down = False
        best_knee_angle = 180
        best_hip_angle = 180
        total_knee_score = 0
        total_hip_score = 0
        count = 0

        stframe = st.empty()

        current_frame = 0

        # 開始秒数になるまでフレームをスキップ
        while current_frame < start_frame:
            ret, _ = cap.read()
            if not ret:
                break
            current_frame += 1

        # 開始時間に達したら動画処理を開始
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or current_frame > end_frame:
                break

            if current_frame >= start_frame:
                # 指定された角度で回転
                frame = rotate_frame(frame, rotation_angle)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(frame_rgb)

                if results.pose_landmarks:
                    # 単一の人物のランドマークを処理
                    landmarks = results.pose_landmarks.landmark
                    left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]
                    left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
                    left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y]
                    left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]

                    knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                    hip_angle = calculate_angle(left_shoulder, left_hip, left_knee)

                    cv2.putText(frame, f"Knee: {int(knee_angle)}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(frame, f"Hip: {int(hip_angle)}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

                    if knee_angle < 100 and hip_angle < 100 and not down:
                        down = True
                        best_knee_angle = knee_angle
                        best_hip_angle = hip_angle
                    else:
                        if down:
                            best_knee_angle = min(best_knee_angle, knee_angle)
                            best_hip_angle = min(best_hip_angle, hip_angle)

                    if knee_angle > 100 and hip_angle > 100 and down:
                        squat_count += 1
                        down = False

                        min_knee_angle = best_knee_angle
                        min_hip_angle = best_hip_angle

                        # ひざスコア
                        knee_score = max(0, 100 - abs(min_knee_angle - 50))
                        hip_score = 100 if min_hip_angle <= 30 else max(0, 100 - (min_hip_angle - 30))

                        total_knee_score += knee_score
                        total_hip_score += hip_score
                        count += 1

                    cv2.putText(frame, f"Squat Count: {squat_count}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    mp.solutions.drawing_utils.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                stframe.image(frame, channels="BGR")

            current_frame += 1

        cap.release()

        if count > 0:
            avg_knee_score = total_knee_score / count
            avg_hip_score = total_hip_score / count
            average_score = (avg_knee_score + avg_hip_score) / 2

            st.success(f"✅ スクワット回数: {squat_count} 回")
            st.success(f"🦵 平均ひざスコア: {avg_knee_score:.2f} 点")
            st.success(f"🪑 平均腰スコア: {avg_hip_score:.2f} 点")
            st.success(f"📊 平均総合スコア: {average_score:.2f} 点")

        else:
            st.warning("スクワットが正しく行われませんでした")

        tfile.close()
        os.unlink(tfile.name)

else:
    # パスワードが間違っている場合、エラーメッセージを表示
    st.error("⚠️ パスワードが間違っています。再度入力してください。")
