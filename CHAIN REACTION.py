import pygame
import sys
import random
import pickle
import os

'''
Aqui a gente coloco todas as variaveis globais que vamos usar no programa
'''

LARGURA, COMPRIMENTO = 700, 700
LINHAS, COLUNAS = 6, 6
CELL_SIZE = LARGURA // COLUNAS
FPS = 60
BG_COR = (15, 15, 25)
GRID_COR = (70, 70, 90)
PLAYER1_COR = (255, 80, 80)
PLAYER2_COR = (80, 160, 255)
MENU = 0
PVP = 1
VS_IA = 2
#Inicializamos o pygame e usamos os parametros criados
pygame.init()
tela = pygame.display.set_mode((LARGURA, COMPRIMENTO))
pygame.display.set_caption("JOGO CHAIN REACTION")
clock = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 28)
modo_jogo = MENU
player_atual = 1
vencedor = None
turno = 0
ia_treinada_fim = False
animacoes = []
particulas = []
fila_explosoes = []
tempo_explosao = 0
DELAY_EXPLOSAO = 250
q_table = {}
historico_ia = []
BRAIN_FILE = "brain.pkl"
if os.path.exists(BRAIN_FILE):
    with open(BRAIN_FILE, "rb") as f:
        q_table = pickle.load(f)
class Cell:
    def __init__(self, linha, coluna):
        self.linha = linha
        self.coluna = coluna
        self.count = 0
        self.owner = 0
    def massa_critica(self):
        if (
            (self.linha == 0 and self.coluna == 0)
            or (self.linha == 0 and self.coluna == COLUNAS - 1)
            or (self.linha == LINHAS - 1 and self.coluna == 0)
            or (self.linha == LINHAS - 1 and self.coluna == COLUNAS - 1)
        ):
            return 2
        if (
            self.linha == 0
            or self.linha == LINHAS - 1
            or self.coluna == 0
            or self.coluna == COLUNAS - 1
        ):
            return 3
        return 4
tabuleiro = [[Cell(r, c) for c in range(COLUNAS)] for r in range(LINHAS)]


#Criamos uma classe para fazer funcionar as animações
class OrbAnim:
    def __init__(self, x, y, alvo_x, alvo_y, cor, nr, nc, player):
        self.x = x
        self.y = y
        self.alvo_x = alvo_x
        self.alvo_y = alvo_y
        self.cor = cor
        self.nr = nr
        self.nc = nc
        self.player = player
        self.finished = False
    def update(self):
        dx = self.alvo_x - self.x
        dy = self.alvo_y - self.y
        dist = (dx**2 + dy**2) ** 0.5
        if dist < 2:
            self.x = self.alvo_x
            self.y = self.alvo_y
            cell = tabuleiro[self.nr][self.nc]
            cell.count += 1
            cell.owner = self.player
            if cell.count >= cell.massa_critica():
                fila_explosoes.append((self.nr, self.nc, self.player))
            self.finished = True
            return
        self.x += dx * 0.18
        self.y += dy * 0.18
    def draw(self):
        pygame.draw.circle(tela, self.cor, (int(self.x), int(self.y)), 10)




class Particula:
    def __init__(self, x, y, cor):
        self.x = x
        self.y = y
        self.dx = random.uniform(-4, 4)
        self.dy = random.uniform(-4, 4)
        self.life = 30
        self.cor = cor
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
    def draw(self):
        pygame.draw.circle(tela, self.cor, (int(self.x), int(self.y)), 4)



def get_status():
    status = []
    for linha in tabuleiro:
        for cell in linha:
            status.append((cell.owner, cell.count))
    return tuple(status)


def get_possiveis_movimentos(player):
    movimentos = []
    for linha in range(LINHAS):
        for coluna in range(COLUNAS):
            cell = tabuleiro[linha][coluna]
            if cell.owner in [0, player]:
                movimentos.append((linha, coluna))
    return movimentos


def escolher_acao(state, player):
    movimentos = get_possiveis_movimentos(player)
    if not movimentos:
        return None
    if random.random() < 0.2:
        return random.choice(movimentos)
    best_score = -999999
    best_move = random.choice(movimentos)
    for move in movimentos:
        value = q_table.get((state, move), 0)
        if value > best_score:
            best_score = value
            best_move = move
    return best_move


def update_q(state, action, reward, next_state):
    alpha = 0.25
    gamma = 0.95
    old_value = q_table.get((state, action), 0)
    future_rewards = [
        q_table.get((next_state, move), 0)
        for move in get_possiveis_movimentos(2)
    ]
    max_future = max(future_rewards, default=0)
    new_value = old_value + alpha * (
        reward + gamma * max_future - old_value
    )
    q_table[(state, action)] = new_value


