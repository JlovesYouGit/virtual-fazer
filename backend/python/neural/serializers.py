from rest_framework import serializers
from .models import (
    NeuralModel, UserNeuralProfile, CategoryPattern, UserInteraction,
    NeuralPrediction, AutoFollowRule, AutoFollowAction
)
from users.serializers import UserSerializer


class NeuralModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeuralModel
        fields = '__all__'


class UserNeuralProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserNeuralProfile
        fields = '__all__'


class CategoryPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryPattern
        fields = '__all__'


class UserInteractionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserInteraction
        fields = '__all__'


class NeuralPredictionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    model_used = NeuralModelSerializer(read_only=True)
    
    class Meta:
        model = NeuralPrediction
        fields = '__all__'


class AutoFollowRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoFollowRule
        fields = '__all__'


class AutoFollowActionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    rule = AutoFollowRuleSerializer(read_only=True)
    
    class Meta:
        model = AutoFollowAction
        fields = '__all__'


class UserCategorizationSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    categories = serializers.DictField()
    confidence_scores = serializers.DictField()
    behavior_patterns = serializers.DictField()


class UserMatchingSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    matched_users = serializers.ListField(child=serializers.UUIDField())
    match_scores = serializers.ListField(child=serializers.FloatField())
    match_reasons = serializers.ListField(child=serializers.CharField())


class AutoFollowRequestSerializer(serializers.Serializer):
    rule_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    max_follows = serializers.IntegerField(default=10)
    min_confidence = serializers.FloatField(default=0.8)
