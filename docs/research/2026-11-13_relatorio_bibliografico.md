# Relatório bibliográfico — tarefa R1-BIB-01 (2026-11-13)

Agente: academic-research-auditor (Agente 15). Emissor: Supervisor (Agente 01).
Status: **parcial** (ver Seção 4). Data de acesso de todas as consultas: **2026-11-13**.

## Método e limites de acesso (declarados antes de qualquer afirmação)

- Bases/catálogos consultados: J-STAGE (editor), Crossref REST API, Semantic Scholar Graph API,
  Open Library Search API, NIST Reference on Constants/CODATA, GitHub (pycalphad), sites de editores
  (Wiley, AIP, JMST) e busca na web geral.
- **Nenhum livro desta lista foi acessado em texto integral.** A verificação foi de **identidade
  bibliográfica** (autoria, título, edições, ano, editora, ISBN quando localizado). Sumários não foram
  abertos; por isso **nenhuma seção, capítulo ou página foi confirmada** neste relatório.
- Ferramentas indisponíveis nesta sessão: shell, OCR e renderizador de PDF (poppler ausente). Consequência:
  **PDFs sem camada de texto não puderam ser lidos** (isso bloqueou a Parte B — ver
  `docs/research/2026-11-13_entalpias_binarias_candidatas.json`).
- Acessos bloqueados pelo servidor: Wiley Online Library (HTTP 403), MDPI busca (HTTP 403).
- Regra aplicada: nada marcado como verificado sem URL consultada. Nenhum DOI, ISBN, página, autor ou
  valor foi inventado ou completado de memória.

---

## Seção 1 — Referências FORNECIDAS pelo usuário (numeração 1–11 preservada)

### 1. Gaskell, D. R. — *Introduction to the Thermodynamics of Materials*
- **Estado: metadados confirmados (parcialmente) no Open Library.**
- URL: `https://openlibrary.org/search.json?q=Introduction+to+the+Thermodynamics+of+Materials+Gaskell` (2026-11-13).
- Registros lidos: ed. de 1995, Taylor & Francis (ISBN 9781560329923, 1560324325, 9781591690436);
  ed. de 2003 (ISBN 9781591690139, 9781498757034, 9781032451015, CRC Press/Taylor & Francis);
  **6ª edição, 2017, Taylor & Francis, por David R. Gaskell e David E. Laughlin** (ISBN 9781498757003,
  9781498757027, 1498757006).
- **Divergência em relação ao que o usuário escreveu:** a partir da 6ª edição a obra tem **coautor
  (D. E. Laughlin)**, omitido na lista. É preciso dizer qual edição será citada.
- **O que pode sustentar no sistema:** base conceitual de ΔG = ΔH − TΔS, entropia de mistura de solução
  ideal e modelo de solução regular — usados em `backend/app/engines/hea/analitico.py`. **Capítulo/seção
  não confirmados** (sumário não consultado).

### 2. DeHoff, R. T. — *Thermodynamics in Materials Science*
- **Estado: metadados confirmados (parcialmente) no Open Library.**
- URL: `https://openlibrary.org/search.json?q=Thermodynamics+in+Materials+Science+DeHoff` (2026-11-13).
- Registros lidos: 1ª ed. 1993, McGraw-Hill (ISBN 0070163138/9780070163133); edição 2006, CRC/Taylor &
  Francis (ISBN 0849340659/9780849340659); existe *Solutions Manual* separado (2006, CRC, ISBN 0849381657).
- **Divergência:** o usuário escreveu apenas "Robert DeHoff"; o nome no catálogo é **Robert T. DeHoff**.
  Edição não especificada (há 1993 e 2006, em editoras diferentes).
- **O que pode sustentar:** mesmo escopo do item 1 (solução ideal/regular, energia livre de mistura).
  Seções **não confirmadas**.

### 3. Callister, W. D. — *Ciência e Engenharia de Materiais: Uma Introdução*
- **Estado: metadados parcialmente confirmados** (via agregadores de catálogo, não no site da editora).
- URLs: `https://minhabiblioteca.com.br/catalogo/livro/98804/ci-ncia-e-engenharia-de-materiais` e
  `https://www.estantevirtual.com.br/livro/ciencia-e-engenharia-de-materiais-uma-introducao-77I-9678-000-BK` (2026-11-13).
- Confirmado: **10ª ed., Rio de Janeiro: LTC, 2020** — ISBN impresso 9788521637325, ISBN digital
  9788521637288. Também localizado registro de edição LTC de 2012 com ISBN 9788521621249 (indicada por uma
  fonte como 8ª ed.).
- **Divergências importantes:**
  1. A obra tem **coautor David G. Rethwisch** desde a 7ª/8ª edição em inglês; o usuário omitiu-o. O código
     backend já cita "Callister & Rethwisch" (correto), mas a lista do usuário não.
  2. O **frontend cita "CAL9" (9ª edição) com páginas** (`§3.5, p. 54` etc.). O **ISBN e os dados da 9ª
     edição em português NÃO foram localizados** nesta sessão, e **nenhuma página foi confirmada**.
  3. Há também *Fundamentos da Ciência e Engenharia de Materiais* (obra distinta, do mesmo autor) no
     catálogo — risco de confusão de citação.
