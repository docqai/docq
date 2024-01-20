"""Visualise agent messages."""
import json
from datetime import datetime

import streamlit as st
from docq.agents.main import run_agent
from utils.layout import auth_required, render_page_title_and_favicon
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("visualise_agent_messages", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    auth_required(requiring_selected_org_admin=True)

    chats = run_agent()
    # for m in chats:
    #     #st.write("Agent (aka `conversation_id`):", a.name)
    #     st.write(m)
    #     st.divider()

    # for k, messages in chats.items():
    #     st.write(f"Agent (aka conversation_id): `{k.name}`")
    #     for m in messages:
    #         st.write(m)

    #     st.divider()

    st.write(chats)

    st.divider()
    if chats.metadata:
        for k, i in chats.metadata.items():
            st.write(k)
            st.write(i)
