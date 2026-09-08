
import itertools
import math
import json
import streamlit as st
import pandas as pd

st.set_page_config(page_title="40K Team Pairings V10", page_icon="⚔️", layout="wide")

st.title("⚔️ 40K Team Pairings — V10")
st.caption("6 vs 6 · Army matchup + disposición · 720 combinaciones")

DEFAULT_MY = [
    ("Álvaro", "Aeldari", "Reconnaissance (R)"),
    ("Jugador 2", "Orks", "Purge the Foe (PF)"),
    ("Jugador 3", "Tau Empire", "Reconnaissance (R)"),
    ("Jugador 4", "Adeptus Custodes", "Disruption (D)"),
    ("Jugador 5", "Necrons", "Priority Assets (PA)"),
    ("Jugador 6", "Black Templars", "Take and Hold (TH)"),
]
DEFAULT_OPP = [
    ("Rival 1", "Space Marines", "Purge the Foe (PF)"),
    ("Rival 2", "Orks", "Reconnaissance (R)"),
    ("Rival 3", "Tau Empire", "Disruption (D)"),
    ("Rival 4", "Aeldari", "Priority Assets (PA)"),
    ("Rival 5", "Chaos Space Marines", "Take and Hold (TH)"),
    ("Rival 6", "Imperial Knights", "Reconnaissance (R)"),
]


# ============================================================
# GUARDAR / CARGAR EQUIPO
# ============================================================

with st.sidebar:
    st.header("💾 Mi equipo")
    st.caption("Guarda tus 6 jugadores para reutilizarlos en otro torneo o sesión.")
    uploaded_team = st.file_uploader("📂 Cargar equipo guardado", type=["json"], key="team_upload")
    if uploaded_team is not None and st.session_state.get("loaded_upload_name") != uploaded_team.name:
        try:
            payload = json.load(uploaded_team)
            players = payload.get("players", [])
            if len(players) != 6:
                st.error("El archivo no contiene exactamente 6 jugadores.")
            else:
                for i, pl in enumerate(players):
                    st.session_state[f"my_name_{i}"] = pl.get("name", f"Jugador {i+1}")
                    st.session_state[f"my_army_{i}"] = pl.get("army", DEFAULT_MY[i][1])
                    st.session_state[f"my_disp_{i}"] = pl.get("disposition", DEFAULT_MY[i][2])
                st.session_state["team_name"] = payload.get("team_name", "Mi equipo")
                st.session_state["loaded_upload_name"] = uploaded_team.name
                st.rerun()
        except Exception:
            st.error("No he podido leer ese archivo de equipo.")
    team_name = st.text_input("Nombre del equipo", value=st.session_state.get("team_name", "Mi equipo"), key="team_name")

    team_payload = {
        "team_name": team_name,
        "players": [
            {
                "name": st.session_state.get(f"my_name_{i}", DEFAULT_MY[i][0]),
                "army": st.session_state.get(f"my_army_{i}", DEFAULT_MY[i][1]),
                "disposition": st.session_state.get(f"my_disp_{i}", DEFAULT_MY[i][2]),
            } for i in range(6)
        ]
    }
    st.download_button(
        "💾 Guardar mi equipo",
        data=json.dumps(team_payload, ensure_ascii=False, indent=2),
        file_name=f"{team_name.strip() or 'mi_equipo'}.json",
        mime="application/json",
        use_container_width=True,
        help="Descarga un archivo con los 6 jugadores, armies y disposiciones para poder cargarlo otro día."
    )


# ============================================================
# CONFIGURACIÓN FIJA
# ============================================================

DISPOSITIONS = [
    "Take and Hold (TH)",
    "Purge the Foe (PF)",
    "Reconnaissance (R)",
    "Priority Assets (PA)",
    "Disruption (D)",
]