- **O que pode sustentar:** densidade teórica ρ = nA/(V_C·N_A), FEA, relações a–R, índices de Miller e
  Miller-Bravais, densidades linear/planar, regras de Hume-Rothery, conversão at.% ↔ %massa e dilatação
  térmica — tudo já citado no código. **Nenhuma seção/página verificada.**

### 4. Cullity, B. D.; Stock, S. R. — *Elements of X-Ray Diffraction*
- **Estado: metadados confirmados no Open Library.**
- URL: `https://openlibrary.org/search.json?q=Elements+of+X-ray+diffraction` (2026-11-13).
- Registros lidos: 1ª ed. 1956, Addison-Wesley (ISBN 0201011743); edição 2001, Prentice Hall, Cullity e
  S. R. Stock (ISBN 0201610914); **3ª ed., Pearson, 2013/2014** (ISBN 9781292040547, 1292040548;
  edição indiana 9789332535169).
- **Divergência:** a coautoria de Stock existe só a partir da 3ª edição (as edições de 1956/1978 são só de
  Cullity). A busca combinada "Cullity Stock" retornou 0 registros; foi necessário buscar pelo título.
- **O que pode sustentar:** difração, lei de Bragg e fator de estrutura. **Observação de utilidade: não há,
  no repositório inspecionado, motor de difração** — esta obra hoje **não sustenta nenhuma funcionalidade
  implementada**; é referência de base/futuro (ver Seção 3).

### 5. Kittel, C. — *Introduction to Solid State Physics*
- **Estado: metadados confirmados no Open Library.**
- URL: `https://openlibrary.org/search.json?q=Introduction+to+Solid+State+Physics+Kittel` (2026-11-13).
- Registros lidos: 1ª ed. 1953, Wiley, 12 edições registradas no grupo principal; **"Kittel's Introduction
  to Solid State Physics", 2018, Wiley (ISBN 1119454166/9781119454168)** — reedição mais recente.
- **Divergência:** edição não especificada pelo usuário (há 8ª, 9ª e a reedição de 2018 com título alterado).
- **O que pode sustentar:** redes de Bravais, estruturas cristalinas, vibração da rede (contexto do critério
  de Lindemann em `thermodynamics/termico.py`). **Seções não confirmadas.**

### 6. Porter, D. A.; Easterling, K. E. — *Phase Transformations in Metals and Alloys*
- **Estado: metadados confirmados no Open Library.**
- URL: `https://openlibrary.org/search.json?q=Phase+Transformations+in+Metals+and+Alloys+Porter+Easterling` (2026-11-13).
- Registros lidos: 1ª ed. 1981 (Van Nostrand Reinhold); 2ª ed. 1992, Chapman & Hall (ISBN 0412450305/
  9780412450303); **"Revised Reprint", 2009, CRC/Taylor & Francis (ISBN 9781420062113)**; registros da
  **3ª edição listam um terceiro autor, Mohamed Y. Sherif** (ISBN 9781420074383, 9781000467796).
- **Divergência:** a 3ª edição tem **coautor (M. Y. Sherif)**, omitido na lista.
- **O que pode sustentar:** termodinâmica de soluções, diagramas de fase, nucleação. É a fonte adequada para
  a advertência, já presente no código, de que ΔG_mix < 0 não prova fase única. **Seções não confirmadas.**

### 7. Reed-Hill, R. E.; Abbaschian, R. — *Princípios de Metalurgia Física*
- **Estado: a EDIÇÃO EM PORTUGUÊS NÃO FOI LOCALIZADA.** Metadados do original em inglês parcialmente
  confirmados.
- URLs: `https://find.library.upatras.gr/Record/135637/Description?lng=en`,
  `https://www.schweitzer-online.de/en/buch/Hill/Physical-Metallurgy-Principles/9780534268688/A22153164/` (2026-11-13).
- Confirmado no original: **R. E. Reed-Hill, R. Abbaschian, *Physical Metallurgy Principles***; 2ª ed. rev.
  1973 (ISBN 9780534268688); 3ª ed. PWS-Kent, c.1992/1994 (ISBN 0534921736); 4ª ed. Cengage Learning
  (edição indiana, 2010, ISBN 9788131520697).
- **Divergência:** o título em português "Princípios de Metalurgia Física" **não foi encontrado em nenhum
  catálogo consultado**; não há confirmação de tradução, editora brasileira, tradutor ou ISBN. **Não citar
  como obra em português sem confirmação.**
- **O que pode sustentar:** soluções sólidas, discordâncias, encruamento. **Nada implementado depende dela hoje.**

### 8. Padilha, A. F. — *Metalurgia Física*
- **Estado: NÃO LOCALIZADA.** Nenhum livro com este título e esta autoria foi encontrado.
- URLs: `https://repositorio.usp.br/item/001577950`,
  `https://www.udesc.br/arquivos/cct/id_cpmenu/7913/EL_MFI_Metalurgiaf_sica_16540033916717_7913.pdf` (2026-11-13).