def save_ai():
    with open(BRAIN_FILE, "wb") as f:
        pickle.dump(q_table, f)


def treinar_ia_fim_de_partida():
    global historico_ia
    if vencedor == 2:
        recompensa_final = 100
    elif vencedor == 1:
        recompensa_final = -150
    else:
        recompensa_final = 0
    for state, action, next_state in reversed(historico_ia):
        update_q(state, action, recompensa_final, next_state)
        recompensa_final *= 0.9
    save_ai()
    historico_ia.clear()


def draw_orbs(x, y, count, cor):
    center_x = x + CELL_SIZE // 2
    center_y = y + CELL_SIZE // 2
    raio = 16
    if count == 1:
        pygame.draw.circle(tela, cor, (center_x, center_y), raio)
    elif count == 2:
        pygame.draw.circle(tela, cor, (center_x - 18, center_y), raio)
        pygame.draw.circle(tela, cor, (center_x + 18, center_y), raio)
    elif count >= 3:
        pygame.draw.circle(tela, cor, (center_x, center_y - 18), raio)
        pygame.draw.circle(tela, cor, (center_x - 18, center_y + 12), raio)
        pygame.draw.circle(tela, cor, (center_x + 18, center_y + 12), raio)


def desenhar_mensagem_final():
    if modo_jogo == VS_IA:
        if vencedor == 1:
            mensagem = "VOCÊ VENCEU! Aperte R para reiniciar"
        else:
            mensagem = "VOCÊ PERDEU! Aperte R para reiniciar"
    else:
        mensagem = f"PLAYER {vencedor} VENCEU! Aperte R para reiniciar"
    pygame.draw.rect(tela, (0, 0, 0), (20, COMPRIMENTO - 80, 660, 60))
    pygame.draw.rect(tela, (255, 255, 255), (20, COMPRIMENTO - 80, 660, 60), 2)
    texto = fonte.render(mensagem, True, (255, 255, 255))
    tela.blit(texto, (45, COMPRIMENTO - 62))


def draw_board():
    tela.fill(BG_COR)
    for linha in range(LINHAS):
        for coluna in range(COLUNAS):
            x = coluna * CELL_SIZE
            y = linha * CELL_SIZE
            pygame.draw.rect(tela, GRID_COR, (x, y, CELL_SIZE, CELL_SIZE), 2)
            cell = tabuleiro[linha][coluna]
            if cell.count > 0:
                cor = PLAYER1_COR if cell.owner == 1 else PLAYER2_COR
                draw_orbs(x, y, cell.count, cor)
    if vencedor:
        desenhar_mensagem_final()


def get_vizinhos(linha, coluna):
    vizinhos = []
    direcoes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in direcoes:
        nr = linha + dr
        nc = coluna + dc
        if 0 <= nr < LINHAS and 0 <= nc < COLUNAS:
            vizinhos.append((nr, nc))
    return vizinhos



def checar_vencedor():
    global vencedor
    if turno < 2:
        return
    player1_existe = False
    player2_existe = False
    for linha in tabuleiro:
        for cell in linha:
            if cell.owner == 1 and cell.count > 0:
                player1_existe = True
            if cell.owner == 2 and cell.count > 0:
                player2_existe = True
    if not player1_existe and player2_existe:
        vencedor = 2
    elif not player2_existe and player1_existe:
        vencedor = 1


def parar_jogo_se_vencedor():
    if vencedor:
        fila_explosoes.clear()
        animacoes.clear()
        particulas.clear()


def explode(linha, coluna, player):
    fila_explosoes.append((linha, coluna, player))


def processar_explosoes():
    global tempo_explosao
    if not fila_explosoes or vencedor:
        return
    
    
    agora = pygame.time.get_ticks()
    
    
    if agora - tempo_explosao < DELAY_EXPLOSAO:
        return
    
    tempo_explosao = agora
    linha, coluna, player = fila_explosoes.pop(0)
    cell = tabuleiro[linha][coluna]
    
    if cell.count < cell.massa_critica():
        return
    x = coluna * CELL_SIZE + CELL_SIZE // 2
    y = linha * CELL_SIZE + CELL_SIZE // 2
    cell.count -= cell.massa_critica()
    
    if cell.count <= 0:
        cell.count = 0
        cell.owner = 0
    vizinhos = get_vizinhos(linha, coluna)
    
    for nr, nc in vizinhos:
        alvo_x = nc * CELL_SIZE + CELL_SIZE // 2
        alvo_y = nr * CELL_SIZE + CELL_SIZE // 2
        cor = PLAYER1_COR if player == 1 else PLAYER2_COR
        for _ in range(8):
            particulas.append(Particula(x, y, cor))
        animacoes.append(
            OrbAnim(x, y, alvo_x, alvo_y, cor, nr, nc, player)
        )
    
    checar_vencedor()
    
    parar_jogo_se_vencedor()



