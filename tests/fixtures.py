"""Gera os CSVs de teste (nenhum dado real do projeto é usado)."""
import os, random

def make(dest, big=True):
    os.makedirs(dest, exist_ok=True)
    w = lambda n, t: open(os.path.join(dest, n), 'w', encoding='utf-8', newline='').write(t)
    w('t2.csv', 'uid;fogo_id;nome;cargo;idade;ano;imagem\n1;F1;Phelipe de Souza;capitão;40;1776;img1.jpg\n2;F1;Maria da Silva;;30;1776;img1.jpg\n3;F2;José Pereira;padre;50;1777;img2.jpg\n4;F3;Anna Joze;;20;1778;img3.jpg\n')
    w('br.csv', 'fogo_id;nome;sobrenome;cargo;obs\n1;Fran[cis]co;Xavier;capitão;"uma\nduas"\n2;Joaq[ui]m;Pires;;x\n3;Pedro [?];Lima;padre;y\n')
    w('x.csv', 'fogo_id;nome;cargo\n1;Ana;\n')
    rows = ['fogo_id;nome;ano;idade;obs'] + [f'G1;Pessoa {i};1780;{20+i};obs {i}' for i in range(20)] + ['G2;Solo;1781;30;x']
    w('g20.csv', '\n'.join(rows) + '\n')
    if big:
        random.seed(1)
        nomes = ['Pedro', 'Maria', 'Joaquim', 'José', 'Ana', 'Antonio', 'Francisco', 'Manoel', 'Luzia', 'Joana', 'Bento', 'Inácio']
        sob = ['Pereira', 'Silva', 'Oliveira', 'de Almeida', 'da Costa', 'Ribeiro', 'Gomes', 'Lopes']
        cargos = ['', '', 'capitão', 'padre', 'sargento mor', 'alferes', 'lavrador', '']
        with open(os.path.join(dest, 'big.csv'), 'w', encoding='utf-8', newline='') as f:
            f.write('fogo_id,nome,sobrenome,ano,cargo,sexo,idade,estado,local,lista,arquivo,obs,pai\n')
            fogo = 0
            for i in range(95520):
                if i % 4 == 0: fogo += 1
                f.write(f'{fogo},{random.choice(nomes)},{random.choice(sob)},{1765+i%30},{random.choice(cargos)},{random.choice("MF")},{20+i%50},casado,Taubaté,Lista {i%9},Taubate_{1780+i%5}_{i%300:04d}.png,"obs {i}\nlinha dois",{random.choice(nomes)}\n')
