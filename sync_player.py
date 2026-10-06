import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import cv2
import os

# Настраиваем широкую страницу Streamlit
st.set_page_config(layout="wide", page_title="VR Motion & Video Sync")

st.title("🎬 Синхронный плеер: Видео MP4 + 3D-Трекинг VR")

CSV_PATH = "clean_ai_dataset.csv"
VIDEO_PATH = "CameraRecord_20260505_165740.mp4".replace(".txt", ".mp4") # Автоматически ищет видео с тем же именем, либо впишите "video.mp4"

@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

# Если видео называется просто video.mp4, проверим этот вариант
if not os.path.exists(VIDEO_PATH) and os.path.exists("video.mp4"):
    VIDEO_PATH = "CameraRecord_20260505_165740.mp4"

if not os.path.exists(VIDEO_PATH):
    st.error(f"Файл видео '{VIDEO_PATH}' не найден в папке VIS! Переименуйте ваше видео в 'video.mp4' или укажите имя в коде.")
else:
    df_full = load_data(CSV_PATH)
    total_vr_frames = len(df_full) # 4357 кадров

    # Открываем видео для получения общего количества кадров
    cap = cv2.VideoCapture(VIDEO_PATH)
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    # --- ИНТЕРФЕЙС УПРАВЛЕНИЯ В БОКОВОЙ ПАНЕЛИ ---
    st.sidebar.header("⚙️ Настройки синхронизации")
    
    # Математически точный коэффициент соотношения частот (4357 / 1456)
    exact_ratio = total_vr_frames / total_video_frames
    st.sidebar.write(f"Авто-коэффициент скорости: **{exact_ratio:.3f}**")
    
    # Ручное смещение (Offset) на случай задержки старта записи
    offset = st.sidebar.slider("Смещение видео (кадры)", min_value=-150, max_value=150, value=0, step=1)
    
    # Главный слайдер таймлайна (теперь идет строго от 0 до конца кадров трекинга)
    current_vr_frame = st.slider("Ползунок времени (Кадр VR трекинга)", min_value=0, max_value=total_vr_frames-1, value=0)

    # --- РАСЧЕТ КАДРА ВИДЕО ---
    video_frame_target = int((current_vr_frame / exact_ratio) + offset)
    video_frame_target = max(0, min(video_frame_target, total_video_frames - 1))
    
    # Извлекаем нужный кадр из видеофайла
    cap = cv2.VideoCapture(VIDEO_PATH)
    cap.set(cv2.CAP_PROP_POS_FRAMES, video_frame_target)
    ret, frame = cap.read()
    cap.release()

    # --- ОТРИСОВКА КОЛОНОК ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📹 Исходное видео")
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, use_column_width=True, caption=f"Кадр видео: {video_frame_target} / {total_video_frames}")
        else:
            st.warning("Не удалось прочитать кадр видео.")

    with col2:
        st.subheader("🤖 3D-Облако точек VR")
        
        # Вытаскиваем координаты по точному индексу current_vr_frame
        lh_x = [df_full.loc[current_vr_frame, f'lh_j{j}_x'] for j in range(26)]
        lh_y = [df_full.loc[current_vr_frame, f'lh_j{j}_y'] for j in range(26)]
        lh_z = [df_full.loc[current_vr_frame, f'lh_j{j}_z'] for j in range(26)]
        
        rh_x = [df_full.loc[current_vr_frame, f'rh_j{j}_x'] for j in range(26)]
        rh_y = [df_full.loc[current_vr_frame, f'rh_j{j}_y'] for j in range(26)]
        rh_z = [df_full.loc[current_vr_frame, f'rh_j{j}_z'] for j in range(26)]
        
        hx = df_full.loc[current_vr_frame, 'head_x']
        hy = df_full.loc[current_vr_frame, 'head_y']
        hz = df_full.loc[current_vr_frame, 'head_z']
        
        # ИСПРАВЛЕНО: Инвертируем знак минус для всех координат X, чтобы убрать эффект зеркала
        all_x = [-hx] + [-x for x in lh_x] + [-x for x in rh_x]
        all_y = [hy] + lh_y + rh_y
        all_z = [hz] + lh_z + rh_z
        
        colors = ['red'] + ['blue'] * 26 + ['green'] * 26
        sizes = [14] + [6] * 26 + [6] * 26
        
        fig = go.Figure(data=[go.Scatter3d(
            x=all_x, y=all_y, z=all_z,
            mode='markers', marker=dict(size=sizes, color=colors)
        )])
        
        fig.update_layout(
            scene=dict(
                xaxis=dict(range=[-1.0, 1.0], title="Влево / Вправо"), 
                yaxis=dict(range=[-1.0, 1.0], title="Вперед / Назад"), 
                zaxis=dict(range=[-1.0, 1.0], title="Выше / Ниже"), 
                aspectmode='manual', 
                aspectratio=dict(x=1, y=1, z=1)
            ),
            margin=dict(l=0, r=0, b=0, t=0), height=500
        )
        st.plotly_chart(fig, use_container_width=True)
