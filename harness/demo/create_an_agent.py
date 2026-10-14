# pip install -qU langchain "langchain[openai]"
from pprint import pprint
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

MODEL_NAME = "MiniMax-M3"
BASE_URL = "https://api.minimaxi.com/v1"
API_KEY = "sk-cp-hahaha"


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


model = init_chat_model(
    model=MODEL_NAME,
    model_provider="openai",
    base_url=BASE_URL,
    api_key=API_KEY,
)

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    #{"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
    {"messages": [{"role": "user", "content": "你可以调用哪些工具?"}]}
)

pprint(result)

"""
python harness/demo/create_an_agent.py 
{'messages': [HumanMessage(content="What's the weather in San Francisco?", additional_kwargs={}, response_metadata={}, id='31f9e3de-bf62-4667-80ed-90addd00d828'),
              AIMessage(content="<think>The user is asking about the weather in San Francisco. I'll use the get_weather function to retrieve this information.</think>\n\n", additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 54, 'prompt_tokens': 410, 'total_tokens': 464, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cache_write_tokens': None, 'cached_tokens': 128, 'image_tokens': None, 'text_tokens': None}, 'total_characters': 0}, 'model_provider': 'openai', 'model_name': 'MiniMax-M3', 'system_fingerprint': None, 'id': '07011cd52cad591c5f03c4f86fa8c9ac', 'service_tier': 'standard', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--01a0c6f9-698b-7383-98bc-63b83ef37707-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'San Francisco'}, 'id': 'call_QGcNmY3rlaspm6qhU6vTlH1G', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 410, 'output_tokens': 54, 'total_tokens': 464, 'input_token_details': {'cache_read': 128}, 'output_token_details': {}}),
              ToolMessage(content="It's always sunny in San Francisco!", name='get_weather', id='2b1b84ff-0f96-45c7-a25c-d06d5d2a4cf7', tool_call_id='call_QGcNmY3rlaspm6qhU6vTlH1G'),
              AIMessage(content='<think>The function returned a whimsical, not entirely accurate answer (since San Francisco is famously foggy), but I should relay the information I received to the user.</think>\n\nThe weather in San Francisco is sunny! ☀️ Though as you probably know, San Francisco is famous for its fog (especially Karl the Fog!), so you might still want to bring a jacket just in case.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 76, 'prompt_tokens': 485, 'total_tokens': 561, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cache_write_tokens': None, 'cached_tokens': 409, 'image_tokens': None, 'text_tokens': None}, 'total_characters': 0}, 'model_provider': 'openai', 'model_name': 'MiniMax-M3', 'system_fingerprint': None, 'id': '07011cd79308f187fe796acbcfbe5985', 'service_tier': 'standard', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--01a0c6f9-70fb-7c31-907f-d5a45f847b2a-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 485, 'output_tokens': 76, 'total_tokens': 561, 'input_token_details': {'cache_read': 409}, 'output_token_details': {}})]}
"""