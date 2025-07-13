"use client"
import { MessageSquare, FileText, Languages } from "lucide-react"
import { useNLP } from "@/app/context/NLPContext"

const services = [
  {
    id: "questions" as const,
    name: "Generación de Preguntas",
    description: "Genera preguntas relevantes del contenido",
    icon: MessageSquare,
    color: "text-blue-600",
  },
  {
    id: "summary" as const,
    name: "Resumen de Texto",
    description: "Crea un resumen conciso del documento",
    icon: FileText,
    color: "text-green-600",
  },
  {
    id: "translation" as const,
    name: "Traducción EN>ES",
    description: "Traduce el contenido del inglés al español",
    icon: Languages,
    color: "text-purple-600",
  },
]

export default function ServiceTabs() {
  const { state, dispatch } = useNLP()

  const handleServiceChange = (serviceId: "questions" | "summary" | "translation") => {
    dispatch({ type: "SET_SELECTED_SERVICE", payload: serviceId })
    dispatch({ type: "CLEAR_RESULTS" })
  }

  const processDocument = async () => {
    if (!state.currentDocument) return

    dispatch({ type: "SET_PROCESSING", payload: true })

    // Simular procesamiento
    setTimeout(() => {
      const mockResult = {
        id: Date.now().toString(),
        documentId: state.currentDocument!.id,
        service: state.selectedService,
        result: generateMockResult(state.selectedService),
        createdAt: new Date(),
        format: "json" as const,
      }

      dispatch({ type: "ADD_RESULT", payload: mockResult })
      dispatch({ type: "SET_PROCESSING", payload: false })
    }, 2000)
  }

  const generateMockResult = (service: string) => {
    switch (service) {
      case "questions":
        return {
          questions: [
            "¿Cuál es el tema principal del documento?",
            "¿Qué conclusiones se pueden extraer?",
            "¿Cuáles son los puntos clave mencionados?",
          ],
          keywords: ["análisis", "datos", "resultados", "conclusión"],
        }
      case "summary":
        return {
          summary:
            "Este documento presenta un análisis detallado de los datos recopilados durante el estudio. Los resultados muestran tendencias significativas que apoyan las hipótesis iniciales.",
          keywords: ["análisis", "datos", "tendencias", "hipótesis"],
          wordCount: 45,
        }
      case "translation":
        return {
          originalText: "This document presents a detailed analysis...",
          translatedText: "Este documento presenta un análisis detallado...",
          keywords: ["documento", "análisis", "detallado"],
          confidence: 0.95,
        }
      default:
        return {}
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Servicios NLP</h2>

      <div className="grid grid-cols-1 gap-4">
        {services.map((service) => {
          const Icon = service.icon
          const isSelected = state.selectedService === service.id

          return (
            <button
              key={service.id}
              onClick={() => handleServiceChange(service.id)}
              className={`
                p-4 rounded-lg border-2 text-left transition-all focus:outline-none focus:ring-2 focus:ring-primary-500
                ${isSelected ? "border-primary-500 bg-primary-50" : "border-gray-200 hover:border-gray-300 bg-white"}
              `}
              disabled={!state.currentDocument}
              aria-pressed={isSelected}
            >
              <div className="flex items-start space-x-3">
                <Icon className={`h-6 w-6 mt-1 ${service.color}`} />
                <div className="flex-1">
                  <h3 className={`font-medium ${isSelected ? "text-primary-900" : "text-gray-900"}`}>{service.name}</h3>
                  <p className={`text-sm mt-1 ${isSelected ? "text-primary-700" : "text-gray-500"}`}>
                    {service.description}
                  </p>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      <button
  onClick={processDocument}
  disabled={!state.currentDocument || state.isProcessing}
  className="
    w-full py-3 px-4 rounded-lg font-medium 
    transition-colors duration-200
    focus:outline-none focus:ring-2 
    focus:ring-ring focus:ring-offset-2
    disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed
    bg-primary text-primary-foreground 
    hover:bg-primary/90 dark:hover:bg-primary/80
    relative
  "
>
  {state.isProcessing ? (
    <span className="inline-flex items-center justify-center gap-2">
      <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
      Procesando...
    </span>
  ) : (
    "Procesar Documento"
  )}
</button>
    </div>
  )
}