# Fuente proporcionada por el usuario.
# Escala original: 0–5.
# Para el modelo, 3.0 se considera el punto neutro.
DISPOSITION_SCORES = {
    ("Take and Hold (TH)", "Take and Hold (TH)"): 3.0,
    ("Take and Hold (TH)", "Purge the Foe (PF)"): 1.5,
    ("Take and Hold (TH)", "Reconnaissance (R)"): 3.0,
    ("Take and Hold (TH)", "Priority Assets (PA)"): 2.5,
    ("Take and Hold (TH)", "Disruption (D)"): 3.0,

    ("Purge the Foe (PF)", "Take and Hold (TH)"): 5.0,
    ("Purge the Foe (PF)", "Purge the Foe (PF)"): 3.0,
    ("Purge the Foe (PF)", "Reconnaissance (R)"): 3.0,
    ("Purge the Foe (PF)", "Priority Assets (PA)"): 3.0,
    ("Purge the Foe (PF)", "Disruption (D)"): 3.5,

    ("Reconnaissance (R)", "Take and Hold (TH)"): 3.5,
    ("Reconnaissance (R)", "Purge the Foe (PF)"): 2.5,
    ("Reconnaissance (R)", "Reconnaissance (R)"): 3.0,
    ("Reconnaissance (R)", "Priority Assets (PA)"): 4.0,
    ("Reconnaissance (R)", "Disruption (D)"): 4.0,

    ("Priority Assets (PA)", "Take and Hold (TH)"): 3.5,
    ("Priority Assets (PA)", "Purge the Foe (PF)"): 3.0,
    ("Priority Assets (PA)", "Reconnaissance (R)"): 3.0,
    ("Priority Assets (PA)", "Priority Assets (PA)"): 3.0,
    ("Priority Assets (PA)", "Disruption (D)"): 4.0,

    ("Disruption (D)", "Take and Hold (TH)"): 2.5,
    ("Disruption (D)", "Purge the Foe (PF)"): 1.5,
    ("Disruption (D)", "Reconnaissance (R)"): 2.0,
    ("Disruption (D)", "Priority Assets (PA)"): 2.0,
    ("Disruption (D)", "Disruption (D)"): 3.0,
}

ARMY_GROUPS = {
    "CHAOS": [
        "Chaos Daemons", "Chaos Knights", "Chaos Space Marines",
        "Death Guard", "Emperor's Children", "Thousand Sons", "World Eaters",
    ],
    "IMPERIUM": [
        "Adepta Sororitas", "Adeptus Custodes", "Adeptus Mechanicus",
        "Adeptus Titanicus", "Astra Militarum", "Grey Knights",
        "Imperial Agents", "Imperial Knights",
    ],
    "SPACE MARINES": [
        "Black Templars", "Blood Angels", "Dark Angels", "Deathwatch",
        "Imperial Fists", "Iron Hands", "Raven Guard", "Salamanders",
        "Space Marines", "Space Wolves", "Ultramarines", "White Scars",
    ],
    "XENOS": [
        "Aeldari", "Drukhari", "Genestealer Cults", "Leagues of Votann",
        "Necrons", "Orks", "Tau Empire", "Tyranids",
    ],
}
ALL_ARMIES = [a for group in ARMY_GROUPS.values() for a in group]

# ============================================================
# MODELO
# ============================================================

def probability_from_score(score):
    # Modelo experimental. 0 = 50%.
    # El score total está limitado para evitar extremos artificiales.
    score = max(-6.5, min(6.5, score))
    return 1.0 / (1.0 + math.exp(-0.45 * score))

def calculate_pairing(me, opp, army_scores):
    army_score = army_scores.get((me["army"], opp["army"]), 0.0)

    # La fuente de disposiciones está en 0–5.
    # 3.0 es el valor neutro, por lo que transformamos:
    # 5 -> +2, 3 -> 0, 1.5 -> -1.5, etc.
    raw_disp = DISPOSITION_SCORES[
        (me["disposition"], opp["disposition"])
    ]
    disposition_modifier = raw_disp - 3.0

    total_score = army_score + disposition_modifier
    probability = probability_from_score(total_score)

    return {
        "probability": probability,
        "army_score": army_score,
        "raw_disposition": raw_disp,
        "disposition_modifier": disposition_modifier,
        "total_score": total_score,
    }

def result_distribution(probabilities):
    dp = [1.0] + [0.0] * 6
    for p in probabilities:
        new = [0.0] * 7
        for wins in range(7):
            if dp[wins] == 0:
                continue
            new[wins] += dp[wins] * (1 - p)
            if wins < 6:
                new[wins + 1] += dp[wins] * p
        dp = new
    return dp

