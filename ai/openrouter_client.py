"""OpenRouter client for Wealth Advisor."""
import os
import json
import time
from typing import Optional, Dict, Any
from config.settings import settings

class OpenRouterClient:
    """Client for OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model_name = model or settings.openrouter_model
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                )
                print(f"✓ OpenRouter client initialized ({self.model_name})")
            except ImportError:
                print("⚠️ openai package not installed.")
        else:
            print("⚠️ OpenRouter API key not found")
            
    @property
    def is_available(self) -> bool:
        return self.client is not None
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.client:
            return "OpenRouter not configured."
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": "https://cryptoaion.com", # Optional but requested by OpenRouter
                    "X-Title": "Wealth Advisor",
                },
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_with_tools(
        self, 
        prompt: str, 
        tools: Dict[str, callable],
        system_prompt: str = ""
    ) -> str:
        """
        Generate response with tool calling capability.
        """
        if not self.client:
            return "OpenRouter not configured."
        
        # Create tool descriptions
        tool_descriptions = "\n".join([
            f"- {name}: {func.__doc__ or 'No description'}"
            for name, func in tools.items()
        ])
        
        # Enhanced prompt with tool instructions
        enhanced_prompt = f"""
{system_prompt}

You have access to these tools:
{tool_descriptions}

To use a tool, respond with:
TOOL: <tool_name>
INPUT: <json_input>

After seeing the tool result, provide your final answer.

User query: {prompt}
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_text = self.generate(enhanced_prompt)
                
                # Check if model wants to use a tool
                if "TOOL:" in response_text and "INPUT:" in response_text:
                    # Parse tool call
                    lines = response_text.split("\n")
                    tool_name = None
                    tool_input = None
                    
                    for i, line in enumerate(lines):
                        if line.startswith("TOOL:"):
                            tool_name = line.replace("TOOL:", "").strip()
                        elif line.startswith("INPUT:"):
                            tool_input = line.replace("INPUT:", "").strip()
                            if not tool_input.endswith("}"):
                                for j in range(i+1, len(lines)):
                                    tool_input += lines[j]
                                    if "}" in lines[j]:
                                        break
                    
                    if tool_name and tool_name in tools:
                        # Execute tool
                        tool_func = tools[tool_name]
                        try:
                            result = tool_func(tool_input or "{}")
                        except Exception as e:
                            result = f"Tool error: {str(e)}"
                        
                        # Get final response with tool result
                        followup = f"""
Tool result for {tool_name}:
{result}

Now provide a helpful response to the user based on this result.
"""
                        # We append the tool interaction to history effectively by making a new call
                        # Ideally we should maintain message history, but fitting into the current 'generate' valid interface
                        # We will just do a simplified follow-up.
                        
                        # Ideally pass the full history back.
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": enhanced_prompt},
                            {"role": "assistant", "content": response_text},
                            {"role": "user", "content": f"Tool result: {result}\n\nPlease continue."}
                        ]
                        
                        followup_response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=messages
                        )
                        return followup_response.choices[0].message.content
                
                return response_text
                
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return f"Error: {str(e)}"
        return "Error: Maximum retries exceeded."
