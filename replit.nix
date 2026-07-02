{ pkgs }: {
  # System libraries required by the Python PDF/image stack:
  #   WeasyPrint -> pango, cairo, gdk-pixbuf, glib, fontconfig, harfbuzz, libffi
  #   pdf2image  -> poppler_utils
  deps = [
    pkgs.pango
    pkgs.cairo
    pkgs.gdk-pixbuf
    pkgs.glib
    pkgs.fontconfig
    pkgs.harfbuzz
    pkgs.libffi
    pkgs.poppler_utils
    pkgs.ghostscript
  ];
}