def evaluate_all_pairings(my_players, opp_players, army_scores):
    results = []

    for permutation in itertools.permutations(opp_players):
        pairs = []
        probabilities = []

        for me, opp in zip(my_players, permutation):
            result = calculate_pairing(me, opp, army_scores)
            p = result["probability"]
            probabilities.append(p)

            pairs.append({
                "Nuestro jugador": me["name"],
                "Nuestro army": me["army"],
                "Nuestra disposición": me["disposition"],
                "Rival": opp["name"],
                "Rival army": opp["army"],
                "Rival disposición": opp["disposition"],
                "Army": round(result["army_score"], 2),
                "Disp. base (0-5)": round(result["raw_disposition"], 2),
                "Disp. modificador": round(result["disposition_modifier"], 2),
                "Score total": round(result["total_score"], 2),
                "Victoria %": round(p * 100, 1),
            })

        distribution = result_distribution(probabilities)

        results.append({
            "pairs": pairs,
            "expected_wins": sum(probabilities),
            "p_3plus": sum(distribution[3:]),
            "p_4plus": sum(distribution[4:]),
            "p_5plus": sum(distribution[5:]),
        })

    return results

def sort_results(results, objective):
    if objective == "Maximizar victorias esperadas":
        return sorted(
            results,
            key=lambda x: (x["expected_wins"], x["p_3plus"], x["p_4plus"]),
            reverse=True
        )
    if objective == "Maximizar 4-2 o mejor":
        return sorted(
            results,
            key=lambda x: (x["p_4plus"], x["expected_wins"], x["p_3plus"]),
            reverse=True
        )
    return sorted(
        results,
        key=lambda x: (x["p_3plus"], x["expected_wins"], x["p_4plus"]),
        reverse=True
    )


# ============================================================
# ASISTENTE DE PAIRING POR CARTAS
# ============================================================

def assistant_probability(me, opp, army_scores):
    return calculate_pairing(me, opp, army_scores)["probability"]

def assistant_best_completion(ours, rivals, army_scores):
    if not ours or not rivals:
        return {"expected_wins": 0.0, "p_3plus": 0.0, "p_4plus": 0.0}
    best = None
    for perm in itertools.permutations(rivals):
        probs = [assistant_probability(me, op, army_scores) for me, op in zip(ours, perm)]
        dist = result_distribution(probs)
        cand = (sum(probs), sum(dist[3:]), sum(dist[4:]))
        if best is None or cand > best[0]:
            best = (cand, list(zip(ours, perm)))
    return {"expected_wins": best[0][0], "p_3plus": best[0][1], "p_4plus": best[0][2], "pairs": best[1]}

def assistant_choose_opening(ours, rivals, army_scores):
    out = []
    for me in ours:
        worst = min(max(assistant_probability(me, a, army_scores), assistant_probability(me, b, army_scores)) for a,b in itertools.combinations(rivals, 2))
        out.append((worst, me))
    return sorted(out, key=lambda x: x[0], reverse=True)

def assistant_counter_options(ours, rival_card, remaining_rivals, army_scores):
    out = []
    for pair in itertools.combinations(ours, 2):
        immediate = min(assistant_probability(pair[0], rival_card, army_scores), assistant_probability(pair[1], rival_card, army_scores))
        rest = [p for p in ours if p not in pair]
        completion = assistant_best_completion(rest, remaining_rivals, army_scores)
        out.append((immediate + completion["expected_wins"], immediate, completion, pair))
    return sorted(out, reverse=True, key=lambda x: (x[0], x[2]["p_3plus"], x[2]["p_4plus"]))


