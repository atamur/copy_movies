__author__ = 'looser'

from subprocess import call

class HbEncoder:
    """
    Uses CLI of HandBrake to encode videos from JVC camera that were shoot with 16x9 setting.
    """
    def encode(self, source, target):
        cmd = ("C:/Program Files/Handbrake/HandBrakeCLI.exe "
               + "-i \"" + source + "\" -t 1 -c 1 "
               + "-o \"" + target + "\" "
               + "-f mp4 -4 --detelecine --decomb --denoise=\"weak\" -w 1024 -l 576 "
               + "-e x264 -q 19 --cfr  -a 1 -E ffaac -B 0 -6 auto -R Auto -D 0 --gain=0 "
               + "--audio-copy-mask none --audio-fallback ffac3 -x b-adapt=2:rc-lookahead=50 --verbose=0"
        )
        ret = call(cmd)
        return ret

if __name__ == "__main__":
    HbEncoder().encode("D:\\temp\\MOV042.MOD", "D:\\temp\\processed\MOV042.m4v")