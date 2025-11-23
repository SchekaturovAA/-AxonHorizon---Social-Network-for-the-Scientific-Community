import requests
import json
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class DeepSeekMLService:
    def __init__(self):
        self.api_key = "API-key"
        self.base_url = "https://api.deepseek.com/v1"
        self.timeout = 60
        self.model = "deepseek-chat"

    def _call_deepseek_api(self, messages, temperature=0.7, max_tokens=2000):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format from DeepSeek API: {e}")
            raise

    def preprocess_experiment_data(self, raw_data):
        try:
            processed_data = {
                'title': raw_data.get('title', '').strip(),
                'description': raw_data.get('description', '').strip(),
                'hypothesis': raw_data.get('hypothesis', ''),
                'materials': self._normalize_materials(raw_data.get('materials', [])),
                'methods': self._validate_methods(raw_data.get('methods', [])),
                'expected_results': raw_data.get('expected_results', ''),
                'budget_constraints': raw_data.get('budget_constraints', {}),
                'time_constraints': raw_data.get('time_constraints', {}),
                'equipment': raw_data.get('equipment', []),
                'safety_considerations': raw_data.get('safety_considerations', ''),
                'field_of_study': raw_data.get('field_of_study', 'general'),
            }
            return processed_data
        except Exception as e:
            logger.error(f"Error in data preprocessing: {e}")
            raise

    def _normalize_materials(self, materials):
        normalized = []
        for material in materials:
            if isinstance(material, dict):
                normalized.append({
                    'name': material.get('name', '').strip().lower(),
                    'quantity': float(material.get('quantity', 0)),
                    'unit': material.get('unit', '').strip().lower(),
                    'cost': float(material.get('cost', 0)) if material.get('cost') else None,
                    'availability': material.get('availability', 'unknown')
                })
            elif isinstance(material, str):
                normalized.append({'name': material.strip().lower()})
        return normalized

    def _validate_methods(self, methods):
        valid_methods = []
        for method in methods:
            if isinstance(method, str) and method.strip():
                valid_methods.append(method.strip())
            elif isinstance(method, dict) and method.get('name'):
                valid_methods.append(method['name'].strip())
        return valid_methods

    def analyze_experiment_feasibility(self, processed_data):
        system_prompt = """Ты - эксперт по анализу научных экспериментов. Проанализируй предложенный эксперимент и оцени:
        1. Реализуемость (feasibility_score) - насколько реалистично провести этот эксперимент
        2. Правдоподобность (plausibility_score) - насколько научно обоснован эксперимент
        3. Предложения по улучшению (improvements) - конкретные рекомендации
        4. Потенциальные проблемы (warnings) - что может пойти не так
        5. Альтернативные подходы (alternative_methods) - другие возможные методы

        Ответь ТОЛЬКО в формате JSON:
        {
            "feasibility_score": число от 0 до 1,
            "plausibility_score": число от 0 до 1,
            "improvements": ["предложение 1", "предложение 2", ...],
            "warnings": ["предупреждение 1", "предупреждение 2", ...],
            "alternative_methods": ["метод 1", "метод 2", ...],
            "reasoning": "краткое обоснование оценок"
        }"""

        user_prompt = f"""
        Проанализируй следующий научный эксперимент:

        НАЗВАНИЕ: {processed_data['title']}
        ОПИСАНИЕ: {processed_data['description']}
        ГИПОТЕЗА: {processed_data['hypothesis']}

        МАТЕРИАЛЫ: {json.dumps(processed_data['materials'], ensure_ascii=False, indent=2)}
        МЕТОДЫ: {processed_data['methods']}
        ОБОРУДОВАНИЕ: {processed_data['equipment']}

        ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ: {processed_data['expected_results']}
        БЮДЖЕТНЫЕ ОГРАНИЧЕНИЯ: {processed_data['budget_constraints']}
        ВРЕМЕННЫЕ ОГРАНИЧЕНИЯ: {processed_data['time_constraints']}
        БЕЗОПАСНОСТЬ: {processed_data['safety_considerations']}
        ОБЛАСТЬ ИССЛЕДОВАНИЙ: {processed_data['field_of_study']}
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._call_deepseek_api(messages, temperature=0.3)
            result = json.loads(response)

            if not all(key in result for key in ['feasibility_score', 'plausibility_score']):
                raise ValueError("Invalid response format from DeepSeek API")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response as JSON: {e}")
            return self._extract_json_from_text(response)
        except Exception as e:
            logger.error(f"Error in experiment analysis: {e}")
            return self._get_fallback_response()

    def suggest_improvements(self, processed_data):
        system_prompt = """Ты - опытный научный исследователь. Предложи конкретные улучшения для эксперимента.

        Ответь в формате JSON:
        {
            "method_improvements": ["улучшение 1", "улучшение 2", ...],
            "cost_optimizations": ["оптимизация 1", "оптимизация 2", ...],
            "safety_enhancements": ["улучшение безопасности 1", ...],
            "efficiency_boosters": ["способ повышения эффективности 1", ...]
        }"""

        user_prompt = f"""
        Эксперимент: {processed_data['title']}
        Текущие методы: {processed_data['methods']}
        Материалы: {processed_data['materials']}
        Бюджет: {processed_data['budget_constraints']}
        Время: {processed_data['time_constraints']}
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._call_deepseek_api(messages, temperature=0.5)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error in improvement suggestions: {e}")
            return {"method_improvements": [], "cost_optimizations": [], "safety_enhancements": [],
                    "efficiency_boosters": []}

    def validate_experiment_design(self, processed_data):
        feasibility_analysis = self.analyze_experiment_feasibility(processed_data)
        improvements = self.suggest_improvements(processed_data)

        combined_result = {
            **feasibility_analysis,
            "detailed_improvements": improvements,
            "overall_score": (
                    feasibility_analysis.get('feasibility_score', 0) * 0.6 +
                    feasibility_analysis.get('plausibility_score', 0) * 0.4
            )
        }

        return combined_result

    def _extract_json_from_text(self, text):
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass

        return self._get_fallback_response()

    def _get_fallback_response(self):
        return {
            "feasibility_score": 0.5,
            "plausibility_score": 0.5,
            "improvements": ["Не удалось провести детальный анализ. Проверьте входные данные."],
            "warnings": ["Анализ может быть неполным из-за технических проблем."],
            "alternative_methods": [],
            "reasoning": "Анализ не был завершен из-за технической ошибки.",
            "overall_score": 0.5
        }


deepseek_service = DeepSeekMLService()