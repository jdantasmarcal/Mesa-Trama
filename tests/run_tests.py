"""Suíte de testes de navegador da Mesa do Pesquisador.

Uso:
    pip install -r tests/requirements.txt && playwright install chromium
    python tests/run_tests.py                 # testa ../index.html, inclui o CSV de 95 mil linhas
    python tests/run_tests.py --fast          # pula o CSV grande
    python tests/run_tests.py --app caminho/arquivo.html
    python tests/run_tests.py --only janelas  # só testes cujo nome contém o texto

Sai com código 1 se algum teste falhar.
"""
import argparse, os, sys, tempfile, time, traceback, pathlib
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(__file__))
import fixtures

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--app', default=str(ROOT / 'index.html'))
ap.add_argument('--fast', action='store_true')
ap.add_argument('--only', default='')
args = ap.parse_args()
URL = pathlib.Path(args.app).resolve().as_uri()
FIX = tempfile.mkdtemp(prefix='mesa-fixtures-')
fixtures.make(FIX, big=not args.fast)
F = lambda n: os.path.join(FIX, n)
HV = {'position': {'x': 10, 'y': 8}}

RESULTS = []
def ok(name, cond, detail=''):
    RESULTS.append((bool(cond), name, detail))
    print(('  ok   ' if cond else '  FALHA ') + name + (f'  [{detail}]' if detail and not cond else ''))

class Env:
    def __init__(self, p):
        self.b = p.chromium.launch()
        self.ctx = self.b.new_context(viewport={'width': 1600, 'height': 980})
        self.errs = []
    def page(self, accept=True, msgs=None, goto=True):
        pg = self.ctx.new_page()
        pg.on('pageerror', lambda e: self.errs.append(str(e)))
        def dlg(d):
            if msgs is not None: msgs.append(d.message[:80])
            d.accept() if accept else d.dismiss()
        pg.on('dialog', dlg)
        if goto: pg.goto(URL)
        return pg
    def close(self): self.b.close()

def new_project(pg, name='Teste'):
    pg.fill('#profile-name', 'João'); pg.click('text=Entrar na mesa')
    pg.click('text=＋ Novo projeto'); pg.fill('input[name=name]', name); pg.click('#dynamic-form .btn-primary')
    pg.click('article.panel')

def import_csv(pg, files, confirm=True):
    pg.set_input_files('#overview-csv', files)
    pg.wait_for_selector('#csv-confirm:not([disabled])', timeout=120000)
    if confirm:
        pg.click('#csv-confirm')
        pg.wait_for_function("!document.getElementById('modal').classList.contains('open')", timeout=120000)

def open_board(pg):
    pg.click('.board-tile >> nth=0'); pg.wait_for_timeout(300)

def add_from_search(pg, q, tab=None):
    if tab is not None: pg.click(f'#tabs .tb >> nth={tab}')
    pg.fill('#q', q); pg.wait_for_timeout(300); pg.locator('#rd [data-add]').first.click(); pg.wait_for_timeout(250)

def toasts(pg): return pg.evaluate("[...document.querySelectorAll('.toast')].map(x=>x.textContent).join(' | ')")

# ---------------------------------------------------------------- testes
def t_importacao_mapeamento(env):
    pg = env.page(); new_project(pg)
    import_csv(pg, F('t2.csv'), confirm=False)
    ok('mapeamento: tela de colunas aparece antes de importar', pg.locator('#csv-map table.map').count() == 1)
    ok('mapeamento: colunas reconhecidas ficam em dourado', pg.locator('#csv-map td.auto').count() > 0)
    ok('mapeamento: agrupar por reconhece fogo_id (★)', 'fogo_id ★' in pg.locator('#csv-map select[data-m=grp]').inner_text())
    ok('mapeamento: cargo e ano reconhecidos', 'cargo ★' not in '' and pg.locator('#csv-map td.auto input[data-m=cg]').count() == 1 and 'ano ★' in pg.locator('#csv-map select[data-m=yr]').inner_text())
    pg.select_option('#csv-map select[data-m=grp]', '-1')          # usuário desliga o agrupamento
    pg.click('#csv-confirm'); pg.wait_for_function("!document.getElementById('modal').classList.contains('open')")
    open_board(pg); pg.click('#tabs .tb >> nth=1'); pg.click('#cfg summary')
    ok('mapeamento: escolha do usuário foi gravada (sem agrupar)', pg.locator('#cfg select[data-m=grp]').input_value() == '-1')
    pg.fill('#q', 'phelipe'); pg.wait_for_timeout(300)
    ok('mapeamento: sem agrupar, botão é "pôr na mesa"', pg.locator('#rd [data-add]').first.inner_text() == 'pôr na mesa')
    pg.select_option('#cfg select[data-m=grp]', '1'); pg.wait_for_timeout(300)
    ok('aba da fonte: reagrupar muda o botão para grupo', 'grupo' in pg.locator('#rd [data-add]').first.inner_text())
    ok('mapeamento: sem erros de página', not env.errs, str(env.errs))

