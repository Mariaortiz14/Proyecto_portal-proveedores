from rest_framework import serializers
from .models import registro_formulario

class RegistroFormularioSerializer(serializers.ModelSerializer):
    class Meta:
        model = registro_formulario
        fields = '__all__'
