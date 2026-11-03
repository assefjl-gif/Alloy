/**
 * Banco inicial de atividades (6.3/6.4). Conteúdo conceitual com referência ao registro
 * bibliográfico do projeto (CAL9 = Callister 9ª ed.; ASK6 = Askeland 6ª ed.). Valores numéricos:
 * sempre do motor, no momento da resolução.
 */
import type { Activity } from './model.ts';

const CUBIC_METALS = ['Fe', 'Cr', 'Mo', 'W', 'Cu', 'Al', 'Ni', 'Ag', 'Au', 'Pb'];

export const ACTIVITIES: Activity[] = [
  {
    id: 'densidade-cobre', module: 'crystalab', topic: 'densidade', level: 'introdutorio', format: 'guided', pool: [], fixedMaterial: 'Cu',
    title: { 'pt-BR': 'Densidade teórica do cobre', en: 'Theoretical density of copper', es: 'Densidad teórica del cobre' },
    objective: { 'pt-BR': 'Calcular a densidade teórica de um metal CFC a partir do raio atômico e da massa atômica.', en: 'Compute the theoretical density of an FCC metal from its atomic radius and atomic mass.', es: 'Calcular la densidad teórica de un metal FCC a partir del radio atómico y la masa atómica.' },
    instructions: { 'pt-BR': 'Resolva cada passo; as dicas aparecem aos poucos. O resultado do motor só é revelado depois da sua tentativa.', en: 'Solve each step; hints appear gradually. The engine result is revealed only after your attempt.', es: 'Resuelva cada paso; las pistas aparecen de a poco. El resultado del motor solo se revela después de su intento.' },
    criteria: [
      { id: 'a', text: { 'pt-BR': 'Parâmetro de rede a (nm) com desvio ≤ 1 %', en: 'Lattice parameter a (nm) within 1 %', es: 'Parámetro de red a (nm) con desvío ≤ 1 %' }, tolerance: 0.01 },
      { id: 'vc', text: { 'pt-BR': 'Volume da célula Vc (cm³) com desvio ≤ 1 %', en: 'Cell volume Vc (cm³) within 1 %', es: 'Volumen de la celda Vc (cm³) con desvío ≤ 1 %' }, tolerance: 0.01 },
      { id: 'rho', text: { 'pt-BR': 'Densidade ρ (g/cm³) com desvio ≤ 1 %', en: 'Density ρ (g/cm³) within 1 %', es: 'Densidad ρ (g/cm³) con desvío ≤ 1 %' }, tolerance: 0.01 },
    ],
    explanation: { 'pt-BR': 'A densidade teórica é a massa dos átomos contidos na célula unitária dividida pelo volume da célula: ρ = nA/(Vc·N_A). Na CFC os átomos se tocam na diagonal da face, logo a = 2R√2 e Vc = a³.', en: 'Theoretical density is the mass of the atoms in the unit cell divided by the cell volume: ρ = nA/(Vc·N_A). In FCC the atoms touch along the face diagonal, so a = 2R√2 and Vc = a³.', es: 'La densidad teórica es la masa de los átomos contenidos en la celda unitaria dividida por el volumen de la celda: ρ = nA/(Vc·N_A). En FCC los átomos se tocan en la diagonal de la cara, así a = 2R√2 y Vc = a³.' },
    references: ['CAL9 §3.5, p. 54', 'CAL9 §3.4, p. 48'], validation: 'catalog-only',
  },
  {
    id: 'densidade-sorteada', module: 'crystalab', topic: 'densidade', level: 'intermediario', format: 'guided', pool: CUBIC_METALS,
    title: { 'pt-BR': 'Densidade teórica de um metal sorteado', en: 'Theoretical density of a random metal', es: 'Densidad teórica de un metal sorteado' },
    objective: { 'pt-BR': 'Aplicar o mesmo raciocínio a CCC ou CFC, escolhendo a relação a–R correta.', en: 'Apply the same reasoning to BCC or FCC, choosing the correct a–R relation.', es: 'Aplicar el mismo razonamiento a BCC o FCC, eligiendo la relación a–R correcta.' },
    instructions: { 'pt-BR': 'O metal é sorteado com uma semente reproduzível. Use “nova semente” para outra variação.', en: 'The metal is drawn with a reproducible seed. Use “new seed” for another variation.', es: 'El metal se sortea con una semilla reproducible. Use «nueva semilla» para otra variación.' },
    criteria: [{ id: 'rho', text: { 'pt-BR': 'Densidade com desvio ≤ 1 %', en: 'Density within 1 %', es: 'Densidad con desvío ≤ 1 %' }, tolerance: 0.01 }],
    explanation: { 'pt-BR': 'Na CCC, 4R = a√3 (contato na diagonal do cubo) e n = 2; na CFC, 4R = a√2 e n = 4.', en: 'In BCC, 4R = a√3 (contact along the cube diagonal) and n = 2; in FCC, 4R = a√2 and n = 4.', es: 'En BCC, 4R = a√3 (contacto en la diagonal del cubo) y n = 2; en FCC, 4R = a√2 y n = 4.' },
    references: ['CAL9 §3.4, p. 48–54', 'CAL9 §3.5, p. 54'], validation: 'catalog-only',
  },
  {
    id: 'atomos-por-celula', module: 'crystalab', topic: 'celulas', level: 'introdutorio', format: 'guided', pool: ['Po', 'Fe', 'Cu', 'Mg'],
    title: { 'pt-BR': 'Átomos por célula unitária', en: 'Atoms per unit cell', es: 'Átomos por celda unitaria' },
    objective: { 'pt-BR': 'Contar a contribuição de vértices, faces, centro e interior para obter n.', en: 'Count the contribution of corners, faces, centre and interior to obtain n.', es: 'Contar la contribución de vértices, caras, centro e interior para obtener n.' },
    instructions: { 'pt-BR': 'Observe a célula no laboratório e informe quantos átomos equivalentes ela contém.', en: 'Look at the cell in the lab and enter how many equivalent atoms it contains.', es: 'Observe la celda en el laboratorio e indique cuántos átomos equivalentes contiene.' },
    criteria: [{ id: 'n', text: { 'pt-BR': 'n exato', en: 'exact n', es: 'n exacto' }, tolerance: 0 }],
    explanation: { 'pt-BR': 'Um átomo de vértice é compartilhado por 8 células cúbicas (1/8); de face, por 2 (1/2); o do centro pertence só à célula. No prisma hexagonal, cada vértice vale 1/6.', en: 'A corner atom is shared by 8 cubic cells (1/8); a face atom by 2 (1/2); the centre atom belongs only to the cell. In the hexagonal prism each corner counts 1/6.', es: 'Un átomo de vértice se comparte entre 8 celdas cúbicas (1/8); de cara, entre 2 (1/2); el del centro pertenece solo a la celda. En el prisma hexagonal cada vértice vale 1/6.' },
    references: ['CAL9 §3.4, p. 48–54'], validation: 'catalog-only',
  },
  {
    id: 'fea', module: 'crystalab', topic: 'fea', level: 'intermediario', format: 'guided', pool: ['Po', 'Fe', 'Cu'],
    title: { 'pt-BR': 'Fator de empacotamento atômico', en: 'Atomic packing factor', es: 'Factor de empaquetamiento atómico' },
    objective: { 'pt-BR': 'Relacionar n, R e a para obter o FEA de uma estrutura cúbica.', en: 'Relate n, R and a to obtain the APF of a cubic structure.', es: 'Relacionar n, R y a para obtener el FEA de una estructura cúbica.' },
    instructions: { 'pt-BR': 'O motor não fornece os passos intermediários do FEA (D-12): só a sua resposta final é comparada.', en: 'The engine does not provide intermediate APF steps (D-12): only your final answer is compared.', es: 'El motor no proporciona pasos intermedios del FEA (D-12): solo se compara su respuesta final.' },
    criteria: [{ id: 'fea', text: { 'pt-BR': 'FEA com desvio ≤ 1 %', en: 'APF within 1 %', es: 'FEA con desvío ≤ 1 %' }, tolerance: 0.01 }],
    explanation: { 'pt-BR': 'FEA = volume dos átomos na célula / volume da célula = n·(4/3)πR³ / Vc.', en: 'APF = volume of atoms in the cell / cell volume = n·(4/3)πR³ / Vc.', es: 'FEA = volumen de los átomos en la celda / volumen de la celda = n·(4/3)πR³ / Vc.' },
    references: ['CAL9 §3.4, p. 48–54'], validation: 'catalog-only',
  },
  {
    id: 'plano-miller', module: 'crystalab', topic: 'miller-planos', level: 'introdutorio', format: 'guided', pool: ['Cu', 'Fe'],
    title: { 'pt-BR': 'Identificar um plano de Miller', en: 'Identify a Miller plane', es: 'Identificar un plano de Miller' },
    objective: { 'pt-BR': 'Ler as interseções de um plano desenhado e escrever seus índices (hkl).', en: 'Read the intercepts of a drawn plane and write its (hkl) indices.', es: 'Leer las intersecciones de un plano dibujado y escribir sus índices (hkl).' },
    instructions: { 'pt-BR': 'O motor desenha um plano sorteado. Informe h, k e l (use negativos se necessário).', en: 'The engine draws a random plane. Enter h, k and l (use negatives if needed).', es: 'El motor dibuja un plano sorteado. Indique h, k y l (use negativos si es necesario).' },
    criteria: [{ id: 'hkl', text: { 'pt-BR': 'Índices equivalentes aos do motor', en: 'Indices matching the engine', es: 'Índices equivalentes a los del motor' } }],
    explanation: { 'pt-BR': 'Os índices de Miller são os inversos das interseções com os eixos, reduzidos a inteiros; um plano paralelo a um eixo tem índice 0 nesse eixo.', en: 'Miller indices are the reciprocals of the axis intercepts, reduced to integers; a plane parallel to an axis has index 0 for that axis.', es: 'Los índices de Miller son los inversos de las intersecciones con los ejes, reducidos a enteros; un plano paralelo a un eje tiene índice 0 en ese eje.' },
    references: ['CAL9 §3.8–3.10, p. 58–74'], validation: 'catalog-only',
  },
  {
    id: 'direcao-miller', module: 'crystalab', topic: 'miller-direcoes', level: 'introdutorio', format: 'guided', pool: ['Cu', 'Fe'],
    title: { 'pt-BR': 'Identificar uma direção cristalográfica', en: 'Identify a crystallographic direction', es: 'Identificar una dirección cristalográfica' },
    objective: { 'pt-BR': 'Escrever [uvw] a partir do vetor desenhado.', en: 'Write [uvw] from the drawn vector.', es: 'Escribir [uvw] a partir del vector dibujado.' },
    instructions: { 'pt-BR': 'Subtraia as coordenadas da cauda das da ponta e reduza aos menores inteiros.', en: 'Subtract tail coordinates from head coordinates and reduce to the smallest integers.', es: 'Reste las coordenadas de la cola de las de la punta y reduzca a los menores enteros.' },
    criteria: [{ id: 'uvw', text: { 'pt-BR': 'Índices iguais aos do motor', en: 'Indices matching the engine', es: 'Índices iguales a los del motor' } }],
    explanation: { 'pt-BR': 'Uma direção [uvw] é o vetor da cauda à ponta, em unidades dos parâmetros de rede, reduzido a inteiros.', en: 'A direction [uvw] is the tail-to-head vector in units of the lattice parameters, reduced to integers.', es: 'Una dirección [uvw] es el vector de la cola a la punta, en unidades de los parámetros de red, reducido a enteros.' },
    references: ['CAL9 §3.8–3.10, p. 58–74'], validation: 'catalog-only',
  },
  {
    id: 'abp-al-cu', module: 'crystalab', topic: 'densidade', level: 'intermediario', format: 'pbl', pool: [],
    title: { 'pt-BR': 'ABP: por que o alumínio é tão mais leve que o cobre?', en: 'PBL: why is aluminium so much lighter than copper?', es: 'ABP: ¿por qué el aluminio es mucho más liviano que el cobre?' },
    objective: { 'pt-BR': 'Explicar a diferença de densidade entre dois metais CFC usando evidências do laboratório.', en: 'Explain the density difference between two FCC metals using lab evidence.', es: 'Explicar la diferencia de densidad entre dos metales FCC usando evidencias del laboratorio.' },
    instructions: { 'pt-BR': 'Formule hipóteses, colete evidências no laboratório e classifique cada uma como observação, cálculo ou interpretação.', en: 'Formulate hypotheses, gather evidence in the lab and classify each as observation, calculation or interpretation.', es: 'Formule hipótesis, recoja evidencias en el laboratorio y clasifique cada una como observación, cálculo o interpretación.' },
    criteria: [
      { id: 'evidence', text: { 'pt-BR': 'Pelo menos uma evidência de cada tipo', en: 'At least one piece of evidence of each type', es: 'Al menos una evidencia de cada tipo' } },
      { id: 'conclusion', text: { 'pt-BR': 'Conclusão que cita n, A e Vc', en: 'Conclusion citing n, A and Vc', es: 'Conclusión que cita n, A y Vc' } },
    ],
    explanation: { 'pt-BR': 'Com a mesma estrutura (mesmo n), a densidade depende da razão A/Vc: a massa atômica do Al é bem menor e seu raio é maior, o que aumenta Vc.', en: 'With the same structure (same n), density depends on A/Vc: Al has a much smaller atomic mass and a larger radius, which increases Vc.', es: 'Con la misma estructura (mismo n), la densidad depende de A/Vc: el Al tiene una masa atómica mucho menor y un radio mayor, lo que aumenta Vc.' },
    references: ['CAL9 §3.5, p. 54', 'CAL9 Tab. 3.1, p. 49'], validation: 'catalog-only',
  },
  {
    id: 'quiz-estruturas', module: 'crystalab', topic: 'estruturas', level: 'introdutorio', format: 'quiz', pool: [],
    title: { 'pt-BR': 'Quiz e flashcards: estruturas cristalinas', en: 'Quiz and flashcards: crystal structures', es: 'Quiz y tarjetas: estructuras cristalinas' },
    objective: { 'pt-BR': 'Revisar n, NC, FEA, relações a–R, empilhamento e notação de Miller-Bravais.', en: 'Review n, CN, APF, a–R relations, stacking and Miller-Bravais notation.', es: 'Repasar n, NC, FEA, relaciones a–R, apilamiento y notación de Miller-Bravais.' },
    instructions: { 'pt-BR': 'As perguntas numéricas usam as tabelas do motor; a ordem é embaralhada com semente.', en: 'Numeric questions use the engine tables; the order is shuffled with a seed.', es: 'Las preguntas numéricas usan las tablas del motor; el orden se baraja con semilla.' },
    criteria: [{ id: 'score', text: { 'pt-BR': 'Acertos registrados por tópico', en: 'Correct answers recorded per topic', es: 'Aciertos registrados por tema' } }],
    explanation: { 'pt-BR': 'Revisão de conceitos do Capítulo 3.', en: 'Review of Chapter 3 concepts.', es: 'Repaso de conceptos del Capítulo 3.' },
    references: ['CAL9 Cap. 3, p. 48–75', 'ASK6 Cap. 3, p. 60–96'], validation: 'catalog-only',
  },
  {
    id: 'hea-mapa', module: 'hea', topic: 'hea-parametros', level: 'intermediario', format: 'quiz', pool: [], requiresHea: true,
    title: { 'pt-BR': 'HEA: ler o mapa de estabilidade', en: 'HEA: reading the stability map', es: 'HEA: leer el mapa de estabilidad' },
    objective: { 'pt-BR': 'Localizar uma liga no mapa δ × ΔH a partir do resultado do preditor.', en: 'Place an alloy on the δ × ΔH map from the predictor result.', es: 'Ubicar una aleación en el mapa δ × ΔH a partir del resultado del predictor.' },
    instructions: { 'pt-BR': 'Usa somente valores que o preditor retornou para a liga selecionada no módulo HEA.', en: 'Uses only values the predictor returned for the alloy selected in the HEA module.', es: 'Usa solo valores que el predictor devolvió para la aleación seleccionada en el módulo HEA.' },
    criteria: [{ id: 'zone', text: { 'pt-BR': 'Classificação correta em relação aos limites do mapa', en: 'Correct classification against the map limits', es: 'Clasificación correcta respecto a los límites del mapa' } }],
    explanation: { 'pt-BR': 'O mapa do HEA Virtual Lab marca a zona estável em δ < 6,6 % e −15 < ΔH < 5 kJ/mol (critério de Zhang usado na v1.17).', en: 'The HEA Virtual Lab map marks the stable zone at δ < 6.6 % and −15 < ΔH < 5 kJ/mol (Zhang criterion used in v1.17).', es: 'El mapa del HEA Virtual Lab marca la zona estable en δ < 6,6 % y −15 < ΔH < 5 kJ/mol (criterio de Zhang usado en la v1.17).' },
    references: ['HEA Virtual Lab v1.17 (mapa de estabilidade)'], validation: 'awaiting-specialist',
  },
];

export function activityById(id: string): Activity | undefined {
  return ACTIVITIES.find((a) => a.id === id);
}
