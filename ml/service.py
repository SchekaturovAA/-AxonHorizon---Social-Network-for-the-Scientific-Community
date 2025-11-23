from decouple import config
from openai import OpenAI


class DeepSeekAnalyzer:
    def __init__(self):
        api_key = config('OPENROUTER_API_KEY', default='')

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY не найден в .env файле!")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def analyze_scientific_data(self, experiment_data, research_question):
        """
        Анализ научных экспериментальных данных
        """
        try:
            response = self.client.chat.completions.create(
                # ✅ ИСПРАВЛЕННЫЕ МОДЕЛИ (выбери одну):
                model="deepseek/deepseek-chat",  # Основная модель DeepSeek
                # model="deepseek/deepseek-coder",  # Для кода и анализа данных
                # model="meta-llama/llama-3-70b-instruct",  # Альтернатива

                messages=[
                    {
                        "role": "system",
                        "content": """Ты - эксперт по анализу научных данных. 
                        Анализируй экспериментальные данные, находи закономерности, 
                        статистические зависимости и делай научно обоснованные выводы.
                        Будь точным и детализированным в анализе."""
                    },
                    {
                        "role": "user",
                        "content": f"""
                        ДАННЫЕ ЭКСПЕРИМЕНТА:
                        {experiment_data}

                        НАУЧНЫЙ ВОПРОС ДЛЯ АНАЛИЗА:
                        {research_question}

                        Пожалуйста, проанализируй данные и предоставь подробный научный отчет.
                        """
                    }
                ],
                max_tokens=4000,
                temperature=0.3,
                # reasoning больше не поддерживается для этих моделей
            )

            return {
                'success': True,
                'analysis': response.choices[0].message.content,
                'model_used': "deepseek-chat",
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }