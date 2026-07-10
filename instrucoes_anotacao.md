# Instruções de Anotação — Validação de Toxicidade

Você vai analisar mensagens de chat da Twitch e marcar, para cada uma, em qual(is) categoria(s) de toxicidade ela se encaixa. Marque com um `X` (ou `1`) nas colunas `anotador_*` correspondentes na planilha `data/validation_sample.csv`. Cada mensagem pode receber **mais de uma marcação** (ex.: pode ser INS e OBS ao mesmo tempo) ou nenhuma, se não for tóxica.

## Categorias

- **NT — Não Tóxico**: mensagem sem conteúdo ofensivo; comunicação neutra ou positiva entre jogadores.
- **INS — Insulto**: ataque à habilidade, ao desempenho ou à identidade do jogador (ex.: "noob", "inútil", "lixo").
- **ASS — Assédio**: ataque dirigido e repetido a um usuário específico (moral ou sexual). *Como você verá as mensagens isoladas, sem o restante da conversa, julgue pelo tom da mensagem em si — se parecer um ataque pessoal direcionado, marque ASS mesmo sem ver a repetição.*
- **DO — Discurso de Ódio**: ataque a um grupo com base em raça, gênero, orientação sexual, religião ou origem (racismo, misoginia, homofobia, xenofobia).
- **AME — Ameaça**: mensagem com teor ameaçador ou que incita violência física ou virtual contra outra pessoa.
- **OBS — Obscenidade**: linguagem vulgar/baixo calão sem alvo específico (palavrão genérico, sem grupo ou pessoa visada). *Atenção: conta como OBS mesmo quando o palavrão é usado como interjeição de ênfase (ex.: "caralho, que jogada"), não apenas como ofensa direta.*

## Como marcar

1. Leia a mensagem na coluna `message`.
2. Marque `X` em todas as colunas `anotador_*` que se aplicarem.
3. Se a mensagem for NT, marque apenas `anotador_NT` e deixe as demais em branco.
4. Em caso de dúvida real entre duas categorias, marque as duas — isso será tratado como ambiguidade na análise.
5. Não é necessário pesquisar o canal ou o usuário; julgue apenas pelo texto da mensagem.
