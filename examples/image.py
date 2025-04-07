from bazmek import llm, utils
from pathlib import Path


image = Path(__file__).parent / 'img.png'
image_b64 = utils.img_to_base64(image, new_size=(896, 896))

gemma = llm.LLM(
    url='http://localhost:11435',
    model='llama3.3'
)

messages = [
    llm.Message.user('Hi, what is in the image?', images=(image_b64,))
]

response = utils.sync(llm.prompt(gemma, messages))

match response:
    case utils.Error():
        print(f'[Error]: {response.message}')
    case llm.Message():
        print(f'[Response]: ```{response.content}```')
