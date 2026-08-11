# reacao-em-cadeia-python-ia
Projeto acadêmico de Reação em Cadeia desenvolvido em Python, Pygame e Inteligência Artificial com Q-Learning.


# Chain Reaction: Motor Gráfico com Pygame e Inteligência Artificial por Aprendizado por Reforço (Q-Learning Tabular)


Este projeto consiste no desenvolvimento e implementação completa do clássico jogo de estratégia **Chain Reaction**. O software foi consolidado em arquitetura de arquivo único, integrando um motor de renderização gráfica bidimensional (2D) em tempo real e um agente autônomo baseado em Inteligência Artificial que aprende estratégias de combate tático através de **Aprendizado por Reforço (Tabular Q-Learning)**.

### A pesquisa e criação do projeto foi feita pelos estudantes:
- Matheus Terceiro Daniel - 824121622
- Samuel Gutierrez - 824150619
- Kaique Nunes Dicherman - 824132510
- Jeremias Henry Callata Quispe - 824113042
- Juan David Fontecha - 82419678
- Erlan Omar Arce Vasquez - 826178640

---

## 1. Ideia Principal do Projeto

A essencia do projeto é criar um jogo visualmente atraente com o objetivo de criar um ecossistema fechado onde um agente computacional (IA) evolui sua capacidade de tomada de decisão sem regras preprogramadas de jogabilidade, baseando-se estritamente na experimentação empírica (tentativa e erro) e na otimização de uma função de utilidade (recompensas).

---

## 2. Regras Completas do Jogo

O jogo é disputado em uma matriz bidimensional de **6x6 células** por dois jogadores (Player 1 - Vermelho; Player 2/IA - Azul).

### Mecânica de Posicionamento e Propriedade
- Os jogadores alternam turnos inserindo um orbe em uma célula vazia ou em uma célula que já seja de sua propriedade.
- Ao inserir um orbe em uma célula própria, o contador (`count`) daquela célula é incrementado em $+1$.

### O Conceito de Massa Crítica
Cada célula possui um limite de estabilidade física chamado **Massa Crítica**. Este limite depende estritamente da localização geográfica da célula no grid:
- **Cantos (Vértices):** Massa crítica = **2**. Possuem apenas 2 vizinhos adjacentes.
- **Bordas (Laterais):** Massa crítica = **3**. Possuem 3 vizinhos adjacentes.
- **Células Internas (Centro):** Massa crítica = **4**. Possuem 4 vizinhos adjacentes.

### Explosões e Reações em Cadeia
1. Quando o número de orbes de uma célula atinge ou excede sua **Massa Crítica**, a célula torna-se instável e **explode**.
2. Na explosão, a célula perde uma quantidade de orbes igual à sua massa crítica. Se o contador zerar, ela perde seu proprietário.
3. Os orbes resultantes da explosão são disparados para as células vizinhas adjacentes (norte, sul, leste, oeste).
4. Ao entrarem nas células vizinhas, esses orbes **reivindicam a propriedade** daquelas células para o jogador que causou a explosão, independentemente de quem as controlava antes.
5. Se o acréscimo desses novos orbes fizer com que uma célula vizinha também atinja sua massa crítica, uma **reação em cadeia** é engatilhada, gerando explosões subsequentes.

### Condição de Vitória
Um jogador vence quando **elimina completamente** a presença do oponente no tabuleiro (o oponente fica com 0 orbes). Esta checagem só é validada após o segundo turno do jogo (`turno >= 2`), permitindo o setup inicial de ambos os competidores.

---

## 3. Funcionamento do Motor do Jogo (Engine)

O motor do jogo foi construído sobre a biblioteca **Pygame**.

### Bucle Principal (Game Loop) e Controle de Estados
O loop principal roda de forma assíncrona gerenciando as entradas do usuário, atualizações físicas e chamadas de desenho. O controle de framerate é cravado em **60 FPS** via `clock.tick(FPS)`, garantindo estabilidade de CPU. O fluxo do jogo é ditado por uma máquina de estados simples (`modo_jogo`): `MENU`, `PVP` ou `VS_IA`.

### Gerenciamento de Animações e Partículas
Para evitar que as reações em cadeia ocorram instantaneamente (o que prejudicaria a experiência visual e o entendimento do usuário), o motor implementa um sistema de renderização desacoplado:
- **Animações Cinéticas (`OrbAnim`):** Quando ocorre uma explosão, os projéteis não teletransportam. A classe calcula vetores de deslocamento baseados em interpolação linear (`self.x += dx * 0.18`), movendo os orbes de forma suave até o alvo.
- **Sistema de Partículas (`Particula`):** No momento do impacto, vetores aleatórios de dispersão (`random.uniform(-4, 4)`) geram partículas de feedback visual com tempo de vida limitado (`life = 30`), simulando uma explosão física.

