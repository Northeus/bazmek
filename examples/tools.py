from bazmek import llm, utils


gemma = llm.LLM(
    url='http://localhost:11435',
    model='llama3.3'
)

messages = [
    llm.Message.user('Compute this equation: `3 + 3 * 88`')
]

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'compute_equation',
            'description': 'Compute given equation',
            'parameters': {
                'equation': {
                    'type': 'string',
                    'description': 'Equation to be computed'
                },
                'required': ['equation']
            }
        }
    }
]

response = utils.sync(llm.prompt(gemma, messages, tools=tools))

match response:
    case utils.Error():
        print(f'[Error]: {response.message}')
    case llm.Message():
        print(f'[Response]: {response.content}')
        print(f'[Calls]: {response.tool_calls}')
