import subprocess

def create_sliding_transition(input_image1, input_image2, output_video, slide_speed):
    # Calculate the duration of the sliding transition based on slide_speed
    # For example, if slide_speed is 100 pixels per second, and the width of the image is 1920 pixels,
    # the duration will be width / slide_speed seconds
    duration = 1920 / slide_speed

    # Use ffmpeg to create the sliding transition
    subprocess.run([
        'ffmpeg',
        '-loop', '1', '-i', input_image1,
        '-loop', '1', '-i', input_image2,
        '-filter_complex', f'[0:v]setpts=PTS-STARTPTS[v0];[1:v]setpts=PTS-STARTPTS+{duration}/TB[v1];[v0][v1]overlay=x=\'min(-W+(W-W*{slide_speed}*t),0)\':y=0:shortest=1[v]',
        '-map', '[v]',
        '-c:v', 'libx264',
        '-t', str(duration),
        '-pix_fmt', 'yuv420p',
        output_video
    ])

# Example usage:
# create_sliding_transition('image1.jpg', 'image2.jpg', 'sliding_transition.mp4', 100)