import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.getcwd(), "service-account.json")

query = "Explain the theory of relativity in simple terms."
from vertexai.generative_models import GenerativeModel  #issue
model = GenerativeModel("gemini-2.5-flash")

result = model.generate_content(query)

print("Generated content:", result.text)