# TCC — Dataset de Toxicidade para Comunidades Gamer Brasileiras

## Tema Geral
Construção de um dataset de toxicidade voltado para comunidades gamer brasileiras, com foco em mensagens em português (e alguns termos em inglês utilizados em jogos), incluindo definição de taxonomia de toxicidade e, caso haja tempo, treinamento preliminar de modelos de PLN/LLMs.

---

# Objetivo Geral

Desenvolver um dataset de toxicidade voltado para comunidades gamer brasileiras, contendo mensagens rotuladas e uma taxonomia de termos ofensivos, com foco na língua portuguesa e no vocabulário específico utilizado em ambientes de jogos on-line.

---

# Objetivos Específicos

- Coletar mensagens provenientes de plataformas como Twitch, Reddit e outras comunidades on-line relacionadas ao universo gamer.
- Construir um dataset contendo mensagens rotuladas quanto à presença ou ausência de toxicidade.
- Definir uma taxonomia de toxicidade adequada ao contexto das comunidades de jogos, incluindo categorias como insultos, assédio, discurso de ódio e ameaças.
- Elaborar um segundo dataset contendo palavras, gírias e expressões ofensivas utilizadas no ambiente gamer, com foco na língua portuguesa e presença eventual de termos em inglês.
- Realizar limpeza, padronização e pré-processamento textual.
- Definir estratégia de tokenização e anotação das mensagens.
- Disponibilizar o dataset como recurso para pesquisas futuras.
- Caso haja tempo, realizar treinamento preliminar de modelos de classificação textual.

---

# Estrutura do TCC

## Capítulo 1 — Introdução
- Contextualização
- Motivação
- Problema
- Objetivos gerais e específicos

## Capítulo 2 — Fundamentação Teórica
### Jogos multiplayer com chat
- Twitch
- Discord
- Reddit
- comunicação gamer
- linguagem informal
- anonimato
- competição

### Toxicidade em comunidades gamer
- insultos
- assédio
- misoginia
- xenofobia
- discurso de ódio
- impacto psicológico

### PLN e LLMs
- transformers
- embeddings contextuais
- BERT
- RoBERTa
- T5
- classificação textual
- toxicidade

### Trabalhos relacionados
- GameTox
- artigos sobre toxicidade em jogos
- datasets de toxicidade
- PLN aplicado a toxicidade
- estudos sociológicos sobre toxicidade

---

# Explicações importantes usadas no TCC

## PLN
Processamento de Linguagem Natural é a área da Inteligência Artificial responsável por permitir que computadores interpretem textos e linguagem humana.

## LLM
Large Language Models são modelos de linguagem de grande porte treinados com enormes volumes de texto para compreender linguagem natural de forma contextual.

## Diferença entre PLN e LLM
- PLN = área de estudo
- LLM = tipo de modelo dentro do PLN

---

# Arquitetura Transformer

Transformers utilizam mecanismos de self-attention para analisar o contexto das palavras em uma frase simultaneamente.

Importância:
- compreensão contextual
- gírias
- ironia
- abreviações
- linguagem informal gamer

Modelos:
- BERT
- RoBERTa
- T5

---

# Métricas

## Precisão
Mede quantas previsões positivas realmente estavam corretas.

## Recall
Mede quantos casos positivos reais foram identificados.

## F1-score
Equilíbrio entre precisão e recall.

---

# Fundamentação Teórica — Conteúdo já estruturado

## Jogos Multiplayer com Chat
- jogos online como ambientes sociais
- Twitch e Discord como extensões sociais dos jogos
- linguagem própria do ambiente gamer
- grande volume de interação textual

## Toxicidade em Jogos
- insultos relacionados à habilidade
- xingamentos
- misoginia
- racismo
- assédio
- toxicidade normalizada

## PLN e Toxicidade
- uso de transformers
- embeddings contextuais
- classificação textual
- intent classification
- slot filling