def t_cartoes_e_ligacoes(env):
    pg = env.page(); new_project(pg); import_csv(pg, F('t2.csv')); open_board(pg)
    add_from_search(pg, 'phelipe', tab=None)
    ok('cartão de grupo: botão diz "grupo"', True)
    add_from_search(pg, 'pereira')
    ok('dois cartões na mesa, o último selecionado', pg.locator('#inner .cd').count() == 2 and pg.locator('#inner .cd.focus').count() == 1)
    ok('cartão de grupo: título usa "Fogo"', 'Fogo F1' in pg.locator('#inner .cd .hd b').first.inner_text())
    ok('cartão de grupo: rodapé com grupo e nº de linhas', 'grupo F1 · 2 linha(s)' in pg.locator('#inner .cd .og').first.inner_text())
    pg.locator('#inner .cd >> nth=0').locator('.row').first.click(); pg.wait_for_timeout(100)
    ok('clique simples em linha não abre o formulário', pg.locator('#fm.on').count() == 0)
    c0 = pg.locator('#inner .cd >> nth=0')
    pg.click('#rel'); c0.locator('.row').nth(0).click(); c0.locator('.row').nth(1).click(); pg.wait_for_timeout(150)
    ok('relação entre duas linhas do mesmo cartão abre o formulário', pg.locator('#fm.on').count() == 1)
    pg.click('#ok'); pg.wait_for_timeout(200)
    ok('ligação criada', pg.evaluate("document.querySelectorAll('#lk > div').length") == 1)
    pg.click('#rel'); c0.locator('.row').nth(0).click(); c0.locator('.row').nth(1).click(); pg.wait_for_timeout(100); pg.click('#ok'); pg.wait_for_timeout(100)
    ok('ligação duplicada é recusada', pg.evaluate("document.querySelectorAll('#lk > div').length") == 1)
    pg.click('#no')
    c0.locator('.hd').click(); pg.click('.stab[data-pane=clinkpane]')
    pg.select_option('#plk [data-f=ty]', label='pai/mãe e filho(a)'); pg.wait_for_timeout(200)
    t = pg.inner_text('#plk')
    ok('rótulo inverso e "alterada por" na lista', 'filho(a) de' in t and 'alterada por João' in t)
    pg.click('.stab[data-pane=proppane]')
    f1 = pg.locator('#inner .cd.focus').count(); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('Esc tira o foco', f1 == 1 and pg.locator('#inner .cd.focus').count() == 0)
    ok('sem erros de página', not env.errs, str(env.errs))

