import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from graphviz import Digraph
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI API key and model
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(api_key=api_key, model="gpt-4o-2024-08-06")

# Function to load PDF and extract pages
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return pages

# Define the digraph template example
digraph_example = """
    from graphviz import Digraph

    dot = Digraph(comment='Portfolio Structure')

    # Root
    dot.node('ROOT', 'ROOT\nportfolio: object')

    # Portfolio node
    dot.node('portfolio', 'portfolio\nname: string\nseries: string\nfees: object\nwithdrawalRights: object\n'
                        'contactInformation: object\nyearByYearReturns: object[]\nbestWorstReturns: object[]\n'
                        'averageReturn: string\ntargetInvestors: string[]\ntaxInformation: string')

    # Connect Root to Portfolio
    dot.edge('ROOT', 'portfolio')

    # Nodes under Portfolio
    dot.node('fees', 'fees\nsalesCharges: string\nfundExpenses: object\ntrailingCommissions: string')
    dot.node('withdrawalRights', 'withdrawalRights\ntimeLimit: string\nconditions: string[]')
    dot.node('contactInformation', 'contactInformation\ncompanyName: string\naddress: string\nphone: string\n'
                                    'email: string\nwebsite: string')
    dot.node('yearByYearReturns', 'yearByYearReturns\nyear: string\nreturn: string')
    dot.node('bestWorstReturns', 'bestWorstReturns\ntype: string\nreturn: string\ndate: string\ninvestmentValue: string')

    # Connect Portfolio to its components
    dot.edge('portfolio', 'fees')
    dot.edge('portfolio', 'withdrawalRights')
    dot.edge('portfolio', 'contactInformation')
    dot.edge('portfolio', 'yearByYearReturns')
    dot.edge('portfolio', 'bestWorstReturns')

    # Sub-components
    dot.node('fundExpenses', 'fundExpenses\nmanagementExpenseRatio: string\ntradingExpenseRatio: string\n'
                            'totalExpenses: string')

    # Connect sub-components
    dot.edge('fees', 'fundExpenses')

    # Render the graph always in png
    dot.render('portfolio_structure', format='png')
"""

# Define the prompt_digraph template for generating the digraph code
prompt_digraph = PromptTemplate(
    template="Generate only the Python code in your answer in order to generate a digraph of the entities and their relationships and save all the generated file inside this path ./digraph with the name temp in the given PDF following the format\n{digraph_example} of the following pdf:\n{content}",
    input_variables=["content"],
    partial_variables={"digraph_example": digraph_example}
)

prompt_pydantic = PromptTemplate(
    template="Generate the only the json code that describe the schema from the following digraph code:\n{content}",
    input_variables=["content"],
)

# Streamlit App
def main():
    st.title("PDF to entities schema")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        with open("./digraph/temp.pdf", "wb") as f:
            f.write(uploaded_file.read())

        pages = load_pdf("./digraph/temp.pdf")
        
        # Generate the digraph code
        chain = prompt_digraph | llm 
        response = chain.invoke({"content": pages})

        exec(response.content[9:-3])


        chain_pydantic = prompt_pydantic | llm

        response_pydantic = chain_pydantic.invoke({"content": response.content})

        if response and response_pydantic:

            st.image('./digraph/temp.png', use_column_width=True)

            st.write("Generated Json schema:")
            st.code(response_pydantic.content, language="python",line_numbers=True)


if __name__ == "__main__":
    main()