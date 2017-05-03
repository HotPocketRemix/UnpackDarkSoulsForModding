# -*- mode: python -*-

block_cipher = None


a = Analysis(['unpack_dark_souls_for_modding.py'],
             pathex=['C:\\Users\\S. S. Cosmonaut\\Desktop\\ds-testbed'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='UnpackDarkSoulsForModding',
          debug=False,
          strip=False,
          upx=True,
          console=True , icon='favicon.ico')
