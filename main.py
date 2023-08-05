import argparse
import subprocess
from pathlib import Path

from loguru import logger
import platform

parser = argparse.ArgumentParser(description='合并米家摄像头视频，以天为单位。')
parser.add_argument('indir', help='原米家摄像头视频目录。')
parser.add_argument('--outdir', default='./', help='合并后视频存放目录，目录不存在会被创建。默认当前目录。')
args = parser.parse_args()
skip_filenames = []

def merge_vids(vidlist_file: str, tofile: str):
    """执行 ffmpeg 命令合并视频。"""
    # 需要对音频重新编码，否则会报错：
    # Could not find tag for codec pcm_alaw in stream #1, codec not currently supported in container when concatenating 2 files using ffmpeg
    # ffmpeg -y overwrite
    if platform.system().lower() == "windows":
        cmd = f"ffmpeg -f concat -safe 0 -i {vidlist_file} -c:v copy -c:a flac -strict -2 {tofile}"
        subprocess.run(cmd)
    else:
        cmd = f"ffmpeg -y -f concat -safe 0 -i {vidlist_file} -c:v copy -c:a aac -strict -2 {tofile}"
        subprocess.run(cmd,shell=True)

def merge_dirs(indir: str, outdir: str, date_name: str, parent_path: str):
    """合并目录下的监控文件，在当前目录生成以天为单位的视频。
    indir 结构：
    indir
        2021051001
        2021051002
        2021051003
        ...
    即，子目录结构为：年月日时。
    """
    if not Path(outdir).exists():
        logger.info(f'{outdir} 不存在，即将被创建')
        Path(outdir).mkdir(parents=True)

    date_dict = {}


    # 小米第一代文件目录有多层
    for d in Path(indir).iterdir():
        if d.is_file():
            # 兼容一级目录是视频文件
            date_dict[date_name] = [Path(indir)]
            break
        if not d.is_dir():
            continue
        date = d.stem[:8]
        if date not in date_dict:
            date_dict[date] = []
        date_dict[date].append(d)

    for ds_date, ds in date_dict.items():
        videos = []
        for d in ds:
            mp4_list = list(Path(d).glob("*.mp4"))
            videos.extend(mp4_list)

        if len(videos) == 0:
            # 往下层递归
            merge_dirs(Path(d), outdir, date_name, ds_date)
        logger.info(f"{ds_date}, {len(videos)} videos")
        if not videos:
            continue
        videos = sorted(videos, key=lambda f: int(f.stem.split("_")[-1]))
        videos = [
            "file " + str(f.resolve(strict=True)).replace("\\", "/") for f in videos
        ]

        merge_outdir = f'{outdir}/{date_name}/{parent_path}'
        if not Path(merge_outdir).exists():
            Path(merge_outdir).mkdir(parents=True)

        vidslist_path = f"{merge_outdir}/vidslist.txt"

        Path(vidslist_path).write_text("\n".join(videos), encoding="utf8")
        merge_vids(vidslist_path, Path(merge_outdir).joinpath(f"{ds_date}.mp4"))


def startup(indir: str, outdir: str):
    for date in Path(indir).iterdir():
        date_name = Path(date).name
        if date_name in skip_filenames:
            continue
        print(f"start merge:{date_name} video")
        merge_dirs(Path(date), outdir, date_name, "")


if __name__ == "__main__":
    startup(args.indir, args.outdir)