- Obras **efetivamente localizadas** do autor: *Transformações de Fase* (com Paulo Rangel Rios, Artliber,
  2007, 215 p., ISBN 8588098369); *Encruamento, Recristalização, Crescimento de Grão e Textura* (com
  Fúlvio Siciliano Jr., ABM — registros divergem entre 1995 e 2ª ed. 1996, sem ISBN localizado);
  *Materiais de Engenharia: Microestrutura e Propriedades* (Hemus, 1997, sem ISBN localizado).
- **Hipótese (não verificada):** "Metalurgia Física" pode ser nome de **disciplina/apostila**, não de livro.
  É preciso que o usuário informe a obra pretendida.

### 9. Tilley, R. J. D. — *Cristalografia: Cristais e Estruturas Cristalinas*
- **Estado: metadados parcialmente confirmados** (ISBN em agregador; editora e tradutor **não confirmados**).
- URLs: `https://www.buscape.com.br/livros/cristalografia-cristais-e-estruturas-cristalinas-richard-j-d-tilley-9788579751547`,
  `https://www.wiley-vch.de/en/areas-interest/natural-sciences/crystals-and-crystal-structures-978-1-119-54838-6` (2026-11-13).
- Confirmado: edição em português com **ISBN 9788579751547**; uma bibliografia de disciplina da USP a cita
  como **1ª ed., 2014**. Original: *Crystals and Crystal Structures*, Wiley — 1ª ed. 2006 (ISBN
  9780470018200), **2ª ed. maio/2020, 312 p. (ISBN 9781119548386)**.
- **Divergência:** a atribuição da editora "Oficina de Textos" **não foi confirmada** em nenhuma fonte
  consultada; o tradutor não foi localizado.
- **O que pode sustentar:** redes de Bravais, sistemas cristalinos, índices de Miller — tema do CrystaLab.
  **Seções não confirmadas.**

### 10. Ávila, S. G. de; Becker, M. — *Mineralogia e Cristalografia*
- **Estado: NÃO LOCALIZADA.** Nenhum registro com esta autoria e este título foi encontrado.
- URL: `https://minhabiblioteca.com.br/catalogo/livro/80808/mineralogia` (2026-11-13).
- O que foi encontrado: livro **"Mineralogia" (SAGAH, 2020, ISBN impresso 9786556900346)**, de **outros
  autores** (R. S. Wetzel, M. F. Leão, L. A. da Silva). "Mineralogia e Cristalografia" aparece como **nome de
  disciplina** (p. ex. CG 517 na UFC), não como título de livro nos resultados.
- **Pendência:** o usuário precisa fornecer ISBN, editora e ano, ou o link do material (pode ser capítulo de
  obra coletiva da SAGAH/Grupo A, o que mudaria a forma de citação).

### 11. Chvátal, M. — *Cristalografia — Mineralogia para Principiantes*
- **Estado: NÃO LOCALIZADA.** Nenhum registro bibliográfico do título foi encontrado.
- URL: `https://gregem.ufes.br/sites/gregem.ufes.br/files/field/anexo/Cristalografia%20I%20Aula%201_0.pdf` (2026-11-13).
- Único rastro: material de aula da UFES que cita **"Chvátal, 2007"** como origem de imagens e definições de
  cristalografia, **sem título, editora nem ISBN**.
- **Hipótese (não verificada):** autor tcheco; pode haver original em tcheco e versão em português de Portugal.
- **Pendência:** confirmar com o usuário a obra exata (ISBN/editora) antes de qualquer citação.

### Resumo da Seção 1

| # | Obra | Estado |
|---|---|---|
| 1 | Gaskell | metadados confirmados (Open Library); coautor Laughlin na 6ª ed. omitido; edição a definir |
| 2 | DeHoff | metadados confirmados (Open Library); nome correto R. T. DeHoff; 1993 e 2006 |
| 3 | Callister | parcialmente confirmados; 10ª ed. LTC 2020 ISBN 9788521637325; coautor Rethwisch omitido; **9ª ed. PT e páginas não confirmadas** |
| 4 | Cullity & Stock | metadados confirmados; Stock só a partir da 3ª ed. (2013/2014) |
| 5 | Kittel | metadados confirmados; edição não especificada |
| 6 | Porter & Easterling | metadados confirmados; 3ª ed. tem coautor Sherif |
| 7 | Reed-Hill & Abbaschian | **edição em português não localizada**; original em inglês confirmado |
| 8 | Padilha, *Metalurgia Física* | **não localizada** (existem outras obras do autor) |
| 9 | Tilley | parcialmente confirmados (ISBN 9788579751547); **editora/tradutor não confirmados** |
| 10 | Ávila & Becker | **não localizada** |
| 11 | Chvátal | **não localizada** (só rastro "Chvátal, 2007" em material de aula) |

---

## Seção 2 — Fontes ADICIONAIS pesquisadas

Estados usados: **M+** = metadados verificados na fonte indicada; **C–** = conteúdo não lido (sem acesso ao
texto integral); **NL** = não localizada.

