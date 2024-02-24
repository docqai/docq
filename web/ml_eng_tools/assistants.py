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

