from django.contrib import admin
from .models import UserEmbedding, PaperEmbedding, Recommendation, Experiment, MLModelVersion

@admin.register(UserEmbedding)
class UserEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')

@admin.register(PaperEmbedding)
class PaperEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('doi', 'title', 'scientific_field')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recommended_user', 'score', 'created_at')

# блок для анализа данных
@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'feasibility_score', 'plausibility_score', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MLModelVersion)
class MLModelVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')

    #superuser - log - testuser; pass - testpassword123;