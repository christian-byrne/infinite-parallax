import subprocess

def stack_videos(input_videos, output_video):
    # Generate a filter complex string to stack the videos vertically
    filter_complex = ""
    for i, video in enumerate(input_videos):
        filter_complex += f"[{i}:v]scale=iw:ih, pad=iw:1920/{len(input_videos)} [v{i}];"
    for i in range(len(input_videos)):
        filter_complex += f"[v{i}]"

    # Use ffmpeg to stack the videos
    subprocess.run([
        'ffmpeg',
        '-i', input_videos[0],  # Use the first video to set the output format
        '-filter_complex', filter_complex + 'concat=n=' + str(len(input_videos)) + ':v=1:a=0[v]',
        '-map', '[v]',
        output_video
    ])

# Example usage:
# input_videos = ['video1.mp4', 'video2.mp4', 'video3.mp4', 'video4.mp4', 'video5.mp4']
# output_video = 'combined_video.mp4'
# stack_videos(input_videos, output_video)