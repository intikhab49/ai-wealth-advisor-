"""Google Gemini AI client for Wealth Advisor."""
import os
import json
from typing import Optional, Dict, Any


class GeminiClient:
    """
    Client for Google Gemini AI.
    Free tier: 60 requests/minute, 1500 requests/day
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google AI API key (get free at: https://aistudio.google.com/apikey)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = None
        
        if self.api_key:
            self._init_client()
    
    def _init_client(self):
        """Initialize the Gemini model."""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            print("✓ Gemini client initialized (gemini-2.0-flash-lite)")
            
        except ImportError:
            print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")
            self.model = None
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini: {e}")
            self.model = None
    
    @property
    def is_available(self) -> bool:
        """Check if Gemini is available."""
        return self.model is not None
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate a response using Gemini with retries.
        """
        if not self.model:
            return "Gemini is not configured. Please set GOOGLE_API_KEY."
        
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Combine system and user prompts
                full_prompt = f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
                
                response = self.model.generate_content(full_prompt)
                return response.text
                
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = 5 * (2 ** attempt)  # Exponential: 5s, 10s, 20s
                    print(f"⚠️ Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return f"Error generating response: {str(e)}"
        return "Error: Maximum retries exceeded."
    
    def generate_with_tools(
        self, 
        prompt: str, 
        tools: Dict[str, callable],
        system_prompt: str = ""
    ) -> str:
        """
        Generate response with tool calling capability.
        
        Args:
            prompt: User prompt
            tools: Dictionary of tool name -> function
            system_prompt: System instructions
        
        Returns:
            Final response after tool execution
        """
        if not self.model:
            return "Gemini is not configured. Please set GOOGLE_API_KEY."
        
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
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(enhanced_prompt)
                text = response.text
                
                # Check if model wants to use a tool
                if "TOOL:" in text and "INPUT:" in text:
                    # Parse tool call
                    lines = text.split("\n")
                    tool_name = None
                    tool_input = None
                    
                    for i, line in enumerate(lines):
                        if line.startswith("TOOL:"):
                            tool_name = line.replace("TOOL:", "").strip()
                        elif line.startswith("INPUT:"):
                            # Get everything after INPUT:
                            tool_input = line.replace("INPUT:", "").strip()
                            # Try to get multi-line JSON
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
                        final_response = self.model.generate_content(followup)
                        return final_response.text
                
                return text
                
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = 5 * (2 ** attempt)  # Exponential: 5s, 10s, 20s
                    print(f"⚠️ Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return f"Error: {str(e)}"
        return "Error: Maximum retries exceeded."


# Create default client
def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client."""
    return GeminiClient()
