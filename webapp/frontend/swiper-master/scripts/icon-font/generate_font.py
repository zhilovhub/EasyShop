import fontforge  # noqa
import os  # noqa
import md5  # noqa
import subprocess  # noqa
import tempfile  # noqa
import json  # noqa
import copy  # noqa

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))  # noqa
BLANK_PATH = os.path.join(SCRIPT_PATH, 'blank.svg')  # noqa
INPUT_SVG_DIR = os.path.join(SCRIPT_PATH, '..', '..', 'src/icons/svg')  # noqa
OUTPUT_FONT_DIR = os.path.join(SCRIPT_PATH, '..', '..', 'src/icons/font')  # noqa
AUTO_WIDTH = True  # noqa
KERNING = 15  # noqa

m = md5.new()  # noqa

f = fontforge.font()  # noqa
f.encoding = 'UnicodeFull'  # noqa
f.design_size = 24  # noqa
f.em = 24  # noqa
f.ascent = 448  # noqa
f.descent = 64  # noqa

# Add lookup table
f.addLookup("ligatable","gsub_ligature",(),(("liga",(("latn",("dflt")),)),))  # noqa
f.addLookupSubtable("ligatable","ligatable1")  # noqa

# Import base characters
for char in "0123456789abcdefghijklmnopqrstuvwzxyz_- ":  # noqa
  glyph = f.createChar(ord(char))  # noqa
  glyph.importOutlines(BLANK_PATH)  # noqa
  glyph.width = 0  # noqa

font_name = 'swiper-icons';  # noqa
m.update(font_name + ';')  # noqa

for dirname, dirnames, filenames in os.walk(INPUT_SVG_DIR):  # noqa
  for filename in filenames:  # noqa
    name, ext = os.path.splitext(filename)  # noqa
    filePath = os.path.join(dirname, filename)  # noqa
    size = os.path.getsize(filePath)  # noqa
    if ext in ['.svg', '.eps']:  # noqa
      if ext in ['.svg']:  # noqa
        # hack removal of <switch> </switch> tags
        svgfile = open(filePath, 'r+')  # noqa
        tmpsvgfile = tempfile.NamedTemporaryFile(suffix=ext, delete=False)  # noqa
        svgtext = svgfile.read()  # noqa
        svgfile.seek(0)  # noqa

        # replace the <switch> </switch> tags with 'nothing'  # noqa
        svgtext = svgtext.replace('<switch>', '')  # noqa
        svgtext = svgtext.replace('</switch>', '')  # noqa

        tmpsvgfile.file.write(svgtext)  # noqa

        svgfile.close()  # noqa
        tmpsvgfile.file.close()  # noqa

        filePath = tmpsvgfile.name  # noqa
        # end hack  # noqa

      m.update(name + str(size) + ';')  # noqa

      glyph = f.createChar(-1, name)  # noqa
      glyph.importOutlines(filePath)  # noqa

      # Add ligatures  # noqa
      ligature = [];  # noqa
      for c in name:  # noqa
        if (c == '_'):  # noqa
          c = "underscore"  # noqa
        if (c == '-'):  # noqa
          c = "hyphen"  # noqa
        if (c == ' '):  # noqa
          c = "space"  # noqa
        ligature.append(c)  # noqa
      glyph.addPosSub('ligatable1', ligature)  # noqa

      # if we created a temporary file, let's clean it up  # noqa
      if tmpsvgfile:  # noqa
        os.unlink(tmpsvgfile.name)  # noqa

      # set glyph size explicitly or automatically depending on autowidth  # noqa
      if AUTO_WIDTH:  # noqa
        glyph.left_side_bearing = glyph.right_side_bearing = 0  # noqa
        glyph.round()  # noqa

    # resize glyphs if autowidth is enabled  # noqa
    if AUTO_WIDTH:  # noqa
      f.autoWidth(0, 0, 512)  # noqa

fontfile = '%s/swiper-icons' % (OUTPUT_FONT_DIR)  # noqa
print fontfile;  # noqa
build_hash = m.hexdigest()  # noqa

f.fontname = font_name  # noqa
f.familyname = font_name  # noqa
f.fullname = font_name  # noqa

f.generate(fontfile + '.ttf')  # noqa

scriptPath = os.path.dirname(os.path.realpath(__file__))  # noqa
try:  # noqa
  subprocess.Popen([scriptPath + '/sfnt2woff', fontfile + '.ttf'], stdout=subprocess.PIPE)  # noqa
except OSError:  # noqa
  # If the local version of sfnt2woff fails (i.e., on Linux), try to use the  # noqa
  # global version. This allows us to avoid forcing OS X users to compile  # noqa
  # sfnt2woff from source, simplifying install.  # noqa
  subprocess.call(['sfnt2woff', fontfile + '.ttf'])  # noqa


# Hint the TTF file  # noqa
subprocess.call('ttfautohint -s -f -n ' + fontfile + '.ttf ' + fontfile + '-hinted.ttf > /dev/null 2>&1 && mv ' + fontfile + '-hinted.ttf ' + fontfile + '.ttf', shell=True)  # noqa

# WOFF2 Font
subprocess.call('woff2_compress ' + fontfile + '.ttf', shell=True)  # noqa
