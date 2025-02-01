from rest_framework import serializers
from .models import Document, Rating
from django.contrib.auth.models import User


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'text']


class DocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['title', 'text']


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['document', 'score']

    def validate_score(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating score must be between 1 and 5")
        return value


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name')
        ref_name = "RateWiseUser"

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
