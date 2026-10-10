import unittest

from tools.pc2_monitor_dispatch import dispatch


class FakeRpc:
    def __init__(self, active=True, entries=None, error=False):
        self.active = active
        self.entries = entries or []
        self.calls = []
        self.error = error

    def call(self, method, params):
        self.calls.append((method, params))
        if self.error:
            raise RuntimeError('access denied')
        if method == 'thread/read':
            return {'thread': {'status': {'type': 'active' if self.active else 'idle'}}}
        if method == 'thread/queue/list':
            return {'data': self.entries}
        if method == 'thread/queue/add':
            item = {'id': 'queued1', 'clientUserMessageId': params['clientUserMessageId']}
            self.entries.append(item)
            return {'queuedSubmission': item}
        if method == 'thread/queue/start':
            return {}
        if method == 'thread/resume':
            return {}
        raise AssertionError(method)


class DispatchTests(unittest.TestCase):
    def test_active_writer_queues_without_resume_or_interrupt(self):
        rpc = FakeRpc()
        result = dispatch(rpc, 'thread', 'monitor', 'nconnect-monitor-test')
        self.assertEqual('QUEUED_WHILE_ACTIVE', result['state'])
        self.assertFalse(result['report_delivered'])
        self.assertEqual(['thread/read', 'thread/queue/list', 'thread/queue/add'], [x[0] for x in rpc.calls])

    def test_idle_starts_queued_turn(self):
        rpc = FakeRpc(active=False)
        self.assertEqual('DISPATCHED', dispatch(rpc, 'thread', 'monitor', 'nconnect-monitor-test')['state'])
        self.assertEqual(('thread/queue/start', {'threadId': 'thread', 'queuedSubmissionId': 'queued1'}), rpc.calls[-1])

    def test_pending_monitor_is_not_duplicated(self):
        rpc = FakeRpc(active=False, entries=[{'id': 'old', 'clientUserMessageId': 'nconnect-monitor-old'}])
        dispatch(rpc, 'thread', 'monitor', 'nconnect-monitor-new')
        self.assertNotIn('thread/queue/add', [x[0] for x in rpc.calls])
        self.assertEqual('old', rpc.calls[-1][1]['queuedSubmissionId'])

    def test_probe_never_mutates(self):
        rpc = FakeRpc()
        self.assertEqual('PROBE_OK', dispatch(rpc, 'thread', '', '', probe=True)['state'])
        self.assertEqual(1, len(rpc.calls))

    def test_unloaded_uses_same_app_server_resume_before_start(self):
        class UnloadedRpc(FakeRpc):
            def call(self, method, params):
                result = super().call(method, params)
                if method == 'thread/read':
                    result['thread']['status']['type'] = 'notLoaded'
                return result
        rpc = UnloadedRpc(active=False)
        dispatch(rpc, 'thread', 'monitor', 'nconnect-monitor-test')
        self.assertEqual(['thread/resume', 'thread/queue/list', 'thread/queue/start'], [x[0] for x in rpc.calls[-3:]])

    def test_host_auto_consumption_is_not_a_failure_or_duplicate(self):
        class AutoRpc(FakeRpc):
            def call(self, method, params):
                result = super().call(method, params)
                if method == 'thread/resume':
                    self.entries.clear()
                if method == 'thread/read':
                    result['thread']['status']['type'] = 'notLoaded'
                return result
        rpc = AutoRpc(active=False)
        self.assertEqual('DISPATCHED', dispatch(rpc, 'thread', 'monitor', 'nconnect-monitor-test')['state'])
        self.assertNotIn('thread/queue/start', [x[0] for x in rpc.calls])

    def test_denied_access_is_not_success(self):
        with self.assertRaisesRegex(RuntimeError, 'access denied'):
            dispatch(FakeRpc(error=True), 'thread', 'monitor', 'nconnect-monitor-test')


if __name__ == '__main__':
    unittest.main()
