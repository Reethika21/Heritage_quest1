import google.generativeai as genai
import pandas as pd
from tabulate import tabulate

# Configure Gemini API with your new key
genai.configure(api_key="AIzaSyB132JcIy5oeTqE865cpZiqPg88fZ1f8Ms")

# Function to list available models and their capabilities
def list_models_with_capabilities():
    try:
        # Get all available models
        models = genai.list_models()
        
        # Create a list to store model information
        model_info = []
        
        # Extract relevant information for each model
        for model in models:
            model_info.append({
                "Name": model.name,
                "Generation Methods": ", ".join(model.supported_generation_methods),
                "Input Types": getattr(model, "input_token_limit", "Unknown"),
                "Output Types": getattr(model, "output_token_limit", "Unknown")
            })
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(model_info)
        
        # Display as table
        print("\n=== Available Gemini Models ===\n")
        print(tabulate(df, headers="keys", tablefmt="grid"))
        
        return df
    
    except Exception as e:
        print(f"Error listing models: {e}")
        return None

# Function to test model capabilities with a simple prompt
def test_model(model_name="gemini-1.5-pro-latest"):
    try:
        print(f"\nTesting model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        # Simple test prompt
        test_prompt = "Explain the significance of the Taj Mahal in three sentences."
        
        # Generate response
        response = model.generate_content(test_prompt)
        
        print("\n=== Test Results ===")
        print(f"Prompt: {test_prompt}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error testing model: {e}")

# Main execution
if __name__ == "__main__":
    print("Gemini API Model Explorer")
    print("-------------------------")
    
    # List all available models
    models_df = list_models_with_capabilities()
    
    # Test default model
    test_model()
    
    print("\nScript completed successfully.")