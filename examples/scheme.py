from bazmek import llm, utils

import json


print('[INFO] Funny enough, they can do it without scheme but no with..')

gemma = llm.LLM(
    url='http://localhost:11435',
    model='llama3.3'
)

messages = [
    llm.Message.system('You are pet extractor, extract every single pet!'),
    llm.Message.user(
        'Extract all animals and their info from following text:\n'
        'Dog Rony is bigger than our cat Lucy. Rony is 18 years old.')
]

schema = {
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string'
        },
        'species': {
            'type': 'string',
            'description': 'Species of the animal.'
        },
        'age': {
            'type': 'integer',
            'description': 'Age of the pet, can be omitted.'
        }
    },
    'required': ['name', 'species']
}

response = utils.sync(llm.prompt(gemma, messages, schema=schema))

match response:
    case utils.Error():
        print(f'[Error]: {response.message}')
    case dict():
        print(f'[Response]: \n{json.dumps(response, indent=4)}')