def add_orb(linha, coluna, player):
    cell = tabuleiro[linha][coluna]
    cell.count += 1
    cell.owner = player
    if cell.count >= cell.massa_critica():
        explode(linha, coluna, player)
    checar_vencedor()
    parar_jogo_se_vencedor()



def trocar_player():
    global player_atual
    player_atual = 2 if player_atual == 1 else 1



def resetar_game():
    global tabuleiro, player_atual, vencedor, turno, ia_treinada_fim
    tabuleiro = [[Cell(r, c) for c in range(COLUNAS)] for r in range(LINHAS)]
    animacoes.clear()
    particulas.clear()
    fila_explosoes.clear()
    historico_ia.clear()
    player_atual = 1
    vencedor = None
    turno = 0
    ia_treinada_fim = False


FUNDO_MENU = (30, 30, 30)
CINZA = (90, 90, 90)
CINZA_HOVER = (140, 140, 140)
BRANCO = (255, 255, 255)
fonte_titulo = pygame.font.SysFont("Arial", 60, bold=True)
fonte_botao = pygame.font.SysFont("Arial", 30)
botao_pvp = pygame.Rect(150, 250, 400, 80)
botao_ia = pygame.Rect(150, 370, 400, 80)



def draw_menu():
    mouse = pygame.mouse.get_pos()
    tela.fill(FUNDO_MENU)
    titulo = fonte_titulo.render("CHAIN REACTION", True, BRANCO)
    tela.blit(titulo, (120, 100))
    cor_pvp = CINZA_HOVER if botao_pvp.collidepoint(mouse) else CINZA
    cor_ia = CINZA_HOVER if botao_ia.collidepoint(mouse) else CINZA
    pygame.draw.rect(tela, cor_pvp, botao_pvp, border_radius=15)
    pygame.draw.rect(tela, cor_ia, botao_ia, border_radius=15)
    texto_pvp = fonte_botao.render("JOGADOR VS JOGADOR", True, BRANCO)
    texto_ia = fonte_botao.render("JOGADOR VS IA", True, BRANCO)
    tela.blit(texto_pvp, (205, 275))
    tela.blit(texto_ia, (240, 395))
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_ai()
            running = False
        if modo_jogo == MENU:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if botao_pvp.collidepoint(mouse):
                    modo_jogo = PVP
                    resetar_game()
                if botao_ia.collidepoint(mouse):
                    modo_jogo = VS_IA
                    resetar_game()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                modo_jogo = MENU
                resetar_game()
            if event.key == pygame.K_DELETE:
                q_table.clear()
                if os.path.exists(BRAIN_FILE):
                    os.remove(BRAIN_FILE)
                print("Memória da IA apagada")
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and modo_jogo != MENU
            and not vencedor
            and not fila_explosoes
            and not animacoes
            and (modo_jogo == PVP or player_atual == 1)
        ):
            mx, my = pygame.mouse.get_pos()
            coluna = mx // CELL_SIZE
            linha = my // CELL_SIZE
            if 0 <= linha < LINHAS and 0 <= coluna < COLUNAS:
                cell = tabuleiro[linha][coluna]
                if cell.owner in [0, player_atual]:
                    add_orb(linha, coluna, player_atual)
                    turno += 1
                    if not vencedor:
                        trocar_player()
    if (
        modo_jogo == VS_IA
        and player_atual == 2
        and not vencedor
        and not fila_explosoes
        and not animacoes
    ):
        pygame.time.delay(300)
        state = get_status()
        move = escolher_acao(state, 2)
        if move is not None:
            linha, coluna = move
            before_score = len(get_possiveis_movimentos(2))
            add_orb(linha, coluna, 2)
            next_state = get_status()
            historico_ia.append((state, move, next_state))
            after_score = len(get_possiveis_movimentos(2))
            reward = after_score - before_score
            update_q(state, move, reward, next_state)
            turno += 1
            if not vencedor:
                trocar_player()
    if not vencedor:
        checar_vencedor()
        parar_jogo_se_vencedor()
    if vencedor and not ia_treinada_fim:
        treinar_ia_fim_de_partida()
        ia_treinada_fim = True
    if modo_jogo == MENU:
        draw_menu()
    else:
        draw_board()
    if not vencedor:
        for anim in animacoes[:]:
            anim.update()
            anim.draw()
            if anim.finished:
                animacoes.remove(anim)
        for p in particulas[:]:
            p.update()
            p.draw()
            if p.life <= 0:
                particulas.remove(p)
        processar_explosoes()
    pygame.display.flip()
pygame.quit()
sys.exit()
