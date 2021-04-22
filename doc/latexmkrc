$latex = 'xelatex --no-pdf ' . $ENV{'LATEXOPTS'} . ' %O %S';
$pdflatex = 'echo "using custom latexmkrc"; '
. 'for f in *.tex_; do xelatex -jobname="${f%.*}" -interaction=nonstopmode -recorder "$f"; done; '
. 'xelatex ' . $ENV{'LATEXOPTS'} . ' %O %S';
$lualatex = 'lualatex ' . $ENV{'LATEXOPTS'} . ' %O %S';
$xelatex = 'xelatex --no-pdf ' . $ENV{'LATEXOPTS'} . ' %O %S';
$makeindex = 'makeindex -s python.ist %O -o %D %S';
add_cus_dep( "glo", "gls", 0, "makeglo" );
sub makeglo {
 return system( "makeindex -s gglo.ist -o '$_[0].gls' '$_[0].glo'" );
}
