from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE = os.getenv('BACKEND_API_URL', 'http://backend:8000').rstrip('/')

st.set_page_config(page_title='English Text Checker', layout='centered')

st.markdown(
    """
    <style>
      .rotate-90 {
        transform: rotate(90deg);
        transform-origin: left top;
        width: 100vh; /* helps avoid clipping after rotation */
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if 'token' not in st.session_state:
    st.session_state.token = None
if 'tg_username' not in st.session_state:
    st.session_state.tg_username = ''


def api_headers():
    if st.session_state.token:
        return {'Authorization': f"Bearer {st.session_state.token}"}
    return {}


# -------------------------
# красивые ошибки
# -------------------------
def _pretty_label(x: object) -> str:
    s = str(x or '').strip()
    if not s or s.lower() in {'none', 'null', '-'}:
        return '—'
    s = s.replace('_', ' ').replace('-', ' ')
    return s[:1].upper() + s[1:]


TYPE_TITLES: dict[str, str] = {
    'grammar': 'Grammar',
    'style': 'Style',
    'punctuation': 'Punctuation',
    'spelling': 'Spelling',
    'lexis': 'Vocabulary',
    'vocabulary': 'Vocabulary',
}


def _pretty_type(t: object) -> str:
    key = str(t or '').strip().lower()
    if not key:
        return 'Other'
    return TYPE_TITLES.get(key, _pretty_label(key))


def _short_text(x: object, limit: int = 140) -> str:
    s = str(x or '').strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1] + '…'


st.sidebar.title('Menu')
page = st.sidebar.radio(
    'Go to',
    ['Login', 'Checker', 'Settings', 'Stats'],
    index=0 if not st.session_state.token else 1,
)
st.sidebar.caption(f"API: {API_BASE}")


# -------------------------
# регистрация
# -------------------------
if page == 'Login':
    st.title('Login via Telegram username')
    st.caption("Telegram bot: [@engelinabot](https://t.me/engelinabot)")

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
                    st.success('Code requested. (Demo: code is printed in backend logs)')
                    st.session_state.tg_username = username.strip().lstrip('@')
                else:
                    if r.status_code == 404:
                        st.error('User not found')
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
                    json={'tg_username': username.strip(), 'code': code.strip()},
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
# чекер
# -------------------------
elif page == 'Checker':
    st.title('English Text Checker')

    if not st.session_state.token:
        st.warning('Please login first (Menu → Login).')
        st.stop()

    current_level = 'B1'
    try:
        r = requests.get(
            f"{API_BASE}/api/settings",
            headers=api_headers(),
            timeout=10,
        )
        if r.ok:
            current_level = r.json().get('level', 'B1')
    except requests.RequestException:
        pass

    level = st.selectbox(
        'Level',
        ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'],
        index=['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].index(current_level),
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
                        rows = []
                        for e in errs:
                            etype = _pretty_type(e.get('type'))
                            subtype = _pretty_label(e.get('subtype'))
                            kind = etype if subtype == '—' else f"{etype} • {subtype}"

                            rows.append({
                                'Type': kind,
                                'Original': _short_text(e.get('original')),
                                'Corrected': _short_text(e.get('corrected')),
                            })

                        st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.error(f"Backend error: {r.status_code}")
                    st.code(r.text)


# -------------------------
# настройки
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
            headers=api_headers(),
            timeout=15,
        )
        if r.ok:
            current_level = r.json().get('level', 'B1')
    except requests.RequestException:
        pass

    st.write('Choose the level the bot should use when communicating with you.')
    level = st.selectbox(
        'Preferred level',
        ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'],
        index=['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].index(current_level),
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
# статистика
# -------------------------
elif page == 'Stats':
    st.title('Stats')

    if not st.session_state.token:
        st.warning('Please login first (Menu → Login).')
        st.stop()

    st.markdown('<div class="rotate-90">', unsafe_allow_html=True)

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
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    if not r.ok:
        st.error(f"Backend error: {r.status_code}")
        st.code(r.text)
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    data = r.json()

    c1, c2, c3 = st.columns(3)
    c1.metric('Messages', data.get('messages_count', 0))
    c2.metric('Errors', data.get('errors_count', 0))
    c3.metric('Errors / message', data.get('errors_per_message', 0))

    st.divider()

    st.subheader('Errors over time')
    ts = data.get('errors_timeseries', [])
    if ts:
        chart = {p['date']: p['errors'] for p in ts}
        st.line_chart(chart)
    else:
        st.info('No timeseries data')

    st.subheader('Errors by type')
    ebt = data.get('errors_by_type', [])
    if ebt:
        chart = {_pretty_type(p.get('type')): p.get('count', 0) for p in ebt}
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
                f"✅ **{a.get('title', '')}** (`{a.get('code', '')}`) — {a.get('earned_at', '')}",
            )

    st.markdown('</div>', unsafe_allow_html=True)