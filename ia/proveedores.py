"""Servicios de IA disponibles. Añadir uno compatible con OpenAI es añadir una entrada."""
from dataclasses import dataclass, field
from typing import List

COMPATIBLE_OPENAI = "compatible_openai"
ANTHROPIC = "anthropic"


@dataclass(frozen=True)
class Proveedor:
    id: str            # Se usa como nombre en la configuración y en el almacén de claves
    nombre: str        # Lo que se ve en la lista
    nombre_corto: str  # Lo que se dice en los mensajes
    tipo: str
    url: str = ""
    modelos: List[str] = field(default_factory=list)  # El primero es el predeterminado
    necesita_clave: bool = True
    es_local: bool = False


# Los nombres de modelo cambian a menudo: el campo Modelo deja escribir cualquiera.
PROVEEDORES = [
    Proveedor("openai", "OpenAI", "OpenAI", COMPATIBLE_OPENAI,
              "https://api.openai.com/v1",
              ["gpt-6-luna", "gpt-5-nano", "gpt-4o-mini"]),
    Proveedor("claude", "Claude", "Claude", ANTHROPIC, "",
              ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]),
    Proveedor("gemini", "Google Gemini", "Google Gemini", COMPATIBLE_OPENAI,
              "https://generativelanguage.googleapis.com/v1beta/openai",
              ["gemini-3.8-flash", "gemini-3.5-flash-lite"]),
    Proveedor("groq", "Groq", "Groq", COMPATIBLE_OPENAI,
              "https://api.groq.com/openai/v1",
              ["qwen/qwen3.8-27b"]),
    Proveedor("openrouter", "OpenRouter", "OpenRouter", COMPATIBLE_OPENAI,
              "https://openrouter.ai/api/v1",
              ["thinkingmachines/inkling-2-small:free"]),
    Proveedor("ollama", "Ollama (en este ordenador)", "Ollama", COMPATIBLE_OPENAI,
              "http://localhost:11434/v1",
              ["qwen3-vl:8b", "gemma3:4b"],
              necesita_clave=False, es_local=True),
]

PREDETERMINADO = "openai"


def buscar(id_proveedor):
    for proveedor in PROVEEDORES:
        if proveedor.id == id_proveedor:
            return proveedor
    return buscar(PREDETERMINADO)