### A1. Takeuchi, A.; Inoue, A. (2005) — entalpias de mistura (modelo de Miedema)
*Classification of Bulk Metallic Glasses by Atomic Size Difference, Heat of Mixing and Period of Constituent
Elements and Its Application to Characterization of the Main Alloying Element.* **Materials Transactions**
46(12), 2817–2829, 2005. **DOI 10.2320/matertrans.46.2817**. Editor: The Japan Institute of Metals and Materials.
URL: `https://www.jstage.jst.go.jp/article/matertrans/46/12/46_12_2817/_article` (2026-11-13).
Acesso: *JOURNAL FREE ACCESS*; copyright © 2005 JIM, **sem licença Creative Commons declarada**.
Sustenta: ΔH_ij de `analitico.py:77` (`FONTE_MIEDEMA`) e, por consequência, ΔH_mix e Ω.
**Estado: M+ / C– (tabela não lida: PDF digitalizado, sem OCR disponível).** Detalhes e bloqueio em
`docs/research/2026-11-13_entalpias_binarias_candidatas.json`.

### A2. Zhang, Y.; Zhou, Y. J.; Lin, J. P.; Chen, G. L.; Liaw, P. K. (2008)
*Solid-Solution Phase Formation Rules for Multi-component Alloys.* **Advanced Engineering Materials** 10(6),
534–538, 2008. **DOI 10.1002/adem.200700240**. URL (metadados): `https://api.crossref.org/works/10.1002/adem.200700240` (2026-11-13).
Sustenta: parâmetro δ (`analitico.py:74`) e a "zona de solução sólida" do gráfico do frontend.
**Estado: M+ / C–.** Wiley retornou HTTP 403; Crossref e Semantic Scholar não trazem resumo.
**Alerta:** fontes secundárias divergem sobre a faixa de entalpia atribuída a este artigo
(−15 ≤ ΔH ≤ 5; −15 ≤ ΔH ≤ −5; −10 ≤ ΔH ≤ 5 kJ/mol). **Divergência não resolvida.**

### A3. Yang, X.; Zhang, Y. (2012)
*Prediction of high-entropy stabilized solid-solution in multi-component alloys.* **Materials Chemistry and
Physics** 132(2–3), 233–238, 2012. **DOI 10.1016/j.matchemphys.2011.11.021**.
URL: `https://api.crossref.org/works/10.1016/j.matchemphys.2011.11.021` (2026-11-13).
Sustenta: critério conjunto Ω ≥ 1,1 e δ ≤ 6,6 % (`textos.py:14–15,19`; `analitico.py:188`).
**Estado: M+ / C– (os valores 1,1 e 6,6 % não foram lidos na fonte).**

### A4. Guo, S.; Ng, C.; Lu, J.; Liu, C. T. (2011)
*Effect of valence electron concentration on stability of fcc or bcc phase in high entropy alloys.* **Journal
of Applied Physics** 109(10), artigo 103505, 2011. **DOI 10.1063/1.3587228**.
URLs: `https://api.crossref.org/works/10.1063/1.3587228` e
`https://api.semanticscholar.org/graph/v1/paper/DOI:10.1063/1.3587228` (2026-11-13).
Sustenta: VEC ≥ 8,0 (CFC) e VEC < 6,87 (CCC) (`textos.py:12–13,20`; `analitico.py:266–270`).
**Estado: M+ / C–.** O resumo confirma o tema (VEC × estabilidade fcc/bcc) mas **não traz números**.
Múltiplas fontes secundárias atribuem a Guo et al. exatamente 8,0 / 6,87 — **corroboração indireta, não leitura**.
Observação: o código cita "109, 103505" sem número de página — correto, é artigo numerado, **não inventar páginas**.

### A5. Yeh, J.-W. et al. (2004)
*Nanostructured High-Entropy Alloys with Multiple Principal Elements: Novel Alloy Design Concepts and
Outcomes.* **Advanced Engineering Materials** 6(5), 299–303, 2004. **DOI 10.1002/adem.200300567**.
URL: `https://api.crossref.org/works?query.bibliographic=...` (Crossref, 2026-11-13).
Sustenta: definição de HEA por composição (aviso de `analitico.py:470`) e o exemplo
`Al0.5CoCrCuFeNi` rotulado "CFC (Yeh 2004)" (`analitico.py:580`).
**Estado: M+ / C–.** Atenção: o código usa também "Yeh (2006)" em `textos.py:21` — **essa referência de 2006
não tem metadados no código e não foi verificada** (ver Seção 4).

### A6. Cantor, B.; Chang, I. T. H.; Knight, P.; Vincent, A. J. B. (2004)
*Microstructural development in equiatomic multicomponent alloys.* **Materials Science and Engineering: A**
375–377, 213–218, 2004. **DOI 10.1016/j.msea.2003.10.257**. URL: Crossref (2026-11-13).
Sustenta: origem da liga de Cantor (CoCrFeMnNi), citada no cartão de tarefa. **Hoje o catálogo do motor
(`analitico.py:576–582`) NÃO inclui CoCrFeMnNi** — a liga depende do Mn na matriz de entalpias.
**Estado: M+ / C–.**

