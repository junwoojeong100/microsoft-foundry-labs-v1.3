from __future__ import annotations

import streamlit as st

from workshop import (
    WORKSHOP_VERSION,
    WorkshopError,
    ask,
    exclusive_session,
    load_settings,
    read_state,
)

st.set_page_config(
    page_title=f"출장 도우미 · 실습 v{WORKSHOP_VERSION}",
    page_icon="🧭",
    layout="centered",
)
st.title("다온테크 출장 도우미")
st.caption(
    f"실습 v{WORKSHOP_VERSION} · 교육용 합성 데이터 · 지원 상한 안내만 · 승인/예약/결제 불가"
)

try:
    settings = load_settings()
    state = read_state(settings)
    selected = state.selected()
except (WorkshopError, OSError, ValueError) as exc:
    st.error(str(exc))
    st.info("보존된 축약 예제입니다. docs/compact-example.md의 별도 환경을 확인하세요.")
    st.stop()

st.info(
    f"Foundry agent: {state.agent_name} · version {state.selected_version} · {selected['stage']}"
)
st.markdown(
    "**예시 질문:** 2026년 9월 서울 2박 3일 출장의 숙박비와 식비 상한을 계산해 주세요."
)
st.caption(
    "질문은 각각 독립적으로 처리합니다. '그럼 부산은?' 대신 도시·기간·날짜를 모두 적으세요."
)

with st.form("question"):
    query = st.text_area("출장 질문", max_chars=4000, height=100)
    submitted = st.form_submit_button("Foundry에 질문하기")

if submitted:
    try:
        with exclusive_session(), st.spinner("문서와 계산 결과를 확인하고 있습니다..."):
            st.session_state["result"] = ask(settings, query)
    except (WorkshopError, OSError, ValueError) as exc:
        st.session_state.pop("result", None)
        st.error(str(exc))
        st.info(
            "오류를 성공한 답변으로 대체하지 않았습니다. outputs/와 문제 해결 문서를 확인하세요."
        )

if "result" in st.session_state:
    result = st.session_state["result"]
    st.subheader("답변")
    st.markdown(result["answer"])
    st.caption(
        f"실행 버전 {result['agent_version']} · {result['latency_ms']} ms · {result['output_file']}"
    )
    if not result["citations"]:
        st.warning(
            "파일 인용이 없습니다. 확인 질문에는 정상일 수 있지만, 규정 답변이라면 원문을 대조하세요."
        )
    with st.expander("실제 파일 인용", expanded=True):
        st.json(result["citations"])
    with st.expander("실제로 실행한 계산 도구", expanded=True):
        if result["tool_calls"]:
            st.json(result["tool_calls"])
        else:
            st.write("이번 질문에서는 계산 도구를 실행하지 않았습니다.")
    with st.expander("Response ID와 사용량"):
        st.json(
            [
                {
                    "response_id": item["response_id"],
                    "status": item["status"],
                    "usage": item["usage"],
                }
                for item in result["responses"]
            ]
        )