def assistant_choose_rival_for_offered(our_offered, rival_pair, our_counter_pair, received_rival, remaining_ours_after_round, remaining_rivals_after_round, army_scores):
    """Recomienda cuál de las 2 cartas rivales elegir contra nuestra carta ofrecida.
    Evalúa el impacto global y, para la otra pareja, toma el peor de los dos cruces
    posibles porque todavía no sabemos cuál elegirá el rival de nuestras 2 cartas.
    """
    out = []
    for chosen_rival in rival_pair:
        other_rival = rival_pair[1] if chosen_rival is rival_pair[0] else rival_pair[0]
        p_offered = assistant_probability(our_offered, chosen_rival, army_scores)
        # La otra carta rival de la pareja vuelve a la mano.
        rivals_after = list(remaining_rivals_after_round) + [other_rival]
        # Para nuestras 2 cartas contra la carta recibida, el rival elegirá la peor para nosotros.
        p_second = min(
            assistant_probability(our_counter_pair[0], received_rival, army_scores),
            assistant_probability(our_counter_pair[1], received_rival, army_scores)
        )
        # Una de nuestras dos se cierra en la segunda pareja; conservadoramente
        # consideramos la que deja la mejor continuación entre ambas posibilidades.
        continuation_candidates = []
        for chosen_our in our_counter_pair:
            other_our = our_counter_pair[1] if chosen_our is our_counter_pair[0] else our_counter_pair[0]
            ours_after = list(remaining_ours_after_round) + [other_our]
            completion = assistant_best_completion(ours_after, rivals_after, army_scores)
            continuation_candidates.append(completion)
        best_cont = max(continuation_candidates, key=lambda c: (c["expected_wins"], c["p_3plus"], c["p_4plus"]))
        total = p_offered + p_second + best_cont["expected_wins"]
        out.append((total, p_offered, p_second, best_cont, chosen_rival))
    return sorted(out, reverse=True, key=lambda x: (x[0], x[1], x[3]["p_3plus"], x[3]["p_4plus"]))

def army_select(label, key, default):
    index = ALL_ARMIES.index(default) if default in ALL_ARMIES else 0
    return st.selectbox(label, ALL_ARMIES, index=index, key=key)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Objetivo del algoritmo")
    objective = st.selectbox(
        "Ordenar resultados por",
        [
            "Maximizar 3-3 o mejor",
            "Maximizar victorias esperadas",
            "Maximizar 4-2 o mejor",
        ]
    )

    st.divider()
    st.subheader("Disposiciones")
    st.write("La valoración procede de la tabla incorporada en el programa.")
    st.write("3.0 = neutro para el cálculo.")
    st.caption("No es necesario introducirlas manualmente.")

# ============================================================
# NUESTRO EQUIPO
# ============================================================

st.header("1️⃣ Nuestro equipo — 6 jugadores")

my_players = []
cols = st.columns(2)

for i, default in enumerate(DEFAULT_MY):
    with cols[i % 2]:
        st.subheader(f"Jugador {i + 1}")

        name = st.text_input(
            "Nombre",
            default[0],
            key=f"my_name_{i}"
        )

        army = army_select(
            "Army",
            f"my_army_{i}",
            default[1]
        )

        disposition = st.selectbox(
            "Disposición",
            DISPOSITIONS,
            index=DISPOSITIONS.index(default[2]),
            key=f"my_disp_{i}"
        )

        my_players.append({
            "name": name,
            "army": army,
            "disposition": disposition,
        })

# ============================================================
# RIVAL
# ============================================================

st.header("2️⃣ Equipo rival — 6 jugadores")

opp_players = []
cols = st.columns(2)

for i, default in enumerate(DEFAULT_OPP):
    with cols[i % 2]:
        st.subheader(f"Rival {i + 1}")

        name = st.text_input(
            "Nombre",
            default[0],
            key=f"opp_name_{i}"
        )

        army = army_select(
            "Army",
            f"opp_army_{i}",
            default[1]
        )

        disposition = st.selectbox(
            "Disposición",
            DISPOSITIONS,
            index=DISPOSITIONS.index(default[2]),
            key=f"opp_disp_{i}"
        )

        opp_players.append({
            "name": name,
            "army": army,
            "disposition": disposition,
        })

# ============================================================
# ARMY MATCHUP
# ============================================================

st.header("3️⃣ Valoración Army vs Army")

st.write(
    "Aquí solamente introducimos vuestro conocimiento del matchup. "
    "−5 = muy malo · 0 = neutro · +5 = muy bueno."
)

my_armies = sorted(set(p["army"] for p in my_players))
opp_armies = sorted(set(p["army"] for p in opp_players))

army_scores = {}