### A7. Miracle, D. B.; Senkov, O. N. (2017)
*A critical review of high entropy alloys and related concepts.* **Acta Materialia** 122, 448–511, 2017.
**DOI 10.1016/j.actamat.2016.08.081**. URL: Crossref (2026-11-13).
Sustenta: `textos.py:21` (definição por entropia, ΔS ≥ 1,5R) e as advertências de domínio de validade.
**Estado: M+ / C–.** É revisão (fonte secundária de alta autoridade): adequada para contexto e para
contra-evidência, **não** para atribuir resultado primário.

### A8. Vegard, L. (1921)
*Die Konstitution der Mischkristalle und die Raumfüllung der Atome.* **Zeitschrift für Physik** 5, 17–26, 1921.
**DOI 10.1007/bf01349680**. URL: Crossref (2026-11-13).
Sustenta: lei de Vegard em `crystallography/ligas.py:5,58` e `ligas.py:748`.
**Estado: M+ / C–.** Os metadados conferem exatamente com o que o código cita ("Z. Phys. 5, 17–26 (1921)").

### A9. Darken, L. S.; Gurry, R. W. — *Physical Chemistry of Metals* (1953)
Editora McGraw-Hill, 1953. URL: `https://openlibrary.org/search.json?q=Physical+Chemistry+of+Metals+Darken+Gurry` (2026-11-13).
Sustenta: critério de eletronegatividade ±0,4 (`ligas.py:54,60,159,164`).
**Estado: metadados PARCIALMENTE confirmados.** Os registros do Open Library trazem título, editora e ano
corretos, mas listam **apenas L. S. Darken como autor**; a coautoria de **R. W. Gurry não foi confirmada**
nesta sessão, e **não há ISBN** (obra anterior ao ISBN). O limiar ±0,4 **não foi lido na fonte**.

### A10. Lindemann, F. A. (1910)
*Citado no código como:* "Phys. Z. 11, 609–612 (1910) — critério de fusão"
(`thermodynamics/termico.py:6,27`).
**Estado: NL / não verificada.** *Physikalische Zeitschrift* de 1910 não foi localizada em base consultável
nesta sessão (não indexada no Crossref). **Não confirmar volume nem páginas sem checagem em catálogo de
biblioteca ou repositório histórico.**

### A11. Regras de Hume-Rothery
O código as atribui a "Callister, seção 4.3" (`ligas.py:8,53,185`), não à obra original de Hume-Rothery.
**Estado: NL / não verificada.** Nenhuma publicação original de W. Hume-Rothery foi localizada ou verificada
nesta sessão. Para citar como regra histórica, falta a fonte primária; para citar como texto didático, falta
confirmar a seção no Callister.

### A12. Regra de Hägg (r/R < 0,59)
`ligas.py:9,55,200`. **Estado: NL / não verificada.** Nenhuma fonte (primária ou didática) foi localizada
para o limiar 0,59 nesta sessão. **É hoje um número sem fonte verificável no sistema.**

### A13. CODATA / NIST — constante dos gases R
Valor recomendado: **R = 8,314 462 618... J·mol⁻¹·K⁻¹, exato** (exato pela redefinição do SI).
URL: `https://physics.nist.gov/cgi-bin/cuu/Value?r` (2026-11-13). A página indica **CODATA 2022** como edição
dos dados.
Sustenta: `analitico.py:57` (`R_GASES = 8.314462618`). **Estado: verificada, valor idêntico.**
**Divergência de rótulo (não de valor):** o comentário do código diz "CODATA 2018"; a página do NIST
consultada é CODATA 2022. O valor é o mesmo (exato). Recomendação: ajustar o comentário para "valor exato do
SI (CODATA 2018 e 2022 coincidem)".
**N_A:** citado em `backend/tests/unit/test_arquitetura.py:81` e em `test_regressao_versoes.py:4` como
"CODATA 2018". **Não verificado nesta sessão** (a página de N_A não foi consultada).

### A14. pycalphad — documentação e licença
Repositório oficial: `https://github.com/pycalphad/pycalphad` (2026-11-13).
Descrição: "CALPHAD tools for designing thermodynamic models, calculating phase diagrams and investigating
phase equilibria". **Licença: MIT** (declarada no README). Citação pedida pelo projeto:
**Otis, R.; Liu, Z.-K. "pycalphad: CALPHAD-based Computational Thermodynamics in Python", Journal of Open
Research Software 5(1), DOI 10.5334/jors.140 (2017)** — DOI lido na página do repositório, **não conferido
no Crossref**. **Versão liberada mais recente: não exibida na página** (seção de releases vazia).
**Estado: licença e citação verificadas na página do projeto; versão não verificada.**
Relevância: o sistema declara explicitamente **não** fazer CALPHAD (`textos.py:42,122`); pycalphad seria
dependência de uma funcionalidade futura, não de algo implementado.