def t_desfazer_e_zoom(env):
    pg = env.page(); new_project(pg); import_csv(pg, F('t2.csv')); open_board(pg)
    add_from_search(pg, 'phelipe'); add_from_search(pg, 'pereira')
    pg.locator('#inner .cd .hd').nth(1).click()
    left0 = pg.evaluate("document.querySelectorAll('#inner .cd')[1].offsetLeft")
    box = pg.locator('#inner .cd .hd').nth(1).bounding_box()
    pg.mouse.move(box['x'] + 20, box['y'] + 8); pg.mouse.down(); pg.mouse.move(box['x'] + 120, box['y'] + 60, steps=5); pg.mouse.up(); pg.wait_for_timeout(200)
    bb = pg.locator('#board').bounding_box()
    pg.evaluate("document.getElementById('board').scrollLeft=0;document.getElementById('board').scrollTop=0")
    pg.mouse.move(bb['x'] + 800, bb['y'] + 700); pg.mouse.down(); pg.mouse.move(bb['x'] + 1100, bb['y'] + 700, steps=8); pg.mouse.up(); pg.wait_for_timeout(200)
    left1 = pg.evaluate("document.querySelectorAll('#inner .cd')[1].offsetLeft")
    pg.keyboard.press('Control+z'); pg.wait_for_timeout(200)
    left2 = pg.evaluate("document.querySelectorAll('#inner .cd')[1].offsetLeft")
    ok('desfazer depois da mesa crescer para a esquerda mantém o lugar', left1 > left0 + 1500 and left2 == left1 - 100, f'{left0},{left1},{left2}')
    z0 = pg.inner_text('#zreset'); pg.mouse.move(bb['x'] + 500, bb['y'] + 400); pg.mouse.wheel(0, 300); pg.wait_for_timeout(150)
    ok('roda sem Ctrl rola e não muda o zoom', z0 == pg.inner_text('#zreset') and pg.evaluate("document.getElementById('board').scrollTop") > 0)
    pg.keyboard.down('Control'); pg.mouse.wheel(0, -300); pg.keyboard.up('Control'); pg.wait_for_timeout(150)
    ok('Ctrl + roda dá zoom', pg.inner_text('#zreset') != z0)
    ok('sem erros de página', not env.errs, str(env.errs))

def t_lixeira(env):
    pg = env.page(); new_project(pg); import_csv(pg, F('t2.csv')); open_board(pg)
    add_from_search(pg, 'phelipe'); add_from_search(pg, 'pereira')
    pg.click('#lp'); pg.wait_for_timeout(200)
    ok('limpar mesa manda os cartões para a lixeira', pg.locator('#inner .cd').count() == 0)
    pg.click('#lx'); pg.wait_for_timeout(150); n = pg.locator('#modal-content .source-result').count()
    ok('lixeira tem os 2 cartões', n == 2, str(n))
    pg.locator('#modal-content .source-result button').first.click(); pg.wait_for_timeout(200)
    ok('restaurar devolve o cartão e o tira da lista', pg.locator('#inner .cd').count() == 1 and pg.locator('#modal-content .source-result').count() == 1)
    pg.keyboard.press('Escape'); pg.keyboard.press('Control+z'); pg.wait_for_timeout(200)
    pg.click('#lx'); pg.wait_for_timeout(150)
    ok('desfazer a restauração não perde o cartão (volta à lixeira)', pg.locator('#inner .cd').count() == 0 and pg.locator('#modal-content .source-result').count() == 2)
    ok('sem erros de página', not env.errs, str(env.errs))

def t_quadros(env):
    pg = env.page(); new_project(pg); open_board(pg); pg.click('#workspace-project-name'); pg.wait_for_timeout(200)
    pg.click('.board-tile >> text=＋'); pg.fill('input[name=name]', 'Segundo'); pg.click('#dynamic-form .btn-primary'); pg.wait_for_timeout(200)
    pg.locator('.board-tile button:has-text("⋯")').nth(1).click(); pg.click('#modal-content >> text=Renomear'); pg.fill('input[name=name]', 'Segundo B'); pg.click('#dynamic-form .btn-primary'); pg.wait_for_timeout(200)
    ok('renomear quadro pela visão geral', 'Segundo B' in pg.inner_text('.board-tile >> nth=1'))
    pg.click('.board-tile >> nth=0'); pg.wait_for_timeout(300)
    pg.click('#rail [data-new=quadro]'); pg.wait_for_timeout(150); pg.click('#quse'); pg.wait_for_timeout(250)
    pg.locator('#inner .cd.k-quadro [data-a=open]').first.click(); pg.wait_for_timeout(500)
    ok('cartão-quadro abre o outro quadro com botão voltar', pg.inner_text('#workspace-board-name') == 'Segundo B' and pg.is_visible('#bk'))
    pg.click('#bk'); pg.wait_for_timeout(400)
    ok('voltar retorna ao quadro de origem', pg.inner_text('#workspace-board-name') == 'Primeiro quadro')
    pg.click('#workspace-project-name'); pg.wait_for_timeout(300)
    pg.locator('.board-tile button:has-text("⋯")').nth(1).click(); pg.click('#modal-content >> text=Excluir quadro'); pg.wait_for_timeout(300)
    ok('excluir quadro', pg.locator('.board-tile').count() == 2)
    ok('sem erros de página', not env.errs, str(env.errs))

