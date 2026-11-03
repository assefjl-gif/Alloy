/**
 * Registro de dependências pendentes exibido no app (Configurações → Pendências).
 * Espelha docs/etapa-1/registro-dependencias.md. Cada recurso desativado ou demonstrativo
 * aponta para um destes ids, para que a interface diga POR QUE algo não está disponível.
 */
import type { Localized } from '../../i18n/index.ts';

export type PendingId =
  | 'D-01' | 'D-02' | 'D-03' | 'D-04' | 'D-05' | 'D-06' | 'D-07' | 'D-08' | 'D-09' | 'D-10'
  | 'D-11' | 'D-12' | 'D-13' | 'D-14' | 'D-15' | 'D-16' | 'D-17' | 'D-18' | 'D-19' | 'D-20';

export interface PendingItem {
  id: PendingId;
  owner: 'hea' | 'crystalab' | 'platform' | 'specialist' | 'team' | 'qa';
  title: Localized;
  behavior: Localized;
}

export const PENDING: PendingItem[] = [
  { id: 'D-01', owner: 'hea',
    title: { 'pt-BR': 'Motor HEA (hea_engine) ausente', en: 'HEA engine (hea_engine) missing', es: 'Motor HEA (hea_engine) ausente' },
    behavior: { 'pt-BR': 'Módulo HEA em modo demonstrativo com valores fictícios de semente fixa; usa o motor real quando ele responder.', en: 'HEA module runs in demo mode with fixed-seed fictitious values; switches to the real engine when it responds.', es: 'Módulo HEA en modo demostrativo con valores ficticios de semilla fija; usa el motor real cuando responda.' } },
  { id: 'D-02', owner: 'hea',
    title: { 'pt-BR': 'Estrutura sugerida no resultado HEA', en: 'Suggested structure in HEA result', es: 'Estructura sugerida en el resultado HEA' },
    behavior: { 'pt-BR': 'Estrutura única citada na fase → abertura direta; senão, escolha explícita do usuário.', en: 'A single structure named in the phase → opens directly; otherwise the user chooses explicitly.', es: 'Una única estructura en la fase → apertura directa; si no, elección explícita del usuario.' } },
  { id: 'D-03', owner: 'platform',
    title: { 'pt-BR': 'Turmas, tarefas e avaliações', en: 'Classes, assignments and assessments', es: 'Grupos, tareas y evaluaciones' },
    behavior: { 'pt-BR': 'Rascunhos locais; nada é publicado sem confirmação do serviço.', en: 'Local drafts; nothing is published without service confirmation.', es: 'Borradores locales; nada se publica sin confirmación del servicio.' } },
  { id: 'D-04', owner: 'platform',
    title: { 'pt-BR': 'Workspaces no servidor', en: 'Server-side workspaces', es: 'Espacios de trabajo en el servidor' },
    behavior: { 'pt-BR': 'Armazenamento local rotulado + exportar/importar JSON.', en: 'Labelled local storage + JSON export/import.', es: 'Almacenamiento local etiquetado + exportar/importar JSON.' } },
  { id: 'D-05', owner: 'crystalab',
    title: { 'pt-BR': 'Exportação CIF/XYZ no servidor stdlib', en: 'CIF/XYZ export on the stdlib server', es: 'Exportación CIF/XYZ en el servidor stdlib' },
    behavior: { 'pt-BR': 'Habilitada só quando /v1/export responde.', en: 'Enabled only when /v1/export responds.', es: 'Habilitada solo cuando /v1/export responde.' } },
  { id: 'D-06', owner: 'crystalab',
    title: { 'pt-BR': 'PDF gerado pelo motor', en: 'Engine-generated PDF', es: 'PDF generado por el motor' },
    behavior: { 'pt-BR': 'PDF pela impressão do navegador.', en: 'PDF through the browser print dialog.', es: 'PDF mediante la impresión del navegador.' } },
  { id: 'D-07', owner: 'crystalab',
    title: { 'pt-BR': 'Parâmetros térmicos (expansão)', en: 'Thermal parameters (expansion)', es: 'Parámetros térmicos (expansión)' },
    behavior: { 'pt-BR': 'Animação de expansão térmica apenas ilustrativa, sem números.', en: 'Thermal expansion animation is illustrative only, without numbers.', es: 'Animación de expansión térmica solo ilustrativa, sin números.' } },
  { id: 'D-08', owner: 'platform',
    title: { 'pt-BR': 'Serviço de IA generativa', en: 'Generative AI service', es: 'Servicio de IA generativa' },
    behavior: { 'pt-BR': 'Assistente desativado e identificado.', en: 'Assistant disabled and labelled.', es: 'Asistente desactivado e identificado.' } },
  { id: 'D-09', owner: 'crystalab',
    title: { 'pt-BR': 'Coordenadas fracionárias da HC', en: 'HCP fractional coordinates', es: 'Coordenadas fraccionarias de la HC' },
    behavior: { 'pt-BR': 'Exibidas só se o motor enviar o campo base (v1.1.0).', en: 'Shown only if the engine sends the base field (v1.1.0).', es: 'Se muestran solo si el motor envía el campo base (v1.1.0).' } },
  { id: 'D-10', owner: 'crystalab',
    title: { 'pt-BR': 'Vetores de rede na resposta', en: 'Lattice vectors in the response', es: 'Vectores de red en la respuesta' },
    behavior: { 'pt-BR': 'Supercélula usa convenção de desenho documentada.', en: 'Supercell uses a documented drawing convention.', es: 'La supercelda usa una convención de dibujo documentada.' } },
  { id: 'D-11', owner: 'crystalab',
    title: { 'pt-BR': 'Poliedros de coordenação e famílias de planos', en: 'Coordination polyhedra and plane families', es: 'Poliedros de coordinación y familias de planos' },
    behavior: { 'pt-BR': 'Opções desativadas com explicação.', en: 'Options disabled with an explanation.', es: 'Opciones desactivadas con explicación.' } },
  { id: 'D-12', owner: 'crystalab',
    title: { 'pt-BR': 'Passos intermediários do FEA', en: 'Intermediate APF steps', es: 'Pasos intermedios del FEA' },
    behavior: { 'pt-BR': 'Só a fórmula simbólica; valores intermediários não são inventados.', en: 'Symbolic formula only; intermediate values are not invented.', es: 'Solo la fórmula simbólica; no se inventan valores intermedios.' } },
  { id: 'D-13', owner: 'crystalab',
    title: { 'pt-BR': 'Camadas compactas A/B/C', en: 'Close-packed A/B/C layers', es: 'Capas compactas A/B/C' },
    behavior: { 'pt-BR': 'Animação de empilhamento esquemática, rotulada como ilustração.', en: 'Schematic stacking animation, labelled as illustration.', es: 'Animación de apilamiento esquemática, etiquetada como ilustración.' } },
  { id: 'D-14', owner: 'team',
    title: { 'pt-BR': 'Código da v1.1.0 fora do projeto', en: 'v1.1.0 code not in the project', es: 'Código de la v1.1.0 fuera del proyecto' },
    behavior: { 'pt-BR': 'Front aceita os campos aditivos da v1.1.0; testado contra a v1.0.', en: 'The front accepts v1.1.0 additive fields; tested against v1.0.', es: 'El front acepta los campos aditivos de la v1.1.0; probado contra la v1.0.' } },
  { id: 'D-15', owner: 'crystalab',
    title: { 'pt-BR': 'Contrato OpenAPI executável', en: 'Runnable OpenAPI contract', es: 'Contrato OpenAPI ejecutable' },
    behavior: { 'pt-BR': 'Contratos TypeScript manuais validados com zod.', en: 'Hand-written TypeScript contracts validated with zod.', es: 'Contratos TypeScript manuales validados con zod.' } },
  { id: 'D-16', owner: 'specialist',
    title: { 'pt-BR': 'Dados sem fonte (Po) e desvio do Ti', en: 'Unsourced data (Po) and Ti deviation', es: 'Datos sin fuente (Po) y desviación del Ti' },
    behavior: { 'pt-BR': 'Avisos do motor exibidos; o front não corrige valores.', en: 'Engine warnings are shown; the front never corrects values.', es: 'Se muestran avisos del motor; el front no corrige valores.' } },
  { id: 'D-17', owner: 'specialist',
    title: { 'pt-BR': 'Faixas validadas para exercícios', en: 'Validated ranges for exercises', es: 'Rangos validados para ejercicios' },
    behavior: { 'pt-BR': 'Exercícios usam só materiais do catálogo do motor.', en: 'Exercises use only engine catalogue materials.', es: 'Los ejercicios usan solo materiales del catálogo del motor.' } },
  { id: 'D-18', owner: 'platform',
    title: { 'pt-BR': 'Sincronização de notas offline', en: 'Offline note sync', es: 'Sincronización de notas sin conexión' },
    behavior: { 'pt-BR': 'Notas ficam neste navegador, com aviso ao reconectar.', en: 'Notes stay in this browser, with a notice on reconnect.', es: 'Las notas quedan en este navegador, con aviso al reconectar.' } },
  { id: 'D-19', owner: 'team',
    title: { 'pt-BR': 'Vite, ESLint, axe-core e Lighthouse indisponíveis no ambiente de build', en: 'Vite, ESLint, axe-core and Lighthouse unavailable in the build environment', es: 'Vite, ESLint, axe-core y Lighthouse no disponibles en el entorno de build' },
    behavior: { 'pt-BR': 'esbuild, lint próprio e auditoria de acessibilidade própria.', en: 'esbuild, project lint and in-house accessibility audit.', es: 'esbuild, lint propio y auditoría de accesibilidad propia.' } },
  { id: 'D-20', owner: 'qa',
    title: { 'pt-BR': 'Medição no equipamento-alvo', en: 'Measurement on target hardware', es: 'Medición en el equipo objetivo' },
    behavior: { 'pt-BR': 'Medido só em contêiner headless; metas não declaradas atingidas.', en: 'Measured only in a headless container; targets not declared met.', es: 'Medido solo en contenedor headless; metas no declaradas alcanzadas.' } },
];

export function pendingById(id: PendingId): PendingItem {
  const item = PENDING.find((p) => p.id === id);
  if (!item) throw new Error(`pendência desconhecida: ${id}`);
  return item;
}