### A15. de Boer, F. R.; Boom, R.; Mattens, W. C. M.; Miedema, A. R.; Niessen, A. K. — *Cohesion in Metals*
**Estado: NL.** A busca no Open Library retornou 0 registros
(`https://openlibrary.org/search.json?q=Cohesion+in+Metals+Transition+Metal+Alloys+de+Boer+Miedema`, 2026-11-13).
Autoria e título foram escritos aqui **a partir do pedido da tarefa**, não de catálogo verificado: **tratar
como não verificada**. É a compilação primária alternativa para as entalpias de Miedema (ver opção 3 do
bloqueio no JSON).

### A16. Kim, M. J. et al. (2020) — fonte secundária de valores de ΔH_ij
*Understanding microstructure and mechanical properties of (AlTa0.76)xCoCrFeNi2.1 eutectic high entropy
alloys via thermo-physical parameters.* **Journal of Materials Science & Technology** 57, 131–137, 2020.
**DOI 10.1016/j.jmst.2020.03.045**.
URLs: `https://www.jmst.org/EN/Y2020/V57/I0/131` e
`https://www.jmst.org/article/2020/1005-0302/1005-0302-57-0-131/T6.html` (2026-11-13).
A Table 6 (lida em HTML) traz ΔH_ij e atribui os dados às refs. **[32] B. Chanda, J. Das, J. Alloys Compd.
798 (2019) 167–173** e **[33] A. Takeuchi, A. Inoue, Mater. Trans. 46 (2005) 2817–2829** (lista de
referências lida na página).
**Estado: metadados verificados; 15 valores lidos em tabela HTML; atribuição conjunta a duas fontes ⇒
confiança baixa.** Registrados no JSON como `fonte: secundaria`.

### A17. Askeland — "ASK6" citado no frontend
`frontend/src/modules/didactics/bank.ts:3` declara "ASK6 = Askeland 6ª ed."; a citação
`ASK6 §3-4, p. 72` aparece em `frontend/src/modules/crystalab/SidePanels.tsx:395`.
**Estado: NÃO VERIFICADA e AUSENTE da bibliografia fornecida pelo usuário.** Nenhuma busca foi feita nesta
sessão por falta de dados mínimos no código (título e autoria completos não constam).

### A18. Odetola, P. I. et al. (2024) — *Heliyon* — **RETRATADA: NÃO USAR**
*Exploring high entropy alloys: A review on thermodynamic design and computational modeling strategies for
advanced materials applications.* Heliyon 10(22):e39660. DOI 10.1016/j.heliyon.2024.e39660.
URL: `https://pmc.ncbi.nlm.nih.gov/articles/PMC11605370/` (2026-11-13).
A página do PMC marca o artigo como **retratado**, com aviso em Heliyon 12(1):e44468 (PMC13456000).
**Registrado aqui como advertência de integridade:** esta revisão aparece com facilidade em buscas sobre
critérios de HEA e **não deve ser citada**. (O aviso de retratação em si não foi aberto.)

---

## Seção 3 — Matriz afirmação–fonte

Estados: **A** = sustentada e verificada; **B** = fonte plausível, conteúdo não lido; **C** = sem fonte;
**D** = divergente / atribuição em conflito.

