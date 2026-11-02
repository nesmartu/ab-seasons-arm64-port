"""Regression tests for package selection, APK metadata and explicit overrides."""
import re
import struct
import sys
import tempfile
import unittest
import zipfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from axml import NO, pool, patch_manifest, manifest_attrs
from config import settings, version_digits
from check_reproducible import collect_outputs


def manifest(version, package='org.example.input'):
    values=['manifest'];attrs=[]
    for key,value in [('versionName',version),('package',package)]:
        if value is None:continue
        ni=len(values);values.append(key);vi=len(values);values.append(value)
        attrs.append(struct.pack('<IIIHBBI',NO,ni,vi,8,0,3,vi))
    raw=b''.join(attrs)
    start=struct.pack('<HHIII',0x102,16,36+len(raw),1,NO)
    start+=struct.pack('<IIHHHHHH',NO,0,20,20,len(attrs),0,0,0)+raw
    end=struct.pack('<HHIIIII',0x103,16,24,1,NO,NO,0)
    body=pool(values,256)+start+end
    return struct.pack('<HHI',3,8,8+len(body))+body


class PackageSettingsTests(unittest.TestCase):
    def resolve(self, filename='game.apk', version='6.6.2', config='', *, legacy=True, package='org.example.input'):
        # Earlier automatic-ID tests explicitly opt out of the new preservation policy.
        if legacy:
            flags='preserve_original_package=false\n'
            if not re.search(r'(?m)^package\s*=',config):flags+='package=""\n'
            config=config.replace('[app]\n','[app]\n'+flags,1) if '[app]\n' in config else '[app]\n'+flags+config
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp) / filename
            with zipfile.ZipFile(apk, 'w') as z:
                z.writestr('AndroidManifest.xml', manifest(version,package))
            cfg = Path(tmp) / 'config.toml'
            cfg.write_text(config)
            return settings(apk, cfg)

    def test_current_defaults_and_exact_source_package(self):
        app=self.resolve(legacy=False)['app']
        self.assertIs(app['preserve_original_package'],False)
        self.assertEqual(app['package'],'com.rovio.angrybirdsseasons.port')
        self.assertEqual(self.resolve(legacy=False,config='[app]\npreserve_original_package=false')['app']['package'],'com.rovio.angrybirdsseasons.port')
        for package in ['com.rovio.angrybirdsseasons','org.example.changed_input']:
            cfg='[app]\npreserve_original_package=true\npackage="org.example.ignored"'
            self.assertEqual(self.resolve('fake_money_v9.apk','4.1.1',cfg,legacy=False,package=package)['app']['package'],package)

    def test_preservation_overrides_custom_and_variant_policy(self):
        cfg='[app]\npreserve_original_package=true\npackage="org.example.custom"\n[variants."game.apk"]\npackage="org.example.variant"'
        self.assertEqual(self.resolve(config=cfg,legacy=False)['app']['package'],'org.example.input')
        cfg+='\npreserve_original_package=false'
        self.assertEqual(self.resolve(config=cfg,legacy=False)['app']['package'],'org.example.variant')
        cfg='[app]\npreserve_original_package=false\npackage="org.example.custom"\n[variants."game.apk"]\npreserve_original_package=true'
        self.assertEqual(self.resolve(config=cfg,legacy=False)['app']['package'],'org.example.input')

    def test_preservation_rejects_missing_package_and_wrong_type(self):
        for package in [None,'bad-package','']:
            with self.subTest(package=package),self.assertRaises(ValueError):
                self.resolve(config='[app]\npreserve_original_package=true',package=package,legacy=False)
        with self.assertRaises(ValueError):self.resolve(config='[app]\npreserve_original_package="true"',legacy=False)

    def test_preservation_suppresses_fixed_suffix(self):
        cfg='[app]\npreserve_original_package=true\npackage=""\n[selectable_fixes]\nappend_fixed=true'
        self.assertEqual(self.resolve(config=cfg,legacy=False)['app']['package'],'org.example.input')

    def test_three_modes(self):
        for mode, expected in [('base', 'com.rovio.seasonsport.unofficial'),
                               ('version', 'com.rovio.seasonsport662.unofficial')]:
            with self.subTest(mode=mode):
                self.assertEqual(self.resolve('game_unlocked.apk', config=f'[app]\npackage_mode="{mode}"')['app']['package'], expected)

    def test_fix_defaults_and_fixed_suffix(self):
        cfg=self.resolve()
        self.assertEqual(cfg['fixes'], dict(unlock_all_episodes=True,unlocked_all_with_coins=False,unlock_ragnahog_levels=True,quest_video=True,cosmetics=False,unlock_all_levels=False))
        self.assertTrue(cfg['selectable_fixes']['enabled'])
        self.assertFalse(cfg['selectable_fixes']['append_fixed'])
        cases=[('[selectable_fixes]\nappend_fixed=true','.fixed'),
               ('[selectable_fixes]\nappend_fixed=true\nenabled=false',''),
               ('[selectable_fixes]\nappend_fixed=true\n[fixes]\nunlock_all_episodes=false\nunlock_ragnahog_levels=false\nquest_video=false',''),
               ('[app]\npackage="org.example.exact"\n[selectable_fixes]\nappend_fixed=true',None)]
        for config,suffix in cases:
            with self.subTest(config=config):
                expected='org.example.exact' if suffix is None else 'com.rovio.seasonsport662.unofficial'+suffix
                self.assertEqual(self.resolve(config=config)['app']['package'],expected)
        for config in ['[fixes]\ncosmetics="true"','[fixes]\ncosmaticsopened=true',
                       '[selectable_fixes]\nenabled=1','[selectable_fixes]\ncoins_amount=true',
                       '[selectable_fixes]\ncoins_amount=16000001']:
            with self.subTest(config=config),self.assertRaises(ValueError):self.resolve(config=config)

    def test_manifest_app_and_launcher_labels(self):
        data = (Path(__file__).parent / 'seasons662-manifest.axml').read_bytes()
        patched = patch_manifest(data, package='org.example.port', app_name='Angry Birds Seasons')
        labels = [a['label'] for tag, a in manifest_attrs(patched)
                  if tag in ['application', 'activity', 'activity-alias'] and 'label' in a]
        self.assertGreaterEqual(len(labels), 2)
        self.assertEqual(set(labels), {'Angry Birds Seasons'})

    def test_preserve_original_label_references(self):
        data = (Path(__file__).parent / 'seasons662-manifest.axml').read_bytes()
        patched = patch_manifest(data, package='org.example.port', app_name=None)
        labels = lambda b: [(tag, a['label']) for tag, a in manifest_attrs(b) if 'label' in a]
        self.assertEqual(labels(patched), labels(data))
        self.assertTrue(self.resolve()['app']['preserve_original_name'])
        self.assertFalse(self.resolve(config='[app]\npreserve_original_name=false')['app']['preserve_original_name'])

    def test_reproducibility_ignores_intermediate_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'reports').mkdir()
            (root / 'dist').mkdir()
            (root / 'reports/batch.json').write_text(json.dumps([{'input': 'game.apk', 'output': 'game-arm64.apk'}]))
            for name in ['game-arm64.apk', 'game.bridge.so', 'game-arm64.unsigned.apk', 'game-arm64.aligned.apk']:
                (root / 'dist' / name).write_bytes(name.encode())
            self.assertEqual(set(collect_outputs(root)), {'game-arm64.apk', 'game.bridge.so'})

    def test_filename_never_changes_package(self):
        for filename in ['GAME_COINS.apk','money_unlocked.apk','GAME_UNLOCKED.apk','plain.apk']:
            with self.subTest(filename=filename):
                self.assertEqual(self.resolve(filename)['app']['package'], 'com.rovio.seasonsport662.unofficial')

    def test_missing_version_uses_base(self):
        for version in [None,'','unknown']:
            with self.subTest(version=version):
                self.assertEqual(self.resolve('game_coins.apk',version)['app']['package'], 'com.rovio.seasonsport.unofficial')

    def test_version_comes_from_manifest(self):
        self.assertEqual(self.resolve('fake_v9.9.9.apk', '4.1.1')['app']['package'],
                         'com.rovio.seasonsport411.unofficial')
        self.assertEqual(version_digits('6.6.2-beta'), '662')

    def test_explicit_and_per_file_overrides(self):
        cfg = '[app]\npackage="org.example.global"\n[variants."game.apk"]\npackage="org.example.variant"\nname="Custom"'
        app = self.resolve(config=cfg)['app']
        self.assertEqual((app['package'], app['name']), ('org.example.variant', 'Custom'))
        cfg = '[app]\npackage="org.example.global"\n[variants."game.apk"]\npackage=""\npackage_mode="version"'
        self.assertEqual(self.resolve(config=cfg)['app']['package'], 'com.rovio.seasonsport662.unofficial')
        cfg = '[app]\npackage_base="org.example.port.unofficial"'
        self.assertEqual(self.resolve(config=cfg)['app']['package'], 'org.example.port662.unofficial')

    def test_invalid_settings_fail(self):
        for config in ['[app]\npackage_mode="typo"', '[app]\npackage_mode="version_type"', '[app]\npackage="bad-package"',
                       '[app]\npackage_base="org.example.no_suffix"', '[bridge]\nmax_fps=true',
                       '[icons]\ncustom=1', '[bridge]\nrender_height=8193',
                       '[app]\npreserve_original_name="true"']:
            with self.subTest(config=config), self.assertRaises(ValueError):
                self.resolve(config=config)


if __name__ == '__main__':
    unittest.main()
