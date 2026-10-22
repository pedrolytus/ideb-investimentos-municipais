"""Gera as versões em PDF (A4) do diário e do guia da apresentação.

Uso (na raiz do projeto, com o ambiente ativado):
    python docs/gerar_pdfs.py

Converte o Markdown em HTML com o mistune (instalado junto com o Jupyter) e imprime
com o Chrome ou o Edge em modo headless. Rode de novo sempre que editar os .md.
"""
import html
import re
import subprocess
import tempfile
from pathlib import Path

import mistune

DOCS = Path(__file__).resolve().parent
ARQUIVOS = ['diario_do_projeto', 'guia_apresentacao']
NAVEGADORES = [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
               r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
               r'C:\Program Files\Microsoft\Edge\Application\msedge.exe']
SUBTITULO = ('Problema 4 – Política e Gestão Pública · FATESG – Aprendizado de Máquina Supervisionado<br>'
             'Pedro Lytus – LYTUS Inteligência de Negócios')

CSS = """
@page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-left { content: "%(rodape)s"; font: 8pt 'Segoe UI', Arial, sans-serif; color: #898781; }
    @bottom-right { content: "Página " counter(page) " de " counter(pages);
                    font: 8pt 'Segoe UI', Arial, sans-serif; color: #898781; }
}
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10.5pt/1.5 'Segoe UI', Calibri, Arial, sans-serif; color: #1f1f1d; margin: 0; }
h1 { font-size: 21pt; line-height: 1.2; margin: 0 0 4pt; color: #0b0b0b; }
.subtitulo { color: #52514e; font-size: 9.5pt; margin: 0 0 14pt; padding-bottom: 10pt;
             border-bottom: 1px solid #c3c2b7; }
h2 { font-size: 14.5pt; margin: 20pt 0 6pt; color: #0b0b0b; break-after: avoid; }
h3 { font-size: 12pt; margin: 16pt 0 5pt; color: #184f95; break-after: avoid; }
h4 { font-size: 10.5pt; margin: 12pt 0 4pt; color: #0b0b0b; break-after: avoid; }
h4 + table, h4 + ul, h4 + ol { break-before: avoid; }
p { margin: 0 0 6pt; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 7pt; padding-left: 18pt; }
li { margin: 0 0 2pt; }
strong { color: #0b0b0b; }
code { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; background: #f0efec;
       padding: 0 3px; border-radius: 3px; }
hr { border: 0; border-top: 1px solid #e1e0d9; margin: 14pt 0; }
blockquote { margin: 6pt 0 10pt; padding: 6pt 12pt; background: #f4f3ef; border-radius: 6px; color: #3a3936;
             break-inside: avoid; }
blockquote h3 { margin-top: 2pt; }
table { width: 100%%; border-collapse: collapse; margin: 4pt 0 10pt; font-size: 9pt; line-height: 1.35; }
thead { display: table-header-group; }
th { text-align: left; background: #e9eef6; color: #0b0b0b; font-weight: 600; padding: 4pt 6pt;
     border-bottom: 1px solid #9eb3d1; }
td { padding: 4pt 6pt; border-bottom: 1px solid #e1e0d9; vertical-align: top; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) td { background: #fafaf8; }
img { max-width: 100%%; display: block; margin: 4pt 0 12pt; border: 1px solid #e1e0d9; border-radius: 4px;
      break-inside: avoid; }
figure { margin: 8pt 0 14pt; break-inside: avoid; }
figure img { margin: 3pt 0 0; }
figcaption { font-weight: 600; color: #0b0b0b; font-size: 10pt; }
.task-list-item { list-style: none; margin-left: -14pt; }
.task-list-item-checkbox { margin-right: 6pt; }
"""


def para_html(origem):
    texto = origem.read_text(encoding='utf-8')
    titulo = re.search(r'^# (.+)$', texto, flags=re.M).group(1).strip()
    corpo = mistune.create_markdown(plugins=['table', 'task_lists', 'strikethrough'])(texto)
    # Legenda "Print – ..." + imagem viram uma figura que não se divide entre páginas
    corpo = re.sub(r'<p><strong>(Print – [^<]+)</strong></p>\s*<p>(<img [^>]+>)</p>',
                   r'<figure><figcaption>\1</figcaption>\2</figure>', corpo)
    # Parágrafo que é só um trecho em negrito funciona como subtítulo: não pode ficar órfão
    corpo = re.sub(r'<p><strong>([^<]+)</strong></p>', r'<h4>\1</h4>', corpo)
    corpo = corpo.replace('</h1>', f'</h1>\n<p class="subtitulo">{SUBTITULO}</p>', 1)
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<base href="{origem.parent.as_uri()}/">
<title>{html.escape(titulo)}</title>
<style>{CSS % {'rodape': titulo.replace('"', "'")}}</style>
</head><body>
{corpo}
</body></html>"""


navegador = next((n for n in NAVEGADORES if Path(n).exists()), None)
if navegador is None:
    raise SystemExit('Chrome ou Edge não encontrado. Ajuste a lista NAVEGADORES.')

for nome in ARQUIVOS:
    origem, destino = DOCS / f'{nome}.md', DOCS / f'{nome}.pdf'
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as tmp:
        tmp.write(para_html(origem))
    subprocess.run([navegador, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    '--allow-file-access-from-files', '--virtual-time-budget=5000',
                    f'--print-to-pdf={destino}', Path(tmp.name).as_uri()],
                   check=True, capture_output=True, timeout=180)
    Path(tmp.name).unlink(missing_ok=True)
    print(f'{destino.relative_to(DOCS.parent)}: {destino.stat().st_size / 1024:.0f} KB')