| # | Afirmação / equação / limiar no código | Local (arquivo:linha) | Fonte citada | Estado | Observação |
|---|---|---|---|---|---|
| M1 | `R = 8.314462618` J/(mol·K) | `backend/app/engines/hea/analitico.py:57` | CODATA/NIST (A13) | **A** | valor idêntico ao do NIST; só o rótulo do ano divergiu |
| M2 | ΔS_mix = −R·Σ xᵢ ln xᵢ | `analitico.py:72,84–85` | "entropia configuracional de Boltzmann" (sem referência) | **C** | expressão padrão, mas **sem fonte citada**; Gaskell (1) ou DeHoff (2) resolveriam |
| M3 | δ = 100·√(Σ xᵢ(1−rᵢ/r̄)²) | `analitico.py:338`, fonte em `:74` | Zhang 2008 (A2) | **B** | metadados ok; expressão não lida na fonte |
| M4 | δ ≤ 6,6 % | `textos.py:14`, `analitico.py:189` | Yang & Zhang 2012 (A3) | **D** | secundárias atribuem δ ≤ 6,6 % **também** a Zhang 2008; atribuição única não confirmada |
| M5 | Ω ≥ 1,1 | `textos.py:15`, `analitico.py:190` | Yang & Zhang 2012 (A3) | **B** | limiar não lido na fonte |
| M6 | Ω = T_m·ΔS/(1000·|ΔH|) | `analitico.py:411` | Yang & Zhang 2012 (A3) | **B** | definição não lida na fonte |
| M7 | VEC ≥ 8,0 ⇒ CFC | `textos.py:12`, `analitico.py:266` | Guo 2011 (A4) | **B** | corroborado por secundárias; não lido no primário |
| M8 | VEC < 6,87 ⇒ CCC | `textos.py:13`, `analitico.py:268` | Guo 2011 (A4) | **B** | idem |
| M9 | ΔS_mix ≥ 1,5R = alta entropia | `textos.py:16`, `analitico.py:58` | "Yeh (2006); Miracle & Senkov 2017" (`textos.py:21`) | **B/C** | Miracle & Senkov verificado (A7); **"Yeh (2006)" sem metadados e não verificado** |
| M10 | HEA exige ≥ 5 elementos principais | `analitico.py:470` | Yeh 2004 (A5) | **B** | metadados verificados |
| M11 | ΔH_mix = Σ 4·ΔH_ij·xᵢxⱼ e valores de ΔH_ij | `analitico.py:399`, fonte em `:77` | Takeuchi & Inoue 2005 (A1) | **B** | metadados verificados; **tabela não lida ⇒ ΔH_mix segue indisponível (correto)** |
| M12 | Domínio do VEC (ΔS ≥ 1R; grupos 4–11 + Al) | `analitico.py:69,247–251`, `textos.py:57–60` | **nenhuma** (declarado "sem fonte") | **C** | o código já declara isso; honesto, mas é pendência |
| M13 | `MARGEM_LIMIAR = 0.02` e `DH_PEQUENO = 1.0` | `analitico.py:61,63` | "heurística do especialista" | **C** | sem fonte; declarado |
| M14 | Zona do gráfico: −15 < ΔH < 5 kJ/mol e δ < 6,6 % | frontend (gráfico HEA) / `textos.py:14` | Zhang 2008 (A2) | **D** | faixa de ΔH **divergente entre secundárias**; manter `verificada: false` |
| M15 | T_m = Σ xᵢ·T_f,ᵢ (regra das misturas) | `analitico.py:348` | nenhuma | **C** | o código já avisa que não é solidus/liquidus |
| M16 | Lei de Vegard: a = (1−x)a_A + x·a_B | `crystallography/ligas.py:5,58,748` | Vegard 1921 (A8) | **B** | metadados **exatamente** conferentes (Z. Phys. 5, 17–26, 1921) |
| M17 | at.% ↔ %massa, "eq. 4.6–4.7" | `ligas.py:7,59` | Callister & Rethwisch (3) | **B**, numeração **não verificada** | **nenhuma equação/seção foi confirmada**; não há edição citada (o próprio código marca CR-10) |
| M18 | Hume-Rothery, "seção 4.3"; ±15 % de tamanho | `ligas.py:8,53,185` | Callister, seção 4.3 (3) / A11 | **B**, seção **não verificada** | falta fonte primária de Hume-Rothery |
| M19 | ±0,4 de eletronegatividade | `ligas.py:54,60,159,164` | Darken & Gurry 1953 (A9) | **B** | obra confirmada; **coautor Gurry e o valor 0,4 não confirmados** |
| M20 | Regra de Hägg: r/R < 0,59 | `ligas.py:9,55,200` | "Hägg" (A12) | **C** | **nenhuma referência bibliográfica no código e nenhuma localizada** |
| M21 | Dilatação a(T) = a₂₀[1+α(T−20)], "seção 19.3" | `thermodynamics/termico.py:4,26` | Callister & Rethwisch (3) | **B**, seção **não verificada** | sem edição citada |
| M22 | Critério de Lindemann u/d = f√(T/T_f) | `thermodynamics/termico.py:6,27` | Lindemann 1910 (A10) | **B/NL** | **"Phys. Z. 11, 609–612 (1910)" não pôde ser conferido em nenhuma base** |
| M23 | Densidades planares, "seção 3.11" | `crystallography/planar.py:6,83` | Callister & Rethwisch (3) | **B**, seção **não verificada** | |
| M24 | Contato de esferas rígidas, "seções 3.4 e 3.5" | `crystallography/passos.py:22` | Callister & Rethwisch (3) | **B**, seção **não verificada** | |
| M25 | `CAL9 §3.12, p. 75` (empilhamento ABAB/ABCABC) | `frontend/src/modules/crystalab/SidePanels.tsx:350`; `Results.tsx:117` | Callister 9ª ed. (3) | **B**, página **NÃO verificada** | a 9ª ed. em português não foi localizada; página não conferida |
| M26 | `CAL9 §3.6, p. 55` e `ASK6 §3-4, p. 72` | `SidePanels.tsx:395` | Callister 9ª ed. (3); Askeland 6ª ed. (A17) | **B/C**, páginas **NÃO verificadas** | ASK6 **não está na bibliografia fornecida** e não tem autoria/título no código |
| M27 | `CAL9 §3.5, p. 54` (ρ = nA/V_C N_A) | `Results.tsx:116`; `QuizPanel.tsx:47`; `bank.ts:22,79` | Callister 9ª ed. (3) | **B**, página **NÃO verificada** | |
| M28 | `CAL9 §3.4, p. 48–54` (FEA, a–R, nº de coordenação) | `QuizPanel.tsx:33,34,48–52`; `bank.ts:31,40,49` | Callister 9ª ed. (3) | **B**, página **NÃO verificada** | |
| M29 | `CAL9 §3.8–3.10, p. 58–74` (Miller/Miller-Bravais) | `QuizPanel.tsx:40,41,52`; `bank.ts:58,67` | Callister 9ª ed. (3) | **B**, página **NÃO verificada** | |
| M30 | `CAL9 §3.11, p. 74` (densidade linear) | `QuizPanel.tsx:53` | Callister 9ª ed. (3) | **B**, página **NÃO verificada** | |
| M31 | `CAL9 Tab. 3.1, p. 49` (Mg é HC; raios/densidades) | `QuizPanel.tsx:38`; `bank.ts:79`; `_origem/.../crystalab_modulo1.py:18` | Callister 9ª ed. (3) | **B**, página **NÃO verificada** | seed `metais.json` já está `aguardando_validacao` por isso (CR-10, `app/repositories/seed_sql.py:4`) |
| M32 | `CAL9 Cap. 3, p. 48–75` + `ASK6 Cap. 3, p. 60–96` | `bank.ts:88` | (3) e A17 | **B/C**, páginas **NÃO verificadas** | |
| M33 | Cullity & Stock (4) sustenta algo no sistema | — | (4) | **sem uso** | não há motor de difração no repositório: a obra **não sustenta funcionalidade implementada** |
| M34 | Reed-Hill (7), Padilha (8), Ávila & Becker (10), Chvátal (11) sustentam algo | — | (7),(8),(10),(11) | **sem uso** | nenhuma é citada em código; e três delas não foram localizadas |

