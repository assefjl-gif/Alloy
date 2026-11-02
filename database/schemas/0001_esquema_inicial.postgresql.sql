BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE elementos (
    simbolo VARCHAR(3) NOT NULL, 
    nome VARCHAR(60) NOT NULL, 
    numero_atomico INTEGER, 
    CONSTRAINT pk_elementos PRIMARY KEY (simbolo), 
    CONSTRAINT uq_elementos_numero_atomico UNIQUE (numero_atomico)
);

CREATE TABLE estruturas (
    codigo VARCHAR(4) NOT NULL, 
    nome VARCHAR(60) NOT NULL, 
    grupo_espacial_hm VARCHAR(20) NOT NULL, 
    grupo_espacial_numero INTEGER NOT NULL, 
    wyckoff VARCHAR(4) NOT NULL, 
    n INTEGER NOT NULL, 
    nc INTEGER NOT NULL, 
    CONSTRAINT pk_estruturas PRIMARY KEY (codigo)
);

CREATE TABLE instituicoes (
    nome VARCHAR(200) NOT NULL, 
    sigla VARCHAR(30), 
    configuracoes JSONB NOT NULL, 
    arquivado_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_instituicoes PRIMARY KEY (id)
);

CREATE TABLE motores (
    codigo VARCHAR(30) NOT NULL, 
    versao VARCHAR(20) NOT NULL, 
    descricao TEXT, 
    ativo BOOLEAN NOT NULL, 
    CONSTRAINT pk_motores PRIMARY KEY (codigo, versao)
);

CREATE TABLE propriedades (
    codigo VARCHAR(40) NOT NULL, 
    nome VARCHAR(100) NOT NULL, 
    grupo VARCHAR(20) NOT NULL, 
    unidade_si VARCHAR(30) NOT NULL, 
    unidade_exibicao VARCHAR(30) NOT NULL, 
    CONSTRAINT pk_propriedades PRIMARY KEY (codigo), 
    CONSTRAINT ck_propriedades_grupo CHECK (grupo IN ('fisica', 'mecanica', 'termica', 'cristalografica', 'quimica'))
);

CREATE TABLE usuarios (
    nome VARCHAR(120) NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    senha_hash TEXT, 
    email_verificado_em TIMESTAMP WITH TIME ZONE, 
    admin_geral BOOLEAN NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    ultimo_acesso_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_usuarios PRIMARY KEY (id), 
    CONSTRAINT ck_usuarios_status CHECK (status IN ('ativo', 'bloqueado', 'pendente', 'anonimizado')), 
    CONSTRAINT ck_usuarios_email_minusculo CHECK (email = lower(email)), 
    CONSTRAINT uq_usuarios_email UNIQUE (email)
);

