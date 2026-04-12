"""
tl;dv動画からスライド画面を自動抽出するツール

【使用方法】
python tldv_slide_extractor.py <tldv_meeting_url> [--output_dir ./slides]

【処理内容】
1. tl;dvのミーティングページからPlaywrightで動画URLを取得
2. ffmpegで動画をダウンロード
3. シーン変化検出でスライド切り替えタイミングを特定
4. 各スライドのスクリーンショットを保存
5. 重複・非スライド画面をフィルタリング
"""

import subprocess
import sys
import json
import os
import re
import time
import tempfile
from pathlib import Path
from typing import Optional, List

# Chrome cookie reader for tldv auth
sys.path.insert(0, "/Users/takumiyoshikawa/Desktop/Tools/tldv-scraper")
try:
    from config import SESSION_DIR, TOKEN_CACHE
except ImportError:
    SESSION_DIR = Path("./session")
    TOKEN_CACHE = SESSION_DIR / "token_cache.json"


def get_video_url_via_playwright(meeting_url: str, timeout: int = 300) -> Optional[str]:
    """PlaywrightでtldvページからビデオURLを取得"""
    from playwright.sync_api import sync_playwright

    video_url = None

    with sync_playwright() as p:
        tmpdir = tempfile.mkdtemp(prefix='tldv_slide_')
        context = p.chromium.launch_persistent_context(
            user_data_dir=tmpdir,
            channel='chrome',
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-first-run']
        )

        page = context.pages[0] if context.pages else context.new_page()

        # セッション復元
        session_file = SESSION_DIR / 'session_state.json'
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    storage = json.load(f)
                if storage.get('cookies'):
                    context.add_cookies(storage['cookies'])
            except:
                pass

        # ネットワークリクエストからビデオURLをキャプチャ
        captured_urls = []

        def handle_response(response):
            url = response.url
            if any(ext in url for ext in ['.mp4', '.webm', '.m3u8', 'video', 'recording']):
                captured_urls.append(url)

        page.on("response", handle_response)

        print(f"tl;dvにアクセス中: {meeting_url}")
        page.goto(meeting_url, wait_until='networkidle', timeout=60000)

        # ログインチェック
        time.sleep(3)
        if 'login' in page.url or 'auth' in page.url:
            print(f"\n{'='*60}")
            print(f"{timeout}秒間待機します。ログインしてください。")
            print(f"{'='*60}\n")

            remaining = timeout
            while remaining > 0:
                if 'meetings' in page.url or 'app' in page.url:
                    print("ログイン検出!")
                    page.goto(meeting_url, wait_until='networkidle', timeout=60000)
                    break
                time.sleep(10)
                remaining -= 10
                print(f"  待機中... {remaining}秒残り")

        # ビデオ要素からURLを取得
        time.sleep(5)

        # 方法1: video/source要素から
        try:
            video_src = page.evaluate("""() => {
                const videos = document.querySelectorAll('video');
                for (const v of videos) {
                    if (v.src) return v.src;
                    const source = v.querySelector('source');
                    if (source && source.src) return source.src;
                }
                return null;
            }""")
            if video_src:
                video_url = video_src
                print(f"video要素からURL取得: {video_url[:80]}...")
        except:
            pass

        # 方法2: ネットワークキャプチャから
        if not video_url and captured_urls:
            for url in captured_urls:
                if '.mp4' in url or 'video' in url:
                    video_url = url
                    print(f"ネットワークからURL取得: {video_url[:80]}...")
                    break

        # 方法3: ページ内のAPIレスポンスからビデオURLを探す
        if not video_url:
            try:
                # tldvのAPIをダイレクトに叩く
                meeting_id = meeting_url.split('/')[-1]
                api_data = page.evaluate(f"""async () => {{
                    try {{
                        const resp = await fetch('/api/meetings/{meeting_id}');
                        return await resp.json();
                    }} catch(e) {{ return null; }}
                }}""")
                if api_data and isinstance(api_data, dict):
                    for key in ['videoUrl', 'video_url', 'recordingUrl', 'recording_url']:
                        if key in api_data:
                            video_url = api_data[key]
                            print(f"APIからURL取得: {video_url[:80]}...")
                            break
            except:
                pass

        # セッション保存
        try:
            state = context.storage_state()
            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            with open(session_file, 'w') as f:
                json.dump(state, f)
        except:
            pass

        context.close()

    return video_url


