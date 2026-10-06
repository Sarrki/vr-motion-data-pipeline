import pandas as pd
import numpy as np
import plotly.graph_objects as go

def build_3d_player(csv_path):
    print("Загружаем датасет...")
    df = pd.read_csv(csv_path)
    
    # Берем каждый 10-й кадр для гарантированной плавности без зависаний
    df_anim = df.iloc[::10].reset_index(drop=True)
    
    frames = []
    
    print("Подготовка облака точек для анимации...")
    for i in range(len(df_anim)):
        # Сбор координат левой руки (26 точек)
        lh_x = [df_anim.loc[i, f'lh_j{j}_x'] for j in range(26)]
        lh_y = [df_anim.loc[i, f'lh_j{j}_y'] for j in range(26)]
        lh_z = [df_anim.loc[i, f'lh_j{j}_z'] for j in range(26)]
        
        # Сбор координат правой руки (26 точек)
        rh_x = [df_anim.loc[i, f'rh_j{j}_x'] for j in range(26)]
        rh_y = [df_anim.loc[i, f'rh_j{j}_y'] for j in range(26)]
        rh_z = [df_anim.loc[i, f'rh_j{j}_z'] for j in range(26)]
        
        # Голова
        hx, hy, hz = df_anim.loc[i, 'head_x'], df_anim.loc[i, 'head_y'], df_anim.loc[i, 'head_z']
        
        # Объединяем все точки кадра в единые три массива (строгая структура для Plotly)
        all_x = [hx] + lh_x + rh_x
        all_y = [hy] + lh_y + rh_y
        all_z = [hz] + lh_z + rh_z
        
        # 1 красная (голова), 26 синих (левая), 26 зеленых (правая)
        colors = ['red'] + ['blue'] * 26 + ['green'] * 26
        sizes = [14] + [6] * 26 + [6] * 26
        
        frames.append(go.Frame(
            data=[go.Scatter3d(
                x=all_x, y=all_y, z=all_z,
                mode='markers',
                marker=dict(size=sizes, color=colors)
            )],
            name=str(i)
        ))

    initial_data = frames[0].data

    fig = go.Figure(
        data=initial_data,
        layout=go.Layout(
            title="VR Облако точек (Красный: Голова, Синий: Левая, Зеленый: Правая)",
            scene=dict(
                xaxis=dict(title="X"),
                yaxis=dict(title="Y"),
                zaxis=dict(title="Z"),
                aspectmode='data'
            ),
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    # Включаем redraw=True, чтобы анимация физически шла
                    dict(label="▶ Play", method="animate", args=[None, {"frame": {"duration": 30, "redraw": True}, "fromcurrent": True}]),
                    dict(label="⏸ Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}])
                ]
            )]
        ),
        frames=frames
    )
    
    sliders = [dict(
        steps=[dict(method='animate', args=[[f.name], dict(mode='immediate', frame=dict(duration=30, redraw=True))], label=f"Кадр {f.name}") for f in frames],
        x=0, y=0
    )]
    fig.update_layout(sliders=sliders)
    
    print("Открываем плеер...")
    fig.show()

if __name__ == "__main__":
    build_3d_player("clean_ai_dataset.csv")