for ma in my_armies:
    st.markdown(f"**{ma}**")
    row = st.columns(len(opp_armies))

    for j, oa in enumerate(opp_armies):
        army_scores[(ma, oa)] = row[j].number_input(
            oa,
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.5,
            key=f"army_score_{ma}_{oa}"
        )

# ============================================================
# DISPOSITION MATRIX - SOLO LECTURA
# ============================================================

st.header("4️⃣ Valoración de disposiciones")
st.caption(
    "Fuente incorporada: 0–5. Para el cálculo, 3.0 es el punto neutro."
)

disp_table = pd.DataFrame(
    [
        [
            DISPOSITION_SCORES[(mine, theirs)]
            for theirs in DISPOSITIONS
        ]
        for mine in DISPOSITIONS
    ],
    index=DISPOSITIONS,
    columns=DISPOSITIONS
)
st.dataframe(disp_table, use_container_width=True)


# ============================================================
# ASISTENTE — FLUJO REAL DE CARTAS (V8: RONDA 1 + RONDA 2)
# ============================================================

st.markdown("---")
st.header("🎴 Asistente de pairing por cartas")
st.info("El asistente acompaña el pairing real por rondas. Primero calcula la salida con 6 cartas; después registra lo que realmente ha ocurrido y recalcula desde las 4 cartas restantes. La recomendación de salida es conservadora: no puede conocer las decisiones ocultas del rival.")

