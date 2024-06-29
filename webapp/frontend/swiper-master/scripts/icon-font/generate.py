from subprocess import call  # noqa
import os  # noqa
import json  # noqa

BUILDER_PATH = os.path.dirname(os.path.abspath(__file__))  # noqa

def main():  # noqa
  generate_font_files()  # noqa

def generate_font_files():  # noqa
  print "Generate Fonts"  # noqa
  cmd = "fontforge -script %s/generate_font.py" % (BUILDER_PATH)  # noqa
  call(cmd, shell=True)  # noqa

if __name__ == "__main__":  # noqa
  main()  # noqa