---

# Trabalhos Relacionados

## Pires & Fortim (2021)
- estudo qualitativo em League of Legends
- categorização de insultos
- relação entre anonimato e agressividade
- mais de 90% dos jogadores relataram já ter testemunhado toxicidade
- cerca de 40% admitiram já ter praticado

Diferença:
- trabalho sociológico/descritivo
- meu TCC visa construir dataset e taxonomia

---

## Nunes & Fortim (2025)
- toxicidade em Twitch e Discord
- discursos discriminatórios
- impacto psicológico
- comunidades gamer como ambientes sociais

Diferença:
- estudo não utiliza PLN
- meu foco é dataset e possível automação futura

---

## Naseem et al. (2025)
- dataset de 53 mil mensagens
- World of Tanks
- categorias:
  - insults and flaming
  - hate and harassment
  - threats
  - extremism

- uso de:
  - intent classification
  - slot filling

Diferença:
- dataset em inglês
- apenas um jogo
- meu TCC:
  - português brasileiro
  - Twitch
  - Reddit
  - Discord
  - linguagem gamer brasileira

---

## Investigating Contextual Word Embeddings in Semi-Supervised Learning for Toxic Comment Detection
- embeddings contextuais
- aprendizado semi-supervisionado
- classificação de toxicidade
- importância do contexto linguístico

Diferença:
- dataset genérico
- não gamer
- não português

Contribuição para meu TCC:
- reforça importância de embeddings contextuais
- reforça necessidade de dataset especializado

---

# Desenvolvimento (Capítulo 3)

## Descrição da proposta
Construção de:
- dataset gamer brasileiro
- taxonomia de toxicidade
- base de gírias e termos ofensivos
- possível treinamento preliminar

## Pipeline planejado
1. coleta
2. limpeza textual
3. anotação
4. tokenização
5. construção do dataset
6. treinamento preliminar (se houver tempo)

---

# Validação / Experimentos (Capítulo 4)

Planejamento para TCC II:
- avaliação quantitativa
- métricas:
  - precisão
  - recall
  - F1-score
- comparação entre modelos
- validação do dataset

---

# Considerações Parciais

## TCC I
Já realizado:
- fundamentação teórica
- definição do problema
- definição da taxonomia preliminar
- modelagem da solução
- planejamento do pipeline

Ainda falta:
- coleta definitiva
- anotação
- construção final do dataset
- treinamento
- validação

---

# Próximos Passos (TCC II)

- coleta definitiva dos dados
- limpeza e padronização
- anotação manual
- tokenização
- construção do dataset
- treinamento preliminar
- avaliação experimental

---

# Estratégia de Busca Bibliográfica

Bases:
- Scopus
- IEEE Xplore
- Google Scholar
- Portal CAPES

Uso de operadores:
- AND
- OR

Strings:
- português e inglês

---

# Strings importantes de busca

## Dataset gamer
("game chat dataset" OR "gaming communication dataset")
AND
(annotation OR corpus OR dataset)
AND
(toxicity OR insults OR harassment)

## Toxicidade em jogos
("online games" OR gaming)
AND
(toxicity OR "hate speech")
AND
(dataset OR corpus)

## Português
("jogos online")
AND
(toxicidade OR "linguagem ofensiva")
AND
(dataset OR corpus)

---

# Contribuição Principal do TCC

Construção de:
- dataset gamer brasileiro
- taxonomia de toxicidade
- vocabulário gamer em português
- recurso para futuras pesquisas em PLN e moderação automática

---

# Possíveis Títulos do TCC

- Construção de um Dataset de Toxicidade para Comunidades Gamer Brasileiras
- Dataset de Toxicidade em Português para Comunidades de Jogos Online
- Construção de um Corpus Gamer para Detecção de Toxicidade em Português
- Taxonomia e Dataset de Toxicidade para Comunidades Gamer Brasileiras

---