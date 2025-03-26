from google.generativeai import configure, list_models

# Configure API key (Replace with your actual key)
configure(api_key="AIzaSyD2CeYtsMGXsgV8ygmU5VdJefJmqg6Xb-U")

# List available models
models = list_models()

# Print model details
for model in models:
    print(model.name)
