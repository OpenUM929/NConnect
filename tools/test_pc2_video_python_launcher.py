import unittest
from pc2_video_python_launcher import command, FLAGS

class LauncherTests(unittest.TestCase):
    def test_verified_pc2_renderer_settings(self):
        self.assertEqual(FLAGS.split(), [
            '--/app/vulkan=false', '--/renderer/multiGpu/enabled=false',
            '--/renderer/multiGpu/autoEnable=false', '--/renderer/activeGpu=1',
        ])

    def test_nonvideo_unchanged(self):
        for args in [['train.py'], ['play.py', '--_run_isaaclab_child'], ['play.py', '--video']]:
            self.assertEqual(command(args)[2:], args)

    def test_video_child(self):
        args = ['play.py', '--_run_isaaclab_child', '--video']
        self.assertEqual(command(args)[2:], args + ['--kit_args', FLAGS])

    def test_existing_args(self):
        for tail in [['--kit_args', '--foo=bar'], ['--kit_args=--foo=bar']]:
            result = command(['play.py', '--_run_isaaclab_child', '--video', *tail])
            self.assertTrue(result[-1].endswith('--foo=bar ' + FLAGS))

if __name__ == '__main__':
    unittest.main()
