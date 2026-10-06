import json
import re
import pandas as pd
import numpy as np

def parse_vr_jsonl(file_path):
    parsed_records = []
    num_pattern = re.compile(r'-?\d+,\d+|-?\d+\.\d+|-?\d+')

    def extract_floats(text_string):
        if not text_string or not isinstance(text_string, str):
            return []
        raw_parts = num_pattern.findall(text_string)
        return [float(p.replace(',', '.')) for p in raw_parts]

    print("Начинаем чтение файла...")
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line or "notice" in line:
                continue
                
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            record = {}
            record['predict_time'] = data.get('predictTime', 0)
            
            # 1. Парсим Голову (Head)
            if 'Head' in data and 'pose' in data['Head']:
                head_vals = extract_floats(data['Head']['pose'])
                if len(head_vals) >= 7:
                    record['head_x'], record['head_y'], record['head_z'] = head_vals[0:3]
                    record['head_qx'], record['head_qy'], record['head_qz'], record['head_qw'] = head_vals[3:7]

            # 2. ИСПРАВЛЕНО: Парсим Руки (Раздельный сбор данных для каждой руки)
            for hand_name, prefix in [('leftHand', 'lh'), ('rightHand', 'rh')]:
                if 'Hand' in data and hand_name in data['Hand']:
                    hand_data = data['Hand'][hand_name]
                    if hand_data.get('isActive') == 1:
                        joints = hand_data.get('HandJointLocations', [])
                        
                        # Собираем данные всех 26 суставов
                        for j_idx, joint in enumerate(joints):
                            p_vals = extract_floats(joint.get('p'))
                            if len(p_vals) >= 7:
                                # ВАЖНО: Теперь префиксы rh_ и lh_ жестко разделены!
                                record[f'{prefix}_j{j_idx}_x'] = p_vals[0]
                                record[f'{prefix}_j{j_idx}_y'] = p_vals[1]
                                record[f'{prefix}_j{j_idx}_z'] = p_vals[2]
                                record[f'{prefix}_j{j_idx}_qx'] = p_vals[3]
                                record[f'{prefix}_j{j_idx}_qy'] = p_vals[4]
                                record[f'{prefix}_j{j_idx}_qz'] = p_vals[5]
                                record[f'{prefix}_j{j_idx}_qw'] = p_vals[6]
            
            if 'head_x' in record:
                parsed_records.append(record)
                
    df = pd.DataFrame(parsed_records)
    
    # Сразу заполняем пустые ячейки (NaN) нулями, чтобы ИИ не ругался
    df = df.fillna(0.0)
    
    print(f"Парсинг окончен. Собрано кадров: {len(df)}")
    return df

if __name__ == "__main__":
    # Указываем ваше точное имя файла
    INPUT_FILE = "trackingData_20260505_165740.txt" 
    
    df_raw = parse_vr_jsonl(INPUT_FILE)
    if not df_raw.empty:
        df_raw.to_csv("clean_ai_dataset.csv", index=False)
        print("Идеальный датасет экспортирован в clean_ai_dataset.csv!")
