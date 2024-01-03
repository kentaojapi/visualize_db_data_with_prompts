import ast
from dataclasses import dataclass
from functools import lru_cache
import os

from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_experimental.sql import SQLDatabaseChain
import pandas as pd
from pydantic import BaseModel, validator

from llm.database import load_db


@lru_cache
def get_chat() -> ChatOpenAI:
    return ChatOpenAI(
        model_name=os.environ["OPENAI_API_MODEL"],
        temperature=os.environ["OPENAI_API_TEMPERATURE"],
        streaming=True,
    )


class ChatToVisualizationChainResults(BaseModel):
    title: str
    chart_type: str
    dataset: pd.DataFrame
    description: str
    parameters: dict

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True

    @validator('dataset', pre=True)
    def _convert_to_dataframe(cls, v) -> pd.DataFrame:
        return pd.DataFrame(v)


class ChatToVisualizationChain:
    UPPER_LIMIT_TO_SELECT_DB: int = 1000

    def __init__(self) -> None:
        self.llm_model: ChatOpenAI = get_chat()
        self.db: SQLDatabase = load_db()

    def _sql_chain(self) -> SQLDatabaseChain:
        return SQLDatabaseChain(
            llm=self.llm_model,
            database=self.db,
            verbose=True,
            top_k=self.UPPER_LIMIT_TO_SELECT_DB)

    def _create_elements_for_visualization_chain(self) -> LLMChain:
        template: str = """
        Define JSON data according to '{answer}'. 
        This JSON data is used for data visualization according to python3 syntax.
        The AI assistant will only reply in the following JSON format:

        {{
            'title': string,
            'chart_type': string,
            'dataset': dict,
            'description': string,
            'parameters': {{...}}
        }}

        Instructions:

        1. The dataset should contain a list of column names in key and a list of values in value, in dict format, to be used as a dict to be read as a pandas.DataFrame.
        2. chart_type must only contain methods of plotly.express from the Python library Plotly.
        3. The format for chart_type string: plotly.express.chartType.
        4. For each chart_type, parameters must contain the value to be used for all parameters of that plotly.express method.
        5. There should 4 parameters for each chart.
        6. Do not include "data_frame" in the parameters.
        7. Output a summary statement about the contents of the visualized data in the description. You should use japanese.
        """
        prompt = PromptTemplate(
            input_variables=["answer"], template=template)
        return LLMChain(llm=self.llm_model, prompt=prompt)

    def _exec(self, prompt: str) -> ChatToVisualizationChainResults:
        chain = SimpleSequentialChain(
            chains=[
                self._sql_chain(),
                self._create_elements_for_visualization_chain()
            ],
            verbose=True
        )
        chain_result: str = chain(prompt)
        chain_output = ast.literal_eval(chain_result['output'])
        return ChatToVisualizationChainResults(**chain_output)

    def create(self):
        return self._exec
