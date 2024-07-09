import os 
import tiktoken
from enum import Enum
from . import async_openai_client, async_anthropic_client



enc=tiktoken.get_encoding("cl100k_base")

# Enum for model names
model_name_company_mapping={
    "gpt-4-turbo": "openai",
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "gpt-3.5-turbo": "openai",
    "claude-3-5-sonnet-20240620": "anthropic",
    "claude-3-sonnet-20240229": "anthropic",
    "claude-3-opus-20240229": "anthropic",
    "claude-3-haiku-20240307": "anthropic"
}
class ModelCompanyEnum(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
class ModelNameEnum(str, Enum):
    gpt_4_turbo = "gpt-4-turbo"
    gpt_4o = "gpt-4o"
    gpt_4o_mini = "gpt-4o-mini"
    gpt_3_5_turbo = "gpt-3.5-turbo"
    claude_3_5_sonnet = "claude-3-5-sonnet-20240620"
    claude_3_sonnet = "claude-3-sonnet-20240229"
    claude_3_opus = "claude-3-opus-20240229"
    claude_3_haiku = "claude-3-haiku-20240307"
class ModelCostEnum(str, Enum):
    gpt_4_turbo = {"input": 10/1000000.0, "output": 30/1000000.0}
    gpt_4o = {"input": 5/1000000.0, "output": 20/1000000.0}
    gpt_4o_mini = {"input": 0.3/1000000.0, "output": 0.6/1000000.0}
    gpt_3_5_turbo = {"input": 1/1000000.0, "output": 8/1000000.0}
    claude_3_5_sonnet = {"input": 3/1000000.0, "output": 15/1000000.0}
    claude_3_sonnet = {"input": 3/1000000.0, "output": 15/1000000.0}
    claude_3_opus = {"input": 10/1000000.0, "output": 60/1000000.0}
    claude_3_haiku = {"input": 0.25/1000000.0, "output": 1.25/1000000.0}



# Response Handler
async def async_response_handler(
    prompt: dict,
    model_name: str,
    temp=0.0,
    frequency_penalty=0,
    presence_penalty=0,
) -> tuple[str, float]:
    model_company=model_name_company_mapping.get(model_name,None)

    if model_company==ModelCompanyEnum.openai:
        response = await async_openai_client.chat.completions.create(
                model=model_name,
                messages=prompt,
                temperature=temp,
                top_p=1,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
        
        cost=prompt_and_response_cost(prompt, response.choices[0].message.content, model_name)

        return response.choices[0].message.content, cost
    
    elif model_company==ModelCompanyEnum.anthropic:
        system_message=prompt[0]["content"]
        response = await async_anthropic_client.messages.create(
                model=model_name,
                max_tokens=4000,
                temperature=temp,
                system=system_message,
                messages=prompt[1:]
            )
        
        cost=prompt_and_response_cost(prompt, response.content[0].text, model_name)

        return response.content[0].text, cost
    
    else:
        raise Exception("Model not recognized")
    
# calculate cost
def calculate_cost(model_name, input="", output=""):
    # get the cost rates for the model name
    for model_enum_name in ModelNameEnum:
        if model_name==model_enum_name.value:
            cost_rate = ModelCostEnum[model_enum_name.name].value
            cost_rate=eval(cost_rate)

            input_cost = len(enc.encode(input)) * cost_rate["input"]
            output_cost = len(enc.encode(output)) * cost_rate["output"]
            # print(input_cost, output_cost, len(input), len(output))
            # return {"input": input_cost, "output": output_cost}
            cost=input_cost+output_cost
            return cost
    return 0

def prompt_and_response_cost(prompt, response, model_name):
    input_str=""
    for message in prompt:
        if "content" in message:
            input_str+=message["content"]
    output_str=response
    return calculate_cost(model_name, input_str, output_str)
