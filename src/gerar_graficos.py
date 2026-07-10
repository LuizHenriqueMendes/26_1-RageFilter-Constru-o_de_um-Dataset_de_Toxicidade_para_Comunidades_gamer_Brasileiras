"""Gera os graficos usados no Capitulo de Desenvolvimento/Caracterizacao do TCC2."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

AZUL = "#2b6ca3"
VERMELHO = "#b3382c"
CINZA = "#8c8c8c"
VERDE = "#3c8a52"

# ---------------------------------------------------------------------------
# 1. Funil do pipeline de limpeza
# ---------------------------------------------------------------------------
etapas = [
    "Mensagens\nbrutas",
    "Ruído de\nbroadcaster",
    "Bots\nconhecidos",
    "Comandos\nde chat",
    "Spam /\npropaganda",
    "Duplicatas\nexatas",
    "Quase-\nduplicatas",
    "Dataset\nfinal",
]
valores = [1_212_642, 1_211_735, 1_191_857, 1_173_603, 1_024_080, 1_024_060, 1_013_339, 1_013_339]
# valor de cada etapa = total restante apos aquele filtro; a ultima barra repete o final

deltas = ["", "−907", "−19.878", "−18.254", "−149.523", "−20", "−10.721", ""]
xticklabels = [f"{e}\n{d}" if d else e for e, d in zip(etapas, deltas)]

fig, ax = plt.subplots(figsize=(9.5, 4.5))
cores = [CINZA, VERMELHO, VERMELHO, VERMELHO, VERMELHO, VERMELHO, VERMELHO, VERDE]
barras = ax.bar(range(len(etapas)), valores, color=cores, width=0.6)
ax.set_xticks(range(len(etapas)))
ax.set_xticklabels(xticklabels, fontsize=8.5)
ax.set_ylabel("Mensagens restantes")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
ax.set_ylim(0, 1_300_000)
for i, v in enumerate(valores):
    if i in (0, len(valores) - 1):
        ax.text(i, v + 25000, f"{v:,}".replace(",", "."), ha="center", fontsize=9, fontweight="bold")
ax.set_title("Redução do volume de mensagens ao longo do pipeline de limpeza")
fig.tight_layout()
fig.savefig("figuras/fig_pipeline_limpeza.png", dpi=200)
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Distribuicao em nivel de sentenca
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1, 1.4]})

# 2a. Nao toxico vs toxico (proporcao geral)
labels_geral = ["Não tóxico", "Tóxico"]
valores_geral = [986_966, 26_373]
axes[0].pie(
    valores_geral,
    labels=[f"{l}\n{v:,}".replace(",", ".") for l, v in zip(labels_geral, valores_geral)],
    autopct="%1.1f%%",
    colors=[AZUL, VERMELHO],
    startangle=90,
    wedgeprops={"linewidth": 1, "edgecolor": "white"},
)
axes[0].set_title("Mensagens por toxicidade")

# 2b. Categorias toxicas (escala log, pois variam em ordens de grandeza)
cats = ["OBS", "INS", "DO", "AME", "ASS"]
vals = [18_638, 7_007, 971, 183, 27]
axes[1].barh(cats, vals, color=VERMELHO)
axes[1].set_xscale("log")
axes[1].set_xlabel("Mensagens (escala logarítmica)")
axes[1].set_title("Composição das categorias tóxicas")
for i, v in enumerate(vals):
    axes[1].text(v * 1.15, i, f"{v:,}".replace(",", "."), va="center", fontsize=9)
axes[1].invert_yaxis()

fig.suptitle("Distribuição dos rótulos em nível de sentença", y=1.02, fontsize=12)
fig.tight_layout()
fig.savefig("figuras/fig_distribuicao_sentenca.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# 3. Distribuicao em nivel de token
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.3))
rotulos = ["NEUTRO", "GÍRIA_GAMER", "TÓXICO"]
valores_tok = [3_172_786, 207_408, 27_753]
cores_tok = [CINZA, AZUL, VERMELHO]
barras = ax.bar(rotulos, valores_tok, color=cores_tok, width=0.55)
ax.set_yscale("log")
ax.set_ylim(top=ax.get_ylim()[1] * 6)
ax.set_ylabel("Tokens (escala logarítmica)")
ax.set_title("Distribuição dos tokens por rótulo (slot filling)", pad=14)
total_tok = sum(valores_tok)
for b, v in zip(barras, valores_tok):
    ax.text(b.get_x() + b.get_width() / 2, v * 1.3, f"{v:,}".replace(",", ".") + f"\n({v/total_tok:.1%})",
            ha="center", fontsize=9)
fig.tight_layout()
fig.savefig("figuras/fig_distribuicao_token.png", dpi=200)
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. Ranking de toxicidade por canal (top 8 + bottom 5)
# ---------------------------------------------------------------------------
import pandas as pd
df = pd.read_csv("data/toxicity_by_stream.csv")
df = df[df["volume_suficiente"] == True].sort_values("taxa_toxicidade_pct", ascending=False)
top = df.head(8)
bottom = df.tail(5)
sel = pd.concat([top, bottom]).drop_duplicates()
sel = sel.sort_values("taxa_toxicidade_pct")

fig, ax = plt.subplots(figsize=(8, 5.5))
cores_canais = [VERMELHO if v in top["stream"].values else AZUL for v in sel["stream"]]
ax.barh(sel["stream"], sel["taxa_toxicidade_pct"], color=cores_canais)
ax.set_xlabel("Taxa de mensagens tóxicas (%)")
ax.set_title("Canais com maior e menor taxa de toxicidade")
for i, (s, v) in enumerate(zip(sel["stream"], sel["taxa_toxicidade_pct"])):
    ax.text(v + 0.1, i, f"{v:.2f}%", va="center", fontsize=9)
fig.tight_layout()
fig.savefig("figuras/fig_ranking_canais.png", dpi=200)
plt.close(fig)

print("Gráficos gerados em figuras/")

# ---------------------------------------------------------------------------
# 5. Fluxograma da arquitetura/pipeline geral da solucao
# ---------------------------------------------------------------------------
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

etapas_fluxo = [
    "COLETA DOS\nDADOS",
    "FILTRAGEM E\nLIMPEZA",
    "DEFINIÇÃO DE\nTAXONOMIA",
    "CONSTRUÇÃO DO\nLÉXICO",
    "ROTULAÇÃO DAS\nMENSAGENS",
    "DIVISÃO EM\nDATASETS FINAIS",
]

box_w, box_h = 2.7, 0.95
step_x, step_y = 1.75, 1.15

fig, ax = plt.subplots(figsize=(9, 7.5))
for i, texto in enumerate(etapas_fluxo):
    x = i * step_x
    y = -i * step_y
    ax.add_patch(FancyBboxPatch(
        (x, y), box_w, box_h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=2, edgecolor="black", facecolor="white", zorder=2,
    ))
    ax.text(x + box_w / 2, y + box_h / 2, texto, ha="center", va="center",
            fontsize=10.5, fontweight="bold", zorder=3)
    if i > 0:
        x0 = (i - 1) * step_x
        y0 = -(i - 1) * step_y
        start = (x0 + box_w * 0.22, y0)
        end = (x, y + box_h / 2)
        ax.add_patch(FancyArrowPatch(
            start, end,
            connectionstyle="angle,angleA=-90,angleB=180,rad=0",
            arrowstyle="-|>", mutation_scale=18, linewidth=1.8,
            color="black", zorder=1,
        ))

ax.set_xlim(-0.5, (len(etapas_fluxo) - 1) * step_x + box_w + 0.5)
ax.set_ylim(-(len(etapas_fluxo) - 1) * step_y - box_h - 0.5, box_h + 0.5)
ax.set_aspect("equal")
ax.axis("off")
fig.tight_layout()
fig.savefig("figuras/fig_arquitetura.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("Fluxograma gerado em figuras/fig_arquitetura.png")