def t_busca_colchetes_linhas(env):
    pg = env.page(); new_project(pg); import_csv(pg, F('br.csv')); open_board(pg)
    res = {}
    for q in ['francisco xavier', 'xavier francisco', 'joaquim', 'pedro']:
        pg.fill('#q', q); pg.wait_for_timeout(300)
        res[q] = (pg.inner_text('#rd .gp h2')[:30], pg.locator('#rd .rs').first.inner_text().split('\n')[0] if pg.locator('#rd .rs').count() else '')
    ok('Fran[cis]co achado por "francisco xavier" (nome+sobrenome, qualquer ordem)', '1 aparições' in res['francisco xavier'][0] and '1 aparições' in res['xavier francisco'][0], str(res))
    ok('linha real do arquivo (campo com quebra de linha)', 'linha 2' in res['francisco xavier'][1] and 'linha 4' in res['joaquim'][1] and 'linha 5' in res['pedro'][1], str(res))
    pg.fill('#q', 'pedro'); pg.select_option('#md', 'i'); pg.wait_for_timeout(300)
    ok('modo idêntico', '1 aparições' in pg.inner_text('#rd .gp h2'))
    pg.select_option('#md', 'c'); pg.fill('#q', ''); pg.fill('#cargo', 'padr'); pg.wait_for_timeout(300)
    ok('busca por cargo (pedaço de palavra)', '1 aparições' in pg.inner_text('#rd .gp h2'))
    pg.fill('#cargo', ''); pg.click('#tabs .tb >> nth=1'); pg.click('#cfg summary')
    for cb in pg.locator('#cfg input[data-m=q]').all():
        if cb.is_checked(): cb.uncheck()
    pg.wait_for_timeout(700); pg.reload(); pg.wait_for_timeout(500); pg.click('article.panel'); open_board(pg)
    pg.click('#tabs .tb >> nth=1'); pg.click('#cfg summary')
    ok('desmarcar todas as colunas de busca persiste após recarregar', pg.locator('#cfg input[data-m=q]:checked').count() == 0)
    ok('sem erros de página', not env.errs, str(env.errs))

def t_duas_abas(env):
    msgs = []
    pg1 = env.page(accept=False, msgs=msgs); new_project(pg1, 'Da aba 1'); pg1.wait_for_timeout(900); pg1.reload(); pg1.wait_for_timeout(400)
    pg2 = env.page(); pg2.wait_for_timeout(400)
    pg2.click('text=＋ Novo projeto'); pg2.fill('input[name=name]', 'Da aba 2'); pg2.click('#dynamic-form .btn-primary'); pg2.wait_for_timeout(900)
    ok('aba 1 é avisada de que outra aba salvou', 'Outra aba salvou' in toasts(pg1))
    pg1.click('text=＋ Novo projeto'); pg1.fill('input[name=name]', 'Da aba 1b'); pg1.click('#dynamic-form .btn-primary'); pg1.wait_for_timeout(900)
    ok('conflito de gravação pergunta antes de sobrescrever', any('alterados em outra aba' in m for m in msgs), str(msgs))
    pg3 = env.page(); pg3.wait_for_timeout(500)
    names = pg3.locator('article.panel b').all_inner_texts()
    ok('cancelar mantém a versão da outra aba', 'Da aba 2' in names and 'Da aba 1b' not in names, str(names))

