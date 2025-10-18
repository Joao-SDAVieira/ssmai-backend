from enum import Enum

class MovementTypesEnum(str, Enum):
    entrada = 'Entrada'
    saida = 'Saida'
    outro = 'Outro'