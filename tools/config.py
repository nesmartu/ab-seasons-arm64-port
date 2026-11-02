"""Validated build settings. Relative resource paths use the project root."""
from pathlib import Path
import re
import tomllib
import zipfile
from axml import manifest_attrs

ROOT = Path(__file__).resolve().parents[1]
ENGINE = 'libAngryBirdsSeasonsFull.so'
PACKAGE_RE = r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+'
FIX_DEFAULTS = dict(unlock_all_episodes=True, unlocked_all_with_coins=False,
                    unlock_ragnahog_levels=True, quest_video=True, cosmetics=False, unlock_all_levels=False)

def apk_version(apk):
    with zipfile.ZipFile(apk) as z:
        tags = manifest_attrs(z.read('AndroidManifest.xml'))
    value = next((a.get('versionName') for tag, a in tags if tag == 'manifest'), None)
    return value if isinstance(value, str) else None

def apk_package(apk):
    if apk is None:
        raise ValueError('preserve_original_package=true requires an input APK')
    with zipfile.ZipFile(apk) as z:
        tags = manifest_attrs(z.read('AndroidManifest.xml'))
    value = next((a.get('package') for tag,a in tags if tag == 'manifest'), None)
    if not isinstance(value,str) or not re.fullmatch(PACKAGE_RE,value):
        raise ValueError('Input APK has no valid Android package identifier')
    return value

def version_digits(version):
    match = re.match(r'^(\d+(?:\.\d+)*)(?=$|[^\d.])', version.strip()) if version else None
    return match[1].replace('.', '') if match else ''

def fixes_active(cfg):
    return cfg['selectable_fixes']['enabled'] and any(cfg['fixes'].values())

def resolve_package(app, version=None, fixed=False, original_package=None):
    if app['preserve_original_package']:
        if not isinstance(original_package,str) or not re.fullmatch(PACKAGE_RE,original_package):
            raise ValueError('Cannot preserve a missing or invalid input package')
        return original_package  # Exact input ID; no custom/automatic/.fixed suffix.
    if app['package']:
        return app['package']  # Explicit IDs are exact, including any desired suffix.
    base = app['package_base']
    if not base.endswith('.unofficial'):
        raise ValueError('app.package_base must end with .unofficial')
    digits = version_digits(version) if app['package_mode'] == 'version' else ''
    return base.removesuffix('.unofficial') + digits + '.unofficial' + ('.fixed' if fixed else '')

def settings(apk=None, path=None):
    path = Path(path) if path else ROOT / 'build_config.toml'
    with path.open('rb') as f:
        raw = tomllib.load(f)
    if set(raw) - {'app','icons','bridge','variants','selectable_fixes','fixes'}:
        raise ValueError('Unknown configuration section')
    patch = dict(enabled=True, append_fixed=False, coins_amount=1000000)
    if set(raw.get('selectable_fixes', {})) - set(patch):
        raise ValueError('Unknown selectable_fixes setting')
    patch.update(raw.get('selectable_fixes', {}))
    flags = dict(FIX_DEFAULTS)
    supplied = dict(raw.get('fixes', {}))
    if 'ragnahog' in supplied:
        if 'unlock_ragnahog_levels' in supplied:raise ValueError('Conflicting Ragnahog flags')
        supplied['unlock_ragnahog_levels']=supplied.pop('ragnahog')
    for old,new in [('unlocked_all','unlock_all_episodes')]:
        if old in supplied:
            if new in supplied:raise ValueError('Conflicting old/new fix keys')
            value=supplied.pop(old)
            if type(value) is not bool:raise ValueError('Fix flags must be booleans')
            supplied[new]=value
            if value:supplied['unlock_all_levels']=True
    if set(supplied) - set(flags):
        raise ValueError('Unknown fix flag')
    flags.update(supplied)
    if any(type(v) is not bool for v in flags.values()) or any(type(patch[k]) is not bool for k in ['enabled','append_fixed']):
        raise ValueError('Fix flags, enabled and append_fixed must be TOML booleans')
    if type(patch['coins_amount']) is not int or not 1 <= patch['coins_amount'] <= 16000000:
        raise ValueError('coins_amount must be an integer in [1,16000000]')
    app = dict(name='Angry Birds Seasons', preserve_original_name=True, preserve_original_package=False,
               package='com.rovio.angrybirdsseasons.port',
               package_base='com.rovio.seasonsport.unofficial', package_mode='version')
    if set(raw.get('app', {})) - set(app):
        raise ValueError('Unknown app setting')
    app.update(raw.get('app', {}))
    if apk:
        override = raw.get('variants', {}).get(Path(apk).name, {})
        if set(override) - set(app):raise ValueError('Unknown per-input app setting')
        app.update(override)
    if not isinstance(app['name'], str) or not app['name'].strip():
        raise ValueError('app.name must be a nonempty string')
    if type(app['preserve_original_package']) is not bool:
        raise ValueError('app.preserve_original_package must be a TOML boolean')
    if type(app['preserve_original_name']) is not bool:
        raise ValueError('app.preserve_original_name must be a TOML boolean')
    if app['package_mode'] not in ['base', 'version']:
        raise ValueError('app.package_mode must be base or version; filename type detection was removed')
    for key in ['package', 'package_base']:
        if not isinstance(app[key], str) or (app[key] and not re.fullmatch(PACKAGE_RE, app[key])):
            raise ValueError('Invalid Android application package in app.' + key)
    active = patch['enabled'] and any(flags.values())
    app['package'] = resolve_package(app, apk_version(apk) if apk else None, active and patch['append_fixed'],
                                     apk_package(apk) if app['preserve_original_package'] else None)
    if not re.fullmatch(PACKAGE_RE, app['package']):
        raise ValueError('Invalid resolved Android application package')
    icons = dict(custom=False, directory='icons'); icons.update(raw.get('icons', {}))
    bridge = dict(render_height=1080, max_fps=60, allow_network=False); bridge.update(raw.get('bridge', {}))
    if not isinstance(icons['directory'], str) or not icons['directory']:
        raise ValueError('icons.directory must be a nonempty path string')
    if type(icons['custom']) is not bool or type(bridge['allow_network']) is not bool:
        raise ValueError('custom and allow_network must be TOML booleans')
    for key, maximum in [('render_height',8192),('max_fps',1000)]:
        if type(bridge[key]) is not int or not 0 <= bridge[key] <= maximum:
            raise ValueError(f'{key} must be an integer in [0,{maximum}]')
    return dict(app=app, icons=icons, bridge=bridge, selectable_fixes=patch, fixes=flags)

def inputs():
    result = sorted((ROOT / 'input').glob('*.apk'), key=lambda p:p.name)
    if not result:raise ValueError('No APK files found in input/')
    return result