**Recomendação explícita sobre as citações com página (M25–M32):** nenhuma das páginas (`p. 48`, `p. 54`,
`p. 55`, `p. 72`, `p. 74`, `p. 75`, `p. 49`, `p. 58–74`, `p. 60–96`) foi confirmada, e a própria 9ª edição em
português não foi localizada. Até que alguém com o exemplar confira, **remover o número de página ou
marcá-la como não verificada na interface** (o padrão já adotado no motor HEA com `verificada: false`).
Manter página não conferida em material didático é risco pedagógico direto.

---

## Seção 4 — Pendências bibliográficas concretas

**Pode ser resolvido só pelo usuário (acesso físico/assinatura):**
1. **Entalpias de Takeuchi & Inoue 2005** — fornecer o PDF com OCR, a transcrição da tabela (com número da
   tabela e página), ou autorizar instalação de `poppler-utils` + extração por agente com shell.
   **Sem isso, ΔH_mix e Ω permanecem indisponíveis.** (Detalhes no JSON.)
2. **Callister, 9ª edição em português** — confirmar ISBN/ano e **conferir as páginas** citadas em
   M25–M32. Decidir se o sistema passa a citar a 10ª ed. (LTC, 2020, ISBN 9788521637325), o que **mudaria
   todas as páginas**.
3. **Itens 8, 10 e 11 da lista** (Padilha "Metalurgia Física"; Ávila & Becker; Chvátal) — fornecer ISBN,
   editora e ano, ou o link/arquivo. **Não localizadas; não citar até então.**
4. **Item 7 (Reed-Hill em português)** — confirmar se existe tradução; caso não exista, citar o original
   *Physical Metallurgy Principles* com a edição correta.
5. **Item 9 (Tilley em português)** — confirmar editora e tradutor (ISBN 9788579751547).
6. **"ASK6" (Askeland)** — informar autoria, título e edição completos; a obra **não está** na bibliografia
   fornecida, mas é citada com página no frontend.
7. **"Yeh (2006)"** (`backend/app/engines/hea/textos.py:21`) — informar a referência completa; hoje é uma
   citação sem metadados.
8. **Faixa de ΔH da "zona de solução sólida"** — conferir em Zhang et al. (2008) qual é a faixa publicada
   (−15 a 5, −15 a −5 ou −10 a 5 kJ/mol) e o domínio de validade declarado. **Fontes secundárias divergem.**
9. **Lindemann 1910** — confirmar volume/páginas em catálogo de biblioteca; não indexado no Crossref.
10. **Regra de Hägg (0,59)** e **limiar de ±0,4 de Darken & Gurry** — fornecer a página da fonte; hoje são
    números sem suporte verificado.

**Pode ser resolvido pelo Supervisor com outros agentes (registrado, não acionado por mim):**
11. **HEA specialist / Materials Science:** parecer sobre o domínio de validade do critério de VEC
    (M12) e sobre as heurísticas sem fonte (M13), que hoje saem como "sem fonte bibliográfica".
12. **Materials Science:** confirmar se o par **Cr–Ni** vale −5 ou −7 kJ/mol (divergência registrada no JSON)
    antes de qualquer uso.
13. **Decisão de escopo:** Cullity & Stock (4) e Kittel (5) **não sustentam nada implementado**. Manter na
    bibliografia como referência de base é legítimo, mas não devem aparecer como fonte de resultado.
14. **Catálogo HEA:** CoCrFeMnNi (liga de Cantor, A6 verificada) não está em `EXEMPLOS`
    (`analitico.py:576–582`). Se for incluída, depende de entalpias com Mn — hoje inexistentes.

**Advertência de integridade:** a revisão de Heliyon sobre projeto termodinâmico de HEAs (A18,
DOI 10.1016/j.heliyon.2024.e39660) está **retratada** e aparece com destaque em buscas sobre estes critérios.
**Não citar.**
