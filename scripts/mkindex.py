#!/usr/bin/env python

'''
Creates a JSON index file listing information about all of the color schemes.
Note: requires Python Imaging Library (PIL), ex. 'python-imaging' Debian package.
'''

# TODO this script needs to be ported to Python 3 properly

import os
import sys
import json
from configparser import ConfigParser, Error as ConfigParserError
import hashlib
import base64
from io import BytesIO, StringIO
from PIL import Image, ImageDraw, ImageOps, ImageFilter

THUMBNAIL_SIZE = (128, 128)
SCREENSHOT_BASE = 'https://raw.github.com/geany/geany-themes/master/screenshots/'
SCHEMES_BASE = 'https://raw.github.com/geany/geany-themes/master/colorschemes/'

def get_option(cp, group, key, default=None):
    try:
        return cp.get(group, key)
    except ConfigParserError:
        return default

def generate_thumbnail(conf_fn, screenshot_dir='screenshots'):
  base = os.path.splitext(os.path.basename(conf_fn))[0]
  png_file = os.path.join(screenshot_dir, '%s.png' % base)

  if not os.path.exists(png_file):
    png_file = os.path.join(screenshot_dir, 'screenshot-missing.png')
    img = Image.open(png_file)
    output = BytesIO()
    img.save(output, "PNG", optimize=True)
    data = base64.b64encode(output.getvalue())
    output.close()
    return data.decode()
  else:
    img = Image.open(png_file)
    img = img.crop((2,2,img.size[1]-2,img.size[1]-2))
    img.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
#-- set to True to save thumbs into screenshots/.thumbs
    do_thumbs = False
    if do_thumbs:
      thumb_dir = os.path.join(screenshot_dir, '.thumbs')
      try:
        os.makedirs(thumb_dir)
      except OSError as e:
        if e.errno != 17: raise
      thumb_fn = os.path.join(thumb_dir, base + '.png')
      img.save(thumb_fn, "PNG", optimize=True)
#--
    output = BytesIO()
    img.save(output, "PNG", optimize=True)
    data = base64.b64encode(output.getvalue())
    output.close()

  return data.decode()

def create_index(themes_dir, screenshot_dir='screenshots'):
    data = {}

    for conf_file in os.listdir(themes_dir):

        if not conf_file.endswith('.conf'):
            continue

        conf_file = os.path.join(themes_dir, conf_file)
        cp = ConfigParser()
        cp.read(conf_file)

        if not cp.has_section('theme_info'):
            continue

        scheme_name = '.'.join(os.path.basename(conf_file).split('.')[:-1])

        try:
            version = int(get_option(cp, 'theme_info', 'version', '0'))
        except:
            version = '0'

        png_file = os.path.join(screenshot_dir, scheme_name + '.png')
        if os.path.isfile(png_file):
          png_hash = hashlib.md5(open(png_file, 'rb').read()).hexdigest()
        else:
          png_hash = ''

        compat = get_option(cp, 'theme_info', 'compat', '0.0.0')
        versions = []
        for ver in compat.split(';'):
          ver = [int(v) for v in ver.split('.')] + [0]*3
          ver = '.'.join([ str(v) for v in ver[0:3] ])
          versions.append(ver)

        data[scheme_name] = {
            'name': get_option(cp, 'theme_info', 'name', 'Untitled'),
            'description': get_option(cp, 'theme_info', 'description', ''),
            'version': version,
            'author': get_option(cp, 'theme_info', 'author', 'Unknown Author'),
            'screenshot': '%s%s.png' % (SCREENSHOT_BASE, scheme_name),
            'colorscheme': '%s%s.conf' % (SCHEMES_BASE, scheme_name),
            'thumbnail': generate_thumbnail(conf_file, screenshot_dir),
            'screen_hash': png_hash,
            'scheme_hash': hashlib.md5(open(conf_file, 'rb').read()).hexdigest(),
            'compat': versions,
        }

    # json.dumps() leaves trailing whitespace on some lines, strip it off
    data = json.dumps(data, indent=2, sort_keys=True).rstrip()
    return '\n'.join([l.rstrip() for l in data.split('\n')]) + '\n'

if __name__ == "__main__":
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    root_dir = os.path.abspath(os.path.dirname(cur_dir))
    screen_dir = os.path.join(root_dir, 'screenshots')
    scheme_dir = os.path.join(root_dir, 'colorschemes')
    index = create_index(scheme_dir, screen_dir)
    sys.stdout.write(index)
