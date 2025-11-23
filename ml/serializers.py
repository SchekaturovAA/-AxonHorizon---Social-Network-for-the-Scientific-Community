from rest_framework import serializers
from .models import Experiment, MLModelVersion, UserEmbedding, PaperEmbedding, Recommendation


class ExperimentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    overall_score = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = [
            'id', 'user', 'title', 'description', 'input_data',
            'output_data', 'status', 'feasibility_score',
            'plausibility_score', 'improvements', 'created_at',
            'updated_at', 'overall_score'
        ]
        read_only_fields = [
            'id', 'user', 'output_data', 'status', 'feasibility_score',
            'plausibility_score', 'improvements', 'created_at', 'updated_at', 'overall_score'
        ]

    def get_overall_score(self, obj):
        if obj.feasibility_score and obj.plausibility_score:
            return (obj.feasibility_score * 0.6 + obj.plausibility_score * 0.4)
        return None


class MLModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModelVersion
        fields = '__all__'


class ExperimentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    hypothesis = serializers.CharField(required=False, allow_blank=True)
    experimental_data = serializers.JSONField()
    model_version = serializers.CharField(required=False, default='latest')

    def validate_experimental_data(self, value):
        required_fields = ['materials', 'methods', 'expected_results']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value


# Существующие сериализаторы для рекомендаций (если нужны)
class UserEmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEmbedding
        fields = '__all__'


class PaperEmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperEmbedding
        fields = '__all__'


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'