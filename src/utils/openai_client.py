"""
OpenAI client wrapper with compatibility fixes
"""

import os
from typing import List, Dict, Any

def get_openai_response(messages: List[Dict[str, str]], api_key: str) -> str:
    """
    Get response from OpenAI with compatibility handling
    """
    try:
        # Try with the new OpenAI client
        from openai import OpenAI
        
        # Create client with minimal parameters
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.1,
            top_p=0.9
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # If new client fails, try alternative approach
        try:
            import openai
            
            # Try setting the API key globally
            openai.api_key = api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.1,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e2:
            # Try with requests directly
            try:
                import requests
                import json
                
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'model': 'gpt-3.5-turbo',
                    'messages': messages,
                    'max_tokens': 1000,
                    'temperature': 0.1,
                    'top_p': 0.9
                }
                
                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return f"API Error: {response.status_code} - {response.text}"
                    
            except Exception as e3:
                return f"Failed to connect to OpenAI: {e3}"