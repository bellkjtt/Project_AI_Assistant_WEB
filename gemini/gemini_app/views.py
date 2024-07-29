from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import requests

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def process_speech(request):
    if request.method == 'POST':
        if 'image' in request.FILES:
            image = request.FILES['image']
            path = default_storage.save('uploads/' + image.name, ContentFile(image.read()))
            with default_storage.open(path) as img:
                img_data = img.read()

            # 이미지 데이터를 API에 전송하는 코드 예시
            gemini_api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': 'AIzaSyDRhH2m3ICi7qC3RIhrRvcngZvq4JVVbH0',  # 실제 API 키로 변경
            }
            payload = {
                "contents": [{"parts": [{"image": img_data}]}]  # 이미지 데이터 포함
            }

            response = requests.post(gemini_api_url, headers=headers, json=payload)
            response_data = response.json()

            # Gemini API 응답에서 텍스트 추출
            generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
            return JsonResponse({'response': generated_text})

        else:
            data = json.loads(request.body)
            user_text = data['text']

            # Gemini API 호출
            gemini_api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': 'AIzaSyDRhH2m3ICi7qC3RIhrRvcngZvq4JVVbH0',  # 실제 API 키로 변경
            }
            payload = {
                "contents": [{"parts": [{"text": user_text}]}]
            }

            response = requests.post(gemini_api_url, headers=headers, json=payload)
            response_data = response.json()

            # Gemini API 응답에서 텍스트 추출
            generated_text = response_data['candidates'][0]['content']['parts'][0]['text']

            return JsonResponse({'response': generated_text})

    return JsonResponse({'error': 'Invalid request method'}, status=400)
