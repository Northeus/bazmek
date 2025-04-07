from bazmek import llm, utils


gemma = llm.LLM(
    url='http://localhost:11435',
    model='gemma3'
)

messages = [
    llm.Message.system('You are dog, please behave as one!'),
    llm.Message.user('Hi, how are you?')
]

response = utils.sync(llm.prompt(gemma, messages))
tokens = llm.tokenize('google/gemma-3-4b-it', messages)

print(f'[Chat] {len(messages)} messages, {len(tokens)} tokens')
for message in messages:
    print(f'\t{message.role}: {message.content}')

match response:
    case utils.Error():
        print(f'[Error]: {response.message}')
    case llm.Message():
        print(f'[Response]: ```{response.content}```')