if len(my_players) == 6 and len(opp_players) == 6:
    # ---------- helpers de estado ----------
    def reset_assistant():
        for k in list(st.session_state.keys()):
            if k.startswith("pa_"):
                del st.session_state[k]
        st.session_state["pa_ours"] = list(range(6))
        st.session_state["pa_rivals"] = list(range(6))
        st.session_state["pa_round"] = 1
        st.session_state["pa_closed"] = []

    if "pa_ours" not in st.session_state or "pa_rivals" not in st.session_state:
        reset_assistant()

    if st.button("🔄 Reiniciar asistente de pairing", use_container_width=True):
        reset_assistant()
        st.rerun()

    def cards(indices, players):
        return [players[i] for i in indices]

    def choose_opening_for_indices(our_indices, rival_indices):
        ours = cards(our_indices, my_players)
        rivals = cards(rival_indices, opp_players)
        return assistant_choose_opening(ours, rivals, army_scores)

    round_no = st.session_state["pa_round"]
    our_ids = st.session_state["pa_ours"]
    rival_ids = st.session_state["pa_rivals"]

    st.subheader(f"🃏 Ronda {round_no} — {len(our_ids)} cartas restantes")

    # Tras cerrar la ronda 2 quedan 2 cartas. V8 no simula la ronda final:
    # no intentamos calcular recomendaciones con una cantidad de cartas no soportada.
    if round_no > 2:
        st.success("### ✅ Rondas 1 y 2 completadas")
        st.write(f"**Nuestras 2 cartas restantes:** {', '.join(my_players[i]['name'] for i in st.session_state['pa_ours'])}")
        st.write(f"**Sus 2 cartas restantes:** {', '.join(opp_players[i]['army'] for i in st.session_state['pa_rivals'])}")
        st.info("La ronda final 2→1 se añadirá más adelante. Por ahora el asistente termina aquí sin mostrar errores ni recomendaciones adicionales.")
    else:
        # ==================== RONDA ACTIVA ====================
        opening = choose_opening_for_indices(our_ids, rival_ids)
        first = opening[0][1]
        first_idx = my_players.index(first)

        st.success(f"### 🎯 CARTA RECOMENDADA PARA SALIR: {first['name']} — {first['army']} · {first['disposition']}")
        with st.expander("Ver las cartas ordenadas para salir"):
            st.dataframe(pd.DataFrame([
                {"#": i+1, "Jugador": me["name"], "Army": me["army"], "Disposición": me["disposition"], "Peor caso": f"{score*100:.1f}%"}
                for i, (score, me) in enumerate(opening)
            ]), use_container_width=True, hide_index=True)

        # En la ronda 1 el ofrecido debe ser la recomendación; en la ronda 2 también se puede cambiar manualmente.
        offer_options = [i for i in our_ids]
        offer_idx = st.selectbox(
            "1️⃣ ¿Qué carta nuestra entregamos al rival?",
            offer_options,
            index=offer_options.index(first_idx) if first_idx in offer_options else 0,
            format_func=lambda i: f"{my_players[i]['name']} — {my_players[i]['army']} · {my_players[i]['disposition']}",
            key=f"pa_offer_{round_no}"
        )
        offered_ours = my_players[offer_idx]

        rival_labels = [f"{opp_players[i]['name']} — {opp_players[i]['army']} · {opp_players[i]['disposition']}" for i in rival_ids]
        receive_idx = st.selectbox(
            "2️⃣ ¿Qué carta nos entrega el rival?",
            rival_ids,
            format_func=lambda i: f"{opp_players[i]['name']} — {opp_players[i]['army']} · {opp_players[i]['disposition']}",
            key=f"pa_receive_{round_no}"
        )
        received_rival = opp_players[receive_idx]

        our_remaining = [i for i in our_ids if i != offer_idx]
        rival_remaining = [i for i in rival_ids if i != receive_idx]

        # El asistente recomienda las 2 mejores, pero NO las selecciona por nosotros.
        # El jugador debe introducir manualmente la decisión real tomada en mesa.
        st.subheader(f"3️⃣ Nuestras 2 cartas contra {received_rival['army']}")
        our_remaining_cards = cards(our_remaining, my_players)
        rival_remaining_cards = cards(rival_remaining, opp_players)
        options = assistant_counter_options(our_remaining_cards, received_rival, rival_remaining_cards, army_scores)

        if options:
            recommended_pair = options[0][3]
            rec_names = " + ".join(c["name"] for c in recommended_pair)
            st.success(f"### 🎯 Te recomiendo poner: {rec_names}")
            st.caption("Es una recomendación del modelo. Tú debes seleccionar manualmente las 2 cartas que realmente vais a poner en mesa.")

        our_pair_indices = st.multiselect(
            "Selecciona manualmente exactamente 2 de nuestras cartas",
            our_remaining,
            max_selections=2,
            default=[],
            format_func=lambda i: f"{my_players[i]['name']} — {my_players[i]['army']} · {my_players[i]['disposition']}",
            key=f"pa_our_pair_{round_no}"
        )

        if len(our_pair_indices) < 2:
            st.info("👆 Selecciona las 2 cartas que habéis decidido poner para continuar.")
            st.stop()

        selected_pair = [my_players[i] for i in our_pair_indices]
        selected_key = frozenset(c['name'] for c in selected_pair)
        selected_option = next((o for o in options if frozenset(c['name'] for c in o[3]) == selected_key), None)

        if selected_option is not None:
            rank = next(i for i, o in enumerate(options, 1) if o is selected_option)
            if rank == 1:
                st.success("### ✅ Buena elección: tus 2 cartas son la opción mejor valorada por el asistente.")
            else:
                st.info(f"### 📊 Tu elección queda en la posición #{rank} de {len(options)} según el modelo.")
            st.caption(f"Resultado conservador de esta elección: {selected_option[1]*100:.1f}% en el cruce inmediato; continuación esperada: {selected_option[2]['expected_wins']:.2f} victorias.")
        else:
            st.warning("No se ha podido valorar la pareja seleccionada.")

        with st.expander("🔎 Comparar con las demás parejas posibles"):
            st.dataframe(pd.DataFrame([
                {"#": i+1, "Carta 1": o[3][0]["name"], "Carta 2": o[3][1]["name"], "Mínimo inmediato": f"{o[1]*100:.1f}%", "Equipo restante (esperado)": f"{o[2]['expected_wins']:.2f}"}
                for i, o in enumerate(options)
            ]), use_container_width=True, hide_index=True)

        st.subheader("4️⃣ Se revelan las 2 cartas que ellos han puesto contra nuestra carta ofrecida")
        if len(rival_remaining) >= 2:
            rival_pair_indices = st.multiselect(
                "Selecciona las 2 cartas RIVALES que han puesto contra nuestra carta",
                rival_remaining,
                max_selections=2,
                format_func=lambda i: f"{opp_players[i]['name']} — {opp_players[i]['army']} · {opp_players[i]['disposition']}",
                key=f"pa_rival_pair_{round_no}"
            )
        else:
            rival_pair_indices = rival_remaining
            st.info("Quedan 2 cartas rivales: ambas son las que se revelan.")

        if len(rival_pair_indices) == 2:
            rival_pair_cards = [opp_players[i] for i in rival_pair_indices]
            remaining_ours_after_round_base = [my_players[i] for i in our_remaining if i not in our_pair_indices]
            remaining_rivals_after_round_base = [opp_players[i] for i in rival_remaining if i not in rival_pair_indices]
            rival_choice_options = assistant_choose_rival_for_offered(
                offered_ours,
                rival_pair_cards,
                [my_players[i] for i in our_pair_indices],
                received_rival,
                remaining_ours_after_round_base,
                remaining_rivals_after_round_base,
                army_scores
            )
            recommended_rival = rival_choice_options[0][4]
            recommended_rival_idx = rival_pair_indices[rival_pair_cards.index(recommended_rival)]

            st.subheader("5️⃣ Elegimos cuál de sus 2 cartas enfrenta a la nuestra")
            st.success(f"### 🎯 Te recomiendo elegir: {recommended_rival['name']} — {recommended_rival['army']} · {recommended_rival['disposition']}")
            st.caption("La recomendación busca el mejor resultado global del equipo, teniendo en cuenta las cartas que quedarían disponibles.")
            chosen_rival_idx = st.radio(
                "¿Cuál elegimos contra nuestra carta ofrecida?",
                rival_pair_indices,
                index=rival_pair_indices.index(recommended_rival_idx),
                format_func=lambda i: f"{opp_players[i]['name']} — {opp_players[i]['army']} · {opp_players[i]['disposition']}",
                key=f"pa_chosen_rival_{round_no}"
            )
            with st.expander("🔎 Comparar las 2 opciones"):
                st.dataframe(pd.DataFrame([
                    {
                        "Opción": "⭐ RECOMENDADA" if x[4] is recommended_rival else "Alternativa",
                        "Carta rival": x[4]["army"],
                        "Cruce ofrecida": f"{x[1]*100:.1f}%",
                        "Equipo proyectado": f"{x[0]:.2f} victorias esperadas"
                    } for x in rival_choice_options
                ]), use_container_width=True, hide_index=True)

            st.subheader("6️⃣ Registramos cuál de nuestras 2 han elegido ellos")
            chosen_our_idx = st.radio(
                "¿Cuál de nuestras 2 cartas han elegido contra su carta ofrecida?",
                our_pair_indices,
                format_func=lambda i: f"{my_players[i]['name']} — {my_players[i]['army']} · {my_players[i]['disposition']}",
                key=f"pa_chosen_our_{round_no}"
            )

            if st.button(f"⚔️ CERRAR RONDA {round_no} Y CALCULAR LA SIGUIENTE", type="primary", use_container_width=True, key=f"pa_close_{round_no}"):
                # Se cierran exactamente dos pairings: carta ofrecida vs carta rival elegida,
                # y carta nuestra elegida por ellos vs carta rival que recibimos.
                closed = [
                    (offered_ours, opp_players[chosen_rival_idx]),
                    (my_players[chosen_our_idx], received_rival)
                ]
                st.session_state["pa_closed"] = st.session_state.get("pa_closed", []) + closed

                # Las cartas que no fueron elegidas en los cruces vuelven a la mano.
                used_ours = {offer_idx, chosen_our_idx}
                used_rivals = {receive_idx, chosen_rival_idx}
                st.session_state["pa_ours"] = [i for i in our_ids if i not in used_ours]
                st.session_state["pa_rivals"] = [i for i in rival_ids if i not in used_rivals]
                st.session_state["pa_round"] = round_no + 1
                st.rerun()

    # ==================== HISTORIAL ====================
    if st.session_state.get("pa_closed"):
        st.markdown("---")
        st.subheader("📋 Pairings ya cerrados")
        for n, (me, op) in enumerate(st.session_state["pa_closed"], 1):
            st.write(f"**{n}. {me['name']}** ({me['army']} · {me['disposition']})  ⚔️  **{op['army']}** ({op['disposition']})")

