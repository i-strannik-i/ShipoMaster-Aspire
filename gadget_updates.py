"""Public release checks and SHA-256 verified gadget downloads; no job data is sent."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.request
import urllib.parse

REPO='i-strannik-i/ShipoMaster-Aspire'
MANIFEST_URL='https://raw.githubusercontent.com/'+REPO+'/main/update.json'
MAX_PACKAGE_SIZE=100*1024*1024

def version_tuple(value):
    match=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)',str(value))
    if not match:raise ValueError('Неверный номер версии обновления.')
    return tuple(map(int,match.groups()))

def validated_manifest(data):
    version_tuple(data['version'])
    version=data['version'].lstrip('v')
    expected='https://github.com/'+REPO+'/releases/download/v'+version+'/ShipoMaster_Aspire_'+version+'.vgadget'
    if data.get('url')!=expected:raise ValueError('Неверный адрес пакета обновления.')
    if not re.fullmatch(r'[a-fA-F0-9]{64}',data.get('sha256','')):raise ValueError('Не указана контрольная сумма обновления.')
    return {'version':version,'url':expected,'sha256':data['sha256'].lower()}

def read_manifest():
    req=urllib.request.Request(MANIFEST_URL,headers={'User-Agent':'ShipoMaster-Aspire-Updater','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=6) as r:
        raw=r.read(65537)
    if len(raw)>65536:raise ValueError('Слишком большой ответ сервера обновлений.')
    return validated_manifest(json.loads(raw.decode('utf-8-sig')))

def check_update(current):
    try:
        data=read_manifest();available=version_tuple(data['version'])>version_tuple(current)
        return dict(ok=True,available=available,latest=data['version'],message=('Доступна версия '+data['version']+'. Нажмите «Обновить».' if available else 'Установлена актуальная версия '+current+'.'))
    except Exception:
        return dict(ok=True,available=False,latest='',message='Не удалось проверить обновления. Проверьте подключение к Интернету и нажмите «Проверить сейчас».')

def download_update(current,open_folder=True):
    data=read_manifest()
    if version_tuple(data['version'])<=version_tuple(current):return dict(ok=True,available=False,message='Установлена актуальная версия '+current+'.')
    folder=Path(tempfile.mkdtemp(prefix='ShipoMaster_Update_'))
    target=folder/('ShipoMaster_Aspire_'+data['version']+'.vgadget')
    partial=target.with_suffix('.part');digest=hashlib.sha256();size=0
    try:
        req=urllib.request.Request(data['url'],headers={'User-Agent':'ShipoMaster-Aspire-Updater'})
        with urllib.request.urlopen(req,timeout=30) as r,partial.open('wb') as f:
            while True:
                block=r.read(1024*1024)
                if not block:break
                size+=len(block)
                if size>MAX_PACKAGE_SIZE:raise ValueError('Пакет обновления слишком большой.')
                digest.update(block);f.write(block)
        if digest.hexdigest()!=data['sha256']:raise ValueError('Контрольная сумма обновления не совпала. Установка отменена.')
        partial.replace(target)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    if open_folder and os.name=='nt':os.startfile(str(folder))
    return dict(ok=True,available=True,path=str(target),message='Версия '+data['version']+' скачана и проверена.\nЗакройте гаджет. В Aspire: Gadgets → Install New Gadget…\nВыберите файл из открывшейся папки: '+str(target))
