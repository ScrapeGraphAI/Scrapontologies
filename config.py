from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

DIGRAPH_EXAMPLE = """
    from graphviz import Digraph

    dot = Digraph(comment='Portfolio Structure')

    # Root
    dot.node('ROOT', 'ROOT\\nportfolio: object')

    # Portfolio node
    dot.node('portfolio', 'portfolio\\nname: string\\nseries: string\\nfees: object\\nwithdrawalRights: object\\n'
                        'contactInformation: object\\nyearByYearReturns: object[]\\nbestWorstReturns: object[]\\n'
                        'averageReturn: string\\ntargetInvestors: string[]\\ntaxInformation: string')

    # Connect Root to Portfolio
    dot.edge('ROOT', 'portfolio')

    # Nodes under Portfolio
    dot.node('fees', 'fees\\nsalesCharges: string\\nfundExpenses: object\\ntrailingCommissions: string')
    dot.node('withdrawalRights', 'withdrawalRights\\ntimeLimit: string\\nconditions: string[]')
    dot.node('contactInformation', 'contactInformation\\ncompanyName: string\\naddress: string\\nphone: string\\n'
                                    'email: string\\nwebsite: string')
    dot.node('yearByYearReturns', 'yearByYearReturns\\nyear: string\\nreturn: string')
    dot.node('bestWorstReturns', 'bestWorstReturns\\ntype: string\\nreturn: string\\ndate: string\\ninvestmentValue: string')

    # Connect Portfolio to its components
    dot.edge('portfolio', 'fees')
    dot.edge('portfolio', 'withdrawalRights')
    dot.edge('portfolio', 'contactInformation')
    dot.edge('portfolio', 'yearByYearReturns')
    dot.edge('portfolio', 'bestWorstReturns')

    # Sub-components
    dot.node('fundExpenses', 'fundExpenses\\nmanagementExpenseRatio: string\\ntradingExpenseRatio: string\\n'
                            'totalExpenses: string')

    # Connect sub-components
    dot.edge('fees', 'fundExpenses')
"""