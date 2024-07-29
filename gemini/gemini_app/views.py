from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import google.generativeai as genai
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Gemini API 설정
try:
    genai.configure(api_key=os.environ["API_KEY"])
except KeyError:
    logger.error("API_KEY environment variable is not set")
    raise

generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 32,
    "max_output_tokens": 1024,
}

try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {str(e)}")
    raise

def index(request):
    return render(request, 'index.html')

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        logger.info(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    except Exception as e:
        logger.error(f"Failed to upload file to Gemini: {str(e)}")
        raise

@csrf_exempt
def process_speech(request):
    if request.method == 'POST':
        user_text = ''
        file = None

        # 먼저 request.body를 처리합니다.
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_text = data.get('text', '')
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON body")
        else:
            # multipart/form-data 또는 application/x-www-form-urlencoded 처리
            user_text = request.POST.get('text', '')

        # 이미지 처리
        if 'image' in request.FILES:
            image = request.FILES['image']
            path = default_storage.save('uploads/' + image.name, ContentFile(image.read()))
            try:
                file = upload_to_gemini(path, mime_type="image/jpeg")
            except Exception as e:
                logger.error(f"Failed to upload image: {str(e)}")
                return JsonResponse({'error': 'Failed to process image'}, status=500)
            finally:
                default_storage.delete(path)

        if not user_text and not file:
            return JsonResponse({'error': 'No text or image provided'}, status=400)

        try:
            # Prepare content for Gemini API
            content = ["한국어로, "]
            if user_text:
                content.append(user_text)
            if file:
                content.extend(["Image: ", file])

            # Gemini API에 요청 보내기
            response = model.generate_content(content)

            # 응답 처리
            if response.text:
                logger.info(f"Received response from Gemini API: {response.text}")
                return JsonResponse({'response': response.text})
            else:
                logger.warning("Received empty response from Gemini API")
                return JsonResponse({'error': 'No response from Gemini API'}, status=500)

        except Exception as e:
            logger.error(f"An error occurred during processing: {str(e)}")
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)