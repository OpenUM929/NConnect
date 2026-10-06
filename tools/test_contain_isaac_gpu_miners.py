"""Safety checks use mocks only; no live processes are changed."""
import unittest
from unittest.mock import Mock, patch

import contain_isaac_gpu_miners as target


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.rows = []
        self.processes = {}
        for pid, parent, name, cmd in [
            (2588, 5064, 'svchost.exe', 'svchost.exe'),
            (5780, 2588, 'cmd.exe', 'cmd.exe -a rx/0 --url ssl-maimai.com:27039'),
            (21840, 2588, 'cmd.exe', 'cmd.exe --algo progpowz --url pool.zh.woolypooly.com:3146'),
        ]:
            path = 'C:/Windows/System32/' + name
            self.rows.append(dict(Id=pid, ParentId=parent, Path=path, Created='/Date(1000000)/'))
            p = Mock()
            p.pid = pid
            p.create_time.return_value = 1000
            p.exe.return_value = path
            p.ppid.return_value = parent
            p.name.return_value = name
            p.cmdline.return_value = cmd.split()
            self.processes[pid] = p
        self.proc_patch = patch.object(target.psutil, 'Process', side_effect=self.processes.__getitem__)
        self.service_patch = patch.object(target.psutil, 'win_service_iter', return_value=[])
        self.proc_patch.start()
        self.services = self.service_patch.start()
        self.addCleanup(self.proc_patch.stop)
        self.addCleanup(self.service_patch.stop)

    def check(self):
        return target.verified_processes({'Processes': self.rows})

    def test_exact_identity_and_parent_first(self):
        self.assertEqual([p.pid for p in self.check()], [2588, 5780, 21840])
        self.assertNotIn(22380, self.processes)

    def test_reused_pid_rejected(self):
        self.processes[21840].create_time.return_value = 2000
        with self.assertRaisesRegex(RuntimeError, 'creation time'):
            self.check()

    def test_different_command_rejected(self):
        self.processes[5780].cmdline.return_value = ['cmd.exe', '/c', 'backup.bat']
        with self.assertRaisesRegex(RuntimeError, 'command mismatch'):
            self.check()

    def test_real_service_rejected(self):
        service = Mock()
        service.pid.return_value = 2588
        self.services.return_value = [service]
        with self.assertRaisesRegex(RuntimeError, 'registered Windows service'):
            self.check()

    def test_parent_mismatch_rejected(self):
        self.processes[21840].ppid.return_value = 1
        with self.assertRaisesRegex(RuntimeError, 'path/parent mismatch'):
            self.check()


if __name__ == '__main__':
    unittest.main()
