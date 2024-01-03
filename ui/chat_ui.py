import ast
import traceback

import streamlit as st
from langchain.callbacks import StreamlitCallbackHandler
import pandas as pd
import plotly
import plotly.express as px

from llm.chains import (
    ChatToVisualizationChainResults,
    ChatToVisualizationChain
)


class ChatUI:
    TITLE: str = "Visualize DB Data"
    PLACEHOLDER: str = "xxxを棒グラフで表示してください"

    def __init__(self) -> None:
        pass

    def _init_session_state(self) -> None:
        if "agent_chain" not in st.session_state:
            st.session_state.chain = ChatToVisualizationChain().create()

    def _get_input(self) -> str:
        return st.chat_input(self.PLACEHOLDER)

    def _exec_plotly_code(
            self, result: ChatToVisualizationChainResults) -> dict:
        local_variables = {}
        df = result.dataset
        code = f"""
import plotly
params = {result.parameters}
params['data_frame'] = df
params['title'] = "{result.title}"
fig = {result.chart_type}(**params)
"""
        exec(code, {"df": df}, local_variables)
        return local_variables

    def run(self) -> None:
        self._init_session_state()
        st.title(self.TITLE)

        prompt = self._get_input()

        if not prompt:
            return

        with st.chat_message("user"):
            st.markdown(prompt)

        with (
                st.chat_message("assistant"),
                st.spinner(text="実行中...")):
            try:
                result = st.session_state.chain(prompt)
                plotly_variables = self._exec_plotly_code(result)

                st.markdown(result.description)
                st.plotly_chart(plotly_variables['fig'], use_container_width=True)
            except Exception as e:
                st.error("適切にデータを抽出および出力することができませんでした。")
                st.text_area("traceback", traceback.format_exc())

