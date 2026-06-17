from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
import re
import os
from dotenv import load_dotenv
load_dotenv()

SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")

if not os.path.isfile(SERVICE_ACCOUNT_PATH):
    raise RuntimeError("Service account file missing")

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_PATH
)


translate_client = translate.Client(credentials=creds)


def translation(detected_lang, user_query):
    # Translate non-English query to English
    if detected_lang != "en":
        try:
            translation = translate_client.translate(user_query, target_language="en")
            user_query = translation.get("translatedText", user_query)
            # print("query: ",user_query)
            return user_query
        except Exception as e:
            print(f"[Translation Error] {e}")  # Replace with logger.error
    
    else:
        return user_query
    

# def output_converison(response,target_language):
#     translated_response = translate_client.translate(response, target_language=target_language)
#     translated_response = translated_response.get("translatedText", translated_response)

#     return translated_response




def output_converison(text, targeted_language):
    if targeted_language and targeted_language.strip():
        try:
            # Use a less "natural" placeholder that is unlikely to be altered
            placeholder = "__[[[LINE_BREAK]]]__"
            text_with_placeholders = text.replace("\n", placeholder)

            translation = translate_client.translate(
                text_with_placeholders,
                target_language=targeted_language
            )

            translated_text = translation['translatedText']

            # Normalize potential placeholder variants before restoring newlines
            translated_text = re.sub(
                r'[_\s\[\]]*LINE[\s_]*BREAK[_\s\[\]]*',
                placeholder,
                translated_text,
                flags=re.IGNORECASE
            )

            # Replace placeholders with actual newlines
            text = translated_text.replace(placeholder, "\n")

        except Exception as e:
            print("Translation failed:", str(e))
    return text

