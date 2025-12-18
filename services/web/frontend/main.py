from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE = os.getenv('BACKEND_API_URL', 'http://backend:8000').rstrip('/')

st.set_page_config(page_title='English Text Checker', layout='centered')

if 'token' not in st.session_state:
    st.session_state.token = None
if 'tg_username' not in st.session_state:
    st.session_state.tg_username = ''


def api_headers():
    if st.session_state.token:
        return {'Authorization': f"Bearer {st.session_state.token}"}
    return {}


st.sidebar.title('Menu')
page = st.sidebar.radio(
    'Go to',
    ['Login', 'Checker', 'Settings', 'Stats'],
    index=0 if not st.session_state.token else 1,
)
st.sidebar.caption(f"API: {API_BASE}")


# -------------------------
# LOGIN
# -------------------------
if page == 'Login':
    st.title('Login via Telegram username')

    username = st.text_input(
        'Telegram username (without @)', value=st.session_state.tg_username,
    )

    if st.button('Send 5-digit code', use_container_width=True):
        if not username.strip():
            st.error('Enter your Telegram username')
        else:
            try:
                r = requests.post(
                    f"{API_BASE}/api/auth/request-code",
                    json={'tg_username': username.strip()},
                    timeout=30,
                )
            except requests.RequestException as e:
                st.error('Backend is unavailable')
                st.caption(str(e))
            else:
                if r.ok:
                    st.success(
                        'Code requested.\
                        (Demo: code is printed in backend logs)',
                    )
                    st.session_state.tg_username = username.strip().lstrip('@')
                else:
                    st.error(f"Error: {r.status_code}")
                    st.code(r.text)

    st.divider()
    code = st.text_input('Enter 5-digit code', max_chars=5)

    if st.button('Verify & Login', use_container_width=True):
        if not username.strip() or not code.strip():
            st.error('Enter username and code')
        else:
            try:
                r = requests.post(
                    f"{API_BASE}/api/auth/verify",
                    json={
                        'tg_username': username.strip(),
                        'code': code.strip(),
                    },
                    timeout=30,
                )
            except requests.RequestException as e:
                st.error('Backend is unavailable')
                st.caption(str(e))
            else:
                if r.ok:
                    data = r.json()
                    st.session_state.token = data['token']
                    st.session_state.tg_username = data['tg_username']
                    st.success(f"Logged in as @{st.session_state.tg_username}")
                else:
                    st.error(f"Login failed: {r.status_code}")
                    st.code(r.text)

    if st.session_state.token:
        if st.button('Logout'):
            st.session_state.token = None
            st.success('Logged out')


# -------------------------
# CHECKER
# -------------------------
elif page == 'Checker':
    st.title('English Text Checker')

    if not st.session_state.token:
        st.warning('Please login first (Menu → Login).')
        st.stop()

    # подтянуть текущий уровень из settings
    current_level = 'B1'
    try:
        r = requests.get(
            f"{API_BASE}/api/settings",
            headers=api_headers(), timeout=10,
        )
        if r.ok:
            current_level = r.json().get('level', 'B1')
    except requests.RequestException:
        pass

    level = st.selectbox(
        'Level',
        ['A1', 'A2', 'B1', 'B2', 'C1'],
        index=['A1', 'A2', 'B1', 'B2', 'C1'].index(current_level),
    )

    text = st.text_area('Enter your text', height=220)

    if st.button('Check', type='primary', use_container_width=True):
        if not text.strip():
            st.error('Text cannot be empty.')
        else:
            try:
                with st.spinner('Checking...'):
                    r = requests.post(
                        f"{API_BASE}/api/check",
                        json={'text': text, 'level': level},
                        headers=api_headers(),
                        timeout=60,
                    )
            except requests.RequestException as e:
                st.error('Backend is unavailable')
                st.caption(str(e))
            else:
                if r.ok:
                    data = r.json()
                    st.subheader('Corrected text')
                    st.write(data.get('corrected_text', ''))

                    st.subheader('Explanation')
                    st.write(data.get('explanation', ''))

                    st.subheader('Errors')
                    errs = data.get('errors', [])
                    if not errs:
                        st.success('No errors')
                    else:
                        for e in errs:
                            st.write(
                                f"- {e.get('type')} / \
                                    {e.get('subtype', '-')}: "
                                f"{e.get('original')} → {e.get('corrected')}",
                            )
                else:
                    st.error(f"Backend error: {r.status_code}")
                    st.code(r.text)


# -------------------------
# SETTINGS
# -------------------------
elif page == 'Settings':
    st.title('Settings')

    if not st.session_state.token:
        st.warning('Please login first (Menu → Login).')
        st.stop()

    current_level = 'B1'
    try:
        r = requests.get(
            f"{API_BASE}/api/settings",
            headers=api_headers(), timeout=15,
        )
        if r.ok:
            current_level = r.json().get('level', 'B1')
    except requests.RequestException:
        pass

    st.write(
        'Choose the level the bot should use when communicating with you.',
    )
    level = st.selectbox(
        'Preferred level',
        ['A1', 'A2', 'B1', 'B2', 'C1'],
        index=['A1', 'A2', 'B1', 'B2', 'C1'].index(current_level),
    )

    if st.button('Save', type='primary'):
        try:
            r = requests.post(
                f"{API_BASE}/api/settings",
                json={'level': level},
                headers=api_headers(),
                timeout=15,
            )
        except requests.RequestException as e:
            st.error('Backend is unavailable')
            st.caption(str(e))
        else:
            if r.ok:
                st.success('Saved')
            else:
                st.error(f"Save failed: {r.status_code}")
                st.code(r.text)


# -------------------------
# STATS
# -------------------------
elif page == 'Stats':
    st.title('Stats')

    if not st.session_state.token:
        st.warning('Please login first (Menu → Login).')
        st.stop()

    period = st.selectbox('Period', ['day', 'week', 'all'], index=1)

    try:
        r = requests.get(
            f"{API_BASE}/api/stats",
            params={'period': period},
            headers=api_headers(),
            timeout=20,
        )
    except requests.RequestException as e:
        st.error('Backend is unavailable')
        st.caption(str(e))
        st.stop()

    if not r.ok:
        st.error(f"Backend error: {r.status_code}")
        st.code(r.text)
        st.stop()

    data = r.json()

    c1, c2, c3 = st.columns(3)
    c1.metric('Messages', data.get('messages_count', 0))
    c2.metric('Errors', data.get('errors_count', 0))
    c3.metric('Errors / message', data.get('errors_per_message', 0))

    st.divider()

    # LINE CHART: errors over time
    st.subheader('Errors over time')
    ts = data.get('errors_timeseries', [])
    if ts:
        # line_chart принимает dict: x -> y
        chart = {p['date']: p['errors'] for p in ts}
        st.line_chart(chart)
    else:
        st.info('No timeseries data')

    st.subheader('Errors by type')
    ebt = data.get('errors_by_type', [])
    if ebt:
        chart = {p['type']: p['count'] for p in ebt}
        st.bar_chart(chart)
    else:
        st.info('No errors_by_type data')

    st.subheader('Achievements')
    ach = data.get('achievements', [])
    if not ach:
        st.info('No achievements yet')
    else:
        for a in ach:
            st.write(
                f"✅ **{a.get('title', '')}** \
                    (`{a.get('code', '')}`) — \
                    {a.get('earned_at', '')}",
            )
