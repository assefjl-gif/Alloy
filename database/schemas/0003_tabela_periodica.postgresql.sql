BEGIN;

-- Running upgrade 0002 -> 0003

CREATE TABLE propriedades_elemento (
    elemento_simbolo VARCHAR(3) NOT NULL, 
    propriedade_codigo VARCHAR(40) NOT NULL, 
    valor NUMERIC NOT NULL, 
    incerteza NUMERIC, 
    intervalo_min NUMERIC, 
    intervalo_max NUMERIC, 
    unidade VARCHAR(30) NOT NULL, 
    classe VARCHAR(15) NOT NULL, 
    fonte_id VARCHAR(60) NOT NULL, 
    estado VARCHAR(25) NOT NULL, 
    conjunto_versao VARCHAR(40) NOT NULL, 
    vigente BOOLEAN NOT NULL, 
    substitui_id UUID, 
    nota TEXT, 
    id UUID NOT NULL, 
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_propriedades_elemento PRIMARY KEY (id), 
    CONSTRAINT ck_propriedades_elemento_classe CHECK (classe IN ('medido', 'calculado', 'estimado', 'importado', 'demonstrativo')), 
    CONSTRAINT ck_propriedades_elemento_estado CHECK (estado IN ('rascunho', 'aguardando_validacao', 'validado', 'rejeitado', 'arquivado')), 
    CONSTRAINT ck_propriedades_elemento_incerteza CHECK (incerteza IS NULL OR incerteza >= 0), 
    CONSTRAINT ck_propriedades_elemento_intervalo CHECK (intervalo_min IS NULL OR intervalo_max IS NULL OR intervalo_min <= intervalo_max), 
    CONSTRAINT fk_propriedades_elemento_elemento_simbolo_elementos FOREIGN KEY(elemento_simbolo) REFERENCES elementos (simbolo) ON DELETE RESTRICT, 
    CONSTRAINT fk_propriedades_elemento_fonte_id_fontes FOREIGN KEY(fonte_id) REFERENCES fontes (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_propriedades_elemento_propriedade_codigo_propriedades FOREIGN KEY(propriedade_codigo) REFERENCES propriedades (codigo) ON DELETE RESTRICT, 
    CONSTRAINT fk_propriedades_elemento_substitui_id_propriedades_elemento FOREIGN KEY(substitui_id) REFERENCES propriedades_elemento (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_propriedades_elemento_vigentes ON propriedades_elemento (elemento_simbolo, propriedade_codigo) WHERE vigente;

ALTER TABLE elementos ADD COLUMN nome_en VARCHAR(40);

ALTER TABLE elementos ADD COLUMN periodo SMALLINT;

ALTER TABLE elementos ADD COLUMN grupo SMALLINT;

ALTER TABLE elementos ADD COLUMN bloco VARCHAR(1);

ALTER TABLE elementos ADD COLUMN categoria VARCHAR(40);

ALTER TABLE elementos ADD COLUMN configuracao_eletronica VARCHAR(60);

ALTER TABLE elementos ADD COLUMN estados_oxidacao VARCHAR(80);

ALTER TABLE elementos ADD COLUMN estado_padrao VARCHAR(20);

ALTER TABLE elementos ADD COLUMN ano_descoberta SMALLINT;

ALTER TABLE elementos ADD COLUMN conhecido_antiguidade BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE elementos ADD CONSTRAINT ck_elementos_numero_atomico CHECK (numero_atomico IS NULL OR numero_atomico BETWEEN 1 AND 118);

ALTER TABLE elementos ADD CONSTRAINT ck_elementos_periodo CHECK (periodo IS NULL OR periodo BETWEEN 1 AND 7);

ALTER TABLE elementos ADD CONSTRAINT ck_elementos_grupo CHECK (grupo IS NULL OR grupo BETWEEN 1 AND 18);

ALTER TABLE elementos ADD CONSTRAINT ck_elementos_bloco CHECK (bloco IS NULL OR bloco IN ('s', 'p', 'd', 'f'));

ALTER TABLE elementos ADD CONSTRAINT ck_elementos_estado_padrao CHECK (estado_padrao IS NULL OR estado_padrao IN ('solido', 'liquido', 'gas', 'solido_previsto', 'gas_previsto'));

ALTER TABLE elementos ADD CONSTRAINT ck_elementos_bloco_f_sem_grupo CHECK (bloco IS NULL OR (bloco = 'f' AND grupo IS NULL) OR (bloco <> 'f' AND grupo IS NOT NULL));

ALTER TABLE elementos ADD CONSTRAINT ck_elementos_descoberta CHECK (NOT (conhecido_antiguidade AND ano_descoberta IS NOT NULL));

ALTER TABLE fontes ADD COLUMN acessado_em DATE;

ALTER TABLE fontes ADD COLUMN versao_fonte VARCHAR(60);

UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

COMMIT;

