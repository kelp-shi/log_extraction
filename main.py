import datetime
import glob
import re
import os

def extract_timestamp(line):
    start = line.find('[')
    end = line.find(']')
    if start == -1 or end == -1:
        return None
    date_str = line[start+1:end]
    try:
        timestamp = datetime.datetime.strptime(date_str, '%d/%b/%Y:%H:%M:%S %z')
    except ValueError as e:
        print("タイムスタンプ解析エラー:", e)
        return None
    return timestamp

def extract_ip(line):
    ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    match = re.search(ip_pattern, line)
    if match:
        return match.group()
    else:
        return None

def filter_logs_multiple(file_path, target_string, time_window=60):
    # セッションのリスト
    sessions = []
    # 現在のセッション開始時刻
    current_session_start = None
    # 現在のセッションに該当するログ行
    current_session_lines = []

    with open(file_path, 'r', encoding='utf-8') as f:
        current_ip = []
        for line in f:

            ts = extract_timestamp(line)
            if ts is None:
                continue
            now_ip = extract_ip(line)
            if now_ip is None:
                continue

            # ターゲット行が現れた場合
            if target_string in line:
                # 既にセッション中なら、前回のセッションを終了して保存
                if current_session_lines:
                    if now_ip in current_ip:
                        continue
                    if now_ip not in current_ip:
                        current_ip.append(now_ip)
                        sessions.append(current_session_lines)
                current_session_start = ts
                current_session_lines = [line]
                continue

            if current_session_start:
                elapsed = (ts - current_session_start).total_seconds()
                if elapsed <= time_window:
                    if now_ip in current_ip:
                        continue
                    if now_ip not in current_ip:
                        current_ip.append(now_ip)
                    current_session_lines.append(line)
                else:
                    if now_ip in current_ip:
                        continue
                    if now_ip not in current_ip:
                        current_ip.append(now_ip)
                        sessions.append(current_session_lines)
                    current_session_start = None
                    current_session_lines = []

    if current_session_lines:
        if now_ip in current_ip:
            return
        if now_ip not in current_ip:
            current_ip.append(now_ip)
        sessions.append(current_session_lines)

    return sessions

if __name__ == '__main__':
    files = glob.glob("logs/*")
    fileNum = 1
    # フォルダがなければつくる
    if not os.path.exists('output'):
        os.makedirs('output')
    for file in files:
        file_path = file
        target = '"POST / HTTP/2.0" 302 0'
        sessions = filter_logs_multiple(file_path, target, time_window=60)

        output_file = os.path.join('output', f"{fileNum}filtered_sessions.txt")

        # ファイルに書き込み処理
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for i, session in enumerate(sessions, start=1):
                out_file.write(f"--- Session {i} ---\n")
                for line in session:
                    out_file.write(line)

        print(f"Filtered sessions have been saved to: {output_file}")
        fileNum+=1