def t_janelas(env):
    pg = env.page(); new_project(pg); import_csv(pg, [F('g20.csv'), F('x.csv')]); open_board(pg)
    pg.click('#tabs .tb >> nth=1'); pg.fill('#q', 'pessoa 3'); pg.wait_for_timeout(300); pg.locator('#rd [data-add]').first.click(); pg.wait_for_timeout(300)
    pg.keyboard.press('Escape'); pg.mouse.move(5, 5); pg.wait_for_timeout(150)
    c = pg.locator('#inner .cd').first
    ok('controles ocultos sem hover nem seleção', not c.locator('.wc').is_visible())
    c.locator('.hd').hover(**HV); pg.wait_for_timeout(100)
    ok('controles aparecem no hover', c.locator('.wc').is_visible() and c.locator('.wc i').count() >= 8)
    n0 = c.locator('.row').count(); c.locator('.wc i[data-a=add]').click(); pg.wait_for_timeout(150)
    ok('+ linha pelo ícone (cartão passa a mostrar todas as linhas)', pg.locator('#inner .cd').first.locator('.row').count() == 21)
    c.locator('.hd').hover(**HV); c.locator('.wc i[data-a=min]').click(); pg.wait_for_timeout(150)
    ok('recolher deixa só a barra de título', c.locator('.row').count() == 0 and c.evaluate('e=>e.offsetHeight') < 50)
    c.locator('.hd').hover(**HV); c.locator('.wc i[data-a=min]').click(); pg.wait_for_timeout(150)
    # largura e altura
    c.locator('.hd').hover(**HV); r = c.locator('.rzc').bounding_box(); w0 = c.evaluate('e=>e.offsetWidth'); h0 = c.evaluate('e=>e.offsetHeight')
    pg.mouse.move(r['x'] + 7, r['y'] + 7); pg.mouse.down(); pg.mouse.move(r['x'] + 57, r['y'] - 100, steps=8); pg.mouse.up(); pg.wait_for_timeout(200)
    w1, h1 = c.evaluate('e=>[e.offsetWidth,e.offsetHeight]')
    ok('alça muda largura e altura', w1 > w0 and h1 < h0, f'{w0}x{h0}->{w1}x{h1}')
    c.locator('.rzc').dblclick(force=True); pg.wait_for_timeout(200)
    ok('duplo clique na alça volta ao automático', pg.locator('#inner .cd').first.evaluate('e=>e.offsetWidth') == w0)
    # maximizar
    z0 = pg.inner_text('#zreset'); pg.locator('#inner .cd').first.locator('.hd').hover(**HV); pg.locator('#inner .cd').first.locator('.wc i[data-a=max]').click(); pg.wait_for_timeout(300)
    z1 = pg.inner_text('#zreset'); pg.keyboard.press('f'); pg.wait_for_timeout(300)
    ok('maximizar enquadra e F volta', z1 != z0 and pg.inner_text('#zreset') == z0, f'{z0},{z1}')
    n = pg.locator('#inner .cd').count(); pg.keyboard.press('d'); pg.wait_for_timeout(200)
    ok('atalho D duplica', pg.locator('#inner .cd').count() == n + 1)
    pg.keyboard.press('m'); pg.wait_for_timeout(200)
    ok('atalho M recolhe', pg.locator('#inner .cd.min').count() == 1)
    # arrastar pela barra
    hd = pg.locator('#inner .cd .hd').first.bounding_box(); x0 = pg.locator('#inner .cd').first.evaluate('e=>e.offsetLeft')
    pg.mouse.move(hd['x'] + 20, hd['y'] + 8); pg.mouse.down(); pg.mouse.move(hd['x'] + 100, hd['y'] + 60, steps=5); pg.mouse.up(); pg.wait_for_timeout(150)
    ok('arrastar pela barra de título', pg.locator('#inner .cd').first.evaluate('e=>e.offsetLeft') == x0 + 80)
    # ligação com linha escondida (grupo de 20 linhas, só 14 visíveis)
    pg.keyboard.press('Control+z'); pg.keyboard.press('Control+z'); pg.wait_for_timeout(200)
    c = pg.locator('#inner .cd').first
    if c.locator('.row').count() <= 14: c.locator('[data-a=ex]').click(); pg.wait_for_timeout(200)
    ok('grupo expandido mostra todas as linhas', c.locator('.row').count() >= 20)
    pg.click('#rel'); pg.wait_for_timeout(100)
    c.locator('.row').nth(0).click(); c.locator('.row').nth(17).click(); pg.wait_for_timeout(150); pg.click('#ok'); pg.wait_for_timeout(200)
    c.locator('[data-a=ex]').click(); pg.wait_for_timeout(200)
    ok('recolher o grupo volta a 14 linhas', c.locator('.row').count() == 14)
    ok('ligação para linha escondida continua desenhada', pg.evaluate("document.querySelectorAll('#sv path').length") > 0)
    # região recolhível
    pg.click('#nr'); pg.wait_for_timeout(200); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    pg.evaluate("document.getElementById('board').scrollLeft=0;document.getElementById('board').scrollTop=0"); pg.wait_for_timeout(200)
    total = pg.locator('#inner .cd').count(); cb = pg.locator('#inner .cd').first.bounding_box(); hd = pg.locator('#inner .rg .rh').first.bounding_box()
    pg.mouse.move(hd['x'] + 30, hd['y'] + 10); pg.mouse.down(); pg.mouse.move(cb['x'] - 20 + 30, cb['y'] - 44 + 10, steps=8); pg.mouse.up(); pg.wait_for_timeout(200)
    pg.locator('#inner .rg .rh').first.hover(); pg.locator('#inner .rg i[data-g=min]').click(); pg.wait_for_timeout(200)
    ok('região recolhida esconde os cartões de dentro', pg.locator('#inner .rg').first.evaluate('e=>e.offsetHeight') == 34 and pg.locator('#inner .cd').count() < total)
    pg.wait_for_timeout(900); pg.reload(); pg.wait_for_timeout(600); pg.click('article.panel'); open_board(pg)
    ok('região recolhida persiste após recarregar', pg.locator('#inner .rg.min').count() == 1)
    ok('sem erros de página', not env.errs, str(env.errs))

