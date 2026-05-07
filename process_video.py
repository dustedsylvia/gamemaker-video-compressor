import sys
import subprocess
import os
import urllib.request
import shutil
import cv2

if shutil.which("ffmpeg"):
    ffmpeg_path = "ffmpeg"
    print("a version of ffmpeg is on PATH, skipping...")
else:
    if os.path.isfile("ffmpeg-windows.exe"):
        print("ffmpeg has already been downloaded, skipping...")
        ffmpeg_path = ".\\ffmpeg-windows.exe"
    else:
        print("ffmpeg not found, downloading...", end="")
        urllib.request.urlretrieve("https://github.com/eugeneware/ffmpeg-static/releases/latest/download/ffmpeg-win32-x64", "ffmpeg-windows.exe")
        print("done.")
        ffmpeg_path = ".\\ffmpeg-windows.exe"
    
try:
    video = sys.argv[1]
    if video.count(".") > 1:
        target = video.split()[:-1]+".mp4"
    else:
        target = video.split(".")[0]+"_processed."+video.split(".")[1]
except:
    print("No video specified, exiting...\n(You can input a video by dragging the icon onto this EXE.)")
    os.system("pause")
    sys.exit(1)

if os.path.isfile(target):
    cleanup = input("Warning! A target with this filename already exists. Overwrite? [Y/n]: ")
    if cleanup.lower() != "n":
        try:
            subprocess.run(["del", target], check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Deleted!")
        except subprocess.CalledProcessError:
            print("Fatal: Failed to delete the old file. Check and make sure that you have the right permissions to do this.")
            sys.exit(1)
    else:
        print("Will not overwrite, exiting...")
        sys.exit(0)

try:
    compression_factor = sys.argv[2]
except:
    compression_factor = "24"
    print("No compression factor specified. Using 24 as the default.")

if os.path.isfile("PROCESSOR_TMP.MKV") or os.path.isfile("PROCESSOR_TMP2.MKV"):
    print("Cleaning up temporary files (the program likely did not execute successfully last time...)")
    subprocess.run(["del", "PROCESSOR_TMP.MKV"], check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["del", "PROCESSOR_TMP2.MKV"], check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
else:
    print("No temporary files to clean up, skipping...")


print(f"Processing video. Video will be output as {target}.")
print("Beginning phase 1 (rescaling)...", end="")
sys.stdout.flush()

p1 = subprocess.run([ffmpeg_path, '-i', video, '-s', '320x240', '-c:a', 'copy', 'PROCESSOR_TMP.MKV'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if p1.returncode > 0:
    print(f"failed.\nFatal: rescaling the video failed with exit code {p1.returncode}.")
    sys.exit(1)

print("done.")
print("Beginning phase 2 (compression)...", end="")
sys.stdout.flush()

tmpV = cv2.VideoCapture(video)
if tmpV.get(cv2.CAP_PROP_FPS) > 30:
    p2 = subprocess.run([ffmpeg_path, '-i', 'PROCESSOR_TMP.MKV', '-vcodec', 'libx264', '-crf', compression_factor, '-preset', 'medium', '-filter:v', 'fps=30', 'PROCESSOR_TMP2.MKV'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    limitedFPS = True
else:
    p2 = subprocess.run([ffmpeg_path, '-i', 'PROCESSOR_TMP.MKV', '-vcodec', 'libx264', '-crf', compression_factor, '-preset', 'medium', 'PROCESSOR_TMP2.MKV'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    limitedFPS = False
tmpV.release()

if p2.returncode > 0:
    print(f"failed.\nFatal: compressing the video failed with exit code {p2.returncode}.")
    sys.exit(1)

print("done.")
print("Beginning phase 3 (stripping audio)...", end="")
sys.stdout.flush()

p3 = subprocess.run([ffmpeg_path, '-i', 'PROCESSOR_TMP2.MKV', '-an', '-c:v', 'copy', target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if p3.returncode > 0:
    print(f"failed.\nFatal: stripping the audio tracks failed with exit code {p2.returncode}.")
    sys.exit(1)

print("done.")
print("Removing temporary files...", end="")
sys.stdout.flush()

try:
    subprocess.run(["del", "PROCESSOR_TMP.MKV"], check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["del", "PROCESSOR_TMP2.MKV"], check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    print("failed.\nAnomaly: One or more of the temporary files do not seem to exist. Checking the existence of the final video.")
    if os.path.isfile(target):
        print("Final video exists. Ignoring anomaly.")
    else:
        print("The final video was not created!")
        print("You may need to try running the commands manually:\n")
        print(f"{ffmpeg_path} -i {video} -s 320x240 -c:a copy PROCESSOR_TMP.MKV")
        print(f"{ffmpeg_path} -i PROCESSOR_TMP.MKV -vcodec libx264 -crf {compression_factor} -preset medium PROCESSOR_TMP2.MKV")
        print(f"{ffmpeg_path} -i PROCESSOR_TMP2.MKV -an -c:v copy {target}")
        print("del PROCESSOR_TMP.MKV")
        print("del PROCESSOR_TMP2.MKV")

        print("All of the parameters have been filled out for you based on input.")

        sys.exit(1)

print("done.\n")

if ffmpeg_path == ".\\ffmpeg-windows.exe":
    cleanup = input("Delete the downloaded ffmpeg? [Y/n]: ")
    if cleanup.lower() != "n":
        try:
            subprocess.run(["del", "ffmpeg-windows.exe"], check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Deleted!")
        except subprocess.CalledProcessError:
            print("Failed to delete ffmpeg. Check and make sure you have the right permissions to do this.")

print("Video successfully compressed!\n")
print("Summary of what was performed on the video file:")
print("   1. The video was rescaled to 320x240.")
if limitedFPS:
    print(f"   2. The video was compressed by a factor of {compression_factor}, and the FPS was limited to 30.")
else:
    print(f"   2. The video was compressed by a factor of {compression_factor}.")
print("   3. The audio was stripped from the video.")
print("(Note: This is not everything that was done. A lot more happened behind the scenes.)\n")
print(f"The output can be found at: {target}.")