import os
import json 
from openai import OpenAI # OpenAI API 사용을 위한 모듈
from datetime import datetime # 날짜 처리용
from dotenv import load_dotenv # 환경변수 로딩용

# API 키 로딩
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 사용자 정의 함수 
# 날짜 포맷 변경
def convert_data_format(date_str, current_format, target_format):
    dt = datetime.strptime(date_str, current_format)  # 현재 포맷으로 파싱
    return dt.strftime(target_format)  # 원하는 포맷으로 변환하여 반환
# 숫자 덧셈
def add_numbers(x, y):
    return x + y

# Function schema 정의
function_schemas = [
    {
        "name": "convert_data_format",
        "description": "날짜 문자열을 다른 형식으로 변환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_str": {"type": "string", "description": "예: '2020-12-25'"},
                "current_format": {"type": "string", "description": "예: '%Y-%m-%d'"},
                "target_format": {"type": "string", "description": "예: '%Y년 %m월 %d일'"},
            },
            "required": ["date_str", "current_format", "target_format"], # 필수 인자
        }
    },
    {
        "name": "add_numbers",
        "description": "두 숫자를 더합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "첫 번째 숫자"},
                "y": {"type": "number", "description": "두 번째 숫자"},
            },
            "required": ["x", "y"],
        }
    }
]

# OpenAI 기반 챗봇 클래스 정의
class OpenAiAgent:
    def __init__(self):
        # 시스템 메시지로 역할 설정
        self.messages = [{
            "role": "system", 
            "content": "너는 사용자의 요청을 이해해서 적절한 함수를 자동으로 호출하는 AI 비서야. 사용자가 날짜 변환이나 숫자 계산을 요구하면 등록된 함수를 호출해."
            }]
    # 사용자의 질문을 처리하는 메인 함수
    def chat(self, user_input):
        self.messages.append({"role": "user", "content": user_input}) # 사용자 메시지 추가
        response = self.call_openai(self.messages) # OpenAI에 메시지 전달

        function_call = response.get("function_call")
        if function_call: # 함수 호출 요청이 있는 경우
            try:
                args = json.loads(function_call["arguments"]) # JSON 형식으로 파싱
                result = self.handle_function_call(function_call["name"], args) # 로컬 함수 실행

                # 함수 결과를 OpenAI에게 전달하여 자연어 응답 생성
                self.messages.append({
                    "role": "function",
                    "name": function_call["name"],
                    "content": str(result)
                })

                # 최종 응답 생성
                final_response = self.call_openai(self.messages, functions_enabled=False)
                answer = final_response["content"]

            except Exception as e:
                answer = f"함수 실행 중 오류 발생: {e}"
        else:
            answer = response["content"] # 일반 응답 처리

        print(f"\n AI: {answer}\n") # 사용자에게 출력

    # OpenAI API 호출 함수
    def call_openai(self, messages, functions_enabled=True):
        kwargs = {
            "model": "gpt-4-0613", # 함수 호출 가능한 GPT-4 버전
            "messages": messages,
        }

        if functions_enabled:
            kwargs["functions"] = function_schemas # 사전 정의된 함수 리스트 제공
            kwargs["function_call"] = "auto" # 자동으로 적절한 함수 호출

        response = client.chat.completions.create(**kwargs) # API 호출
        choice = response.choices[0].message # 응답 중 첫 번째 결과 선택

        return {
            "content": choice.content, # 일반 응답 내용
            "function_call": {
                "name": choice.function_call.name,
                "arguments": choice.function_call.arguments
            } if choice.function_call else None
        }

    # 실제 로컬 함수 호출 처리
    def handle_function_call(self, name, args):
        if name == "convert_data_format":
            return convert_data_format(**args)
        elif name == "add_numbers":
            return add_numbers(**args)
        else:
            return "알 수 없는 함수입니다."


# 메인 루프 (사용자 입력 기반)
if __name__ == "__main__":
    agent = OpenAiAgent()
    print("AI 함수 호출 챗봇입니다. 'exit'을 입력하면 종료됩니다.")

    # 사용자로부터 반복적으로 입력 받기
    while True:
        user_input = input("질문하세요: ")
        if user_input.lower() in ["exit", "quit", "종료"]:
            print("챗봇을 종료합니다.")
            break
        agent.chat(user_input)