def download_video(url: str, output_path: str) -> bool:
    """ffmpegまたはcurlで動画をダウンロード"""
    print(f"動画をダウンロード中...")

    if '.m3u8' in url:
        # HLS stream
        cmd = ['ffmpeg', '-i', url, '-c', 'copy', '-y', output_path]
    else:
        cmd = ['curl', '-L', '-o', output_path, url]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print(f"ダウンロード完了: {output_path} ({os.path.getsize(output_path) // 1024 // 1024}MB)")
        return True
    else:
        print(f"ダウンロード失敗")
        return False


def extract_slides_with_scene_detection(video_path: str, output_dir: str, threshold: float = 0.3) -> List[str]:
    """シーン変化検出でスライド切り替えを検出してスクリーンショットを保存"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("シーン変化を検出中...")

    # シーン検出してタイムスタンプを取得
    cmd = [
        'ffmpeg', '-i', video_path,
        '-filter:v', f"select='gt(scene,{threshold})',showinfo",
        '-vsync', 'vfr',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # タイムスタンプを抽出
    timestamps = [0.0]  # 最初のフレームも含む
    for line in result.stderr.split('\n'):
        if 'pts_time:' in line:
            match = re.search(r'pts_time:(\d+\.?\d*)', line)
            if match:
                ts = float(match.group(1))
                # 最低2秒間隔を確保（同じスライドの微小変化を除外）
                if not timestamps or (ts - timestamps[-1]) >= 2.0:
                    timestamps.append(ts)

    print(f"検出されたシーン変化: {len(timestamps)}箇所")

    # 各タイムスタンプでスクリーンショットを取得
    saved_files = []
    for i, ts in enumerate(timestamps):
        # タイムスタンプの少し後（0.5秒後）のフレームを取得（切り替え途中を避ける）
        capture_ts = ts + 0.5
        minutes = int(capture_ts // 60)
        seconds = int(capture_ts % 60)

        output_file = os.path.join(output_dir, f"slide_{i+1:03d}_{minutes:02d}m{seconds:02d}s.png")

        cmd = [
            'ffmpeg', '-ss', str(capture_ts),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y', output_file
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if os.path.exists(output_file) and os.path.getsize(output_file) > 5000:
            saved_files.append(output_file)
            print(f"  保存: {os.path.basename(output_file)} ({minutes}:{seconds:02d})")

    return saved_files


def extract_slides_interval(video_path: str, output_dir: str, interval: int = 10) -> List[str]:
    """一定間隔でスクリーンショットを取得（フォールバック方法）"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 動画の長さを取得
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())

    print(f"動画の長さ: {int(duration // 60)}分{int(duration % 60)}秒")
    print(f"{interval}秒間隔でスクリーンショットを取得中...")

    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', f'fps=1/{interval}',
        '-q:v', '2',
        '-y', os.path.join(output_dir, 'frame_%04d.png')
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    saved_files = sorted(Path(output_dir).glob('frame_*.png'))
    print(f"取得したフレーム数: {len(saved_files)}")

    return [str(f) for f in saved_files]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='tl;dv動画からスライドを抽出')
    parser.add_argument('url', help='tl;dvミーティングURL')
    parser.add_argument('--output_dir', default='./slides', help='出力先ディレクトリ')
    parser.add_argument('--threshold', type=float, default=0.3, help='シーン変化の閾値')
    parser.add_argument('--interval', type=int, default=10, help='フォールバック時のフレーム間隔(秒)')

    args = parser.parse_args()

    # 1. 動画URLを取得
    video_url = get_video_url_via_playwright(args.url)

    if not video_url:
        print("動画URLを取得できませんでした")
        sys.exit(1)

    # 2. 動画をダウンロード
    video_path = os.path.join(args.output_dir, 'temp_video.mp4')
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    if not download_video(video_url, video_path):
        sys.exit(1)

    # 3. スライドを抽出
    slides = extract_slides_with_scene_detection(video_path, args.output_dir, args.threshold)

    if len(slides) < 5:
        print("シーン検出が少なすぎます。間隔方式にフォールバック...")
        slides = extract_slides_interval(video_path, args.output_dir, args.interval)

    print(f"\n完了: {len(slides)}枚のスライドを保存しました → {args.output_dir}")
