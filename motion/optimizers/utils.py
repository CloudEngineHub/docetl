from typing import Dict, List, Any, Optional, Tuple, Union
import json
from litellm import completion, completion_cost
import os
import jinja2
from jinja2 import Environment, meta
import re


def extract_jinja_variables(template_string: str) -> List[str]:
    """
    Extract variables from a Jinja2 template string.

    This function uses both Jinja2's AST parsing and regex to find all variables
    referenced in the given template string.

    Args:
        template_string (str): The Jinja2 template string to analyze.

    Returns:
        List[str]: A list of unique variable names found in the template.
    """
    # Create a Jinja2 environment
    env = Environment()

    # Parse the template
    ast = env.parse(template_string)

    # Find all the variables referenced in the template
    variables = meta.find_undeclared_variables(ast)

    # Use regex to find any additional variables that might be missed
    # This regex looks for {{ variable }} patterns
    regex_variables = set(re.findall(r"{{\s*(\w+)\s*}}", template_string))

    # Combine both sets of variables
    all_variables = variables.union(regex_variables)

    return list(all_variables)


SUPPORTED_OPS = ["map"]


class LLMClient:
    """
    A client for interacting with LLMs, mainly used for the agent.

    This class provides methods to generate responses using specified LLM models
    and keeps track of the total cost of API calls.
    """

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize the LLMClient.

        Args:
            model (str, optional): The name of the LLM model to use. Defaults to "gpt-4o".
        """
        if model == "gpt-4o":
            model = "gpt-4o-2024-08-06"
        self.model = model
        self.total_cost = 0

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        parameters: Dict[str, Any],
    ) -> Any:
        """
        Generate a response using the LLM.

        This method sends a request to the LLM with the given messages, system prompt,
        and parameters, and returns the response.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries to send to the LLM.
            system_prompt (str): The system prompt to use for the generation.
            parameters (Dict[str, Any]): Additional parameters for the LLM request.

        Returns:
            Any: The response from the LLM.
        """
        parameters["additionalProperties"] = False

        response = completion(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                *messages,
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "output",
                    "strict": True,
                    "schema": parameters,
                },
            },
        )
        cost = completion_cost(response)
        self.total_cost += cost
        return response