CREATE TABLE arquivos (
    sha256 BYTEA NOT NULL, 
    nome_original VARCHAR(160) NOT NULL, 
    tipo_mime VARCHAR(120) NOT NULL, 
    extensao VARCHAR(5) NOT NULL, 
    tamanho_bytes BIGINT NOT NULL, 
    categoria VARCHAR(20) NOT NULL, 
    dono_id UUID NOT NULL, 
    instituicao_id UUID NOT NULL, 
    visibilidade VARCHAR(15) NOT NULL, 
    arquivado_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_arquivos PRIMARY KEY (id), 
    CONSTRAINT ck_arquivos_categoria CHECK (categoria IN ('tutorial', 'anexo_atividade', 'anexo_nota')), 
    CONSTRAINT ck_arquivos_extensao CHECK (extensao IN ('txt', 'md', 'mp4', 'webm', 'pdf', 'csv', 'xlsx', 'xls', 'ods', 'docx', 'doc', 'odt')), 
    CONSTRAINT ck_arquivos_tamanho CHECK (tamanho_bytes >= 0), 
    CONSTRAINT fk_arquivos_dono_id_usuarios FOREIGN KEY(dono_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_arquivos_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT
);

CREATE INDEX ix_arquivos_biblioteca ON arquivos (instituicao_id, categoria);

CREATE TABLE atividades (
    instituicao_id UUID NOT NULL, 
    autor_id UUID NOT NULL, 
    titulo VARCHAR(200) NOT NULL, 
    tipo VARCHAR(15) NOT NULL, 
    descricao TEXT, 
    materiais_ids JSONB NOT NULL, 
    estado VARCHAR(15) NOT NULL, 
    versao INTEGER NOT NULL, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_atividades PRIMARY KEY (id), 
    CONSTRAINT ck_atividades_estado CHECK (estado IN ('rascunho', 'publicada', 'arquivada')), 
    CONSTRAINT ck_atividades_tipo CHECK (tipo IN ('exercicio', 'abp', 'quiz', 'simulacao')), 
    CONSTRAINT fk_atividades_autor_id_usuarios FOREIGN KEY(autor_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_atividades_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT
);

CREATE TABLE auditoria (
    id BIGSERIAL NOT NULL, 
    ator_id UUID, 
    acao VARCHAR(60) NOT NULL, 
    entidade VARCHAR(40) NOT NULL, 
    entidade_id VARCHAR(60), 
    antes JSONB, 
    depois JSONB, 
    request_id VARCHAR(64), 
    ip VARCHAR(45), 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_auditoria PRIMARY KEY (id), 
    CONSTRAINT fk_auditoria_ator_id_usuarios FOREIGN KEY(ator_id) REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE TABLE caderno_notas (
    usuario_id UUID NOT NULL, 
    titulo VARCHAR(200) NOT NULL, 
    conteudo TEXT NOT NULL, 
    cena JSONB, 
    atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    versao INTEGER NOT NULL, 
    id UUID NOT NULL, 
    CONSTRAINT pk_caderno_notas PRIMARY KEY (id), 
    CONSTRAINT fk_caderno_notas_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_caderno_notas_usuario_id ON caderno_notas (usuario_id);

CREATE TABLE consentimentos (
    usuario_id UUID NOT NULL, 
    finalidade VARCHAR(60) NOT NULL, 
    versao_texto VARCHAR(20) NOT NULL, 
    concedido_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    revogado_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    CONSTRAINT pk_consentimentos PRIMARY KEY (id), 
    CONSTRAINT fk_consentimentos_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE cursos (
    instituicao_id UUID NOT NULL, 
    nome VARCHAR(200) NOT NULL, 
    codigo VARCHAR(30) NOT NULL, 
    id UUID NOT NULL, 
    CONSTRAINT pk_cursos PRIMARY KEY (id), 
    CONSTRAINT fk_cursos_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_curso_codigo UNIQUE (instituicao_id, codigo)
);

CREATE TABLE fontes (
    id VARCHAR(60) NOT NULL, 
    tipo VARCHAR(20) NOT NULL, 
    citacao TEXT NOT NULL, 
    doi VARCHAR(200), 
    url TEXT, 
    edicao_pagina VARCHAR(120), 
    licenca VARCHAR(120), 
    observacao TEXT, 
    conferida_por UUID, 
    conferida_em TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT pk_fontes PRIMARY KEY (id), 
    CONSTRAINT ck_fontes_tipo CHECK (tipo IN ('livro', 'artigo', 'norma', 'base_dados', 'relatorio', 'outro')), 
    CONSTRAINT fk_fontes_conferida_por_usuarios FOREIGN KEY(conferida_por) REFERENCES usuarios (id) ON DELETE RESTRICT
);

CREATE TABLE materiais (
    tipo VARCHAR(20) NOT NULL, 
    nome VARCHAR(200) NOT NULL, 
    elemento_simbolo VARCHAR(3), 
    aliases JSONB NOT NULL, 
    estado VARCHAR(25) NOT NULL, 
    visibilidade VARCHAR(15) NOT NULL, 
    instituicao_id UUID, 
    origem VARCHAR(20) NOT NULL, 
    criado_por UUID, 
    atualizado_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_materiais PRIMARY KEY (id), 
    CONSTRAINT ck_materiais_estado CHECK (estado IN ('rascunho', 'aguardando_validacao', 'validado', 'rejeitado', 'arquivado')), 
    CONSTRAINT ck_materiais_origem CHECK (origem IN ('curado', 'contribuicao', 'demonstrativo')), 
    CONSTRAINT ck_materiais_tipo CHECK (tipo IN ('elemento_puro', 'liga', 'hea', 'composto', 'intersticial')), 
    CONSTRAINT ck_materiais_elemento_obrigatorio CHECK (tipo NOT IN ('elemento_puro', 'intersticial') OR elemento_simbolo IS NOT NULL), 
    CONSTRAINT ck_materiais_escopo_instituicao CHECK (visibilidade = 'publico' OR instituicao_id IS NOT NULL), 
    CONSTRAINT ck_materiais_visibilidade CHECK (visibilidade IN ('publico', 'instituicao', 'privado')), 
    CONSTRAINT fk_materiais_criado_por_usuarios FOREIGN KEY(criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_materiais_elemento_simbolo_elementos FOREIGN KEY(elemento_simbolo) REFERENCES elementos (simbolo) ON DELETE RESTRICT, 
    CONSTRAINT fk_materiais_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT
);

CREATE INDEX ix_materiais_catalogo ON materiais (estado, visibilidade, tipo);

CREATE UNIQUE INDEX uq_materiais_elemento_puro ON materiais (elemento_simbolo) WHERE tipo IN ('elemento_puro', 'intersticial');

CREATE TABLE preferencias_usuario (
    usuario_id UUID NOT NULL, 
    tema VARCHAR(10), 
    idioma VARCHAR(10), 
    cores_elementos JSONB NOT NULL, 
    atualizado_em TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT pk_preferencias_usuario PRIMARY KEY (usuario_id), 
    CONSTRAINT fk_preferencias_usuario_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE questoes (
    instituicao_id UUID, 
    autor_id UUID NOT NULL, 
    versao INTEGER NOT NULL, 
    tipo VARCHAR(20) NOT NULL, 
    titulo VARCHAR(120) NOT NULL, 
    enunciado TEXT NOT NULL, 
    pergunta_publica JSONB NOT NULL, 
    gabarito JSONB NOT NULL, 
    parametros JSONB, 
    politica JSONB NOT NULL, 
    resolucao JSONB, 
    dicas JSONB NOT NULL, 
    topicos JSONB NOT NULL, 
    dificuldade INTEGER NOT NULL, 
    publicada BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_questoes PRIMARY KEY (id), 
    CONSTRAINT ck_questoes_tipo CHECK (tipo IN ('numerico', 'multipla_escolha', 'verdadeiro_falso', 'miller', 'texto_curto', 'tabela_numerica')), 
    CONSTRAINT ck_questoes_dificuldade CHECK (dificuldade BETWEEN 1 AND 5), 
    CONSTRAINT fk_questoes_autor_id_usuarios FOREIGN KEY(autor_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_questoes_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT
);

CREATE TABLE revisoes_validacao (
    entidade VARCHAR(30) NOT NULL, 
    entidade_id UUID NOT NULL, 
    de_estado VARCHAR(25) NOT NULL, 
    para_estado VARCHAR(25) NOT NULL, 
    revisor_id UUID NOT NULL, 
    comentario TEXT, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_revisoes_validacao PRIMARY KEY (id), 
    CONSTRAINT fk_revisoes_validacao_revisor_id_usuarios FOREIGN KEY(revisor_id) REFERENCES usuarios (id) ON DELETE RESTRICT
);

CREATE TABLE sessoes (
    usuario_id UUID NOT NULL, 
    token_sha256 BYTEA NOT NULL, 
    csrf_sha256 BYTEA NOT NULL, 
    criada_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    ultimo_uso_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    expira_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    revogada_em TIMESTAMP WITH TIME ZONE, 
    ip_criacao VARCHAR(45), 
    agente_usuario VARCHAR(200), 
    id UUID NOT NULL, 
    CONSTRAINT pk_sessoes PRIMARY KEY (id), 
    CONSTRAINT fk_sessoes_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE, 
    CONSTRAINT uq_sessoes_token_sha256 UNIQUE (token_sha256)
);

CREATE INDEX ix_sessoes_usuario_ativas ON sessoes (usuario_id, revogada_em);

CREATE TABLE tokens_uso_unico (
    usuario_id UUID NOT NULL, 
    finalidade VARCHAR(30) NOT NULL, 
    token_sha256 BYTEA NOT NULL, 
    expira_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    usado_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    CONSTRAINT pk_tokens_uso_unico PRIMARY KEY (id), 
    CONSTRAINT ck_tokens_uso_unico_finalidade CHECK (finalidade IN ('verificar_email', 'redefinir_senha')), 
    CONSTRAINT fk_tokens_uso_unico_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE, 
    CONSTRAINT uq_tokens_uso_unico_token_sha256 UNIQUE (token_sha256)
);

CREATE TABLE vinculos_institucionais (
    usuario_id UUID NOT NULL, 
    instituicao_id UUID NOT NULL, 
    papel VARCHAR(30) NOT NULL, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_vinculos_institucionais PRIMARY KEY (id), 
    CONSTRAINT ck_vinculos_institucionais_papel CHECK (papel IN ('admin_institucional', 'professor', 'estudante', 'pesquisador')), 
    CONSTRAINT fk_vinculos_institucionais_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_vinculos_institucionais_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_vinculo UNIQUE (usuario_id, instituicao_id, papel)
);

CREATE TABLE atividade_questoes (
    atividade_id UUID NOT NULL, 
    questao_id UUID NOT NULL, 
    ordem INTEGER NOT NULL, 
    peso NUMERIC NOT NULL, 
    CONSTRAINT pk_atividade_questoes PRIMARY KEY (atividade_id, questao_id), 
    CONSTRAINT fk_atividade_questoes_atividade_id_atividades FOREIGN KEY(atividade_id) REFERENCES atividades (id) ON DELETE CASCADE, 
    CONSTRAINT fk_atividade_questoes_questao_id_questoes FOREIGN KEY(questao_id) REFERENCES questoes (id) ON DELETE RESTRICT
);

CREATE TABLE composicoes (
    material_id UUID NOT NULL, 
    versao INTEGER NOT NULL, 
    base VARCHAR(10) NOT NULL, 
    tolerancia_soma NUMERIC NOT NULL, 
    vigente BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_composicoes PRIMARY KEY (id), 
    CONSTRAINT ck_composicoes_base CHECK (base IN ('atomica', 'massa')), 
    CONSTRAINT fk_composicoes_material_id_materiais FOREIGN KEY(material_id) REFERENCES materiais (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_composicao_versao UNIQUE (material_id, versao)
);

CREATE TABLE entalpias_pares (
    elemento_a VARCHAR(3) NOT NULL, 
    elemento_b VARCHAR(3) NOT NULL, 
    fonte_id VARCHAR(60) NOT NULL, 
    dh_mix_kj_mol NUMERIC NOT NULL, 
    modelo VARCHAR(40), 
    CONSTRAINT pk_entalpias_pares PRIMARY KEY (elemento_a, elemento_b, fonte_id), 
    CONSTRAINT ck_entalpias_pares_par_ordenado CHECK (elemento_a < elemento_b), 
    CONSTRAINT fk_entalpias_pares_elemento_a_elementos FOREIGN KEY(elemento_a) REFERENCES elementos (simbolo) ON DELETE RESTRICT, 
    CONSTRAINT fk_entalpias_pares_elemento_b_elementos FOREIGN KEY(elemento_b) REFERENCES elementos (simbolo) ON DELETE RESTRICT, 
    CONSTRAINT fk_entalpias_pares_fonte_id_fontes FOREIGN KEY(fonte_id) REFERENCES fontes (id) ON DELETE RESTRICT
);

CREATE TABLE execucoes_calculo (
    usuario_id UUID, 
    instituicao_id UUID, 
    motor_codigo VARCHAR(30) NOT NULL, 
    motor_versao VARCHAR(20) NOT NULL, 
    versao_dados VARCHAR(60) NOT NULL, 
    operacao VARCHAR(30) NOT NULL, 
    parametros JSONB NOT NULL, 
    parametros_sha256 BYTEA NOT NULL, 
    resultado JSONB, 
    classe_resultado VARCHAR(25) NOT NULL, 
    status VARCHAR(15) NOT NULL, 
    erro TEXT, 
    duracao_ms NUMERIC, 
    material_id UUID, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_execucoes_calculo PRIMARY KEY (id), 
    CONSTRAINT ck_execucoes_calculo_classe CHECK (classe_resultado IN ('analitico', 'estimativa_modelo', 'experimental', 'simulacao_ilustrativa', 'demonstrativo')), 
    CONSTRAINT ck_execucoes_calculo_status CHECK (status IN ('pendente', 'em_execucao', 'concluido', 'falhou')), 
    CONSTRAINT fk_execucoes_calculo_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_execucoes_calculo_material_id_materiais FOREIGN KEY(material_id) REFERENCES materiais (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_execucoes_calculo_motor FOREIGN KEY(motor_codigo, motor_versao) REFERENCES motores (codigo, versao) ON DELETE RESTRICT, 
    CONSTRAINT fk_execucoes_calculo_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE INDEX ix_execucoes_calculo_parametros_sha256 ON execucoes_calculo (parametros_sha256);

CREATE INDEX ix_execucoes_usuario_data ON execucoes_calculo (usuario_id, criado_em DESC);

CREATE TABLE materiais_estruturas (
    material_id UUID NOT NULL, 
    estrutura_codigo VARCHAR(4) NOT NULL, 
    fase VARCHAR(20), 
    temperatura_min_c NUMERIC, 
    temperatura_max_c NUMERIC, 
    referencia_ambiente BOOLEAN NOT NULL, 
    c_a NUMERIC, 
    a_nm NUMERIC, 
    c_nm NUMERIC, 
    fonte_id VARCHAR(60), 
    fonte_rede_id VARCHAR(60), 
    estado VARCHAR(25) NOT NULL, 
    id UUID NOT NULL, 
    CONSTRAINT pk_materiais_estruturas PRIMARY KEY (id), 
    CONSTRAINT ck_materiais_estruturas_validado_exige_fonte CHECK (estado <> 'validado' OR fonte_id IS NOT NULL), 
    CONSTRAINT ck_materiais_estruturas_estado CHECK (estado IN ('rascunho', 'aguardando_validacao', 'validado', 'rejeitado', 'arquivado')), 
    CONSTRAINT ck_materiais_estruturas_c_exige_a CHECK (c_nm IS NULL OR a_nm IS NOT NULL), 
    CONSTRAINT fk_materiais_estruturas_estrutura_codigo_estruturas FOREIGN KEY(estrutura_codigo) REFERENCES estruturas (codigo) ON DELETE RESTRICT, 
    CONSTRAINT fk_materiais_estruturas_fonte_id_fontes FOREIGN KEY(fonte_id) REFERENCES fontes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_materiais_estruturas_fonte_rede_id_fontes FOREIGN KEY(fonte_rede_id) REFERENCES fontes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_materiais_estruturas_material_id_materiais FOREIGN KEY(material_id) REFERENCES materiais (id) ON DELETE RESTRICT
);

CREATE TABLE processamentos (
    material_id UUID NOT NULL, 
    descricao TEXT NOT NULL, 
    tratamento_termico JSONB, 
    fonte_id VARCHAR(60), 
    id UUID NOT NULL, 
    CONSTRAINT pk_processamentos PRIMARY KEY (id), 
    CONSTRAINT fk_processamentos_fonte_id_fontes FOREIGN KEY(fonte_id) REFERENCES fontes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_processamentos_material_id_materiais FOREIGN KEY(material_id) REFERENCES materiais (id) ON DELETE RESTRICT
);

CREATE TABLE turmas (
    instituicao_id UUID NOT NULL, 
    curso_id UUID, 
    disciplina VARCHAR(200) NOT NULL, 
    periodo VARCHAR(10) NOT NULL, 
    professor_responsavel_id UUID NOT NULL, 
    codigo_convite VARCHAR(16), 
    arquivada_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_turmas PRIMARY KEY (id), 
    CONSTRAINT fk_turmas_curso_id_cursos FOREIGN KEY(curso_id) REFERENCES cursos (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_turmas_instituicao_id_instituicoes FOREIGN KEY(instituicao_id) REFERENCES instituicoes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_turmas_professor_responsavel_id_usuarios FOREIGN KEY(professor_responsavel_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_turmas_codigo_convite UNIQUE (codigo_convite)
);

CREATE INDEX ix_turmas_instituicao_id ON turmas (instituicao_id);

CREATE TABLE valores_propriedade (
    material_id UUID NOT NULL, 
    propriedade_codigo VARCHAR(40) NOT NULL, 
    valor NUMERIC NOT NULL, 
    incerteza NUMERIC, 
    unidade VARCHAR(30) NOT NULL, 
    classe VARCHAR(15) NOT NULL, 
    condicoes JSONB, 
    fonte_id VARCHAR(60), 
    estado VARCHAR(25) NOT NULL, 
    substitui_id UUID, 
    vigente BOOLEAN NOT NULL, 
    origem TEXT, 
    criado_por UUID, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_valores_propriedade PRIMARY KEY (id), 
    CONSTRAINT ck_valores_propriedade_classe CHECK (classe IN ('medido', 'calculado', 'estimado', 'importado', 'demonstrativo')), 
    CONSTRAINT ck_valores_propriedade_validado_exige_fonte CHECK (estado <> 'validado' OR fonte_id IS NOT NULL), 
    CONSTRAINT ck_valores_propriedade_estado CHECK (estado IN ('rascunho', 'aguardando_validacao', 'validado', 'rejeitado', 'arquivado')), 
    CONSTRAINT fk_valores_propriedade_criado_por_usuarios FOREIGN KEY(criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_valores_propriedade_fonte_id_fontes FOREIGN KEY(fonte_id) REFERENCES fontes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_valores_propriedade_material_id_materiais FOREIGN KEY(material_id) REFERENCES materiais (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_valores_propriedade_propriedade_codigo_propriedades FOREIGN KEY(propriedade_codigo) REFERENCES propriedades (codigo) ON DELETE RESTRICT, 
    CONSTRAINT fk_valores_propriedade_substitui_id_valores_propriedade FOREIGN KEY(substitui_id) REFERENCES valores_propriedade (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_valores_vigentes ON valores_propriedade (material_id, propriedade_codigo) WHERE vigente;

CREATE TABLE atribuicoes (
    atividade_id UUID NOT NULL, 
    turma_id UUID NOT NULL, 
    abre_em TIMESTAMP WITH TIME ZONE, 
    fecha_em TIMESTAMP WITH TIME ZONE, 
    criterios JSONB NOT NULL, 
    criado_por UUID NOT NULL, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_atribuicoes PRIMARY KEY (id), 
    CONSTRAINT ck_atribuicoes_prazo CHECK (fecha_em IS NULL OR abre_em IS NULL OR fecha_em > abre_em), 
    CONSTRAINT fk_atribuicoes_atividade_id_atividades FOREIGN KEY(atividade_id) REFERENCES atividades (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_atribuicoes_criado_por_usuarios FOREIGN KEY(criado_por) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_atribuicoes_turma_id_turmas FOREIGN KEY(turma_id) REFERENCES turmas (id) ON DELETE RESTRICT
);

CREATE TABLE composicao_itens (
    composicao_id UUID NOT NULL, 
    elemento_simbolo VARCHAR(3) NOT NULL, 
    fracao NUMERIC NOT NULL, 
    CONSTRAINT pk_composicao_itens PRIMARY KEY (composicao_id, elemento_simbolo), 
    CONSTRAINT ck_composicao_itens_fracao CHECK (fracao > 0 AND fracao <= 1), 
    CONSTRAINT fk_composicao_itens_composicao_id_composicoes FOREIGN KEY(composicao_id) REFERENCES composicoes (id) ON DELETE CASCADE, 
    CONSTRAINT fk_composicao_itens_elemento_simbolo_elementos FOREIGN KEY(elemento_simbolo) REFERENCES elementos (simbolo) ON DELETE RESTRICT
);

CREATE TABLE matriculas (
    turma_id UUID NOT NULL, 
    usuario_id UUID NOT NULL, 
    papel_turma VARCHAR(30) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_matriculas PRIMARY KEY (id), 
    CONSTRAINT ck_matriculas_papel_turma CHECK (papel_turma IN ('estudante', 'monitor', 'professor_assistente')), 
    CONSTRAINT ck_matriculas_status CHECK (status IN ('ativa', 'trancada', 'concluida')), 
    CONSTRAINT fk_matriculas_turma_id_turmas FOREIGN KEY(turma_id) REFERENCES turmas (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_matriculas_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_matricula UNIQUE (turma_id, usuario_id)
);

CREATE INDEX ix_matriculas_usuario_id ON matriculas (usuario_id);

CREATE TABLE entregas (
    atribuicao_id UUID NOT NULL, 
    usuario_id UUID NOT NULL, 
    status VARCHAR(15) NOT NULL, 
    entregue_em TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    CONSTRAINT pk_entregas PRIMARY KEY (id), 
    CONSTRAINT ck_entregas_status CHECK (status IN ('em_andamento', 'entregue', 'avaliada')), 
    CONSTRAINT fk_entregas_atribuicao_id_atribuicoes FOREIGN KEY(atribuicao_id) REFERENCES atribuicoes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_entregas_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_entrega UNIQUE (atribuicao_id, usuario_id)
);

CREATE INDEX ix_entregas_painel ON entregas (atribuicao_id, status);

CREATE TABLE instancias_questao (
    questao_id UUID NOT NULL, 
    questao_versao INTEGER NOT NULL, 
    usuario_id UUID NOT NULL, 
    atribuicao_id UUID, 
    semente BIGINT NOT NULL, 
    parametros_sorteados JSONB NOT NULL, 
    gabarito_calculado JSONB NOT NULL, 
    versao_motor VARCHAR(20), 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_instancias_questao PRIMARY KEY (id), 
    CONSTRAINT fk_instancias_questao_atribuicao_id_atribuicoes FOREIGN KEY(atribuicao_id) REFERENCES atribuicoes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_instancias_questao_questao_id_questoes FOREIGN KEY(questao_id) REFERENCES questoes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_instancias_questao_usuario_id_usuarios FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_instancia UNIQUE (questao_id, usuario_id, atribuicao_id, semente)
);

CREATE TABLE notas (
    entrega_id UUID NOT NULL, 
    valor NUMERIC NOT NULL, 
    lancada_por UUID NOT NULL, 
    lancada_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    comentario TEXT, 
    substitui_id UUID, 
    id UUID NOT NULL, 
    CONSTRAINT pk_notas PRIMARY KEY (id), 
    CONSTRAINT fk_notas_entrega_id_entregas FOREIGN KEY(entrega_id) REFERENCES entregas (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_notas_lancada_por_usuarios FOREIGN KEY(lancada_por) REFERENCES usuarios (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_notas_substitui_id_notas FOREIGN KEY(substitui_id) REFERENCES notas (id) ON DELETE RESTRICT
);

CREATE TABLE tentativas (
    instancia_id UUID NOT NULL, 
    n INTEGER NOT NULL, 
    resposta JSONB NOT NULL, 
    resposta_normalizada JSONB, 
    correta BOOLEAN NOT NULL, 
    pontuacao NUMERIC, 
    tipo_erro VARCHAR(20), 
    tempo_ms INTEGER, 
    dicas_usadas INTEGER NOT NULL, 
    gabarito_visto BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_tentativas PRIMARY KEY (id), 
    CONSTRAINT ck_tentativas_tipo_erro CHECK (tipo_erro IS NULL OR tipo_erro IN ('unidade', 'fator_10n', 'sinal', 'indice_oposto', 'conceitual', 'nao_classificado')), 
    CONSTRAINT ck_tentativas_tempo CHECK (tempo_ms IS NULL OR (tempo_ms >= 0 AND tempo_ms <= 3600000)), 
    CONSTRAINT fk_tentativas_instancia_id_instancias_questao FOREIGN KEY(instancia_id) REFERENCES instancias_questao (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_tentativa_n UNIQUE (instancia_id, n)
);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

