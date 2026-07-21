"""
Authentication module for the Regulatory Compliance Intelligence System.

Provides:
1. User Login
2. Logout
3. Session Management
4. Role-Based Access

Current implementation uses local user.
"""

import streamlit as st

# -----------------------------------------------------------------------------
# Demo Users
# -----------------------------------------------------------------------------

USERS = {
    "admin": {
        "password": "admin123",
        "role": "Admin",
        "display_name": "System Administrator",
    },
    "analyst": {
        "password": "analyst123",
        "role": "Compliance Analyst",
        "display_name": "Compliance User",
    },
}


# -----------------------------------------------------------------------------
# Session Initialization
# -----------------------------------------------------------------------------


def initialize_session() -> None:
    """
    Initialize Streamlit session state.
    """

    defaults = {
        "authenticated": False,
        "username": "",
        "display_name": "",
        "role": "",
        "messages": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# -----------------------------------------------------------------------------
# Login Validation
# -----------------------------------------------------------------------------


def authenticate(username: str, password: str) -> bool:
    """
    Validate user credentials.
    """

    user = USERS.get(username)

    if not user:
        return False

    if user["password"] != password:
        return False

    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.role = user["role"]
    st.session_state.display_name = user["display_name"]

    return True


# -----------------------------------------------------------------------------
# Login Screen
# -----------------------------------------------------------------------------


def login() -> None:
    """
    Display login page.
    """

    if st.session_state.authenticated:
        return

    left, center, right = st.columns([2, 3, 2])

    with center:

        st.title("Regulatory Compliance Intelligence System")

        st.caption("AI Powered Regulatory Knowledge Assistant")

        st.divider()

        username = st.text_input(
            "Username",
            placeholder="Enter username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
        )

        if st.button(
            "Login",
            use_container_width=True,
        ):

            if authenticate(username, password):

                st.success("Login Successful")

                st.rerun()

            st.error("Invalid username or password.")

        st.divider()

        st.info("""
Demo Users

Admin
Username : admin
Password : admin123

Compliance User
Username : analyst
Password : analyst123
""")

    st.stop()


# -----------------------------------------------------------------------------
# Sidebar User Profile
# -----------------------------------------------------------------------------


def sidebar_profile() -> None:
    """
    Display logged-in user details.
    """

    st.sidebar.title("User Information")

    st.sidebar.success(st.session_state.display_name)

    st.sidebar.write(f"**Username:** {st.session_state.username}")

    st.sidebar.write(f"**Role:** {st.session_state.role}")


# -----------------------------------------------------------------------------
# Logout
# -----------------------------------------------------------------------------


def logout() -> None:
    """
    Logout current user.
    """

    if st.sidebar.button(
        "Logout",
        use_container_width=True,
    ):

        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.display_name = ""
        st.session_state.role = ""
        st.session_state.messages = []

        st.rerun()


# -----------------------------------------------------------------------------
# Role Checks
# -----------------------------------------------------------------------------


def is_admin() -> bool:
    """
    Returns True if current user is Admin.
    """

    return st.session_state.role == "Admin"


def is_authenticated() -> bool:
    """
    Returns authentication status.
    """

    return st.session_state.authenticated
