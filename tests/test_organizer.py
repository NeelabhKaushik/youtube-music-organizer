import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import organizer as o

class Fake:
    def __init__(self):
        self.playlists = {}
        self.creates = 0
        self.fail_after_write = False
    def create_playlist(self, title, description, privacy_status):
        self.creates += 1
        pid = f'PL{self.creates}'
        self.playlists[pid] = dict(title=title, description=description, privacy=privacy_status, tracks=[])
        return pid
    def get_playlist(self, pid, limit=None):
        return self.playlists[pid]
    def add_playlist_items(self, pid, ids, duplicates=False):
        tracks = self.playlists[pid]['tracks']
        tracks.extend({'videoId': v} for v in ids if v not in {t['videoId'] for t in tracks})
        if self.fail_after_write:
            self.fail_after_write = False
            raise ConnectionError()
        return {'status': 'STATUS_SUCCEEDED'}
    def get_library_playlists(self, limit=None):
        return [{'title': p['title'], 'playlistId': pid} for pid, p in self.playlists.items()]

class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)
        o.save(self.data/'library.json', {'songs': [{'videoId': 'a', 'title': 'A'}, {'videoId': 'b', 'title': 'B'}], 'completeness_verified': True, 'missing_ids': []})
        self.records = [dict(videoId=v, categories=[o.CATEGORIES[0]], confidence=c, needs_review=False, explanation='Known song' if c>.75 else 'Uncertain', evidence=['test']) for v,c in [('a', .9), ('b', .3)]]
        o.save(self.data/'input.json', self.records)
        o.ingest(self.data, self.data/'input.json')
    def test_review_and_idempotency(self):
        plan = o.preview(self.data)
        self.assertEqual(plan['uncertain'], ['b'])
        api = Fake()
        o.apply(self.data, api, plan['approval_hash'])
        o.apply(self.data, api, plan['approval_hash'])
        self.assertEqual(api.creates, 7)
        self.assertEqual(api.playlists['PL1']['tracks'], [{'videoId': 'a'}])
    def test_stale_approval_rejected_before_mutation(self):
        plan = o.preview(self.data)
        self.records[0]['explanation'] = 'Changed'
        o.save(self.data/'input.json', self.records)
        o.ingest(self.data, self.data/'input.json')
        api = Fake()
        with self.assertRaises(ValueError): o.apply(self.data, api, plan['approval_hash'])
        self.assertEqual(api.creates, 0)
    def test_import_is_atomic(self):
        before = o.read(self.data/'classifications.json')
        self.records[1]['videoId'] = 'unknown'
        o.save(self.data/'input.json', self.records)
        with self.assertRaises(ValueError): o.ingest(self.data, self.data/'input.json')
        self.assertEqual(before, o.read(self.data/'classifications.json'))
    def test_unacknowledged_write_reconciles(self):
        api = Fake(); api.fail_after_write = True
        plan = o.preview(self.data)
        from unittest.mock import patch
        with patch('organizer.time.sleep'):
            o.apply(self.data, api, plan['approval_hash'])
        self.assertEqual(len(api.playlists['PL1']['tracks']), 1)
    def test_ambiguous_creation_stops(self):
        plan = o.preview(self.data)
        api = Fake()
        o.save(self.data/'sync.json', {'run': 'x', 'playlists': {o.CATEGORIES[0]: {'status': 'creating', 'marker': 'ytmo:x:0'}}})
        with self.assertRaises(ValueError): o.apply(self.data, api, plan['approval_hash'])
        self.assertEqual(api.creates, 0)
        api.create_playlist(o.CATEGORIES[0], 'ytmo:x:0', 'PRIVATE')
        o.recover(self.data, api)
        o.apply(self.data, api, plan['approval_hash'])
        self.assertEqual(api.creates, 7)
    def test_unrelated_playlist_refused(self):
        plan = o.preview(self.data); api = Fake()
        api.create_playlist('Existing', 'unrelated', 'PRIVATE')
        o.save(self.data/'sync.json', {'run': 'x', 'playlists': {o.CATEGORIES[0]: {'status': 'created', 'id': 'PL1'}}})
        with self.assertRaises(ValueError): o.apply(self.data, api, plan['approval_hash'])
        self.assertFalse(api.playlists['PL1']['tracks'])
    def test_export_paginates_and_preserves_missing(self):
        class ExportAPI:
            def get_liked_songs(self, limit):
                assert limit is None
                return {'trackCount': 3, 'tracks': [{'videoId': 'x'}, {'videoId': 'x'}, {'title': 'Unavailable'}]}
        o.export(self.data, ExportAPI())
        result = o.read(self.data/'library.json')
        self.assertEqual(len(result['songs']), 1)
        self.assertEqual(len(result['missing_ids']), 1)
        self.assertTrue(result['completeness_verified'])
        self.assertEqual(len(list((self.data/'backups').glob('*'))), 2)

if __name__ == '__main__':
    unittest.main()
