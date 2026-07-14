# RageFilter

**Título do TCC:** RageFilter: Construção de um Dataset de Toxicidade para Comunidades *gamer* Brasileiras
**Alunos:** Luiz Henrique Mendes de Oliveira Castro
**Semestre de Defesa:** 2026-1

[PDF do TCC](RageFilter.pdf)

# TL;DR

Para reproduzir o pipeline de construção do dataset (coleta → limpeza → rotulação → exportações):

```
$ npm install && node src/twitch_chat_scraper.js   # coleta de chats ao vivo da Twitch (tmi.js)
$ python src/filter_and_merge.py                   # limpeza, deduplicação e consolidação -> data/final_chat.csv
$ python src/annotate.py                            # rotulação automática (léxico + regras) -> data/final_chat_labeled.csv
$ python src/export_toxic.py                        # separa mensagens tóxicas / não tóxicas
$ python src/export_girias.py                       # exporta ocorrências de gírias
$ python src/toxicity_by_stream.py                  # taxa de toxicidade por canal
$ python src/check_duplicates.py                    # auditoria de duplicatas
$ python src/gerar_graficos.py                       # gera os gráficos usados no TCC
```

# Descrição Geral

O crescimento das comunidades digitais de jogos eletrônicos intensificou a ocorrência de interações tóxicas em plataformas como a Twitch. Apesar da existência de pesquisas sobre toxicidade textual, ainda há escassez de *datasets* em português voltados especificamente para a linguagem *gamer*, marcada por gírias, abreviações e expressões próprias desse contexto.

Este trabalho constrói um *dataset* de toxicidade direcionado às comunidades *gamer* brasileiras, a partir da coleta de mais de 1 milhão de mensagens de chat da Twitch (30 canais monitorados, entre abril e junho de 2026). As mensagens passam por um *pipeline* de limpeza (remoção de ruído do *broadcaster*, bots, comandos, *spam* e duplicatas) e são rotuladas automaticamente por meio de um léxico curado de termos *gamer* e regras, seguindo uma taxonomia de seis categorias de toxicidade (Não Tóxico, Insulto, Assédio, Discurso de Ódio, Ameaça, Obscenidade) em nível de sentença, além de rótulos em nível de *token* (TÓXICO, GÍRIA\_GAMER, NEUTRO), inspirados na abordagem de *slot filling*. O resultado é um recurso especializado para pesquisas futuras em Processamento de Linguagem Natural e detecção de toxicidade em português brasileiro.

# Funcionalidades

* Coleta de dados em tempo real
   * *Scraper* em Node.js (biblioteca `tmi.js`) conectado ao chat da Twitch
   * Monitoramento de 49 canais de *streamers* brasileiros, cobrindo diferentes perfis (League of Legends, CS2/FPS, variedade)
   * Registro de mensagens públicas em arquivos CSV por canal e data
* *Pipeline* de limpeza (`src/filter_and_merge.py`)
   * Remoção de mensagens automatizadas do *broadcaster*, bots conhecidos e comandos de chat
   * Filtro de *spam*/propaganda e remoção de duplicatas exatas e quase-duplicatas
   * Consolidação de todo o conteúdo em um único *dataset* (`data/final_chat.csv`)
* Léxico de gírias e termos ofensivos (`lexicon/lexicon.csv`)
   * Mais de 500 entradas cobrindo gírias *gamer* neutras e termos de insulto, discurso de ódio, obscenidade e ameaça
   * Suporte a termos ambíguos (gíria vs. insulto condicional) e normalização de variações ortográficas/*leetspeak*
* Rotulação automática (`src/annotate.py`)
   * Nível de sentença: classificação multi-rótulo em seis categorias (NT, INS, ASS, DO, AME, OBS)
   * Nível de *token*: *slot filling* (TÓXICO, GÍRIA\_GAMER, NEUTRO)
   * Heurística de assédio baseada em persistência de remetente contra o mesmo alvo em janela temporal
* Exportações derivadas
   * `src/export_toxic.py`: separação em mensagens tóxicas e não tóxicas
   * `src/export_girias.py`: extração de ocorrências de gírias identificadas
   * `src/toxicity_by_stream.py`: taxa de toxicidade por canal monitorado
* Auditoria de qualidade (`src/check_duplicates.py`)
   * Validação da integridade do processo de deduplicação sobre os artefatos exportados
* Visualizações (`src/gerar_graficos.py`)
   * Gráficos de distribuição de rótulos, *pipeline* de limpeza, ranking de canais e nuvens de palavras