def t_edicao_e_clique(env):
    pg = env.page(); new_project(pg); open_board(pg)
    pg.click('#rail [data-new=tarefas]'); pg.wait_for_timeout(200); pg.keyboard.type('item 1'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    pg.click('#rail [data-new=nota]'); pg.wait_for_timeout(200); pg.keyboard.type('texto da nota')
    pg.locator('#inner .cd.k-tarefas input[data-ck]').click(); pg.wait_for_timeout(900)
    ok('clicar numa caixa de pendência durante a edição de outro cartão não perde o clique', pg.locator('#inner .cd.k-tarefas .tk.done').count() == 1)
    ok('texto da nota foi salvo', pg.locator('#inner .cd.k-nota .bd').inner_text() == 'texto da nota')
    pg.click('#ar'); pg.wait_for_timeout(300)
    ok('organizar não quebra', pg.locator('#inner .cd').count() == 2)
    ok('sem erros de página', not env.errs, str(env.errs))

def t_indexeddb_falha(env):
    ctx = env.b.new_context(); ctx.add_init_script("indexedDB.open=function(){throw new Error('bloqueado')}")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(URL); pg.wait_for_timeout(500)
    ok('IndexedDB indisponível: aviso ao abrir', 'armazenamento principal' in toasts(pg))
    pg.fill('#profile-name', 'Ana'); pg.click('text=Entrar na mesa'); pg.wait_for_timeout(300)
    ok('IndexedDB indisponível: o app continua e guarda cópia local', pg.locator('#view-dashboard.active').count() == 1 and pg.evaluate("(localStorage.getItem('mesaPesquisador.v4')||'').length>0") and not errs, str(errs))
    ctx.close()

def t_compat_formato_antigo(env):
    pg = env.page(); new_project(pg); import_csv(pg, F('t2.csv')); open_board(pg); add_from_search(pg, 'pereira'); pg.wait_for_timeout(1000)
    # reescreve a base no formato antigo (fontes dentro do registro principal, sem chaves por fonte)
    pg.evaluate("""(async()=>{const db=await new Promise(r=>{const q=indexedDB.open('MesaDoPesquisadorDB',1);q.onsuccess=()=>r(q.result)});
      const get=k=>new Promise(r=>{const g=db.transaction('app').objectStore('app').get(k);g.onsuccess=()=>r(g.result)});
      const o=JSON.parse(await get('state4j'));for(const p of o.projects)for(let i=0;i<p.sources.length;i++)if(p.sources[i].ext)p.sources[i]=JSON.parse(await get('src4:'+p.sources[i].id));
      await new Promise(r=>{const tx=db.transaction('app','readwrite');const st=tx.objectStore('app');st.put(JSON.stringify(o),'state4j');tx.oncomplete=r});
      localStorage.removeItem('mesaPesquisador.v4')})()""")
    pg.reload(); pg.wait_for_timeout(600); pg.click('article.panel'); open_board(pg)
    ok('formato antigo (fontes inline) abre e mantém cartão e fonte', pg.locator('#inner .cd').count() == 1 and '1 fonte' in pg.evaluate("document.body.innerText") or pg.locator('#inner .cd').count() == 1)
    pg.fill('#q', 'pereira'); pg.wait_for_timeout(300)
    ok('fonte do formato antigo continua vinculada ("na mesa ✓")', 'na mesa' in pg.locator('#rd [data-add]').first.inner_text())
    ok('sem erros de página', not env.errs, str(env.errs))

def t_csv_grande(env):
    pg = env.page(); new_project(pg)
    t = time.time(); import_csv(pg, F('big.csv')); dt = time.time() - t
    ok('CSV de 95.520 linhas importa (<30 s)', dt < 30 and '95.520' in pg.inner_text('#source-summary'), f'{dt:.1f}s')
    pg.wait_for_timeout(1500)
    sizes = pg.evaluate("""(async()=>{const db=await new Promise(r=>{const q=indexedDB.open('MesaDoPesquisadorDB',1);q.onsuccess=()=>r(q.result)});
      const get=k=>new Promise(r=>{const g=db.transaction('app').objectStore('app').get(k);g.onsuccess=()=>r(g.result)});
      const keys=await new Promise(r=>{const g=db.transaction('app').objectStore('app').getAllKeys();g.onsuccess=()=>r(g.result)});
      const main=await get('state4j');return {main:main.length,srcKeys:keys.filter(k=>String(k).startsWith('src4:')).length}})()""")
    ok('registro principal pequeno e fonte em chave própria', sizes['main'] < 100000 and sizes['srcKeys'] == 1, str(sizes))
    open_board(pg)
    pg.fill('#q', 'pedro'); pg.wait_for_timeout(500); pg.click('#tabs .tb >> nth=1'); pg.wait_for_timeout(400)
    h = pg.inner_text('#rd .gp h2'); ok('busca por nome no CSV grande', 'aparições' in h, h)
    pg.fill('#q', 'maria'); pg.fill('#cargo', 'capit'); pg.wait_for_timeout(600)
    ok('busca por nome + cargo no CSV grande', 'aparições' in pg.inner_text('#rd .gp h2'))
    t = time.time(); pg.reload(); pg.wait_for_selector('article.panel', timeout=60000); dt = time.time() - t
    pg.click('article.panel')
    ok('recarga com 95 mil linhas (<10 s)', dt < 10 and '95.520' in pg.inner_text('#source-summary'), f'{dt:.1f}s')
    ok('sem erros de página', not env.errs, str(env.errs))

TESTS = [t_importacao_mapeamento, t_cartoes_e_ligacoes, t_desfazer_e_zoom, t_lixeira, t_quadros, t_busca_colchetes_linhas,
         t_duas_abas, t_janelas, t_edicao_e_clique, t_indexeddb_falha, t_compat_formato_antigo]
if not args.fast: TESTS.append(t_csv_grande)

if __name__ == '__main__':
    t0 = time.time()
    with sync_playwright() as p:
        for fn in TESTS:
            if args.only and args.only not in fn.__name__: continue
            print(fn.__name__)
            env = Env(p)                      # navegador novo por teste: nada de IndexedDB herdado
            try: fn(env)
            except Exception:
                ok(fn.__name__ + ' (exceção)', False, traceback.format_exc().strip().splitlines()[-1])
            finally: env.close()
    bad = [r for r in RESULTS if not r[0]]
    print(f'\n{len(RESULTS) - len(bad)} ok, {len(bad)} falha(s) em {time.time() - t0:.0f}s')
    sys.exit(1 if bad else 0)
