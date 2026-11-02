"""Build settings; TOML paths are relative to the project, never the shell cwd."""
from pathlib import Path
import re
import tomllib
import zipfile
from axml import manifest_attrs

ROOT = Path(__file__).resolve().parents[1]
ENGINE = 'libAngryBirdsSeasonsFull.so'
PACKAGE_RE = r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+'

def apk_version(apk):
    """Read versionName from the APK, never from its filename."""
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
    # Accept a leading numeric version, optionally followed by e.g. -beta.
    match = re.match(r'^(\d+(?:\.\d+)*)(?=$|[^\d.])', version.strip()) if version else None
    return match[1].replace('.', '') if match else ''

def resolve_package(app, version=None, fixed=False, original_package=None):
    if app['preserve_original_package']:
        if not isinstance(original_package,str) or not re.fullmatch(PACKAGE_RE,original_package):
            raise ValueError('Cannot preserve a missing or invalid input package')
        return original_package  # Exact input ID; no custom/automatic/.fixed suffix.
    if app['package']:
        return app['package']
    base = app['package_base']
    if not base.endswith('.unofficial'):
        raise ValueError('app.package_base must end with .unofficial')
    digits = version_digits(version) if app['package_mode'] != 'base' else ''
    result = base.removesuffix('.unofficial') + digits + '.unofficial'
    return result

def settings(apk=None, path=None):
    path = Path(path) if path else ROOT / 'build_config.toml'
    with path.open('rb') as f:
        raw = tomllib.load(f)
    app = dict(name='Angry Birds Seasons', preserve_original_name=True, preserve_original_package=False,
               package='com.rovio.angrybirdsseasons.port411',
               package_base='com.rovio.seasonsport.unofficial', package_mode='version')
    app.update(raw.get('app', {}))
    if apk:
        app.update(raw.get('variants', {}).get(Path(apk).name, {}))
    if not isinstance(app['name'], str) or not app['name'].strip():
        raise ValueError('app.name must be a nonempty string')
    if type(app['preserve_original_package']) is not bool:
        raise ValueError('app.preserve_original_package must be a TOML boolean')
    if type(app['preserve_original_name']) is not bool:
        raise ValueError('app.preserve_original_name must be a TOML boolean')
    if app['package_mode'] not in ['base', 'version']:
        raise ValueError('app.package_mode must be base or version')
    for key in ['package', 'package_base']:
        if not isinstance(app[key], str) or (app[key] and not re.fullmatch(PACKAGE_RE, app[key])):
            raise ValueError('Invalid Android application package in app.' + key)
    app['package'] = resolve_package(app, apk_version(apk) if apk else None,
                                     original_package=apk_package(apk) if app['preserve_original_package'] else None)
    if not re.fullmatch(PACKAGE_RE, app['package']):
        raise ValueError('Invalid resolved Android application package')
    icons = dict(custom=False, directory='icons')
    icons.update(raw.get('icons', {}))
    bridge = dict(render_height=1080, max_fps=60, allow_network=False)
    bridge.update(raw.get('bridge', {}))
    if not isinstance(icons['directory'], str) or not icons['directory']:
        raise ValueError('icons.directory must be a nonempty path string')
    if type(icons['custom']) is not bool or type(bridge['allow_network']) is not bool:
        raise ValueError('custom and allow_network must be TOML booleans')
    for key, maximum in [('render_height',8192),('max_fps',1000)]:
        if type(bridge[key]) is not int or not 0 <= bridge[key] <= maximum:
            raise ValueError(f'{key} must be an integer in [0,{maximum}]')
    return dict(app=app, icons=icons, bridge=bridge)

def inputs():
    result = sorted((ROOT / 'input').glob('*.apk'), key=lambda p:p.name)
    if not result:
        raise ValueError('No APK files found in input/')
    return result
