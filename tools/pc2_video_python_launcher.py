"""PC2-only video renderer compatibility; leaves training and telemetry unchanged."""
import subprocess
import sys

# PC2 Kit enumeration: Intel UHD=0, RTX 5070=1 (not CUDA device indices).
# Revalidate this local mapping if hardware/driver enumeration changes.
FLAGS = '--/app/vulkan=false --/renderer/multiGpu/enabled=false --/renderer/multiGpu/autoEnable=false --/renderer/activeGpu=1'

def command(args):
    result = list(args)
    if '--video' in result and '--_run_isaaclab_child' in result:
        if '--kit_args' in result:
            i = result.index('--kit_args') + 1
            result[i] += ' ' + FLAGS
        else:
            for i, arg in enumerate(result):
                if arg.startswith('--kit_args='):
                    result[i] += ' ' + FLAGS
                    break
            else:
                result += ['--kit_args', FLAGS]
    return [sys.executable, '-u', *result]

if __name__ == '__main__':
    cmd = command(sys.argv[1:])
    print('[PC2 launcher] ' + repr(cmd), flush=True)
    rc = subprocess.call(cmd)
    sys.exit(rc if 0 <= rc <= 255 else 1)
