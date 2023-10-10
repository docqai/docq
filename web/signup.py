"""Signup page for the web app."""
import re

import docq
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

st.title("Signup")

base_key= "user-signup"

def submit_handler() -> None:
    """Handle form submission."""
    print("Submitted!")

def _validate_name(name: str, generator: DeltaGenerator) -> bool:
    """Validate the name."""
    if not name:
        generator.error("Name is required!")
        return False
    elif len(name) < 3:
        generator.error("Name must be at least 3 characters long!")
        return False
    return True


def _validate_email(email: str, generator: DeltaGenerator) -> bool:
    """Validate the email."""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not email:
        generator.error("Email is required!")
        return False
    elif len(email) < 3:
        generator.error("Email must be at least 3 characters long!")
        return False
    elif not re.match(email_regex, email):
        generator.error(f"_{email}_ is not a valid email address!")
        return False
    return True


def _validate_password(password: str, generator: DeltaGenerator) -> bool:
    """Validate the password."""
    special_chars = r"[_@$!#%^&*()-=+\{\}\[\]|\\:;\"'<>,.?/~`]"
    if  password is None:
        generator.error("Password is required!")
        return False
    elif len(password) < 8:
        generator.error("Password must be at least 8 characters long!")
        return False
    elif not re.search("[a-z]", password):
        generator.error("Password must contain at least 1 lowercase letter!")
        return False
    elif not re.search("[A-Z]", password):
        generator.error("Password must contain at least 1 uppercase letter!")
        return False
    elif not re.search("[0-9]", password):
        generator.error("Password must contain at least 1 number!")
        return False
    elif not re.search(special_chars, password):
        generator.error("Password must contain at least 1 special character!")
        return False
    return True

def _validate_form() -> None:
    """Handle validation of the signup form."""
    name = st.session_state.get(f"{base_key}-name", None)
    email = st.session_state.get(f"{base_key}-email", None)
    password = st.session_state.get(f"{base_key}-password", None)
    validator = st.session_state["signup-validator"]

    if not _validate_name(name, validator):
        st.stop()
    if not _validate_email(email, validator):
        st.stop()
    if not _validate_password(password, validator):
        st.stop()

    submit_handler()


st.session_state["signup-validator"] = st.empty()
with st.form(key="signup"):
    name = st.text_input("Name", placeholder="John Doe", key=f"{base_key}-name")
    email = st.text_input("Email", placeholder="johndoe@mail.com", key=f"{base_key}-email")
    password = st.text_input("Password", type="password", key=f"{base_key}-password")
    submit = st.form_submit_button("Signup")
    if submit:
        _validate_form()