else:
    st.warning("Configura los 6 jugadores de cada equipo para activar el asistente.")


# ============================================================
# CALCULAR
# ============================================================

st.header("5️⃣ Buscar el pairing óptimo")

if st.button(
    "🚀 CALCULAR LOS 720 PAIRINGS",
    type="primary",
    use_container_width=True
):
    with st.spinner("Calculando 720 combinaciones..."):
        st.session_state["results"] = evaluate_all_pairings(
            my_players,
            opp_players,
            army_scores
        )

if "results" in st.session_state:
    results = sort_results(st.session_state["results"], objective)
    best = results[0]

    # ========================================================
    # RESULTADO — FORMATO "HOJA DE PAIRING"
    # ========================================================
    st.markdown("---")
    st.header("🏆 Pairing recomendado")
    st.caption("La combinación que mejor encaja con el objetivo seleccionado.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Victorias esperadas", f'{best["expected_wins"]:.2f} / 6')
    c2.metric("3-3 o mejor", f'{best["p_3plus"] * 100:.1f}%')
    c3.metric("4-2 o mejor", f'{best["p_4plus"] * 100:.1f}%')

    st.markdown("### ⚔️ Los 6 enfrentamientos")

    # Tarjetas grandes, pensadas para leerlas rápidamente en una tablet.
    for i, p in enumerate(best["pairs"], 1):
        with st.container(border=True):
            left, mid, right = st.columns([4, 1, 4])
            with left:
                st.markdown(f"**{p['Nuestro jugador']}**")
                st.caption(f"{p['Nuestro army']} · {p['Nuestra disposición']}")
            with mid:
                st.markdown("### ⚔️")
            with right:
                st.markdown(f"**{p['Rival army']}**")
                st.caption(f"Disposición rival · {p['Rival disposición']}")

            st.progress(
                p["Victoria %"] / 100,
                text=f"Probabilidad de victoria: {p['Victoria %']:.1f}%"
            )
            st.caption(
                f"Army {p['Army']:+.1f} · "
                f"Disposición {p['Disp. base (0-5)']:.1f} "
                f"({p['Disp. modificador']:+.1f}) · "
                f"Score total {p['Score total']:+.1f}"
            )

    with st.expander("📋 Ver detalle numérico del pairing"):
        detail_df = pd.DataFrame(best["pairs"]).drop(columns=["Rival"], errors="ignore")
        st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # ========================================================
    # ALTERNATIVAS
    # ========================================================
    st.markdown("### 🔄 Otras opciones fuertes")
    st.caption("No son simples números de combinación: aquí puedes ver exactamente qué cambia en cada pairing.")

    for rank, result in enumerate(results[1:4], 2):
        with st.expander(
            f"Opción {rank} · {result['expected_wins']:.2f} victorias esperadas · "
            f"{result['p_3plus'] * 100:.1f}% de 3-3+"
        ):
            for i, p in enumerate(result["pairs"], 1):
                st.write(
                    f"**{i}. {p['Nuestro jugador']} → {p['Rival army']}** "
                    f"· {p['Nuestro army']} vs {p['Rival army']} · "
                    f"**{p['Victoria %']:.1f}%**"
                )

    # ========================================================
    # MATRIZ — ANÁLISIS AVANZADO
    # ========================================================
    st.markdown("### 📊 Análisis avanzado")

    with st.expander("Ver matriz 6×6 de enfrentamientos"):
        matrix = pd.DataFrame(
            index=[
                f"{p['name']} — {p['army']} — {p['disposition']}"
                for p in my_players
            ],
            columns=[
                f"{p['army']} — {p['disposition']}"
                for p in opp_players
            ],
            dtype=float
        )

        for me in my_players:
            for opp in opp_players:
                r = calculate_pairing(me, opp, army_scores)
                matrix.loc[
                    f"{me['name']} — {me['army']} — {me['disposition']}",
                    f"{opp['army']} — {opp['disposition']}"
                ] = round(r["probability"] * 100, 1)

        st.dataframe(matrix, use_container_width=True)

    with st.expander("ℹ️ Cómo interpretar los resultados"):
        st.info(
            "Importante: los porcentajes actuales son una primera aproximación matemática. "
            "La tabla de disposiciones ya está fijada con la fuente proporcionada; "
            "lo que iremos calibrando será principalmente cómo convertir vuestra "
            "valoración Army vs Army en probabilidades reales."
        )