### Processamento de Eventos e Fila Assíncrona (Explosion Queue)
As explosões são gerenciadas por uma estrutura de dados de fila (`fila_explosoes`). Quando uma célula explode, ela entra na fila. A função `processar_explosoes()` consome essa fila sequencialmente utilizando um temporizador de clock do sistema (`pygame.time.get_ticks()`) respeitando um intervalo constante de `DELAY_EXPLOSAO = 250` milissegundos. Isso garante que a IA e o jogador visualizem cada etapa da reação em cadeia ordenadamente antes do próximo turno iniciar.

---

## 4. Funcionamento da Inteligência Artificial (Q-Learning)

A IA deste projeto adota uma abordagem pura de **Aprendizado por Reforço Tabular**, eliminando a necessidade de frameworks de Deep Learning pesados (como TensorFlow ou PyTorch). Toda a lógica matemática foi construída de forma otimizada utilizando estruturas nativas do Python.

### Biblioteca de Análise e Persistência: `pickle`
A "memória" da IA é armazenada em uma tabela hash volátil (`q_table = {}`). Para garantir que o aprendizado não seja perdido ao encerrar o script, foi utilizada a biblioteca padrão **`pickle`**. Ela realiza a **serialização e desserialização binária** do dicionário Python diretamente no disco rígido através do arquivo `brain.pkl`. Sempre que o jogo inicia, a engine verifica a existência deste arquivo e carrega o histórico cognitivo acumulado da IA.

### Modelagem do Algoritmo de Aprendizado

#### 1. Representação do Estado ($S$)
O estado do tabuleiro precisa ser imutável para servir como chave no dicionário da `q_table`. A função `get_status()` compacta a matriz 6x6 em uma **tupla flat** contendo pares de informação de cada célula: `(owner, count)`. O espaço de estados totaliza todas as combinações possíveis de orbes e donos nas 36 posições.

#### 2. Escolha de Ações: Política $\epsilon$-Greedy (Epsilon-Greedy)
Na função `escolher_acao()`, o agente pondera entre explorar o ambiente ou explorar o conhecimento adquirido:
- **Exploração (20% de chance):** Com uma probabilidade fixa de $0.2$, a IA escolhe um movimento puramente aleatório entre as coordenadas legais. Isso evita que ela fique presa em ótimos locais e permite descobrir novas táticas.
- **Explotação (80% de chance):** Nos outros 80%, a IA varre a `q_table` procurando a ação que possui o maior valor de utilidade acumulado ($Q$) para o estado atual.

#### 3. Função de Atualização Matemática (Equação de Bellman)
A atualização da matriz de conhecimento é realizada através da fórmula padrão do Q-Learning:

$$Q(s, a) \leftarrow Q(s, a) + \alpha \cdot \left[ R + \gamma \cdot \max_{a'} Q(s', a') - Q(s, a) \right]$$

No código, os hiperparâmetros foram calibrados da seguinte forma:
- **Taxa de Aprendizado ($\alpha = 0.25$):** Determina o impacto das novas informações em relação ao conhecimento antigo.
- **Fator de Desconto ($\gamma = 0.95$):** Define a importância dada às recompensas de longo prazo (estratégia futura) em detrimento do ganho imediato.

#### 4. Engenharia de Recompensas (Reward Engineering)
A IA recebe estímulos em dois níveis para moldar seu comportamento:
- **Recompensa Imediata (Turno a Turno):** Calculada pela diferença de território disponível entre o final e o início do movimento (`after_score - before_score`). Se a jogada da IA reduzir as opções de movimento do oponente humano ou aumentar as suas próprias através de capturas, ela recebe um feedback positivo instantâneo.
- **Recompensa Terminal e Propagação Temporal (Fim de Jogo):** Ao finalizar a partida, a função `treinar_ia_fim_de_partida()` aplica o veredito final:
  - **Vitória:** $+100$
  - **Derrota:** $-150$ (Penalidade severa para forçar a IA a evitar posições de risco).
  
  O histórico completo de estados e ações daquela partida (`historico_ia`) é percorrido em ordem reversa (`reversed()`). A recompensa terminal é propagada de volta para as jogadas anteriores que levaram àquele desfecho, sofrendo um decaimento geométrico multiplicativo de $0.9$ a cada passo para trás. Isso ensina à IA que as escolhas feitas no início do jogo foram as fundações da vitória ou da derrota final.

---

## 5. Controles e Interface do Sistema

- **Clique Esquerdo do Mouse:** Interage com o menu principal e realiza a inserção de orbes nas células válidas do tabuleiro.
- **Tecla [R]:** Força o reset completo do estado físico do tabuleiro, retornando o fluxo para o Menu Principal.
- **Tecla [DELETE]:** Limpa a memória volátil da tabela hash e apaga fisicamente o arquivo binário `brain.pkl`, resetando completamente o aprendizado da IA para o estado zero (fábrica).
