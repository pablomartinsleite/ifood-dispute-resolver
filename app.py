"""
iFood Dispute Resolver - Aplicação Streamlit
Interface com visualização em duas colunas (Wide Layout):
- Coluna Esquerda: App do Cliente (Seleção de pedido mock, resumo de itens, relato do problema, upload de foto e chat interativo)
- Coluna Direita: Painel Interno AI Builder / Observabilidade (Métricas em cards, regra_aplicada em destaque, justificativa_interna e JSON estruturado Pydantic)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

# Importações do resolvedor de disputas
try:
    from agent_resolver import (
        MODELOS_PREFERENCIAIS,
        PEDIDOS_MOCK_PATH,
        analisar_disputa,
        carregar_pedido,
    )
except ImportError:
    st.error("Erro ao importar o módulo 'agent_resolver.py'. Certifique-se de que o arquivo está no diretório correto.")
    st.stop()

# ==============================================================================
# Configuração da Página Streamlit (Layout Wide)
# ==============================================================================
st.set_page_config(
    page_title="iFood Dispute Resolver | AI CX & Observabilidade",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização visual inspirada no Design System do iFood
st.markdown(
    """
    <style>
    /* Cabeçalho principal iFood */
    .ifood-banner {
        background: linear-gradient(135deg, #EA1D2C 0%, #C41221 100%);
        padding: 1.25rem 1.8rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(234, 29, 44, 0.22);
    }
    .ifood-banner h1 {
        color: #FFFFFF !important;
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .ifood-banner p {
        color: #FFE5E7;
        margin: 5px 0 0 0;
        font-size: 0.95rem;
    }

    /* Box destacado para a regra aplicada */
    .regra-box-highlight {
        background-color: #EFF6FF;
        border: 1.5px solid #3B82F6;
        border-left: 6px solid #1D4ED8;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 0.8rem;
        margin-bottom: 1rem;
    }
    .regra-box-title {
        font-size: 0.88rem;
        font-weight: 700;
        color: #1E40AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .regra-box-body {
        color: #1E3A8A;
        font-size: 0.96rem;
        line-height: 1.5;
        font-weight: 500;
    }

    /* Box para a justificativa interna */
    .justificativa-box {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-left: 6px solid #0EA5E9;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 1rem;
        color: #1E293B;
        font-size: 0.93rem;
        line-height: 1.55;
    }
    .justificativa-title {
        font-size: 0.88rem;
        font-weight: 700;
        color: #0369A1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Estilo de lista de itens */
    .item-pill {
        display: inline-block;
        background-color: #F1F5F9;
        border: 1px solid #E2E8F0;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 2px 4px 2px 0;
        color: #334155;
    }

    /* Correção global para nunca truncar st.metric no Streamlit */
    div[data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    div[data-testid="stMetricValue"] > div {
        overflow: visible !important;
        text-overflow: unset !important;
        white-space: normal !important;
        font-size: 1.3rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    div[data-testid="stMetricLabel"] > div {
        overflow: visible !important;
        text-overflow: unset !important;
        white-space: normal !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
        white-space: normal !important;
    }

    /* Cards customizados para Telemetria e Perfil de Risco */
    .kpi-row {
        display: flex;
        gap: 12px;
        margin: 12px 0 16px 0;
        flex-wrap: wrap;
    }
    .kpi-card-box {
        flex: 1;
        min-width: 130px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 14px;
        text-align: left;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    @media (prefers-color-scheme: dark) {
        .kpi-card-box {
            background: #1E293B;
            border-color: #334155;
        }
    }
    .kpi-card-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .kpi-card-value {
        font-size: 1.4rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 6px;
    }
    .kpi-card-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def carregar_todos_pedidos() -> List[Dict[str, Any]]:
    """Carrega os pedidos a partir do arquivo pedidos_mock.json."""
    if not PEDIDOS_MOCK_PATH.exists():
        st.error(f"Arquivo não encontrado: {PEDIDOS_MOCK_PATH}")
        return []
    with open(PEDIDOS_MOCK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# Carregamento da base mock de pedidos
pedidos = carregar_todos_pedidos()

# ==============================================================================
# Barra Lateral (Controles de IA e Guia)
# ==============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Configurações IA")

    # Seleção do Modelo Gemini
    modelo_selecionado = st.selectbox(
        "Modelo Gemini Preferencial:",
        options=MODELOS_PREFERENCIAIS,
        index=0,
        help="Modelo padrão gemini-2.5-flash com fallback resiliente.",
    )

    # Checagem da API Key
    api_key_env = os.getenv("GEMINI_API_KEY")
    if api_key_env:
        st.success("GEMINI_API_KEY configurada", icon="🔑")
    else:
        st.warning("GEMINI_API_KEY não detectada no .env", icon="⚠️")
        nova_chave = st.text_input(
            "Insira sua GEMINI_API_KEY:",
            type="password",
            placeholder="AIzaSy...",
            help="Sua chave de API do Google Gemini Studio.",
        )
        if nova_chave:
            os.environ["GEMINI_API_KEY"] = nova_chave.strip()
            st.success("Chave temporária salva para esta execução!")

    st.divider()

    st.markdown("### 📋 Cenários de Teste Mock")
    st.markdown(
        """
        - **IFD-8921**: Item Faltando *(Mariana - McDonald's)*
        - **IFD-4412**: Atraso de 58min + Pizza Fria *(Carlos)*
        - **IFD-9930**: Embalagem Violada *(Lucas - Churrascaria)*
        - **IFD-6209**: Pedido Errado *(Beatriz - Sushi)*
        - **IFD-7781**: Prompt Injection *(Thiago - Smash Burger)*
        """
    )

    st.divider()
    if st.button("🔄 Reiniciar Sessão", use_container_width=True):
        st.session_state.pop("resultado_disputa", None)
        st.session_state.pop("chat_history", None)
        st.rerun()


# ==============================================================================
# Cabeçalho da Aplicação
# ==============================================================================
st.markdown(
    """
    <div class="ifood-banner">
        <h1>🍔 iFood Dispute Resolver</h1>
        <p>Resolução Autônoma de Disputas de Pedidos com IA Multimodal, Prevenção de Fraudes e Observabilidade em Tempo Real</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Inicialização dos estados na sessão
if "resultado_disputa" not in st.session_state:
    st.session_state["resultado_disputa"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ==============================================================================
# Divisão da Tela: Duas Colunas Principais (Esquerda: Cliente | Direita: Painel)
# ==============================================================================
col_cliente, col_interno = st.columns([1, 1], gap="large")


# ==============================================================================
# COLUNA ESQUERDA: APP DO CLIENTE
# ==============================================================================
with col_cliente:
    st.markdown("### 📱 Aplicativo do Cliente (Central de Ajuda)")
    st.caption("Interface do consumidor para reporte de incidentes pós-entrega.")

    if not pedidos:
        st.error("Não foram encontrados pedidos no arquivo pedidos_mock.json.")
        st.stop()

    def formatar_opcao_pedido(p: Dict[str, Any]) -> str:
        itens_txt = ", ".join(f"{it['quantidade']}x {it['nome']}" for it in p.get("itens", []))
        total = p.get("pagamento", {}).get("valor_total", 0.0)
        return f"{p['id_pedido']} • {p['restaurante']['nome']} (R$ {total:.2f}) — {itens_txt}"

    # 1. Seletor de pedidos
    pedido_selecionado = st.selectbox(
        "Selecione o pedido com problema:",
        options=pedidos,
        format_func=formatar_opcao_pedido,
        key="pedido_selecionado_widget",
    )

    pedido_id = pedido_selecionado["id_pedido"]
    dados_restaurante = pedido_selecionado.get("restaurante", {})
    dados_cliente = pedido_selecionado.get("cliente", {})
    dados_pagamento = pedido_selecionado.get("pagamento", {})
    itens_pedido = pedido_selecionado.get("itens", [])
    disputa_mock = pedido_selecionado.get("disputa", {})

    # Card com Resumo Detalhado dos Itens do Pedido
    with st.container(border=True):
        st.markdown(f"**🏪 {dados_restaurante.get('nome')}**")
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            st.caption(f"👤 **Cliente:** {dados_cliente.get('nome')}")
            st.caption(f"📅 **Data:** {pedido_selecionado.get('data_pedido', '')[:16].replace('T', ' ')}")
        with c_sub2:
            st.caption(f"💳 **Total Pago:** R$ {dados_pagamento.get('valor_total', 0.0):.2f}")
            st.caption(f"🏷️ **Status:** `{pedido_selecionado.get('status', 'concluído')}`")

        st.markdown("**Resumo dos Itens:**")
        for item in itens_pedido:
            st.markdown(
                f"- **{item['quantidade']}x** {item['nome']} "
                f"<span style='color: #64748B;'>— R$ {item['preco_unitario']:.2f} cada</span>",
                unsafe_allow_html=True,
            )

    # 2. Caixa de texto para o cliente relatar o problema
    texto_padrao = disputa_mock.get("descricao_cliente", "")
    relato_cliente = st.text_area(
        "Descreva o problema ocorrido com o pedido:",
        value=texto_padrao,
        key=f"relato_area_{pedido_id}",
        height=125,
        help="Você pode editar este texto livremente ou digitar uma nova reclamação.",
    )

    # 3. Componente file_uploader para anexar foto do pedido
    foto_upload = st.file_uploader(
        "📷 Anexar foto do pedido (evidência da entrega / itens recebidos):",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"foto_uploader_{pedido_id}",
        help="Opcional: anexe imagem para comprovar itens faltantes, violação ou troca de sacola.",
    )

    if foto_upload:
        st.image(
            foto_upload,
            caption="Evidência anexada pelo cliente",
            width=250,
        )

    # 4. Botão 'Enviar Reclamação'
    btn_enviar = st.button("Enviar Reclamação", type="primary", use_container_width=True)

    if btn_enviar:
        if not relato_cliente.strip():
            st.warning("Por favor, relate o problema antes de enviar a reclamação.")
        else:
            imagem_bytes = foto_upload.getvalue() if foto_upload else None

            with st.spinner("🤖 O Agente Autônomo está analisando as políticas e evidências..."):
                try:
                    resultado = analisar_disputa(
                        pedido_id=pedido_id,
                        relato_cliente=relato_cliente,
                        imagem_bytes=imagem_bytes,
                        modelo_preferencial=modelo_selecionado,
                    )
                    st.session_state["resultado_disputa"] = resultado
                    st.session_state["chat_history"] = [
                        {
                            "role": "user",
                            "content": relato_cliente,
                            "has_image": bool(imagem_bytes),
                        },
                        {
                            "role": "assistant",
                            "content": resultado["decisao"]["resposta_cliente"],
                            "acao": resultado["decisao"]["acao_tomada"],
                            "valor": resultado["decisao"]["valor_reembolso"],
                        },
                    ]
                except Exception as err:
                    st.error(f"Erro ao processar análise da disputa: {err}")

    # 5. Exibição da resposta_cliente em formato de chat amigável
    if st.session_state["chat_history"]:
        st.divider()
        st.markdown("#### 💬 Atendimento iFood")

        for msg in st.session_state["chat_history"]:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
                    if msg.get("has_image"):
                        st.caption("📎 *Foto de evidência anexada.*")
            else:
                with st.chat_message("assistant", avatar="🍔"):
                    st.write(msg["content"])

                    # Feedback visual complementar baseado no desfecho
                    acao = msg.get("acao", "")
                    valor = msg.get("valor", 0.0)
                    if acao in ["Reembolso Total", "Reembolso Parcial"] and valor > 0:
                        st.success(f"💳 Reembolso de **R$ {valor:.2f}** concedido com sucesso!")
                    elif acao == "Cupom" and valor > 0:
                        st.info(f"🎟️ Cupom de compensação de **R$ {valor:.2f}** adicionado à sua conta!")
                    elif acao == "Escalar Humano":
                        st.warning("👨‍💼 Caso transferido com prioridade para a equipe humana de atendimento.")
                    elif acao == "Negado":
                        st.error("Desfecho: Solicitação indeferida segundo os termos de serviço.")


# ==============================================================================
# COLUNA DIREITA: PAINEL INTERNO AI BUILDER / OBSERVABILIDADE
# ==============================================================================
with col_interno:
    st.markdown("### 🛡️ Painel Interno AI Builder / Observabilidade")
    st.caption("Monitoramento de telemetria, governança de regras e integridade de IA.")

    resultado = st.session_state.get("resultado_disputa")

    if not resultado:
        # Estado inicial com prévia dos dados analíticos do pedido selecionado
        with st.container(border=True):
            st.info(
                "ℹ️ **Aguardando Envio de Disputa**\n\n"
                "Selecione um pedido e clique em **'Enviar Reclamação'** na coluna à esquerda "
                "para visualizar métricas, regras aplicadas, justificativa e JSON gerado pelo Pydantic."
            )

            st.markdown("#### 📊 Perfil de Risco e Telemetria do Pedido:")

            # Extração e normalização dos indicadores
            score = dados_cliente.get("score_confianca", 0)
            if score >= 80:
                c_score, bg_score, tx_score, b_score = "#16A34A", "#DCFCE7", "#166534", "Confiável (VIP)"
            elif score >= 40:
                c_score, bg_score, tx_score, b_score = "#D97706", "#FEF3C7", "#92400E", "Padrão / Neutro"
            else:
                c_score, bg_score, tx_score, b_score = "#DC2626", "#FEE2E2", "#991B1B", "Alto Risco / Suspeito"

            tier_str = dados_cliente.get("tier_risco", "Tier 2")
            tier_num = tier_str.split(" - ")[0] if " - " in tier_str else tier_str
            tier_desc = tier_str.split(" - ")[1] if " - " in tier_str else ("Baixo Risco" if score >= 80 else ("Médio Risco" if score >= 40 else "Alto Risco"))
            if "1" in tier_num:
                c_tier, bg_tier, tx_tier = "#2563EB", "#DBEAFE", "#1E40AF"
            elif "2" in tier_num:
                c_tier, bg_tier, tx_tier = "#D97706", "#FEF3C7", "#92400E"
            else:
                c_tier, bg_tier, tx_tier = "#DC2626", "#FEE2E2", "#991B1B"

            atraso = pedido_selecionado.get("telemetria_entrega", {}).get("atraso_minutos", 0)
            if atraso == 0:
                c_atraso, bg_atraso, tx_atraso, b_atraso = "#16A34A", "#DCFCE7", "#166534", "Entregue no Prazo"
            elif atraso <= 40:
                c_atraso, bg_atraso, tx_atraso, b_atraso = "#D97706", "#FEF3C7", "#92400E", "Tolerável (≤40 min)"
            else:
                c_atraso, bg_atraso, tx_atraso, b_atraso = "#DC2626", "#FEE2E2", "#991B1B", "Atraso Crítico (>40 min)"

            # Renderização de cards nítidos e responsivos sem truncamento
            st.markdown(
                f"""
                <div class="kpi-row">
                    <div class="kpi-card-box">
                        <div class="kpi-card-title">🎯 Trust Score</div>
                        <div class="kpi-card-value" style="color: {c_score};">
                            {score} <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">/ 100</span>
                        </div>
                        <span class="kpi-card-badge" style="background-color: {bg_score}; color: {tx_score};">
                            {b_score}
                        </span>
                    </div>
                    <div class="kpi-card-box">
                        <div class="kpi-card-title">🛡️ Tier de Risco</div>
                        <div class="kpi-card-value" style="color: {c_tier};">
                            {tier_num}
                        </div>
                        <span class="kpi-card-badge" style="background-color: {bg_tier}; color: {tx_tier};">
                            {tier_desc}
                        </span>
                    </div>
                    <div class="kpi-card-box">
                        <div class="kpi-card-title">⏱️ Atraso Rota</div>
                        <div class="kpi-card-value" style="color: {c_atraso};">
                            {atraso} min
                        </div>
                        <span class="kpi-card-badge" style="background-color: {bg_atraso}; color: {tx_atraso};">
                            {b_atraso}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                "O agente de IA correlaciona esses dados com as regras do `politicas_reembolso.md` "
                "para decidir com rigor determinístico e blindagem contra fraudes."
            )
    else:
        decisao = resultado.get("decisao", {})
        tokens = resultado.get("tokens", {})
        latencia = resultado.get("latencia_segundos", 0.0)
        modelo_utilizado = resultado.get("modelo_usado", "Gemini")

        # ----------------------------------------------------
        # 1. Métricas em Grid 2x2 com espaçamento adequado (sem truncamento)
        # ----------------------------------------------------
        m1, m2 = st.columns(2)
        with m1:
            st.metric(
                label="⏱️ Latência de Resposta",
                value=f"{latencia:.2f} s",
                delta=f"Modelo: {modelo_utilizado}",
                delta_color="off",
            )
        with m2:
            st.metric(
                label="🔢 Tokens Utilizados",
                value=f"{tokens.get('total_tokens', 0):,}",
                delta=f"In: {tokens.get('input_tokens', 0)} | Out: {tokens.get('output_tokens', 0)}",
                delta_color="off",
            )

        m3, m4 = st.columns(2)
        with m3:
            risco = decisao.get("risco_fraude", "Baixo")
            delta_label = "Alerta Alto Risco" if risco == "Alto" else ("Atenção Risco Médio" if risco == "Médio" else "Seguro / Confiável")
            delta_color = "inverse" if risco == "Alto" else ("off" if risco == "Médio" else "normal")
            st.metric(
                label="🛡️ Risco de Fraude",
                value=risco,
                delta=delta_label,
                delta_color=delta_color,
            )
        with m4:
            valor_aprovado = decisao.get("valor_reembolso", 0.0)
            acao_tomada = decisao.get("acao_tomada", "N/A")
            st.metric(
                label="💰 Desfecho & Valor",
                value=f"R$ {valor_aprovado:.2f}",
                delta=acao_tomada,
            )

        # ----------------------------------------------------
        # 2. A regra_aplicada destacada em um box
        # ----------------------------------------------------
        regra_aplicada = decisao.get("regra_aplicada", "Nenhuma regra identificada.")
        st.markdown(
            f"""
            <div class="regra-box-highlight">
                <div class="regra-box-title">
                    📜 Regra Aplicada (Manual de Políticas)
                </div>
                <div class="regra-box-body">
                    {regra_aplicada}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # 3. A justificativa_interna
        # ----------------------------------------------------
        justificativa_interna = decisao.get("justificativa_interna", "Sem justificativa cadastrada.")
        categoria_problema = decisao.get("categoria_problema", "N/A")

        st.markdown(
            f"""
            <div class="justificativa-box">
                <div class="justificativa-title">
                    🔍 Justificativa Interna (CX, Operações & Risk)
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Categoria:</strong> <code>{categoria_problema}</code> | 
                    <strong>Ação Operacional:</strong> <code>{acao_tomada}</code>
                </div>
                <div>{justificativa_interna}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # 4. JSON Completo Gerado pelo Pydantic
        # ----------------------------------------------------
        st.markdown("##### 📦 JSON Completo Gerado pelo Pydantic (`DecisaoDisputa`)")
        st.json(decisao)

        # Expander opcional com metadados adicionais da chamada
        with st.expander("🔬 Telemetria Completa da Execução"):
            st.json(resultado)
